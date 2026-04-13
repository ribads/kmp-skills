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
| `ImagePicker` | `bind`, `placeholder` |
| `Checkbox` | `checked`, `label`, `stateKey`, `onCheckedChangeActionId` |
| `RadioButton` | `selected`, `label`, `stateKey`, `onSelectedChangeActionId` |
| `Switch` | `checked`, `label`, `stateKey`, `onCheckedChangeActionId` |

### Chart Nodes

| Type | Key fields |
|------|-----------|
| `BarChart` | `series` (List\<UIChartSeries\>), `title`, `showGrid`, `showValues`, `animate`, `cornerRadius` |
| `LineChart` | `series` (List\<UIChartSeries\>), `title`, `showGrid`, `showDots`, `smoothCurve`, `showArea`, `animate`, `lineWidth`, `dotRadius` |
| `PieChart` | `slices` (List\<UIPieSlice\>), `title`, `donutFraction`, `showPercentages`, `showLegend`, `animate` |

**UIChartSeries**: `entries` (List\<UIChartEntry\>), `label` (String?), `color` (hex String?)
**UIChartEntry**: `value` (Float), `label` (String)
**UIPieSlice**: `value` (Float), `label` (String?), `color` (hex String?)

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

### Chart JSON

```json
{
  "type": "BarChart",
  "title": "Monthly Revenue",
  "modifier": { "fillMaxWidth": true, "padding": 16 },
  "series": [
    {
      "label": "2024",
      "color": "#4CAF50",
      "entries": [
        { "value": 120, "label": "Jan" },
        { "value": 180, "label": "Feb" },
        { "value": 95, "label": "Mar" }
      ]
    }
  ],
  "showValues": true
}
```

```json
{
  "type": "PieChart",
  "title": "Allocation",
  "slices": [
    { "value": 40, "label": "Stocks", "color": "#2196F3" },
    { "value": 35, "label": "Bonds", "color": "#4CAF50" },
    { "value": 25, "label": "Cash", "color": "#FF9800" }
  ],
  "donutFraction": 0.5
}
```

Extensible via `NodeRendererRegistry` for custom node types.

---

## Data-Bound Node Extensions

These fields were added to existing node types for data layer integration.

### LazyColumn (data-bound mode)

| Field | Type | Description |
|-------|------|-------------|
| `dataSource` | `String?` | Collection name to bind to. When set, children are ignored and `itemTemplate` is rendered per record. |
| `itemTemplate` | `UINode?` | Node tree rendered for each record. Supports `{{item.field}}` template interpolation. |

### Button Nodes (all 4 types)

| Field | Type | Description |
|-------|------|-------------|
| `stateCondition` | `String?` | Named condition key. When set, button is `Enabled` when condition is true, `Disabled` when false. Overrides `state`. |

### Input Nodes (TextField, PasswordField, CurrencyField, TextArea)

| Field | Type | Description |
|-------|------|-------------|
| `bind` | `String?` | Declared field name to bind to. Preferred over `stateKey` when using the data layer. |

### Template Interpolation

Inside `itemTemplate` nodes, text content supports `{{item.field}}` patterns that resolve to the current record's field value at render time.

---

## Declarative Data Layer

**Module**: `ui:renderer-data` | **Artifact**: `com.ribads.synapse:ui-renderer-data`
**Package**: `com.ribads.synapse.ui.renderer.data`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-renderer-data:<version>")
}
```

Depends on `ui:renderer` and Compose Runtime.

The data layer lets JSON schemas declare typed fields, collections, mutations, and conditions. The renderer binds to this data reactively — no Kotlin code needed for data operations.

### Architecture

```
Schema types (ui:renderer)          ← serializable declarations
    ↓
Runtime (ui:renderer-data)          ← ReactiveDataStore, MutationExecutor, SchemaConditionEvaluator
    ↓
Navigation wiring (ui:renderer-navigation)  ← automatic setup in renderedComposable
```

### DataSchema

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

### DataField

```kotlin
@Serializable
data class DataField(
    val type: DataFieldType,       // string, long, boolean
    val default: JsonPrimitive? = null,
)

@Serializable
enum class DataFieldType { string, long, boolean }
```

### DataCollection

```kotlin
@Serializable
data class DataCollection(
    val schema: Map<String, String> = emptyMap(),  // field name → type name
    val orderBy: DataOrderBy? = null,
)

@Serializable
data class DataOrderBy(
    val field: String,
    val direction: SortDirection = SortDirection.asc,
)

