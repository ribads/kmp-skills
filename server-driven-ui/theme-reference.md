# UITheme Reference

JSON-declarable theme that overrides the design system at render time. Passed via `UIScreen.theme` or the `renderedComposable` `theme` parameter.

```kotlin
@Serializable
data class UITheme(
    val colors: UIThemeColors? = null,
    val typography: UIThemeTypography? = null,
    val spacing: UIThemeSpacing? = null,
    val shape: UIThemeShape? = null,
)
```

---

## UIThemeColors

```kotlin
@Serializable
data class UIThemeColors(
    val surface: UIThemeSurface? = null,
    val surfaceInteractive: UIThemeSurfaceInteractive? = null,
    val border: UIThemeBorder? = null,
    val element: UIThemeElement? = null,
    val elementInteractive: UIThemeElementInteractive? = null,
    val shadow: UIThemeShadow? = null,
    val intents: UIThemeIntents? = null,
)
```

**UIThemeSurface**: `primaryLight`, `secondaryLight`, `subtleLight`, `primaryDark`, `secondaryDark`, `subtleDark` (all `String?` hex)

**UIThemeSurfaceInteractive**: `enabledOnLight`, `hoverTapOnLight`, `disabledOnLight`, `enabledOnDark`, `hoverTapOnDark`, `disabledOnDark` (all `String?` hex)

**UIThemeBorder**: `primaryOnLight`, `secondaryOnLight`, `emphasisOnLight`, `primaryOnDark`, `secondaryOnDark`, `emphasisOnDark` (all `String?` hex)

**UIThemeElement**: `primaryOnLight`, `secondaryOnLight`, `primaryOnDark`, `secondaryOnDark` (all `String?` hex)

**UIThemeElementInteractive**: `enabledOnLight`, `hoverTapOnLight`, `disabledOnLight`, `enabledOnDark`, `hoverTapOnDark`, `disabledOnDark` (all `String?` hex)

**UIThemeShadow**: `spotOnLight`, `spotOnDark` (all `String?` hex)

**UIThemeIntents**: `accent`, `success`, `error`, `warning` (all `UIThemeIntentPalette?`)

**UIThemeIntentPalette**: `contentOnLight`, `contentOnDark`, `surfaceOnLight`, `surfaceOnDark`, `borderOnLight`, `borderOnDark` (all `String?` hex)

---

## UIThemeTypography

```kotlin
@Serializable
data class UIThemeTypography(
    val fontFamily: String? = null,
    val h1: UIThemeTextStyle? = null,
    val h2: UIThemeTextStyle? = null,
    val h3: UIThemeTextStyle? = null,
    val h4: UIThemeTextStyle? = null,
    val headingS: UIThemeTextStyle? = null,
    val headingM: UIThemeTextStyle? = null,
    val button: UIThemeTextStyle? = null,
    val body: UIThemeTextStyle? = null,
    val bodyM: UIThemeTextStyle? = null,
    val bodyS: UIThemeTextStyle? = null,
    val bodyXs: UIThemeTextStyle? = null,
    val labelS: UIThemeTextStyle? = null,
    val labelXs: UIThemeTextStyle? = null,
)
```

**UIThemeTextStyle**: `fontSize` (Float?), `fontWeight` (Int?), `lineHeight` (Float?), `letterSpacing` (Float?)

---

## UIThemeSpacing

`x1`, `x2`, `x3`, `x4`, `x5`, `x6`, `x7`, `x8`, `x9`, `x10`, `x12`, `x14`, `x16`, `x18`, `x22`, `x24`, `x32` (all `Float?`)

---

## UIThemeShape

`button`, `round`, `chip`, `image`, `circle`, `text`, `card` (all `Float?`)

---

## Theme JSON Example

```json
{
  "theme": {
    "colors": {
      "surfaceInteractive": {
        "enabledOnLight": "#1A73E8",
        "enabledOnDark": "#8AB4F8"
      },
      "intents": {
        "success": {
          "contentOnLight": "#1B5E20",
          "surfaceOnLight": "#E8F5E9"
        }
      }
    },
    "typography": {
      "fontFamily": "Inter",
      "h1": { "fontSize": 32, "fontWeight": 700 }
    },
    "shape": {
      "button": 12,
      "card": 16
    }
  }
}
```
