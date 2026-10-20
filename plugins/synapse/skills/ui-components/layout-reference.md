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
data class DatePickerModel(
    val selectedDate: Long?,                              // epoch millis
    val minDate: Long?,
    val maxDate: Long?,
    val monthLabels: List<Clause> = /* "January" … "December" */,   // exactly 12, January first
    val weekdayLabels: List<Clause> = /* "Su" … "Sa" */,            // exactly 7, Sunday first
    val resetLabel: Clause = "Reset".asText(),
    val doneLabel: Clause = "Done".asText(),
)
```

The labels default to English; pass localized clauses for other languages. A label list of the wrong size throws `IllegalArgumentException` when the model is built. The year and day numbers are drawn as plain digits.

The picker keeps the month on screen and whether the calendar, month grid or year grid is showing as its own state, starting from `selectedDate` (or today); a new model resets them. Days are converted with the device's time zone: `onDateSelected` receives the start of the chosen day there.

---

## Card

```kotlin
@Composable fun Card(modifier: Modifier = Modifier, content: @Composable () -> Unit)
```

Paints `surface.secondary` in `Theme.shape.card` and provides `LocalContentColor = element.primary` to its content.

## Divider

```kotlin
@Composable fun Divider(color: Color? = null, modifier: Modifier = Modifier.fillMaxWidth(), thickness: Dp = 1.dp)
```

## Scaffold

```kotlin
@Composable fun Scaffold(
    modifier: Modifier = Modifier, contentWindowInsets: WindowInsets = WindowInsets(0),
    backgroundColor: Color? = null,
    topBar: @Composable () -> Unit = {}, bottomBar: @Composable () -> Unit = {},
    floatingActionBar: @Composable () -> Unit = {},
    content: @Composable (PaddingValues) -> Unit,
)
```

Paints `backgroundColor ?: surface.primary` and provides `LocalContentColor = element.primary`, so a screen needs no colour arguments to be correct in both appearances.

---

## TopNavBar

Top navigation bar with an optional leading icon, optional title, and optional trailing content (either a clickable title or a row of icon buttons). A plain themed `Row` (56dp tall), not Material 3 `TopAppBar`. The leading icon slot is 48dp; tapping it invokes `onLeadingClick` (the slot is only clickable when `onLeadingClick` is non-null). Trailing icons are keyed by `String` id so callers can dispatch on which one was tapped.

```kotlin
@Composable fun TopNavBar(
    model: TopNavBarModel,
    modifier: Modifier = Modifier,
    onLeadingClick: (() -> Unit)? = null,
    onTrailingTitleClick: (() -> Unit)? = null,
    onTrailingIconClick: ((id: String) -> Unit)? = null,
)
```

**TopNavBarModel**:
```kotlin
@Immutable
data class TopNavBarModel(
    val leadingIcon: Image? = null,
    val title: Clause? = null,
    val trailing: TopNavBarTrailingContentModel? = null,
    val leadingIconLabel: Clause? = null,     // screen-reader label; null uses leadingIcon.contentDescription
) {
    companion object {
        val BackIcon: Image.Glyph    // Image.Glyph(Res.drawable.sc_icon_chevron_left, contentDescription = "Back")
        val CloseIcon: Image.Glyph   // Image.Glyph(Res.drawable.sc_icon_close, contentDescription = "Close")
        val MenuIcon: Image.Glyph    // Image.Glyph(Res.drawable.sc_icon_menu, contentDescription = "Menu")

        fun withTitle(
            title: Clause,
            leadingIconType: NavBarIconType? = null,
            trailing: TopNavBarTrailingContentModel? = null,
            leadingIconLabel: Clause? = null,
        ): TopNavBarModel
    }
}

enum class NavBarIconType { Back, Close, Menu }

@Immutable
data class TrailingIconModel(
    val id: String,
    val icon: Image,
    val label: Clause? = null,                // screen-reader label; null uses icon.contentDescription
)

@Stable
sealed class TopNavBarTrailingContentModel {
    @Immutable
    data class Title(
        val clause: Clause,
        val enabled: Boolean = true,
    ) : TopNavBarTrailingContentModel()

