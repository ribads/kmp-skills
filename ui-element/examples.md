# Usage Examples

## Theme setup

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

## Image & Icon

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

## Shimmer loading

```kotlin
Box(modifier = Modifier.size(200.dp).shimmer(showShimmer = isLoading))
```
