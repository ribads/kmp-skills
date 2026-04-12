---
name: ui-element
description: Use when implementing theming, design tokens, colors, typography, spacing, shapes, image/icon loading, rich text (money, timestamps, clickable links, inline icons, formatting), or shimmer animations in a KMP Compose project. This is the Synapse design system foundation.
user-invocable: true
---

# ui:element — Design System Foundation

**Module**: `ui:element` | **Artifact**: `com.ribads.synapse:ui-element`
**Package**: `com.ribads.synapse.ui.element`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-element:<version>")
}
```

---

## Theme System

```kotlin
@Composable
fun SynapseTheme(invertedColors: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit)

@Composable
fun AuroraTheme(invertedColors: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit)

@Composable
fun WithTheme(colors: Colors, typography: Typography, shape: Shape, content: @Composable () -> Unit)

object Theme {
    val colors: Colors          @Composable get()
    val typography: Typography  @Composable get()
    val spacing: Spacing        @Composable get()
    val shape: Shape            @Composable get()
}
```

### Colors

```kotlin
@Immutable
data class Colors(
    val surface: Surface,
    val surfaceInteractive: SurfaceInteractive,
    val shadow: Shadow,
    val border: Border,
    val element: Element,
    val elementInteractive: ElementInteractive,
    val intents: Intents,
)

@Immutable
data class Surface(
    val primaryLight: Color, val secondaryLight: Color, val subtleLight: Color,
    val primaryDark: Color, val secondaryDark: Color, val subtleDark: Color,
)

@Immutable
data class SurfaceInteractive(
    val enabledOnLight: Color, val hoverTapOnLight: Color, val disabledOnLight: Color,
    val enabledOnDark: Color, val hoverTapOnDark: Color, val disabledOnDark: Color,
)

@Immutable
data class Border(
    val primaryOnLight: Color, val secondaryOnLight: Color, val emphasisOnLight: Color,
    val primaryOnDark: Color, val secondaryOnDark: Color, val emphasisOnDark: Color,
)

@Immutable
data class Shadow(val spotOnLight: Color, val spotOnDark: Color)

@Immutable
data class Element(
    val primaryOnLight: Color, val secondaryOnLight: Color,
    val primaryOnDark: Color, val secondaryOnDark: Color,
)

@Immutable
data class ElementInteractive(
    val enabledOnLight: Color, val hoverTapOnLight: Color, val disabledOnLight: Color,
    val enabledOnDark: Color, val hoverTapOnDark: Color, val disabledOnDark: Color,
)

@Immutable
data class Intents(val accent: IntentPalette, val success: IntentPalette, val error: IntentPalette, val warning: IntentPalette)

@Immutable
data class IntentPalette(
    val contentOnLight: Color, val contentOnDark: Color,
    val surfaceOnLight: Color, val surfaceOnDark: Color,
    val borderOnLight: Color, val borderOnDark: Color,
)
```

### Typography

```kotlin
@Immutable
data class Typography(
    val h1: TextStyle,
    val h2: TextStyle,
    val h3: TextStyle,
    val h4: TextStyle,
    val headingS: TextStyle,
    val headingM: TextStyle,
    val button: TextStyle,
    val body: TextStyle,
    val bodyM: TextStyle,
    val bodyS: TextStyle,
    val bodyXs: TextStyle,
    val labelS: TextStyle,
    val labelXs: TextStyle,
)
```

### Spacing

```kotlin
@Immutable
data class Spacing(
    val x1: Dp, val x2: Dp, val x3: Dp, val x4: Dp, val x5: Dp,
    val x6: Dp, val x7: Dp, val x8: Dp, val x9: Dp, val x10: Dp,
    val x12: Dp, val x14: Dp, val x16: Dp, val x18: Dp,
    val x22: Dp, val x24: Dp, val x32: Dp,
)
```

### Shape

```kotlin
@Immutable
data class Shape(
    val buttonShape: Shape,
    val roundShape: Shape,
    val chipShape: Shape,
    val imageShape: Shape,
    val circleShape: Shape,
    val textShape: Shape,
    val card: Shape,
)
```

All theme values (colors, typography styles, spacing sizes, shapes) are **defined by the consuming app**, not by this library. The library provides the data structures and the `WithTheme` composable to wire them into the composition. `SynapseTheme` and `AuroraTheme` are example/preset themes — apps should create their own theme composable using `WithTheme`.

---

## Image & Icon System

```kotlin
@Immutable
sealed class Image {
    @Immutable data class Drawable(val resId: DrawableResource) : Image()
    @Immutable data class Bitmap(val filePath: String, val placeholder: Drawable? = null) : Image()
    @Immutable data class LocalIdentifier(val localIdentifier: String, val placeholder: Drawable? = null) : Image()