    @Immutable
    data class Icons(
        val icons: List<TrailingIconModel>,
    ) : TopNavBarTrailingContentModel()
}
```

- `TopNavBarModel.withTitle(...)` is the convenient factory: pass a `NavBarIconType` and it resolves the matching `BackIcon`/`CloseIcon`/`MenuIcon` for the leading slot.
- `TopNavBarTrailingContentModel.Title` renders a tappable text action on the trailing edge; when `enabled = false` it draws at `0.38` alpha and ignores taps. Its tap invokes `onTrailingTitleClick`.
- `TopNavBarTrailingContentModel.Icons` renders one 48dp icon button per `TrailingIconModel`; each tap invokes `onTrailingIconClick(id)`.
- The built-in icons are `Image.Glyph`s, tinted with the bar's content colour, and carry English content descriptions. Every icon button is announced as a button with its label: `leadingIconLabel` / `TrailingIconModel.label` when set (pass `Text.Localized(...)` to localize), the image's `contentDescription` otherwise. A button with no click handler is announced as disabled.

**Colors** (via `Theme.colors`):
- Container: `surface.primary`
- Content: `element.primary`

---

## BottomNavigationBar

The app's top-level destinations, docked along the bottom of the screen. Made for `Scaffold.bottomBar`. Items share the width equally and selection is tracked by `String` id, so ids can be route names. When `items` is empty the composable renders nothing.

```kotlin
@Composable fun BottomNavigationBar(
    model: BottomNavigationBarModel,
    modifier: Modifier = Modifier,
    windowInsets: WindowInsets = WindowInsets.navigationBars,
    onItemSelected: (id: String) -> Unit,
)

@Immutable
data class BottomNavigationBarModel(
    val items: List<BottomNavigationItem> = emptyList(),
    val selectedId: String? = null,
)

@Immutable
data class BottomNavigationItem(
    val id: String,
    val icon: Image,
    val selectedIcon: Image? = null,
    val label: Clause? = null,
    val badge: BottomNavigationBadge? = null,
    val enabled: Boolean = true,
)

