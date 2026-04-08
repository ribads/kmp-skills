---
name: mvi
description: Use when implementing screen architecture, view models, unidirectional data flow, Intent-Result-State patterns, or any MVI/Elm-style architecture in a KMP Compose project. This is the Synapse IRS-MVI framework.
user-invocable: true
---

# ui:mvi — IRS-MVI Architecture

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
interface Interactor<Intent, Result> {
    fun process(intents: Flow<Intent>): Flow<Result>
}

interface Reducer<State, Result> {
    fun reduce(state: State, result: Result): State
}

open class LifecycleViewModel<Intent, Result, ViewState>(
    args: FlowViewModelArgs<Intent, Result, ViewState>
) {
    val state: State<ViewState>
    fun emit(intent: Intent)
}

data class FlowViewModelArgs<Intent, Result, ViewState>(
    val initialState: ViewState,
    val reducer: Reducer<ViewState, Result>,
    val interactor: Interactor<Intent, Result>
)
```

## Data Flow

```
Intent → Interactor → Result → Reducer → State
           (effects)            (pure)
```

---

## Implementation Pattern

### 1. Define the Contract

```kotlin
internal object LoginContract {
    sealed class Intent {
        data class OnEmailChanged(val email: String) : Intent()
        data class OnPasswordChanged(val password: String) : Intent()
        data object OnSubmit : Intent()
    }

    sealed class Result {
        data class EmailUpdated(val email: String) : Result()
        data class PasswordUpdated(val password: String) : Result()
        data object Loading : Result()
        data class Success(val userId: String) : Result()
        data class Error(val message: String) : Result()
    }

    @Immutable
    data class ViewState(
        val email: String = "",
        val password: String = "",
        val isLoading: Boolean = false,
        val error: String? = null
    )
}
```

### 2. Implement the Interactor

```kotlin
internal class LoginInteractor @Inject constructor(
    private val authRepository: AuthRepository
) : Interactor<Intent, Result> {

    override fun process(intents: Flow<Intent>): Flow<Result> = merge(
        intents.filterIsInstance<Intent.OnEmailChanged>()
            .map { Result.EmailUpdated(it.email) },
        intents.filterIsInstance<Intent.OnPasswordChanged>()
            .map { Result.PasswordUpdated(it.password) },
        intents.filterIsInstance<Intent.OnSubmit>()
            .let(::submitProcessor)
    )

    private fun submitProcessor(upstream: Flow<Intent.OnSubmit>): Flow<Result> =
        upstream.flatMapLatest {
            flow { emit(authRepository.login()) }
                .map { Result.Success(it.userId) }
                .catch { emit(Result.Error(it.message ?: "Unknown error")) }
                .onStart { emit(Result.Loading) }
        }
}
```

### 3. Implement the Reducer

```kotlin
internal class LoginReducer @Inject constructor() : Reducer<ViewState, Result> {
    override fun reduce(state: ViewState, result: Result): ViewState = when (result) {
        is Result.EmailUpdated -> state.copy(email = result.email)
        is Result.PasswordUpdated -> state.copy(password = result.password)
        is Result.Loading -> state.copy(isLoading = true, error = null)
        is Result.Success -> state.copy(isLoading = false)
        is Result.Error -> state.copy(isLoading = false, error = result.message)
    }
}
```

### 4. Create the ViewModel

```kotlin
internal class LoginViewModel @Inject constructor(
    initialState: ViewState,
    interactor: Interactor<Intent, Result>,
    reducer: Reducer<ViewState, Result>
) : LifecycleViewModel<Intent, Result, ViewState>(
    args = FlowViewModelArgs(
        initialState = initialState,
        reducer = reducer,
        interactor = interactor
    )
)
```

### 5. Connect to Compose UI

```kotlin
@Composable
fun LoginScreen(viewModel: LoginViewModel) {
    val viewState by viewModel.state

    Column {
        TextField(
            value = viewState.email,
            onValueChange = { viewModel.emit(Intent.OnEmailChanged(it)) }
        )
        TextField(
            value = viewState.password,
            onValueChange = { viewModel.emit(Intent.OnPasswordChanged(it)) }
        )
        Button(
            onClick = { viewModel.emit(Intent.OnSubmit) },
            enabled = !viewState.isLoading
        ) {
            Text(if (viewState.isLoading) "Loading..." else "Login")
        }
    }
}
```

---

## Rules

- **Contract Pattern**: Keep Intent, Result, ViewState in one object
- **Reducers are pure**: No side effects, no async
- **ViewState is immutable**: Use `data class` with `copy()`
- **Use `filterIsInstance` + `merge`**: Clean intent routing in Interactor
- Works with kotlin-inject (`@Inject constructor`)