@Serializable
enum class SortDirection { asc, desc }
```

### DataMutation (sealed, discriminator `"type"`)

| Variant | SerialName | Key fields |
|---------|-----------|-----------|
| `Insert` | `"insert"` | `collection: String`, `record: Map<String, DataValueRef>`, `then: List<DataEffect>` |
| `Delete` | `"delete"` | `collection: String`, `id: DataValueRef`, `then: List<DataEffect>` |
| `Update` | `"update"` | `collection: String`, `id: DataValueRef`, `values: Map<String, DataValueRef>`, `then: List<DataEffect>` |
| `Trigger` | `"trigger"` | `then: List<DataEffect>` (effects-only, no collection operation) |

Triggered from UI via `"actionId": "mutation:<name>"`.

### DataValueRef (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Description |
|---------|-----------|--------|-------------|
| `FieldRef` | `"fieldRef"` | `name: String` | Current value of a declared field |
| `Literal` | `"literal"` | `value: JsonPrimitive` | Hard-coded value |
| `Timestamp` | `"timestamp"` | — | Current epoch milliseconds |
| `UuidRef` | `"uuid"` | — | Random UUID string |
| `ItemRef` | `"itemRef"` | `path: String` | Value from current item context (inside `itemTemplate`) |

### DataEffect (sealed, discriminator `"type"`)

| Variant | SerialName | Fields | Description |
|---------|-----------|--------|-------------|
| `SetField` | `"setField"` | `field: String`, `value: JsonPrimitive` | Reset a declared field |
| `SetFieldFromRef` | `"setFieldFromRef"` | `field: String`, `ref: DataValueRef` | Set a field from a resolved value ref |
| `Navigate` | `"navigate"` | `page: String` | Navigate to a rendered page |

### DataCondition (sealed, discriminator `"type"`)

| Variant | SerialName | Fields |
|---------|-----------|--------|
| `FieldNotEmpty` | `"fieldNotEmpty"` | `field: String` |
| `FieldEmpty` | `"fieldEmpty"` | `field: String` |
| `CollectionNotEmpty` | `"collectionNotEmpty"` | `collection: String` |
| `CollectionEmpty` | `"collectionEmpty"` | `collection: String` |
| `Equals` | `"equals"` | `field: String`, `value: JsonPrimitive` |
| `And` | `"and"` | `operands: List<DataCondition>` |
| `Or` | `"or"` | `operands: List<DataCondition>` |
| `Not` | `"not"` | `operand: DataCondition` |

---

### Runtime Classes

#### ReactiveDataStore

`@Stable` class that materializes a `DataSchema` into reactive Compose state. Implements `RendererStateHolder`.

```kotlin
@Stable
class ReactiveDataStore(
    val schema: DataSchema,
    private val persistence: DataPersistence? = null,
    private val scope: String = "default",
) : RendererStateHolder {
    fun getCollection(name: String): State<List<DataRecord>>
    fun insertRecord(collectionName: String, record: DataRecord)
    fun deleteRecord(collectionName: String, recordId: Any?)
    fun updateRecord(collectionName: String, recordId: Any?, values: Map<String, Any?>)
    fun collectionSize(name: String): Int
    fun readField(name: String): Any?
    override fun clear()
    // + all RendererStateHolder methods (getOrPutString, putString, getString, etc.)
}
```

#### MutationExecutor

Executes named mutations against a `ReactiveDataStore`. Returns navigation targets from `DataEffect.Navigate`.

```kotlin
class MutationExecutor(
    private val store: ReactiveDataStore,
    private val schema: DataSchema,
) {
    fun execute(name: String, itemContext: DataRecord? = null): List<String>
}
```

#### SchemaConditionEvaluator

Evaluates `DataCondition` trees against live store state. Implements `ConditionEvaluator`.

```kotlin
class SchemaConditionEvaluator(
    private val store: ReactiveDataStore,
    private val schema: DataSchema,
) : ConditionEvaluator {
    override fun evaluate(conditionKey: String): Boolean
}
```

#### DataPersistence (interface)

Optional durable storage backend. Implement with your storage engine of choice.

```kotlin
interface DataPersistence {
    fun saveField(scope: String, fieldName: String, value: Any?)
    fun saveCollection(scope: String, collectionName: String, records: List<DataRecord>)
    fun loadFields(scope: String): Map<String, Any?>
    fun loadCollection(scope: String, collectionName: String): List<DataRecord>
    fun clear(scope: String)
}

typealias DataRecord = Map<String, Any?>
```

#### CollectionProvider (fun interface)

Provides reactive collection access to the renderer. Automatically wired from `ReactiveDataStore` in `renderedComposable`.

```kotlin
fun interface CollectionProvider {
    fun getCollection(name: String): State<List<Map<String, Any?>>>
    companion object { val Empty: CollectionProvider }
}

