# JSON Examples

## Basic Layout

```json
{
  "type": "Column",
  "modifier": { "fillMaxWidth": true, "padding": 16 },
  "children": [
    { "type": "Text", "content": "Transfer complete", "style": "HeadingM", "textFormat": { "intent": "Success" } },
    { "type": "MoneyText", "amount": 249999, "currency": "GBP", "style": "H1" },
    { "type": "Spacer", "modifier": { "height": { "type": "fixed", "dp": 24 } } },
    { "type": "PrimaryButton", "title": "Done", "actionId": "dismiss" }
  ]
}
```

---

## TopNavBar

Both actions have icons, so both render as icons and announce their labels. Had `Save` been label-only, the bar would show only `Save`, as text (see the TopNavBar rules in nodes-reference.md).

```json
{
  "type": "Scaffold",
  "topBar": {
    "type": "TopNavBar",
    "title": "Expenses",
    "leadingIcon": { "type": "back", "actionId": "navigate_back" },
    "trailingActions": [
      { "iconUrl": "ic_filter.png", "label": "Filter", "actionId": "open_filter" },
      { "iconUrl": "ic_save.png", "label": "Save", "actionId": "save_form" }
    ]
  },
  "content": [
    { "type": "Text", "content": "Screen body" }
  ]
}
```

---

## Charts

### Bar Chart

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

### Pie Chart

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

---

## Conditional

A `Conditional` draws no layout of its own, so its branch takes its place in the parent: a `weight` on the branch works when the `Conditional` sits directly in a `Row` or `Column`.

```json
{
  "type": "Conditional",
  "conditionKey": "has_notes",
  "thenNode": {
    "type": "LazyColumn",
    "dataSource": "notes",
    "itemTemplate": {
      "type": "Card",
      "children": [
        { "type": "Text", "content": "{{item.title}}", "style": "HeadingS" }
      ]
    }
  },
  "elseNode": {
    "type": "EmptyState",
    "title": "No notes yet",
    "subtitle": "Tap the button below to add one",
    "actionLabel": "Add Note",
    "actionId": "renderer:navigate:add_note"
  }
}
```

---

## Data Layer: Full Note-Taking App

A multi-page app with reactive collections, computed fields, mutations, and conditional UI:

