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
    val persist: Boolean = true,      // false: never saved, and a saved value is ignored on load
)

@Serializable
enum class DataFieldType { string, long, double, boolean, stringList }
```

Every declared field is saved between launches unless it sets `"persist": false`. Mark search text, dialog and picker flags, and other state that belongs to one visit with `"persist": false`, so it starts from its `default` on each launch.

```json
"search": { "type": "string", "default": "", "persist": false }
```

---

## DataCollection

```kotlin
@Serializable
data class DataCollection(
    val schema: Map<String, String> = emptyMap(),  // field name → type name
    val orderBy: DataOrderBy? = null,
    val initialData: List<Map<String, JsonPrimitive>> = emptyList(),
    val computed: Map<String, RecordComputed> = emptyMap(),  // column name → computation; see Computed columns
)

@Serializable
data class DataOrderBy(
    val field: String,
    val direction: SortDirection = SortDirection.asc,
)

@Serializable
enum class SortDirection { asc, desc }
```

### Column types

`schema` names each column's type with a `DataFieldType` name. The store converts every value to its column's type on every write: `insert`, `update` and `updateWhere` mutations, `renderer:setItemField:`, a `replaceCollection` result, `initialData`, and the records it hydrates. A record therefore reads the same before and after a relaunch.

| Column type | Holds | A value converts when it is |
|---|---|---|
| `string`, or not declared | text | anything: it becomes its text |
| `stringList` | comma-joined text | a list, whose items are joined with `,`; anything else becomes its text |
| `long` | whole number | a number, truncated, or text that is a whole number |
| `double` | number | a number, or numeric text |
| `boolean` | `true` / `false` | a boolean, or the text `"true"` or `"false"` |

- Null stores null in any column, and so does blank text in a `long` or `double` column.
- A value that does not convert (a boolean into a `long`, `"many"` into a `long`, `"yes"` into a `boolean`) stores null. `renderer:setItemField:` leaves the record unchanged instead, and never writes a column the collection does not declare.
- A record whose `id` is missing or does not convert gets one generated in the `id` column's type: one more than the largest for `long`, a random UUID otherwise.
- `update` and `delete` convert the id they are given to the `id` column's type before matching, so `"2"` finds the record whose `long` id is `2`. An id that does not convert matches nothing.
- A record's `id` never changes: an `update`, an `updateWhere` or `renderer:setItemField:` that writes `id` leaves it as it was.
- Keep ids unique within a collection. The store generates unique ones, but `initialData`, an `insert` that gives its own `id`, and a `replaceCollection` result can repeat one. `delete` and `update` act on every record holding the id they are given, and the edits `DataPersistence.save` receives name records by id, so records that share an id cannot be told apart once saved. An `insert` whose `unique` lists `id` is skipped when its id is taken.
- Declare every numeric column. An undeclared column holds text, so it sorts as text (`"10"` before `"9"`) and reads as null through a number lane such as `ListItem.amountKey`.

### Computed columns

`computed` names columns that each record derives from its own columns. An operand is a string naming a column of the same record, computed ones included, or a number.

```kotlin
@Serializable
sealed class RecordComputed   // discriminator "type"
```

| Variant | SerialName | Fields | Value |
|---------|-----------|--------|-------|
| `DaysUntil` | `"daysUntil"` | `field: String` | Calendar days from today to the time in `field`, in the device's time zone: 1 for tomorrow, -1 for yesterday |
| `DaysSince` | `"daysSince"` | `field: String` | Calendar days from the time in `field` to today |
| `DateOffset` | `"dateOffset"` | `field: String`, `years`, `months`, `weeks`, `days`, `hours`, `minutes: Int` (each default 0), `timesField: String? = null` | The time in `field` moved as the `dateOffset` value ref moves it. `timesField` names a column whose value, read as a whole number, multiplies every unit; a missing value counts as 0 |
| `StartOf` | `"startOf"` | `field: String`, `unit: CalendarUnit` | The first instant of the day, week (from Monday), month or year holding the time in `field` |
| `Ratio` | `"ratio"` | `numerator: JsonPrimitive`, `denominator: JsonPrimitive` | Always a double, and 0.0 when the denominator is 0, as computed `divide` gives |
| `Add` | `"add"` | `operands: List<JsonPrimitive>` | Sum |
| `Subtract` | `"subtract"` | `left: JsonPrimitive`, `right: JsonPrimitive` | `left - right` |
| `Multiply` | `"multiply"` | `operands: List<JsonPrimitive>` | Product |

```json
"tasks": {
  "schema": { "id": "long", "title": "string", "due": "long" },
  "computed": {
    "days_left": { "type": "daysUntil", "field": "due" },
    "remind_at": { "type": "dateOffset", "field": "due", "days": -1 }
  },
  "orderBy": { "field": "days_left" }
}
```

- The store derives every computed column, in dependency order, whenever a record enters the collection: `initialData`, hydration, `insertRecord`, `updateRecord`, an `updateWhere` mutation, `renderer:setItemField:` and `replaceCollection`. Node filters, `where`, `orderBy`, `groupBy`, aggregates, named conditions, templates and `DataRecordView` read them like any other column.
- A date computation is null when `field` holds no time (a number, or text holding a whole number), and when the result does not fit in epoch milliseconds.
- Arithmetic follows the [value ref arithmetic](#datavalueref-sealed-discriminator-type) with one difference: a column holds one type for every record, decided from its operands. It holds doubles when an operand is a `double` column, a fractional number, or a computed column that holds doubles (`ratio`, or arithmetic over one), and whole numbers otherwise. So `add` over two `double` columns gives `0.0`, not `0`, for a record missing both, and sorting, grouping and equality see one type per column.
- Computed columns are never written or saved. Every write drops a value given under a computed name (an `insert`, `update` or `updateWhere` mutation, a `replaceCollection` result, `initialData`, `renderer:setItemField:`), a value saved under one earlier is ignored on load, and `DataPersistence.save` receives only the stored columns, in `records` and in `upserted` alike. Conversion to the [column types](#column-types) applies to the stored columns only.
- `daysUntil`, `daysSince` and every column that reads one read the clock. While their collection, an aggregate whose `field` or `where` reads one of them, or a named condition about the collection is observed, the store derives them again on the first `RendererClock.minutes` tick of a new day, and at once when something starts observing them on a day later than their values. A tick on the same day, or a new day that changes no value, emits and saves nothing, and columns that do not read the clock never wake.
- Building the store throws `IllegalStateException`, naming the collection and the columns, when a computed column is named `id`, shares its name with a `schema` column, or is part of a cycle of computed columns.

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
| `Divide` | `"divide"` | `numerator: String`, `denominator: String` (field names); 0 when the denominator is 0 |
| `Subtract` | `"subtract"` | `left: String`, `right: String` (field names) |
| `Add` | `"add"` | `operands: List<JsonPrimitive>`: a string names a field, a number is itself |
| `Multiply` | `"multiply"` | `operands: List<JsonPrimitive>`, read as `Add` reads them |

`add` and `multiply` follow the [value ref arithmetic](#datavalueref-sealed-discriminator-type): a missing or non-numeric operand counts as 0, the result is whole when every operand is, and it is null over no operands or when a number cannot hold it. A field named among the operands is a dependency like a `divide` operand, so a cycle or an unknown field throws when the store is built; a number is no dependency. `divide` and `subtract` keep field names only, so a schema using them still parses on clients older than schema version 3.

```json
"yearly_cost": { "type": "double", "computed": { "type": "multiply", "operands": ["monthly_cost", 12] } }
```

---

## DataMutation (sealed, discriminator `"type"`)

| Variant | SerialName | Key fields |
|---------|-----------|-----------|
| `Insert` | `"insert"` | `collection: String`, `record: Map<String, DataValueRef>`, `unique: List<String>` (default empty), `then: List<DataEffect>` |
| `Delete` | `"delete"` | `collection: String`, `id: DataValueRef`, `then: List<DataEffect>` |
| `Update` | `"update"` | `collection: String`, `id: DataValueRef`, `values: Map<String, DataValueRef>`, `then: List<DataEffect>` |
| `DeleteWhere` | `"deleteWhere"` | `collection: String`, `where: DataCondition` (required), `then: List<DataEffect>` |
| `UpdateWhere` | `"updateWhere"` | `collection: String`, `where: DataCondition` (required), `values: Map<String, DataValueRef>`, `then: List<DataEffect>` |
| `Trigger` | `"trigger"` | `then: List<DataEffect>` (effects-only, no collection operation) |

Triggered from UI via `"actionId": "mutation:<name>"`. Mutations are local and synchronous; for anything that leaves the device, use a [DataOperation](#dataoperation).

### A mutation run

A run makes the mutation's change, then applies its `then` effects in order, inside one `ReactiveDataStore.batch`: computed fields and conditions are brought up to date, observers are told, and the change is saved once, when the run ends. Its value refs read the clock once, so every `timestamp` in the run is the same time.

A `runMutation` effect runs the mutation it names at that point. Its change and its effects join the same batch, read the same row (`itemRef`) and the same clock reading, and add their navigation to the run's: their pages in order among the run's own, and `back` when either asks for it. A name the schema does not declare is skipped. An operation's `onSuccess` and `onFailure` run mutations the same way, with the reading the operation took when it settled.

Mutations that run each other, directly (`a` runs `a`) or through a chain (`a` runs `b`, which runs `a`), would never finish. Building a `MutationExecutor` or an `OperationExecutor` checks every mutation, including one only an operation runs, and throws `IllegalStateException("mutations run each other: a -> b -> a")`, naming the first such chain.

```json
"checkout": { "type": "insert", "collection": "orders",
  "record": { "placed_at": { "type": "timestamp" } },
  "then": [ { "type": "runMutation", "mutation": "empty_cart" }, { "type": "navigate", "page": "receipt" } ] },
