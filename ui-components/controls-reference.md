# Controls Reference

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
