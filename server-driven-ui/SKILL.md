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
    fun onAction(actionId: String, payload: Map<String, Any?>)
}
```

---

## SynapseRenderer

```kotlin
@Composable
fun SynapseRenderer(
    root: UINode,
    actionHandler: ActionHandler,
    stateHolder: RendererStateHolder = remember { RendererStateHolder() },
    registry: NodeRendererRegistry = remember { NodeRendererRegistry.defaults() },
    conditionEvaluator: ConditionEvaluator = ConditionEvaluator.AlwaysFalse,
    collectionProvider: CollectionProvider = CollectionProvider.Empty,
    mediaProvider: MediaProvider = MediaProvider.NoOp,
)

@Composable
fun SynapseRenderer(
    nodes: List<UINode>,
    actionHandler: ActionHandler,
    stateHolder: RendererStateHolder = remember { RendererStateHolder() },
    registry: NodeRendererRegistry = remember { NodeRendererRegistry.defaults() },
    conditionEvaluator: ConditionEvaluator = ConditionEvaluator.AlwaysFalse,
    collectionProvider: CollectionProvider = CollectionProvider.Empty,
    mediaProvider: MediaProvider = MediaProvider.NoOp,
)
```

Extensible via `NodeRendererRegistry` for custom node types.

---

## Node Type Catalog

Type-discriminated via `"type"` field. Unknown types → `UINode.Unknown` (renders nothing — forward compatible).

| Category | Types |
|----------|-------|
| **Layout** | `Column`, `Row`, `Box`, `LazyColumn`, `LazyRow`, `LazyGrid`, `Spacer`, `Card`, `Expandable` |
| **Content** | `Text`, `MoneyText`, `Image`, `Icon`, `RichText` |
| **Buttons** | `PrimaryButton`, `OutlineButton`, `SmallButton`, `SmallOutlineButton` |
| **Inputs** | `TextField`, `PasswordField`, `CurrencyField`, `SelectionField`, `DropdownField`, `TextArea`, `ImagePicker`, `DatePicker`, `NumberField`, `SearchBar`, `RatingInput`, `ChipGroup`, `Slider`, `Stepper`, `TimePicker`, `Timer` |
| **Toggle/Progress** | `Checkbox`, `RadioGroup`, `ProgressBar`, `CircularProgress` |
| **Structured** | `Divider`, `Scaffold`, `TopNavBar`, `Tray`, `TabLayout`, `ConfirmDialog`, `EmptyState` |
| **Charts** | `BarChart`, `LineChart`, `PieChart` |
| **Meta** | `Conditional`, `Unknown` |

For complete field reference for each node type, see [nodes-reference.md](nodes-reference.md).

---

## Multi-Page Navigation

**Module**: `ui:renderer-navigation` | **Artifact**: `com.ribads.synapse:ui-renderer-navigation`

### UIScreen

```kotlin
@Serializable
data class UIScreen(
    val startPage: String? = null,
    val theme: UITheme? = null,
    val data: DataSchema? = null,
    val pages: List<UIPage> = emptyList(),
) {
    val entryPage: String?
}

@Serializable
data class UIPage(val id: String, val root: UINode)

fun String.toUIScreen(): UIScreen
```

### renderedEntries / renderedEntry

Server-driven pages are addressed by a single typed key carrying the dynamic page id as data, so they fit Navigation 3's typed entry provider:

```kotlin
@Serializable
data class RenderedPageKey(val baseRoute: String, val pageId: String) : NavKey

// Fold into a feature's FeatureLauncher.serializers so rendered pages survive saved state on iOS/web:
val rendererNavigationSerializers: SerializersModule
```

Register rendered pages inside a feature's `EntryProviderScope<NavKey>.register(dispatcher)` block. When `config.dataSchema` is provided, `ReactiveDataStore`, `MutationExecutor`, `SchemaConditionEvaluator`, and `CollectionProvider` are created automatically. The `mutation:` action prefix is intercepted and routed to the executor.

```kotlin
// One base route (convenience):
fun EntryProviderScope<NavKey>.renderedEntry(
    baseRoute: String,
    schemaStore: SchemaStore,
    actionHandler: ActionHandler,
    navigationDispatcher: NavigationDispatcher,
    config: RenderedPageConfig = RenderedPageConfig(),
    onPageNotFound: @Composable (pageId: String) -> Unit = { /* minimal default */ },
)

// Multiple base routes in a single RenderedPageKey registration:
fun EntryProviderScope<NavKey>.renderedEntries(block: RenderedRoutesBuilder.() -> Unit)

// Navigate to a rendered page:
fun NavigationDispatcher.navigateToRenderedPage(baseRoute: String, pageId: String, clearStack: Boolean = false)

data class RenderedPageConfig(
    val registry: NodeRendererRegistry = NodeRendererRegistry.defaults(),
    val conditionEvaluator: ConditionEvaluator = ConditionEvaluator.AlwaysFalse,
    val stateHolder: RendererStateHolder = RendererStateHolder(),
    val dataSchema: DataSchema? = null,
    val theme: UITheme? = null,
    val fontResolver: FontResolver = FontResolver.Default,
    val mediaProvider: MediaProvider = MediaProvider.NoOp,
)
```

`stateHolder` and `conditionEvaluator` are ignored when `dataSchema` is set — the `ReactiveDataStore` takes over both roles.

**Built-in action prefixes:**
- `renderer:navigate:<pageId>` — navigates to another rendered page
- `renderer:back` — pops the back stack
- `mutation:<name>` — executes a declared data mutation

---

## Detailed Reference

- [Node Types](nodes-reference.md) — All node fields, base fields, data-bound extensions
- [Modifiers & Enums](modifier-enums.md) — UIModifier, UIDimension, UIGradient, all enums
- [Data Layer](data-layer.md) — DataSchema, fields, collections, mutations, conditions, runtime classes
- [Theme](theme-reference.md) — UITheme, colors, typography, spacing, shape
- [Examples](examples.md) — JSON examples for all features
