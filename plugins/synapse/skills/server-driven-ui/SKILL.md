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
| `com.ribads.synapse.ui.renderer.data` | `CollectionChange`, `DataChanges`, `DataPersistence`, `MutationExecutor`, `MutationResult`, `OperationExecutor`, `PageDestination`, `PageOperations`, `ReactiveDataStore`, `renderedPageActionHandler` |
| `com.ribads.synapse.ui.renderer.diagnostics` | `RenderDiagnostics`, `RenderPassSummary`, `callbackRenderDiagnostics`, `children`, `reportNodeRenderError`, `summarizeTree` |
| `com.ribads.synapse.ui.renderer.engine` | `BoundRecordGroups`, `BoundRecords`, `CollectionProvider`, `CompiledCondition`, `CompiledTemplate`, `ConditionEvaluator`, `DataRecord`, `DataRecordView`, `ITEM_COLLECTION_KEY`, `ITEM_CONTEXT_PAYLOAD_KEY`, `MediaProvider`, `NodeRenderer`, `NodeRendererRegistry`, `PageRecord`, `RecordConditionEvaluator`, `RecordFieldKey`, `RecordId`, `RecordSource`, `RenderNode`, `RendererCalendar`, `RendererClock`, `SynapseRenderer`, `TemplateEngine`, `boundRecords`, `committedValue`, `compile`, `currentRecord`, `dispatchWithRecord`, `effectiveTextFormat`, `hasConditionalFormat`, `inCollection`, `inRow`, `narrowRecords`, `pageAwareFieldReader`, `recordFieldReader`, `rowKeys`, `watchBoundRecords`, `watchCondition`, `watchEffectiveTextFormat`, `watchPageRecord`, `watchTemplateInputs` |
| `com.ribads.synapse.ui.renderer.navigation` | `InMemorySchemaStore`, `PersistedState`, `PersistentRendererStateHolder`, `RenderedPageAction`, `RenderedPageConfig`, `RenderedPageKey`, `RenderedRoutesBuilder`, `SchemaStore`, `ScreenNavigationHost`, `ScreenNavigationState`, `ScreenNavigator`, `ScreenParseResult`, `ScreenRequirements`, `StatePersistence`, `UINavigationTab`, `UIPage`, `UIScreen`, `UIScreenNavigation`, `load`, `navigateToRenderedPage`, `parseUIScreen`, `rememberScreenNavigator`, `renderedEntries`, `renderedEntry`, `rendererNavigationSerializers`, `toUIScreen`, `uiScreenJsonSchema` |
| `com.ribads.synapse.ui.renderer.schema` | `CalendarUnit`, `ComputedField`, `DataCollection`, `DataCondition`, `DataEffect`, `DataField`, `DataFieldType`, `DataMutation`, `DataOperation`, `DataOperationResult`, `DataOrderBy`, `DataSchema`, `DataValueRef`, `OperationConcurrency`, `RecordComputed`, `SchemaParseResult`, `SortDirection`, `UIButtonState`, `UIDimension`, `UIGradient`, `UIModifier`, `UINavBarAction`, `UINavBarLeadingIcon`, `UINode`, `UITextFormat`, `UITextIntent`, `UITheme`, `UIThemeBorder`, `UIThemeColors`, `UIThemeCorners`, `UIThemeElement`, `UIThemeElementInteractive`, `UIThemeIntentPalette`, `UIThemeIntents`, `UIThemeNeutral`, `UIThemeShadow`, `UIThemeShape`, `UIThemeSpacing`, `UIThemeSurface`, `UIThemeSurfaceInteractive`, `UIThemeTextStyle`, `UIThemeTypography`, `UIVisibility`, `containsUnsupported`, `parseUINode`, `schemaType`, `toUINode`, `toUINodes`, `uiNodeJsonSchema` |
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

