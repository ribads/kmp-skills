---
name: a2ui
description: Use when rendering agent-generated UI with the A2UI protocol (Agent-to-User Interface, v0.9 and v0.9.1) in a KMP Compose app, processing an agent's createSurface, updateComponents, updateDataModel or deleteSurface messages, drawing A2UI surfaces with Synapse components, sending user actions and errors back to an agent, advertising renderer capabilities, or adding custom A2UI components, functions and catalogs. For Synapse's own JSON screen schema use server-driven-ui instead.
user-invocable: true
---

# ui:a2ui-core + ui:a2ui: A2UI Renderer

**Modules**: `ui:a2ui-core` (protocol, state, validation, node tree; pure Kotlin) | `ui:a2ui` (Compose renderer on Synapse components)
**Artifacts**: `com.ribads.synapse:ui-a2ui-core` | `com.ribads.synapse:ui-a2ui`
**Packages**: `com.ribads.synapse.ui.a2ui.*`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-a2ui:<version>")        // the Compose renderer; brings ui-a2ui-core
    // implementation("com.ribads.synapse:ui-a2ui-core:<version>") // core alone: no UI, also on the JVM
}
```

`ui:a2ui` exposes `ui:a2ui-core`, `ui:element`, `ui:component` and Compose runtime, foundation and UI as `api` dependencies. `ui:a2ui-core` exposes `kotlinx-serialization-json`. Targets: Android, iOS, wasmJs; the core also targets the JVM.

A2UI is an open protocol in which an agent describes UI as JSON messages: a flat list of components that reference each other by id, a JSON data model they bind to, and actions that report back. The core speaks A2UI v0.9 and v0.9.1 with the published basic catalog (18 components, 14 functions), passes the protocol's conformance suites, and makes no network calls: the transport (A2A, AG-UI, SSE, a WebSocket) is the app's.

## Imports

| Package | Types |
|---|---|
| `com.ribads.synapse.ui.a2ui.basic` | `BasicCatalog`, `GuardedRegex` |
| `com.ribads.synapse.ui.a2ui.catalog` | `AnySchema`, `ArraySchema`, `BooleanSchema`, `Catalog`, `CatalogApi`, `CommonType`, `CommonTypeSchema`, `ComponentApi`, `Formatting`, `FunctionApi`, `FunctionArguments`, `FunctionContext`, `FunctionImplementation`, `FunctionReturnType`, `NumberSchema`, `ObjectSchema`, `PluralCategory`, `Schema`, `StringSchema`, `UnionSchema`, `implementedBy` |
| `com.ribads.synapse.ui.a2ui.exceptions` | `A2uiCatalogError`, `A2uiDataError`, `A2uiError`, `A2uiExpressionError`, `A2uiIntegrityError`, `A2uiParseError`, `A2uiRecursionError`, `A2uiStateError`, `A2uiValidationError`, `ValidationIssue` |
| `com.ribads.synapse.ui.a2ui.expressions` | `ExpressionParser` |
| `com.ribads.synapse.ui.a2ui.processing` | `MessageProcessor`, `ValidationConfig` |
| `com.ribads.synapse.ui.a2ui.protocol` | `DynamicValue`, `FunctionCall`, `ProtocolVersion`, `RendererMessage` |
| `com.ribads.synapse.ui.a2ui.reactive` | `EventSource`, `Signal`, `Subscription`, `SubscriptionBag` |
| `com.ribads.synapse.ui.a2ui.resolution` | `Accessibility`, `ComponentNode`, `NodeAction`, `NodeProps`, `NodeResolver`, `NodeState`, `ResolvedBinding`, `Severity`, `ValidationResult`, `WritableBinding` |
| `com.ribads.synapse.ui.a2ui.state` | `ComponentModel`, `DataModel`, `JsonPointer`, `SurfaceComponentsModel`, `SurfaceGroupModel`, `SurfaceModel`, `SurfaceTheme` |
| `com.ribads.synapse.ui.a2ui.compose` | `A2uiMedia`, `A2uiNode`, `A2uiNodeScope`, `A2uiStrings`, `A2uiSurface`, `ComposeCatalog`, `ComposeComponent`, `LocalA2uiMedia`, `LocalA2uiStrings`, `LocalA2uiSurface`, `LocalA2uiTriggerAction`, `collectAsState` |
| `com.ribads.synapse.ui.a2ui.compose.basic` | `SynapseBasicCatalog` |

`ui:a2ui-core` packages are in both artifacts; the last two rows are `ui:a2ui` only.

---

## When to use

- An agent (yours, or one reached over A2A or AG-UI) returns UI as A2UI messages, and the app draws it natively.
- A chat or assistant screen shows agent-built cards, forms and lists inline, and reports taps and input back.
- A server or test validates an agent's A2UI output against the catalog (`ui:a2ui-core` alone, `ValidationConfig.Strict`).

**A2UI or `/synapse:server-driven-ui`?** `/synapse:server-driven-ui` renders Synapse's own schema, written by your backend for your screens. A2UI is the open protocol an LLM agent writes against, with the agent's catalog as the contract. Use A2UI when an agent generates the UI.

---

## Quick start

```kotlin
// Once per conversation, on the main thread (a ViewModel, or the screen's state holder).
val processor = MessageProcessor(listOf(SynapseBasicCatalog.catalog()))

