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
)

@Composable fun PasswordTextField(
    model: TextInputModel,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    modifier: Modifier = Modifier,
    onValueChange: (String) -> Unit,
    onPasswordToggleChange: ((Boolean) -> Unit)? = null,
)

@Composable fun PhoneTextField(
    model: PhoneInputModel, modifier: Modifier = Modifier,
    onPhoneNumberChanged: (String) -> Unit,
    onCountryCodePickClick: OptionalClickCallback,
)

@Composable fun CurrencyTextField(
    model: CurrencyInputModel, readOnly: Boolean = false, modifier: Modifier = Modifier,
    onClick: OptionalClickCallback = null,
    onAmountChanged: (Long?) -> Unit,
    dropDownContent: @Composable ((Dp) -> Unit)? = null,
)

@Composable fun SelectionTextField(
    model: TextInputModel, modifier: Modifier = Modifier,
    trailingIcon: Image = Image.Glyph(Res.drawable.sc_icon_chevron_down),
    clickLabel: Clause? = null,           // what tapping does, for screen readers; null keeps the platform wording
    onClick: OptionalClickCallback,
)

@Composable fun DropdownSelectionField(
    model: SelectionFieldModel,
    modifier: Modifier = Modifier,
    onOptionSelected: (SelectionOption) -> Unit,
)
// The menu paints surface.raised; its items render inside WithRaisedSurface.
```

`SelectionTextField` and `DropdownSelectionField` are read-only and act as one control: tapping anywhere on the field calls `onClick` (or opens the menu), with a ripple clipped to the field's shape. A screen reader announces the field as a button (`SelectionTextField`) or a dropdown list (`DropdownSelectionField`) with its value, or its placeholder when empty, and the click label when one is set. The trailing icon is decorative. `SelectionTextField` is disabled when `onClick` is null. `DropdownSelectionField` renders the selected option's `label` in the field as a `Clause`, so any clause works there as in the menu: localized text, money, timestamps, inline graphics, formatting.

`CurrencyTextField` treats the digits typed as minor units and shows them formatted behind the currency's symbol (`$24.99` for `2499`), using the device locale's separators. An empty field shows `placeholder` and reports `null` to `onAmountChanged`; zero is an amount and shows as `$0.00`. A keystroke that would overflow a `Long` is ignored. `onClick` fires from the trailing currency chevron only.

```kotlin
@Composable fun TextArea(
    model: TextInputModel, minLines: Int = 4, maxLines: Int = 4,
    modifier: Modifier = Modifier,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    onValueChange: (value: String) -> Unit,
)
```

---

## Text Field Models

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