// A page of a screen, opened on the record its navigation entry names.
@Composable
fun SynapseRenderer(
    page: UIPage,
    record: RecordId?,
    actionHandler: ActionHandler,
    stateHolder: RendererStateHolder = remember { RendererStateHolder() },
    registry: NodeRendererRegistry = remember { NodeRendererRegistry.defaults() },
    conditionEvaluator: ConditionEvaluator = ConditionEvaluator.AlwaysFalse,
    collectionProvider: CollectionProvider = CollectionProvider.Empty,
    mediaProvider: MediaProvider = MediaProvider.NoOp,
    diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,
)
```

Render a screen's pages with the `page` overload:

- A page with a `record` collection draws its `root` while `collectionProvider` holds a record of that collection whose `id` is `record`, and its `whenMissing`, or nothing, while it does not: no `record`, or the record was deleted. It follows the record as the collection changes. A page without `record` draws its `root` and ignores `record`.
- `record.<field>` reads that record in templates, every `bind`, `ListItem.check`, `amountKey` and `iconField`, `MoneyText.bind`, a list `filter`'s `fieldRef`, and named conditions and conditional text formats (asked through `conditionFlow(key, record)`), inside list rows too, where `item.<field>` keeps meaning the row.
- An input bound to `item.<field>` or `record.<field>` shows that record's value, or its initial value, never written, while the record holds none. Each change shows at once and dispatches `renderer:setItemField:<field>` with the record under `_itemContext` and the value under `RenderedPageAction.VALUE_PAYLOAD_KEY`, and the input follows the record when it changes elsewhere. A record bind never creates a state field; without a record it shows its default and dispatches nothing.
- A render pass is reported for both `root` and `whenMissing`.
- Build the page's handler with `renderedPageActionHandler(..., pageRecord = page.recordOf(record), ...)`, so its mutations, operations and navigation see the same record.

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
    // The answer on a page showing record, for a condition reading record.<field>; those read nothing without one.
    fun conditionFlow(conditionKey: String, record: PageRecord?): StateFlow<Boolean> = conditionFlow(conditionKey)
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
`StatePersistence` may block on I/O. A write that fails should throw: it is reported through
`onPersistenceError` and the same values are offered again with the next save.

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

// Item contexts, the record a dispatch carries: a row's adds "_index" and "_collection", a page's "_collection" alone.
const val ITEM_COLLECTION_KEY = "_collection"
fun DataRecord.inRow(collection: String, index: Int): DataRecord
fun DataRecord.inCollection(collection: String): DataRecord

/** The id of the record a page shows. Saved as {"type":"long","value":5} or {"type":"string","value":"b1"}. */
@Serializable
sealed class RecordId {
    abstract fun matches(id: Any?): Boolean      // Whole: a Long, Int, Short or Byte of equal value; Text: equal text
    data class Whole(val value: Long) : RecordId()
    data class Text(val value: String) : RecordId()
    companion object {
        fun of(id: Any?): RecordId?              // text or a whole number; a Double, a Boolean or null is no id
    }
}

/** The record a page shows: the one of [collection] whose `id` is [id]. */
data class PageRecord(val collection: String, val id: RecordId)

/**
 * Fires with the record before it returns, then each time that record changes, and with null
 * while its collection holds none. A change to another record of the collection does not fire it.
 * The view carries "_collection", so dispatchWithRecord with it reaches the record as a row's does.
 */
fun watchPageRecord(collectionProvider: CollectionProvider, record: PageRecord, onChange: (DataRecordView?) -> Unit): WatchHandle

/** The record as its page reads it: the one its collection holds now, with its "_collection"; null while it holds none. */
fun CollectionProvider.currentRecord(record: PageRecord): DataRecord?

/** A key naming a record field: "item.<field>" of the row's record, "record.<field>" of the page's. */
data class RecordFieldKey(val source: RecordSource, val field: String) {
    companion object {
        const val ITEM_PREFIX = "item."
        const val RECORD_PREFIX = "record."
        fun parse(key: String): RecordFieldKey?  // null for a data field
    }
}
enum class RecordSource { Item, Page }

/** Reads "record.<field>" from pageRecord, nothing without one, and every other key through fields. */
fun pageAwareFieldReader(pageRecord: DataRecord?, fields: (String) -> Any?): (String) -> Any?

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
    val fieldRefs: Set<String>     // read through the field reader: an equals' fieldRef, inside an exists too
    val collections: Set<String>   // collections it asks about: emptiness, or a record an exists' where keeps
    val collectionFields: Map<String, Set<String>>  // per collection asked about, the record fields an exists' where tests; none for emptiness
    val readsClock: Boolean        // the answer moves with time: now, dateWithin, dateInLast, dateInPeriod, isToday
    val readsPageRecord: Boolean   // a field or fieldRef names record.<field>, an exists' fieldRefs included
    // Without collectionRecords, collection questions (collectionEmpty, collectionNotEmpty, exists) are false.
    fun matches(
        valueOf: (String) -> Any?,
        fieldReader: ((String) -> Any?)? = null,
        collectionRecords: ((String) -> List<DataRecord>)? = null,
    ): Boolean
    // Reads the clock once for every record.
    fun filter(records: List<DataRecord>, fieldReader: ((String) -> Any?)? = null): List<DataRecord>
}
fun DataCondition.compile(): CompiledCondition

/** String-first state reads for record filters (templates read long, double, string). */
fun RendererStateHolder.recordFieldReader(): (String) -> Any?

/** A filter's "record.<field>" fieldRefs compare against pageRecord, the record the node's page shows. */
fun boundRecords(
    collectionProvider: CollectionProvider, stateHolder: RendererStateHolder, dataSource: String,
    filter: DataCondition? = null, searchKey: String? = null, searchFields: List<String> = emptyList(),
    pageRecord: DataRecordView? = null,
): BoundRecords

/**
 * Fires synchronously with the current records, then each time they change. They are narrowed
 * again when the collection, the search text, a field the filter compares against, the page record
 * a "record.<field>" fieldRef reads, or, for a time-relative filter, the minute changes; narrowing
 * to the records already shown fires nothing. pageRecord's collection is followed only while the
 * filter reads it, and a "record." fieldRef is never watched as a data field.
 */
fun watchBoundRecords(
    collectionProvider: CollectionProvider, stateHolder: RendererStateHolder, dataSource: String,
    filter: DataCondition? = null, searchKey: String? = null, searchFields: List<String> = emptyList(),
    pageRecord: PageRecord? = null,
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
    val readsClock: Boolean                                   // {{now}} or a relative pipe: the text moves with time
    val readsPageRecord: Boolean                              // a {{record.<field>}} slot reads the page's record
    fun stateKeys(readsRecord: Boolean): Set<String>          // state keys its slots read; never a record. slot
    fun countedCollections(readsRecord: Boolean): Set<String> // collections its `.count` slots read
    // A record. slot reads pageRecord, and is empty without one.
    fun resolve(
        stateHolder: RendererStateHolder, itemContext: Map<String, Any?>? = null, pageRecord: DataRecord? = null,
        collectionSize: ((String) -> Int)? = null,
    ): String
    fun resolveWithRecord(
        stateHolder: RendererStateHolder, record: DataRecordView?, collectionProvider: CollectionProvider,
        pageRecord: DataRecordView? = null,
    ): String
}

/**
 * Runs [onChange] each time a state key or a counted collection's size that [template] reads
 * changes, and at each minute boundary while it reads the clock; never for anything else, and
 * not for the current values. With [readsRecord], `item.` slots read the host's record and are
 * not watched; `record.` slots read the page's record and are never watched.
 */
fun watchTemplateInputs(
    template: CompiledTemplate, stateHolder: RendererStateHolder, collectionProvider: CollectionProvider,
    readsRecord: Boolean, onChange: () -> Unit,
): WatchHandle

/** Fires with the current answer on a page showing record, then each time it changes. */
fun ConditionEvaluator.watchCondition(conditionKey: String, record: PageRecord?, onChange: (Boolean) -> Unit): WatchHandle

/** Fires with the current effective format on a page showing record, then only when it changes. */
fun watchEffectiveTextFormat(
    node: UINode.TextNode, evaluator: ConditionEvaluator, record: PageRecord?, onChange: (UITextFormat?) -> Unit,
): WatchHandle

/** The time source of time-relative conditions and templates. */
object RendererClock {
    fun nowMillis(): Long
    // The time at each wall-clock minute, on the main thread. One shared ticker, running only while collected.
    val minutes: Flow<Long>
}

/**
 * The one calendar conditions, templates and value refs read. Times are epoch milliseconds; days,
 * weeks (from Monday), months and years are the device's time zone's. Calendar units keep the
 * wall-clock time across a daylight saving change, hours and minutes are elapsed time, and a month
 * after 31 January is the last day of February. A result epoch milliseconds cannot hold is null.
 */
object RendererCalendar {
    fun timeOf(value: Any?): Long?                             // a number, or text holding a whole number
    fun daysBetween(fromMillis: Long, toMillis: Long): Long    // calendar days: 1 when toMillis falls on the next day
    fun startOf(timeMillis: Long, unit: CalendarUnit): Long?
    fun shift(
        timeMillis: Long, years: Int = 0, months: Int = 0, weeks: Int = 0, days: Int = 0, hours: Int = 0, minutes: Int = 0,
    ): Long?
    // In the period offset periods from the one holding nowMillis: 0 that one, -1 the one before.
    fun isInPeriod(timeMillis: Long, period: CalendarUnit, offset: Int, nowMillis: Long): Boolean
}

// TemplateEngine members for record-held item context and page record
fun resolveWithRecord(
    content: String, stateHolder: RendererStateHolder, record: DataRecordView?,
    pageRecord: DataRecordView? = null, collectionSize: ((String) -> Int)? = null,
): String
fun resolveNumericWithRecord(value: String, stateHolder: RendererStateHolder, record: DataRecordView?): Float

// Conditional text formats resolve Kotlin-side (the format map cannot cross the bridge)
fun effectiveTextFormat(node: UINode.TextNode, evaluator: ConditionEvaluator, record: PageRecord?): UITextFormat?
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

An unknown `type` inside the data layer does not fail the parse either. `DataCondition`, `ComputedField`, `RecordComputed`, `DataMutation`, `DataEffect`, `DataValueRef` and `DataOperationResult` each decode it to their `Unsupported` variant, which keeps the original `typeName` (see [data-layer.md](data-layer.md#unsupported-types) for what each does at runtime):

```kotlin
data class Unsupported(@Transient val typeName: String = "unsupported")   // in each of the seven types

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