@Stable
sealed class BottomNavigationBadge {
    @Immutable data object Dot : BottomNavigationBadge()
    @Immutable data class Count(val value: Int) : BottomNavigationBadge()
}
```

**Anatomy**: a `surface.primary` bar with a 1dp `border.secondary` hairline along its top. Each item is an icon in a 56×32dp capsule, with an optional one-line label under it. The selected item's capsule fills with `intents.accent.surface` and its icon turns `intents.accent.content`. The capsule grows sideways out from behind the icon as it fades in. Icon tint, label colour and capsule are all driven by one selection animation, so they move together.

**Interaction**: the whole cell is the touch target, but there is no ripple. Feedback is drawn in the item's capsule, the same place the selection lands. Pressing tints the capsule with `element.primary` at 8% and squeezes the icon to 90%, then springs it back with a slight overshoot on release. A tap shorter than the squeeze still plays it out. Keyboard focus and pointer hover tint the capsule without squeezing. `onItemSelected` fires for the already-selected item too, so a screen can scroll back to its top or pop to its root on reselect.

**Insets**: the bar paints behind `windowInsets` (the system navigation bar or home indicator by default) and keeps its items above them, so it sits flush with the bottom of an edge-to-edge screen. Pass `WindowInsets(0)` when an ancestor already handles them, or when the bar is not at the bottom of the window (a preview inside a scrolling page). Insets an ancestor has already consumed are not applied twice.

**Dimensions**: at least `64dp` tall above the insets, and taller when the label's font scale needs it; icon `24dp`; capsule `56×32dp`; label `4dp` below the capsule, one line, ellipsized.

**Colors** (via `Theme.colors`):
- Bar: `surface.primary`, hairline `border.secondary`
- Selected: capsule `intents.accent.surface`, icon `intents.accent.content`, label `element.primary`
- Unselected icon and label: `element.secondary`
- Press, focus and hover tint: `element.primary` at 8%
- Disabled: the whole item at `0.38` alpha, in the colours of its state. It is not clickable and is announced as disabled.
- Badge fill: `intents.error.content`. The ring around the badge and the count's text are cut out in the bar colour (`surface.primary`), so the count is light on a saturated fill and dark on the pastel fill of a dark theme.

**Behavior**:
- Labels use `Theme.typography.labelS` at a constant weight in both states, so the selected label does not reflow.
- Icon tinting: the image type decides. An `Image.Glyph` takes the item's state colour, whether it is the `icon` or the `selectedIcon`, so an outline/filled glyph pair still follows the theme. An `Image.Artwork` is drawn as authored in every state; use it for icons that ship their own colours.
- Badges sit on the icon's top-end shoulder, outside its centre, so a three-character count leaves the glyph recognisable. `BottomNavigationBadge.Count` shows `"99+"` when `value > 99`.
- Screen readers hear each item once, as its label (or, without one, the icon's `contentDescription`) followed by the badge count, plus its tab role, position and selected state. Give icon-only items a `contentDescription`. A `Dot` badge is not announced.

---

## LiquidGlassBottomNavigationBar

The same destinations on a floating island, for apps where the bar is a centrepiece. Same `BottomNavigationBarModel` and call shape as `BottomNavigationBar`.

```kotlin
@Composable fun LiquidGlassBottomNavigationBar(
    model: BottomNavigationBarModel,
    modifier: Modifier = Modifier,
    windowInsets: WindowInsets = WindowInsets.navigationBars,
    onItemSelected: (id: String) -> Unit,
)
```

Shares `BottomNavigationBarModel`, `BottomNavigationItem`, and `BottomNavigationBadge` with `BottomNavigationBar` (see above).

**Anatomy**: a fully rounded `surface.raised` island with an 8dp shadow and a 1dp `border.secondary` edge. Inside it, one `intents.accent.surface` capsule, inset 4dp and concentric with the island, marks the selected item. The selected item's icon and label are both `intents.accent.content`, since both sit inside the capsule.

**Motion**: the capsule travels between items like a drop of liquid. Its leading edge springs ahead to the new item (`spring(DampingRatioLowBouncy, StiffnessMediumLow)`) and lands with a slight wobble. Its trailing edge follows more softly (`spring(DampingRatioNoBouncy, StiffnessLow)`). So the capsule stretches in flight, more on a long jump than a short one, and settles back into shape. When `selectedId` matches no item, the capsule fades out where it is. When a selection returns, the capsule fades back in on that item instead of sliding from the old one.

**Interaction**: as for `BottomNavigationBar`, with the cell itself as the capsule. Pressing an item tints a capsule of exactly the shape the indicator takes when it lands there, and squeezes the icon and label inside it.

**Insets**: the island lifts itself above `windowInsets`, but spans the width it is given and adds no margins of its own. Pad it from the screen's edges for the floating look (see the example below). Pass `WindowInsets(0)` when an ancestor already handles the insets.

**Dimensions**: at least `64dp` tall; capsule inset `4dp`; icon `24dp`; label `2dp` below the icon.

**Colors** (via `Theme.colors`):
- Island: `surface.raised`, edge `border.secondary`
- Selected: capsule `intents.accent.surface`, icon and label `intents.accent.content`
- Unselected icon and label: `element.secondary`
- Press, focus, hover, disabled and badges: as for `BottomNavigationBar`, with badge cut-outs in `surface.raised`

**When to pick which**:
- `BottomNavigationBar`: flush with the bottom of the screen and quiet. Best for productivity apps and dense interfaces, or when content is colourful and the bar should recede.
- `LiquidGlassBottomNavigationBar`: free-standing and expressive. Best for consumer apps where the bar is a showpiece. Inside `Scaffold.bottomBar`, give it `Modifier.padding(horizontal = Theme.spacing.x4, vertical = Theme.spacing.x2)` so it floats as an island.

---

## Trays / Bottom Sheets

### `Tray`

Standard modal bottom sheet with a drag handle, shown from inside a screen and driven by that screen's state. Wraps content height, supports swipe-to-dismiss, and can pin a `stickyBottom` slot that stays visually anchored to the bottom of the visible sheet area as the user drags (it tracks `sheetState.requireOffset()` via an `IntOffset`, so it does not scroll off-screen with the content). It is the sheet plus a [`TraySurface`](#traysurface), so it applies `navigationBarsPadding` and `imePadding` automatically. Its drag handle, container colour, content colour and content decoration come from the `NavContainer`'s `BottomSheetAppearance` (see [One look for all sheets](#one-look-for-all-sheets)).

**Never use `Tray` as the root of a `bottomSheet()` destination.** Navigation already draws that sheet, so a `Tray` inside it opens a second sheet, visible behind the first as the user drags down. Use `TraySurface` there.

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

Standalone bottom sheet shown from inside a screen, designed for modals whose **inner content scrolls** (e.g. `verticalScroll`, `LazyColumn`). It is the sheet plus a [`ScrollableTraySurface`](#scrollabletraysurface). Differs from `Tray` in several ways:

- **Locked in place** — no drag or swipe can move the sheet. Scroll/fling overflow is consumed by a custom `NestedScrollConnection` so it never reaches the sheet's drag handler.
- **No drag handle** is rendered.
- **Expands to fill** available space below the status bar (`statusBarsPadding`), leaving a portion of the screen behind it visible.
- Container colour, content colour and content decoration come from the `NavContainer`'s `BottomSheetAppearance`. Applies `navigationBarsPadding` and `imePadding`.
- **Callers are responsible for providing their own close button** inside `content` — there is no swipe-to-dismiss and no drag handle, so the only way the user can dismiss is via an explicit control you render.

As with `Tray`, never use it as the root of a `bottomSheet()` destination; use `ScrollableTraySurface`.

```kotlin
@Composable fun ScrollableTray(
    onDismissRequest: OptionalClickCallback,
    content: @Composable BoxScope.() -> Unit,
)
```

### `TraySurface`

The inside of a `Tray`, without the sheet. Use it as the root of a screen registered with `bottomSheet()` metadata, where navigation owns the sheet. Applies `navigationBarsPadding` and `imePadding`, and renders `stickyBottom` the same way `Tray` does. The sheet around it, including its look, is the `bottomSheet()` scene's.

```kotlin
@Composable fun TraySurface(
    modifier: Modifier = Modifier,
    stickyBottom: (@Composable BoxScope.() -> Unit)? = null,
    stickyBottomOffset: (() -> Int)? = null,
    content: @Composable BoxScope.() -> Unit,
)
```

- `stickyBottomOffset` is a vertical offset in px applied to `stickyBottom`. `Tray` passes its sheet offset so the slot follows a drag; in a `bottomSheet()` screen the sheet state belongs to navigation, so leave it `null` (the slot then stays at the bottom of the content).

```kotlin
entry<FilterRoute>(metadata = bottomSheet()) { FilterScreen() }