```json
{
  "startPage": "notes_list",
  "data": {
    "fields": {
      "new_note_title": { "type": "string" },
      "new_note_body": { "type": "string" },
      "total_notes": { "type": "long", "computed": { "type": "count", "collection": "notes" } }
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
          { "type": "clearFields", "fields": ["new_note_title", "new_note_body"] },
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
            "type": "Conditional",
            "conditionKey": "has_notes",
            "thenNode": {
              "type": "LazyColumn",
              "modifier": { "weight": 1 },
              "dataSource": "notes",
              "itemTemplate": {
                "type": "Card",
                "actionId": "mutation:delete_note",
                "children": [
                  {
                    "type": "Column",
                    "children": [
                      { "type": "Text", "content": "{{item.title}}", "style": "HeadingS" },
                      { "type": "Text", "content": "{{item.body}}", "style": "BodyS" }
                    ]
                  }
                ]
              }
            },
            "elseNode": {
              "type": "EmptyState",
              "title": "No notes yet",
              "subtitle": "Tap below to add your first note"
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

---

## Operations: Load on Appear, Submit with Loading and Failure

The list page loads through `OnAppear`; the form page submits with a loading button and shows copy chosen from the failure code. The host binds `list_tasks` and `add_task` through its `OperationHandler`.

```json
{
  "requires": { "minSchemaVersion": 2 },
  "data": {
    "fields": {
      "loading_tasks": { "type": "boolean" },
      "new_task_title": { "type": "string" },
      "saving": { "type": "boolean" },
      "save_error": { "type": "string" }
    },
    "collections": { "tasks": { "schema": { "id": "string", "title": "string" } } },
    "conditions": {
      "is_loading": { "type": "isTrue", "field": "loading_tasks" },
      "is_saving": { "type": "isTrue", "field": "saving" },
      "can_save": { "type": "fieldNotEmpty", "field": "new_task_title" },
      "save_failed_offline": { "type": "equals", "field": "save_error", "value": "offline" }
    },
    "operations": {
      "list_tasks": {
        "pendingField": "loading_tasks",
        "result": { "type": "replaceCollection", "collection": "tasks" }
      },
      "add_task": {
        "input": { "title": { "type": "fieldRef", "name": "new_task_title" } },
        "pendingField": "saving",
        "failureField": "save_error",
        "result": { "type": "replaceCollection", "collection": "tasks" },
        "onSuccess": [ { "type": "clearFields", "fields": ["new_task_title"] }, { "type": "back" } ]
      }
    }
  },
  "pages": [
    { "id": "tasks", "root": { "type": "Column", "children": [
      { "type": "OnAppear", "actionIds": ["operation:list_tasks"] },
      { "type": "Conditional", "conditionKey": "is_loading",
        "thenNode": { "type": "Text", "content": "Loading tasks…" },
        "elseNode": { "type": "LazyColumn", "dataSource": "tasks",
          "itemTemplate": { "type": "Text", "content": "{{item.title}}" } } },
      { "type": "PrimaryButton", "title": "Add task", "actionId": "renderer:navigate:add_task" }
    ] } },
    { "id": "add_task", "root": { "type": "Column", "children": [
      { "type": "TextField", "label": "Title", "bind": "new_task_title" },
      { "type": "PrimaryButton", "title": "Save", "actionId": "operation:add_task",
        "stateCondition": "can_save", "loadingCondition": "is_saving" },
      { "type": "Conditional", "conditionKey": "save_failed_offline",
        "thenNode": { "type": "Text", "content": "You're offline. Try again." } }
    ] } }
  ]
}
```

Host side, with `renderedEntries`:

```kotlin
renderedEntry(
    baseRoute = "tasks",
    schemaStore = InMemorySchemaStore().apply { load(screen) },
    actionHandler = handler,
    navigationDispatcher = dispatcher,
    config = RenderedPageConfig(dataSchema = screen.data, operationHandler = tasksOperationHandler),
)
```

---

## Gateway Operation Handler

One handler that forwards every operation to your backend, so new operations ship without an app release. It lives in the feature's `ui` module and goes through a use case, so the request goes through the app's single `HttpClient` (`/synapse:network`) with its base URL and auth, and failures are classified in the repository like any other call (`/synapse:data-boundaries`). The domain sees the payload as opaque JSON text; parsing the returned records is a UI-layer concern, like `parseUIScreen`.

```kotlin
// features/<name>/ui
internal class GatewayOperationHandler(
    private val runOperation: RunSduiOperationUseCase,   // POST sdui/operations/{name} with the JSON body
) : OperationHandler {

    override suspend fun execute(name: String, input: ActionPayload): OperationOutcome =
        when (val result = runOperation.execute(name, input.toJsonObject().toString())) {
            is SduiOperationResult.Success -> OperationOutcome.Success(result.recordsJson.toRecords())
            is SduiOperationResult.Failure -> OperationOutcome.Failure(result.code)   // "offline", "unauthorized", or a server code
        }

    private fun String.toRecords(): List<DataRecord> =
        Json.decodeFromString<List<Map<String, JsonPrimitive>>>(this)
}
```

Keep native bindings for operations that are not HTTP calls (purchase, restore, share) by matching their names before falling through to the gateway, and list those names in `RendererCapabilities(operations = …)`.

## Tabs, Sections and Row Checkboxes: a Packing List

The tab bar comes from `navigation.tabs`, not from a node; each tab keeps its own stack of pages. The checkbox in each row sets `packed` on that row's record, so no mutation is needed, and `requires` asks for the schema version these need.

```json
{
  "requires": { "minSchemaVersion": 3 },
  "theme": { "brand": "#1B2A4A", "neutral": "Warm" },
  "navigation": { "tabs": [
    { "page": "trip", "label": "Trip", "icon": "map" },
    { "page": "packing", "label": "Packing", "icon": "luggage" }
  ] },
  "data": {
    "collections": {
      "packing": {
        "schema": { "name": "string", "packed": "boolean" },
        "initialData": [ { "name": "Passports", "packed": false }, { "name": "Umbrella", "packed": true } ]
      }
    }
  },
  "pages": [
    { "id": "trip", "root": { "type": "Text", "content": "Paris and Lyon", "style": "H1" } },
    {
      "id": "packing",
      "root": {
        "type": "Scaffold",
        "topBar": { "type": "TopNavBar", "title": "Packing" },
        "content": [ {
          "type": "Column",
          "modifier": { "verticalScroll": true, "paddingStart": 16, "paddingEnd": 16 },
          "children": [
            {
              "type": "Section", "title": "To pack", "grouped": true, "dataSource": "packing",
              "filter": { "type": "isFalse", "field": "packed" }, "emptyText": "All packed",
              "itemTemplate": { "type": "ListItem", "title": "{{item.name}}", "check": "item.packed" }
            },
            {
              "type": "Section", "title": "Packed", "grouped": true, "dataSource": "packing",
              "filter": { "type": "isTrue", "field": "packed" },
              "itemTemplate": { "type": "ListItem", "title": "{{item.name}}", "check": "item.packed" }
            }
          ]
        } ]
      }
    }
  ]
}
```
