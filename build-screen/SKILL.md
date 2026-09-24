---
name: build-screen
description: Use when building, implementing, or wiring up a new screen end-to-end in a Synapse-based KMP app. Orchestrates component selection, `/create-screen` scaffolding, and IRSE-MVI wiring (Contract, Mapper, Interactor, Reducer, Screen). For scaffold-only with no wiring, use `/create-screen` instead.
user-invocable: true
---

# build-screen — End-to-End Screen Build Workflow

Orchestration recipe for turning a screen requirement into a working IRSE-MVI screen. Drives `/create-screen` for the 7-file scaffold, then fills it in using Synapse UI component models. This skill deliberately defers API details to its sister skills — invoke those only when you need a specific signature.

## When to invoke

- "Build / implement / add a `<Name>` screen" (e.g. *"add a login screen"*, *"implement the checkout screen"*).
- Not for pure scaffold only — call `/create-screen` directly.
- Not for edits to an existing screen — read its `Contract` and edit.

## Sister skills (defer, don't duplicate)

| Need | Skill |
|---|---|
| Component signatures, component catalog | `/ui-components` |
| `Clause`, `Text`, `Image`, `Icon`, `Theme`, `asText()` | `/ui-element` |
| Contract shape, Mapper/Interactor/Reducer rules | `/mvi` |
| `NavigationCommand`, `NavigationDispatcher`, typed routes | `/navigation` |
| Writing a composable Synapse doesn't ship | `/component-authoring` |
| What may cross a layer; UseCase and error contracts | `/data-boundaries` |
| The scaffolding script | `/create-screen` |

---

## Workflow (run in order)

1. **Clarify requirements.** Screen name, package, what it renders, what it interacts with (UseCases). Ask the user if missing.
2. **Pick components.** Match each UI element to a Synapse component using the picker below. Only reach for a custom composable after step-6's rules.
3. **Scaffold.** Run `/create-screen` with `--name`, `--package`, `--src|--dir`, and `--use-case-provider` if any UseCase is needed. That creates the 7 files with sensible defaults.
4. **Fill `Contract`.** Add one `Intent.*` per user interaction, one `Result.*` per state change or nav, one `Effect.*` per one-shot (nav/toast). Declare `ViewState` with the component models picked in step 2. Build initial values in `ViewState.Default` inside the `companion object`.
5. **Wire `Mapper` → `Interactor` → `Reducer`.** Use the interaction matrix. Processors (`on*Processor`) go **above** `process()`, take `Flow<Intent.SpecificType>` (plus `StateFlow<ViewState>` only if state is needed).
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

