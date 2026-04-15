# Layout & Containers Reference

## Calendar / Date Picker

```kotlin
@Composable fun DatePicker(
    model: DatePickerModel, modifier: Modifier = Modifier.wrapContentHeight(),
    onDateSelected: (Long) -> Unit,
    onResetClick: (() -> Unit)? = null,
    onDoneClick: () -> Unit,
)

@Composable fun DatePickerBottomSheet(
    isVisible: Boolean, model: DatePickerModel,
    onDateSelected: (Long) -> Unit,
    onDismissRequest: OptionalClickCallback,
)

@Immutable
data class DatePickerModel(val selectedDate: Long?, val minDate: Long?, val maxDate: Long?)
```

---

## Card

```kotlin
@Composable fun Card(modifier: Modifier = Modifier, invertedColors: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit)
```

## Divider

```kotlin
@Composable fun Divider(color: Color? = null, modifier: Modifier = Modifier.fillMaxWidth(), thickness: Dp = 1.dp, invertedColors: Boolean = isSystemInDarkTheme())
```

## Scaffold

```kotlin
@Composable fun Scaffold(
    modifier: Modifier = Modifier, contentWindowInsets: WindowInsets = WindowInsets(0),
    backgroundColor: Color? = null, invertedColors: Boolean = isSystemInDarkTheme(),
    topBar: @Composable () -> Unit = {}, bottomBar: @Composable () -> Unit = {},
    floatingActionBar: @Composable () -> Unit = {},
    content: @Composable (PaddingValues) -> Unit,
)
```

---

## TopNavBar

Top navigation bar with optional leading icon, title, and trailing actions. Wraps Material 3 `TopAppBar` with Synapse theme colours.

```kotlin
@Composable fun TopNavBar(
    model: TopNavBarModel,
    modifier: Modifier = Modifier,
    leadingIcon: @Composable (() -> Unit)? = null,
    onTrailingActionClick: ((index: Int) -> Unit)? = null,
    invertedColors: Boolean = Theme.invertedColors,
)
```

**TopNavBarModel**:
```kotlin
@Stable data class TopNavBarModel(
    val title: Clause,
    val trailingActions: List<ActionModel> = emptyList(),
) {
    @Stable data class ActionModel(val label: Clause? = null, val icon: Image? = null)
}
```

**TopNavBarLeadingIcon** — pre-built leading-icon composables:
```kotlin
TopNavBarLeadingIcon.Back(onClick = { /* navigate back */ })
TopNavBarLeadingIcon.Close(onClick = { /* dismiss */ })
TopNavBarLeadingIcon.Menu(onClick = { /* open drawer */ })
```

---

## Trays / Bottom Sheets

### `Tray`

Standard modal bottom sheet with a drag handle. Wraps content height, supports swipe-to-dismiss, and can pin a `stickyBottom` slot that stays visually anchored to the bottom of the visible sheet area as the user drags (it tracks `sheetState.requireOffset()` via an `IntOffset`, so it does not scroll off-screen with the content). Applies `navigationBarsPadding` automatically.

- `isSwipeDismissible = false` locks the sheet in place (gesture changes are rejected via `confirmValueChange`).
- `skipPartiallyExpanded = true` forces the sheet to open fully without a half-expanded stop.
- `stickyBottom` is rendered inside a `BoxScope` aligned to `BottomEnd`, padded by `Theme.spacing.x5` — typically used for a primary action button that must remain reachable.

```kotlin
@Composable fun Tray(
    onDismissRequest: OptionalClickCallback,
    isSwipeDismissible: Boolean = true,
    skipPartiallyExpanded: Boolean = false,
    stickyBottom: (@Composable BoxScope.() -> Unit)? = null,
    content: @Composable BoxScope.() -> Unit,
)
```

### `ScrollableTray`

Standalone bottom sheet designed for modals whose **inner content scrolls** (e.g. `verticalScroll`, `LazyColumn`). Differs from `Tray` in several ways:

- **Locked in place** — no drag or swipe can move the sheet. Scroll/fling overflow is consumed by a custom `NestedScrollConnection` so it never reaches the sheet's drag handler.
- **No drag handle** is rendered.
- **Expands to fill** available space below the status bar (`statusBarsPadding`), leaving a portion of the screen behind it visible.
- Uses `Theme.colors.surface.primaryDark`/`primaryLight` as container color based on `invertedColors`.
- **Callers are responsible for providing their own close button** inside `content` — there is no swipe-to-dismiss and no drag handle, so the only way the user can dismiss is via an explicit control you render.

```kotlin
@Composable fun ScrollableTray(
    onDismissRequest: OptionalClickCallback,
    invertedColors: Boolean = isSystemInDarkTheme(),
    content: @Composable BoxScope.() -> Unit,
)
```

**When to use which:**
- Use `Tray` for standard modal sheets with fixed or wrap-height content (forms, confirmations, pickers).
- Use `ScrollableTray` when the sheet contains a long scrollable list that would otherwise fight the sheet's own drag gesture.
