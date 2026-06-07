---
name: ui-components
description: Use when implementing buttons, text fields, password fields, phone inputs, currency inputs, date pickers, cards, dividers, scaffolds, trays, bottom sheets, top nav bars, bottom navigation bars, liquid-glass navigation bars, checkboxes, progress bars, circular progress, rating inputs, chip groups, tab layouts, sliders, timers, steppers, time pickers, confirm dialogs, empty states, radio groups, bar charts, line charts, pie charts, chat text areas, message bubbles, or toasts/snackbars in a KMP Compose project.
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

## Component Catalog

| Component | Composable | Model | Reference |
|-----------|-----------|-------|-----------|
| Primary button | `PrimaryButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Small button | `SmallButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Outline button | `OutlineButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Small outline button | `SmallOutlineButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Label text field | `LabelTextField` | `TextInputModel` | [inputs](inputs-reference.md) |
| Password text field | `PasswordTextField` | `TextInputModel` | [inputs](inputs-reference.md) |
| Phone text field | `PhoneTextField` | `PhoneInputModel` | [inputs](inputs-reference.md) |
| Currency text field | `CurrencyTextField` | `CurrencyInputModel` | [inputs](inputs-reference.md) |
| Selection text field | `SelectionTextField` | `TextInputModel` | [inputs](inputs-reference.md) |
| Dropdown selection field | `DropdownSelectionField` | `SelectionFieldModel` | [inputs](inputs-reference.md) |
| Text area | `TextArea` | `TextInputModel` | [inputs](inputs-reference.md) |
| Date picker | `DatePicker` / `DatePickerBottomSheet` | `DatePickerModel` | [layout](layout-reference.md) |
| Card | `Card` | — | [layout](layout-reference.md) |
| Divider | `Divider` | — | [layout](layout-reference.md) |
| Scaffold | `Scaffold` | — | [layout](layout-reference.md) |
| Top nav bar | `TopNavBar` | `TopNavBarModel` | [layout](layout-reference.md) |
| Bottom navigation bar | `BottomNavigationBar` | `BottomNavigationBarModel` | [layout](layout-reference.md) |
| Liquid-glass bottom navigation bar | `LiquidGlassBottomNavigationBar` | `BottomNavigationBarModel` | [layout](layout-reference.md) |
| Tray | `Tray` | — | [layout](layout-reference.md) |
| Scrollable tray | `ScrollableTray` | — | [layout](layout-reference.md) |
| Checkbox | `LabelCheckbox` | `CheckboxModel` | [controls](controls-reference.md) |
| Progress bar | `ProgressBar` | `ProgressBarModel` | [controls](controls-reference.md) |
| Circular progress | `CircularProgress` | `CircularProgressModel` | [controls](controls-reference.md) |
| Rating input | `RatingInput` | `RatingInputModel` | [controls](controls-reference.md) |
| Chip group | `ChipGroup` | `ChipGroupModel` | [controls](controls-reference.md) |
| Tab layout | `TabLayout` | `TabLayoutModel` | [controls](controls-reference.md) |
| Liquid-glass tab layout | `LiquidGlassTabLayout` | `TabLayoutModel` | [controls](controls-reference.md) |
| Radio group | `RadioGroup` | `RadioGroupModel` | [controls](controls-reference.md) |
| Slider | `Slider` | `SliderModel` | [controls](controls-reference.md) |
| Stepper | `Stepper` | `StepperModel` | [controls](controls-reference.md) |
| Timer | `Timer` | `TimerModel` | [controls](controls-reference.md) |
| Time picker | `TimePicker` | `TimePickerModel` | [controls](controls-reference.md) |
| Confirm dialog | `ConfirmDialog` | `ConfirmDialogModel` | [controls](controls-reference.md) |
| Empty state | `EmptyState` | `EmptyStateModel` | [controls](controls-reference.md) |
| Waveform | `Waveform` | — | [controls](controls-reference.md) |
| Bar chart | `BarChart` | `BarChartModel` | [charts](charts-reference.md) |
| Line chart | `LineChart` | `LineChartModel` | [charts](charts-reference.md) |
| Pie chart | `PieChart` | `PieChartModel` | [charts](charts-reference.md) |
| Chat text area | `ChatTextArea` | `ChatTextAreaModel` | [chat](chat-reference.md) |
| Message bubble | `MessageBubble` | `MessageBubbleModel` | [chat](chat-reference.md) |
| Toast | `ToastHandler` + `Toast.current` | `ToastModel` | [toast](toast-reference.md) |

---

## Detailed Reference

- [Buttons & Inputs](inputs-reference.md) — Buttons, text fields, phone, currency, selection, text area + models
- [Layout & Containers](layout-reference.md) — DatePicker, Card, Divider, Scaffold, TopNavBar, Trays
- [Controls](controls-reference.md) — Checkbox, progress, rating, chips, tabs, radio, slider, stepper, timer, time picker, confirm dialog, empty state
- [Charts](charts-reference.md) — Bar, line, pie charts + models
- [Chat](chat-reference.md) — ChatTextArea, MessageBubble + models
- [Toast](toast-reference.md) — ToastHandler, ToastController, ToastModel, ToastStyle
- [Usage Examples](examples.md) — Code examples for all components

---

Note: `Clause`, `Image`, `Currency`, `OptionalClickCallback` come from `ui:element`.