const val ITEM_CONTEXT_PAYLOAD_KEY = "_itemContext"
```

#### ConditionEvaluator (fun interface)

Evaluates named boolean conditions. Automatically wired from `SchemaConditionEvaluator` in `renderedComposable`.

```kotlin
fun interface ConditionEvaluator {
    fun evaluate(conditionKey: String): Boolean
    companion object { val AlwaysFalse: ConditionEvaluator }
}
```

#### MediaProvider (fun interface)

Abstraction for picking images from the device. The consumer provides the implementation using platform-specific APIs (e.g. `core:file`'s `FilePicker`). Used by the `ImagePicker` node.

```kotlin
fun interface MediaProvider {
    suspend fun pickImage(): String?   // returns stable file path/URI, or null if cancelled
    companion object { val NoOp: MediaProvider }
}
```

---

### SynapseRenderer (updated signatures)

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

---

## Multi-Page Navigation with Data

**Module**: `ui:renderer-navigation` | **Artifact**: `com.ribads.synapse:ui-renderer-navigation`

### UIScreen

```kotlin
@Serializable
data class UIScreen(
    val startPage: String? = null,
    val data: DataSchema? = null,       // ← data layer declaration
    val pages: List<UIPage> = emptyList(),
) {
    val entryPage: String?
}

@Serializable
data class UIPage(val id: String, val root: UINode)

fun String.toUIScreen(): UIScreen
```

### renderedComposable

When `dataSchema` is provided, `ReactiveDataStore`, `MutationExecutor`, `SchemaConditionEvaluator`, and `CollectionProvider` are created automatically. The `mutation:` action prefix is intercepted and routed to the executor.

```kotlin
fun NavGraphBuilder.renderedComposable(
    baseRoute: String,
    schemaStore: SchemaStore,
    actionHandler: ActionHandler,
    navigationDispatcher: NavigationDispatcher,
    registry: NodeRendererRegistry = NodeRendererRegistry.defaults(),
    conditionEvaluator: ConditionEvaluator = ConditionEvaluator.AlwaysFalse,
    stateHolder: RendererStateHolder = RendererStateHolder(),
    dataSchema: DataSchema? = null,
    mediaProvider: MediaProvider = MediaProvider.NoOp,
    onPageNotFound: (@Composable (pageId: String) -> Unit)? = null,
)
```

**Built-in action prefixes:**
- `renderer:navigate:<pageId>` — navigates to another rendered page
- `renderer:back` — pops the back stack
- `mutation:<name>` — executes a declared data mutation

---

## Data Layer JSON Example

A note-taking app with two pages, reactive collections, and conditional UI:

```json
{
  "startPage": "notes_list",
  "data": {
    "fields": {
      "new_note_title": { "type": "string" },
      "new_note_body": { "type": "string" }
    },
    "collections": {
      "notes": {
        "schema": { "id": "string", "title": "string", "body": "string", "createdAt": "long" },
        "orderBy": { "field": "createdAt", "direction": "desc" }
      }
    },
    "mutations": {
      "save_note": {
        "type": "insert",
        "collection": "notes",
        "record": {
          "title": { "type": "fieldRef", "name": "new_note_title" },
          "body": { "type": "fieldRef", "name": "new_note_body" },
          "createdAt": { "type": "timestamp" }
        },
        "then": [
          { "type": "setField", "field": "new_note_title", "value": "" },
          { "type": "setField", "field": "new_note_body", "value": "" },
          { "type": "navigate", "page": "notes_list" }
        ]
      },
      "delete_note": {
        "type": "delete",
        "collection": "notes",
        "id": { "type": "itemRef", "path": "id" }
      }
    },
    "conditions": {
      "can_save": {
        "type": "and",
        "operands": [
          { "type": "fieldNotEmpty", "field": "new_note_title" },
          { "type": "fieldNotEmpty", "field": "new_note_body" }
        ]
      },
      "has_notes": { "type": "collectionNotEmpty", "collection": "notes" }
    }
  },
  "pages": [
    {
      "id": "notes_list",
      "root": {
        "type": "Column",
        "children": [
          {
            "type": "LazyColumn",
            "modifier": { "weight": 1 },
            "dataSource": "notes",
            "itemTemplate": {
              "type": "Card",
              "actionId": "mutation:delete_note",
              "children": [
                { "type": "Text", "content": "{{item.title}}", "style": "HeadingS" },
                { "type": "Text", "content": "{{item.body}}", "style": "BodyS" }
              ]
            }
          },
          {
            "type": "PrimaryButton",
            "title": "Add Note",
            "actionId": "renderer:navigate:add_note"
          }
        ]
      }
    },
    {
      "id": "add_note",
      "root": {
        "type": "Column",
        "modifier": { "padding": 16 },
        "children": [
          { "type": "TextField", "label": "Title", "bind": "new_note_title" },
          { "type": "TextArea", "label": "Body", "bind": "new_note_body" },
          {
            "type": "PrimaryButton",
            "title": "Save",
            "actionId": "mutation:save_note",
            "stateCondition": "can_save"
          },
          {
            "type": "OutlineButton",
            "title": "Cancel",
            "actionId": "renderer:back"
          }
        ]
      }
    }
  ]
}
```
