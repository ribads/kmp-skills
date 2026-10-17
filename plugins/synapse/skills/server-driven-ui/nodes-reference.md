# Node Types Reference

## Base Fields (all nodes)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `String?` | Optional node identifier |
| `modifier` | `UIModifier?` | Styling/layout modifiers |
| `visibility` | `UIVisibility?` | Rendering visibility control |

---

## Layout Nodes

| Type | Maps to | Key fields |
|------|---------|-----------|
| `Column` | Compose `Column` | `children`, `verticalArrangement`, `horizontalAlignment` |
| `Row` | Compose `Row` | `children`, `horizontalArrangement`, `verticalAlignment` |
| `Box` | Compose `Box` | `children`, `contentAlignment` |
| `LazyColumn` | Compose `LazyColumn` | `children`, `verticalArrangement` |
| `LazyRow` | Compose `LazyRow` | `children`, `horizontalArrangement`, `verticalAlignment` |
| `LazyGrid` | Compose `LazyVerticalGrid` | `columns` (Int, default 2), `children`, `verticalArrangement`, `horizontalArrangement` |
| `Spacer` | Compose `Spacer` | (modifier only) |
| `Card` | Surface container; children stack like a `Box`, so wrap several in a `Column` | `children`, `actionId` |
| `Expandable` | Collapsible section | `header` (UINode, required), `content` (List\<UINode\>), `initiallyExpanded` (Boolean), `stateKey` |

---

## Content Nodes

| Type | Key fields |
|------|-----------|
| `Text` | `content` (templates), `style` (UITypographyToken), `textFormat` (UITextFormat), `conditionalTextFormat` (Map\<String, UITextFormat\>), `actionId`, `maxLines` |
| `MoneyText` | `amount` (Long, minor units), `currency` (ISO 4217, matched ignoring case; one of NGN, GBP, USD, EUR, JPY, CHF, CAD, AUD, NZD, CNY, HKD, any other draws nothing and is reported through `onNodeRenderError`), `style`, `textFormat` (UITextFormat), `stateKey` |
| `Image` | `url` (templates), `contentDescription`, `actionId` |
| `Icon` | `url`, `adaptive` (Boolean: tint the icon with the surrounding content colour, `element.primary` by default), `actionId` |
| `RichText` | `content` (markdown, templates), `style` (UITypographyToken) |

---

## Button Nodes

Shared fields: `title`, `leadingImageUrl`, `trailingImageUrl`, `state`, `stateCondition`, `actionId`

| Type | Style |
|------|-------|
| `PrimaryButton` | Filled, high-emphasis |
| `OutlineButton` | Outlined, medium-emphasis |
| `SmallButton` | Compact filled |
| `SmallOutlineButton` | Compact outlined |

`UIButtonState`: `Enabled`, `Disabled`, `Loading`

---

## Input Nodes

| Type | Key fields |
|------|-----------|
| `TextField` | `label`, `placeholder`, `initialValue`, `isError`, `footerText`, `stateKey`, `bind`, `onValueChangeActionId` |
| `PasswordField` | Same as TextField |
| `CurrencyField` | `label`, `placeholder`, `initialAmount` (Long), `currency` (String, default "GBP"; same supported set as `MoneyText`, any other draws nothing and is reported), `stateKey`, `bind`, `onAmountChangeActionId` |
| `SelectionField` | `label`, `placeholder`, `value`, `isError`, `actionId` |
| `DropdownField` | `label`, `placeholder`, `options` (List\<UISelectionOption\>), `isError`, `footerText`, `stateKey`, `bind`, `onSelectionChangeActionId` |
| `TextArea` | `label`, `placeholder`, `initialValue`, `isError`, `footerText`, `stateKey`, `bind`, `onValueChangeActionId`, `minLines` (Int, default 4), `maxLines` (Int, default 4) |
| `ImagePicker` | `bind`, `placeholder` |
| `DatePicker` | `selectedDate` (Long?), `minDate` (Long?), `maxDate` (Long?), `stateKey` (no `bind`), `onDateSelectedActionId` |
| `NumberField` | `label`, `placeholder`, `min` (Double?), `max` (Double?), `step` (Double?, default null: on leaving the field the value snaps to the nearest multiple of `step` from `min` or zero, staying in range; see `committedValue`), `decimals` (Int, default 0), `stateKey`, `bind`, `onValueChangeActionId` |
| `SearchBar` | `placeholder` (default "Search..."), `stateKey`, `bind` |
| `RatingInput` | `maxStars` (Int, default 5), `stateKey`, `bind`, `onRatingChangeActionId` |
| `ChipGroup` | `options` (List\<UISelectionOption\>), `multiSelect` (Boolean), `stateKey`, `bind`, `onSelectionChangeActionId` |
| `Slider` | `min` (Float, default 0), `max` (Float, default 1), `step` (Float), `showValue` (Boolean), `label`, `stateKey`, `bind`, `onValueChangeActionId` |
| `Stepper` | `min` (Int, default 0), `max` (Int, default `Int.MAX_VALUE`), `step` (Int, default 1), `label`, `stateKey`, `bind`, `onValueChangeActionId` |
| `TimePicker` | `label`, `is24Hour` (Boolean, default true), `stateKey`, `bind`, `onTimeChangeActionId` |
| `Timer` | `label`, `autoStart` (Boolean, default false), `stateKey`, `bind` |