"empty_cart": { "type": "deleteWhere", "collection": "cart", "where": { "type": "isTrue", "field": "in_cart" } }
```

### Changing many records

`deleteWhere` deletes, and `updateWhere` updates, every record of the collection that `where` matches.

- `where` is required, so a bulk mutation never empties a collection by accident. To act on every record, match something every record has, such as `fieldNotEmpty` on `id`.
- Inside `where`, `field` reads the record, computed columns included, and `fieldRef` reads the model's fields. It is tested once, against the records as they were before the mutation, all against one reading of the clock. As in any `where`, `exists`, `collectionEmpty` and `collectionNotEmpty` are false, and an `Unsupported` condition anywhere in it matches nothing, so nothing changes. A `where` that reads `record.` matches nothing when the run has no page record, or its record is gone, so a missing record can never widen it to records whose field is empty.
- In `updateWhere`'s `values`, `itemRef` reads the record being updated, computed columns included, and every ref shares the run's clock reading. Values convert to the [column types](#column-types), and an `id` among them is ignored, as in `update`.
- The collection keeps its `orderBy`: deleting leaves the other records in place, and the records an `updateWhere` moves are sorted into place together.
- Each deleted or changed record's id reaches `DataPersistence.save` as an edit. A record that `updateWhere` leaves as it was is no edit, so an `updateWhere` that changes nothing saves nothing.

```json
"uncheck_all": { "type": "updateWhere", "collection": "items",
  "where": { "type": "isTrue", "field": "in_cart" },
  "values": { "in_cart": { "type": "literal", "value": false } } }
