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

Triggered from UI via `"actionId": "mutation:<name>"`.

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

## Runtime Classes

### ReactiveDataStore

Materialises a `DataSchema` into `StateFlow`-backed state. It is the whole reactive model, so it implements all three renderer contracts at once: `RendererStateHolder` (fields), `CollectionProvider` (collections), and `ConditionEvaluator` (the schema's named conditions). Pass the same instance as `stateHolder`, `collectionProvider`, and `conditionEvaluator`.

```kotlin
class ReactiveDataStore(
    val schema: DataSchema,
    // Non-null. Use DataPersistence.NoOp for a purely transient store.
    private val persistence: DataPersistence = DataPersistence.NoOp,
    private val scope: String = "default",
) : RendererStateHolder, CollectionProvider, ConditionEvaluator {
    override fun getCollection(name: String): StateFlow<List<DataRecord>>
    override fun conditionFlow(conditionKey: String): StateFlow<Boolean>
    override fun evaluate(conditionKey: String): Boolean

    fun insertRecord(collectionName: String, record: DataRecord)
    fun deleteRecord(collectionName: String, recordId: Any?)
    fun updateRecord(collectionName: String, recordId: Any?, values: Map<String, Any?>)
    fun collectionSize(name: String): Int
    fun readField(name: String): Any?
    fun setSortOrder(collection: String, field: String, direction: SortDirection)

    // Restore a declared field to its schema default (or zero value when no default).
    // Throws on unknown fields; silently no-op on computed fields.
    fun resetField(name: String)

    // Group mutations. Persistence, computed recompute, condition refresh, and the revision
    // bump fire exactly once on the outermost flush. Returns [block]'s result.
    fun <R> batch(block: ReactiveDataStore.() -> R): R

    override fun clear()
    // + all RendererStateHolder methods (getOrPutString, putString, getString, revision, etc.)
}
```

Conditions are re-evaluated after every settled change. Field questions inside them go through the core `RecordConditionEvaluator.matchesValues`; only `collectionEmpty`/`collectionNotEmpty` and the `and`/`or`/`not` combinators are answered by the store.

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

### renderedPageActionHandler

Gives the built-in action prefixes their meaning for any host, Nav3 or not, and passes everything else to `fallback`. A `mutation:` action reads its item context from the payload's `_itemContext`.

```kotlin
fun renderedPageActionHandler(
    fallback: ActionHandler,
    mutationExecutor: MutationExecutor?,          // null: mutation: actions are ignored
    navigateToPage: (pageId: String) -> Unit,
    navigateBack: () -> Unit,
): ActionHandler
```

### DataPersistence (interface)

Optional durable storage backend. Implement with your storage engine of choice. In the navigation module, pass it as `RenderedPageConfig.dataPersistence`; each route uses its base route as the `scope`. Wrap your implementation to prefix scopes when one base route must hold separate data per user or session.

```kotlin
interface DataPersistence {
    fun saveField(scope: String, fieldName: String, value: Any?)
    fun saveCollection(scope: String, collectionName: String, records: List<DataRecord>)
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
