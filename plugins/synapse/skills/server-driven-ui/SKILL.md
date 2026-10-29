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
| `com.ribads.synapse.ui.renderer.action` | `ActionDispatcher`, `ActionHandler`, `ActionPayload`, `OperationHandler`, `OperationOutcome`, `bridgedActionHandler`, `onAction` |
| `com.ribads.synapse.ui.renderer.capability` | `IncompatibilityReason`, `RendererCapabilities`, `SchemaElementKind`, `ScreenCompatibility`, `SynapseSchemaVersion`, `compatibilityWith` |
| `com.ribads.synapse.ui.renderer.data` | `CollectionChange`, `DataChanges`, `DataPersistence`, `MutationExecutor`, `MutationResult`, `OperationExecutor`, `PageOperations`, `ReactiveDataStore`, `renderedPageActionHandler` |
| `com.ribads.synapse.ui.renderer.diagnostics` | `RenderDiagnostics`, `RenderPassSummary`, `callbackRenderDiagnostics`, `children`, `reportNodeRenderError`, `summarizeTree` |
| `com.ribads.synapse.ui.renderer.engine` | `BoundRecordGroups`, `BoundRecords`, `CollectionProvider`, `CompiledCondition`, `CompiledTemplate`, `ConditionEvaluator`, `DataRecord`, `DataRecordView`, `ITEM_CONTEXT_PAYLOAD_KEY`, `MediaProvider`, `NodeRenderer`, `NodeRendererRegistry`, `RecordConditionEvaluator`, `RenderNode`, `RendererClock`, `SynapseRenderer`, `TemplateEngine`, `boundRecords`, `committedValue`, `compile`, `dispatchWithRecord`, `effectiveTextFormat`, `hasConditionalFormat`, `narrowRecords`, `recordFieldReader`, `rowKeys`, `watchBoundRecords`, `watchCondition`, `watchEffectiveTextFormat`, `watchTemplateInputs` |
| `com.ribads.synapse.ui.renderer.navigation` | `InMemorySchemaStore`, `PersistedState`, `PersistentRendererStateHolder`, `RenderedPageAction`, `RenderedPageConfig`, `RenderedPageKey`, `RenderedRoutesBuilder`, `SchemaStore`, `ScreenNavigationHost`, `ScreenNavigationState`, `ScreenNavigator`, `ScreenParseResult`, `ScreenRequirements`, `StatePersistence`, `UINavigationTab`, `UIPage`, `UIScreen`, `UIScreenNavigation`, `load`, `navigateToRenderedPage`, `parseUIScreen`, `rememberScreenNavigator`, `renderedEntries`, `renderedEntry`, `rendererNavigationSerializers`, `toUIScreen`, `uiScreenJsonSchema` |
| `com.ribads.synapse.ui.renderer.schema` | `ComputedField`, `DataCollection`, `DataCondition`, `DataEffect`, `DataField`, `DataFieldType`, `DataMutation`, `DataOperation`, `DataOperationResult`, `DataOrderBy`, `DataSchema`, `DataValueRef`, `OperationConcurrency`, `SchemaParseResult`, `SortDirection`, `UIButtonState`, `UIDimension`, `UIGradient`, `UIModifier`, `UINavBarAction`, `UINavBarLeadingIcon`, `UINode`, `UITextFormat`, `UITextIntent`, `UITheme`, `UIThemeBorder`, `UIThemeColors`, `UIThemeCorners`, `UIThemeElement`, `UIThemeElementInteractive`, `UIThemeIntentPalette`, `UIThemeIntents`, `UIThemeNeutral`, `UIThemeShadow`, `UIThemeShape`, `UIThemeSpacing`, `UIThemeSurface`, `UIThemeSurfaceInteractive`, `UIThemeTextStyle`, `UIThemeTypography`, `UIVisibility`, `containsUnsupported`, `parseUINode`, `schemaType`, `toUINode`, `toUINodes`, `uiNodeJsonSchema` |
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

    /**
     * Advances when [key]'s value changes, when its lane is created, and on clear. Observing it
     * never creates the key. The default, [revision], is correct but wakes every reader.
     */
    fun revisionOf(key: String): StateFlow<Long> = revision

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

