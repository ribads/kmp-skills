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

### Waveform

Bar-style audio waveform visualizer. Pure visualizer — no audio engine coupling. Two modes share the same API:

- **Live, right-edge** (recording, real-time visualization). Append samples to a bounded buffer and leave `progress` at its default of `1f`. Buffers smaller than the bar count are right-aligned so the newest sample sits at the right edge.
- **Playback with playhead** (audio messages, podcasts). Pass the full waveform plus a `progress` fraction. Bars at-or-before the playhead use `progressColor`; the rest use `barColor`.

```kotlin
@Composable fun Waveform(
    samples: List<Float>,                                  // amplitudes 0.0..1.0, oldest -> newest
    modifier: Modifier = Modifier,
    progress: Float = 1f,                                  // 0.0..1.0; default = entire waveform tinted as "played"
    invertedColors: Boolean = Theme.invertedColors,
    barColor: Color? = null,                               // unplayed bars; defaults to Theme.colors.border.secondary
    progressColor: Color? = null,                          // played bars; defaults to Theme.colors.intents.accent.content
    barWidth: Dp = 2.5.dp,
    barGap: Dp = 1.5.dp,
)
```

Live wiring example (decoupled from `core:playback`):

```kotlin
val player = remember { buildAudioPlayer() }
val samples = remember { mutableStateListOf<Float>() }

LaunchedEffect(player) {
    player.amplitudes.collect { info ->
        samples.add(info.rms)
        if (samples.size > 120) samples.removeAt(0)         // bound the buffer
    }
}

Waveform(samples = samples, modifier = Modifier.fillMaxWidth().height(28.dp))
```

Playback example with playhead:

```kotlin
val position by player.position.collectAsState()
val progress = if (position.durationMs > 0) {
    position.currentMs.toFloat() / position.durationMs
} else 0f

Waveform(samples = waveform, progress = progress)
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

Underline-style tab bar: row of labels with a sliding 2dp indicator beneath the selected tab, animated via a spring. Selected label renders in `Theme.typography.bodyM` at `FontWeight.SemiBold`; unselected at `FontWeight.Normal`. Uses `Modifier.selectable(role = Role.Tab)` inside a `selectableGroup()` for a11y. Renders nothing when `tabs` is empty; `selectedIndex` is coerced into `0..tabs.lastIndex`.

```kotlin
@Composable fun TabLayout(
    model: TabLayoutModel,
    modifier: Modifier = Modifier,
    onTabSelected: (Int) -> Unit,
    invertedColors: Boolean = Theme.invertedColors,
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

Colors (via `Theme.colors`):
- Active indicator: `surfaceInteractive.enabledOnLight` / `enabledOnDark`
- Track (inactive indicator baseline): `border.secondaryOnLight` / `secondaryOnDark`
- Active label: `element.primaryOnLight` / `primaryOnDark`
- Inactive label: `element.secondaryOnLight` / `secondaryOnDark`

---

## Liquid Glass Tab Layout

Pill-shaped tab bar with a floating capsule that springs between tabs. Solid (non-transparent) fills: a subtle track surface, a raised primary-surface pill behind the selected tab, a 1dp hairline border on the pill for the glass edge, and a 6dp shadow elevation. Fixed 48dp bar height. Same `TabLayoutModel` as `TabLayout`; drop-in replacement with identical call shape.

```kotlin
@Composable fun LiquidGlassTabLayout(
    model: TabLayoutModel,
    modifier: Modifier = Modifier,
    onTabSelected: (Int) -> Unit,
    invertedColors: Boolean = Theme.invertedColors,
    content: @Composable (selectedIndex: Int) -> Unit,
)
```

Colors (via `Theme.colors`):
- Track: `surface.subtleLight` / `subtleDark`
- Pill fill: `surface.primaryLight` / `primaryDark`
- Pill hairline: `border.secondaryOnLight` / `secondaryOnDark`
- Selected label: `element.primaryOnLight` / `primaryOnDark` @ `FontWeight.SemiBold`
- Unselected label: `element.secondaryOnLight` / `secondaryOnDark` @ `FontWeight.Normal`

Pick `TabLayout` for a standard underline indicator inline in content; pick `LiquidGlassTabLayout` for a free-standing segmented selector (e.g., a toolbar control, top-of-sheet filter, or view-mode switch).

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