**UISelectionOption**: `key` (String), `label` (String)

---

## Toggle / Progress Nodes

| Type | Key fields |
|------|-----------|
| `Checkbox` | `label` (templates), `bind`, `stateKey`, `onToggleActionId` |
| `RadioGroup` | `options` (List\<UISelectionOption\>), `orientation` (UIOrientation, default Vertical), `stateKey`, `bind`, `onSelectionChangeActionId` |
| `ProgressBar` | `value` (String, default "0", templates), `max` (String, default "1", templates), `label` (templates), `showPercentage` (Boolean), `color` (hex), `animate` (Boolean, default true) |
| `CircularProgress` | `value` (String, default "0", templates), `max` (String, default "1", templates), `label` (templates), `showPercentage` (Boolean, default true), `color` (hex), `animate` (Boolean, default true) |

---

## Structured Component Nodes

| Type | Key fields |
|------|-----------|
| `Divider` | (modifier only) |
| `Scaffold` | `topBar` (UINode?), `bottomBar` (UINode?), `content` (List\<UINode\>) |
| `TopNavBar` | `title`, `leadingIcon` (UINavBarLeadingIcon?), `trailingActions` (List\<UINavBarAction\>) |
| `Tray` | `content` (List\<UINode\>), `dismissActionId`, `isSwipeDismissible` (Boolean, default true) |
| `TabLayout` | `tabs` (List\<UITab\>), `stateKey` |
| `ConfirmDialog` | `title`, `message`, `confirmLabel` (default "Confirm"), `cancelLabel` (default "Cancel"), `confirmActionId`, `stateKey` |
| `EmptyState` | `iconUrl`, `title` (templates), `subtitle` (templates), `actionLabel`, `actionId` |

**UITab**: `label` (String), `content` (List\<UINode\>)

---

## Navigation Nodes

**TopNavBar**: top navigation bar with optional leading icon, title, and trailing actions. Designed for the `Scaffold.topBar` slot.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | `String` | `""` | Title text (supports `{{key}}` templates) |
| `leadingIcon` | `UINavBarLeadingIcon?` | `null` | Optional leading icon |
| `trailingActions` | `List<UINavBarAction>` | `[]` | Trailing action buttons |

**UINavBarLeadingIcon** (sealed, type-discriminated):

| Type | Fields | Icon |
|------|--------|------|
| `back` | `actionId: String` | Left arrow |
| `close` | `actionId: String` | X |
| `menu` | `actionId: String` | Hamburger |
| `custom` | `iconUrl: String`, `actionId: String` | Custom bitmap |

**UINavBarAction**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | `String?` | `null` | Text label (renders as text button) |
| `iconUrl` | `String?` | `null` | Icon URL (renders as icon button) |
| `actionId` | `String` | `""` | Action dispatched on tap |

The bar shows either a row of icons or one text action, never both:

- An action with an icon draws the icon; its `label`, when set, is the icon's accessibility description.
- When every drawable action has an icon, all of them render as icons.
- Otherwise only the first action with a `label` renders, as text; the others are not shown.
- An action with neither `iconUrl` nor `label` draws nothing (blank strings count as absent).

---

## Chart Nodes

