# Declarative Data Layer

**Module**: `ui:renderer-data` | **Artifact**: `com.ribads.synapse:ui-renderer-data`
**Package**: `com.ribads.synapse.ui.renderer.data`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-renderer-data:<version>")
}
```

Depends only on `ui:renderer-core` (pure Kotlin, no Compose), so it runs in any engine, a browser preview, or a test.

The data layer lets JSON schemas declare typed fields, collections, mutations, and conditions. The renderer binds to this data reactively, with no Kotlin code needed for data operations.

### Architecture

```
Schema types (ui:renderer-core)     <- serializable declarations, RecordConditionEvaluator
    |
Runtime (ui:renderer-data)          <- ReactiveDataStore, MutationExecutor, renderedPageActionHandler
    |
Navigation wiring (ui:renderer-navigation)  <- automatic setup in renderedEntry / renderedEntries
```

Without a `DataSchema` there is no store, so a route's collections are always empty: every `dataSource` binds to an empty list.

---

## DataSchema

Top-level data model declared in the `"data"` section of a `UIScreen`.

```kotlin
@Serializable
data class DataSchema(
    val fields: Map<String, DataField> = emptyMap(),
    val collections: Map<String, DataCollection> = emptyMap(),
    val mutations: Map<String, DataMutation> = emptyMap(),
    val conditions: Map<String, DataCondition> = emptyMap(),
    val operations: Map<String, DataOperation> = emptyMap(),
)
```

---

## DataField

```kotlin
@Serializable
data class DataField(
    val type: DataFieldType,
    val default: JsonPrimitive? = null,
    val computed: ComputedField? = null,
)

@Serializable
enum class DataFieldType { string, long, double, boolean, stringList }
```

---

## DataCollection

```kotlin
@Serializable
data class DataCollection(
    val schema: Map<String, String> = emptyMap(),  // field name → type name
    val orderBy: DataOrderBy? = null,
    val initialData: List<Map<String, JsonPrimitive>> = emptyList(),
)

@Serializable
data class DataOrderBy(
    val field: String,
    val direction: SortDirection = SortDirection.asc,
)

