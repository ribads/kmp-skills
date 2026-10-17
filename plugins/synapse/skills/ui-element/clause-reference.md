# Rich Text — Clause System

## Core Types

```kotlin
sealed class Clause

sealed class Text(
    open val format: TextFormat? = null,
    open val textActionId: String? = null,
) : Clause() {

    data class Simple(
        val text: String,
        override val format: TextFormat? = null,
        override val textActionId: String? = null,
    ) : Text()

    data class Localized(
        val resId: StringResource,
        val args: List<Clause> = emptyList(),
        override val textActionId: String? = null,
        override val format: TextFormat? = null,
    ) : Text()

    data class Money(                            // device locale for separators and symbol position; Currency for code, symbol, fraction digits
        val amount: Long,                        // Minor units (cents/pence)
        val currency: Currency = Currency.GBP,
        override val textActionId: String? = null,
        override val format: TextFormat? = null,
    ) : Text()

    data class Timestamp(
        val date: Long,                           // Unix timestamp millis
        val pattern: String? = null,              // Unicode pattern; null renders ISO 8601 (yyyy-MM-dd'T'HH:mm:ss.SSS'Z')
        override val textActionId: String? = null,
        val timeZone: TimeZone? = null,           // kotlinx.datetime.TimeZone; null renders in UTC, not the device's zone
        override val format: TextFormat? = null,
    ) : Text()

    companion object {
        val empty: Text.Simple = Text.Simple("")
        val whiteSpace: Text.Simple = Text.Simple(" ")
        val newLine: Text.Simple = Text.Simple("\n")
        fun listOf(vararg items: Clause): Clause
    }
}

data class Graphics(
    val image: Image,
    val intent: TextIntent? = null,
    val actionId: String? = null,
    val size: Int? = null,         // Size in sp (default 20sp)
    val contentDescription: String? = null,  // Screen-reader label; null = decorative
) : Clause()

data class CompositeClause(val items: List<Clause>) : Clause()
```

A `Graphics` clause with an `Image.Glyph` is tinted with its `intent`'s colour, or with the surrounding text colour when `intent` is null. Any other image type is drawn as authored.

---

## TextFormat

```kotlin
@Immutable
data class TextFormat(
    val bold: Boolean = false,
    val italic: Boolean = false,
    val underline: Boolean = false,
    val strikethrough: Boolean = false,
    val intent: TextIntent? = null,
    val backgroundIntent: TextIntent? = null,
) {
    operator fun plus(other: TextFormat): TextFormat

    companion object {
        val Bold: TextFormat
        val Italic: TextFormat
        val Underline: TextFormat
        val Strikethrough: TextFormat
        val BoldItalic: TextFormat
        val Caution: TextFormat          // intent = TextIntent.Caution
        val Emphasis: TextFormat         // intent = TextIntent.Emphasis
        val Success: TextFormat          // intent = TextIntent.Success
        val Error: TextFormat            // intent = TextIntent.Error
        val Mention: TextFormat          // bold + backgroundIntent = Emphasis
    }
}
```

---

## TextIntent & TextIntentPalette

```kotlin
enum class TextIntent { Caution, Emphasis, Success, Error }

@Composable fun TextIntent.toColor(): Color
@Composable fun TextIntent.toBackgroundColor(): Color

@Immutable
data class TextIntentPalette(
    val cautionContent: Color, val cautionSurface: Color,
    val emphasisContent: Color, val emphasisSurface: Color,
    val successContent: Color, val successSurface: Color,
    val errorContent: Color, val errorSurface: Color,
)

@Composable
fun textIntentPalette(
    cautionContent: Color? = null, cautionSurface: Color? = null,
    emphasisContent: Color? = null, emphasisSurface: Color? = null,
    successContent: Color? = null, successSurface: Color? = null,
    errorContent: Color? = null, errorSurface: Color? = null,
): TextIntentPalette

@Composable
fun WithTextIntentPalette(palette: TextIntentPalette, content: @Composable () -> Unit)

// Holds the optional palette provided by WithTextIntentPalette; null means resolve from Theme.
val LocalTextIntentPalette: ProvidableCompositionLocal<TextIntentPalette?>   // default null
```

