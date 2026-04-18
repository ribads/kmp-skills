---
name: mvi
description: Use when implementing screen architecture, view models, unidirectional data flow, Intent-Result-State-Effect patterns, or any MVI/Elm-style architecture in a KMP Compose project. This is the Synapse IRSE-MVI framework.
user-invocable: true
---

# ui:mvi — IRSE-MVI Architecture

**Module**: `ui:mvi` | **Artifact**: `com.ribads.synapse:ui-mvi`
**Package**: `com.ribads.synapse.ui.mvi`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-mvi:<version>")
}
```

---

## Core Types

```kotlin
interface Interactor<Intent, Result, State> {
    fun process(intents: Flow<Intent>, state: StateFlow<State>): Flow<Result>
}

interface Reducer<State, Result, Effect> {
    fun reduce(state: State, result: Result): Reduction<State, Effect>
}

data class Reduction<State, Effect>(
    val state: State,
    val effects: List<Effect> = emptyList()
)

interface MviProcessor<Intent, Result, State, Effect> {
    val state: StateFlow<State>
    val effects: Flow<Effect>
    fun emit(intent: Intent)
}

abstract class LifecycleViewModel<Intent, Result, ViewState, Effect> protected constructor(
    args: ViewModelArgs<Intent, Result, ViewState, Effect>
) : ViewModel() {
    val state: androidx.compose.runtime.State<ViewState>
    val effects: Flow<Effect>
    fun emit(intent: Intent)
}

class FlowViewModelArgs<Intent, Result, State, Effect>(
    initialState: State,
    interactor: Interactor<Intent, Result, State>,
    reducer: Reducer<State, Result, Effect>,
    onPipelineError: (Throwable) -> Unit = {}
) : LifecycleViewModel.ViewModelArgs<Intent, Result, State, Effect>()

interface IntentFlowHolder<Intent> {
    val intents: Flow<Intent>
    suspend fun emit(intent: Intent)
}

class SharedIntentFlowHolder<Intent> : IntentFlowHolder<Intent>

class FlowMviProcessor<Intent, Result, State, Effect>(
    initialState: State,
    interactor: Interactor<Intent, Result, State>,
    reducer: Reducer<State, Result, Effect>,
    intentFlowHolder: IntentFlowHolder<Intent>,
    coroutineScope: CoroutineScope,
    onPipelineError: (Throwable) -> Unit = {}
) : MviProcessor<Intent, Result, State, Effect>
```

### Reduction helpers

```kotlin
infix fun <State, Effect> State.withEffect(effect: Effect): Reduction<State, Effect>
fun <State, Effect> State.withEffects(vararg effects: Effect): Reduction<State, Effect>
fun <State, Effect> State.noEffects(): Reduction<State, Effect>
```

### Compose helpers

```kotlin
@Composable
fun <Intent> LifecycleViewModel<Intent, *, *, *>.OnFirstComposition(vararg intents: Intent)

@Composable
fun <Effect> Flow<Effect>.CollectAsEffect(onEffect: suspend (Effect) -> Unit)
```

---

## Data Flow

```
Intent ─► Interactor(intents, state) ─► Result ─► Reducer ─► Reduction(State, Effects)
                                                               │
                                                     ┌─────────┴─────────┐
                                                     ▼                   ▼
                                              State (StateFlow)    Effects (Flow)
```

- **State** is what the UI renders (durable; survives recomposition).
- **Effects** are one-shot side effects: navigation, toasts, analytics pings, dialog-open events.
- Interactor receives the current `StateFlow` so handlers can read the latest state without needing it in Intents.

---

## Implementation Pattern

### 1. Define the Contract

```kotlin
internal object LoginContract {
    sealed class Intent {
        data class OnEmailChanged(val email: String) : Intent()
        data class OnPasswordChanged(val password: String) : Intent()
        data object OnSubmit : Intent()
        data object OnBack : Intent()
    }

    sealed class Result {
        data class EmailUpdated(val email: String) : Result()
        data class PasswordUpdated(val password: String) : Result()
        data object Loading : Result()
        data class Success(val userId: String) : Result()
        data class Error(val message: String) : Result()
        data object NavigateBack : Result()
    }

    sealed class Effect {
        data class NavigateToHome(val userId: String) : Effect()
        data object NavigateBack : Effect()
        data class ShowToast(val message: String) : Effect()
    }