// Agent -> app: hand every A2UI message (or batch) the transport receives to the processor.
transport.incoming.collect { json -> processor.process(json) }   // errors also go to `outbound`

// App -> agent: actions and errors, with the capabilities and data model the protocol asks for.
processor.outbound.subscribe { message ->
    transport.send(
        body = message.toJsonString(),
        capabilities = processor.rendererCapabilities(),
        dataModel = processor.rendererDataModel(),
    )
}

// The screen: draw every live surface.
@Composable
fun AgentSurfaces(processor: MessageProcessor<ComposeComponent>) {
    val surfaces by processor.model.surfaces.collectAsState()
    Column { surfaces.forEach { surface -> key(surface.id) { A2uiSurface(surface = surface) } } }
}
```

`A2uiSurface` draws inside the enclosing Synapse theme (`WithAppTheme`), so agent UI looks like the rest of the app in light and dark. Send `rendererCapabilities()` with every request, so the agent knows which catalogs it may use; it advertises the basic catalog under its v0.9 id and its aliases.

---

## Processing: `ui:a2ui-core`

### MessageProcessor

```kotlin
class MessageProcessor<C : ComponentApi>(
    catalogs: List<Catalog<C, FunctionImplementation>>,             // every catalog the renderer supports
    val validation: ValidationConfig = ValidationConfig.Streaming,
    val formatting: Formatting = Formatting.Default,                 // conventions of formatNumber, formatCurrency, formatDate, pluralize
    clock: Clock = Clock.System,                                     // kotlin.time.Clock: action timestamps
) {
    val model: SurfaceGroupModel<C>                                  // the live surfaces
    val outbound: EventSource<RendererMessage>                       // every action and error bound for the agent

    fun process(json: String): List<A2uiError>                       // one message, a JSON list, or {"messages": [...]}
    fun process(payload: JsonElement): List<A2uiError>
    fun rendererCapabilities(includeInlineCatalogs: Boolean = false): JsonObject   // {"v0.9": {"supportedCatalogIds": [...]}}
    fun rendererDataModel(): JsonObject?                             // {"version", "surfaces"} for surfaces created with sendDataModel; null when none
    fun dispose()                                                    // deletes every surface, stops all events
}
```

- `process` never throws. A message that fails is rejected whole, its surface left as it was, and reported twice: in the returned list and on `outbound` as an `error` message the agent can act on. The rest of a batch still applies.
- A batch applies before anything redraws: a parent and the children the same batch defines resolve together.
- Not thread-safe. Call it, and read surfaces, on one thread, normally the main thread.
- Two catalogs with the same id throw `A2uiCatalogError` from the constructor.

### ValidationConfig

```kotlin
data class ValidationConfig(
    val validateSchemas: Boolean = true,              // check components and themes against the catalog schemas
    val allowMissingRoot: Boolean = false,
    val allowDanglingReferences: Boolean = false,
    val allowOrphanComponents: Boolean = false,
) {
    companion object {
        val Strict: ValidationConfig     // everything: for validating an agent's output, or tests
        val Streaming: ValidationConfig  // schemas, cycles and depth; partial trees accepted (the renderer default)
        val Relaxed: ValidationConfig    // envelope checks only: a trusted agent
    }
}
```

Cycles and depth (50 levels) are checked whenever schemas are. Under `Streaming` a component may reference one that has not arrived; it shows as a placeholder until it does.

Surfaces, their data and components, and the catalog types are in [core-reference.md](core-reference.md).

### Messages back to the agent

```kotlin
sealed interface RendererMessage {
    val surfaceId: String
    val version: ProtocolVersion
    fun toJson(): JsonObject          // the protocol envelope: {"version", "action"} or {"version", "error"}
    fun toJsonString(): String