    companion object {
        const val DefaultAspectRatio: Float = 4f / 5f
    }
}

typealias OptionalClickCallback = (() -> Unit)?
fun OptionalClickCallback.isEnabled(): Boolean = this != null

@Composable
fun Image(
    image: Image, modifier: Modifier = Modifier,
    contentDescription: String? = null, contentScale: ContentScale = ContentScale.Fit,
    alpha: Float = DefaultAlpha, colorFilter: ColorFilter? = null,
)

@Composable
fun Icon(
    image: Image, modifier: Modifier = Modifier,
    contentDescription: String? = null, adaptive: Boolean = false,
    contentScale: ContentScale = ContentScale.Fit, alpha: Float = DefaultAlpha,
    colorFilter: ColorFilter? = null, onClick: OptionalClickCallback = null,
    isDarkTheme: Boolean = isSystemInDarkTheme(),
)

@Composable
fun WithImagePainter(
    imagePainterFactory: @Composable (String, ConstraintsSizeResolver, DrawableResource?) -> Painter,
    content: @Composable () -> Unit,
)

object ImagePainterFactory {
    @Composable
    fun createPainterFactory(): @Composable (String, ConstraintsSizeResolver, DrawableResource?) -> Painter
}
```

---

## Rich Text — Clause System

### Core Types

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
) : Clause()

data class CompositeClause(val items: List<Clause>) : Clause()
```

### TextFormat

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

### TextIntent & TextIntentPalette

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
```

### Currency

```kotlin
enum class Currency(val symbol: String, val hasDecimals: Boolean = true, val decimalPlaces: Int = 2) {
    NGN("₦"), GBP("£"), USD("$"), EUR("€"),
    JPY("¥", hasDecimals = false, decimalPlaces = 0),
    CHF("CHF"), CAD("$"), AUD("$"), NZD("$"), CNY("¥"), HKD("$");

    val code: String get() = name
}
```

### MoneyParser

```kotlin
interface MoneyParser {
    fun parseMoney(input: String): Long
    fun formatDisplay(amount: Long, currency: Currency): String
    fun formatAmount(amount: Double, currency: Currency): String
}

fun getMoneyParser(): MoneyParser
```

### Text Composables

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
    invertedColors: Boolean = isSystemInDarkTheme(),
    onClick: () -> Unit,
)

@Composable
fun WithTextClickHandler(
    onGraphicsClick: ((tag: String) -> Unit)? = null,
    onTextActionClick: ((tag: String) -> Unit)? = null,
    content: @Composable () -> Unit,
)
```

### Extension Functions

```kotlin
fun String.asText(format: TextFormat? = null, textActionId: String? = null): Text
fun String.asMention(textActionId: String? = null): Text  // Bold + Emphasis background
fun Text.asClickable(textId: String): Text
fun Text.withFormat(format: TextFormat): Text
fun Clause.toComposite(): CompositeClause
fun localizedClause(resId: StringResource, args: List<Clause> = emptyList(), format: TextFormat? = null): Text.Localized
```

---

## Shimmer

```kotlin
@Composable
fun Modifier.shimmer(showShimmer: Boolean = true): Modifier
```

---

## Hard Rules

1. **Data models must be constructed outside composables.** All `Clause`, `Text`, `Graphics`, `Image`, `TextFormat`, and other ui-element data models should be built in the UI contract (state), mapper, or reducer — never inline inside a `@Composable` function. Composables should only *render* pre-built models, not *create* them.

---

## Usage Examples

### Theme setup

