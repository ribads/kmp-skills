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

    data class Money(
        val amount: Long,                        // Minor units (cents/pence)
        val currency: Currency = Currency.GBP,
        override val textActionId: String? = null,
        override val format: TextFormat? = null,
    ) : Text()

    data class Timestamp(
        val date: Long,                           // Unix timestamp millis
        val pattern: String? = null,              // Format pattern
        override val textActionId: String? = null,
        val timeZone: TimeZone? = null,
        override val format: TextFormat? = null,
    ) : Text()

    companion object {
        val empty: Text = Text.Simple("")
        val whiteSpace: Text = Text.Simple(" ")
        val newLine: Text = Text.Simple("\n")
        fun listOf(vararg items: Clause): Clause
    }
}

data class Graphics(
    val image: Image,
    val intent: TextIntent? = null,
    val actionId: String? = null,
    val size: Int? = null,         // Size in sp (default 20sp)
    val blend: Boolean = false,    // Blend with text color
    val contentDescription: String? = null,  // Screen-reader label; null = decorative
) : Clause()

data class CompositeClause(val items: List<Clause>) : Clause()
```

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
    fun parseMoney(input: String): Long
    fun formatDisplay(amount: Long, currency: Currency): String
    fun formatAmount(amount: Double, currency: Currency): String
}

fun getMoneyParser(): MoneyParser
```

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
    invertedColors: Boolean = Theme.invertedColors,
    onClick: () -> Unit,
)

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