    @Immutable
    data class ViewState(
        val email: String = "",
        val password: String = "",
        val isLoading: Boolean = false,
        val error: String? = null,
    )
}
```

### 2. Implement the Interactor

```kotlin
internal class LoginInteractor @Inject constructor(
    private val authRepository: AuthRepository,
) : Interactor<Intent, Result, ViewState> {

    override fun process(
        intents: Flow<Intent>,
        state: StateFlow<ViewState>,
    ): Flow<Result> = merge(
        intents.filterIsInstance<Intent.OnEmailChanged>()
            .map { Result.EmailUpdated(it.email) },
        intents.filterIsInstance<Intent.OnPasswordChanged>()
            .map { Result.PasswordUpdated(it.password) },
        intents.filterIsInstance<Intent.OnSubmit>()
            .let { submitProcessor(it, state) },
        intents.filterIsInstance<Intent.OnBack>()
            .map { Result.NavigateBack },
    )

    private fun submitProcessor(
        upstream: Flow<Intent.OnSubmit>,
        state: StateFlow<ViewState>,
    ): Flow<Result> = upstream.flatMapLatest {
        val current = state.value
        flow { emit(authRepository.login(current.email, current.password)) }
            .map { Result.Success(it.userId) }
            .catch { emit(Result.Error(it.message ?: "Unknown error")) }
            .onStart { emit(Result.Loading) }
    }
}
```

> Handlers that need state read `state.value` inside `flatMapLatest` — never rely on state smuggled through Intents.

### 3. Implement the Reducer

```kotlin
internal class LoginReducer @Inject constructor() : Reducer<ViewState, Result, Effect> {
    override fun reduce(
        state: ViewState,
        result: Result,
    ): Reduction<ViewState, Effect> = when (result) {
        is Result.EmailUpdated -> state.copy(email = result.email).noEffects()
        is Result.PasswordUpdated -> state.copy(password = result.password).noEffects()
        is Result.Loading -> state.copy(isLoading = true, error = null).noEffects()
        is Result.Success -> state.copy(isLoading = false) withEffect Effect.NavigateToHome(result.userId)
        is Result.Error -> state.copy(isLoading = false, error = result.message)
            .withEffects(Effect.ShowToast(result.message))
        is Result.NavigateBack -> state withEffect Effect.NavigateBack
    }
}
```

> Reducers stay pure. Side effects (navigate, toast, analytics) leave via the Effect channel, never via state mutation.

### 4. Create the ViewModel

```kotlin
internal class LoginViewModel @Inject constructor(
    initialState: ViewState,
    interactor: Interactor<Intent, Result, ViewState>,
    reducer: Reducer<ViewState, Result, Effect>,
) : LifecycleViewModel<Intent, Result, ViewState, Effect>(
    args = FlowViewModelArgs(
        initialState = initialState,
        interactor = interactor,
        reducer = reducer,
    ),
)
```

### 5. Connect to Compose UI

```kotlin
@Composable
fun LoginScreen(
    viewModel: LoginViewModel,
    navigationDispatcher: NavigationDispatcher,
) {
    val viewState by viewModel.state

    viewModel.effects.CollectAsEffect { effect ->
        when (effect) {
            is Effect.NavigateToHome -> navigationDispatcher.navigateTo(
                NavigationCommand.ScreenCommand(route = "home/${effect.userId}"),
            )
            is Effect.NavigateBack -> navigationDispatcher.navigateTo(NavigationCommand.BackCommand())
            is Effect.ShowToast -> snackbarHostState.showSnackbar(effect.message)
        }
    }

    Column {
        TextField(
            value = viewState.email,
            onValueChange = { viewModel.emit(Intent.OnEmailChanged(it)) },
        )
        TextField(
            value = viewState.password,
            onValueChange = { viewModel.emit(Intent.OnPasswordChanged(it)) },
        )
        Button(
            onClick = { viewModel.emit(Intent.OnSubmit) },
            enabled = !viewState.isLoading,
        ) {
            Text(if (viewState.isLoading) "Loading..." else "Login")
        }
    }
}
```

### Emitting an initial intent

```kotlin
@Composable
fun MyScreen(viewModel: MyViewModel) {
    viewModel.OnFirstComposition(Intent.LoadInitialData)
    // ...
}
```

This replaces the old `if (viewModel.isFirstIntent) viewModel.emit(...)` pattern. `OnFirstComposition` runs exactly once per composition lifetime via `LaunchedEffect(Unit)`.

---

## Error Handling

`FlowViewModelArgs` accepts an `onPipelineError: (Throwable) -> Unit` callback that fires whenever the upstream `Interactor` flow throws OR whenever the `Reducer` throws. The pipeline **recovers automatically** — subsequent intents continue to flow — and the previous state is preserved if the reducer throws.

```kotlin
FlowViewModelArgs(
    initialState = ViewState(),
    interactor = interactor,
    reducer = reducer,
    onPipelineError = { throwable -> logger.error(throwable) { "MVI pipeline error" } },
)
```

A `CoroutineExceptionHandler` tied to the same callback catches any escaped coroutine exceptions inside the internal `SupervisorJob`.

---

## Rules

- **Contract pattern**: Keep `Intent`, `Result`, `Effect`, `ViewState` in one `object`.
- **Reducers are pure**: No side effects, no async — emit `Effect`s instead.
- **Effects are one-shot**: Navigation, snackbars, analytics pings — never drive UI from effects.
- **State is durable**: Survives recomposition, represents what is rendered on screen.
- **Interactor reads state via `state.value`**: Never pass state through Intents.
- **`filterIsInstance` + `merge`**: Clean intent routing in Interactor.
- **Handlers named `*Processor`**: Take `Flow<SpecificIntent>` (plus `StateFlow` when needed). Place above `process()`.
- Works with kotlin-inject (`@Inject constructor`).