Without a `WithTextIntentPalette`, each intent reads the theme's `Intents` for the current appearance: `Caution` uses `intents.warning`, `Emphasis` uses `intents.accent`, `Success` uses `intents.success`, and `Error` uses `intents.error`. `toColor()` returns the palette's `content` and `toBackgroundColor()` its `surface`. `textIntentPalette(...)` fills every argument left `null` from the same roles.

---

## Currency

```kotlin
enum class Currency(val symbol: String, val hasDecimals: Boolean = true, val decimalPlaces: Int = 2) {
    NGN("₦"), GBP("£"), USD("$"), EUR("€"),
    JPY("¥", hasDecimals = false, decimalPlaces = 0),
    CHF("CHF"), CAD("$"), AUD("$"), NZD("$"), CNY("¥"), HKD("$");

    val code: String get() = name
}
```

---

## MoneyParser

```kotlin
interface MoneyParser {
    fun parseMoney(input: String): Long                             // digits only, as minor units; "" is 0; throws NumberFormatException past Long.MAX_VALUE
    fun formatDisplay(amount: Long, currency: Currency): String     // minor units, with the symbol: "€1,234.56" in en-US, "1.234,56 €" in de-DE
    fun formatAmount(amount: Double, currency: Currency): String    // major units, no symbol: "1,234.56" in en-US, "1.234,56" in de-DE
}

fun getMoneyParser(): MoneyParser
```

Both format functions use the device's current locale on every platform (`Locale.getDefault(Locale.Category.FORMAT)` on Android, `NSLocale.currentLocale` on iOS, the browser's locale on web), read on each call. The locale decides the separators, grouping and the symbol's position and spacing; the `Currency` decides the ISO code, the symbol (`Currency.symbol`) and the fraction digits (`Currency.decimalPlaces`). `Text.Money` renders through `formatDisplay`.

---

## Text Composables

```kotlin
@Composable
fun Text(
    clause: Clause, modifier: Modifier = Modifier,
    style: TextStyle = Theme.typography.body,
    maxLines: Int? = null,
    lineHeight: TextUnit = TextUnit.Unspecified,
    overflow: TextOverflow = TextOverflow.Clip,
)

@Composable
fun TextLink(
    clause: Text, modifier: Modifier = Modifier,
    textDecoration: TextDecoration = TextDecoration.Underline,
    style: TextStyle = Theme.typography.body.copy(fontWeight = FontWeight.SemiBold),
    enabled: Boolean = true,
    onClick: () -> Unit,
)
// Colour: the clause's intent colour, else style.color, else LocalContentColor.
// Disabled links use Theme.colors.elementInteractive.disabled.

/**
 * The plain text Text would render for [clause], for String-only APIs: a content description, a click label.
 * Formatting and links are dropped; a Graphics contributes its contentDescription, or nothing when decorative.
 * Reads no theme, so it works outside WithTheme.
 */
@Composable
fun rememberPlainText(clause: Clause): String

@Composable
fun WithTextClickHandler(
    onGraphicsClick: ((tag: String) -> Unit)? = null,
    onTextActionClick: ((tag: String) -> Unit)? = null,
    content: @Composable () -> Unit,
)
```

Clickable clauses (`textActionId` on text, `actionId` on `Graphics`) take their look only from their own `TextFormat`. Synapse opts their links out of Material3's default link style (an underline in `MaterialTheme.colorScheme.primary`), so add `TextFormat.Underline` or an intent when a link should look like one.

---

## Extension Functions

```kotlin
fun String.asText(format: TextFormat? = null, textActionId: String? = null): Text
fun String.asMention(textActionId: String? = null): Text  // Bold + Emphasis background
fun Text.asClickable(textId: String): Text
fun Text.withFormat(format: TextFormat): Text
fun Clause.toComposite(): CompositeClause
fun localizedClause(resId: StringResource, args: List<Clause> = emptyList(), format: TextFormat? = null): Text.Localized
```

---

## Markdown

```kotlin
// package: com.ribads.synapse.ui.element.text.markdown
fun String.asMarkdown(): Clause
```

Parses inline Markdown into a `Clause` for rendering with `Text`. Supported syntax:

- `*italic*`
- `**bold**`
- `***bold italic***`
- `~~strikethrough~~`
- `[text](actionId)` — clickable link (handle via `WithTextClickHandler`)
- `\*` — escape a special character
- Nesting: `**bold *and italic* text**`

A string with no Markdown syntax produces a single `Text.Simple`.