The consuming app defines its own theme by constructing `Colors`, `Typography`, and `Shape` and passing them to `WithTheme`:

```kotlin
@Composable
fun MyAppTheme(content: @Composable () -> Unit) {
    val colors = Colors(
        surface = Surface(primaryLight = Color.White, secondaryLight = Color.White, ...),
        surfaceInteractive = SurfaceInteractive(...),
        border = Border(...),
        element = Element(primaryOnLight = Color.Black, secondaryOnLight = Color.Gray, ...),
        elementInteractive = ElementInteractive(...),
        shadow = Shadow(...),
        intents = Intents(
            accent = IntentPalette(...),
            success = IntentPalette(...),
            error = IntentPalette(...),
            warning = IntentPalette(...),
        ),
    )
    val typography = Typography(
        h1 = TextStyle(fontFamily = myFont, fontWeight = FontWeight.SemiBold, fontSize = 40.sp),
        body = TextStyle(fontFamily = myFont, fontWeight = FontWeight.Medium, fontSize = 16.sp),
        // ... all 13 styles
    )
    val shape = Shape(
        buttonShape = RoundedCornerShape(28.dp),
        card = RoundedCornerShape(8.dp),
        // ... all 7 shapes
    )
    WithTheme(colors = colors, typography = typography, shape = shape) {
        WithImagePainter(imagePainterFactory = ImagePainterFactory.createPainterFactory()) {
            content()
        }
    }
}

// Access tokens anywhere inside the theme
Text(text = "Hello", style = Theme.typography.h1, color = Theme.colors.element.primaryOnLight)
Spacer(Modifier.height(Theme.spacing.x4))
```

### Rich text

Build all clause models in the contract/mapper, then render in the composable:

```kotlin
// — Contract / State —
data class ViewState(
    val greeting: Clause = "Hello World".asText(),
    val boldLabel: Clause = "Bold text".asText(format = TextFormat.Bold),
    val errorLabel: Clause = "Error occurred".asText(format = TextFormat.Error),
    val styledLabel: Clause = "Bold + italic".asText(format = TextFormat.Bold + TextFormat.Italic),
    val mention: Clause = "@john".asMention(textActionId = "user_123"),
    val price: Clause = Text.Money(amount = 1999, currency = Currency.GBP),  // £19.99
    val date: Clause = Text.Timestamp(date = 1718000000000L, pattern = "dd MMM yyyy"),
    val featured: Clause = Text.listOf(
        Graphics(image = Image.Drawable(Res.drawable.ic_star), intent = TextIntent.Emphasis),
        " Featured".asText(format = TextFormat.Bold),
    ),
    val link: Clause = "Click here".asText().asClickable("link_id"),
)
```

```kotlin
// — Screen (composable) — only renders pre-built models
@Composable
fun MyScreen(state: ViewState) {
    Text(clause = state.greeting)
    Text(clause = state.boldLabel)
    Text(clause = state.errorLabel)
    Text(clause = state.styledLabel)
    Text(clause = state.mention)
    Text(clause = state.price)
    Text(clause = state.date)
    Text(clause = state.featured)

    WithTextClickHandler(onTextActionClick = { tag -> handleClick(tag) }) {
        Text(clause = state.link)
    }
}
```

```kotlin
// Custom intent palette (theme-level, wraps content)
WithTextIntentPalette(
    palette = textIntentPalette(emphasisContent = Color.Blue, emphasisSurface = Color.LightGray)
) {
    Text(clause = state.styledLabel)
}
```

### Image & Icon

```kotlin
// — Contract / State —
data class ViewState(
    val photo: Image = Image.Bitmap("https://example.com/photo.jpg"),
    val settingsIcon: Image = Image.Drawable(Res.drawable.ic_settings),
)

// — Screen —
@Composable
fun MyScreen(state: ViewState, onSettingsClick: () -> Unit) {
    Image(image = state.photo, modifier = Modifier.fillMaxWidth())
    Icon(image = state.settingsIcon, modifier = Modifier.size(24.dp), adaptive = true, onClick = onSettingsClick)
}
```

### Shimmer loading

```kotlin
Box(modifier = Modifier.size(200.dp).shimmer(showShimmer = isLoading))
```