Use this table to go from need → Synapse composable + model. For composable signatures and model fields, invoke `/ui-components` (each row's reference file).

| Need | Composable | Model on `ViewState` |
|---|---|---|
| Primary CTA / small CTA | `PrimaryButton` / `SmallButton` | `ButtonModel` (+ `ButtonState` as separate field if loading/disabled toggles) |
| Outlined action | `OutlineButton` / `SmallOutlineButton` | `ButtonModel` |
| Text entry | `LabelTextField` | `TextInputModel` |
| Password | `PasswordTextField` | `TextInputModel` |
| Phone | `PhoneTextField` | `PhoneInputModel` |
| Currency | `CurrencyTextField` | `CurrencyInputModel` |
| Dropdown-style | `SelectionTextField` | `TextInputModel` |
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

For each UI event, the changes you need across the 4 files.

| UI event | Contract | Interactor | Reducer | Screen |
|---|---|---|---|---|
| Text-field change | `Intent.OnXChanged(v: String)`, `Result.XUpdated(v)` | `.filterIsInstance<OnXChanged>().map { Result.XUpdated(it.v) }` | `state.copy(x = state.x.copy(value = result.v)).noEffects()` | `onValueChange = { viewModel.emit(Intent.OnXChanged(it)) }` |
| Toggle / checkbox | `Intent.OnXToggled(b: Boolean)`, `Result.XToggled(b)` | `.map { Result.XToggled(it.b) }` | `state.copy(x = state.x.copy(checked = result.b)).noEffects()` | `onCheckedChange = { viewModel.emit(Intent.OnXToggled(it)) }` |
| Click → navigate | `Intent.OnXClick`, `Result.OnNavigate(cmd)`, `Effect.Navigate(cmd)` | `.map { Result.OnNavigate(ScreenCommand(DetailRoute(it.id))) }` | `state withEffect Effect.Navigate(result.command)` | `onClick = { viewModel.emit(Intent.OnXClick) }` |
| Show toast | `Effect.ShowToast(toast: ToastModel)` | (emit from processor) | `state withEffect Effect.ShowToast(toast)` | `val toaster = Toast.current` (outside effect lambda); `is Effect.ShowToast -> toaster.show(effect.toast)` |
| Click → async UseCase | `Intent.OnSubmit`, `Result.Loading` / `Success` / `Error` | `onSubmitProcessor(upstream, state)` using `flatMapLatest { flow { emit(useCase.execute(state.value.field)) }.map(mapper::toResult).onStart { emit(Result.Loading) } }` | `copy(submitState = ButtonState.Loading / Enabled, error = ...)` + `withEffect(Effect.Navigate(...))` on success | `onClick = { viewModel.emit(Intent.OnSubmit) }` |
| Initial load | (already in scaffold) `Intent.LoadInitialData` | `onLoadInitialDataProcessor` calling UseCase via `.map(mapper::toResult)` | `copy(items = result.items).noEffects()` | `viewModel.OnFirstComposition(Intent.LoadInitialData)` |
| Back | `Intent.Navigation.Back` (in scaffold) | (in scaffold — maps via Mapper) | `state withEffect Effect.Navigate(BackCommand())` | Back icon in `TopNavBar` emits the intent |

**Processor convention:** handlers are named `on{IntentName}Processor`, take `Flow<Intent.SpecificType>` (and `StateFlow<ViewState>` only if current state is needed), return `Flow<Result>`, and live **above** `process()`. Never pass state through intents — read `state.value` inside the processor.

---

## Worked example — Login screen

Goal: email field, password field, primary "Log in" button, calls `LoginUseCase`, navigates to `HomeRoute(userId)` on success, shows an error otherwise.

Pick components: `LabelTextField` + `PasswordTextField` + `PrimaryButton`. All three Synapse primitives — no custom composables needed.

**Contract additions** (on top of scaffold):

```kotlin
sealed class Intent {
    data object LoadInitialData : Intent()
    sealed class Navigation : Intent() { data object Back : Navigation() }
    data class OnEmailChanged(val v: String) : Intent()
    data class OnPasswordChanged(val v: String) : Intent()
    data object OnSubmit : Intent()
}

sealed class Result {
    data object OnInitialDataLoaded : Result()
    data class NavigationRequested(val command: NavigationCommand) : Result()
    data class EmailUpdated(val v: String) : Result()
    data class PasswordUpdated(val v: String) : Result()
    data object Submitting : Result()
    data class LoggedIn(val userId: String) : Result()
    data class LoginFailed(val message: String) : Result()
}

sealed class Effect {
    data class Navigate(val command: NavigationCommand) : Effect()
}

@Immutable
data class ViewState(
    val email: TextInputModel,
    val password: TextInputModel,
    val submit: ButtonModel,
    val submitState: ButtonState,
    val error: String?,
) {
    companion object {
        val Default = ViewState(
            email = TextInputModel(label = "Email".asText(), value = "", placeholder = "you@example.com".asText()),
            password = TextInputModel(label = "Password".asText(), value = "", placeholder = "••••••".asText()),
            submit = ButtonModel(title = "Log in".asText()),
            submitState = ButtonState.Enabled,
            error = null,
        )
    }
}
```

**Mapper** — only domain → Result (input Intents are trivial enough to map inline in the Interactor):

```kotlin
fun toResult(result: LoginEntityResult): Result = when (result) {
    is LoginEntityResult.Success -> Result.LoggedIn(result.userId)
    is LoginEntityResult.Failure -> Result.LoginFailed(result.message)
}
```

**Interactor** — processor for submit, inline for the rest:

```kotlin
private fun onSubmitProcessor(
    upstream: Flow<Intent.OnSubmit>,
    state: StateFlow<ViewState>,
): Flow<Result> = upstream.flatMapLatest {
    val s = state.value
    flow { emit(loginUseCase.execute(s.email.value, s.password.value)) }
        .map(mapper::toResult)
        .onStart { emit(Result.Submitting) }
}

override fun process(intents: Flow<Intent>, state: StateFlow<ViewState>): Flow<Result> = merge(
    intents.filterIsInstance<Intent.LoadInitialData>().map(mapper::toResult),
    intents.filterIsInstance<Intent.Navigation>().map(mapper::toResult),
    intents.filterIsInstance<Intent.OnEmailChanged>().map { Result.EmailUpdated(it.v) },
    intents.filterIsInstance<Intent.OnPasswordChanged>().map { Result.PasswordUpdated(it.v) },
    intents.filterIsInstance<Intent.OnSubmit>().let { onSubmitProcessor(it, state) },
)
```

**Reducer**:

```kotlin
is Result.EmailUpdated    -> state.copy(email = state.email.copy(value = result.v), error = null).noEffects()
is Result.PasswordUpdated -> state.copy(password = state.password.copy(value = result.v), error = null).noEffects()
is Result.Submitting      -> state.copy(submitState = ButtonState.Loading, error = null).noEffects()
is Result.LoggedIn        -> state.copy(submitState = ButtonState.Enabled) withEffect
    Effect.Navigate(NavigationCommand.ScreenCommand(HomeRoute(userId = result.userId)))
is Result.LoginFailed     -> state.copy(submitState = ButtonState.Enabled, error = result.message).noEffects()
```

**Screen** body (inside the Scaffold):

```kotlin
LabelTextField(model = viewState.email,    onValueChange = { viewModel.emit(Intent.OnEmailChanged(it)) })
PasswordTextField(model = viewState.password, onValueChange = { viewModel.emit(Intent.OnPasswordChanged(it)) })
PrimaryButton(model = viewState.submit, state = viewState.submitState, onClick = { viewModel.emit(Intent.OnSubmit) })
```

---

## Custom composable escape hatch

Before writing any new `@Composable`, in order:

1. Check the component picker — is there a direct match?
2. Can Synapse primitives be composed (e.g. `Card` + `Image` + `Text`)?
3. Does the app's `compose-ui/` module already have a wrapper?

If one is still needed, invoke `/component-authoring`. It covers where the file goes, parameter order, callback naming, model design, and inverted colours. The short version: put it in `compose-ui/` if a second screen could use it and in the feature's `section/` package otherwise, give it a model built in the Mapper, keep it stateless, and never inline a multi-element composable into `{Name}Screen.kt`.

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
- [ ] `flatMapLatest` vs `flatMapConcat` chosen deliberately per the `/mvi` table
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
