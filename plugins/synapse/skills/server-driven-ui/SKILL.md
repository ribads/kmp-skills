---
name: server-driven-ui
description: Use when implementing server-driven UI, rendering UI from JSON schemas, dynamic screens from backend responses, or building a JSON-to-Compose rendering pipeline in a KMP project. This is the Synapse Renderer framework.
user-invocable: true
---

# ui:renderer: Server-Driven UI

**Module**: `ui:renderer` | **Artifact**: `com.ribads.synapse:ui-renderer`
**Packages**: 8 packages under `com.ribads.synapse.ui.renderer`; see [Imports](#imports)

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

## Imports

Import each type from its package below.

| Package | Types |
|---|---|
| `com.ribads.synapse.ui.renderer.action` | `ActionDispatcher`, `ActionHandler`, `ActionPayload`, `bridgedActionHandler`, `onAction` |
| `com.ribads.synapse.ui.renderer.data` | `DataPersistence`, `MutationExecutor`, `MutationResult`, `ReactiveDataStore`, `renderedPageActionHandler` |
| `com.ribads.synapse.ui.renderer.diagnostics` | `RenderDiagnostics`, `RenderPassSummary`, `callbackRenderDiagnostics`, `children`, `reportNodeRenderError`, `summarizeTree` |
| `com.ribads.synapse.ui.renderer.engine` | `BoundRecordGroups`, `BoundRecords`, `CollectionProvider`, `ConditionEvaluator`, `DataRecord`, `DataRecordView`, `ITEM_CONTEXT_PAYLOAD_KEY`, `MediaProvider`, `NodeRenderer`, `NodeRendererRegistry`, `RecordConditionEvaluator`, `RenderNode`, `SynapseRenderer`, `TemplateEngine`, `boundRecords`, `committedValue`, `dispatchWithRecord`, `effectiveTextFormat`, `hasConditionalFormat`, `narrowRecords`, `recordFieldReader`, `watchBoundRecords` |
| `com.ribads.synapse.ui.renderer.navigation` | `InMemorySchemaStore`, `RenderedPageConfig`, `RenderedPageKey`, `RenderedRoutesBuilder`, `SchemaStore`, `ScreenParseResult`, `UIPage`, `UIScreen`, `load`, `navigateToRenderedPage`, `parseUIScreen`, `renderedEntries`, `renderedEntry`, `rendererNavigationSerializers`, `toUIScreen` |
| `com.ribads.synapse.ui.renderer.schema` | `ComputedField`, `DataCollection`, `DataCondition`, `DataEffect`, `DataField`, `DataFieldType`, `DataMutation`, `DataOrderBy`, `DataSchema`, `DataValueRef`, `SchemaParseResult`, `SortDirection`, `UIButtonState`, `UIDimension`, `UIGradient`, `UIModifier`, `UINavBarAction`, `UINavBarLeadingIcon`, `UINode`, `UITextFormat`, `UITextIntent`, `UITheme`, `UIThemeBorder`, `UIThemeColors`, `UIThemeElement`, `UIThemeElementInteractive`, `UIThemeIntentPalette`, `UIThemeIntents`, `UIThemeShadow`, `UIThemeShape`, `UIThemeSpacing`, `UIThemeSurface`, `UIThemeSurfaceInteractive`, `UIThemeTextStyle`, `UIThemeTypography`, `UIVisibility`, `parseUINode`, `schemaType`, `toUINode`, `toUINodes` |
| `com.ribads.synapse.ui.renderer.state` | `InMemoryRendererStateHolder`, `RendererStateHolder`, `WatchHandle`, `watchBoolean`, `watchDouble`, `watchLong`, `watchRevision`, `watchString` |
| `com.ribads.synapse.ui.renderer.theme` | `FontResolver`, `ResolvedShape`, `ResolvedTheme`, `WithRenderedTheme`, `resolve` |

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

Extensible via `NodeRendererRegistry` for custom node types:

```kotlin
fun interface NodeRenderer<N : UINode> {
    @Composable fun Render(node: N)
}

class NodeRendererRegistry {
    fun <N : UINode> get(nodeClass: KClass<out N>): NodeRenderer<N>?
    fun mergeWith(other: NodeRendererRegistry): NodeRendererRegistry   // entries in `other` win
    class Builder {
        fun <N : UINode> register(nodeClass: KClass<N>, renderer: NodeRenderer<N>): Builder
        fun build(): NodeRendererRegistry
    }
    companion object { fun defaults(): NodeRendererRegistry }
}

/** Renders one child node through the registry, with visibility, diagnostics, and layout-parent handling. */
@Composable
fun RenderNode(node: UINode)
```

A `Builder` starts empty: merge it over `defaults()` to keep the built-in renderers. Custom renderers receive only the node; the built-in modifier mapping (including `weight`) is internal, so apply `node.modifier` yourself when you need it.

### Theme

```kotlin
@Composable
fun WithRenderedTheme(
    theme: UITheme?,
    fontResolver: FontResolver = FontResolver.Default,
    content: @Composable () -> Unit,
)
```

Wrap `SynapseRenderer` in it to apply a payload theme. A null theme leaves the host theme untouched; see [theme-reference.md](theme-reference.md) for how a non-null theme merges.

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

### Bridged surface (Swift Export and other non-Kotlin hosts)

A Swift Export host crashes when the bridge converts a map of arbitrary values across the
boundary, so payloads and collection records stay Kotlin references and are read lane by lane.
Kotlin engines keep using the raw maps; these types exist for the bridge.

```kotlin
// action/: payloads arriving in a host's handler
class ActionPayload internal constructor(/* wraps Map<String, Any?> */) {
    val keys: Set<String>
    fun getString(key: String): String?
    fun getLong(key: String): Long?          // absorbs Int
    fun getDouble(key: String): Double?      // absorbs Float
    fun getBoolean(key: String): Boolean?
    fun getStringList(key: String): List<String>?
    fun isNull(key: String): Boolean         // present but null
}
fun bridgedActionHandler(onAction: (actionId: String, payload: ActionPayload) -> Unit): ActionHandler

// engine/: collection rows and the lazy-binding pipeline
class DataRecordView internal constructor(/* wraps DataRecord */) {
    val keys: Set<String>
    fun getString(key: String): String?      // + getLong/getDouble/getBoolean/isNull as above
    fun describe(key: String): String?       // toString of whatever lane holds the value
}
class BoundRecords internal constructor(/* narrowed rows */) {
    val size: Int
    fun view(index: Int): DataRecordView     // record + 1-based "_index"
    fun stableId(index: Int): String         // record id, or position when absent
    fun groups(groupBy: String): BoundRecordGroups
}
class BoundRecordGroups internal constructor(/* first-encounter order */) {
    val size: Int
    fun key(index: Int): String
    fun records(index: Int): BoundRecords
    fun headerView(index: Int): DataRecordView   // "group.key" and "group.count"
}

/** Search-then-filter narrowing, the collection-bound lazy-node pipeline. */
fun narrowRecords(
    records: List<DataRecord>, searchText: String, searchFields: List<String>,
    filter: DataCondition?, fieldReader: (String) -> Any?,
): List<DataRecord>

/** String-first state reads for record filters (templates read long, double, string). */
fun RendererStateHolder.recordFieldReader(): (String) -> Any?

fun boundRecords(
    collectionProvider: CollectionProvider, stateHolder: RendererStateHolder, dataSource: String,
    filter: DataCondition? = null, searchKey: String? = null, searchFields: List<String> = emptyList(),
): BoundRecords

/** Fires synchronously with the current records, then on collection or search-text changes. */
fun watchBoundRecords(
    collectionProvider: CollectionProvider, stateHolder: RendererStateHolder, dataSource: String,
    filter: DataCondition? = null, searchKey: String? = null, searchFields: List<String> = emptyList(),
    onChange: (BoundRecords) -> Unit,
): WatchHandle

/** Dispatch with the record attached under "_itemContext", the Card-in-a-collection payload. */
fun ActionDispatcher.dispatchWithRecord(
    actionId: String, record: DataRecordView?, payload: Map<String, Any?> = emptyMap(),
)

// TemplateEngine members for record-held item context
fun resolveWithRecord(
    content: String, stateHolder: RendererStateHolder, record: DataRecordView?,
    collectionSize: ((String) -> Int)? = null,
): String
fun resolveNumericWithRecord(value: String, stateHolder: RendererStateHolder, record: DataRecordView?): Float

// Conditional text formats resolve Kotlin-side (the format map cannot cross the bridge)
fun effectiveTextFormat(node: UINode.TextNode, evaluator: ConditionEvaluator): UITextFormat?
fun hasConditionalFormat(node: UINode.TextNode): Boolean
```

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

A `type` this build does not know decodes to `UINode.Unknown`, which keeps what the payload sent:

```kotlin
data class Unknown(
    override val id: String? = null,
    override val modifier: UIModifier? = null,
    override val visibility: UIVisibility? = null,
    @Transient val typeName: String = "Unknown",   // e.g. "Hologram"; not serialised
) : UINode()
```

---

## Node semantics shared by every engine

```kotlin
// engine/
object RecordConditionEvaluator {
    fun matches(record: Map<String, Any?>, condition: DataCondition, fieldReader: ((String) -> Any?)? = null): Boolean
    /** matches over values read one field at a time, such as a data store's live fields. */
    fun matchesValues(valueOf: (String) -> Any?, condition: DataCondition, fieldReader: ((String) -> Any?)? = null): Boolean
}

/** The value a NumberField keeps once the user finishes editing: in range, on the step grid, at `decimals` precision. */
fun UINode.NumberField.committedValue(value: Double): Double
```

Node filters, computed fields' `where`, and the data layer's named conditions all answer field questions through `RecordConditionEvaluator`, so they agree; dates compare in the device's time zone (`isToday` is the user's calendar day).

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
    @Deprecated("Always 0: summarizeTree walks the schema without rendering it. Count onNodeRenderError reports instead.")
    val errorNodes: Int = 0,
)

