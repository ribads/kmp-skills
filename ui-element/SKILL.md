---
name: ui-element
description: Use when implementing theming, design tokens, colors, typography, spacing, shapes, image/icon loading, rich text (money, timestamps, clickable links, inline icons, formatting), or shimmer animations in a KMP Compose project. This is the Synapse design system foundation.
user-invocable: true
---

# ui:element — Design System Foundation

**Module**: `ui:element` | **Artifact**: `com.ribads.synapse:ui-element`
**Packages**: 5 packages under `com.ribads.synapse.ui.element`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-element:<version>")
}
```

Compose runtime, foundation and UI, Coil's `coil-compose` and `kotlinx-datetime` (the `TimeZone` on `Text.Timestamp`) are `api` dependencies, so a consumer needs none of them declared to use the types this module exposes.

## Imports

Import each type from its package below.

| Package | Types |
|---|---|
| `com.ribads.synapse.ui.element.brush` | `shimmer` |
| `com.ribads.synapse.ui.element.image` | `AsyncImagePainterFactory`, `Icon`, `Image`, `ImagePainterFactory`, `OptionalClickCallback`, `WithImagePainter`, `installSynapseImageComponents`, `isEnabled`, `withContentDescription` |
| `com.ribads.synapse.ui.element.text` | `Clause`, `CompositeClause`, `Currency`, `Graphics`, `LocalTextIntentPalette`, `MoneyParser`, `Text`, `TextFormat`, `TextIntent`, `TextIntentPalette`, `TextLink`, `WithTextClickHandler`, `WithTextIntentPalette`, `asClickable`, `asMention`, `asText`, `getMoneyParser`, `localizedClause`, `rememberPlainText`, `textIntentPalette`, `toBackgroundColor`, `toColor`, `toComposite`, `withFormat` |
| `com.ribads.synapse.ui.element.text.markdown` | `asMarkdown` |
| `com.ribads.synapse.ui.element.theme` | `Appearance`, `Border`, `ColorSchemes`, `Colors`, `Element`, `ElementInteractive`, `IntentPalette`, `Intents`, `LocalContentColor`, `Overlay`, `Shadow`, `Shape`, `Spacing`, `Surface`, `SurfaceInteractive`, `Theme`, `ThemedSystemBars`, `Typography`, `WithAppTheme`, `WithAppearance`, `WithRaisedSurface`, `WithTheme` |

---

## Theme System

```kotlin
/** Which ColorSchemes entry the theme applies: a fixed one, or whichever the device is using. */
enum class Appearance { Light, Dark, System }

/**
 * The app root's theme, used once. Applies [appearance] to Synapse and to what the platform draws
 * around the app (window, system bars, dialogs, keyboard), then provides the tokens through WithTheme.
 */
@Composable
fun WithAppTheme(
    appearance: Appearance,
    colorSchemes: ColorSchemes,
    typography: Typography,
    shape: Shape,
    spacing: Spacing? = null,          // null keeps the built-in default spacing scale
    content: @Composable () -> Unit,
)

/**
 * Provides the tokens to [content] in the enclosing appearance, or the device's when nothing above
 * resolved one. Nestable: a nested call swaps the tokens for a region and keeps the appearance.
 */
@Composable
fun WithTheme(
    colorSchemes: ColorSchemes,
    typography: Typography,
    shape: Shape,
    spacing: Spacing? = null,          // null keeps the enclosing scale (the built-in default at the root)
    content: @Composable () -> Unit,
)

/** Renders [content] in a fixed appearance, whatever the app's. */
@Composable
fun WithAppearance(appearance: Appearance, content: @Composable () -> Unit)

/**
 * Makes surface.primary resolve to surface.raised for [content]. Only the colour roles change: the locals
 * below (LocalContentColor included) keep the values the container provided. Applying it twice changes nothing.
 */
@Composable
fun WithRaisedSurface(content: @Composable () -> Unit)

/**
 * Styles the system bar icons for the enclosing theme while composed. The most recently composed call
 * wins; leaving the composition hands the bars back to the previous one. No-op on iOS and wasm.
 */
@Composable
expect fun ThemedSystemBars()