@Serializable
enum class SortDirection { asc, desc }
```

---

## ComputedField (sealed, discriminator `"type"`)

Computed fields derive their value from collection data or other fields. They update automatically when underlying data changes. A computed field is a `DataField` whose `computed` holds the operation:

```json
"total_expenses": {
  "type": "double",
  "computed": { "type": "sum", "collection": "expenses", "field": "amount" }
}
```

| Variant | SerialName | Key fields |
|---------|-----------|------------|
| `Sum` | `"sum"` | `collection: String`, `field: String`, `where: DataCondition?` |
| `Count` | `"count"` | `collection: String`, `where: DataCondition?` |
| `Average` | `"average"` | `collection: String`, `field: String`, `where: DataCondition?` |
| `Min` | `"min"` | `collection: String`, `field: String`, `where: DataCondition?` |
| `Max` | `"max"` | `collection: String`, `field: String`, `where: DataCondition?` |
| `Divide` | `"divide"` | `numerator: String`, `denominator: String` (field names) |
| `Subtract` | `"subtract"` | `left: String`, `right: String` (field names) |

---

## DataMutation (sealed, discriminator `"type"`)

| Variant | SerialName | Key fields |
|---------|-----------|-----------|
| `Insert` | `"insert"` | `collection: String`, `record: Map<String, DataValueRef>`, `then: List<DataEffect>` |
| `Delete` | `"delete"` | `collection: String`, `id: DataValueRef`, `then: List<DataEffect>` |
| `Update` | `"update"` | `collection: String`, `id: DataValueRef`, `values: Map<String, DataValueRef>`, `then: List<DataEffect>` |
| `Trigger` | `"trigger"` | `then: List<DataEffect>` (effects-only, no collection operation) |

Triggered from UI via `"actionId": "mutation:<name>"`. Mutations are local and synchronous; for anything that leaves the device, use a [DataOperation](#dataoperation).

---

## DataValueRef (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Description |
|---------|-----------|--------|-------------|
| `FieldRef` | `"fieldRef"` | `name: String` | Current value of a declared field |
| `Literal` | `"literal"` | `value: JsonPrimitive` | Hard-coded value |
| `Timestamp` | `"timestamp"` | (none) | Current epoch milliseconds |
| `UuidRef` | `"uuid"` | (none) | Random UUID string |
| `ItemRef` | `"itemRef"` | `path: String` | Value from current item context (inside `itemTemplate`) |

---

## DataEffect (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Description |
|---------|-----------|--------|-------------|
| `SetField` | `"setField"` | `field: String`, `value: JsonPrimitive` | Reset a declared field to a literal value |
| `SetFieldFromRef` | `"setFieldFromRef"` | `field: String`, `ref: DataValueRef` | Set a field from a resolved value ref |
| `ClearFields` | `"clearFields"` | `fields: List<String>` | Reset fields to their schema defaults. Computed fields in the list are silently skipped (their value is derived). |
| `Navigate` | `"navigate"` | `page: String` | Navigate to a rendered page |
| `Back` | `"back"` | (none) | Navigate back |
| `IncrementField` | `"incrementField"` | `field: String`, `by: JsonPrimitive` | Increment a numeric field |
| `SetSort` | `"setSort"` | `collection: String`, `field: String`, `direction: SortDirection` (default `asc`) | Change collection sort order. JSON encoding remains `"asc"` / `"desc"` (enum names). |

> `SetField` and `SetFieldFromRef` coerce to the declared field type. Stringified numbers (`"42"` for a `long` field) and stringified booleans (`"true"` for a `boolean` field) are accepted.

---

## DataCondition (sealed, discriminator `"type"`)

| Variant | SerialName | Fields |
|---------|-----------|--------|
| `FieldNotEmpty` | `"fieldNotEmpty"` | `field: String` |
| `FieldEmpty` | `"fieldEmpty"` | `field: String` |
| `CollectionNotEmpty` | `"collectionNotEmpty"` | `collection: String` |
| `CollectionEmpty` | `"collectionEmpty"` | `collection: String` |
| `Equals` | `"equals"` | `field: String`, `value: JsonPrimitive?`, `fieldRef: String?` |
| `GreaterThan` | `"greaterThan"` | `field: String`, `value: JsonPrimitive` |
| `LessThan` | `"lessThan"` | `field: String`, `value: JsonPrimitive` |
| `Contains` | `"contains"` | `field: String`, `value: String` |
| `IsTrue` | `"isTrue"` | `field: String` |
| `IsFalse` | `"isFalse"` | `field: String` |
| `DateBefore` | `"dateBefore"` | `field: String`, `reference: String` (default "now") |
| `DateAfter` | `"dateAfter"` | `field: String`, `reference: String` (default "now") |
| `DateWithin` | `"dateWithin"` | `field: String`, `days: Int` |
| `IsToday` | `"isToday"` | `field: String`. Today is the **device's local calendar day** (start-of-day inclusive, next day exclusive), the same in a named condition, a computed field's `where`, and a node's `filter`. |
| `And` | `"and"` | `operands: List<DataCondition>` |
| `Or` | `"or"` | `operands: List<DataCondition>` |
| `Not` | `"not"` | `operand: DataCondition` |

---

## DataOperation

An operation the host app runs, usually over the network, triggered by `"actionId": "operation:<name>"` (from a button, a card, or an `OnAppear` node). The schema declares what goes in and where the outcome goes; the host's `OperationHandler` decides how it runs. See SKILL.md for the host contract.

```kotlin
@Serializable
data class DataOperation(
    val input: Map<String, DataValueRef> = emptyMap(),   // resolved like a mutation's record, item context included
    val pendingField: String? = null,                    // declared boolean, true while running; never persisted
    val failureField: String? = null,                    // declared string, gets the failure code; cleared on each start; never persisted
    val result: DataOperationResult? = null,             // where Success.records go
    val onSuccess: List<DataEffect> = emptyList(),
    val onFailure: List<DataEffect> = emptyList(),
    val concurrency: OperationConcurrency = OperationConcurrency.dropWhileRunning,
)
```

### DataOperationResult (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Effect of `Success.records` |
|---------|-----------|--------|-----------------------------|
| `ReplaceCollection` | `"replaceCollection"` | `collection: String` | Replace every record, coerced to the collection's declared types, with ids generated where missing |
| `SetFields` | `"setFields"` | `fields: Map<String, String>` (field name to record key) | Copy keys of the first record into fields, coerced to their declared types; with no records, reset the fields to their defaults |
| `Unsupported` | (unknown type) | `typeName` | Records are discarded |

### OperationConcurrency

JSON uses the enum names.

| Value | A second launch while one is running |
|---|---|
| `dropWhileRunning` (default) | Is ignored, so a double tap never submits twice |
| `replace` | Cancels the running one and starts again (search-as-you-type) |

The policy is per operation name: an `OnAppear` inside an `itemTemplate` launching the same operation for every row runs once under `dropWhileRunning`.

### Example

```json
"operations": {
  "submit_order": {
    "input": { "amount": { "type": "fieldRef", "name": "amount" } },
    "pendingField": "submitting",
    "failureField": "submit_error",
    "result": { "type": "replaceCollection", "collection": "orders" },
    "onSuccess": [ { "type": "navigate", "page": "done" } ]
  }
}
```

`pendingField` and `failureField` must be declared fields of type `boolean` and `string`; a misdeclared one is reported through diagnostics and ignored.

---

## Unsupported types

A `"type"` this build does not know decodes to the sealed type's `Unsupported` variant instead of failing the screen. Each keeps the original value in `typeName` and behaves as follows:

| Variant | At runtime |
|---|---|
| `DataCondition.Unsupported` | Any condition tree containing one is `false`, including under `not`, in named conditions, `where`, and node `filter`s |
| `ComputedField.Unsupported` | The field is a plain field holding its declared `default`; it has no dependencies |
| `DataMutation.Unsupported` | Does nothing; its `then` effects are dropped at decode time |
| `DataEffect.Unsupported` | Skipped; later effects in the same `then` still run |
| `DataValueRef.Unsupported` | Resolves to `null` |
| `DataOperationResult.Unsupported` | The returned records are discarded; effects still run |

Use `UIScreen.compatibilityWith` (see SKILL.md) to find them before rendering. An unknown `DataField.type` still fails the parse.

---

## Runtime Classes

### ReactiveDataStore

Materialises a `DataSchema` into `StateFlow`-backed state. It is the whole reactive model, so it implements all three renderer contracts at once: `RendererStateHolder` (fields), `CollectionProvider` (collections), and `ConditionEvaluator` (the schema's named conditions). Pass the same instance as `stateHolder`, `collectionProvider`, and `conditionEvaluator`.

```kotlin
class ReactiveDataStore(
    val schema: DataSchema,
    // Use DataPersistence.NoOp for a purely transient store.
    persistence: DataPersistence = DataPersistence.NoOp,
    // Separates this store's data from others in the same persistence.
    scope: String = "default",
    // Receives onPersistenceError when a save fails.
    diagnostics: RenderDiagnostics = RenderDiagnostics.NoOp,
) : RendererStateHolder, CollectionProvider, ConditionEvaluator {
    override fun getCollection(name: String): StateFlow<List<DataRecord>>
    override fun conditionFlow(conditionKey: String): StateFlow<Boolean>
    override fun evaluate(conditionKey: String): Boolean
    // Advances once per settled change that changed `key`'s value, computed fields included.
    override fun revisionOf(key: String): StateFlow<Long>

    fun insertRecord(collectionName: String, record: DataRecord)
    // Coerces JSON primitives or Kotlin values to the declared types; generates missing ids.
    fun replaceCollection(collectionName: String, records: List<DataRecord>)
    fun deleteRecord(collectionName: String, recordId: Any?)
    fun updateRecord(collectionName: String, recordId: Any?, values: Map<String, Any?>)
    fun collectionSize(name: String): Int
    fun readField(name: String): Any?
    fun setSortOrder(collection: String, field: String, direction: SortDirection)

    // Restore a declared field to its schema default (or zero value when no default).
    // Throws on unknown fields; silently no-op on computed fields.
    fun resetField(name: String)

    // Group mutations. Recompute, condition refresh, the revision bumps and the save happen
    // exactly once, when the outermost batch ends. Returns [block]'s result.
    fun <R> batch(block: ReactiveDataStore.() -> R): R

    // Writes every change not yet saved; returns once it is written or has failed.
    suspend fun flush()
    // Starts writing every change not yet saved and stops the store's clock.
    fun close()

    override fun clear()
    // + all RendererStateHolder methods (getOrPutString, putString, getString, revision, etc.)
}
```

Hydration reads the persistence synchronously, on the thread that builds the store, and coerces every loaded value to its declared type. After that the store saves in the background: changes gather for 250 ms after the first unsaved one and are written in one `DataPersistence.save` call, off the main thread, so typing or toggling never waits on storage. Call `flush()` when the app goes to the background and `close()` when the store is discarded; `renderedEntries` does both. A failed save is reported through `RenderDiagnostics.onPersistenceError` and written again with the next change, `flush()` or `close()`.

Every condition and `where` is compiled once (`DataCondition.compile()`). Named conditions are re-evaluated after every settled change; only `collectionEmpty`/`collectionNotEmpty` and the `and`/`or`/`not` combinators are answered by the store. A computed field whose `where` compares against another field (`fieldRef`) is recomputed when that field changes, and a computed `fieldRef` field is ordered before it. Values that depend on the time (`dateBefore`, `dateAfter`, `dateWithin`, `isToday`) are re-evaluated each wall-clock minute while something observes one of them.

A collection's `orderBy` sorts mixed value types in a fixed order (missing, then booleans, numbers, strings), and records that compare equal keep the order they were inserted in.

Fields named as any operation's `pendingField` or `failureField` are never persisted or hydrated, so a spinner can never come back stuck after process death.

> **Threading:** `ReactiveDataStore` is not thread-safe. Drive it from a single thread (the UI thread in practice). Marshal back to the main dispatcher before calling in from a background coroutine.

### MutationExecutor

Executes named mutations against a `ReactiveDataStore`. The primary operation and its `then` effects run inside a single `ReactiveDataStore.batch`, so persistence and computed recompute happen exactly once. Navigation effects (`Navigate`, `Back`) are collected and returned for the navigation layer to act on.

```kotlin
class MutationExecutor(
    private val store: ReactiveDataStore,
    private val schema: DataSchema,
) {
    fun execute(name: String, itemContext: DataRecord? = null): MutationResult
}

