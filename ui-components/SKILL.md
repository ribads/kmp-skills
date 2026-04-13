---
name: ui-components
description: Use when implementing buttons, text fields, password fields, phone inputs, currency inputs, date pickers, cards, dividers, scaffolds, trays, bottom sheets, checkboxes, progress bars, circular progress, rating inputs, chip groups, tab layouts, sliders, timers, steppers, time pickers, confirm dialogs, empty states, radio groups, bar charts, line charts, or pie charts in a KMP Compose project.
user-invocable: true
---

# ui:component — Reusable UI Components

**Module**: `ui:component` | **Artifact**: `com.ribads.synapse:ui-component`
**Package**: `com.ribads.synapse.ui.component`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-component:<version>")
}
```

Depends on `ui:element`.

---

## Buttons

```kotlin
@Composable fun PrimaryButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: (() -> Unit)?, invertedColors: Boolean = isSystemInDarkTheme())
@Composable fun SmallButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback, invertedColors: Boolean = isSystemInDarkTheme())
@Composable fun OutlineButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, style: ButtonStyle = ButtonStyle.Regular, onClick: OptionalClickCallback, invertedColors: Boolean = isSystemInDarkTheme())
@Composable fun SmallOutlineButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback, invertedColors: Boolean = isSystemInDarkTheme())

@Immutable
data class ButtonModel(val title: Clause, val leadingImage: Image? = null, val trailingImage: Image? = null)
enum class ButtonState { Enabled, Disabled, Loading }
enum class ButtonStyle { Regular, Small }

fun Clause.asButton() = ButtonModel(leadingImage = null, trailingImage = null, title = this)
```

---

## Text Fields

```kotlin
@Composable fun LabelTextField(
    model: TextInputModel, readOnly: Boolean = false, singleLine: Boolean = true,
    minLines: Int = 1, maxLines: Int = 1, borderWidth: Dp = 0.5.dp,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    modifier: Modifier = Modifier,
    visualTransformation: VisualTransformation = VisualTransformation.None,
    interactionSource: MutableInteractionSource = remember { MutableInteractionSource() },
    onValueChange: (String) -> Unit,
    leadingContent: @Composable (RowScope.() -> Unit)? = null,
    trailingContent: @Composable (() -> Unit)? = null,
    invertedColors: Boolean = isSystemInDarkTheme()
)

@Composable fun PasswordTextField(
    model: TextInputModel,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    modifier: Modifier = Modifier,
    onValueChange: (String) -> Unit,
    onPasswordToggleChange: ((Boolean) -> Unit)? = null,
    invertedColors: Boolean = isSystemInDarkTheme()
)

@Composable fun PhoneTextField(
    model: PhoneInputModel, modifier: Modifier = Modifier,
    onPhoneNumberChanged: (String) -> Unit,
    onCountryCodePickClick: OptionalClickCallback,
    invertedColors: Boolean = isSystemInDarkTheme()
)

@Composable fun CurrencyTextField(
    model: CurrencyInputModel, readOnly: Boolean = false, modifier: Modifier = Modifier,
    onClick: OptionalClickCallback = null,
    onAmountChanged: (Long?) -> Unit,
    dropDownContent: @Composable ((Dp) -> Unit)? = null,
    invertedColors: Boolean = isSystemInDarkTheme()
)

@Composable fun SelectionTextField(
    model: TextInputModel, modifier: Modifier = Modifier,
    trailingIcon: Image = Image.Drawable(Res.drawable.sc_icon_chevron_down),
    onClick: OptionalClickCallback,
    invertedColors: Boolean = isSystemInDarkTheme()
)

@Composable fun TextArea(
    model: TextInputModel, minLines: Int = 4, maxLines: Int = 4,
    modifier: Modifier = Modifier,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    onValueChange: (value: String) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme()
)
```

### Text Field Models

```kotlin
@Stable
data class TextInputModel(
    val label: Clause?, val value: String, val placeholder: Clause,
    val isError: Boolean = false, val footerText: Clause? = null,
) {
    companion object { val Default: TextInputModel }
}

@Immutable
data class PhoneInputModel(
    val label: Clause, val value: String, val placeholder: Clause,
    val countryCode: String, val countryFlag: Clause? = null,
    val isError: Boolean = false, val footerText: Clause? = null,
) {
    companion object { val Default: PhoneInputModel }
}

@Immutable
data class CurrencyInputModel(
    val label: Clause, val amount: CurrencyAmount, val placeholder: Clause,
    val isError: Boolean = false, val footerText: Clause? = null,
)

