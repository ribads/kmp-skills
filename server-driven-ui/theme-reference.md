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

### How payload colours apply

The host app's theme has a light and a dark scheme of single-valued roles (see `/ui-element`). The payload keeps light/dark field pairs, and each field sets one role in one scheme: a `...Light` or `...OnLight` field sets the light scheme, a `...Dark` or `...OnDark` field sets the dark scheme, with the suffix dropped (`element.primaryOnDark` sets the dark scheme's `element.primary`).

- **Unset fields keep the host's value** for that role and appearance, so a partial theme changes only what it names. A payload that sets only `...OnLight` fields leaves dark mode entirely to the host.
- **Roles with no payload field** (`surface.raised`, `surface.skeleton`, `overlay`) always come from the host.
- **The appearance is the host's.** The payload never chooses light or dark. Compose renders the scheme for the host's `WithAppTheme` appearance; SwiftUI renders the one for the view's `\.colorScheme`.
- In Compose, a schema with no `theme` renders with the host theme unchanged. The SwiftUI engine has no host Synapse theme, so it uses iOS system colours for anything the payload leaves unset.

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