/** Counts what an engine could draw, without rendering. Validates a payload before it ships. */
fun summarizeTree(root: UINode, isRegistered: (UINode) -> Boolean): RenderPassSummary

/** Every child of a node, across every slot that holds one. */
fun UINode.children(): List<UINode>
```

`path` is a slash-separated trail of node types from the root, such as
`Scaffold/Column/LazyColumn/Text`.

`onUnknownNode` receives the `type` the payload sent (`UINode.Unknown.typeName`), and the path ends
in it, for example `Column/Hologram`.

Implementations must not throw. `onNodeRenderError` means a node could not be rendered as its
payload describes. The SwiftUI engine reports any renderer that throws. The Compose engine cannot
catch an exception thrown while composing, so it reports what it checks before composing: a
modifier Compose refuses to build (negative padding, non-positive `aspectRatio`, `weight`, or
radial-gradient `radius`; the node draws without it), an unsupported currency (the node draws
nothing), and a `LazyGrid` with fewer than one column (drawn with one). An exception inside a
Compose renderer still propagates. `RenderPassSummary.errorNodes` is deprecated and always 0.

Hosts that cannot implement a Kotlin interface (Swift, notably: the bridge generates SAM
adapters only for single-method interfaces) build one from callbacks; errors arrive as messages:

```kotlin
fun callbackRenderDiagnostics(
    onUnknownNode: (nodeType: String, nodeId: String?, path: String) -> Unit = { _, _, _ -> },
    onUnregisteredNode: (nodeType: String, nodeId: String?, path: String) -> Unit = { _, _, _ -> },
    onNodeRenderError: (nodeType: String, nodeId: String?, path: String, message: String) -> Unit = { _, _, _, _ -> },
    onActionDispatched: (actionId: String, payloadKeys: Set<String>) -> Unit = { _, _ -> },
    onActionError: (actionId: String, message: String) -> Unit = { _, _ -> },
    onRenderPass: (summary: RenderPassSummary) -> Unit = { },
): RenderDiagnostics

