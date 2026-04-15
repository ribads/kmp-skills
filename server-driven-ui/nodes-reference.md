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
| `Card` | Elevated container | `children`, `actionId` |
| `Expandable` | Collapsible section | `header` (UINode, required), `content` (List\<UINode\>), `initiallyExpanded` (Boolean), `stateKey` |

---

## Content Nodes

| Type | Key fields |
|------|-----------|
| `Text` | `content`, `style` (UITypographyToken), `textFormat` (UITextFormat), `conditionalTextFormat` (Map\<String, UITextFormat\>), `actionId`, `maxLines` |
| `MoneyText` | `amount` (Long, minor units), `currency` (ISO 4217), `style`, `textFormat` (UITextFormat), `stateKey` |
| `Image` | `url`, `contentDescription`, `actionId` |
| `Icon` | `url`, `adaptive` (Boolean), `actionId` |
| `RichText` | `content`, `style` (UITypographyToken) |

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
| `CurrencyField` | `label`, `placeholder`, `initialAmount` (Long), `currency` (String, default "GBP"), `stateKey`, `bind`, `onAmountChangeActionId` |
| `SelectionField` | `label`, `placeholder`, `value`, `isError`, `actionId` |
| `DropdownField` | `label`, `placeholder`, `options` (List\<UISelectionOption\>), `isError`, `footerText`, `stateKey`, `bind`, `onSelectionChangeActionId` |
| `TextArea` | `label`, `placeholder`, `initialValue`, `isError`, `footerText`, `stateKey`, `bind`, `onValueChangeActionId`, `minLines` (Int, default 4), `maxLines` (Int, default 4) |
| `ImagePicker` | `bind`, `placeholder` |
| `DatePicker` | `selectedDate` (Long?), `minDate` (Long?), `maxDate` (Long?), `stateKey`, `onDateSelectedActionId` |
| `NumberField` | `label`, `placeholder`, `min` (Double?), `max` (Double?), `step` (Double, default 1.0), `decimals` (Int, default 0), `stateKey`, `bind`, `onValueChangeActionId` |
| `SearchBar` | `placeholder` (default "Search..."), `stateKey`, `bind` |
| `RatingInput` | `maxStars` (Int, default 5), `stateKey`, `bind`, `onRatingChangeActionId` |
| `ChipGroup` | `options` (List\<UISelectionOption\>), `multiSelect` (Boolean), `stateKey`, `bind`, `onSelectionChangeActionId` |
| `Slider` | `min` (Float, default 0), `max` (Float, default 1), `step` (Float), `showValue` (Boolean), `label`, `stateKey`, `bind`, `onValueChangeActionId` |
| `Stepper` | `min` (Int, default 0), `max` (Int), `step` (Int, default 1), `label`, `stateKey`, `bind`, `onValueChangeActionId` |
| `TimePicker` | `label`, `is24Hour` (Boolean, default true), `stateKey`, `bind`, `onTimeChangeActionId` |

**UISelectionOption**: `key` (String), `label` (String)

---

## Toggle / Progress Nodes

| Type | Key fields |
|------|-----------|
| `Checkbox` | `label`, `bind`, `stateKey`, `onToggleActionId` |
| `RadioGroup` | `options` (List\<UISelectionOption\>), `orientation` (UIOrientation, default Vertical), `stateKey`, `bind`, `onSelectionChangeActionId` |
| `ProgressBar` | `value` (String, default "0"), `max` (String, default "1"), `label`, `showPercentage` (Boolean), `color` (hex), `animate` (Boolean, default true) |
| `CircularProgress` | `value` (String, default "0"), `max` (String, default "1"), `label`, `showPercentage` (Boolean, default true), `color` (hex), `animate` (Boolean, default true) |

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
| `EmptyState` | `iconUrl`, `title`, `subtitle`, `actionLabel`, `actionId` |

**UITab**: `label` (String), `content` (List\<UINode\>)

---

## Navigation Nodes

**TopNavBar** — top navigation bar with optional leading icon, title, and trailing actions. Designed for the `Scaffold.topBar` slot.

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

When both `iconUrl` and `label` are set, the icon is rendered and the label is used as content-description.

---

## Chart Nodes

| Type | Key fields |
|------|-----------|
| `BarChart` | `series` (List\<UIChartSeries\>), `title`, `showGrid`, `showValues`, `animate`, `cornerRadius` (Float, default 8), `dataSource`, `valueField`, `labelField`, `filter` (DataCondition?) |
| `LineChart` | `series` (List\<UIChartSeries\>), `title`, `showGrid`, `showDots`, `smoothCurve`, `showArea`, `animate`, `lineWidth` (Float, default 3), `dotRadius` (Float, default 5), `dataSource`, `valueField`, `labelField`, `filter` (DataCondition?) |
| `PieChart` | `slices` (List\<UIPieSlice\>), `title`, `donutFraction` (Float, default 0), `showPercentages`, `showLegend`, `animate`, `dataSource`, `valueField`, `labelField`, `filter` (DataCondition?) |

**UIChartSeries**: `entries` (List\<UIChartEntry\>), `label` (String?), `color` (hex String?)
**UIChartEntry**: `value` (Float), `label` (String)
**UIPieSlice**: `value` (Float), `label` (String?), `color` (hex String?)

---

## Meta Nodes

| Type | Key fields |
|------|-----------|
| `Conditional` | `conditionKey` (String, required), `thenNode` (UINode, required), `elseNode` (UINode?) |
| `Unknown` | (renders nothing — forward-compatible fallback) |

---

## Data-Bound Node Extensions

These fields were added to existing node types for data layer integration.

### LazyColumn (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to bind to. When set, children are ignored and `itemTemplate` is rendered per record. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. Supports `{{item.field}}` template interpolation. |
| `filter` | `DataCondition?` | Optional condition to filter which records are displayed. |
| `groupBy` | `String?` | Field name to group records by. |
| `groupHeader` | `UINode?` | Template for group headers. Supports `{{group.key}}` interpolation. |
| `searchKey` | `String?` | State key for a search query. |
| `searchFields` | `List<String>` | Record fields to match against the search query. |

### LazyRow (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to bind to. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. |
| `filter` | `DataCondition?` | Optional condition to filter records. |
| `searchKey` | `String?` | State key for a search query. |
| `searchFields` | `List<String>` | Record fields to match against the search query. |

### LazyGrid (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `columns` | `Int` | Number of grid columns (default 2). |
| `dataSource` | `String?` | Collection name to bind to. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. |
| `filter` | `DataCondition?` | Optional condition to filter records. |
| `searchKey` | `String?` | State key for a search query. |
| `searchFields` | `List<String>` | Record fields to match against the search query. |

### Button Nodes (all 4 types)

| Field | Type | Description |
|-------|------|-------------|
| `stateCondition` | `String?` | Named condition key. When set, button is `Enabled` when condition is true, `Disabled` when false. Overrides `state`. |

### Input Nodes (TextField, PasswordField, CurrencyField, TextArea)

| Field | Type | Description |
|-------|------|-------------|
| `bind` | `String?` | Declared field name to bind to. Preferred over `stateKey` when using the data layer. |

### Chart Nodes (data-bound mode)

All three chart types (BarChart, LineChart, PieChart) support data binding:

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to pull entries from. When set, `series`/`slices` are ignored. |
| `valueField` | `String?` | Record field for the numeric value. |
| `labelField` | `String?` | Record field for the entry label. |
| `filter` | `DataCondition?` | Optional condition to filter records. |

### Template Interpolation

Inside `itemTemplate` nodes, text content supports `{{item.field}}` patterns that resolve to the current record's field value at render time.