@Immutable
data class CurrencyAmount(val amount: Long, val currency: Currency = Currency.USD) {
    fun toValue(): String
}

object CountryLocale {
    fun getCountryDialingCode(countryCode: String): String?
    fun getCountryCodes(): List<String>
    fun getCountryDialCodes(): Map<String, String>
}
```

---

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

---

## Checkbox

Animated checkbox with optional label. Custom Canvas-drawn checkmark — no Material3.

```kotlin
@Composable fun LabelCheckbox(
    model: CheckboxModel,
    modifier: Modifier = Modifier,
    onCheckedChange: (Boolean) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class CheckboxModel(
    val label: Clause? = null,
    val checked: Boolean = false,
    val enabled: Boolean = true,
)
```

---

## Progress

### ProgressBar

Animated horizontal progress bar. Custom Canvas track with rounded corners.

```kotlin
@Composable fun ProgressBar(
    model: ProgressBarModel,
    modifier: Modifier = Modifier,
    animate: Boolean = true,
    overrideColor: Color? = null,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class ProgressBarModel(
    val value: Float = 0f,
    val max: Float = 1f,
    val label: Clause? = null,
    val showPercentage: Boolean = false,
    val color: String? = null,
) {
    val fraction: Float get() = if (max > 0f) (value / max).coerceIn(0f, 1f) else 0f
}
```

### CircularProgress

Animated circular arc with percentage text in center. Custom Canvas-drawn — no Material3.

```kotlin
@Composable fun CircularProgress(
    model: CircularProgressModel,
    modifier: Modifier = Modifier,
    animate: Boolean = true,
    overrideColor: Color? = null,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class CircularProgressModel(
    val value: Float = 0f,
    val max: Float = 1f,
    val label: Clause? = null,
    val showPercentage: Boolean = true,
    val color: String? = null,
) {
    val fraction: Float get() = if (max > 0f) (value / max).coerceIn(0f, 1f) else 0f
}
```

---

## Rating

Star-based rating input. Custom Canvas-drawn filled/empty stars.

```kotlin
@Composable fun RatingInput(
    model: RatingInputModel,
    modifier: Modifier = Modifier,
    starSize: Dp = 28.dp,
    onRatingChange: (Int) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class RatingInputModel(
    val rating: Int = 0,
    val maxStars: Int = 5,
    val enabled: Boolean = true,
)
```

---

## Chips

Multi/single-select chip group using `FlowRow` layout.

```kotlin
@Composable fun ChipGroup(
    model: ChipGroupModel,
    modifier: Modifier = Modifier,
    onSelectionChange: (Set<String>) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class ChipGroupModel(
    val options: List<ChipOption> = emptyList(),
    val selectedKeys: Set<String> = emptySet(),
    val multiSelect: Boolean = false,
)

@Stable
data class ChipOption(
    val key: String,
    val label: Clause,
)
```

---

## Tab Layout

Tab bar with indicator + content slot keyed by selected index.

```kotlin
@Composable fun TabLayout(
    model: TabLayoutModel,
    modifier: Modifier = Modifier,
    onTabSelected: (Int) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
    content: @Composable (selectedIndex: Int) -> Unit,
)

@Stable
data class TabLayoutModel(
    val tabs: List<TabItem> = emptyList(),
    val selectedIndex: Int = 0,
)

@Stable
data class TabItem(
    val label: Clause,
)
```

---

## Radio Group

Custom Canvas-drawn radio buttons with inner dot. Supports vertical and horizontal orientation.

```kotlin
@Composable fun RadioGroup(
    model: RadioGroupModel,
    modifier: Modifier = Modifier,
    horizontal: Boolean = false,
    onSelectionChange: (String) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class RadioGroupModel(
    val options: List<RadioOption>,
    val selectedKey: String? = null,
)

@Stable
data class RadioOption(
    val key: String,
    val label: Clause,
)
```

---

## Slider

Custom Canvas track + thumb with pointer input for tap/drag and step snapping.

```kotlin
@Composable fun Slider(
    model: SliderModel,
    modifier: Modifier = Modifier,
    onValueChange: (Float) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class SliderModel(
    val value: Float = 0f,
    val min: Float = 0f,
    val max: Float = 1f,
    val step: Float = 0f,
    val label: Clause? = null,
    val showValue: Boolean = false,
    val enabled: Boolean = true,
)
```

---

## Stepper

Increment/decrement control with circular bordered `+`/`-` buttons and min/max clamping.

```kotlin
@Composable fun Stepper(
    model: StepperModel,
    modifier: Modifier = Modifier,
    onValueChange: (Int) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class StepperModel(
    val value: Int = 0,
    val min: Int = 0,
    val max: Int = Int.MAX_VALUE,
    val step: Int = 1,
    val label: Clause? = null,
    val enabled: Boolean = true,
)
```

---

## Timer

Label + formatted time display (`HH:MM:SS`) with Start/Stop and Reset buttons.

```kotlin
@Composable fun Timer(
    model: TimerModel,
    modifier: Modifier = Modifier,
    onStartStop: () -> Unit,
    onReset: () -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class TimerModel(
    val elapsedMs: Long = 0L,
    val running: Boolean = false,
    val label: Clause? = null,
)
```

---

## Time Picker

Hour/minute spinners with up/down arrows. Supports 12h (AM/PM toggle) and 24h modes.

```kotlin
@Composable fun TimePicker(
    model: TimePickerModel,
    modifier: Modifier = Modifier,
    onTimeChange: (hour: Int, minute: Int) -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class TimePickerModel(
    val hour: Int = 0,
    val minute: Int = 0,
    val is24Hour: Boolean = true,
    val label: Clause? = null,
)
```

---

## Confirm Dialog

Modal dialog with scrim overlay, surface card, title/message, and confirm/cancel buttons. Uses `Popup` — no Material3 `AlertDialog`.

```kotlin
@Composable fun ConfirmDialog(
    model: ConfirmDialogModel,
    modifier: Modifier = Modifier,
    onConfirm: () -> Unit,
    onCancel: () -> Unit,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class ConfirmDialogModel(
    val title: Clause,
    val message: Clause,
    val confirmLabel: Clause,
    val cancelLabel: Clause,
)
```

---

## Empty State

Centered placeholder for empty screens — optional icon, title, subtitle, and action button.

```kotlin
@Composable fun EmptyState(
    model: EmptyStateModel,
    modifier: Modifier = Modifier,
    onActionClick: (() -> Unit)? = null,
    invertedColors: Boolean = isSystemInDarkTheme(),
)

@Stable
data class EmptyStateModel(
    val icon: Image? = null,
    val title: Clause,
    val subtitle: Clause? = null,
    val actionLabel: Clause? = null,
)
```

---

## Usage

```kotlin
// Button
PrimaryButton(
    model = "Submit".asText().asButton(),
    state = if (isLoading) ButtonState.Loading else ButtonState.Enabled,
    onClick = { viewModel.emit(Intent.OnSubmit) }
)

// Text field
LabelTextField(
    model = TextInputModel(label = "Email".asText(), value = email, placeholder = "Enter email".asText()),
    onValueChange = { email = it }
)

// Date picker in bottom sheet
DatePickerBottomSheet(
    isVisible = showPicker,
    model = DatePickerModel(selectedDate = selectedMs, minDate = null, maxDate = null),
    onDateSelected = { millis -> selectedMs = millis },
    onDismissRequest = { showPicker = false }
)

// Scaffold
Scaffold(topBar = { /* toolbar */ }) { padding ->
    Column(Modifier.padding(padding)) { /* content */ }
}

// Tray with a sticky primary action
Tray(
    onDismissRequest = { viewModel.emit(Intent.DismissSheet) },
    stickyBottom = {
        PrimaryButton(
            model = "Confirm".asText().asButton(),
            onClick = { viewModel.emit(Intent.Confirm) }
        )
    }
) {
    Column { /* form fields */ }
}

// ScrollableTray wrapping a LazyColumn — caller renders its own close button
ScrollableTray(onDismissRequest = { viewModel.emit(Intent.DismissSheet) }) {
    Column {
        Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
            IconButton(onClick = { viewModel.emit(Intent.DismissSheet) }) { /* close icon */ }
        }
        LazyColumn { items(rows) { RowItem(it) } }
    }
}

// Checkbox
LabelCheckbox(
    model = CheckboxModel(label = "Accept terms".asText(), checked = isChecked),
    onCheckedChange = { isChecked = it }
)

// ProgressBar
ProgressBar(
    model = ProgressBarModel(value = 75f, max = 100f, label = "Upload".asText(), showPercentage = true)
)

// CircularProgress
CircularProgress(
    model = CircularProgressModel(value = 72f, max = 100f, label = "Daily Goal".asText())
)

// RatingInput
RatingInput(
    model = RatingInputModel(rating = 3, maxStars = 5),
    onRatingChange = { newRating -> rating = newRating }
)

// ChipGroup — single select
ChipGroup(
    model = ChipGroupModel(
        options = listOf(ChipOption("s", "Small".asText()), ChipOption("m", "Medium".asText()), ChipOption("l", "Large".asText())),
        selectedKeys = setOf(selectedSize),
    ),
    onSelectionChange = { selectedSize = it.first() }
)

// ChipGroup — multi select
ChipGroup(
    model = ChipGroupModel(
        options = listOf(ChipOption("a", "Android".asText()), ChipOption("i", "iOS".asText()), ChipOption("w", "Web".asText())),
        selectedKeys = selectedPlatforms,
        multiSelect = true,
    ),
    onSelectionChange = { selectedPlatforms = it }
)

// TabLayout
TabLayout(
    model = TabLayoutModel(tabs = listOf(TabItem("Overview".asText()), TabItem("Details".asText())), selectedIndex = tab),
    onTabSelected = { tab = it },
) { selectedIndex ->
    when (selectedIndex) {
        0 -> OverviewContent()
        1 -> DetailsContent()
    }
}

// RadioGroup — vertical
RadioGroup(
    model = RadioGroupModel(
        options = listOf(RadioOption("sm", "Small".asText()), RadioOption("md", "Medium".asText()), RadioOption("lg", "Large".asText())),
        selectedKey = selectedSize,
    ),
    onSelectionChange = { selectedSize = it }
)

// RadioGroup — horizontal
RadioGroup(
    model = RadioGroupModel(
        options = listOf(RadioOption("y", "Yes".asText()), RadioOption("n", "No".asText())),
        selectedKey = answer,
    ),
    horizontal = true,
    onSelectionChange = { answer = it }
)

// Slider
Slider(
    model = SliderModel(value = severity, min = 1f, max = 10f, step = 1f, label = "Severity".asText(), showValue = true),
    onValueChange = { severity = it }
)

// Stepper
Stepper(
    model = StepperModel(value = quantity, min = 0, max = 20, step = 1, label = "Quantity".asText()),
    onValueChange = { quantity = it }
)

// Timer
Timer(
    model = TimerModel(elapsedMs = elapsed, running = isRunning, label = "Workout".asText()),
    onStartStop = { isRunning = !isRunning },
    onReset = { elapsed = 0L; isRunning = false }
)

// TimePicker
TimePicker(
    model = TimePickerModel(hour = hour, minute = minute, is24Hour = true, label = "Alarm".asText()),
    onTimeChange = { h, m -> hour = h; minute = m }
)

// ConfirmDialog
ConfirmDialog(
    model = ConfirmDialogModel(
        title = "Delete item?".asText(),
        message = "This action cannot be undone.".asText(),
        confirmLabel = "Delete".asText(),
        cancelLabel = "Cancel".asText(),
    ),
    onConfirm = { viewModel.emit(Intent.ConfirmDelete) },
    onCancel = { showDialog = false }
)

// EmptyState
EmptyState(
    model = EmptyStateModel(
        icon = Image.Drawable(Res.drawable.ic_empty),
        title = "No items yet".asText(),
        subtitle = "Add your first item to get started".asText(),
        actionLabel = "Add Item".asText(),
    ),
    onActionClick = { viewModel.emit(Intent.AddItem) }
)
```

---

## Charts

### Bar Chart

```kotlin
@Composable fun BarChart(
    model: BarChartModel, modifier: Modifier = Modifier,
    height: Dp = 240.dp, invertedColors: Boolean = isSystemInDarkTheme(),
)
```

### Line Chart

```kotlin
@Composable fun LineChart(
    model: LineChartModel, modifier: Modifier = Modifier,
    height: Dp = 240.dp, invertedColors: Boolean = isSystemInDarkTheme(),
)
```

### Pie Chart

```kotlin
@Composable fun PieChart(
    model: PieChartModel, modifier: Modifier = Modifier,
    invertedColors: Boolean = isSystemInDarkTheme(),
)
```

### Chart Models

```kotlin
@Immutable
data class ChartEntry(val value: Float, val label: String = "")

@Immutable
data class ChartSeries(
    val entries: List<ChartEntry>,
    val label: Clause? = null,
    val color: Color? = null,
)

@Immutable
data class PieSlice(
    val value: Float,
    val label: Clause? = null,
    val color: Color? = null,
)

@Immutable
data class PieChartModel(
    val slices: List<PieSlice>,
    val title: Clause? = null,
    val donutFraction: Float = 0f,       // 0f = full pie, 0.6f = typical donut
    val showPercentages: Boolean = true,
    val showLegend: Boolean = true,
    val animate: Boolean = true,
)

@Immutable
data class BarChartModel(
    val series: List<ChartSeries>,
    val title: Clause? = null,
    val showGrid: Boolean = true,
    val showValues: Boolean = false,
    val animate: Boolean = true,
    val cornerRadius: Float = 8f,
) {
    companion object {
        // Single-series convenience constructor
        operator fun invoke(
            entries: List<ChartEntry>, title: Clause? = null, color: Color? = null,
            showGrid: Boolean = true, showValues: Boolean = false,
            animate: Boolean = true, cornerRadius: Float = 8f,
        ): BarChartModel
    }
}

@Immutable
data class LineChartModel(
    val series: List<ChartSeries>,
    val title: Clause? = null,
    val showGrid: Boolean = true,
    val showDots: Boolean = true,
    val smoothCurve: Boolean = true,
    val showArea: Boolean = false,
    val animate: Boolean = true,
    val lineWidth: Float = 3f,
    val dotRadius: Float = 5f,
) {
    companion object {
        // Single-series convenience constructor
        operator fun invoke(
            entries: List<ChartEntry>, title: Clause? = null, color: Color? = null,
            showGrid: Boolean = true, showDots: Boolean = true,
            smoothCurve: Boolean = true, showArea: Boolean = false,
            animate: Boolean = true, lineWidth: Float = 3f, dotRadius: Float = 5f,
        ): LineChartModel
    }
}
```

### Chart Usage

```kotlin
// Simple bar chart
BarChart(
    model = BarChartModel(
        entries = listOf(
            ChartEntry(value = 45f, label = "Mon"),
            ChartEntry(value = 80f, label = "Tue"),
            ChartEntry(value = 65f, label = "Wed"),
            ChartEntry(value = 90f, label = "Thu"),
            ChartEntry(value = 55f, label = "Fri"),
        ),
        title = "Weekly Sales".asText(),
        showValues = true,
    )
)

// Multi-series grouped bar chart
BarChart(
    model = BarChartModel(
        series = listOf(
            ChartSeries(
                entries = listOf(ChartEntry(120f, "Q1"), ChartEntry(180f, "Q2"), ChartEntry(150f, "Q3")),
                label = "Revenue".asText(),
            ),
            ChartSeries(
                entries = listOf(ChartEntry(80f, "Q1"), ChartEntry(110f, "Q2"), ChartEntry(95f, "Q3")),
                label = "Costs".asText(),
            ),
        ),
        title = "Quarterly Report".asText(),
    )
)

// Line chart with area fill
LineChart(
    model = LineChartModel(
        entries = listOf(
            ChartEntry(20f, "Jan"), ChartEntry(35f, "Feb"), ChartEntry(28f, "Mar"),
            ChartEntry(50f, "Apr"), ChartEntry(42f, "May"), ChartEntry(60f, "Jun"),
        ),
        title = "Growth Trend".asText(),
        showArea = true,
    )
)

// Simple pie chart
PieChart(
    model = PieChartModel(
        slices = listOf(
            PieSlice(value = 35f, label = "Mobile".asText()),
            PieSlice(value = 30f, label = "Desktop".asText()),
            PieSlice(value = 20f, label = "Tablet".asText()),
            PieSlice(value = 15f, label = "Other".asText()),
        ),
        title = "Traffic Sources".asText(),
    )
)

// Donut chart
PieChart(
    model = PieChartModel(
        slices = listOf(
            PieSlice(value = 72f, label = "Complete".asText(), color = Color(0xFF34D399)),
            PieSlice(value = 28f, label = "Remaining".asText(), color = Color(0xFFE2E8F0)),
        ),
        title = "Progress".asText(),
        donutFraction = 0.6f,
    )
)

// Multi-series line chart
LineChart(
    model = LineChartModel(
        series = listOf(
            ChartSeries(
                entries = listOf(ChartEntry(10f, "W1"), ChartEntry(30f, "W2"), ChartEntry(25f, "W3"), ChartEntry(45f, "W4")),
                label = "Users".asText(),
            ),
            ChartSeries(
                entries = listOf(ChartEntry(5f, "W1"), ChartEntry(15f, "W2"), ChartEntry(20f, "W3"), ChartEntry(35f, "W4")),
                label = "Sessions".asText(),
            ),
        ),
        title = "Weekly Metrics".asText(),
        showArea = true,
        smoothCurve = true,
    )
)
```

---

Note: `Clause`, `Image`, `Currency`, `OptionalClickCallback` come from `ui:element`.