/** onNodeRenderError for engines that hold the failure as text. */
fun RenderDiagnostics.reportNodeRenderError(nodeType: String, nodeId: String?, path: String, message: String)
```

---

## Node Type Catalog

Type-discriminated via `"type"` field. Unknown types decode to `UINode.Unknown`, which renders nothing and is reported through diagnostics under its original `type` (forward compatible).

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

Register rendered pages inside a feature's `EntryProviderScope<NavKey>.register(dispatcher)` block. When `config.dataSchema` is provided, a `ReactiveDataStore` and a `MutationExecutor` are created once per base route, the store answers state, collections, and conditions, and it persists through `config.dataPersistence` with the base route as its scope. The `mutation:` action prefix is intercepted and routed to the executor. Without a `dataSchema` the route has no collections: every `dataSource` binds to an empty list.

`UIScreen` is the payload as it arrives; nothing applies its `theme` or `data` on its own. Load its pages into the `SchemaStore` and pass the rest through the config:

```kotlin
val store = InMemorySchemaStore().apply { load(screen) }
renderedEntry(
    baseRoute = "onboarding",
    schemaStore = store,
    actionHandler = handler,
    navigationDispatcher = dispatcher,
    config = RenderedPageConfig(dataSchema = screen.data, dataPersistence = persistence, theme = screen.theme),
)
```

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
    val dataPersistence: DataPersistence = DataPersistence.NoOp,   // ignored without dataSchema
    val theme: UITheme? = null,
    val fontResolver: FontResolver = FontResolver.Default,
    val mediaProvider: MediaProvider = MediaProvider.NoOp,
    val diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,
)
```

`stateHolder` and `conditionEvaluator` are ignored when `dataSchema` is set: the `ReactiveDataStore` takes over both roles.

**Built-in action prefixes:**
- `renderer:navigate:<pageId>`: navigates to another rendered page
- `renderer:back`: pops the back stack
- `mutation:<name>`: executes a declared data mutation

---

## Detailed Reference

- [Node Types](nodes-reference.md): all node fields, base fields, data-bound extensions
- [Modifiers & Enums](modifier-enums.md): UIModifier, UIDimension, UIGradient, all enums
- [Data Layer](data-layer.md): DataSchema, fields, collections, mutations, conditions, runtime classes
- [Theme](theme-reference.md): UITheme, colors, typography, spacing, shape
- [Examples](examples.md): JSON examples for all features
