# Layout & Containers Reference

## Calendar / Date Picker

```kotlin
@Composable fun DatePicker(
    model: DatePickerModel, modifier: Modifier = Modifier.wrapContentHeight(),
    onDateSelected: (Long) -> Unit,
    onResetClick: (() -> Unit)? = null,
    onDoneClick: () -> Unit,
    invertedColors: Boolean = Theme.invertedColors,
)

@Composable fun DatePickerBottomSheet(
    isVisible: Boolean, model: DatePickerModel,
    onDateSelected: (Long) -> Unit,
    onDismissRequest: OptionalClickCallback,
    invertedColors: Boolean = Theme.invertedColors,
)

@Immutable
data class DatePickerModel(val selectedDate: Long?, val minDate: Long?, val maxDate: Long?)
```

---

## Card

```kotlin
@Composable fun Card(modifier: Modifier = Modifier, invertedColors: Boolean = Theme.invertedColors, content: @Composable () -> Unit)
```

## Divider

```kotlin
@Composable fun Divider(color: Color? = null, modifier: Modifier = Modifier.fillMaxWidth(), thickness: Dp = 1.dp, invertedColors: Boolean = Theme.invertedColors)
```

## Scaffold

```kotlin
@Composable fun Scaffold(
    modifier: Modifier = Modifier, contentWindowInsets: WindowInsets = WindowInsets(0),
    backgroundColor: Color? = null, invertedColors: Boolean = Theme.invertedColors,
    topBar: @Composable () -> Unit = {}, bottomBar: @Composable () -> Unit = {},
    floatingActionBar: @Composable () -> Unit = {},
    content: @Composable (PaddingValues) -> Unit,
)
```

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
    invertedColors: Boolean = Theme.invertedColors,
)
```

**TopNavBarModel**:
```kotlin
@Immutable
data class TopNavBarModel(
    val leadingIcon: Image? = null,
    val title: Clause? = null,
    val trailing: TopNavBarTrailingContentModel? = null,
) {
    companion object {
        val BackIcon: Image    // Image.Drawable(Res.drawable.sc_icon_chevron_left)
        val CloseIcon: Image   // Image.Drawable(Res.drawable.sc_icon_close)
        val MenuIcon: Image    // Image.Drawable(Res.drawable.sc_icon_menu)

        fun withTitle(
            title: Clause,
            leadingIconType: NavBarIconType? = null,
            trailing: TopNavBarTrailingContentModel? = null,
        ): TopNavBarModel
    }
}

enum class NavBarIconType { Back, Close, Menu }