```

### Unique inserts

An `insert` with `unique` is skipped when a record already holds the new record's value in every listed column. The new record is compared as the collection would hold it, converted to the column types and with its computed columns derived, so `"2"` matches a `long` column's `2`, and a null value matches a missing one. Its `then` effects run either way.

```json
"add_staple": { "type": "insert", "collection": "items", "unique": ["name"],
  "record": { "name": { "type": "itemRef", "path": "name" } } }
```

---

## DataValueRef (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Description |
|---------|-----------|--------|-------------|
| `FieldRef` | `"fieldRef"` | `name: String` | Current value of a declared field |
| `Literal` | `"literal"` | `value: JsonPrimitive` | Hard-coded value; `null` clears the field or column it is written to |
| `Timestamp` | `"timestamp"` | (none) | Current epoch milliseconds, one reading per mutation or operation run |
| `UuidRef` | `"uuid"` | (none) | Random UUID string |
| `ItemRef` | `"itemRef"` | `path: String` | Value from current item context (inside `itemTemplate`); in an `updateWhere`'s `values`, from the record being updated |
| `RecordRef` | `"recordRef"` | `path: String` | A field of the record the running page shows, read from the store when the ref resolves, so a `runMutation` later in the run sees what the run changed before it. Null on a page that shows no record, and once the record is gone |
| `DateOffset` | `"dateOffset"` | `from: DataValueRef`, `years`, `months`, `weeks`, `days`, `hours`, `minutes: Int` (each default 0) | `from` moved on the device's calendar by the date units, keeping its wall-clock time across a daylight saving change, then by the elapsed hours and minutes. Months clamp: 31 January plus a month is the last day of February |
| `StartOf` | `"startOf"` | `from: DataValueRef`, `unit: CalendarUnit` | The first instant of the day, week (from Monday), month or year holding `from` |
| `Add` | `"add"` | `operands: List<DataValueRef>` | Sum |
| `Multiply` | `"multiply"` | `operands: List<DataValueRef>` | Product |
| `Subtract` | `"subtract"` | `left: DataValueRef`, `right: DataValueRef` | `left - right` |
| `Divide` | `"divide"` | `left: DataValueRef`, `right: DataValueRef` | `left / right`, always a double |

Expression refs nest and never throw:

- One clock reading serves a whole mutation run, the mutations it runs included, so `timestamp` and `dateOffset(timestamp)` agree to the millisecond. An operation reads the clock twice: once for its `input` when it starts, and once for its `onSuccess` or `onFailure` effects when it settles.
- A missing or non-numeric operand counts as 0, as `incrementField` reads its value. The result is whole when every operand is whole (an integer, or text holding one), and a double otherwise.
- Null results: dividing by zero, an empty operand list, a whole result a `Long` cannot hold or a double that is not finite, a `from` that is not a time (a number, or text holding a whole number), and a date that epoch milliseconds cannot hold.

```json
"remind_at": { "type": "dateOffset", "from": { "type": "fieldRef", "name": "due" }, "days": -1, "hours": 9 }
```

---

## DataEffect (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Description |
|---------|-----------|--------|-------------|
| `SetField` | `"setField"` | `field: String`, `value: JsonPrimitive` | Reset a declared field to a literal value |
| `SetFieldFromRef` | `"setFieldFromRef"` | `field: String`, `ref: DataValueRef` | Set a field from a resolved value ref |
| `ClearFields` | `"clearFields"` | `fields: List<String>` | Reset fields to their schema defaults. Computed fields in the list are silently skipped (their value is derived). |
| `Navigate` | `"navigate"` | `page: String`, `record: DataValueRef? = null` | Navigate to a rendered page. `record` names the `id` of the record a page that shows one opens on, resolved in the run and read through `RecordId.of`; without it the [record rules](#renderedpageactionhandler) pick one |
| `Back` | `"back"` | (none) | Navigate back |
| `IncrementField` | `"incrementField"` | `field: String`, `by: JsonPrimitive` | Increment a numeric field |
| `SetSort` | `"setSort"` | `collection: String`, `field: String`, `direction: SortDirection` (default `asc`) | Change collection sort order. JSON encoding remains `"asc"` / `"desc"` (enum names). |
| `RunMutation` | `"runMutation"` | `mutation: String` | Run the named mutation at this point, in the same batch and with the same row and clock reading; an unknown name is skipped. See [A mutation run](#a-mutation-run). |

> `SetField` and `SetFieldFromRef` coerce to the declared field type. Stringified numbers (`"42"` for a `long` field) and stringified booleans (`"true"` for a `boolean` field) are accepted. A JSON `null` clears the field: empty text, a null number, or `false`.

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
| `DateWithin` | `"dateWithin"` | `field: String`, `days: Int`: the time is between now and `days` from now |
| `DateInLast` | `"dateInLast"` | `field: String`, `days: Int`: the time is between `days` ago and now, the window `dateWithin` looks forward over |
| `IsToday` | `"isToday"` | `field: String`. Today is the **device's local calendar day** (start-of-day inclusive, next day exclusive), the same in a named condition, a computed field's `where`, and a node's `filter`. |
| `DateInPeriod` | `"dateInPeriod"` | `field: String`, `period: CalendarUnit`, `offset: Int = 0`: the time falls in the calendar period `offset` periods from the current one (0 this one, -1 the previous, 1 the next) |
| `Exists` | `"exists"` | `collection: String`, `where: DataCondition? = null`: a record of the collection satisfies `where`, or, without `where`, the collection has one. Inside `where`, `field` reads the record and `fieldRef` reads the model's fields |
| `And` | `"and"` | `operands: List<DataCondition>` |
| `Or` | `"or"` | `operands: List<DataCondition>` |
| `Not` | `"not"` | `operand: DataCondition` |

```kotlin
@Serializable
enum class CalendarUnit { day, week, month, year }   // JSON uses the entry names; weeks start on Monday
```

- Times are epoch milliseconds, as `timestamp` writes them and a `DatePicker` stores them: a number, or text holding a whole number. Days, weeks, months and years are the device's, through `RendererCalendar`.
- `collectionEmpty`, `collectionNotEmpty` and `exists` are answered only by named conditions, including inside an `exists` condition's `where`. Tested against a single record anywhere else (a node's `filter`, a computed field's `where`, a `deleteWhere` or `updateWhere` mutation's `where`) they are false.
- An `exists` depends on its collection and on the `fieldRef`s inside its `where`, never on the fields its `where` reads from records. An `Unsupported` condition inside `where` makes the whole tree false.
- A named condition reads the record its page shows through `record.<field>`, as a `field` or a `fieldRef`, including a `fieldRef` inside an `exists`'s `where`; a `deleteWhere` or `updateWhere` `where` reads it through a `record.<field>` `fieldRef` too. On a page that shows no record, or once the record is gone, those read null. `item.` in a named condition is not supported.

```json
"finished_this_year": { "type": "exists", "collection": "books",
  "where": { "type": "dateInPeriod", "field": "finished_at", "period": "year" } }
