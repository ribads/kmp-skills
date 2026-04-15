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

```json
{
  "type": "Scaffold",
  "topBar": {
    "type": "TopNavBar",
    "title": "Expenses",
    "leadingIcon": { "type": "back", "actionId": "navigate_back" },
    "trailingActions": [
      { "iconUrl": "ic_filter.png", "actionId": "open_filter" },
      { "label": "Save", "actionId": "save_form" }
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

## Data Layer — Full Note-Taking App

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
                  { "type": "Text", "content": "{{item.title}}", "style": "HeadingS" },
                  { "type": "Text", "content": "{{item.body}}", "style": "BodyS" }
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