@Immutable
data class TrailingIconModel(
    val id: String,
    val icon: Image,
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

**Colors** (via `Theme.colors`):
- Container: `surface.primaryLight` / `primaryDark`
- Content: `element.primaryOnLight` / `primaryOnDark`

---

## BottomNavigationBar

Fixed-height row of icon/label items along the bottom of a screen, intended for top-level destination switching in a `Scaffold.bottomBar` slot. Each item is a `Modifier.selectable(role = Role.Tab)` inside a `selectableGroup()`, spring-free `animateColorAsState` drives icon tint and label color between selected/unselected, and disabled items are rendered at `38%` alpha with ignored clicks. A 1dp hairline divider sits above the bar using `border.secondaryOnLight/Dark`. Label is optional per item (pass `null` for an icon-only bar). When `items` is empty the composable renders nothing. Selection is tracked by `String` id so callers can map directly to routes.

```kotlin
@Composable fun BottomNavigationBar(
    model: BottomNavigationBarModel,
    modifier: Modifier = Modifier,
    onItemSelected: (id: String) -> Unit,
    invertedColors: Boolean = Theme.invertedColors,
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

**Dimensions**: bar height `64dp`, icon size `24dp`, dot badge `8dp`, count badge min `16dp` (widens for `99+`).

**Colors** (via `Theme.colors`):
- Container: `surface.primaryLight` / `primaryDark`
- Divider: `border.secondaryOnLight` / `secondaryOnDark`
- Active icon/label: `surfaceInteractive.enabledOnLight` / `enabledOnDark`
- Inactive icon/label: `element.secondaryOnLight` / `secondaryOnDark`
- Disabled: `elementInteractive.disabledOnLight` / `disabledOnDark` @ `0.38` alpha
- Badge fill: `intents.error.surfaceOnLight` / `surfaceOnDark`
- Badge text: `intents.error.contentOnLight` / `contentOnDark`

**Behavior**:
- Selected label uses `Theme.typography.labelXs` at `FontWeight.SemiBold`; unselected at `FontWeight.Normal`.
- Icon tinting: if only `icon` is provided, it is tinted with the active/inactive color via `ColorFilter.tint` (template image). If `selectedIcon` is also provided, **neither** icon is tinted — the caller owns the visuals for both states (original image). Use the former for monochrome glyph sets, the latter for outline/filled icon pairs that ship their own colors.
- `BottomNavigationBadge.Count` clamps display to `"99+"` when `value > 99`.

---

## LiquidGlassBottomNavigationBar

Drop-in replacement for `BottomNavigationBar` with a pill-shaped track and a floating capsule that springs between items. Same `BottomNavigationBarModel` — identical call shape. Selection is communicated by the pill's position (not by a bright accent tint), so labels/icons only shift between `element.primary` and `element.secondary`. Fixed 64dp bar height; 4dp inset around the pill; 6dp shadow elevation; 1dp hairline border for the glass edge. When `selectedId` doesn't match any item, the pill is rendered at `alpha=0` — the bar itself stays visible.

```kotlin
@Composable fun LiquidGlassBottomNavigationBar(
    model: BottomNavigationBarModel,
    modifier: Modifier = Modifier,
    onItemSelected: (id: String) -> Unit,
    invertedColors: Boolean = Theme.invertedColors,
)
```

Shares `BottomNavigationBarModel`, `BottomNavigationItem`, and `BottomNavigationBadge` with `BottomNavigationBar` — see above.

**Colors** (via `Theme.colors`):
- Track: `surface.subtleLight` / `subtleDark`
- Pill fill: `surface.primaryLight` / `primaryDark`
- Pill hairline: `border.secondaryOnLight` / `secondaryOnDark`
- Active icon/label: `element.primaryOnLight` / `primaryOnDark` @ `FontWeight.SemiBold`
- Inactive icon/label: `element.secondaryOnLight` / `secondaryOnDark` @ `FontWeight.Normal`
- Disabled: `elementInteractive.disabledOnLight` / `disabledOnDark` @ `0.38` alpha
- Badge fill / text: `intents.error.surfaceOnLight` / `contentOnLight` (and Dark equivalents)

**Animation**: `animateDpAsState` with `spring(DampingRatioLowBouncy, StiffnessMediumLow)` drives the pill's x-offset; item tint animates via `animateColorAsState` inside the shared item renderer.

**When to pick which**:
- `BottomNavigationBar` — standard material-style bar that sits flush against content, communicates selection via a bright accent color on the icon/label. Best for productivity apps, dense interfaces, or when the bar competes with colorful content.
- `LiquidGlassBottomNavigationBar` — free-standing, prominent, expressive. Best for consumer apps where the nav bar is a showpiece, or when you want a floating chip feel. Wrap it in `.padding(horizontal = Theme.spacing.x4, vertical = Theme.spacing.x2)` inside `Scaffold.bottomBar` for the "floating island" look.

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
    invertedColors: Boolean = Theme.invertedColors,
    content: @Composable BoxScope.() -> Unit,
)
```

**When to use which:**
- Use `Tray` for standard modal sheets with fixed or wrap-height content (forms, confirmations, pickers).
- Use `ScrollableTray` when the sheet contains a long scrollable list that would otherwise fight the sheet's own drag gesture.
