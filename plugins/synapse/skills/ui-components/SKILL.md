---
name: ui-components
description: Use when implementing buttons, text fields, password fields, phone inputs, currency inputs, date pickers, cards, dividers, scaffolds, trays, bottom sheets, top nav bars, bottom navigation bars, liquid-glass navigation bars, checkboxes, progress bars, circular progress, rating inputs, chip groups, tab layouts, sliders, timers, steppers, time pickers, confirm dialogs, empty states, radio groups, bar charts, line charts, pie charts, chat text areas, message bubbles, or toasts/snackbars in a KMP Compose project.
user-invocable: true
---

# ui:component — Reusable UI Components

**Module**: `ui:component` | **Artifact**: `com.ribads.synapse:ui-component`
**Packages**: `com.ribads.synapse.ui.component.<family>` and `.<family>.model`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-component:<version>")
}
```

Depends on `ui:element` and `ui:compose-presentation`, both exposed as API: `ThemedBottomSheetAppearance` is a `BottomSheetAppearance` from `/synapse:navigation`.

## Imports

Each family's composables live in `com.ribads.synapse.ui.component.<family>` and its models in `com.ribads.synapse.ui.component.<family>.model`. Nothing is importable from `com.ribads.synapse.ui.component` itself.

Import each type from its package below.

| Package | Types |
|---|---|
| `com.ribads.synapse.ui.component.bottomnavbar` | `BottomNavigationBar`, `LiquidGlassBottomNavigationBar` |
| `com.ribads.synapse.ui.component.bottomnavbar.model` | `BottomNavigationBadge`, `BottomNavigationBarModel`, `BottomNavigationItem` |
| `com.ribads.synapse.ui.component.button` | `BaseButton`, `OutlineButton`, `PrimaryButton`, `SmallButton`, `SmallOutlineButton` |
| `com.ribads.synapse.ui.component.button.model` | `BaseButtonColors`, `ButtonModel`, `ButtonState`, `ButtonStyle`, `asButton` |
| `com.ribads.synapse.ui.component.calendar` | `DatePicker`, `DatePickerBottomSheet` |
| `com.ribads.synapse.ui.component.calendar.model` | `DatePickerModel` |
| `com.ribads.synapse.ui.component.card` | `Card`, `SelectableCard` |
| `com.ribads.synapse.ui.component.chart` | `BarChart`, `LineChart`, `PieChart` |
| `com.ribads.synapse.ui.component.chart.model` | `BarChartModel`, `ChartEntry`, `ChartSeries`, `LineChartModel`, `PieChartModel`, `PieSlice` |
| `com.ribads.synapse.ui.component.chat` | `ChatTextArea`, `MessageBubble` |
| `com.ribads.synapse.ui.component.chat.model` | `ChatAttachment`, `ChatInputAction`, `ChatTextAreaModel`, `MessageAudio`, `MessageBubbleModel`, `MessageStatus`, `MessageVariant` |
| `com.ribads.synapse.ui.component.chip` | `ChipGroup` |
| `com.ribads.synapse.ui.component.chip.model` | `ChipGroupModel`, `ChipOption` |
| `com.ribads.synapse.ui.component.dialog` | `ConfirmDialog` |
| `com.ribads.synapse.ui.component.dialog.model` | `ConfirmDialogModel` |
| `com.ribads.synapse.ui.component.divider` | `Divider` |
| `com.ribads.synapse.ui.component.emptystate` | `EmptyState` |
| `com.ribads.synapse.ui.component.emptystate.model` | `EmptyStateModel` |
| `com.ribads.synapse.ui.component.field` | `CurrencyTextField`, `DropdownSelectionField`, `LocalTextFieldStyle`, `PasswordTextField`, `PhoneTextField`, `SelectionTextField`, `TextArea`, `TextField`, `WithTextFieldStyle` |
| `com.ribads.synapse.ui.component.field.model` | `CountryLocale`, `CurrencyAmount`, `CurrencyInputModel`, `FieldState`, `PhoneInputModel`, `SelectionFieldModel`, `SelectionOption`, `TextFieldStyle`, `TextInputModel` |
| `com.ribads.synapse.ui.component.progress` | `CircularProgress`, `ProgressBar` |
| `com.ribads.synapse.ui.component.progress.model` | `CircularProgressModel`, `ProgressBarModel` |
| `com.ribads.synapse.ui.component.radio` | `RadioGroup` |
| `com.ribads.synapse.ui.component.radio.model` | `RadioGroupModel`, `RadioOption` |
| `com.ribads.synapse.ui.component.rating` | `RatingInput` |
| `com.ribads.synapse.ui.component.rating.model` | `RatingInputModel` |
| `com.ribads.synapse.ui.component.scaffold` | `Scaffold` |
| `com.ribads.synapse.ui.component.section` | `Section`, `section` |
| `com.ribads.synapse.ui.component.section.model` | `SectionModel` |
| `com.ribads.synapse.ui.component.slider` | `Slider` |
| `com.ribads.synapse.ui.component.slider.model` | `SliderModel` |
| `com.ribads.synapse.ui.component.stepper` | `Stepper` |
| `com.ribads.synapse.ui.component.stepper.model` | `StepperModel` |
| `com.ribads.synapse.ui.component.tab` | `LiquidGlassTabLayout`, `TabLayout` |
| `com.ribads.synapse.ui.component.tab.model` | `TabItem`, `TabLayoutModel` |
| `com.ribads.synapse.ui.component.timepicker` | `TimePicker` |
| `com.ribads.synapse.ui.component.timepicker.model` | `TimePickerModel` |
| `com.ribads.synapse.ui.component.timer` | `Timer` |
| `com.ribads.synapse.ui.component.timer.model` | `TimerModel` |
| `com.ribads.synapse.ui.component.toast` | `LocalToastController`, `Toast`, `ToastController`, `ToastHandler` |
| `com.ribads.synapse.ui.component.toast.model` | `ToastDefaults`, `ToastDuration`, `ToastId`, `ToastIntent`, `ToastIntentStyle`, `ToastModel`, `ToastPosition`, `ToastSnapshot`, `ToastStyle` |
| `com.ribads.synapse.ui.component.toggle` | `LabelCheckbox` |
| `com.ribads.synapse.ui.component.toggle.model` | `CheckboxModel` |
| `com.ribads.synapse.ui.component.topnavbar` | `TopNavBar` |
| `com.ribads.synapse.ui.component.topnavbar.model` | `NavBarIconType`, `TopNavBarModel`, `TopNavBarTrailingContentModel`, `TrailingIconModel` |
| `com.ribads.synapse.ui.component.tray` | `ScrollableTray`, `ScrollableTraySurface`, `ThemedBottomSheetAppearance`, `Tray`, `TraySurface` |
| `com.ribads.synapse.ui.component.waveform` | `Waveform` |

---

## Component Catalog

| Component | Composable | Model | Reference |
|-----------|-----------|-------|-----------|
| Primary button | `PrimaryButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Small button | `SmallButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Outline button | `OutlineButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Small outline button | `SmallOutlineButton` | `ButtonModel` | [inputs](inputs-reference.md) |
| Text field | `TextField` | `TextInputModel` | [inputs](inputs-reference.md) |
| Password text field | `PasswordTextField` | `TextInputModel` | [inputs](inputs-reference.md) |
| Phone text field | `PhoneTextField` | `PhoneInputModel` | [inputs](inputs-reference.md) |
| Currency text field | `CurrencyTextField` | `CurrencyInputModel` | [inputs](inputs-reference.md) |
| Selection text field | `SelectionTextField` | `TextInputModel` | [inputs](inputs-reference.md) |
| Dropdown selection field | `DropdownSelectionField` | `SelectionFieldModel` | [inputs](inputs-reference.md) |
| Text area | `TextArea` | `TextInputModel` | [inputs](inputs-reference.md) |
| Date picker | `DatePicker` / `DatePickerBottomSheet` | `DatePickerModel` | [layout](layout-reference.md) |
| Card | `Card` | — | [layout](layout-reference.md) |
| Selectable card (one option of a choice) | `SelectableCard` | none | [layout](layout-reference.md) |
| Divider | `Divider` | — | [layout](layout-reference.md) |
| Scaffold | `Scaffold` | — | [layout](layout-reference.md) |
| Top nav bar | `TopNavBar` | `TopNavBarModel` | [layout](layout-reference.md) |
| Bottom navigation bar | `BottomNavigationBar` | `BottomNavigationBarModel` | [layout](layout-reference.md) |
| Liquid-glass bottom navigation bar | `LiquidGlassBottomNavigationBar` | `BottomNavigationBarModel` | [layout](layout-reference.md) |
| Tray | `Tray` | — | [layout](layout-reference.md) |
| Scrollable tray | `ScrollableTray` | — | [layout](layout-reference.md) |
| Tray as a `bottomSheet()` screen | `TraySurface` / `ScrollableTraySurface` | — | [layout](layout-reference.md) |
| Sheet look for `NavContainer` | `ThemedBottomSheetAppearance` | `BottomSheetAppearance` | [layout](layout-reference.md) |
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