| Type | Key fields |
|------|-----------|
| `BarChart` | `series` (List\<UIChartSeries\>), `title`, `showGrid`, `showValues`, `animate`, `cornerRadius` (Float, default 8), `dataSource`, `valueField`, `labelField`, `filter` (DataCondition?) |
| `LineChart` | `series` (List\<UIChartSeries\>), `title`, `showGrid`, `showDots`, `smoothCurve`, `showArea`, `animate`, `lineWidth` (Float, default 3), `dotRadius` (Float, default 5), `dataSource`, `valueField`, `labelField`, `filter` (DataCondition?) |
| `PieChart` | `slices` (List\<UIPieSlice\>), `title`, `donutFraction` (Float, default 0), `showPercentages`, `showLegend`, `animate`, `dataSource`, `valueField`, `labelField`, `filter` (DataCondition?) |

**UIChartSeries**: `entries` (List\<UIChartEntry\>), `label` (String?), `color` (hex String?)
**UIChartEntry**: `value` (Float), `label` (String, default "")
**UIPieSlice**: `value` (Float), `label` (String?), `color` (hex String?)

---

## Meta Nodes

| Type | Key fields |
|------|-----------|
| `Conditional` | `conditionKey` (String, required), `thenNode` (UINode, required), `elseNode` (UINode?) |
| `Unknown` | (renders nothing; forward-compatible fallback, reported through `onUnknownNode` under its original `type`, kept in `typeName`) |

---

## Data-Bound Node Extensions

These fields were added to existing node types for data layer integration.

### LazyColumn (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to bind to. When set with an `itemTemplate`, the template renders per record and `children` still render first, as leading items. Without a data layer (no `CollectionProvider`) the collection is empty. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. Supports `{{item.field}}` and the 1-based `{{item._index}}`. |
| `filter` | `DataCondition?` | Optional condition to filter which records are displayed. |
| `groupBy` | `String?` | Field name to group records by. |
| `groupHeader` | `UINode?` | Template for group headers. Reads `{{item.group.key}}` and `{{item.group.count}}`; a bare `{{group.key}}` does not resolve. |
| `searchKey` | `String?` | State key for a search query. |
| `searchFields` | `List<String>` | Record fields to match against the search query. |

### LazyRow (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to bind to. `children` still render first, as leading items. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. |
| `filter` | `DataCondition?` | Optional condition to filter records. |
| `searchKey` | `String?` | State key for a search query. |
| `searchFields` | `List<String>` | Record fields to match against the search query. |

### LazyGrid (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `columns` | `Int` | Number of grid columns (default 2). Fewer than 1 is reported and drawn with one. |
| `dataSource` | `String?` | Collection name to bind to. `children` still render first, as leading items. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. |
| `filter` | `DataCondition?` | Optional condition to filter records. |
| `searchKey` | `String?` | State key for a search query. |
| `searchFields` | `List<String>` | Record fields to match against the search query. |

### Button Nodes (all 4 types)

| Field | Type | Description |
|-------|------|-------------|
| `stateCondition` | `String?` | Named condition key. When set, button is `Enabled` when condition is true, `Disabled` when false. Overrides `state`. |

### Input Nodes

Every stateful input takes `bind`: TextField, PasswordField, CurrencyField, DropdownField, TextArea, ImagePicker, NumberField, SearchBar, RatingInput, ChipGroup, Slider, Stepper, Timer, TimePicker, Checkbox, and RadioGroup. DatePicker, TabLayout, Expandable, and ConfirmDialog take `stateKey` only.

| Field | Type | Description |
|-------|------|-------------|
| `bind` | `String?` | Declared field name to bind to. Wins over `stateKey`; preferred when using the data layer. |

### Chart Nodes (data-bound mode)

All three chart types (BarChart, LineChart, PieChart) support data binding:

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to pull entries from. Takes effect only together with `labelField`; then `series`/`slices` are ignored. |
| `valueField` | `String?` | Record field summed per label. Unset: each entry counts the records with that label. |
| `labelField` | `String?` | Record field to group by; one entry per distinct label, in first-seen order. Required for data binding. |
| `filter` | `DataCondition?` | Optional condition to filter records. |

### Template Interpolation

Templated fields are marked "(templates)" above. They resolve `{{key}}` from state (long, then double, then string lane), `{{item.field}}` from the current record inside an `itemTemplate`, and `{{name.count}}` from a collection's size, with pipes such as `{{total | number:2}}`. Every templated field re-resolves when the state or the counted collection changes.