data class MutationResult(
    val navigateToPages: List<String> = emptyList(),
    val navigateBack: Boolean = false,
)
```

### OperationExecutor

Runs a schema's operations through the host's `OperationHandler`. Clears `failureField` and sets `pendingField`, calls the handler, then applies the result, the failure code and the effects in one `batch`, resetting `pendingField` in the same batch. On cancellation it resets `pendingField` and applies nothing.

```kotlin
class OperationExecutor(
    store: ReactiveDataStore,
    handler: OperationHandler,
    diagnostics: RenderDiagnostics,
) {
    // Call on the store's thread. Throws only CancellationException: a handler throw becomes
    // Failure(UNEXPECTED), and an effect that throws is reported, never propagated.
    suspend fun execute(name: String, itemContext: DataRecord? = null): MutationResult
}
```

### PageOperations

The operations one page has started, with the concurrency policy applied. Create one per page, launch from the main thread, and `cancel()` it when the page leaves, so an operation the user walked away from never applies its effects or navigates.

```kotlin
class PageOperations(executor: OperationExecutor) {
    fun launch(name: String, itemContext: DataRecord?, onSettled: (MutationResult) -> Unit)
    fun cancel()
}
```

`renderedEntries` does this for you. Host-specific errors (a throwing `onSettled`) are reported through the executor's diagnostics.

### renderedPageActionHandler

Gives the built-in action prefixes their meaning for any host, Nav3 or not, and passes everything else to `fallback`. `mutation:` and `operation:` actions read their item context from the payload's `_itemContext`.

```kotlin
fun renderedPageActionHandler(
    fallback: ActionHandler,
    mutationExecutor: MutationExecutor?,          // null: mutation: actions are ignored
    operations: PageOperations? = null,           // null: operation: actions are ignored
    navigateToPage: (pageId: String) -> Unit,
    navigateBack: () -> Unit,
): ActionHandler
```

### DataPersistence (interface)

Optional durable storage backend. Implement with your storage engine of choice. In the navigation module, pass it as `RenderedPageConfig.dataPersistence`; each route uses its base route as the `scope`. Wrap your implementation to prefix scopes when one base route must hold separate data per user or session.

`save` and `clear` run off the main thread, one call at a time across every store, in the order the changes were made, so they may block on I/O. They must not throw: a failure is reported and the changes are offered again with the next batch. The loads run on the thread that builds the store.

```kotlin
interface DataPersistence {
    // Everything that changed since the previous call.
    fun save(scope: String, changes: DataChanges)
    fun loadFields(scope: String): Map<String, Any?>
    // Return null if the collection has never been persisted for this scope;
    // return an empty list if it was persisted empty (e.g. user deleted all
    // records). The distinction controls whether initialData seeds the store.
    fun loadCollection(scope: String, collectionName: String): List<DataRecord>?
    fun clear(scope: String)