Node filters, computed fields' `where`, and the data layer's named conditions all answer field questions through `RecordConditionEvaluator`, so they agree; dates compare through `RendererCalendar` in the device's time zone (`isToday` is the user's calendar day).

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
    // throws only CancellationException; the input and the outcome's effects read pageRecord through recordRef
    suspend fun execute(name: String, itemContext: DataRecord? = null, pageRecord: PageRecord? = null): MutationResult
}

class PageOperations(executor: OperationExecutor) {
    fun launch(name: String, itemContext: DataRecord?, pageRecord: PageRecord?, onSettled: (MutationResult) -> Unit)
    fun cancel()
}

fun renderedPageActionHandler(
    fallback: ActionHandler,
    mutationExecutor: MutationExecutor?,
    operations: PageOperations? = null,      // null: operation: actions are ignored
    pageRecord: PageRecord? = null,          // the record the dispatching page shows; its mutations and operations run with it
    recordCollectionOf: (pageId: String) -> String?,   // a page's record collection; null for a page that shows none
    navigateToPage: (pageId: String, record: RecordId?) -> Unit,
    navigateBack: () -> Unit,
): ActionHandler
```

The handler picks the record every navigation carries, `renderer:navigate:<page>` and each `PageDestination` in a `MutationResult.navigateTo`, by one set of rules: a page that declares no `record` opens with none; otherwise the destination's explicit record (`navigate.record`), else the dispatching row's id when the row's `_collection` is the page's collection, else `pageRecord`'s id when its collection is the page's, else none.

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

enum class SchemaElementKind { Condition, ComputedField, RecordComputed, Mutation, Effect, ValueRef, OperationResult }
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

/**
 * A page with a record collection shows the record of it whose id its navigation entry names:
 * root while the collection holds that record, whenMissing (or nothing) while it does not.
 */
@Serializable
data class UIPage(
    val id: String,
    val root: UINode,
    val record: String? = null,
    val whenMissing: UINode? = null,
) {
    fun recordOf(id: RecordId?): PageRecord?     // null unless record and id are both set
}

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

- `renderer:navigate:<page>` opens the page on top of the tab showing; naming a tab's root page selects that tab at its root. Opening the page and record already showing does nothing, while another record of that page opens on top of it. A tab root never shows a record.
- Selecting the tab showing returns it to its root.
- Back closes the page showing, then returns to the first tab from another tab's root, then leaves the screen.
- A start page that is not a tab root (onboarding, say) shows without the bar until the user enters a tab.

Every host navigates through the same pure model, `ScreenNavigationState` (in `ui:renderer-core`). Compose hosts draw it with `ScreenNavigationHost` (in `ui:renderer`):

```kotlin
val navigator = rememberScreenNavigator(screen.entryPage!!, screen.resolvedTabs())
val pagesById = remember(screen) { screen.pages.associateBy { it.id } }
WithRenderedTheme(theme = screen.theme) {
    ScreenNavigationHost(navigator) { entry ->
        val page = pagesById.getValue(entry.page)
        val pageRecord = page.recordOf(entry.record)
        val handler = remember(pageRecord) {
            renderedPageActionHandler(
                fallback = appHandler,
                mutationExecutor = mutationExecutor,
                pageRecord = pageRecord,
                recordCollectionOf = { pageId -> pagesById[pageId]?.record },
                navigateToPage = navigator::navigate,
                navigateBack = { if (!navigator.back()) leaveTheScreen() },
            )
        }
        SynapseRenderer(
            page = page,
            record = entry.record,
            actionHandler = handler,
            stateHolder = store,
            conditionEvaluator = store,
            collectionProvider = store,
        )
    }
}
```

```kotlin
@Composable
fun ScreenNavigationHost(
    navigator: ScreenNavigator,
    modifier: Modifier = Modifier,
    page: @Composable (entry: ScreenNavigationState.Entry) -> Unit,   // the entry's page, on its record
)

