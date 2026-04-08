---
name: server-driven-ui
description: Use when implementing server-driven UI, rendering UI from JSON schemas, dynamic screens from backend responses, or building a JSON-to-Compose rendering pipeline in a KMP project. This is the Synapse Renderer framework.
user-invocable: true
---

# ui:renderer — Server-Driven UI

**Module**: `ui:renderer` | **Artifact**: `com.ribads.synapse:ui-renderer`
**Package**: `com.ribads.synapse.ui.renderer`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-renderer:<version>")
}
```

Depends on `ui:element` and `ui:component`.

---

## Quick Start

```kotlin
// Deserialize
val root: UINode = jsonString.toUINode()
val nodes: List<UINode> = jsonString.toUINodes()

// Render
@Composable
fun MyScreen(json: String) {
    val root = remember(json) { json.toUINode() }
    SynapseRenderer(
        root = root,
        actionHandler = ActionHandler { actionId, payload ->
            when (actionId) {
                "submit" -> viewModel.submit(payload)
                "navigate_back" -> navigator.pop()
            }
        }
    )
}

fun interface ActionHandler {
    fun onAction(actionId: String, payload: Map<String, String>)
}
```

---

## JSON Node Types

Type-discriminated via `"type"` field. Unknown types deserialize to `UINode.Unknown` (renders nothing — forward compatible).

### Layout Nodes

| Type | Maps to | Key fields |
|------|---------|-----------|
| `Column` | Compose `Column` | `children`, `verticalArrangement`, `horizontalAlignment` |
| `Row` | Compose `Row` | `children`, `horizontalArrangement`, `verticalAlignment` |
| `Box` | Compose `Box` | `children`, `contentAlignment` |
| `LazyColumn` | Compose `LazyColumn` | `children`, `verticalArrangement` |
| `Spacer` | Compose `Spacer` | (modifier only) |
| `Card` | Elevated container | `children`, `actionId` |

### Content Nodes

| Type | Key fields |
|------|-----------|
| `Text` | `content`, `style` (UITypographyToken), `clauseStyle` (UIClauseStyle), `actionId`, `maxLines` |
| `MoneyText` | `amount` (Long, minor units), `currency` (ISO 4217), `style`, `clauseStyle` |
| `Image` | `url`, `contentDescription`, `actionId` |
| `Icon` | `url`, `adaptive` (Boolean), `actionId` |

### Button Nodes (shared fields: `title`, `leadingImageUrl`, `trailingImageUrl`, `state`, `actionId`)

| Type | Style |
|------|-------|
| `PrimaryButton` | Filled, high-emphasis |
| `OutlineButton` | Outlined, medium-emphasis |
| `SmallButton` | Compact filled |
| `SmallOutlineButton` | Compact outlined |

`UIButtonState`: `Enabled`, `Disabled`, `Loading`

### Input Nodes

| Type | Key fields |
|------|-----------|
| `TextField` | `label`, `placeholder`, `initialValue`, `isError`, `footerText`, `stateKey`, `onValueChangeActionId` |
| `PasswordField` | Same as TextField |
| `Checkbox` | `checked`, `label`, `stateKey`, `onCheckedChangeActionId` |
| `RadioButton` | `selected`, `label`, `stateKey`, `onSelectedChangeActionId` |
| `Switch` | `checked`, `label`, `stateKey`, `onCheckedChangeActionId` |

### Base Fields (all nodes)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `String?` | Optional node identifier |
| `modifier` | `UIModifier?` | Styling/layout modifiers |
| `visibility` | `UIVisibility?` | Rendering visibility control |

### UIModifier

`padding`, `fillMaxWidth`, `fillMaxHeight`, `width`, `height`, `aspectRatio`, `cornerRadius`, `background`, `weight`

### UITypographyToken

`H1`, `H2`, `H3`, `H4`, `HeadingS`, `HeadingM`, `Body`, `BodyM`, `BodyS`, `BodyXs`, `LabelS`, `LabelXs`

### UIClauseStyle

`Regular`, `Caution`, `Emphasis`, `Success`, `Error`

---

## Example JSON

```json
{
  "type": "Column",
  "modifier": { "fillMaxWidth": true, "padding": 16 },
  "children": [
    { "type": "Text", "content": "Transfer complete", "style": "HeadingM", "clauseStyle": "Success" },
    { "type": "MoneyText", "amount": 249999, "currency": "GBP", "style": "H1" },
    { "type": "Spacer", "modifier": { "height": { "type": "fixed", "dp": 24 } } },
    { "type": "PrimaryButton", "title": "Done", "actionId": "dismiss" }
  ]
}
```

Extensible via `NodeRendererRegistry` for custom node types.
