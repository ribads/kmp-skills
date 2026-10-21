# Buttons & Inputs Reference

## Buttons

```kotlin
@Composable fun PrimaryButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: (() -> Unit)?)
@Composable fun SmallButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback)
@Composable fun OutlineButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, style: ButtonStyle = ButtonStyle.Regular, onClick: OptionalClickCallback)
@Composable fun SmallOutlineButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback)

// The filled button PrimaryButton and SmallButton are built on, for an app's own button in its own colours.
@Composable fun BaseButton(
    model: ButtonModel, modifier: Modifier = Modifier,
    style: ButtonStyle, state: ButtonState, colors: BaseButtonColors,
    onClick: OptionalClickCallback,
)

@Immutable
data class ButtonModel(val title: Clause, val leadingImage: Image? = null, val trailingImage: Image? = null)
enum class ButtonState { Enabled, Disabled, Loading }
enum class ButtonStyle { Regular, Small }

@Immutable
data class BaseButtonColors(                          // package button.model
    val backgroundColor: Color = Color.Unspecified,           // container, enabled
    val disabledBackgroundColor: Color = Color.Unspecified,   // container, disabled or loading
    val textColor: Color = Color.Unspecified,                 // title, enabled
    val disabledTextColor: Color = Color.Unspecified,         // title, disabled
    val contentColor: Color = Color.Unspecified,              // Glyph images, enabled
    val disabledContentColor: Color = Color.Unspecified,      // Glyph images, disabled; the loading spinner
)

fun Clause.asButton() = ButtonModel(leadingImage = null, trailingImage = null, title = this)
```

An app-level button (a brand or secondary style) is a `BaseButton` with colours built from roles, in the app's `compose-ui/`:

```kotlin
@Composable
fun SecondaryButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback) {
    BaseButton(
        model = model,
        modifier = modifier,
        style = ButtonStyle.Regular,
        state = state,
        colors = BaseButtonColors(
            backgroundColor = Theme.colors.surface.secondary,
            disabledBackgroundColor = Theme.colors.surface.subtle,
            textColor = Theme.colors.element.primary,
            disabledTextColor = Theme.colors.elementInteractive.disabled,
            contentColor = Theme.colors.element.primary,
            disabledContentColor = Theme.colors.elementInteractive.disabled,
        ),
        onClick = onClick,
    )
}
```

Migrating from 0.2.0-alpha8: `BaseButtonColors` moved from `button.internal` to `button.model` and lost its two outline fields (`borderOutlineColor`, `disabledBorderOutlineColor`), which only Synapse's own outline buttons read. `BaseButton` takes it as `colors` instead of reading `ProvideBaseButtonColors`, which is now internal. Replace `ProvideBaseButtonColors(colors = c) { BaseButton(...) }` with `BaseButton(..., colors = c)`.

---

## Text Fields

Every field takes `model`, `modifier`, `style` and `state` first, then its own config, then callbacks and slots.

