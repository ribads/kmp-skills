# Usage Examples

## Theme setup

The consuming app defines its own theme by authoring a light and a dark `Colors`, plus `Typography` and `Shape`, and passing them to `WithAppTheme` once at the root:

```kotlin
private val LightColors = Colors(
    surface = Surface(
        primary = Color.White, secondary = Grey50, subtle = Grey50,
        raised = Color.White, skeleton = Grey200,
    ),
    surfaceInteractive = SurfaceInteractive(enabled = Brand, hoverTap = BrandPressed, disabled = Grey200),
    border = Border(primary = Grey300, secondary = Grey200, emphasis = Brand),
    element = Element(primary = Ink, secondary = Grey600),
    elementInteractive = ElementInteractive(enabled = Color.White, hoverTap = BrandTint, disabled = Grey600),
    shadow = Shadow(spot = Color(0x14000000)),
    intents = Intents(
        accent = IntentPalette(content = Brand, surface = BrandTint, border = Brand),
        success = IntentPalette(content = Green, surface = Grey50, border = Green),
        error = IntentPalette(content = Red, surface = Grey50, border = Red),
        warning = IntentPalette(content = Amber, surface = Grey50, border = Amber),
    ),
)

private val DarkColors = Colors(
    surface = Surface(
        primary = Night, secondary = Night800, subtle = Night800,
        raised = Night800, skeleton = Night600,
    ),
    // ... every role again, for dark surfaces
)

@Composable
fun MyAppTheme(appearance: Appearance = Appearance.System, content: @Composable () -> Unit) {
    val typography = Typography(
        body = TextStyle(fontFamily = myFont, fontSize = 16.sp, lineHeight = 24.sp),
        h1 = TextStyle(fontFamily = myFont, fontWeight = FontWeight.SemiBold, fontSize = 40.sp),
        // ... any other role to set exactly; the rest derive from body. No colours.
    )
    val shape = Shape(
        buttonShape = RoundedCornerShape(28.dp),
        card = RoundedCornerShape(8.dp),
        // ... all 7 shapes
    )
    WithAppTheme(
        appearance = appearance,
        colorSchemes = ColorSchemes(light = LightColors, dark = DarkColors),
        typography = typography,
        shape = shape,
    ) {
        WithImagePainter(imagePainterFactory = ImagePainterFactory.createPainterFactory()) {
            content()
        }
    }
}

// Access tokens anywhere inside the theme; the role resolves for the current appearance
Text(clause = state.title, style = Theme.typography.h1.copy(color = Theme.colors.element.secondary))
Spacer(Modifier.height(Theme.spacing.x4))
```

## Fixed-appearance regions

```kotlin
// A viewfinder stays dark in a light app; its bar icons stay light while it is on screen
@Composable
fun CameraScreen(state: ViewState) {
    WithAppearance(Appearance.Dark) {
        ThemedSystemBars()
        Box(modifier = Modifier.fillMaxSize().background(Theme.colors.surface.primary)) {
            Icon(image = state.flashIcon)    // a Glyph, tinted with the dark scheme's element.primary
        }
    }
}

// A menu, dialog or custom sheet paints surface.raised; content inside sees it as its canvas
@Composable
fun FilterMenu(content: @Composable () -> Unit) {
    Box(modifier = Modifier.background(Theme.colors.surface.raised)) {
        WithRaisedSurface(content)
    }
}
```

## Rich text

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
        Graphics(image = Image.Glyph(Res.drawable.ic_star), intent = TextIntent.Emphasis),
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

## Image & Icon

```kotlin
// — Contract / State —
data class ViewState(
    val photo: Image = Image.Bitmap(
        filePath = "https://example.com/photo.jpg",
        placeholder = Image.Artwork(Res.drawable.photo_placeholder, darkResId = Res.drawable.photo_placeholder_dark),
    ),
    val settingsIcon: Image = Image.Glyph(Res.drawable.ic_settings),
    val emptyIllustration: Image = Image.Artwork(Res.drawable.empty_inbox),
)

// — Screen —
@Composable
fun MyScreen(state: ViewState, onSettingsClick: () -> Unit) {
    Image(image = state.photo, modifier = Modifier.fillMaxWidth())
    Icon(image = state.settingsIcon, modifier = Modifier.size(24.dp), onClick = onSettingsClick)   // tinted Theme.contentColor
    Icon(image = state.settingsIcon, tint = Theme.colors.element.secondary)                         // explicit tint
    Image(image = state.emptyIllustration)                                                          // drawn as authored
}
```

## Shimmer loading

```kotlin
Box(modifier = Modifier.size(200.dp).shimmer(showShimmer = isLoading))
```
