---
name: mvi
description: Use when implementing screen architecture, view models, unidirectional data flow, Intent-Result-State-Effect patterns, or any MVI/Elm-style architecture in a KMP Compose project. This is the Synapse IRSE-MVI framework.
user-invocable: true
---

# ui:mvi — IRSE-MVI Architecture

**Module**: `ui:mvi` | **Artifact**: `com.ribads.synapse:ui-mvi`
**Packages**: `com.ribads.synapse.ui.mvi`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-mvi:<version>")
}
```

The lifecycle `ViewModel` that `LifecycleViewModel` extends (`org.jetbrains.androidx.lifecycle:lifecycle-viewmodel`) and the Compose runtime behind `state` are `api` dependencies of `ui:mvi`, so a module that declares a ViewModel needs neither of them separately.

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.ui.mvi.CollectAsEffect
import com.ribads.synapse.ui.mvi.FlowMviProcessor
import com.ribads.synapse.ui.mvi.FlowViewModelArgs
import com.ribads.synapse.ui.mvi.IntentFlowHolder
import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.LifecycleViewModel
import com.ribads.synapse.ui.mvi.MviLogging
import com.ribads.synapse.ui.mvi.MviProcessor
import com.ribads.synapse.ui.mvi.OnFirstComposition
import com.ribads.synapse.ui.mvi.Reducer
import com.ribads.synapse.ui.mvi.Reduction
import com.ribads.synapse.ui.mvi.ScheduledIntent
import com.ribads.synapse.ui.mvi.SharedIntentFlowHolder
import com.ribads.synapse.ui.mvi.noEffects
import com.ribads.synapse.ui.mvi.withEffect
import com.ribads.synapse.ui.mvi.withEffects
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

    // Public extension point for supplying a ViewModel's pipeline.
    // Its members are internal — subtype it inside the module (see FlowViewModelArgs).
    abstract class ViewModelArgs<Intent, Result, ViewState, Effect>
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

object MviLogging {
    var isEnabled: Boolean = false   // read once per LifecycleViewModel, at construction
}
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
fun <Intent> LifecycleViewModel<Intent, *, *, *>.OnFirstComposition(
    vararg intents: Intent,
    delay: Duration = Duration.ZERO
)

@Composable
fun <Intent> LifecycleViewModel<Intent, *, *, *>.OnFirstComposition(
    vararg intents: ScheduledIntent<Intent>
)

data class ScheduledIntent<out Intent>(
    val intent: Intent,
    val delay: Duration = Duration.ZERO  // throws IllegalArgumentException when negative
)

@Composable
fun <Effect> Flow<Effect>.CollectAsEffect(onEffect: suspend (Effect) -> Unit)
```

---

## Data Flow

```
  Screen ──emit(Intent)──► Interactor ──► UseCase ──► domain result
                               │                          │
                               │                    Mapper.toResult
                               │                          │
                               ◄──────── Result ──────────┘
                               │
                               ▼
                            Reducer ──► Reduction(ViewState, List<Effect>)
                                             │
                                   ┌─────────┴─────────┐
                                   ▼                   ▼
                        state: State<ViewState>   effects: Flow<Effect>
                          (rendered by Screen)     (consumed once)
```

| Piece | Owns | Must never |
|---|---|---|
| **Screen** | Rendering `viewState`, emitting `Intent`s, consuming `Effect`s | Build models, format text, branch on domain data |
| **Interactor** | Calling UseCases, orchestrating async, routing intents | Build UI models, hold state, mutate state |
| **Mapper** | domain result → `Result`; `Intent` (+ state) → `Result`; all `Clause` / `Image` / `NavigationCommand` construction; validation | Call a UseCase or Repository, suspend, hold state |
| **Reducer** | `(ViewState, Result) → Reduction` | Do I/O, derive or merge data, branch on a `Result`'s *field values* |

