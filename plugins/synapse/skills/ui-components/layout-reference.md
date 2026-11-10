# Layout & Containers Reference

## Calendar and date sheet

`MonthCalendar` draws a month on the page. `DatePickerBottomSheet` asks for one date in a sheet. To ask for a date in a form, use `DateTextField` (see [inputs](inputs-reference.md)), which opens that sheet from a field; a calendar among a form's inputs pushes its other fields and its submit button off the screen.

```kotlin
@Composable fun MonthCalendar(
    model: MonthCalendarModel, modifier: Modifier = Modifier,
    onDisplayedMonthChange: ((Long) -> Unit)? = null,     // the first instant of the month moved to
    onDayClick: (Long) -> Unit,                           // the first instant of the tapped day
)

@Immutable
data class MonthCalendarModel(
    val selectedDate: Long? = null,                       // a day is any instant of it, epoch millis
    val minDate: Long? = null,
    val maxDate: Long? = null,
    val markedDays: Map<Long, Int> = emptyMap(),          // dots under a day; at most three are drawn
    val displayedMonth: Long? = null,                     // null follows the selection, or today, until moved
    val today: Long? = null,                              // null reads the device's clock
    val firstDayOfWeek: DayOfWeek = DayOfWeek.SUNDAY,     // kotlinx.datetime
    val monthLabels: List<Clause>? = null,                // null: the device's language; else 12, January first
    val weekdayLabels: List<Clause>? = null,              // null: the device's language; else 7, Sunday first
)

@Composable fun DatePickerBottomSheet(
    isVisible: Boolean, model: DatePickerModel,
    onDateSelected: (Long) -> Unit,                       // the first instant of the tapped day, as it is tapped
    onResetClick: (() -> Unit)? = null,                   // reset is hidden when null
    onDoneClick: (() -> Unit)? = null,                    // called before the sheet closes
    onDismissRequest: OptionalClickCallback,              // once closed: by done, a tap outside or a swipe
)

@Immutable
data class DatePickerModel(
    val selectedDate: Long?,                              // epoch millis
    val minDate: Long?,
    val maxDate: Long?,
    val monthLabels: List<Clause>? = null,                // null: the device's language; else 12, January first
    val weekdayLabels: List<Clause>? = null,              // null: the device's language; else 7, Sunday first
    val resetLabel: Clause = "Reset".asText(),
    val doneLabel: Clause = "Done".asText(),
    val firstDayOfWeek: DayOfWeek = DayOfWeek.SUNDAY,     // kotlinx.datetime
)
```

Month and weekday names follow the device's language unless you pass labels. A label list of the wrong size throws `IllegalArgumentException` when the model is built. `weekdayLabels` stay Sunday first whatever `firstDayOfWeek` is. The year and day numbers are drawn as plain digits.

The calendar opens on `selectedDate`, or today, moved inside the bounds. Tapping its title opens a grid of months and, from there, a grid of years. It keeps the grid showing as its own state. It also keeps the month on screen until the screen holds it in `displayedMonth`: to restore the month after a configuration change, keep what `onDisplayedMonthChange` reports in `ViewState` and pass it back.

Days are read in the device's time zone. A month with no selectable day can't be reached, and days outside the bounds can't be tapped.

---

## Card

```kotlin
@Composable fun Card(modifier: Modifier = Modifier, content: @Composable () -> Unit)
```

Paints `surface.secondary` in `Theme.shape.card` and provides `LocalContentColor = element.primary` to its content.

## SelectableCard

```kotlin
@Composable fun SelectableCard(
    selected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
    content: @Composable () -> Unit,
)
```

A `Card` that is one option of a single choice, such as a plan on a paywall. It draws the card's surface with a border in the card's shape: 2dp in `surfaceInteractive.enabled` while `selected`, otherwise 1dp in `border.primary`, the colours a selected and an unselected chip use. The whole card is the tap target, clipped to its shape, and announces itself as a selected or unselected radio button. Hold the choice yourself and pass `selected` for each option:

```kotlin
var plan by remember { mutableStateOf("yearly") }
listOf("monthly", "yearly").forEach { option ->
    SelectableCard(selected = plan == option, onClick = { plan = option }) {
        Text(clause = option.asText(), modifier = Modifier.padding(Theme.spacing.x4))
    }
}
```

## Section

A titled group on a page: a heading with an optional text action, then its rows. It keeps a gap above and below itself, so sections stack without spacers, and adds no side padding.