    data class Action(
        val name: String,
        override val surfaceId: String,
        val sourceComponentId: String,
        val timestamp: String,        // ISO 8601
        val context: JsonObject,      // every binding resolved at the moment of the tap
        override val version: ProtocolVersion = ProtocolVersion.Latest,
    ) : RendererMessage

    data class Error(
        val code: String,
        override val surfaceId: String,
        val message: String,
        val path: String? = null,     // a JSON Pointer to the offending field for VALIDATION_FAILED
        override val version: ProtocolVersion = ProtocolVersion.Latest,
    ) : RendererMessage {
        companion object {
            const val VALIDATION_FAILED: String; const val INTEGRITY_ERROR: String; const val CATALOG_ERROR: String
            const val DATA_ERROR: String; const val EXPRESSION_ERROR: String; const val UNKNOWN_COMPONENT_TYPE: String
            const val CYCLIC_REFERENCE: String; const val PARSE_ERROR: String; const val LIMIT_EXCEEDED: String
        }
    }
}

enum class ProtocolVersion(val wireName: String) {
    V0_9, V0_9_1;
    val capabilitiesKey: String              // "v0.9" for both
    companion object {
        fun of(wireName: String?): ProtocolVersion?
        val Latest: ProtocolVersion          // V0_9_1
    }
}
```

---

## The node tree

The processor keeps each surface as flat components and data; a `NodeResolver` turns them into a live tree of `ComponentNode`s, each with resolved `props`. `A2uiSurface` creates the resolver, so a Compose app meets the tree only in its own components, through `NodeProps`. The resolver, node and catalog signatures are in [core-reference.md](core-reference.md).

- One node per referencing position: a component two parents reference is two nodes, and a template makes one node per list item, scoped to it (`node.dataPath`, such as `/items/2`).
- A node emits only when its own props change; a child's change emits on the child. A template list emits on its parent only when the list changes length.
- A reference to a component that has not arrived is a `Pending` placeholder, replaced in place when it does. An unknown type and a component that contains itself are reported to the agent once (`UNKNOWN_COMPONENT_TYPE`, `CYCLIC_REFERENCE`); a failed binding is reported as `EXPRESSION_ERROR` and resolves to nothing.

### NodeProps

What a property holds follows its schema:

| Schema | Value in `NodeProps` |
|---|---|
| `Dynamic*` | `ResolvedBinding`, or `WritableBinding` when the payload bound a path |
| `ComponentId` | `ComponentNode` |
| `ChildList`, list of `ComponentId` | `List<ComponentNode>` (ids or a template alike) |
| `Action` | `NodeAction` |
| object, list of objects | `NodeProps`, `List<NodeProps>` (resolved by the same rules) |
| `accessibility` | `Accessibility` |
| anything else | the literal `JsonElement` |

```kotlin
class NodeProps<C : ComponentApi> {
    val all: Map<String, Any?>
    val names: Set<String>
    operator fun get(name: String): Any?
    operator fun contains(name: String): Boolean
    fun binding(name: String): ResolvedBinding?
    fun writable(name: String): WritableBinding?
    fun json(name: String): JsonElement?              // a binding's value or the literal
    fun string(name: String): String?                 // these four read bindings and literals alike
    fun number(name: String): Double?
    fun boolean(name: String): Boolean?
    fun stringList(name: String): List<String>?
    fun enum(name: String): String?                   // a literal string, such as variant
    fun child(name: String): ComponentNode<C>?
    fun children(name: String): List<ComponentNode<C>>
    fun items(name: String): List<NodeProps<C>>       // a list of objects, such as Tabs.tabs
    fun action(name: String): NodeAction?
    val accessibility: Accessibility                  // Accessibility.None when absent
    val isValid: Boolean                              // false while a check of severity Error fails
    val validationErrors: List<String>                // failed Error checks' messages, in rule order
    val validationResults: List<ValidationResult>     // every failed check
    companion object {
        const val ACCESSIBILITY: String = "accessibility"; const val CHECKS: String = "checks"
        const val IS_VALID: String = "isValid"; const val VALIDATION_ERRORS: String = "validationErrors"
        const val VALIDATION_RESULTS: String = "validationResults"
    }
}

