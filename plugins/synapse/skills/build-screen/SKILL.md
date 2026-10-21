---
name: build-screen
description: Use when building, implementing, or wiring up a new screen end-to-end in a Synapse-based KMP app. Orchestrates component selection, `/synapse:create-screen` scaffolding, and IRSE-MVI wiring (Contract, Mapper, Interactor, Reducer, Screen). For scaffold-only with no wiring, use `/synapse:create-screen` instead.
user-invocable: true
---

# build-screen — End-to-End Screen Build Workflow

Orchestration recipe for turning a screen requirement into a working IRSE-MVI screen. Drives `/synapse:create-screen` for the 7-file scaffold, then fills it in using Synapse UI component models. This skill deliberately defers API details to its sister skills — invoke those only when you need a specific signature.

## When to invoke

- "Build / implement / add a `<Name>` screen" (e.g. *"add a login screen"*, *"implement the checkout screen"*).
- Not for pure scaffold only — call `/synapse:create-screen` directly.
- Not for edits to an existing screen — read its `Contract` and edit.

## Sister skills (defer, don't duplicate)

| Need | Skill |
|---|---|
| Component signatures, component catalog | `/synapse:ui-components` |
| `Clause`, `Text`, `Image`, `Icon`, `Theme`, `asText()` | `/synapse:ui-element` |
| Contract shape, Mapper/Interactor/Reducer rules | `/synapse:mvi` |
| `NavigationCommand`, `NavigationDispatcher`, typed routes | `/synapse:navigation` |
| Writing a composable Synapse doesn't ship | `/synapse:component-authoring` |
| What may cross a layer; UseCase and error contracts | `/synapse:data-boundaries` |
| The scaffolding script | `/synapse:create-screen` |

---

## Workflow (run in order)

1. **Clarify requirements.** Screen name, package, what it renders, what it interacts with (UseCases). Ask the user if missing.
2. **Pick components.** Match each UI element to a Synapse component using the picker below. Only reach for a custom composable after step-6's rules.
3. **Scaffold.** Run `/synapse:create-screen` with `--name`, `--package`, `--src|--dir`, and `--use-case-provider` if any UseCase is needed. That creates the 7 files with sensible defaults.
4. **Fill `Contract`.** Add one `Intent.*` per user interaction, one `Result.*` per state change or nav, one `Effect.*` per one-shot (nav/toast). Declare `ViewState` with the component models picked in step 2. Build initial values in `ViewState.Default` inside the `companion object`.
5. **Wire `Mapper` → `Interactor` → `Reducer`.** Use the interaction matrix. Processors (`{verb}Processor`, e.g. `submitProcessor`) go **above** `process()`, take `Flow<Intent.SpecificType>` (plus `StateFlow<ViewState>` only if state is needed).
6. **Compose `Screen.kt`.** Body order is the same on every screen:

   ```
   val viewState by viewModel.state          // 1. state
   val toaster = Toast.current               // 2. CompositionLocals, at composable scope
   viewModel.OnFirstComposition(Intent.LoadInitialData)   // 3. bootstrap
   viewModel.effects.CollectAsEffect { }     // 4. one-shot effects
   viewState.dialog?.let { }                 // 5. nullable overlays
   Scaffold { }                              // 6. body
   ```

   The Screen consumes `viewState.<model>` fields and emits intents on events. No model construction, no `stringResource`, no formatting, no branching on domain data.

After wiring, the consumer still has to: register the `{Name}UiComponent` in the feature's `ViewModelComponent`, declare the `@Serializable` `NavKey` route, and register `entry<{Name}Route>` in the feature's `FeatureLauncher.register` plus its `serializers` module. Call that out in the final summary to the user.

---

## Component picker