```

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
| `ReplaceCollection` | `"replaceCollection"` | `collection: String` | Replace every record, converted to the collection's declared types (see [Column types](#column-types)), with ids generated where missing or not convertible |
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
| `DataCondition.Unsupported` | Any condition tree containing one is `false`, including under `not`, in named conditions, `where`, and node `filter`s; a `deleteWhere` or `updateWhere` whose `where` holds one changes nothing |
| `ComputedField.Unsupported` | The field is a plain field holding its declared `default`; it has no dependencies |
| `RecordComputed.Unsupported` | The column reads null for every record, and a value written under its name is dropped |
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
    // A lane per (key, record) for a condition that reads record.<field>; see Record conditions below.
    override fun conditionFlow(conditionKey: String, record: PageRecord?): StateFlow<Boolean>
    override fun evaluate(conditionKey: String): Boolean
    // Advances once per settled change that changed `key`'s value, computed fields included.
    override fun revisionOf(key: String): StateFlow<Long>

    // Values convert to the declared column types (see Column types). An id that is missing or
    // does not convert is generated; deleteRecord and updateRecord convert the id they look up.
    fun insertRecord(collectionName: String, record: DataRecord)
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

Hydration reads the persistence synchronously, on the thread that builds the store, and converts every loaded value to its declared type, the way every write does (see [Column types](#column-types)). After that the store saves in the background: changes gather for 250 ms after the first unsaved one and are written in one `DataPersistence.save` call, off the main thread, so typing or toggling never waits on storage. Call `flush()` when the app goes to the background and `close()` when the store is discarded; `renderedEntries` does both. A failed save is reported through `RenderDiagnostics.onPersistenceError` and written again with the next change, `flush()` or `close()`.

Every condition and `where` is compiled once (`DataCondition.compile()`). Named conditions are evaluated against the store's fields and, for `collectionEmpty`, `collectionNotEmpty` and `exists`, its records, and answered again after a settled change to something they read (see below). A computed field whose `where` compares against another field (`fieldRef`) is recomputed when that field changes, and a computed `fieldRef` field is ordered before it. Values that depend on the time (`dateBefore`, `dateAfter`, `dateWithin`, `dateInLast`, `dateInPeriod`, `isToday`) are re-evaluated when something starts observing one of them and then each wall-clock minute while it does, on the shared `RendererClock.minutes` ticker. Computed columns that read the clock follow the date instead; see [Computed columns](#computed-columns).

**What an update recomputes.** An update (`updateRecord`, an `updateWhere` mutation, `renderer:setItemField:`) touches the columns whose values it changed, including each computed column it derived again to another value. An insert, a delete, a `replaceCollection`, or an update that moves records in the collection's order touches every column. Only what reads a touched column runs again:

- An aggregate over the collection (`sum`, `count`, `average`, `min`, `max`) is recomputed when its `field` or `where` reads a touched column, or its `where` reads the clock, and so is every computed field that reads it, through a `where`'s `fieldRef` too. A `count` without a `where` follows inserts, deletes and replaces only.
- A named condition is answered again when it reads a field that changed, or asks about the collection and reads a touched column. `collectionEmpty`, `collectionNotEmpty` and an `exists` without a `where` follow inserts, deletes and replaces only; an `exists` with a `where` also follows the columns its `where` reads. A record condition also follows the columns of its own record that its `record.<field>`s read. A condition that reads the clock is answered after every change, and every condition after a clock tick or a `setSortOrder`.

So a keystroke into a field bound to `record.<field>` recomputes only what reads that column.

**Record conditions.** `conditionFlow(key, record)` answers a condition on a page showing `record`. A condition that reads no `record.<field>`, or one asked about no record, gets the store-wide lane `conditionFlow(key)` returns. One that reads the page record gets a lane per (key, record), evaluated against the record as its collection holds it, with null for every `record.<field>` once the record is gone. A lane is evaluated when it is asked for while nothing collects it; at each settle and each clock tick it is kept, and answered again when something it reads changed, while something collects it or asked for it since the previous settle, and otherwise dropped, so ask again rather than holding a flow you are not collecting. A lane follows the clock when its condition reads the clock, a clock-dependent field, or a clock-reading computed column of the record's collection.

A collection's `orderBy` sorts mixed value types in a fixed order (missing, then booleans, numbers by value whether whole or fractional, then strings), and records that compare equal keep the order they were inserted in.

Fields declared with `"persist": false`, and fields named as any operation's `pendingField` or `failureField`, are never saved, and a value saved for one earlier is ignored on load. Each starts from its `default` after process death, so a spinner or a dialog can never come back stuck.

> **Threading:** `ReactiveDataStore` is not thread-safe. Drive it from a single thread (the UI thread in practice). Marshal back to the main dispatcher before calling in from a background coroutine.

### MutationExecutor

Executes named mutations against a `ReactiveDataStore`. The primary operation and its `then` effects, with every mutation a `runMutation` effect runs, run inside a single `ReactiveDataStore.batch`, so persistence and computed recompute happen exactly once. Navigation effects (`Navigate`, `Back`) are collected and returned for the navigation layer to act on. Building one throws `IllegalStateException` when the schema's mutations run each other; see [A mutation run](#a-mutation-run).

```kotlin
class MutationExecutor(
    store: ReactiveDataStore,
    schema: DataSchema,
) {
    // Reads the clock once for the whole run, the mutations it runs included: every timestamp in
    // its refs and effects is that reading. pageRecord is the record the running page shows: what
    // recordRef reads, as the record is when each ref resolves, and what a where's record.<field>
    // fieldRef compares against.
    fun execute(name: String, itemContext: DataRecord? = null, pageRecord: PageRecord? = null): MutationResult

    // What renderer:setItemField: runs: sets a field of the record the item context names through
    // its "_collection", a row's or a page's (inCollection), converted to its type. A context
    // without "_collection", a value that does not convert, or an undeclared field changes nothing.
    fun setItemField(itemContext: DataRecord?, field: String, value: Any?)
}