open class ResolvedBinding {                // a snapshot: a change arrives as new props
    val value: JsonElement?
    val string: String                      // "" when absent
    val number: Double?
    val boolean: Boolean
    val stringList: List<String>?
}
class WritableBinding : ResolvedBinding {   // two-way: a write lands in the data model now; nothing is sent
    val path: String                        // absolute
    fun set(value: JsonElement?)
    fun set(value: String)
    fun set(value: Boolean)
    fun set(value: Double)
    fun set(value: List<String>)
}
fun interface NodeAction { fun invoke() }    // call from the gesture; does nothing while an Error check fails
enum class Severity { Error, Warning, Info }
data class ValidationResult(val valid: Boolean, val message: String, val code: String? = null, val severity: Severity = Severity.Error)
data class Accessibility(val label: String? = null, val description: String? = null) { companion object { val None: Accessibility } }
```

A `NodeAction` resolves its payload when invoked: an `event` goes to the agent with its context as the data stands then; a `functionCall` (such as `openUrl`) runs in the client and sends nothing.

---

## Drawing: `ui:a2ui`

### A2uiSurface

```kotlin
@Composable
fun A2uiSurface(
    surface: SurfaceModel<ComposeComponent>,
    modifier: Modifier = Modifier,
    strings: A2uiStrings = A2uiStrings.Default,       // the words the renderer draws itself
    media: A2uiMedia = A2uiMedia.External,            // how Video and AudioPlayer play
    applyAgentTheme: Boolean = false,                 // the agent's primaryColor recolours primary buttons and accents
    onOpenUrl: ((url: String) -> Unit)? = null,       // null: the platform URI handler
    loading: @Composable () -> Unit = {},             // until the root arrives
)
```

It owns a `NodeResolver` for as long as it is composed. It does not scroll: put it in the screen's scrolling container. A `List` inside a container that already scrolls the same way lays out every item rather than nesting a lazy list.

### Components and catalogs

```kotlin
class ComposeComponent(
    api: ComponentApi,                                 // the contract: build it from the catalog's own entry
    val content: @Composable A2uiNodeScope.() -> Unit,
) : ComponentApi

class A2uiNodeScope {
    val node: ComponentNode<ComposeComponent>
    val props: NodeProps<ComposeComponent>             // current for this composition
    val modifier: Modifier                             // apply to the outermost layout: weight, width, accessibility
}

typealias ComposeCatalog = Catalog<ComposeComponent, FunctionImplementation>

@Composable fun A2uiNode(node: ComponentNode<ComposeComponent>, modifier: Modifier = Modifier)
                                                       // draws a child; call inside key(child.instanceId) in a list
@Composable fun <T> Signal<T>.collectAsState(): State<T>

object SynapseBasicCatalog {
    val components: List<ComposeComponent>
    fun catalog(overrides: List<ComposeComponent> = emptyList()): ComposeCatalog
                                                       // overrides replace basic components by name
}

@Immutable
data class A2uiStrings(
    val unavailable: Clause = "This content isn't available".asText(),
    val filterPlaceholder: Clause = "Search".asText(),
    val selectPlaceholder: Clause = "Select".asText(),
    val datePlaceholder: Clause = "Select a date".asText(),
    val timePlaceholder: Clause = "Select a time".asText(),
    val done: Clause = "Done".asText(),
    val invalidFormat: Clause = "Check the format".asText(),
    val playMedia: Clause = "Play".asText(),
) { companion object { val Default: A2uiStrings } }