- **State** is durable: it is exactly what is on screen, and it survives recomposition.
- **Effects** are one-shot and fire-and-forget. See [Effect delivery](#effect-delivery) for what that costs you.
- The Interactor receives the current `StateFlow` so processors read the latest state instead of smuggling it through Intents.

`Mapper` is **not** a framework type; `ui:mvi` ships no `Mapper`. It is a per-screen interface declared inside the Contract and implemented in `{Name}Mapper.kt`. `/synapse:create-screen` generates both.

---

## The Contract

One `internal object {Name}Contract` with five members, **in this order**. `/synapse:create-screen` generates exactly this shape. Keep the order, so every screen in the app reads the same way.

```kotlin
internal object LoginContract {

    interface Mapper {                                                              // 1
        fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded
        fun toResult(intent: Intent.Navigation): Result.NavigationRequested
        fun toResult(intent: Intent.OnEmailChanged, state: ViewState): Result.OnEmailUpdated
        fun toResult(result: LoginResult): Result
        fun toInput(state: ViewState): LoginUseCaseInput
    }

    sealed class Intent {                                                           // 2
        data object LoadInitialData : Intent()
        sealed class Navigation : Intent() { data object Back : Navigation() }
        data class OnEmailChanged(val value: String) : Intent()
        data object OnSubmitClick : Intent()
    }

    sealed class Result {                                                           // 3
        data object OnInitialDataLoaded : Result()
        data class NavigationRequested(val command: NavigationCommand) : Result()
        data class OnEmailUpdated(val email: TextInputModel, val submitState: ButtonState) : Result()
        data class OnSubmitStateUpdated(val submitState: ButtonState) : Result()
        data class OnLoginFailed(val toast: ToastModel) : Result()
    }

    sealed class Effect {                                                           // 4
        data class Navigate(val command: NavigationCommand) : Effect()
        data class ShowToast(val model: ToastModel) : Effect()
    }

    @Immutable
    data class ViewState(                                                           // 5
        val email: TextInputModel,
        val submit: ButtonModel,
        val submitState: ButtonState,
    ) {
        companion object {
            val Default = ViewState(
                email = TextInputModel(
                    label = "Email".asText(),
                    value = "",
                    placeholder = "you@example.com".asText(),
                ),
                submit = ButtonModel(title = "Log in".asText()),
                submitState = ButtonState.Disabled,
            )
        }
    }
}
```

### Intent: one per user interaction

Name for what the *user did*, not for what should happen: `OnSubmitClick`, not `PerformLogin`. Conventional prefixes: `On*` for interactions, `LoadInitialData` for bootstrap, and a nested sealed group (`Navigation`, `FormInput`, `BottomSheet`) when a family of intents shares one reducer arm.

### Result: one focused delta

- **Carry only the fields the triggering intent changes.** The reducer's `state.copy()` already preserves everything else.
- **No god result** shared across unrelated intents, and **no `state.x` pass-through**. A field that only echoes current state back is dead weight and obscures which intent owns which field.
- **A no-op returns `null` from the Mapper**, paired with `mapNotNull` in the Interactor. Never emit a Result that reduces to an equal state.
- Name them `On<Thing>Updated` / `On<Thing>Loaded` / `On<Thing>Failed`.
- Nest variants in a sealed sub-class only for a multi-field form with its own sub-reducer arm; otherwise declare them flat on `Result`.

### Effect vs. a nullable `ViewState` field

The distinction that trips people up:

| The thing | Where it lives | Why |
|---|---|---|
| Navigate, toast, clipboard, share sheet | `Effect` | Fires once and leaves nothing on screen |
| Dialog, bottom sheet, popup, picker that stays open | Nullable `ViewState` field + a dismiss `Intent` | It **is** on screen; it must survive recomposition and be re-rendered |

```kotlin
viewState.confirmDialog?.let {
    ConfirmDialog(
        model = it,
        onConfirm = { viewModel.emit(Intent.OnConfirmDialog) },
        onCancel = { viewModel.emit(Intent.OnDismissDialog) },
    )
}
```

Routing a dialog through `Effect` loses it on the next recomposition. Keep `Effect` small: `Navigate` and `ShowToast` cover almost everything; add a third only for a genuinely stateless platform action.

### ViewState: models, not primitives

- **Fields are component models** (`TextInputModel`, `ButtonModel`, `TopNavBarModel`, your own `@Immutable` app models), not raw `String` / `Boolean` the composable would have to interpret. Primitives appear only as flags and opaque identifiers (`selectedId: String?`, `nextPageToken: String?`).
- **`@Immutable` and `companion object { val Default }` on every ViewState.**
- **`Default` is a renderable first frame**, not zeroes: real labels, and `Placeholder` variants for content still loading, so the first composition shows a skeleton instead of an empty screen.
- **Model loading and emptiness as sealed variants, not booleans:**

```kotlin
internal sealed class FeedSection {
    @Immutable data class Items(val items: List<FeedItem>) : FeedSection()
    @Immutable data class Empty(val model: EmptyStateModel) : FeedSection()
}

@Immutable
internal sealed class FeedItem {
    data class Item(val id: String, val title: Clause) : FeedItem()
    data class Placeholder(val id: String) : FeedItem()   // rendered with Modifier.shimmer()
}
```

`isLoading: Boolean` beside `items: List<T>` beside `error: String?` makes eight states representable when only three are legal. A sealed section makes the illegal ones unrepresentable and collapses the Screen to a single `when`.

---

## The Mapper

A per-screen, pure translation layer. It is the only place domain types become UI types.

```kotlin
internal class LoginMapper @Inject constructor() : Mapper {

    override fun toResult(intent: Intent.OnEmailChanged, state: ViewState): Result.OnEmailUpdated {
        val email = state.email.copy(value = intent.value, isError = false, footerText = null)
        return Result.OnEmailUpdated(email = email, submitState = email.value.toSubmitState())
    }

    override fun toResult(result: LoginResult): Result = when (result) {
        is LoginResult.Success -> Result.NavigationRequested(NavigationCommand.FeatureCommand(featureName = "home", clearStack = true))
        is LoginResult.InvalidCredentials -> Result.OnLoginFailed(
            toast = ToastModel(
                message = Text.Localized(Res.string.login_invalid_credentials),
                intent = ToastIntent.Error,
            ),
        )
    }

    override fun toInput(state: ViewState) = LoginUseCaseInput(email = state.email.value)

    private fun String.toSubmitState() =
        if (contains("@")) ButtonState.Enabled else ButtonState.Disabled
}
```

**The Mapper owns:** domain result → `Result` (including turning a typed domain failure into user-facing copy); `Intent` (+ current `ViewState`) → `Result` for form and derived updates; `ViewState` → UseCase input; and every `Clause`, `Image`, `ToastModel`, `NavigationCommand`, and validation decision on the screen.

**The Mapper must not** inject a UseCase or Repository, suspend, return `Flow`, hold mutable state, or be `@Composable`. Its only legal dependencies are formatters and other mappers. That is what makes it testable with real data classes and no mocks.

Return `Result?` for an intent that legitimately changes nothing, and pair it with `mapNotNull` in the Interactor.

---

## The Interactor

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
internal class LoginInteractor @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val mapper: Mapper,
) : Interactor<Intent, Result, ViewState> {

    private fun submitProcessor(
        upstream: Flow<Intent.OnSubmitClick>,
        state: StateFlow<ViewState>,
    ): Flow<Result> = upstream.flatMapConcat {
        flow { emit(loginUseCase.execute(mapper.toInput(state.value))) }
            .map(mapper::toResult)
            .onStart { emit(Result.OnSubmitStateUpdated(ButtonState.Loading)) }
            .onCompletion { emit(Result.OnSubmitStateUpdated(ButtonState.Enabled)) }
    }

    override fun process(intents: Flow<Intent>, state: StateFlow<ViewState>): Flow<Result> = merge(
        intents.filterIsInstance<Intent.LoadInitialData>().map(mapper::toResult),
        intents.filterIsInstance<Intent.Navigation>().map(mapper::toResult),
        intents.filterIsInstance<Intent.OnEmailChanged>().map { mapper.toResult(it, state.value) },
        intents.filterIsInstance<Intent.OnSubmitClick>().let { submitProcessor(it, state) },
    )
}
```

### Processor convention

Handlers are `private fun {verb}Processor(upstream: Flow<Intent.Specific>, state: StateFlow<ViewState>): Flow<Result>`:

- named `*Processor`, and **declared above `process()`** so `process()` lands last and reads as the screen's table of contents
- the parameter is named `upstream` and typed to the **narrowest** intent, never `Flow<Intent>`
- take `state` only when current state is genuinely needed, and read `state.value` inside the operator
- **never** smuggle state through an Intent so a processor can avoid the parameter

### Registering intents

`process()` is a single `merge(...)`. Four idioms, in increasing weight:

```kotlin
intents.filterIsInstance<Intent.Navigation>().map(mapper::toResult),                        // pure mapper
intents.filterIsInstance<Intent.OnEmailChanged>().map { mapper.toResult(it, state.value) }, // mapper + state
intents.filterIsInstance<Intent.OnDismissDialog>().map { Result.OnDialogUpdated(null) },    // inline trivial
intents.filterIsInstance<Intent.OnSubmitClick>().let { submitProcessor(it, state) },        // processor
```

**Register each intent type exactly once.** A second `filterIsInstance<Intent.X>()` in the same `merge` creates a second observer, so one tap produces two Results and two Effects: a duplicated navigation or a double-charged request. When one intent must fan out, fan out *inside* its single registration:

```kotlin
intents.filterIsInstance<Intent.LoadInitialData>().let {
    merge(loadProfileProcessor(it), loadFeedProcessor(it), it.map(mapper::toResult))
},
```

Streams not driven by an intent (repository observers, connectivity) merge in bare, with no `filterIsInstance`:

```kotlin
favouriteChangesProcessor(state),
```

### Choosing the flattening operator

| Operator | Use for | Because |
|---|---|---|
| `flatMapLatest` | loads, refreshes, search-as-you-type, retry | a newer trigger should cancel the in-flight one |
| `flatMapConcat` | form submits, toggles, send-message, load-next-page | every trigger must complete; dropping one loses work |
| `flatMapMerge` | independent parallel fetches off one trigger | they don't depend on each other, so run them concurrently |

This is a correctness choice, not a style one. `flatMapLatest` on a submit button silently drops the first submission when the user double-taps; `flatMapConcat` on a search field queues every keystroke and renders stale results.

### Loading states

Always `onStart` / `onCompletion`, never an imperative set-then-clear:

```kotlin
.onStart { emit(Result.OnSubmitStateUpdated(ButtonState.Loading)) }
.onCompletion { emit(Result.OnSubmitStateUpdated(ButtonState.Enabled)) }
```

`onCompletion` fires on success, failure, **and cancellation**. A terminal `.map` does not, so a cancelled request leaves the button spinning forever.

### Staying declarative

- **Bridge suspend → Flow with `flow { emit(useCase.execute(...)) }`.** Use observing UseCases directly.
- **Never call `.collect { }` on the intent stream.** A manual collect inside a `flow { }` builder reintroduces exactly the cancellation bugs the operators handle for you.
- **A mapper returning `List<Result>` flattens with `.asFlow()`**, not a hand-rolled loop:

```kotlin
.flatMapConcat { mapper.toResults(it).asFlow() }   // not: flow { mapper.toResults(it).forEach { emit(it) } }
```

- **Complex branching goes in a `private suspend fun` returning `List<Result>`**, bridged back with `.asFlow()`. The processor stays a readable pipeline and the imperative part becomes an ordinary testable function.

---

## The Reducer

```kotlin
internal class LoginReducer @Inject constructor() : Reducer<ViewState, Result, Effect> {
    override fun reduce(state: ViewState, result: Result): Reduction<ViewState, Effect> =
        when (result) {
            is Result.OnInitialDataLoaded -> state.noEffects()
            is Result.OnEmailUpdated -> state.copy(
                email = result.email,
                submitState = result.submitState,
            ).noEffects()
            is Result.OnSubmitStateUpdated -> state.copy(submitState = result.submitState).noEffects()
            is Result.OnLoginFailed -> state withEffect Effect.ShowToast(result.toast)
            is Result.NavigationRequested -> state withEffect Effect.Navigate(result.command)
        }
}
```

- **Exhaustive `when (result)`, no `else`.** A newly added Result must break the build until it is handled.
- **`state.copy(...)` only.** No mutation, no I/O, no suspend, no injected collaborators. The constructor stays empty.
- **Dispatch on the result's *type*, never on its *field values*.** No `when (result.status)`, no `if (result.items.isEmpty())`, no `result.x ?: state.x`. Each of those is data shaping, and shaping belongs in the Mapper where it is pure and testable on its own.
- **A nested `when` is fine only for a nested sealed `Result` sub-class**, which is still type dispatch.
- One arm may both change state and emit an effect: `state.copy(...) withEffect Effect.Navigate(...)`.
- Merging in an arm is the one grey area. Append-pagination (`state.copy(items = state.items + result.page)`) is acceptable when the merge is a genuine operator on the UI model. Anything conditional is not.

> Reducers stay pure. Side effects (navigate, toast, analytics) leave via the Effect channel, never via state mutation.

---

## The ViewModel

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

---

## The Screen

```kotlin
@Composable
internal fun LoginScreen(
    viewModel: LoginViewModel,
    navigationDispatcher: NavigationDispatcher,
) {
    val viewState by viewModel.state
    val toaster = Toast.current

    viewModel.OnFirstComposition(Intent.LoadInitialData)

    viewModel.effects.CollectAsEffect { effect ->
        when (effect) {
            is Effect.Navigate -> navigationDispatcher.navigateTo(effect.command)
            is Effect.ShowToast -> toaster.show(effect.model)
        }
    }

    Scaffold { padding ->
        Column(
            modifier = Modifier.padding(padding).padding(horizontal = Theme.spacing.x6),
            verticalArrangement = Arrangement.spacedBy(Theme.spacing.x4),
        ) {
            TextField(
                model = viewState.email,
                modifier = Modifier.fillMaxWidth(),
                onValueChange = { viewModel.emit(Intent.OnEmailChanged(it)) },
            )
            PrimaryButton(
                model = viewState.submit,
                modifier = Modifier.fillMaxWidth(),
                state = viewState.submitState,
                onClick = { viewModel.emit(Intent.OnSubmitClick) },
            )
        }
    }
}
```

**Body order, identical on every screen:**

1. `val viewState by viewModel.state`
2. CompositionLocals (`Toast.current`): read at composable scope, never inside the effect lambda
3. `viewModel.OnFirstComposition(Intent.LoadInitialData)`
4. `viewModel.effects.CollectAsEffect { }`
5. nullable overlays: `viewState.dialog?.let { }`
6. `Scaffold { }`

**The Screen renders and emits, nothing else.** No `Clause` construction, no `stringResource`, no string templates, no money or date formatting, no branching on domain data. If a composable has to decide something, that decision belonged in the Mapper. The only logic that earns its place here is a `when` over a sealed UI model, and even that usually delegates to a section composable.

`viewModel.state` is a Compose `State<ViewState>`, so `by viewModel.state` is all you need. Wrapping it in `remember { derivedStateOf { viewModel.state.value } }` adds a layer that buys nothing.

### Emitting an initial intent

```kotlin
@Composable
fun MyScreen(viewModel: MyViewModel) {
    viewModel.OnFirstComposition(Intent.LoadInitialData)
    // ...
}
```

This replaces the old `if (viewModel.isFirstIntent) viewModel.emit(...)` pattern. `OnFirstComposition` emits the intents **exactly once per ViewModel lifetime**. The guard lives on the `LifecycleViewModel`, not the composition, so navigating away and returning (ViewModel retained by the nav back stack) will **not** re-emit. A fresh ViewModel instance (e.g. after `onCleared`) emits again.

### Delaying initial intents

One delay for every intent:

```kotlin
viewModel.OnFirstComposition(Intent.ShowOnboardingHint, delay = 250.milliseconds)
```

A delay per intent:

```kotlin
viewModel.OnFirstComposition(
    ScheduledIntent(Intent.LoadInitialData),
    ScheduledIntent(Intent.ShowOnboardingHint, delay = 250.milliseconds),
    ScheduledIntent(Intent.StartPulse, delay = 600.milliseconds),
)
```

Use a delay to hold an intent back until the screen has been composed for that long, for example to let an enter transition settle before a hint, a keyboard request, or an animation-driving state change. The two overloads share one set of rules, since the single-`delay` form is the same schedule with every intent at that offset:

- **Every delay is an offset from first composition, not from the previous intent.** Above, `StartPulse` fires at 600ms, not 850ms. Argument order does not change timing; intents with equal delays fire in argument order.
- **The schedule is tied to the composition.** It runs inside the `LaunchedEffect`, so leaving composition cancels whatever has not fired yet.
- **Each intent fires once per ViewModel lifetime.** Intents that already fired stay fired. On the next first composition of the same ViewModel, only the pending ones run, each measured from that new composition. Leaving at 300ms above means `StartPulse` fires 600ms after the return.
- **Progress is tracked by position in the schedule**, so pass the same schedule on every composition and call `OnFirstComposition` once per screen.
- **`Duration.ZERO` (the default) fires immediately.** A negative delay throws `IllegalArgumentException` when the `ScheduledIntent` is created.

Don't use a delay to wait for data or to dodge a race with another intent. Sequence that in the Interactor; a fixed timer only hides the ordering problem.

---

## Effect delivery

`effects` is a `MutableSharedFlow(extraBufferCapacity = 64)` with **`replay = 0`**, emitted with `tryEmit`. Two consequences worth designing around:

- **An effect emitted while nothing is collecting is dropped.** `CollectAsEffect` subscribes on first composition and intents only flow from the Screen, so this is safe for user-driven effects. It is *not* safe for an effect emitted from a stream that starts at construction time.
- **`tryEmit` returns `false` when the 64-slot buffer is full, and the return value is ignored.** Emitting effects in a tight loop can silently lose some.

Both are further reasons that anything which must stay visible belongs in `ViewState`, not in an `Effect`.

---

## Error Handling

`FlowViewModelArgs` accepts an `onPipelineError: (Throwable) -> Unit` callback that fires whenever the upstream `Interactor` flow throws OR whenever the `Reducer` throws. The pipeline **recovers automatically**: subsequent intents continue to flow, and the current state is kept in both cases.

The two recoveries cost different things:

- **The reducer throws**: only that `Result` is lost. The state stays as it was and the pipeline carries on.
- **The interactor's flow throws**: the whole flow `process()` returns, every processor merged into it, is collected again from the start. That restarts all of them, not just the one that failed: in-flight work in the other processors (a load, an upload) is cancelled and is not resumed, observers that start on collection (a repository's `observe…()` flow, an `onStart { }`) subscribe again and re-emit, and intents sent while it resubscribes are dropped. The retry is immediate and has no limit, so a flow that throws every time it is collected retries in a tight loop, reporting each failure to `onPipelineError`.

So `onPipelineError` is a last line of defence for bugs, not error handling. Expected failures never reach it: the repository catches and returns a failure variant (see `/synapse:data-boundaries`), the use case passes it up as a value, and the processor maps it to a `Result` like any other outcome. A throw that does reach the interactor costs the whole screen its in-flight work, which is one more reason nothing above the repository should throw.

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

## Debug tracing

`MviLogging` prints every screen's Intent → Result → Effect flow, plus pipeline errors, one line per event. It is off by default. The app switches it on at startup, guarded by its own debug check, because a published Synapse artifact cannot see the app's build type:

```kotlin
// androidApp, MainActivity.onCreate (needs buildFeatures { buildConfig = true })
MviLogging.isEnabled = BuildConfig.DEBUG