object Theme {
    val colors: Colors                  @Composable get()   // the scheme for the enclosing appearance
    val colorSchemes: ColorSchemes      @Composable get()   // both schemes, as the theme received them
    val isDark: Boolean                 @Composable get()   // for assets and third-party UI, not colour picks
    val typography: Typography          @Composable get()
    @Composable inline fun <reified T : Typography> typography(): T   // the app's own Typography type; throws on a mismatch
    val spacing: Spacing                @Composable get()
    val shape: Shape                    @Composable get()
    val contentColor: Color             @Composable get()   // LocalContentColor.current
}

/** The colour of text and icons that don't set their own, for the surface they sit on. */
val LocalContentColor: ProvidableCompositionLocal<Color>
```

Besides the tokens, `WithTheme` (and so `WithAppTheme`) provides these for the resolved scheme. `WithAppearance` re-provides them for its region. `WithRaisedSurface` does not: it swaps only the colour roles, so a container that paints `surface.raised` still provides its own `LocalContentColor` (Synapse's sheets, dialogs and menus do).

| Local | Value |
|---|---|
| `LocalContentColor` | `colors.element.primary` |
| Material 3 `LocalContentColor` | `colors.element.primary`, so Material components inside match |
| `LocalTextSelectionColors` | handle `border.emphasis`, background `border.emphasis` at 40% alpha |
| `LocalIndication` | Material 3 `ripple()`, coloured by the pressed component's content colour |

Reading `Theme.colors`, `Theme.colorSchemes`, `Theme.isDark`, `Theme.shape` or `LocalContentColor` with no theme above throws, so a missing theme fails on first composition instead of rendering `Color.Unspecified`. `Theme.typography` and `Theme.spacing` fall back to `Typography(body = TextStyle.Default)` and the default spacing scale.

### Colors

Roles name what a colour is for, not what it looks like. An app authors one `Colors` per appearance, and every role resolves to a single value wherever it is read.

```kotlin
@Immutable
data class ColorSchemes(val light: Colors, val dark: Colors)

@Immutable
data class Colors(
    val surface: Surface,
    val surfaceInteractive: SurfaceInteractive,
    val shadow: Shadow,
    val border: Border,
    val element: Element,
    val elementInteractive: ElementInteractive,
    val intents: Intents,
    val overlay: Overlay = Overlay.Default,
)

@Immutable
data class Surface(
    val primary: Color,     // the canvas of the enclosing container: the screen, or the sheet/dialog/menu inside WithRaisedSurface
    val secondary: Color,   // a layered surface on the canvas: a card, an incoming chat bubble
    val subtle: Color,      // a quiet fill for tracks and disabled containers
    val raised: Color,      // sheets, dialogs and menus; dark appearances show elevation through it
    val skeleton: Color,    // loading placeholders drawn by Modifier.shimmer
)

@Immutable
data class SurfaceInteractive(val enabled: Color, val hoverTap: Color, val disabled: Color)   // backgrounds of buttons, list items

@Immutable
data class Border(
    val primary: Color,     // the outline of a text field
    val secondary: Color,   // a list separator
    val emphasis: Color,    // an outlined button's border, a focused field
)

@Immutable
data class Shadow(val spot: Color)

@Immutable
data class Element(val primary: Color, val secondary: Color)   // text and icons on Surface colours

@Immutable
data class ElementInteractive(val enabled: Color, val hoverTap: Color, val disabled: Color)   // text and icons on SurfaceInteractive colours

@Immutable
data class Intents(val accent: IntentPalette, val success: IntentPalette, val error: IntentPalette, val warning: IntentPalette)

@Immutable
data class IntentPalette(
    val content: Color,     // text, icons and indicators in the intent, drawn on the page or on surface
    val surface: Color,     // the intent's background, such as a toast or a highlighted mention
    val border: Color,      // the intent's outline
)

@Immutable
data class Overlay(
    val scrim: Color,       // dims the content beneath a dialog, or a photo under text
    val content: Color,     // text and icons drawn on a scrim or a photo
) {
    companion object {
        val Default: Overlay   // 40% black scrim, white content: reads over any content in both appearances
    }
}
```

`IntentPalette.content` must read on the page canvas: components draw it directly on `surface.primary` (a selected radio, a slider track, `TextFormat.Emphasis`, a progress indicator), not only on `IntentPalette.surface`.

### Typography

`Typography` is the set of text roles Synapse's components read, not the app's whole type scale.

```kotlin
/** Implementations must be immutable. */
@Immutable
interface Typography {
    val h1: TextStyle; val h2: TextStyle; val h3: TextStyle; val h4: TextStyle
    val headingS: TextStyle; val headingM: TextStyle; val button: TextStyle
    val body: TextStyle; val bodyM: TextStyle; val bodyS: TextStyle; val bodyXs: TextStyle
    val labelS: TextStyle; val labelXs: TextStyle
}