data class MutationResult(
    val navigateTo: List<PageDestination> = emptyList(),   // in the order the navigate effects ran, nested runMutation ones included
    val navigateBack: Boolean = false,
)

// A page a navigate effect opens; record is its explicit record, RecordId.of the resolved ref.
data class PageDestination(val page: String, val record: RecordId? = null)
```

### OperationExecutor

Runs a schema's operations through the host's `OperationHandler`. Clears `failureField` and sets `pendingField`, calls the handler, then applies the result, the failure code and the effects in one `batch`, resetting `pendingField` in the same batch. On cancellation it resets `pendingField` and applies nothing. The effects can run mutations, so building one throws `IllegalStateException` when the schema's mutations run each other, as building a `MutationExecutor` does.

```kotlin
class OperationExecutor(
    store: ReactiveDataStore,
    handler: OperationHandler,
    diagnostics: RenderDiagnostics,
) {
    // Call on the store's thread. Throws only CancellationException: a handler throw becomes
    // Failure(UNEXPECTED), and an effect that throws is reported, never propagated. The input and
    // the outcome's effects both read pageRecord through recordRef.
    suspend fun execute(name: String, itemContext: DataRecord? = null, pageRecord: PageRecord? = null): MutationResult
}
```

### PageOperations

The operations one page has started, with the concurrency policy applied. Create one per page, launch from the main thread, and `cancel()` it when the page leaves, so an operation the user walked away from never applies its effects or navigates.

```kotlin
class PageOperations(executor: OperationExecutor) {
    fun launch(name: String, itemContext: DataRecord?, pageRecord: PageRecord?, onSettled: (MutationResult) -> Unit)
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
    pageRecord: PageRecord? = null,               // the record the dispatching page shows; its mutations and operations run with it
    recordCollectionOf: (pageId: String) -> String?,   // a page's record collection, null for a page that shows none
    navigateToPage: (pageId: String, record: RecordId?) -> Unit,
    navigateBack: () -> Unit,
): ActionHandler
```

Every navigation, `renderer:navigate:<page>` and each `PageDestination` a mutation or operation returns, picks its record by the same rules, in order:

1. A page that declares no `record` opens with none.
2. The destination's explicit record (`navigate.record`).
3. The dispatching row's id, when the row's `_collection` (in `_itemContext`) is the page's collection.
4. `pageRecord`'s id, when its collection is the page's.
5. Otherwise none.

### DataPersistence (interface)

Optional durable storage backend. Implement with your storage engine of choice. In the navigation module, pass it as `RenderedPageConfig.dataPersistence`; each route uses its base route as the `scope`. Wrap your implementation to prefix scopes when one base route must hold separate data per user or session.

`save` and `clear` run off the main thread, one call at a time across every store, in the order the changes were made, so they may block on I/O. A write that fails should throw: the store reports the exception through `RenderDiagnostics.onPersistenceError` and offers the same changes again with its next save. The loads run on the thread that builds the store.

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