    companion object {
        // Discards writes; loads always return "never persisted". Use this
        // when you want a transient store with no durable layer.
        val NoOp: DataPersistence
    }
}

// The latest value of each changed field, and each changed collection.
data class DataChanges(
    val fields: Map<String, Any?> = emptyMap(),
    val collections: Map<String, CollectionChange> = emptyMap(),
)

// Both forms carry every current record, in order: a key-value store writes `records`,
// a database applies the edits.
sealed interface CollectionChange {
    val records: List<DataRecord>

    data class Replaced(override val records: List<DataRecord>) : CollectionChange

    data class Edited(
        override val records: List<DataRecord>,
        val upserted: List<DataRecord>,   // inserted and updated records
        val deletedIds: Set<Any?>,
    ) : CollectionChange
}
```

## Engine contracts (package `com.ribads.synapse.ui.renderer.engine`, module `ui:renderer-core`)

These are not data-layer types; the store implements the first two, and the renderers read them.

```kotlin
typealias DataRecord = Map<String, Any?>

fun interface CollectionProvider {
    fun getCollection(name: String): StateFlow<List<DataRecord>>
    companion object { val Empty: CollectionProvider }
}

fun interface ConditionEvaluator {
    fun conditionFlow(conditionKey: String): StateFlow<Boolean>
    fun evaluate(conditionKey: String): Boolean = conditionFlow(conditionKey).value
    companion object { val AlwaysFalse: ConditionEvaluator }
}

const val ITEM_CONTEXT_PAYLOAD_KEY = "_itemContext"

/** Picks an image for an ImagePicker node. Return a stable path or URI, or null when cancelled; never throw. */
fun interface MediaProvider {
    suspend fun pickImage(): String?
    companion object { val NoOp: MediaProvider }
}
```
