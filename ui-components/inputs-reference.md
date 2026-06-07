# Buttons & Inputs Reference

## Buttons

```kotlin
@Composable fun PrimaryButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: (() -> Unit)?, invertedColors: Boolean = Theme.invertedColors)
@Composable fun SmallButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback, invertedColors: Boolean = Theme.invertedColors)
@Composable fun OutlineButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, style: ButtonStyle = ButtonStyle.Regular, onClick: OptionalClickCallback, invertedColors: Boolean = Theme.invertedColors)
@Composable fun SmallOutlineButton(model: ButtonModel, modifier: Modifier = Modifier, state: ButtonState = ButtonState.Enabled, onClick: OptionalClickCallback, invertedColors: Boolean = Theme.invertedColors)

// Lower-level button used by PrimaryButton/SmallButton. Reads its colors from the
// surrounding ProvideBaseButtonColors composition; no invertedColors parameter.
@Composable fun BaseButton(model: ButtonModel, modifier: Modifier = Modifier, style: ButtonStyle, state: ButtonState, onClick: OptionalClickCallback)

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
    invertedColors: Boolean = Theme.invertedColors
)

@Composable fun PasswordTextField(
    model: TextInputModel,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    modifier: Modifier = Modifier,
    onValueChange: (String) -> Unit,
    onPasswordToggleChange: ((Boolean) -> Unit)? = null,
    invertedColors: Boolean = Theme.invertedColors
)

@Composable fun PhoneTextField(
    model: PhoneInputModel, modifier: Modifier = Modifier,
    onPhoneNumberChanged: (String) -> Unit,
    onCountryCodePickClick: OptionalClickCallback,
    invertedColors: Boolean = Theme.invertedColors
)

@Composable fun CurrencyTextField(
    model: CurrencyInputModel, readOnly: Boolean = false, modifier: Modifier = Modifier,
    onClick: OptionalClickCallback = null,
    onAmountChanged: (Long?) -> Unit,
    dropDownContent: @Composable ((Dp) -> Unit)? = null,
    invertedColors: Boolean = Theme.invertedColors
)

@Composable fun SelectionTextField(
    model: TextInputModel, modifier: Modifier = Modifier,
    trailingIcon: Image = Image.Drawable(Res.drawable.sc_icon_chevron_down),
    onClick: OptionalClickCallback,
    invertedColors: Boolean = Theme.invertedColors
)

@Composable fun DropdownSelectionField(
    model: SelectionFieldModel,
    modifier: Modifier = Modifier,
    onOptionSelected: (SelectionOption) -> Unit,
    invertedColors: Boolean = Theme.invertedColors,
)

@Composable fun TextArea(
    model: TextInputModel, minLines: Int = 4, maxLines: Int = 4,
    modifier: Modifier = Modifier,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions(),
    onValueChange: (value: String) -> Unit,
    invertedColors: Boolean = Theme.invertedColors
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
data class CurrencyAmount(val amount: Long, val currency: Currency = Currency.USD) {
    fun toValue(): String
}

@Stable
data class SelectionFieldModel(
    val label: Clause? = null,
    val placeholder: Clause = Text.Simple("Select"),
    val options: List<SelectionOption> = emptyList(),
    val selectedKey: String? = null,
    val isError: Boolean = false,
    val footerText: Clause? = null,
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
