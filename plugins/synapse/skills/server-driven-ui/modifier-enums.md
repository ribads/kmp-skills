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
| `weight` | `Float?` | Share of the free space along a `Row` or `Column`, as Compose's `weight`. Applies to a direct child of a `Row` or `Column` (a `Conditional` branch counts as its position); ignored elsewhere. Must be > 0. |
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
| `gradient` | `UIGradient?` | Gradient background sized to the node (applied over backgroundColor) |
| `cornerRadius` | `Float?` | Corner radius in dp; rounds the background and border and clips the content |
| `borderWidth` | `Float?` | Border stroke width in dp |
| `borderColor` | `String?` | Border color as hex |

### Scroll

| Field | Type | Description |
|-------|------|-------------|
| `verticalScroll` | `Boolean?` | Makes a `Column` scroll vertically; every other node type ignores it |

### Interaction

| Field | Type | Description |
|-------|------|-------------|
| `clickActionId` | `String?` | Action fired when element is clicked (empty payload) |

### Values Compose cannot build

A negative padding, a non-positive `aspectRatio` or `weight`, or a radial gradient without a positive `radius` is reported through `RenderDiagnostics.onNodeRenderError`; the node still draws, without its modifier (or without its weight).

---

## UIDimension (sealed, type-discriminated)

| Variant | JSON | Description |
|---------|------|-------------|
| Fixed | `{ "type": "fixed", "dp": N }` | Exact size in dp |
| Wrap | `{ "type": "wrap" }` | Wrap content |
| Fill | `{ "type": "fill" }` | Fill available space |

---

## UIGradient (sealed, type-discriminated)

Laid out over the node it paints. One colour paints solid, no colours paint nothing, and `stops` apply only when there is one per colour.

**Linear**: `colors` (List\<String\>), `stops` (List\<Float\>?), `angle` (Float degrees, default 0: left to right; 90: top to bottom). Runs through the node's centre, edge to edge.
```json
{ "type": "linear", "colors": ["#FF0000", "#0000FF"], "angle": 90 }
```

**Radial**: `colors` (List\<String\>), `stops` (List\<Float\>?), `centerX` (Float, default 0.5), `centerY` (Float, default 0.5), `radius` (Float, default 0.5). Centre in fractions of the node's width and height; `radius` a fraction of its longer side, > 0.
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

With the container's `spacing` set, `Space*` values share out what is left once neighbours are `spacing` apart.

### UIAlignment

`Start`, `End`, `Center`, `Top`, `Bottom`, `CenterStart`, `CenterEnd`, `TopStart`, `TopEnd`, `BottomStart`, `BottomEnd`

### UIOrientation

`Vertical`, `Horizontal`

### UIContentScale

`Fit` (default: the whole image inside the bounds), `Crop` (covers the bounds, cutting off the overhang)