### Persisted state without a data schema

`PersistentRendererStateHolder` (module `ui:renderer-data`) is a `RendererStateHolder` over a
`StatePersistence` backend. It hydrates on construction, then writes the latest value of each
changed key in the background, at most one batch per 250 ms, one call at a time, so a
`StatePersistence` may block on I/O but must not throw.

```kotlin
class PersistentRendererStateHolder(
    persistence: StatePersistence,
    scope: String,
    diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,   // receives onPersistenceError
) : RendererStateHolder {
    suspend fun flush()   // writes what is unsaved; returns once written or failed
    fun close()           // starts writing what is unsaved
}

interface StatePersistence {
    fun putString(scope: String, key: String, value: String)
    fun putLong(scope: String, key: String, value: Long?)
    fun putDouble(scope: String, key: String, value: Double?)
    fun putBoolean(scope: String, key: String, value: Boolean)
    fun loadAll(scope: String): PersistedState
    fun clear(scope: String)
}

@Serializable
data class PersistedState(
    val strings: Map<String, String> = emptyMap(),
    val longs: Map<String, Long?> = emptyMap(),
    val doubles: Map<String, Double?> = emptyMap(),
    val booleans: Map<String, Boolean> = emptyMap(),
)
```

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
    fun stableId(index: Int): String         // rowKeys(records)[index]
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
    filter: CompiledCondition?, fieldReader: (String) -> Any?,
): List<DataRecord>

/** One key per record, unique within [records]: its id, `@<index>` without one, `#2`, `#3`... appended to repeats. */
fun rowKeys(records: List<DataRecord>): List<String>

/** A condition prepared once for repeated evaluation, with what its answer depends on. */
class CompiledCondition internal constructor(/* parsed predicate */) {
    val fields: Set<String>        // read from the value tested: a record's or the model's fields
    val fieldRefs: Set<String>     // read through the field reader: an equals' fieldRef
    val collections: Set<String>   // collections whose size it asks about
    val readsClock: Boolean        // the answer moves with time: now, dateWithin, isToday
    // Without collectionSize, collection questions are false.
    fun matches(valueOf: (String) -> Any?, fieldReader: ((String) -> Any?)? = null, collectionSize: ((String) -> Int)? = null): Boolean
    // Reads the clock once for every record.
    fun filter(records: List<DataRecord>, fieldReader: ((String) -> Any?)? = null): List<DataRecord>
}
fun DataCondition.compile(): CompiledCondition

/** String-first state reads for record filters (templates read long, double, string). */
fun RendererStateHolder.recordFieldReader(): (String) -> Any?

fun boundRecords(
    collectionProvider: CollectionProvider, stateHolder: RendererStateHolder, dataSource: String,
    filter: DataCondition? = null, searchKey: String? = null, searchFields: List<String> = emptyList(),
): BoundRecords

/**
 * Fires synchronously with the current records, then when the collection, the search text, a
 * field the filter compares against, or, for a time-relative filter, the minute changes.
 */
fun watchBoundRecords(
    collectionProvider: CollectionProvider, stateHolder: RendererStateHolder, dataSource: String,
    filter: DataCondition? = null, searchKey: String? = null, searchFields: List<String> = emptyList(),
    onChange: (BoundRecords) -> Unit,
): WatchHandle

/** Dispatch with the record attached under "_itemContext", the Card-in-a-collection payload. */
fun ActionDispatcher.dispatchWithRecord(
    actionId: String, record: DataRecordView?, payload: Map<String, Any?> = emptyMap(),
)