```kotlin
data class SectionModel(
    val title: Clause? = null,
    val actionLabel: Clause? = null,   // a text action at the end of the heading, such as "See all"
    val emptyText: Clause? = null,     // shown in place of the rows when there are none
    val grouped: Boolean = false,      // rows on one card with hairlines between them; otherwise stacked with a small gap
)

@Composable fun Section(
    model: SectionModel,
    rowCount: Int,
    modifier: Modifier = Modifier,
    onActionClick: (() -> Unit)? = null,
    row: @Composable (index: Int) -> Unit,
)

// The same section as items of a LazyColumn, so only the rows on screen compose.
fun LazyListScope.section(
    model: SectionModel,
    rowCount: Int,
    key: String,                                   // every item key starts with it
    rowKey: (index: Int) -> String = { it.toString() },   // unique within the section, stable as rows change
    onActionClick: (() -> Unit)? = null,
    row: @Composable (index: Int) -> Unit,
)
```

Use `Section` inside a scrolling `Column` for a handful of rows, and `section` for a long or data-driven list:

```kotlin
LazyColumn {
    section(SectionModel(title = "Recent".asText(), grouped = true), rowCount = expenses.size, key = "recent",
        rowKey = { expenses[it].id }) { index -> ExpenseRow(expenses[index]) }
}
```

`section` draws what `Section` draws: the heading is one item and each row another, a grouped card is split across its rows in the theme's card shape, and the gaps match. Give the list no arrangement that spreads free space between items (`SpaceBetween`, `SpaceAround`, `SpaceEvenly`), or the gaps land inside the card.

## Divider

```kotlin
@Composable fun Divider(color: Color? = null, modifier: Modifier = Modifier.fillMaxWidth(), thickness: Dp = 1.dp)   // color: border.secondary by default
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

Under a native navigation shell (iOS 26 Liquid Glass) the bars sit clear of the native chrome, and the `PaddingValues` handed to `content` cover that chrome (navigation bar top, floating tab bar bottom) as well as the bars. A screen that honours the padding is correct on every shell. The overlap is measured from where `LocalNativeChromeInsets` is provided, so system insets a parent has already consumed take nothing off it. To let content scroll beneath translucent native bars, apply the padding inside the scroll container (`Modifier.verticalScroll(state).padding(padding)`, or a lazy list's `contentPadding = padding`) rather than around it. Off the native shell the layout is unchanged. See `/synapse:navigation` for the native shell.

---

## TopNavBar

Top navigation bar with an optional leading icon, optional title, and optional trailing content (a clickable title, a row of icon buttons, or a row of text and icon actions in any mix). A plain themed `Row` (56dp tall), not Material 3 `TopAppBar`. The leading icon slot is 48dp; tapping it invokes `onLeadingClick` (the slot is only clickable when `onLeadingClick` is non-null). Trailing icons are keyed by `String` id so callers can dispatch on which one was tapped.

```kotlin
@Composable fun TopNavBar(
    model: TopNavBarModel,
    modifier: Modifier = Modifier,
    onLeadingClick: (() -> Unit)? = null,
    onTrailingTitleClick: (() -> Unit)? = null,
    onTrailingIconClick: ((id: String) -> Unit)? = null,
    onTrailingActionClick: ((id: String) -> Unit)? = null,
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

    @Immutable
    data class Actions(
        val actions: List<TrailingActionModel>,
    ) : TopNavBarTrailingContentModel()
}

@Stable
sealed class TrailingActionModel {
    abstract val id: String
    abstract val enabled: Boolean

    @Immutable
    data class Icon(
        override val id: String,
        val icon: Image,                       // its contentDescription is the action's only label
        override val enabled: Boolean = true,
    ) : TrailingActionModel()