class ScreenNavigator(initial: ScreenNavigationState, val tabs: List<UINavigationTab>) {
    constructor(entryPage: String, tabs: List<UINavigationTab>, record: RecordId? = null)   // record ignored at a tab's root
    val state: ScreenNavigationState
    fun navigate(pageId: String, record: RecordId? = null)
    fun selectTab(index: Int)
    fun back(): Boolean                          // false: nowhere to go back to within the screen
}

@Composable
fun rememberScreenNavigator(entryPage: String, tabs: List<UINavigationTab>, record: RecordId? = null): ScreenNavigator

// ScreenNavigationState: each opened page is an Entry; the record survives encode() and decode().
data class Entry(val page: String, val key: Int, val record: RecordId? = null)
fun navigate(page: String, record: RecordId? = null): ScreenNavigationState
fun start(entryPage: String, tabRoots: List<String> = emptyList(), record: RecordId? = null): ScreenNavigationState   // companion
```

The page closure receives the whole entry, and each entry is a page of its own: opening another record of the page showing puts a new page on top, with its own saved state.

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
// record: the record a page with a record collection shows; a key saved without one reads back with none.
@Serializable
data class RenderedPageKey(val baseRoute: String, val pageId: String, val record: RecordId? = null) : NavKey

// Fold into a feature's FeatureLauncher.serializers so rendered pages survive saved state on iOS/web:
val rendererNavigationSerializers: SerializersModule
```