// A template parsed once, with the keys it reads: TemplateEngine.compile(content)
class CompiledTemplate internal constructor(/* segments */) {
    val source: String
    val isLiteral: Boolean                                    // no slots: resolve returns source
    fun stateKeys(readsRecord: Boolean): Set<String>          // state keys its slots read
    fun countedCollections(readsRecord: Boolean): Set<String> // collections its `.count` slots read
    fun resolve(stateHolder: RendererStateHolder, itemContext: Map<String, Any?>? = null, collectionSize: ((String) -> Int)? = null): String
    fun resolveWithRecord(stateHolder: RendererStateHolder, record: DataRecordView?, collectionProvider: CollectionProvider): String
}

/**
 * Runs [onChange] each time a state key or a counted collection's size that [template] reads
 * changes, never for anything else, and not for the current values. With [readsRecord],
 * `item.` slots read the host's record and are not watched.
 */
fun watchTemplateInputs(
    template: CompiledTemplate, stateHolder: RendererStateHolder, collectionProvider: CollectionProvider,
    readsRecord: Boolean, onChange: () -> Unit,
): WatchHandle

/** Fires with the current answer, then each time it changes. */
fun ConditionEvaluator.watchCondition(conditionKey: String, onChange: (Boolean) -> Unit): WatchHandle

/** Fires with the current effective format, then only when it changes. */
fun watchEffectiveTextFormat(node: UINode.TextNode, evaluator: ConditionEvaluator, onChange: (UITextFormat?) -> Unit): WatchHandle

/** The time source of time-relative conditions: one tick at each wall-clock minute, on the main thread. */
object RendererClock {
    fun nowMillis(): Long
    fun minuteTicks(): Flow<Long>
}

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