@Composable
internal fun FilterScreen(...) {
    TraySurface {
        Column { /* header, content */ }
    }
}
```

### `ScrollableTraySurface`

The inside of a `ScrollableTray`, without the sheet: inner scrolling works and never drags the sheet. Use it as the root of a `bottomSheet()` screen whose content scrolls. The locked, handle-less, fully expanded sheet comes from the destination's options, not from the surface:

```kotlin
entry<ReportRoute>(
    metadata = bottomSheet(
        BottomSheetOptions(skipPartiallyExpanded = true, isSwipeDismissible = false, showDragHandle = false)
    )
) { ReportScreen() }

@Composable fun ScrollableTraySurface(
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit,
)
```

As with `ScrollableTray`, render your own close button inside `content`.

### One look for all sheets

There is one sheet look, and the app sets it once: the `BottomSheetAppearance` passed to `NavContainer` (see `/synapse:navigation`). `NavContainer` publishes it as `LocalBottomSheetAppearance`, and `Tray`, `ScrollableTray` and `DatePickerBottomSheet` read it, so in-screen trays and `bottomSheet()` destinations share the same drag handle, container colour, content colour and `contentDecoration`.

```kotlin
NavContainer(
    startKey = startKey,
    features = features,
    bottomSheetAppearance = ThemedBottomSheetAppearance,
)
```

`ThemedBottomSheetAppearance` is the Synapse look, and the one to start from:

```kotlin
val ThemedBottomSheetAppearance: BottomSheetAppearance = BottomSheetAppearance(
    containerColor = { Theme.colors.surface.raised },
    dragHandle = { BottomSheetDefaults.DragHandle(color = Theme.colors.border.primary) },
    contentColor = { Theme.colors.element.primary },
    contentDecoration = { content -> WithRaisedSurface(content) },
)
```

The sheet paints `surface.raised`, and `WithRaisedSurface` makes `surface.primary` resolve to it inside, so a field or button that paints "the canvas it sits on" matches the sheet in both appearances. To change one slot, copy it: `ThemedBottomSheetAppearance.copy(dragHandle = { AppDragHandle() })`.

- `ScrollableTray` never shows the handle; a destination hides it with `BottomSheetOptions(showDragHandle = false)`.
- Inside a tray, Synapse `LocalContentColor` defaults to `element.primary`, so `Text` whose style has no colour stays readable. `contentDecoration` wraps the content inside that, so the app can override it. In a `bottomSheet()` destination only `contentDecoration` applies.
- A tray composed outside any `NavContainer` (a preview, an app without Synapse navigation) gets `BottomSheetAppearance()`, i.e. Material 3's defaults. Provide `LocalBottomSheetAppearance provides ThemedBottomSheetAppearance` there to match the app.

**When to use which:**

| The sheet is… | Content | Use |
|---|---|---|
| a destination (`bottomSheet()` metadata; own ViewModel; back closes it) | fixed or wrap height | `TraySurface` |
| a destination | long scrolling list | `ScrollableTraySurface` + locking `BottomSheetOptions` |
| shown from inside a screen, driven by its `ViewState` | fixed or wrap height (forms, confirmations, pickers) | `Tray` |
| shown from inside a screen | long scrolling list that would fight the sheet's drag | `ScrollableTray` |

A destination sheet pops the back stack when dismissed and gets its own lifecycle and ViewModel scope. An in-screen tray is shown and hidden by the caller's state and never touches the back stack.
