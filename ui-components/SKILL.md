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

## The component contract

Every component in this catalog follows the same shape. Knowing it means you can call an unfamiliar component correctly without opening its reference file, and it is the contract your own composables must follow (see `/component-authoring`).

**Signature order:** `model` → `modifier: Modifier = Modifier` → config with defaults → callbacks → `invertedColors: Boolean = Theme.invertedColors` → trailing `content`.

```kotlin
PrimaryButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled,
              onClick: (() -> Unit)?, invertedColors: Boolean = Theme.invertedColors)
```

Required callbacks deliberately sit *after* defaulted config parameters, so `invertedColors` stays last and callbacks are passed as named arguments. Containers (`Scaffold`, `Card`, `Tray`, `ToastHandler`) have no `model`, lead with `modifier`, and end with a trailing `content` slot. A few components predate the rule: `Divider` leads with `color`, and the text-field family buries `modifier` mid-list.

**Everything else that holds across the catalog:**

- **One `model` parameter, not a parameter list.** Models are `@Immutable` or `@Stable` data classes in `component.<family>.model`. Only atomic controls take primitives.
- **All text is a `Clause`.** No component accepts a `String` for user-visible copy, and no model stores one. Images are `Image`, never a URL string.
- **Build models outside composables**, in `ViewState.Default`, the Mapper, or the Reducer. Never inline in a `@Composable`.
- **Components are stateless.** They render what you pass and report events upward; there are no stateful/stateless pairs and no public `rememberXState()` factories. Hoist state into `ViewState`.
- **Components never accept domain models or use-case DTOs.** Translate in the Mapper first.
- **`ButtonState` is a separate `ViewState` field**, not a field on `ButtonModel`. Pass it as the `state =` argument so loading and disabled states are driven by the reducer.
- **Validation feedback goes in the model.** `TextInputModel.isError = true` recolours the indicator and footer automatically; put the message in `footerText`, not in a separate `Text` below the field.
- **Callbacks are named for the slot, not the consequence**: `onClick` when there is one action, otherwise `onLeadingClick` / `onTrailingIconClick` / `onValueChange` / `onCheckedChange`, and `onDismissRequest` for every dismissal. Nullable click handlers use `OptionalClickCallback` from `ui:element`.

**Not in this catalog:** there is no loading-box, error-box, or pagination helper. Build loading states from `Modifier.shimmer()` over `Placeholder` model variants, empty states from `EmptyState`, and drive pagination from `nextPageToken` on your `ViewState`.

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