An unknown `type` inside the data layer does not fail the parse either. `DataCondition`, `ComputedField`, `DataMutation`, `DataEffect` and `DataValueRef` each decode it to their `Unsupported` variant, which keeps the original `typeName` (see [data-layer.md](data-layer.md#unsupported-types) for what each does at runtime):

```kotlin
data class Unsupported(@Transient val typeName: String = "unsupported")   // in each of the five types

/** True when this condition, or any operand beneath it, is DataCondition.Unsupported. */
fun DataCondition.containsUnsupported(): Boolean
```

A `type` this build does not know decodes to `UINode.Unknown`, which keeps what the payload sent:

```kotlin
data class Unknown(
    override val id: String? = null,
    override val modifier: UIModifier? = null,
    override val visibility: UIVisibility? = null,
    @Transient val typeName: String = "Unknown",   // e.g. "Hologram"; not serialised
) : UINode()
```

## JSON Schema for generators

```kotlin
/** Draft 2020-12 JSON Schema for one node payload. */
fun uiNodeJsonSchema(): String           // com.ribads.synapse.ui.renderer.schema

/** Draft 2020-12 JSON Schema for a screen payload. */
fun uiScreenJsonSchema(): String         // com.ribads.synapse.ui.renderer.navigation
```

Both are generated from the serializers, so they always match the library version in use. Use them to validate generated payloads, or to constrain an LLM's output (Gemini, XGrammar in vLLM/SGLang, llguidance). Snapshots for non-Kotlin pipelines are checked in at `ui/renderer-core/json-schema/ui-node.schema.json` and `ui-screen.schema.json`.

- Every named type sits under `$defs`, recursion goes through `$ref` (`UINode.children`, `DataCondition` `and`/`or`/`not`), and each union is an `anyOf` of variants that pin `type` with `const`.
- **Stricter than the parser**: every object sets `additionalProperties: false`, enums are exact, and the `Unknown` and `Unsupported` fallbacks are left out. A payload the renderer draws can still fail validation, for example one with a misspelt enum that `coerceInputValues` quietly drops.
- **Structural only**: no `description`s and no defaults. A property is optional exactly when its Kotlin parameter has a default.
- It does not check meaning: that an `actionId` has a handler, that a data reference resolves, or that a `{{template}}` is well formed.
- Recursive schemas are outside some providers' structured-output support (Claude's included); validate and repair instead there.

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

## Operations

Operations are how a schema reaches the network. The schema names an operation and declares what goes in and where the result goes; the host decides how it runs. The renderer never makes a network call itself, and a payload can never point the app's client at an arbitrary host.

```kotlin
// action package
fun interface OperationHandler {
    suspend fun execute(name: String, input: ActionPayload): OperationOutcome   // never throw
}

sealed class OperationOutcome {
    data class Success(val records: List<DataRecord> = emptyList()) : OperationOutcome()
    data class Failure(val code: String) : OperationOutcome() {
        companion object { const val UNEXPECTED: String; const val UNSUPPORTED: String }   // "unexpected", "unsupported"
    }
}

class ActionPayload(values: Map<String, Any?>) {
    // getString / getLong / getDouble / getBoolean / getStringList / isNull, as above
    fun toJsonObject(): JsonObject                                  // every value, for forwarding to a server
}
```

- `Success.records` are flat maps of primitives (JSON primitives or Kotlin values). They are coerced to the target collection's declared types; give every field a type in the collection's `schema`, or it arrives as a string.
- `Failure.code` is a machine code such as `offline` or `unauthorized`, written to the operation's `failureField`. The schema chooses the copy with an `equals` condition; never put user-facing text in a code.
- Never throw from `execute`: an exception escaping into a Swift Export host crashes the app. A throw from a Kotlin handler is contained, reported through `RenderDiagnostics.onActionError("operation:<name>", …)`, and treated as `Failure(UNEXPECTED)`.

Bind operations in the feature's `ui` module and call the feature's use cases from there, so `/synapse:data-boundaries` still holds: operation → use case → repository → network. To add operations without an app release, implement one gateway handler that forwards every name to your backend (see [examples.md](examples.md#gateway-operation-handler)), and keep native bindings for things like purchase and restore.

Runtime (data package, see [data-layer.md](data-layer.md#operationexecutor)):

```kotlin
class OperationExecutor(store: ReactiveDataStore, handler: OperationHandler, diagnostics: RenderDiagnostics) {
    suspend fun execute(name: String, itemContext: DataRecord? = null): MutationResult   // throws only CancellationException
}

class PageOperations(executor: OperationExecutor) {
    fun launch(name: String, itemContext: DataRecord?, onSettled: (MutationResult) -> Unit)
    fun cancel()
}

fun renderedPageActionHandler(
    fallback: ActionHandler,
    mutationExecutor: MutationExecutor?,
    operations: PageOperations? = null,      // null: operation: actions are ignored
    navigateToPage: (pageId: String) -> Unit,
    navigateBack: () -> Unit,
): ActionHandler
```

Hosts using `renderedEntries` only set `RenderedPageConfig.operationHandler`. A custom host creates one `PageOperations` per page, passes it to `renderedPageActionHandler`, and calls `cancel()` when the page leaves the screen.

---

## Capabilities and compatibility

Package `com.ribads.synapse.ui.renderer.capability`. The client sends what it can run with every screen request; the server only returns screens that fit, and the client can check a screen before rendering it.

```kotlin
object SynapseSchemaVersion { const val CURRENT: Int }      // 3; see the version table in SCHEMA.md

class RendererCapabilities(val operations: Set<String> = emptySet()) {   // names bound natively; no blanks or commas
    val schemaVersion: Int
    val schemaVersionHeaderValue: String
    val operationsHeaderValue: String                       // sorted, comma-separated
    companion object {
        const val SCHEMA_VERSION_HEADER: String             // "X-Synapse-Schema-Version"
        const val OPERATIONS_HEADER: String                 // "X-Synapse-Operations"
    }
}

// navigation package, on the payload
@Serializable
data class ScreenRequirements(val minSchemaVersion: Int = 1, val operations: List<String> = emptyList())
// UIScreen gains: val requires: ScreenRequirements? = null

fun UIScreen.compatibilityWith(capabilities: RendererCapabilities): ScreenCompatibility

sealed class ScreenCompatibility {
    data object Compatible : ScreenCompatibility()
    data class Incompatible(val reasons: List<IncompatibilityReason>) : ScreenCompatibility()
}

sealed class IncompatibilityReason {
    data class SchemaVersionTooNew(val required: Int, val supported: Int) : IncompatibilityReason()
    data class OperationNotBound(val name: String) : IncompatibilityReason()
    data class UnsupportedSchemaElement(val kind: SchemaElementKind, val typeName: String) : IncompatibilityReason()
}

enum class SchemaElementKind { Condition, ComputedField, Mutation, Effect, ValueRef, OperationResult }
```

Attach both headers to the request that fetches screens (from the host's data layer; the renderer makes no network calls). Clients from 0.2.0-alpha9 and earlier send no headers and ignore `requires`, so a server must gate newer screens on the header, not on `requires` alone. Unknown nodes never make a screen incompatible: they render nothing by design.

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
    /** A background save to [scope]'s persistence failed; it is retried with the next change. */
    fun onPersistenceError(scope: String, error: Throwable) {}
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
    onPersistenceError: (scope: String, message: String) -> Unit = { _, _ -> },
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
| **Meta** | `Conditional`, `OnAppear`, `Unknown` |

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
    val requires: ScreenRequirements? = null,
    val navigation: UIScreenNavigation? = null,
) {
    val entryPage: String?                       // startPage, else the first tab's page, else the first page
    fun resolvedTabs(): List<UINavigationTab>    // tabs whose page exists, each page once
}

@Serializable
data class UIPage(val id: String, val root: UINode)

@Serializable
data class UIScreenNavigation(val tabs: List<UINavigationTab> = emptyList())

@Serializable
data class UINavigationTab(val page: String, val label: String, val icon: UIIcon? = null)

fun String.toUIScreen(): UIScreen
```

### Screen tabs

A screen's top-level destinations are declared once, in `navigation.tabs`; pages never draw a tab bar themselves. The renderer keeps one stack of pages per tab, so switching tabs keeps each tab where the user left it.

```json
{
  "navigation": { "tabs": [
    { "page": "trip", "label": "Trip", "icon": "map" },
    { "page": "budget", "label": "Budget", "icon": "payments" }
  ] },
  "pages": [ ... ]
}
```

- `renderer:navigate:<page>` opens the page on top of the tab showing; naming a tab's root page selects that tab at its root. Opening the page already showing does nothing.
- Selecting the tab showing returns it to its root.
- Back closes the page showing, then returns to the first tab from another tab's root, then leaves the screen.
- A start page that is not a tab root (onboarding, say) shows without the bar until the user enters a tab.

Every host navigates through the same pure model, `ScreenNavigationState` (in `ui:renderer-core`). Compose hosts draw it with `ScreenNavigationHost` (in `ui:renderer`):

```kotlin
val navigator = rememberScreenNavigator(screen.entryPage!!, screen.resolvedTabs())
WithRenderedTheme(theme = screen.theme) {
    ScreenNavigationHost(navigator) { pageId -> /* SynapseRenderer for pageId */ }
}
// renderer:navigate: -> navigator.navigate(pageId); renderer:back -> if (!navigator.back()) leaveTheScreen()
```

`ScreenNavigationHost` draws the design system's `BottomNavigationBar` inside its `Scaffold`, keeps every open page's saved state while another tab shows, moves pages with the platform's navigation motion, and handles system back in the order above.

SwiftUI hosts use the SwiftUI engine's `ScreenNavigator` and `ScreenNavigationHost`, which draw the same model as a system `TabView` over one `NavigationStack` per tab:

```swift
@StateObject var navigator = ScreenNavigator(entryPage: screen.entryPage!, tabs: screen.resolvedTabs())
ScreenNavigationHost(navigator: navigator) { pageId in /* SynapseRendererView for pageId */ }
// renderer:navigate: -> navigator.navigate(pageId); renderer:back -> if !navigator.back() { leaveTheScreen() }
```

Tabs need schema version 3; servers should send tabbed screens only to clients that report it.

### renderedEntries / renderedEntry

Server-driven pages are addressed by a single typed key carrying the dynamic page id as data, so they fit Navigation 3's typed entry provider:

```kotlin
@Serializable
data class RenderedPageKey(val baseRoute: String, val pageId: String) : NavKey

// Fold into a feature's FeatureLauncher.serializers so rendered pages survive saved state on iOS/web:
val rendererNavigationSerializers: SerializersModule
```

Register rendered pages inside a feature's `EntryProviderScope<NavKey>.register(dispatcher)` block. When `config.dataSchema` is provided, one `ReactiveDataStore` serves every page of the base route: it answers state, collections, and conditions, and it persists through `config.dataPersistence` with the base route as its scope. The `mutation:` action prefix is intercepted and routed to it. Without a `dataSchema` the route has no collections: every `dataSource` binds to an empty list.

The store is built when one of the route's pages is first shown and kept in the enclosing `NavContainer`'s ViewModel store (`LocalNavContainerViewModelStoreOwner`), so it survives configuration changes and a rebuilt entry provider, and it is closed when that ViewModel store is cleared. Its changes are written in the background and whenever the page stops. A different `dataSchema` (compared by value), `dataPersistence` or `stateHolder` (by identity) replaces the store, once the old one's unsaved changes are written, so keep one persistence instance per backend. Outside a `NavContainer` the store lives as long as the registration that built it, so an entry provider rebuilt within the save window can hydrate a new store without the last change.

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
    val stateHolder: RendererStateHolder? = null,                 // null: an in-memory holder kept with the route's data
    val dataSchema: DataSchema? = null,
    val dataPersistence: DataPersistence = DataPersistence.NoOp,   // ignored without dataSchema
    val theme: UITheme? = null,
    val fontResolver: FontResolver = FontResolver.Default,
    val mediaProvider: MediaProvider = MediaProvider.NoOp,
    val diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,   // failed saves go to the store's first one
    val operationHandler: OperationHandler? = null,             // ignored without dataSchema
    val navigation: UIScreenNavigation? = null,                  // tabs: the screen runs inside one entry
)
```

`stateHolder` and `conditionEvaluator` are ignored when `dataSchema` is set: the `ReactiveDataStore` takes over both roles.

A route without tabs registers each page as its own Nav3 entry. A route whose `navigation` has tabs is one entry holding the whole screen through `ScreenNavigationHost`; navigation between its pages stays inside that entry, and back pops the entry only once there is nowhere to go back to within the screen.

Each rendered page gets its own `PageOperations`, cancelled when the page leaves composition, including an Android configuration change (the route's store itself survives it). An operation the user walked away from never applies its effects, so make submits idempotent on the server. A page under a bottom sheet or dialog stays composed, so its operations keep running.

**Built-in action prefixes:**
- `renderer:navigate:<pageId>`: navigates to another rendered page
- `renderer:back`: pops the back stack
- `mutation:<name>`: executes a declared data mutation
- `operation:<name>`: launches a declared data operation through `RenderedPageConfig.operationHandler`

`RenderedPageAction` (navigation package) holds these as constants: `NAVIGATE_PREFIX`, `BACK`, `MUTATION_PREFIX`, `OPERATION_PREFIX`, with builders `navigateTo(pageId)`, `mutation(name)`, `operation(name)`.

---

## Detailed Reference

- [Node Types](nodes-reference.md): all node fields, base fields, data-bound extensions
- [Modifiers & Enums](modifier-enums.md): UIModifier, UIDimension, UIGradient, all enums
- [Data Layer](data-layer.md): DataSchema, fields, collections, mutations, conditions, runtime classes
- [Theme](theme-reference.md): UITheme, colors, typography, spacing, shape
- [Examples](examples.md): JSON examples for all features
