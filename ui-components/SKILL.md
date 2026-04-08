---
name: ui-components
description: Use when implementing buttons, text fields, password fields, phone inputs, currency inputs, date pickers, cards, dividers, scaffolds, trays, or bottom sheets in a KMP Compose project.
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

```kotlin
@Composable fun Tray(
    onDismissRequest: OptionalClickCallback, isSwipeDismissible: Boolean = true,
    skipPartiallyExpanded: Boolean = false,
    stickyBottom: (@Composable BoxScope.() -> Unit)? = null,
    content: @Composable BoxScope.() -> Unit,
)

@Composable fun ScrollableTray(
    onDismissRequest: OptionalClickCallback, invertedColors: Boolean = isSystemInDarkTheme(),
    content: @Composable BoxScope.() -> Unit,
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

// Scaffold with tray
Scaffold(topBar = { /* toolbar */ }) { padding ->
    Column(Modifier.padding(padding)) { /* content */ }
}
```

Note: `Clause`, `Image`, `Currency`, `OptionalClickCallback` come from `ui:element`.