Use this table to go from need → Synapse composable + model. For composable signatures and model fields, invoke `/synapse:ui-components` (each row's reference file).

| Need | Composable | Model on `ViewState` |
|---|---|---|
| Primary CTA / small CTA | `PrimaryButton` / `SmallButton` | `ButtonModel` (+ `ButtonState` as separate field if loading/disabled toggles) |
| Outlined action | `OutlineButton` / `SmallOutlineButton` | `ButtonModel` |
| Text entry | `TextField` | `TextInputModel` (+ `FieldState` as separate field if read-only/disabled toggles) |
| Password | `PasswordTextField` | `TextInputModel` |
| Phone | `PhoneTextField` | `PhoneInputModel` |
| Currency | `CurrencyTextField` | `CurrencyInputModel` |
| Dropdown-style | `SelectionTextField` | `TextInputModel` |
| Dropdown menu | `DropdownSelectionField` | `SelectionFieldModel` |
| Multi-line | `TextArea` | `TextInputModel` |
| Date | `DatePicker` / `DatePickerBottomSheet` | `DatePickerModel` |
| Time | `TimePicker` | `TimePickerModel` |
| Checkbox / radio | `LabelCheckbox` / `RadioGroup` | `CheckboxModel` / `RadioGroupModel` |
| Chips / tabs | `ChipGroup` / `TabLayout` (`LiquidGlassTabLayout`) | `ChipGroupModel` / `TabLayoutModel` |
| Slider / stepper / rating | `Slider` / `Stepper` / `RatingInput` | `SliderModel` / `StepperModel` / `RatingInputModel` |
| Progress (linear / circular) | `ProgressBar` / `CircularProgress` | `ProgressBarModel` / `CircularProgressModel` |
| Timer | `Timer` | `TimerModel` |
| Top / bottom nav | `TopNavBar` / `BottomNavigationBar` (`LiquidGlassBottomNavigationBar`) | `TopNavBarModel` / `BottomNavigationBarModel` |
| Container | `Scaffold` / `Card` / `Divider` / `Tray` / `ScrollableTray` | — |
| Root of a `bottomSheet()` screen | `TraySurface` / `ScrollableTraySurface` (never `Tray`, which would open a second sheet) | — |
| Empty / dialog | `EmptyState` / `ConfirmDialog` | `EmptyStateModel` / `ConfirmDialogModel` |
| Charts | `BarChart` / `LineChart` / `PieChart` | `*ChartModel` |
| Chat | `ChatTextArea` / `MessageBubble` | `ChatTextAreaModel` / `MessageBubbleModel` |
| Toast / snackbar | `ToastHandler` at root + `Toast.current.show(model)` from any composable | `ToastModel` (passed via Effect, not stored in ViewState) |

For complex screen-specific compositions (feed cards, custom top-bars), wrap Synapse primitives in an app-level model inside the app's `compose-ui/` module. See `DiscoverSearchComponentModel` in the Outside reference app for the pattern.

---

## Model-location matrix (hard rule: never build models inside `@Composable`)

| Thing | Where it lives | Why |
|---|---|---|
| Component models (`ButtonModel`, `TextInputModel`, custom) | `ViewState` field | Durable, survives recomposition, rendered by composables |
| Initial labels / icons / placeholders | `ViewState.Default` (Contract `companion object`) | Static defaults |
| Dynamic models built from domain responses | `Mapper.toResult(...)` | Keeps Reducer pure, keeps Screen dumb |
| `Clause`, `Text.listOf`, `Graphics`, `Image` instances | `Mapper` or `ViewState.Default` | **Never** inside `@Composable` |
| Click/select lambdas | Inline in `Screen.kt` | Can't live in state |
| `ButtonState` (`Enabled` / `Disabled` / `Loading`) | `ViewState` field (separate from `ButtonModel`) | Passed as the `state =` param to the button composable |
| Loading / empty / error for one content area | A **sealed section model** on `ViewState` | Collapses the Screen to one `when`; illegal combinations become unrepresentable |
| Dialog, bottom sheet, picker that stays open | Nullable `ViewState` field + a dismiss `Intent` | It is on screen, so it must survive recomposition; an `Effect` is lost |
| Navigation, toast, clipboard | `Effect` | One-shot; nothing remains on screen afterwards |
| Money and dates | `Text.Money(minorUnits)` / `Text.Timestamp(millis)`, built in the `Mapper` | Formatted at render time with the right locale and time zone |

Do not put `isLoading: Boolean` next to `items: List<T>` next to `error: String?`. That makes eight states representable when three are legal. Model the area instead:

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

Seed `ViewState.Default` with `Placeholder`s so the first frame is a skeleton, not a blank screen. Synapse ships no loading-box or error-box component, so compose them from `Modifier.shimmer()` and `EmptyState`.

**Pagination:** keep `nextPageToken: String?` on `ViewState`, emit a load-next-page intent when the list nears its end, and append in the Reducer (`state.copy(items = state.items + result.page)`) or in the Mapper. Synapse ships no pagination helper.

---

## Interaction matrix

For each UI event, the changes you need across the five files. The Mapper builds every model and `NavigationCommand`; the Reducer only copies what the Result carries.

| UI event | Contract | Mapper | Interactor | Reducer | Screen |
|---|---|---|---|---|---|
| Text-field change | `Intent.OnXChanged(value: String)`, `Result.OnXUpdated(x: TextInputModel)` | `toResult(intent: Intent.OnXChanged, state: ViewState) = Result.OnXUpdated(state.x.copy(value = intent.value))` | `.map { mapper.toResult(it, state.value) }` | `state.copy(x = result.x).noEffects()` | `onValueChange = { viewModel.emit(Intent.OnXChanged(it)) }` |
| Toggle / checkbox | `Intent.OnXToggled(checked: Boolean)`, `Result.OnXUpdated(x: CheckboxModel)` | `Result.OnXUpdated(state.x.copy(checked = intent.checked))` | `.map { mapper.toResult(it, state.value) }` | `state.copy(x = result.x).noEffects()` | `onCheckedChange = { viewModel.emit(Intent.OnXToggled(it)) }` |
| Click → navigate | `Intent.OnItemClick(id: String)`, `Result.NavigationRequested(command)`, `Effect.Navigate(command)` | `toResult(intent: Intent.OnItemClick) = Result.NavigationRequested(ScreenCommand(DetailRoute(intent.id)))` | `.map(mapper::toResult)` | `state withEffect Effect.Navigate(result.command)` | `onClick = { viewModel.emit(Intent.OnItemClick(item.id)) }` |
| Show toast | `Result.OnXFailed(toast: ToastModel)`, `Effect.ShowToast(model: ToastModel)` | builds the `ToastModel` from the typed failure | (emitted by a processor via the Mapper) | `state withEffect Effect.ShowToast(result.toast)` | `val toaster = Toast.current` (outside the effect lambda); `is Effect.ShowToast -> toaster.show(effect.model)` |
| Click → async UseCase | `Intent.OnSubmitClick`, `Result.OnSubmitStateUpdated(submitState)` / `NavigationRequested(command)` / `OnLoginFailed(toast)` | `toInput(state)` for the UseCase input; `toResult(result: LoginResult)` for the outcome | `submitProcessor(upstream, state)`: `flatMapConcat { flow { emit(useCase.execute(mapper.toInput(state.value))) }.map(mapper::toResult).onStart { emit(Result.OnSubmitStateUpdated(ButtonState.Loading)) }.onCompletion { emit(Result.OnSubmitStateUpdated(ButtonState.Enabled)) } }` (`flatMapConcat`: a second tap must not cancel the first submit) | `state.copy(submitState = result.submitState).noEffects()`, `state withEffect Effect.Navigate(result.command)`, `state withEffect Effect.ShowToast(result.toast)` | `onClick = { viewModel.emit(Intent.OnSubmitClick) }` |
| Initial load | (scaffold) `Intent.LoadInitialData` | `toResult(result: FeedResult)` builds the section model | `loadInitialDataProcessor` calling the UseCase, then `.map(mapper::toResult)` | `state.copy(feed = result.feed).noEffects()` | `viewModel.OnFirstComposition(Intent.LoadInitialData)` |
| Back | (scaffold) `Intent.Navigation.Back` | (scaffold) `Result.NavigationRequested(NavigationCommand.BackCommand())` | (scaffold) `.map(mapper::toResult)` | `state withEffect Effect.Navigate(result.command)` | Back icon in `TopNavBar` emits the intent |

**Processor convention:** handlers are named `{verb}Processor` (`submitProcessor`, `loadInitialDataProcessor`), take `Flow<Intent.SpecificType>` (and `StateFlow<ViewState>` only if current state is needed), return `Flow<Result>`, and live **above** `process()`. Never pass state through intents; read `state.value` inside the processor.

---

## Worked example — Login screen

Goal: in the `auth` feature, an email field, a password field and a primary "Log in" button that call `LoginUseCase`. On success the app enters the `home` feature as the new root, so back does not return to login; on failure a toast says why.

Pick components: `TextField` + `PasswordTextField` + `PrimaryButton`. All three are Synapse primitives, so no custom composables are needed.

**UseCase result** (`features/auth/usecase`). The feature owns it; per `/synapse:data-boundaries` a UseCase never returns a domain entity result or `kotlin.Result`:

```kotlin
interface LoginUseCase {
    suspend fun execute(input: LoginUseCaseInput): LoginResult
}

data class LoginUseCaseInput(val email: String, val password: String)

sealed class LoginResult {
    data object Success : LoginResult()
    data object InvalidCredentials : LoginResult()
    data object Failure : LoginResult()
}
```

**Contract** (the scaffold plus the login members):

```kotlin
internal object LoginContract {

    interface Mapper {
        fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded
        fun toResult(intent: Intent.Navigation): Result.NavigationRequested
        fun toResult(intent: Intent.OnEmailChanged, state: ViewState): Result.OnEmailUpdated
        fun toResult(intent: Intent.OnPasswordChanged, state: ViewState): Result.OnPasswordUpdated
        fun toResult(result: LoginResult): Result
        fun toInput(state: ViewState): LoginUseCaseInput
    }

    sealed class Intent {
        data object LoadInitialData : Intent()
        sealed class Navigation : Intent() { data object Back : Navigation() }
        data class OnEmailChanged(val value: String) : Intent()
        data class OnPasswordChanged(val value: String) : Intent()
        data object OnSubmitClick : Intent()
    }

    sealed class Result {
        data object OnInitialDataLoaded : Result()
        data class NavigationRequested(val command: NavigationCommand) : Result()
        data class OnEmailUpdated(val email: TextInputModel) : Result()
        data class OnPasswordUpdated(val password: TextInputModel) : Result()
        data class OnSubmitStateUpdated(val submitState: ButtonState) : Result()
        data class OnLoginFailed(val toast: ToastModel) : Result()
    }

    sealed class Effect {
        data class Navigate(val command: NavigationCommand) : Effect()
        data class ShowToast(val model: ToastModel) : Effect()
    }

    @Immutable
    data class ViewState(
        val email: TextInputModel,
        val password: TextInputModel,
        val submit: ButtonModel,
        val submitState: ButtonState,
    ) {
        companion object {
            val Default = ViewState(
                email = TextInputModel(label = "Email".asText(), value = "", placeholder = "you@example.com".asText()),
                password = TextInputModel(label = "Password".asText(), value = "", placeholder = "••••••".asText()),
                submit = ButtonModel(title = "Log in".asText()),
                submitState = ButtonState.Enabled,
            )
        }
    }
}
```

**Mapper**: builds every model, toast and navigation command on the screen. The typed failure becomes copy here and nowhere else:

```kotlin
private val EnterHome = NavigationCommand.FeatureCommand(featureName = "home", clearStack = true)

private val InvalidCredentialsToast = ToastModel(
    message = Text.Localized(Res.string.login_invalid_credentials),
    intent = ToastIntent.Error,
)

private val LoginFailedToast = ToastModel(
    message = Text.Localized(Res.string.login_failed),
    intent = ToastIntent.Error,
)

internal class LoginMapper @Inject constructor() : Mapper {

    override fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded =
        Result.OnInitialDataLoaded

    override fun toResult(intent: Intent.Navigation): Result.NavigationRequested = when (intent) {
        Intent.Navigation.Back -> Result.NavigationRequested(NavigationCommand.BackCommand())
    }

    override fun toResult(intent: Intent.OnEmailChanged, state: ViewState): Result.OnEmailUpdated =
        Result.OnEmailUpdated(email = state.email.copy(value = intent.value))

    override fun toResult(intent: Intent.OnPasswordChanged, state: ViewState): Result.OnPasswordUpdated =
        Result.OnPasswordUpdated(password = state.password.copy(value = intent.value))

    override fun toResult(result: LoginResult): Result = when (result) {
        LoginResult.Success -> Result.NavigationRequested(EnterHome)
        LoginResult.InvalidCredentials -> Result.OnLoginFailed(toast = InvalidCredentialsToast)
        LoginResult.Failure -> Result.OnLoginFailed(toast = LoginFailedToast)
    }

    override fun toInput(state: ViewState): LoginUseCaseInput =
        LoginUseCaseInput(email = state.email.value, password = state.password.value)
}
```

`FeatureCommand` enters a feature by its `featureName`, so `features/auth/ui` never sees home's route types: they are `internal` to `features/home/ui`, and a feature can only share its `ui-api` types with another. `clearStack = true` makes home's start destination the only entry on the back stack. The name must match home's `FeatureLauncher.featureName`; an unknown name throws `IllegalArgumentException` when dispatched. `FeatureCommand` carries no arguments, so home reads the signed-in user from its own use case rather than from the route.

**Interactor**: a processor for submit, the mapper for everything else:

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
        intents.filterIsInstance<Intent.OnPasswordChanged>().map { mapper.toResult(it, state.value) },
        intents.filterIsInstance<Intent.OnSubmitClick>().let { submitProcessor(it, state) },
    )
}
```

**Reducer**: type dispatch and `state.copy()` only; the effects forward what the Mapper built:

```kotlin
internal class LoginReducer @Inject constructor() : Reducer<ViewState, Result, Effect> {
    override fun reduce(state: ViewState, result: Result): Reduction<ViewState, Effect> =
        when (result) {
            is Result.OnInitialDataLoaded -> state.noEffects()
            is Result.OnEmailUpdated -> state.copy(email = result.email).noEffects()
            is Result.OnPasswordUpdated -> state.copy(password = result.password).noEffects()
            is Result.OnSubmitStateUpdated -> state.copy(submitState = result.submitState).noEffects()
            is Result.OnLoginFailed -> state withEffect Effect.ShowToast(result.toast)
            is Result.NavigationRequested -> state withEffect Effect.Navigate(result.command)
        }
}
```

**Screen**:

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
            TextField(model = viewState.email, onValueChange = { viewModel.emit(Intent.OnEmailChanged(it)) })
            PasswordTextField(model = viewState.password, onValueChange = { viewModel.emit(Intent.OnPasswordChanged(it)) })
            PrimaryButton(model = viewState.submit, state = viewState.submitState, onClick = { viewModel.emit(Intent.OnSubmitClick) })
        }
    }
}
```