```kotlin
@Composable fun TextField(
    model: TextInputModel,
    modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current,
    state: FieldState = FieldState.Enabled,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default,
    visualTransformation: VisualTransformation = VisualTransformation.None,
    interactionSource: MutableInteractionSource? = null,    // the field creates its own when null
    onValueChange: (String) -> Unit,
    leadingContent: @Composable (RowScope.() -> Unit)? = null,
    trailingContent: @Composable (RowScope.() -> Unit)? = null,
)

@Composable fun PasswordTextField(
    model: TextInputModel, modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current, state: FieldState = FieldState.Enabled,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default,
    onValueChange: (String) -> Unit,
    onPasswordToggleChange: ((Boolean) -> Unit)? = null,
)

@Composable fun PhoneTextField(
    model: PhoneInputModel, modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current, state: FieldState = FieldState.Enabled,
    onPhoneNumberChanged: (String) -> Unit,
    onCountryCodePickClick: OptionalClickCallback,
)

@Composable fun CurrencyTextField(
    model: CurrencyInputModel, modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current, state: FieldState = FieldState.Enabled,
    onClick: OptionalClickCallback = null,
    onAmountChanged: (Long?) -> Unit,
    dropDownContent: @Composable ((Dp) -> Unit)? = null,
)

@Composable fun TextArea(
    model: TextInputModel, modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current, state: FieldState = FieldState.Enabled,
    minLines: Int = 4, maxLines: Int = 4,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default,
    onValueChange: (value: String) -> Unit,
)

@Composable fun SelectionTextField(
    model: TextInputModel, modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current, state: FieldState = FieldState.Enabled,
    trailingIcon: Image = Image.Glyph(Res.drawable.sc_icon_chevron_down),
    clickLabel: Clause? = null,           // what tapping does, for screen readers; null keeps the platform wording
    onClick: OptionalClickCallback,
)

@Composable fun DropdownSelectionField(
    model: SelectionFieldModel, modifier: Modifier = Modifier,
    style: TextFieldStyle = LocalTextFieldStyle.current, state: FieldState = FieldState.Enabled,
    onOptionSelected: (SelectionOption) -> Unit,
)
// The menu paints surface.raised; its items render inside WithRaisedSurface.
```

### Style and state

```kotlin
enum class TextFieldStyle { Filled, Outlined }           // package field.model
enum class FieldState { Enabled, ReadOnly, Disabled }    // package field.model

val LocalTextFieldStyle: ProvidableCompositionLocal<TextFieldStyle>    // Filled unless set
@Composable fun WithTextFieldStyle(style: TextFieldStyle, content: @Composable () -> Unit)
```

**Styles:**
- `Filled`, the default, tints its container with `element.primary` at a low alpha and draws no outline at rest. It reads on the canvas, on a `Card` and in a sheet.
- `Outlined` paints the canvas colour, `surface.primary`, with a `border.primary` outline.

**What both styles share:**
- Corners are `Theme.shape.textShape`.
- Focus draws a 2dp `border.emphasis` ring.
- An error draws an `intents.error.border` ring (2dp when focused), with the message in `intents.error.content`.
- The label is `labelS`, the value and placeholder `body`, the footer `bodyXs`.

**Restyling:** there is no colour, shape or size parameter. Restyle through the theme roles, `textShape`, or the other style.
- `WithTextFieldStyle(TextFieldStyle.Outlined) { App() }` at the root sets the style app-wide; wrap a region to set it there only.
- A field's own `style =` wins.
- Server-driven screens (`SynapseRenderer`) always draw `Filled`. A2UI surfaces follow the host app's style.

**`FieldState`** is a separate `ViewState` field, like `ButtonState`, so the reducer can lock a form while it submits.
- `ReadOnly` shows the value with no fill. The field can be focused, selected and copied, but not changed.
- `Disabled` is muted: a `surfaceInteractive.disabled` fill and `elementInteractive.disabled` content. It cannot be focused and shows no error.
- Precedence is Disabled, then error, then focus. A focused read-only field keeps its focus ring.

**Behaviour:**
- **One control.** The label, container and footer form one control. Tapping the label focuses a text field, or clicks a selection field, and a screen reader reads the field as one node.
- **Error message.** With `isError`, the footer is the error message, and screen readers announce it as the field's error. Pass the message in `footerText`.
- **Error glyph.** It appears once: in the trailing slot when that slot is free, otherwise at the start of the footer.
- **Slot colour.** `leadingContent` and `trailingContent` draw in the field's slot colour through `LocalContentColor`: `element.secondary` at rest, `element.primary` when focused, `elementInteractive.disabled` when disabled. An `Icon` with no `tint` follows it.
- **No built-in spacing.** Fields add no space around themselves. Space a form with its parent's `Arrangement.spacedBy`.

### Selection and currency fields

