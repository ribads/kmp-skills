---
name: ui-components
description: Use when implementing buttons, text fields, password fields, phone inputs, currency inputs, date pickers, cards, dividers, scaffolds, trays, bottom sheets, bar charts, line charts, or pie charts in a KMP Compose project.
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