`Toast.current` throws unless a `ToastHandler` encloses the screen. Install one once at the app root, inside the theme.

---

## Custom composable escape hatch

Before writing any new `@Composable`, in order:

1. Check the component picker — is there a direct match?
2. Can Synapse primitives be composed (e.g. `Card` + `Image` + `Text`)?
3. Does the app's `compose-ui/` module already have a wrapper?

If one is still needed, invoke `/synapse:component-authoring`. It covers where the file goes, parameter order, callback naming, model design, and colour roles. The short version: put it in `compose-ui/` if a second screen could use it and in the feature's `section/` package otherwise, give it a model built in the Mapper, keep it stateless, and never inline a multi-element composable into `{Name}Screen.kt`.

---

## Definition of done

Before reporting the screen as built, check every line:

**Contract**
- [ ] Members in order: `Mapper`, `Intent`, `Result`, `Effect`, `ViewState`
- [ ] `ViewState` is `@Immutable` with `companion object { val Default }`, and `Default` renders a real first frame
- [ ] `ViewState` fields are component models, not primitives the composable must interpret
- [ ] Loading/empty modelled as sealed section variants, not `Boolean` flags
- [ ] Each `Result` carries only what its intent changes, with no `state.x` pass-through

**Mapper**
- [ ] Every `Clause`, `Image`, `ToastModel`, and `NavigationCommand` on the screen is built here
- [ ] No UseCase, Repository, `suspend`, `Flow`, or `@Composable` in sight

**Interactor**
- [ ] Every intent type registered exactly once inside one `merge(...)`
- [ ] Processors named `*Processor`, typed to the narrowest intent, declared above `process()`
- [ ] `flatMapLatest` vs `flatMapConcat` chosen deliberately per the `/synapse:mvi` table
- [ ] Loading states use `onStart` / `onCompletion`

**Reducer**
- [ ] Exhaustive `when` on the Result type with no `else`, `state.copy()` only
- [ ] No branching on a Result's field values, no data derived in an arm

**Screen**
- [ ] Body order: state → CompositionLocals → `OnFirstComposition` → `CollectAsEffect` → overlays → `Scaffold`
- [ ] No `stringResource`, no string templates, no model construction, no domain branching
- [ ] Every colour, size, and type value comes from `Theme.*`

**Wiring**
- [ ] `{Name}UiComponent` registered in the feature's `ViewModelComponent`
- [ ] `@Serializable` `NavKey` route declared, registered in `FeatureLauncher.register` and in its `serializers`
- [ ] Builds on both platforms: `./gradlew :<module>:compileAndroidMain :<module>:compileKotlinIosSimulatorArm64`