Register rendered pages inside a feature's `EntryProviderScope<NavKey>.register(dispatcher)` block. When `config.dataSchema` is provided, one `ReactiveDataStore` serves every page of the base route: it answers state, collections, and conditions, and it persists through `config.dataPersistence` with the base route as its scope. The `mutation:` action prefix is intercepted and routed to it. Without a `dataSchema` the route has no collections: every `dataSource` binds to an empty list.

The store is built when one of the route's pages is first shown and kept in the enclosing `NavContainer`'s ViewModel store (`LocalNavContainerViewModelStoreOwner`), so it survives configuration changes and a rebuilt entry provider, and it is closed when that ViewModel store is cleared. Its changes are written in the background and whenever the page stops. A different `dataSchema` (compared by value), `dataPersistence` or `stateHolder` (by identity) replaces the store, once the old one's unsaved changes are written, so keep one persistence instance per backend. Outside a `NavContainer` the store lives as long as the registration that built it, so an entry provider rebuilt within the save window can hydrate a new store without the last change.

`UIScreen` is the payload as it arrives; nothing applies its `theme` or `data` on its own. Load its pages into the `SchemaStore` and pass the rest through the config:

```kotlin
interface SchemaStore {
    fun get(pageId: String): UIPage?
    fun put(page: UIPage)                        // keyed by page.id
    fun remove(pageId: String)
    fun contains(pageId: String): Boolean
    fun clear()
    fun pageIds(): Set<String>
}
fun SchemaStore.load(screen: UIScreen)           // puts every page
class InMemorySchemaStore : SchemaStore
```

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

// Navigate to a rendered page, on record when it shows one:
fun NavigationDispatcher.navigateToRenderedPage(
    baseRoute: String,
    pageId: String,
    clearStack: Boolean = false,
    record: RecordId? = null,
)

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

A route without tabs registers each page as its own Nav3 entry, its key carrying the record the page shows. A route whose `navigation` has tabs is one entry holding the whole screen through `ScreenNavigationHost`, opened at the key's page on the key's record; navigation between its pages stays inside that entry, and back pops the entry only once there is nowhere to go back to within the screen. Either way each page renders through the `page` overload of `SynapseRenderer`, and `renderer:navigate:` and a mutation's or operation's `navigate` effect carry the record `renderedPageActionHandler` picks.

Each rendered page gets its own `PageOperations`, cancelled when the page leaves composition, including an Android configuration change (the route's store itself survives it). An operation the user walked away from never applies its effects, so make submits idempotent on the server. A page under a bottom sheet or dialog stays composed, so its operations keep running.

**Built-in action prefixes:**
- `renderer:navigate:<pageId>`: navigates to another rendered page, on the record `renderedPageActionHandler` picks
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