Every component in this catalog follows the same shape. Knowing it means you can call an unfamiliar component correctly without opening its reference file, and it is the contract your own composables must follow (see `/synapse:component-authoring`).

**Signature order:** `model`, then `modifier: Modifier = Modifier`, then config with defaults, then callbacks, then a trailing `content`.

```kotlin
PrimaryButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled,
              onClick: (() -> Unit)?)
```

Required callbacks deliberately sit *after* defaulted config parameters, so callbacks are passed as named arguments. Containers (`Scaffold`, `Card`, `TraySurface`, `ToastHandler`) have no `model`, lead with `modifier`, and end with a trailing `content` slot. A few components predate the rule: `Divider` leads with `color`, and `Tray` and `ScrollableTray` lead with `onDismissRequest` and take no `modifier` at all (the sheet fills the window's width; size what you put inside it).

**Everything else that holds across the catalog:**

- **One `model` parameter, not a parameter list.** Models are `@Immutable` or `@Stable` data classes in `component.<family>.model`. Only atomic controls take primitives.
- **All text is a `Clause`.** No component accepts a `String` for user-visible copy, and no model stores one. Images are `Image`, never a URL string. The one exception is `ChartEntry.label`, a `String` because charts draw it on a canvas; resolve localized axis labels in the Mapper.
- **Built-in copy is a model field with an English default.** The words a component draws itself are overridable through its model: `DatePickerModel` month, weekday, reset and done labels; `TimerModel` start, stop and reset; `TimePickerModel` AM and PM; `SelectionFieldModel.placeholder`. Pass `Text.Localized(...)` for a localized app; leave them for English.
- **Icon-only controls carry screen-reader labels.** The built-in nav-bar icons (`TopNavBarModel.BackIcon`, `CloseIcon`, `MenuIcon`) carry English content descriptions, overridable with `TopNavBarModel.leadingIconLabel` and `TrailingIconModel.label`; the chat send button announces `ChatTextAreaModel.sendLabel`; caller-supplied icons are announced by their `Image.contentDescription`. Not yet labelled: the password visibility toggle, the time picker's arrows, and the chat attachment-remove and audio play buttons.
- **Build models outside composables**, in `ViewState.Default`, the Mapper, or the Reducer. Never inline in a `@Composable`.
- **Components are stateless for anything that matters to the screen.** They render what you pass and report events upward; there are no stateful/stateless pairs and no public `rememberXState()` factories. Hoist state into `ViewState`. A few keep local UI state that the screen never needs, and it resets when they leave the composition: `PasswordTextField` (whether the password is visible; it still reports toggles through `onPasswordToggleChange`), `DropdownSelectionField` (whether the menu is open), `DatePicker` (the month on screen and whether the month or year grid is showing; a new model resets them), and `Slider` (the thumb position while dragging, reset by a new `value`).
- **Components never accept domain models or use-case DTOs.** Translate in the Mapper first.
- **`ButtonState` and `FieldState` are separate `ViewState` fields**, not fields on `ButtonModel` or the field models. Pass them as the `state =` argument so loading, read-only and disabled states are driven by the reducer.
- **Components read theme roles and never branch on the appearance.** They are correct in light and dark with no arguments; a region that must stay dark (a camera, controls over a photo) is wrapped in `WithAppearance(Appearance.Dark)` by the caller (see `/synapse:ui-element`).
- **Validation feedback goes in the model.** `TextInputModel.isError = true` draws the error ring and recolours the footer automatically; put the message in `footerText`, not in a separate `Text` below the field, so screen readers announce it as the field's error.
- **Callbacks are named for the slot, not the consequence**: `onClick` when there is one action, otherwise `onLeadingClick` / `onTrailingIconClick` / `onValueChange` / `onCheckedChange`, and `onDismissRequest` for every dismissal. Nullable click handlers use `OptionalClickCallback` from `ui:element`.

**Not in this catalog:** there is no loading-box, error-box, or pagination helper. Build loading states from `Modifier.shimmer()` over `Placeholder` model variants, empty states from `EmptyState`, and drive pagination from `nextPageToken` on your `ViewState`.

---

## Detailed Reference

- [Buttons & Inputs](inputs-reference.md) — Buttons, text fields, phone, currency, selection, text area + models
- [Layout & Containers](layout-reference.md): DatePicker, Card, SelectableCard, Divider, Scaffold, TopNavBar, Trays
- [Controls](controls-reference.md) — Checkbox, progress, rating, chips, tabs, radio, slider, stepper, timer, time picker, confirm dialog, empty state
- [Charts](charts-reference.md) — Bar, line, pie charts + models
- [Chat](chat-reference.md) — ChatTextArea, MessageBubble + models
- [Toast](toast-reference.md) — ToastHandler, ToastController, ToastModel, ToastStyle
- [Usage Examples](examples.md) — Code examples for all components

---

Note: `Clause`, `Image`, `Currency`, `OptionalClickCallback` come from `ui:element`.