    @Immutable
    data class Text(
        override val id: String,
        val clause: Clause,
        override val enabled: Boolean = true,
    ) : TrailingActionModel()
}
```

- `TopNavBarModel.withTitle(...)` is the convenient factory: pass a `NavBarIconType` and it resolves the matching `BackIcon`/`CloseIcon`/`MenuIcon` for the leading slot.
- `TopNavBarTrailingContentModel.Title` renders a tappable text action on the trailing edge; when `enabled = false` it draws at `0.38` alpha and ignores taps. Its tap invokes `onTrailingTitleClick`.
- `TopNavBarTrailingContentModel.Icons` renders one 48dp icon button per `TrailingIconModel`; each tap invokes `onTrailingIconClick(id)`.
- `TopNavBarTrailingContentModel.Actions` renders text and icon actions in any mix, in list order; each tap invokes `onTrailingActionClick(id)`. A disabled action draws at `0.38` alpha and ignores taps. Give each `TrailingActionModel.Icon` image a `contentDescription` (`Image.Glyph(res, contentDescription = "Share")`).
- The built-in icons are `Image.Glyph`s, tinted with the bar's content colour, and carry English content descriptions. Every icon button is announced as a button with its label: `leadingIconLabel` / `TrailingIconModel.label` when set (pass `Text.Localized(...)` to localize), the image's `contentDescription` otherwise. A button with no click handler is announced as disabled.

**Colors** (via `Theme.colors`):
- Container: `surface.primary`
- Content: `element.primary`

---

## NavChrome

A screen's navigation chrome, rendered by whichever navigation shell is active. Under the iOS 26 Liquid Glass native shell the `ScreenChrome` declaration is published to the native navigation bar (system back, toolbar buttons, native menus, live titles) and this composable renders nothing; everywhere else it renders a `TopNavBar` in place. Call it where the top bar belongs (a `Scaffold` `topBar` slot). Prefer it over raw `TopNavBar` for any screen that lives inside Synapse navigation: screens then never branch on the active shell.

```kotlin
// package com.ribads.synapse.ui.component.navchrome
@Composable fun NavChrome(
    chrome: ScreenChrome,
    modifier: Modifier = Modifier,            // applied to the Compose top bar; unused while the native bar renders the chrome
    onLeadingClick: (() -> Unit)? = null,     // handles the leading affordance; required for ChromeLeading.Close
    onAction: (id: String) -> Unit = {},      // receives chosen action/menu-item ids
)
```

`ScreenChrome`, `ChromeAction` (`Button`/`Menu`), `ChromeMenuItem`, `ChromeIcon` (`Drawable`/`SfSymbol`), `ChromeLeading`, `ChromeRole` and `ChromeTitleDisplay` come from `ui:chrome` (`com.ribads.synapse.ui.chrome`), which `ui:component` exposes as an `api` dependency. Full signatures are in the `/synapse:navigation` skill. Build chrome models outside composables.

`NavChrome` is the bar of a screen: declare at most one per screen. A header inside a sheet or dialog renders as a `TopNavBar` on every shell, because an overlay never takes the native bar; use `leading = ChromeLeading.Close` with `onLeadingClick` for its close button.

The leading affordance: the Compose top bar shows it only when `onLeadingClick` is non-null (a tab root omits the handler). A native shell draws and handles `ChromeLeading.Back` itself and never calls `onLeadingClick` for it. A system bar with no navigation stack behind it (`NativeChromeSink.handlesBack == false`, as [`SystemNavigationBar`](#systemnavigationbar) is used) follows the Compose rule: it shows Back only when `onLeadingClick` is non-null and reports the tap. `leading = null` removes the affordance on every shell, the native back button included.

Compose top bar rendering rules: actions render in declaration order, text and icon actions in any mix (`TopNavBarTrailingContentModel.Actions`); an icon action's `title` becomes its content description; a text action takes its role's intent (`Confirm` = emphasis, `Destructive` = error); a disabled action draws at `0.38` alpha and ignores taps; `Menu` actions open an anchored `DropdownMenu` at the bar's trailing edge; `subtitle` and `titleDisplay` are native-only and ignored.

## SystemNavigationBar

One screen's `ScreenChrome` on the platform's own navigation bar, which is Liquid Glass on iOS 26 or later. It is for a host that pages through screens inside one destination, where no navigation shell owns a bar: `ScreenNavigationHost` uses it for a document's pages. A screen inside Synapse navigation declares `NavChrome` instead and never calls this.

```kotlin
// package com.ribads.synapse.ui.component.navchrome
@Composable fun SystemNavigationBar(
    chrome: ScreenChrome,
    modifier: Modifier = Modifier,
    onEvent: (ChromeEvent) -> Unit,                         // every tap, the leading one included
)