`SelectionTextField` and `DropdownSelectionField` are read-only and act as one control:
- Tapping anywhere on the field, label included, calls `onClick` or opens the menu, with a ripple clipped to the container.
- A screen reader announces the field as a button (`SelectionTextField`) or a dropdown list (`DropdownSelectionField`). It reads the value, or the placeholder when empty, plus the click label when one is set.
- The trailing icon is decorative.
- The field takes taps only when `state` is `Enabled` and there is something to call. A `ReadOnly` selection field is not a control: it reads as its label and value.
- `DropdownSelectionField` renders the selected option's `label` in the field as a `Clause`, so any clause works there as in the menu: localized text, money, timestamps, inline graphics, formatting.

`CurrencyTextField` treats the digits typed as minor units and shows them formatted behind the currency's symbol (`$24.99` for `2499`), using the device locale's separators.
- An empty field shows `placeholder` and reports `null` to `onAmountChanged`. Zero is an amount and shows as `$0.00`.
- A keystroke that would overflow a `Long` is ignored.
- `onClick` fires from the trailing currency section (code and chevron), and only when the field is enabled.

`PhoneTextField` leads with the country's flag, dialling code and a chevron. `onCountryCodePickClick` fires from that section, only when the field is enabled.

### Migrating from 0.2.0-alpha10

- **Rename and order.** `LabelTextField` is now `TextField`. Every field's parameters follow `model, modifier, style, state`, then config, callbacks and slots. Pass arguments by name.
- **State.** `readOnly = true` becomes `state = FieldState.ReadOnly`, on `TextField` and `CurrencyTextField`. `FieldState.Disabled` is new.
- **Removed parameters.** `TextField` is single-line, so `singleLine`, `minLines` and `maxLines` are gone; use `TextArea` for multi-line input. `borderWidth` is gone too, and `interactionSource` is nullable.
- **Models.**
  - `PhoneInputModel.label` and `CurrencyInputModel.label` are `Clause? = null`, and `null` draws no label.
  - The `Default` models have no label.
  - `CurrencyInputModel.toTextInputModel()` is internal.
- **The look.**
  - The default is now `Filled`. To keep outlined fields, wrap the app in `WithTextFieldStyle(TextFieldStyle.Outlined)`.
  - Corners now follow `Theme.shape.textShape`, so check that token's value.
  - Fields no longer add space below themselves.
- **Server-driven themes** that leave `shape.text` unset now get 12 instead of 8.

---

## Text Field Models

```kotlin
@Stable
data class TextInputModel(
    val label: Clause?,                   // null draws no label
    val value: String, val placeholder: Clause,
    val isError: Boolean = false, val footerText: Clause? = null,
) {
    companion object { val Default: TextInputModel }    // no label, empty value and placeholder
}

@Immutable
data class PhoneInputModel(
    val label: Clause? = null, val value: String, val placeholder: Clause,
    val countryCode: String, val countryFlag: Clause? = null,
    val isError: Boolean = false, val footerText: Clause? = null,
) {
    companion object { val Default: PhoneInputModel }
}

@Immutable
data class CurrencyInputModel(
    val label: Clause? = null, val amount: CurrencyAmount, val placeholder: Clause,
    val isError: Boolean = false, val footerText: Clause? = null,
)

@Immutable
data class CurrencyAmount(
    val amount: Long? = null,             // minor units; null is an empty field, which shows the placeholder
    val currency: Currency = Currency.USD,
) {
    fun toValue(): String                 // the digits, or "" when amount is null
}

@Stable
data class SelectionFieldModel(
    val label: Clause? = null,
    val placeholder: Clause = Text.Simple("Select"),
    val options: List<SelectionOption> = emptyList(),
    val selectedKey: String? = null,
    val isError: Boolean = false,
    val footerText: Clause? = null,
    val clickLabel: Clause? = null,       // what tapping does, for screen readers; null keeps the platform wording
) {
    companion object { val Default: SelectionFieldModel }
}

@Stable
data class SelectionOption(
    val key: String,
    val label: Clause,
)

object CountryLocale {
    fun getCountryDialingCode(countryCode: String): String?
    fun getCountryCodes(): List<String>
    fun getCountryDialCodes(): Map<String, String>
}
```