// composeApp, iosMain MainViewController
@OptIn(ExperimentalNativeApi::class)
MviLogging.isEnabled = Platform.isDebugBinary
```

`MviLogging` lives in `ui-mvi`, so the module that sets it (usually `androidApp`) needs `ui-mvi` on its own classpath; `composeApp`'s `implementation` dependency does not reach it.

Output is tagged with the ViewModel's class name. The value is the type's `toString()`:

```
LoginViewModel  Intent  OnEmailChanged(value=a@b.co)
LoginViewModel  Result  OnEmailUpdated(email=..., submitState=Enabled)
LoginViewModel  Intent  OnSubmitClick
LoginViewModel  Result  OnSubmitStateUpdated(submitState=Loading)
LoginViewModel  Effect  Navigate(command=FeatureCommand(featureName=home, clearStack=true))
LoginViewModel  Error   java.lang.IllegalStateException: boom
```

| Platform | Where | Filter |
|---|---|---|
| Android | Logcat, tag `MVI`; `Error` lines at error priority with the stack trace | `adb logcat -s MVI` |
| iOS | Xcode console via `println`, prefixed `[MVI]` | `[MVI]` in the console filter |

- **Read at ViewModel construction.** Flipping the flag later only affects ViewModels created afterwards. When it's off, nothing is wrapped and events cost nothing.
- **Each event is traced once.** Intents are traced as they're emitted, not per `filterIsInstance` registration, so fanning out inside the Interactor doesn't duplicate lines.
- **Errors are traced and still reach `onPipelineError`.** That includes the default `{}`, which otherwise swallows them silently.
- **ViewState is not traced.** Results already carry each delta.
- **Raw user input is printed.** A `data class` Intent such as `OnPasswordChanged(value=...)` prints its value. Keep the flag debug-only, and override `toString()` on any Intent or Result whose payload must never reach a log.

---

## Rules

**Contract**
- Keep `Mapper`, `Intent`, `Result`, `Effect`, `ViewState` in one `internal object`, in that order.
- `ViewState` is `@Immutable` with a `companion object { val Default }`; `Default` renders a real first frame.
- `ViewState` fields are component models, not primitives the composable has to interpret.
- Loading and emptiness are sealed variants of a section model, not `Boolean` flags beside a list.

**Result**
- One focused delta per Result: only the fields its intent changes. No god result, no `state.x` pass-through.
- A no-op returns `null` from the Mapper and is filtered with `mapNotNull`.

**Effect**
- One-shot only: navigate, toast, clipboard. Anything that stays on screen is a nullable `ViewState` field plus a dismiss intent.
- Effects can be dropped if nothing is collecting, so never make them load-bearing for what is rendered.

**Mapper**
- Owns every domain → UI translation, all `Clause` / `Image` / `NavigationCommand` construction, and all validation.
- Pure: no UseCase, no Repository, no suspend, no `Flow`, no state, never `@Composable`.

**Interactor**
- `process()` is one `merge(...)`, declared last; processors sit above it.
- Processors are `*Processor(upstream: Flow<Intent.Specific>, state: StateFlow<ViewState>)` and read `state.value`. Never accept state through an Intent.
- Register each intent type exactly once; fan out inside that single registration.
- `flatMapLatest` cancels, `flatMapConcat` queues, `flatMapMerge` parallelises. Choose deliberately.
- Loading states use `onStart` / `onCompletion` so cancellation still clears them.
- Never `.collect { }` an intent stream; flatten `List<Result>` with `.asFlow()`.

**Reducer**
- Pure `(State, Result) → Reduction`. Exhaustive `when` on the Result *type*, `state.copy()`, no `else`.
- Never branch on a Result's field values, and never derive or merge data in an arm.

**Screen**
- Renders `viewState` and emits `Intent`s. No model construction, no formatting, no domain branching.
- Read `viewModel.state` directly with `by`; it is already a Compose `State`.

Works with kotlin-inject (`@Inject constructor`) throughout. See `/synapse:build-screen` for the end-to-end workflow, `/synapse:data-boundaries` for what may cross each layer, and `/synapse:component-authoring` for building the models these rules assume.