/**
 * Every role left out is derived from body or heading on the default scale, keeping the font family,
 * colour and other attributes of the style it comes from. Pass any role to set it exactly.
 */
fun Typography(
    body: TextStyle,
    heading: TextStyle = body.copy(fontWeight = FontWeight.SemiBold),
    h1: TextStyle = heading.copy(fontSize = 34.sp, lineHeight = 40.sp),
    h2: TextStyle = heading.copy(fontSize = 28.sp, lineHeight = 34.sp),
    h3: TextStyle = heading.copy(fontSize = 22.sp, lineHeight = 28.sp),
    h4: TextStyle = heading.copy(fontSize = 18.sp, lineHeight = 24.sp),
    headingM: TextStyle = heading.copy(fontSize = 16.sp, lineHeight = 22.sp),
    headingS: TextStyle = heading.copy(fontSize = 14.sp, lineHeight = 20.sp),
    button: TextStyle = body.copy(fontWeight = FontWeight.SemiBold, fontSize = 15.sp, lineHeight = 20.sp),
    bodyM: TextStyle = body.copy(fontWeight = FontWeight.Medium),
    bodyS: TextStyle = body.copy(fontSize = 14.sp, lineHeight = 20.sp),
    bodyXs: TextStyle = body.copy(fontSize = 12.sp, lineHeight = 16.sp),
    labelS: TextStyle = body.copy(fontWeight = FontWeight.Medium, fontSize = 12.sp, lineHeight = 16.sp),
    labelXs: TextStyle = body.copy(fontWeight = FontWeight.Medium, fontSize = 10.sp, lineHeight = 14.sp),
): Typography
```

Pick one of three ways to provide it:

```kotlin
// 1. Just a body style (and optionally a heading style); the scale is derived.
val typography = Typography(body = TextStyle(fontFamily = myFont, fontSize = 16.sp, lineHeight = 24.sp))

// 2. Every role set explicitly, by name.
val typography = Typography(body = …, h1 = …, h2 = …, /* … */ labelXs = …)

// 3. The app's own, richer type scale: implement the interface and map each role to a token.
@Immutable
data class AppTypography(
    val display: TextStyle,
    val titleL: TextStyle,
    val caption: TextStyle,
    private val roles: Typography,               // what isn't remapped below
) : Typography by roles {
    override val headingM: TextStyle get() = titleL
    override val bodyXs: TextStyle get() = caption
}