@Composable fun systemNavigationBarInsets(): WindowInsets?  // what the bar covers; null where the platform has no bar to float
```

Where `systemNavigationBarInsets()` is null the bar draws nothing, so render `NavChrome` there. The bar has no stack behind it: it draws `ChromeLeading.Back` and `Close` as declared and reports `ChromeEvent.LeadingClicked` for both, so the host decides what leaving means. To have screens declare into it with `NavChrome`, provide a `NativeChromeSink` whose `handlesBack` is false through `LocalNativeChromeSink`, and the insets through `LocalNativeChromeInsets`, around each screen.

The title is always inline, and `subtitle` shows beneath it. A `Confirm` action is prominent in the theme's accent colour and sits at the trailing edge, a `Destructive` one takes the error colour, and a `Menu` opens a system menu. An icon uses its `sfSymbol` when it has one, otherwise its drawable. Place the bar at the top edge, beneath the status bar. It is a native view drawn above all Compose content on its window except sheets and dialogs, so leave it out while something should cover it.

## DropdownMenu

Anchored dropdown menu (Material 3 `DropdownMenu` themed with Synapse tokens). Place inside a `Box` together with the anchor content; the menu expands below the anchor. Destructive items render with the error color; disabled items dim and ignore taps.

```kotlin
// package com.ribads.synapse.ui.component.menu
@Composable fun DropdownMenu(
    model: MenuModel,
    expanded: Boolean,
    onDismissRequest: () -> Unit,
    onItemSelected: (id: String) -> Unit,
    modifier: Modifier = Modifier,
)
```

**Models** (`com.ribads.synapse.ui.component.menu.model`):
```kotlin
@Immutable
data class MenuModel(
    val items: List<MenuItemModel>,
)

@Immutable
data class MenuItemModel(
    val id: String,                     // reported to onItemSelected
    val label: Clause,
    val icon: Image? = null,            // 20dp leading icon
    val destructive: Boolean = false,   // error-color treatment
    val enabled: Boolean = true,
)
```

**Colors** (via `Theme.colors`):
- Container: `surface.raised`, with the items inside `WithRaisedSurface`
- Label: `element.primary`; destructive items `intents.error.content`

```kotlin
Box {
    IconButton(onClick = { expanded = true }) { /* anchor */ }
    DropdownMenu(
        model = MenuModel(items = listOf(
            MenuItemModel(id = "rename", label = "Rename".asText()),
            MenuItemModel(id = "delete", label = "Delete".asText(), destructive = true),
        )),
        expanded = expanded,
        onDismissRequest = { expanded = false },
        onItemSelected = { id -> expanded = false; onMenuAction(id) },
    )
}
```

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

**Anatomy**: a `surface.primary` bar with a 1dp `border.secondary` hairline along its top. Each item is an icon in a 56×32dp capsule drawn in `Theme.shape.chipShape` (a pill when the theme's chip shape is one), with an optional one-line label under it. The selected item's capsule fills with `intents.accent.surface` and its icon turns `intents.accent.content`. The capsule grows sideways out from behind the icon as it fades in. Icon tint, label colour and capsule are all driven by one selection animation, so they move together.

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


## SystemTabBar

The app's top-level destinations on the platform's own floating tab bar, which is Liquid Glass on iOS 26 or later. It takes the same `BottomNavigationBarModel` as `BottomNavigationBar`.

```kotlin
@Composable fun SystemTabBar(
    model: BottomNavigationBarModel,
    modifier: Modifier = Modifier,
    onItemSelected: (id: String) -> Unit,                  // every tap, the item already selected included
)

@Composable fun systemTabBarInsets(): WindowInsets?        // what the bar covers; null where the platform has no floating bar
```

Where `systemTabBarInsets()` is null the bar draws nothing, so use `BottomNavigationBar` there. Place it over the content at the bottom edge of the screen, and provide the insets through `LocalNativeChromeInsets` around that content, so a Synapse `Scaffold` rests clear of it:

```kotlin
val barInsets = systemTabBarInsets()
Scaffold(bottomBar = { if (barInsets == null) BottomNavigationBar(tabs, onItemSelected = onTab) }) { padding ->
    Box(Modifier.padding(padding)) {
        CompositionLocalProvider(LocalNativeChromeInsets provides barInsets) { Pages() }
        if (barInsets != null) SystemTabBar(tabs, Modifier.align(Alignment.BottomCenter), onTab)
    }
}
```

The bar is a native view drawn above all Compose content on its window except sheets and dialogs, so leave it out while something should cover it. It steps aside while the keyboard shows. An `Image.Glyph` takes the theme's accent colour, an `Image.Artwork` is drawn as authored, and `Image.Bitmap` or `Image.LocalIdentifier` shows its placeholder.

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
    shape = { Theme.shape.roundShape.topCornersOnly() },   // the theme's panel radius on the top corners
    scrimColor = { Theme.colors.overlay.scrim },
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
