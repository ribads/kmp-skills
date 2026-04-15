# UIModifier & Enums Reference

## UIModifier

All fields optional.

### Padding

| Field | Type | Description |
|-------|------|-------------|
| `padding` | `Float?` | Uniform padding on all sides (dp) |
| `paddingStart` | `Float?` | Start (LTR: left) padding (dp) |
| `paddingEnd` | `Float?` | End (LTR: right) padding (dp) |
| `paddingTop` | `Float?` | Top padding (dp) |
| `paddingBottom` | `Float?` | Bottom padding (dp) |

### Sizing

| Field | Type | Description |
|-------|------|-------------|
| `width` | `UIDimension?` | Explicit width |
| `height` | `UIDimension?` | Explicit height |
| `fillMaxWidth` | `Boolean?` | Expand to fill available width |
| `fillMaxHeight` | `Boolean?` | Expand to fill available height |
| `weight` | `Float?` | Flex weight within Row or Column |
| `aspectRatio` | `Float?` | Width-to-height ratio (e.g. 1.78 for 16:9) |

### Positioning

| Field | Type | Description |
|-------|------|-------------|
| `absoluteX` | `Float?` | X offset in dp |
| `absoluteY` | `Float?` | Y offset in dp |
| `relativeX` | `Float?` | X as fraction of parent width (0.0–1.0) |
| `relativeY` | `Float?` | Y as fraction of parent height (0.0–1.0) |
| `zIndex` | `Float?` | Stack drawing order (higher = on top) |

### Appearance

| Field | Type | Description |
|-------|------|-------------|
| `backgroundColor` | `String?` | Background color as hex (e.g. `"#FF0000"`) |
| `gradient` | `UIGradient?` | Gradient background (applied over backgroundColor) |
| `cornerRadius` | `Float?` | Corner radius in dp |
| `borderWidth` | `Float?` | Border stroke width in dp |
| `borderColor` | `String?` | Border color as hex |

### Scroll

| Field | Type | Description |
|-------|------|-------------|
| `verticalScroll` | `Boolean?` | Enable vertical scrolling |

### Interaction

| Field | Type | Description |
|-------|------|-------------|
| `clickActionId` | `String?` | Action fired when element is clicked |

---

## UIDimension (sealed, type-discriminated)

| Variant | JSON | Description |
|---------|------|-------------|
| Fixed | `{ "type": "fixed", "dp": N }` | Exact size in dp |
| Wrap | `{ "type": "wrap" }` | Wrap content |
| Fill | `{ "type": "fill" }` | Fill available space |

---

## UIGradient (sealed, type-discriminated)

**Linear**: `colors` (List\<String\>), `stops` (List\<Float\>?), `angle` (Float, default 0)
```json
{ "type": "linear", "colors": ["#FF0000", "#0000FF"], "angle": 90 }
```

**Radial**: `colors` (List\<String\>), `stops` (List\<Float\>?), `centerX` (Float, default 0.5), `centerY` (Float, default 0.5), `radius` (Float, default 0.5)
```json
{ "type": "radial", "colors": ["#FFFFFF", "#000000"], "centerX": 0.5, "centerY": 0.5, "radius": 0.7 }
```

---

## Enums

### UITypographyToken

`H1`, `H2`, `H3`, `H4`, `HeadingS`, `HeadingM`, `Button`, `Body`, `BodyM`, `BodyS`, `BodyXs`, `LabelS`, `LabelXs`

### UITextFormat

Data class for rich text decoration + semantic color intents.

```kotlin
@Serializable
data class UITextFormat(
    val bold: Boolean = false,
    val italic: Boolean = false,
    val underline: Boolean = false,
    val strikethrough: Boolean = false,
    val intent: UITextIntent? = null,
    val backgroundIntent: UITextIntent? = null,
)
```

JSON examples:
```json
{ "textFormat": { "bold": true } }
{ "textFormat": { "intent": "Error" } }
{ "textFormat": { "bold": true, "italic": true, "intent": "Success" } }
{ "textFormat": { "strikethrough": true, "intent": "Caution" } }
```

### UITextIntent

`Caution`, `Emphasis`, `Success`, `Error`

### UIVisibility

`Visible`, `Invisible`, `Gone`

### UIArrangement

`Start`, `End`, `Center`, `SpaceBetween`, `SpaceAround`, `SpaceEvenly`

### UIAlignment

`Start`, `End`, `Center`, `Top`, `Bottom`, `CenterStart`, `CenterEnd`, `TopStart`, `TopEnd`, `BottomStart`, `BottomEnd`

### UIOrientation

`Vertical`, `Horizontal`