// Synapse components read the roles; app code reads its own tokens with the typed accessor.
Text(clause = title, style = Theme.typography<AppTypography>().display)
```

With option 3 the app keeps one typography object and one theme: no parallel `CompositionLocal`, and every token stays reachable through `Theme`.

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

All theme values (colour schemes, typography styles, spacing sizes, shapes) are **defined by the consuming app**, not by this library. The library provides the data structures and the composables that wire them into the composition. Apps create their own theme composable that calls `WithAppTheme` at the root. There are no preset or ready-made themes in this module. `spacing` is optional: when omitted, the theme keeps a built-in default spacing scale (`x1 = 4.dp` to `x32 = 128.dp`). Typography carries no colours: `Text` draws in the style's colour if it sets one, and in `LocalContentColor` otherwise.

---

## Image & Icon System

```kotlin
@Immutable
sealed class Image(open val contentDescription: String? = null) {
    /** A single-colour drawable used as a mask: always drawn in a tint, so it follows the theme. */
    @Immutable data class Glyph(
        val resId: DrawableResource,
        override val contentDescription: String? = null,
    ) : Image()
    /** A drawable drawn as authored (an illustration, a brand mark), with an optional dark variant. */
    @Immutable data class Artwork(
        val resId: DrawableResource,
        val darkResId: DrawableResource? = null,     // used when the enclosing theme is dark
        override val contentDescription: String? = null,
    ) : Image()
    @Immutable data class Bitmap(
        val filePath: String,
        val placeholder: Artwork? = null,
        override val contentDescription: String? = null,
    ) : Image()
    @Immutable data class LocalIdentifier(
        val localIdentifier: String,
        val placeholder: Artwork? = null,
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

/** A Glyph is tinted with LocalContentColor unless [colorFilter] is set; [colorFilter] applies to any other image as given. */
@Composable
fun Image(
    image: Image, modifier: Modifier = Modifier,
    contentDescription: String? = null, contentScale: ContentScale = ContentScale.Fit,
    alpha: Float = DefaultAlpha, colorFilter: ColorFilter? = null,
)

/** A Glyph is drawn in [tint]; any other image is drawn as authored. */
@Composable
fun Icon(
    image: Image, modifier: Modifier = Modifier,
    contentDescription: String? = null,
    tint: Color = Theme.contentColor,
    contentScale: ContentScale = ContentScale.Fit, alpha: Float = DefaultAlpha,
    onClick: OptionalClickCallback = null,
)

typealias AsyncImagePainterFactory =
    @Composable (String, ConstraintsSizeResolver, DrawableResource?) -> Painter

/** Optional: overrides the painter factory for [content]. ImagePainterFactory.Default is already installed. */
@Composable
fun WithImagePainter(
    imagePainterFactory: AsyncImagePainterFactory,
    content: @Composable () -> Unit,
)

object ImagePainterFactory {
    val Default: AsyncImagePainterFactory                 // what Image and Icon use when nothing overrides it
    fun createPainterFactory(): AsyncImagePainterFactory  // returns Default
}

/**
 * Install Synapse's platform Coil components (iOS: PHAsset fetcher; Android and web: no-op).
 * Call on your ImageLoader.Builder before build().
 */
expect fun ImageLoader.Builder.installSynapseImageComponents(): ImageLoader.Builder
```

**Loading remote and device images.** `Image.Bitmap` URLs load through Coil's Ktor network fetcher, and `ui:element` brings the Ktor engine for each platform (OkHttp on Android, Darwin on iOS, the JS engine on web), so an app needs no extra dependency for them. `WithImagePainter` is only for replacing the request pipeline (a test double, custom headers); the default works without it.

`Image.LocalIdentifier` (a Photos asset id from `/file-system`) loads on iOS only once the app's `ImageLoader` has Synapse's components. Install them once, where the app sets Coil's singleton loader, before the first image is drawn. Calling it from the shared root composable covers every platform:

```kotlin
// composeApp/commonMain, the root composable
@Composable
fun App() {
    setSingletonImageLoaderFactory { context ->      // coil3.compose
        ImageLoader.Builder(context)                 // coil3.ImageLoader
            .installSynapseImageComponents()         // registers the phasset:// fetcher on iOS
            .crossfade(true)                         // coil3.request.crossfade, optional
            .build()
    }
    MyAppTheme { /* NavContainer, screens */ }
}
```

An app whose iOS entry point builds the loader itself does the same before creating its view controller:

```kotlin
// composeApp/iosMain
fun MainViewController(): UIViewController {
    SingletonImageLoader.setSafe { context ->        // coil3.SingletonImageLoader
        ImageLoader.Builder(context).installSynapseImageComponents().build()
    }
    return ComposeUIViewController { App() }
}
```

The image type decides how a drawable is coloured. Pick it when you build the model:

- **`Glyph`** for single-colour icons (a chevron, a tab icon, a monochrome brand mark). It is always tinted: `Icon` uses `tint`, `Image` uses `LocalContentColor`, and components pass their per-state colour, so a selected and an unselected glyph each take their state's colour.
- **`Artwork`** for anything with more than one colour (illustrations, full-colour logos, flags). It is never tinted. Give it a `darkResId` when the light asset does not read on dark surfaces.
- An explicit `Image(colorFilter = ...)` overrides both rules. It is the escape hatch for tinting a `Bitmap`.

`contentDescription` is an optional accessibility label carried by the `Image` model and the `Graphics` clause. `null` (the default) marks the image as decorative, so screen readers skip it. When set, the `Icon` / `Image` composables and inline `Graphics` rendering announce it. An explicit `contentDescription` argument on a composable, or on a `Graphics` clause, overrides the model value; resolution is `argument ?: image.contentDescription`.

---

## Shimmer

```kotlin
@Composable
fun Modifier.shimmer(showShimmer: Boolean = true): Modifier   // sweeps surface.skeleton
```

---

## Dark mode

Components read roles and never branch on the appearance, so supporting dark mode is authoring the dark `Colors` and choosing where the appearance comes from.

**At the root.** Call `WithAppTheme` once, with the user's choice or `Appearance.System`:

```kotlin
@Composable
fun AppTheme(appearance: Appearance = Appearance.System, content: @Composable () -> Unit) {
    WithAppTheme(
        appearance = appearance,
        colorSchemes = ColorSchemes(light = LightColors, dark = DarkColors),
        typography = AppTypography,     // no colours in the styles
        shape = AppShape,
        content = content,
    )
}
```

If users can pick the appearance, persist it with `/storage` and read it synchronously before the first frame, so the app does not start in one appearance and switch.

**Platform sync.** `WithAppTheme` aligns what the platform draws with the chosen appearance:

- **Android 12+ (API 31):** sets the app's night mode through `UiModeManager.setApplicationNightMode`. The system persists it, so the next cold start's splash screen and window already match. It also outlives the call: an app version that stops using `WithAppTheme` keeps the last mode it set until it sets another or is reinstalled. Give the host activity a DayNight window theme (`values/` and `values-night/`) with a window background that matches `surface.primary`. An activity without `android:configChanges="uiMode"` is recreated when the appearance changes in-app.
- **Android below 12:** there is no per-app night mode without AppCompat, so only the Compose UI follows `Appearance.Light` or `Appearance.Dark`. `Appearance.System` is correct everywhere.
- **iOS:** sets `overrideUserInterfaceStyle` on the app's windows, so UIKit sheets, alerts and the keyboard match.
- **wasm:** Compose only.

**System bars.** The root claims the bar icons for the app's appearance. A full-screen region with a different appearance adds its own claim, which wins while it is composed. Make the claim in the screen that lays out what sits behind the bars, never inside a reusable component: a component cannot know whether it will be placed under a light top bar or edge to edge.

```kotlin
WithAppearance(Appearance.Dark) {
    ThemedSystemBars()
    CameraViewfinder()
}
```

**Fixed regions.** `WithAppearance(Appearance.Dark)` for regions that must stay dark (a camera, a video player, a photo viewer); `WithAppearance(Appearance.Light)` for ones that must stay light (a QR code, a receipt). Everything inside, components included, resolves roles from that scheme.

**Raised surfaces.** Sheets, dialogs and menus paint `surface.raised` and wrap their content in `WithRaisedSurface`, so a component that paints "the canvas it sits on" (`surface.primary`) matches the container. Synapse's dialogs and dropdowns already do; for trays and navigation sheets pass `ThemedBottomSheetAppearance` from `/ui-components`.

**Assets and third-party UI.** Use `Image.Artwork(resId, darkResId)` for assets that need a dark variant. Read `Theme.isDark` only to hand the appearance to UI that does not read Synapse roles, such as `PaystackPaymentSheet(darkTheme = Theme.isDark)`.

### Migrating from 0.2.0-alpha6

| alpha6 | alpha7 |
|---|---|
| `WithTheme(colors, typography, shape, invertedColors, spacing, contentColor, secondaryContentColor)` at the root | `WithAppTheme(appearance, colorSchemes, typography, shape, spacing)` |
| A nested `WithTheme(colors, ...)` | `WithTheme(colorSchemes, typography, shape, spacing)` |
| One `Colors` with `primaryLight`/`primaryDark` and `...OnLight`/`...OnDark` pairs | `ColorSchemes(light = Colors(...), dark = Colors(...))` with one value per role; add `surface.raised` and `surface.skeleton` |
| `Shadow(spotOnLight, spotOnDark)` | `Shadow(spot)` in each scheme |
| Colours baked into `Typography` styles (`color = colors.element.primaryOnLight`) | Remove them. A style colour overrides the content colour in both appearances; `Text` without one draws in `LocalContentColor`, which each surface provides |
| `Theme.colors.element.primaryOnLight`, or `if (invertedColors) ...OnDark else ...OnLight` | `Theme.colors.element.primary` |
| `invertedColors = true` on components | Wrap the region in `WithAppearance(Appearance.Dark)` |
| `Theme.invertedColors`, `LocalInvertedColors` | `Theme.isDark` (read-only) |
| `Theme.secondaryContentColor`, `LocalSecondaryContentColor` | `Theme.colors.element.secondary` |
| `isSystemInDarkTheme()` in app code | `Appearance.System` at the root, `Theme.isDark` below it |
| `Image.Drawable(res)` | `Image.Glyph(res)` for single-colour icons, `Image.Artwork(res, darkResId)` otherwise |
| `Icon(adaptive, isDarkTheme, colorFilter)` | `Icon(image, tint = ...)`; tint applies to a `Glyph` only |
| `Graphics(image, blend = true)` | `Graphics(image = Image.Glyph(res))`, tinted with the intent or text colour |
| `TextLink(invertedColors = ...)` | `TextLink(...)`, coloured by the style or `LocalContentColor` |

---

## Hard Rules

1. **Data models must be constructed outside composables.** All `Clause`, `Text`, `Graphics`, `Image`, `TextFormat`, and other ui-element data models should be built in the UI contract (state), mapper, or reducer — never inline inside a `@Composable` function. Composables should only *render* pre-built models, not *create* them.

2. **User-visible text is a `Clause`, never a `String`.** `Text` composables accept `Clause` only, by design. Use `Text.Localized(Res.string.foo)` for shipped copy and `"…".asText()` for prototypes and tests. A `String` field on a UI model is a bug waiting to happen: it cannot be localized, styled, or composed with an inline icon.

3. **`Text.Money` and `Text.Timestamp` are declarations, not formatted strings.** Carry money as `Long` minor units and dates as `Long` epoch millis all the way to the model, then emit `Text.Money(amount, currency)` / `Text.Timestamp(date, pattern, timeZone = ...)` and let the renderer format at composition time.

   Money renders in the **device's current locale** on every platform: the reader's locale decides the decimal and grouping separators and where the symbol sits, and the `Currency` decides the code, the symbol (`Currency.symbol`, so `CAD` shows `$`, not `CA$`) and the fraction digits (`decimalPlaces`).

   ```kotlin
   Text.Money(amount = 249_900, currency = Currency.GBP)   // "£2,499.00" in en-GB or en-US, "2.499,00 £" in de-DE
   Text.Money(amount = 1_500, currency = Currency.JPY)     // "¥1,500" in en-US: JPY has no minor unit
   ```

   A timestamp renders in UTC unless the clause says otherwise, so pass `timeZone = TimeZone.currentSystemDefault()` for the reader's local time; a `null` pattern renders ISO 8601 (`yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`).

   Pre-formatting into a `String` anywhere upstream (in a mapper, a use case, or worst of all a DTO) bakes in a locale and a currency symbol that the rendering context has not agreed to. Compose money and copy with `Text.listOf(...)`, `Text.whiteSpace`, and `Graphics(...)` rather than string templates.

4. **Tokens, not raw values, in app and feature code.** Colours from `Theme.colors.*`, type from `Theme.typography.<token>` (`.copy(...)` to tweak, never a fresh `TextStyle`), layout from `Theme.spacing.*`, corners from `Theme.shape.*`. Component-intrinsic geometry that is not layout spacing (a thumb radius, an avatar size) belongs in a named file-level `private val Name = 24.dp` inside the component. See `/component-authoring`.

5. **Never branch on the appearance to pick a colour.** Read the role (`Theme.colors.element.primary`), not `isSystemInDarkTheme()` or `Theme.isDark`. The appearance is resolved once, by `WithAppTheme` at the root. A region that must render in a fixed appearance (camera overlays, video scrubbers, controls over a photo) is wrapped in `WithAppearance`, which the caller owns. `Theme.isDark` exists only for dark asset variants and for UI that does not read Synapse roles.

---

## Detailed Reference

- [Rich Text — Clause System](clause-reference.md) — Clause, Text, Graphics, TextFormat, TextIntent, Currency, MoneyParser, Text composables, Markdown, extensions
- [Usage Examples](examples.md) — Theme setup, rich text, image/icon, shimmer examples