@Stable
interface A2uiMedia {
    @Composable fun Video(url: String, modifier: Modifier)
    @Composable fun Audio(url: String, description: Clause?, modifier: Modifier)
    companion object { val External: A2uiMedia }        // a play control that opens the media outside the app
}

val LocalA2uiSurface: ProvidableCompositionLocal<SurfaceModel<ComposeComponent>>
val LocalA2uiStrings: ProvidableCompositionLocal<A2uiStrings>
val LocalA2uiMedia: ProvidableCompositionLocal<A2uiMedia>
val LocalA2uiTriggerAction: ProvidableCompositionLocal<(() -> Unit)?>   // a tappable component calls this instead of its action while set
```

### How the basic catalog draws

Every visible component keeps an 8 dp margin (`Theme.spacing.x2`) and containers add none, so nesting rows and columns never adds space.

| Component | Synapse rendering |
|---|---|
| Text | `Text` in the variant's role (`h1`-`h4`, `h5` as `headingM`, `caption` as `bodyS` in `element.secondary`); Markdown inline styles and links, headings bold, bullets as `•` |
| Image | `Image(Image.Bitmap(url))` for http and https URLs only: `icon` 24 dp, `avatar` 40 dp circle, `smallFeature` 100 dp, `mediumFeature` width up to 300 dp at 4:3, `largeFeature` full width at 16:9, `header` 200 dp tall; `fill` and `cover` crop. A feature image in a row without a weight is a 100 dp thumbnail |
| Icon | the 59 basic names as Lucide glyphs (Synapse's stroke style), 24 dp in the content colour; an `svgPath` is filled |
| Video, AudioPlayer | `A2uiMedia`, given http and https URLs only |
| Row | a flex row: children keep their natural widths, shrink together down to their longest word when crowded, and weights share what is left; `align: stretch` matches heights |
| Column | weights share the height when the column has one; in a scrolling host every child keeps its natural height |
| List | `LazyColumn` or `LazyRow` with a bounded length to scroll in, otherwise every item laid out |
| Card | `Card`; a card inside a card is an outline |
| Tabs | `TabLayout`, showing the selected tab's child |
| Divider | `Divider` in `border.secondary`; vertical is a 1 dp line |
| Modal | the trigger; tapping it opens the content in a `Tray` |
| Button | `primary`: `PrimaryButton`, `default`: `OutlineButton`, `borderless`: a link in the accent. A `Text` child becomes the title, an `Icon` child an icon button, a `Row` of a `Text` between icons a title with images; any other child is drawn inside. Disabled while a check fails |
| TextField | `LabelTextField` (`number`: numeric keyboard), `longText`: `TextArea`, `obscured`: `PasswordTextField`; checks and `validationRegexp` show in the footer once the user has typed |
| CheckBox | `LabelCheckbox` |
| ChoicePicker | `chips`: `ChipGroup`; otherwise checkboxes for `multipleSelection`, `RadioGroup` for `mutuallyExclusive` (a `DropdownSelectionField` past six options); `filterable` adds a search field |
| Slider | `Slider`, showing the value beside its label; a whole-number range at least 10 wide moves in whole steps |
| DateTimeInput | `SelectionTextField`s opening `DatePickerBottomSheet` and a `TimePicker` tray; reads and writes ISO 8601 (`2025-07-15`, `19:00`, or both; an instant stays an instant) |

Inside a `bottomSheet()` destination or a `NavContainer`, trays take the app's sheet look; elsewhere provide `LocalBottomSheetAppearance provides ThemedBottomSheetAppearance` (see `/synapse:ui-components`).

---

## Custom components and catalogs

An agent may use your own components and functions when you publish a catalog for them. A surface uses exactly one catalog, the one its `createSurface` names, so a catalog of your own also holds the basic components and functions the agent should keep using: copy their definitions from the basic catalog document (reworded descriptions and relative `common_types.json#/$defs/...` references are fine), add yours, give the document to the agent, and implement it from the same document so the two cannot drift:

```kotlin
val shopApi = Catalog.fromJson(shopCatalogJson)          // copied basic components + ProductTile + applyDiscount

private val AddToCart = ButtonModel(title = Text.Localized(Res.string.add_to_cart))

val ProductTile = ComposeComponent(shopApi.components.getValue("ProductTile")) {
    val name = props.string("name").orEmpty()
    val nameClause = remember(name) { name.asText() }    // agent text arrives at composition: remember what you build from it
    val addToCart = props.action("action")
    Card(modifier = modifier.padding(Theme.spacing.x2)) {
        Column(modifier = Modifier.padding(Theme.spacing.x4)) {
            Text(clause = nameClause, style = Theme.typography.headingM)
            props.child("badge")?.let { badge -> A2uiNode(badge) }   // children are nodes: draw them with A2uiNode
            PrimaryButton(
                model = AddToCart,
                state = if (addToCart != null && props.isValid) ButtonState.Enabled else ButtonState.Disabled,
                onClick = { addToCart?.invoke() },
            )
        }
    }
}

val applyDiscount = shopApi.functions.getValue("applyDiscount").implementedBy { args, _ ->
    val price = args.number("price") ?: throw A2uiExpressionError("applyDiscount: price is not a number")
    val percent = args.number("percent") ?: throw A2uiExpressionError("applyDiscount: percent is not a number")
    JsonPrimitive(price * (100 - percent) / 100)
}

val shop: ComposeCatalog = shopApi.implementedBy(
    components = SynapseBasicCatalog.components.filter { it.name in shopApi.components } + ProductTile,
    functions = BasicCatalog.functions.filter { it.name in shopApi.functions } + applyDiscount,
)
val processor = MessageProcessor(listOf(SynapseBasicCatalog.catalog(), shop))   // surfaces pick one by catalogId
```

- `implementedBy` compares contracts, not wording: descriptions, titles and examples may differ, and common-type references may be relative or absolute. A copy that changes a contract (an enum value, a required property, a property's type) is refused with `A2uiCatalogError`.
- A function receives its arguments resolved, returns synchronously, and throws `A2uiExpressionError` for arguments it can't use; the agent hears an `EXPRESSION_ERROR` and the value is absent. A call in a `DynamicString` property must return a string: wrap numbers with `formatNumber` or `formatCurrency`.
- Advertise the catalog with `rendererCapabilities()`; with `includeInlineCatalogs = true` it also carries `toInlineJson()` for agents that accept inline catalogs.
- Replace a basic component with your own by building it from the basic contract: `SynapseBasicCatalog.catalog(overrides = listOf(ComposeComponent(BasicCatalog.component("Button")) { ... }))`.
- Read props through `NodeProps`; never read `ComponentModel.properties` in a view. Write user input through `WritableBinding.set`, and invoke a `NodeAction` synchronously from the gesture.
- Apply `modifier` to the outermost layout, colours from `Theme.colors` roles, and the leaf margin (`Theme.spacing.x2`) to visible components, as `/synapse:component-authoring` describes.
- A component that fires an action on tap reads `LocalA2uiTriggerAction` first, so it can be a Modal's trigger.

---

## Rules

1. **One thread.** Process messages, read surfaces and invoke actions on the main thread.
2. **Never parse A2UI yourself.** Hand every message to `MessageProcessor.process` and draw what it builds; it validates, reports errors to the agent, and keeps partial trees consistent.
3. **Send what `outbound` emits.** Actions and errors are how the agent hears the user and corrects itself. Attach `rendererCapabilities()` to every request and `rendererDataModel()` when it is not null.
4. **Catalogs come from their documents.** Implement components and functions from `Catalog.fromJson` or `BasicCatalog`; `implementedBy` refuses an implementation that drifts from the schema the agent sees.
5. **Treat agent content as untrusted.** Links open only through the scheme policy, media loads only over http and https, regexes are guarded, the tree and data are bounded. Set or verify `SurfaceTheme.agentDisplayName` and `iconUrl` in an orchestrator before showing them as an identity.
6. **Let the app's theme win.** Leave `applyAgentTheme` off unless the agent's brand colour belongs in your UI.
