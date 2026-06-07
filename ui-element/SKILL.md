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
fun WithTheme(
    colors: Colors,
    typography: Typography,
    shape: Shape,
    invertedColors: Boolean = LocalInvertedColors.current,
    spacing: Spacing? = null,                       // null keeps the built-in default spacing scale
    contentColor: Color = Color.Unspecified,        // ignored when Unspecified
    secondaryContentColor: Color = Color.Unspecified,
    content: @Composable () -> Unit,
)

object Theme {
    val invertedColors: Boolean         @Composable get()
    val colors: Colors                  @Composable get()
    val typography: Typography          @Composable get()
    val spacing: Spacing                @Composable get()
    val shape: Shape                    @Composable get()
    val contentColor: Color             @Composable get()
    val secondaryContentColor: Color    @Composable get()
}

// Public CompositionLocals — read directly when you need the raw provided value
val LocalInvertedColors: ProvidableCompositionLocal<Boolean>          // default false
val LocalContentColor: ProvidableCompositionLocal<Color>             // default Color.Unspecified
val LocalSecondaryContentColor: ProvidableCompositionLocal<Color>    // default Color.Unspecified
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
    val h1: TextStyle, val h2: TextStyle, val h3: TextStyle, val h4: TextStyle,
    val headingS: TextStyle, val headingM: TextStyle, val button: TextStyle,
    val body: TextStyle, val bodyM: TextStyle, val bodyS: TextStyle, val bodyXs: TextStyle,
    val labelS: TextStyle, val labelXs: TextStyle,
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
    val buttonShape: Shape, val roundShape: Shape, val chipShape: Shape,
    val imageShape: Shape, val circleShape: Shape, val textShape: Shape, val card: Shape,
)
```

All theme values (colors, typography styles, spacing sizes, shapes) are **defined by the consuming app**, not by this library. The library provides the data structures and the `WithTheme` composable to wire them into the composition; apps create their own theme composable that calls `WithTheme`. There are no preset/ready-made theme composables in this module. `spacing` is optional: when omitted, `WithTheme` keeps a built-in default spacing scale (`x1 = 4.dp` … `x32 = 128.dp`).

---

## Image & Icon System

```kotlin
@Immutable
sealed class Image(open val contentDescription: String? = null) {
    @Immutable data class Drawable(
        val resId: DrawableResource,
        override val contentDescription: String? = null,
    ) : Image()
    @Immutable data class Bitmap(
        val filePath: String,
        val placeholder: Drawable? = null,
        override val contentDescription: String? = null,
    ) : Image()
    @Immutable data class LocalIdentifier(
        val localIdentifier: String,
        val placeholder: Drawable? = null,
        override val contentDescription: String? = null,
    ) : Image()

    companion object {
        const val DefaultAspectRatio: Float = 4f / 5f
    }
}

/** Returns a copy of this image with [description] as its accessibility label. */
fun Image.withContentDescription(description: String): Image

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
    isDarkTheme: Boolean = Theme.invertedColors,
)

typealias AsyncImagePainterFactory =
    @Composable (String, ConstraintsSizeResolver, DrawableResource?) -> Painter

@Composable
fun WithImagePainter(
    imagePainterFactory: AsyncImagePainterFactory,
    content: @Composable () -> Unit,
)

object ImagePainterFactory {
    val Default: AsyncImagePainterFactory
    fun createPainterFactory(): AsyncImagePainterFactory
}

/**
 * Install Synapse's platform Coil components (iOS: PHAsset fetcher; Android: no-op).
 * Call on your ImageLoader.Builder before build().
 */
expect fun ImageLoader.Builder.installSynapseImageComponents(): ImageLoader.Builder
```

`contentDescription` is an optional accessibility label carried by the `Image` model and the `Graphics` clause. `null` (the default) marks the image as decorative, so screen readers skip it. When set, the `Icon` / `Image` composables and inline `Graphics` rendering announce it. An explicit `contentDescription` argument on a composable, or on a `Graphics` clause, overrides the model value; resolution is `argument ?: image.contentDescription`.

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

## Detailed Reference

- [Rich Text — Clause System](clause-reference.md) — Clause, Text, Graphics, TextFormat, TextIntent, Currency, MoneyParser, Text composables, Markdown, extensions
- [Usage Examples](examples.md) — Theme setup, rich text, image/icon, shimmer examples
