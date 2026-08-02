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

Depends on `ui:renderer-core`, `ui:element`, and `ui:component`.

### ui:renderer-core

**Artifact**: `com.ribads.synapse:ui-renderer-core` | Targets: Android (via JVM), iOS, JVM, wasmJs

The engine-neutral half: schema, state contracts, actions, templating, conditions, markdown,
resolved theme, and diagnostics, with no Compose dependency. `ui:renderer` exposes it through
`api`, so depend on it directly only when you need the core without a rendering engine, such as
validating schemas on a server or in a tool.

```kotlin
implementation("com.ribads.synapse:ui-renderer-core:<version>")
```

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
    diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,
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
    diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,
)
```

Extensible via `NodeRendererRegistry` for custom node types.

---

## State, Conditions, Collections

All three contracts are flow-shaped, so the same objects drive Compose and any other engine.

```kotlin
interface RendererStateHolder {
    fun getOrPutString(key: String, initialValue: String = ""): StateFlow<String>
    fun putString(key: String, value: String)
    fun getString(key: String): String?
    // same triple for Long?, Double?, Boolean

    fun allStringState(): Map<String, String>
    fun allLongState(): Map<String, Long?>
    fun allDoubleState(): Map<String, Double?>
    fun allBooleanState(): Map<String, Boolean>

    /** Advances once per settled change, and once on clear. */
    val revision: StateFlow<Long>

    fun clear()

    companion object { operator fun invoke(): RendererStateHolder = InMemoryRendererStateHolder() }
}

fun interface CollectionProvider {
    fun getCollection(name: String): StateFlow<List<DataRecord>>
    companion object { val Empty: CollectionProvider }
}

fun interface ConditionEvaluator {
    fun conditionFlow(conditionKey: String): StateFlow<Boolean>
    fun evaluate(conditionKey: String): Boolean = conditionFlow(conditionKey).value
    companion object { val AlwaysFalse: ConditionEvaluator }
}

typealias DataRecord = Map<String, Any?>
```

Read in a composable with `collectAsState()`. Outside composition, subscribe by callback:

```kotlin
class WatchHandle { fun cancel() }

fun RendererStateHolder.watchString(key: String, initialValue: String = "", onChange: (String) -> Unit): WatchHandle
fun RendererStateHolder.watchLong(key: String, initialValue: Long? = null, onChange: (Long?) -> Unit): WatchHandle
fun RendererStateHolder.watchDouble(key: String, initialValue: Double? = null, onChange: (Double?) -> Unit): WatchHandle
fun RendererStateHolder.watchBoolean(key: String, initialValue: Boolean = false, onChange: (Boolean) -> Unit): WatchHandle
fun RendererStateHolder.watchRevision(onChange: (Long) -> Unit): WatchHandle
```

The callback fires with the current value before it returns, so one call both seeds and subscribes.

---

## Parsing without exceptions

```kotlin
sealed interface SchemaParseResult {
    data class Success(val node: UINode) : SchemaParseResult
    data class Failure(val message: String) : SchemaParseResult
}
fun parseUINode(json: String): SchemaParseResult

sealed interface ScreenParseResult {
    data class Success(val screen: UIScreen) : ScreenParseResult
    data class Failure(val message: String) : ScreenParseResult
}
fun parseUIScreen(json: String): ScreenParseResult

/** The discriminator a node serialises under, for registries keyed by string. */
fun UINode.schemaType(): String
```

`toUINode()` and `toUIScreen()` still throw; use these where an exception is not an option.

---

## Render diagnostics

A node type the build does not know, or one with no registered renderer, draws nothing, which
looks exactly like a node the schema meant to hide. Diagnostics are what tell the two apart.

```kotlin
interface RenderDiagnostics {
    fun onUnknownNode(nodeType: String, nodeId: String?, path: String)
    fun onUnregisteredNode(nodeType: String, nodeId: String?, path: String)
    fun onNodeRenderError(nodeType: String, nodeId: String?, path: String, error: Throwable)
    fun onActionDispatched(actionId: String, payloadKeys: Set<String>)
    fun onActionError(actionId: String, error: Throwable)
    fun onRenderPass(summary: RenderPassSummary)
    companion object { val NoOp: RenderDiagnostics }
}

data class RenderPassSummary(
    val rootId: String?,
    val totalNodes: Int,
    val renderedNodes: Int,
    val unknownNodes: Int,
    val unregisteredNodes: Int,
    val errorNodes: Int,
)

/** Counts what an engine could draw, without rendering. Validates a payload before it ships. */
fun summarizeTree(root: UINode, isRegistered: (UINode) -> Boolean): RenderPassSummary

/** Every child of a node, across every slot that holds one. */
fun UINode.children(): List<UINode>
```

`path` is a slash-separated trail of node types from the root, such as
`Scaffold/Column/LazyColumn/Text`.

Implementations must not throw. `onNodeRenderError` only fires for non-composable work in the
Compose engine, because a composable call cannot be wrapped in `try`.

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

Register rendered pages inside a feature's `EntryProviderScope<NavKey>.register(dispatcher)` block. When `config.dataSchema` is provided, a `ReactiveDataStore` and a `MutationExecutor` are created automatically, and the store answers state, collections, and conditions. The `mutation:` action prefix is intercepted and routed to the executor.

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
    val diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,
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
