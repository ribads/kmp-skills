# A2UI core reference

The public surface of `ui:a2ui-core` beyond what [SKILL.md](SKILL.md) covers: surfaces and their data, catalogs, functions and schemas, expressions, the node tree, reactive types and errors. Imports are listed in SKILL.md.

## Surfaces and data

```kotlin
class SurfaceGroupModel<C : ComponentApi> {
    val surfaces: Signal<List<SurfaceModel<C>>>        // in creation order
    val onSurfaceCreated: EventSource<SurfaceModel<C>>
    val onSurfaceDeleted: EventSource<String>          // the surface id
    val onAction: EventSource<RendererMessage.Action>  // every surface's
    val onError: EventSource<RendererMessage.Error>    // every surface's
    operator fun get(surfaceId: String): SurfaceModel<C>?
}

class SurfaceModel<C : ComponentApi> {
    val id: String
    val protocolVersion: ProtocolVersion
    val catalog: Catalog<C, FunctionImplementation>    // the one createSurface named
    val theme: SurfaceTheme?
    val sendDataModel: Boolean
    val formatting: Formatting
    val rootId: String                                 // always "root"
    val dataModel: DataModel
    val components: SurfaceComponentsModel<C>
    val onAction: EventSource<RendererMessage.Action>
    val onError: EventSource<RendererMessage.Error>
    val onOpenUrl: EventSource<String>                 // links an openUrl call asked for, scheme-checked
    val isDeleted: Boolean
    fun openUrl(url: String): Boolean                  // a link from the surface's content; only http, https, mailto, tel pass
    companion object { const val ROOT_ID: String = "root" }
}

data class SurfaceTheme(val json: JsonObject) {
    val primaryColor: String?      // "#RRGGBB", or null when absent or malformed
    val iconUrl: String?
    val agentDisplayName: String?  // set or verify these in an orchestrator: an agent could claim another's identity
}

class DataModel(initial: JsonElement? = null) {
    val value: JsonElement                                         // the whole document
    fun get(path: String): JsonElement?                            // null for absent and for JSON null
    fun get(pointer: JsonPointer): JsonElement?
    fun set(path: String, value: JsonElement?)                     // upsert; null removes; throws A2uiDataError
    fun set(pointer: JsonPointer, value: JsonElement?)
    fun delete(path: String)
    fun subscribe(path: String, listener: (JsonElement?) -> Unit): Subscription   // called on change, not on registration
    fun subscribe(pointer: JsonPointer, listener: (JsonElement?) -> Unit): Subscription
    fun dispose()
    companion object { const val MAX_LIST_INDEX: Int = 10_000 }
}

class SurfaceComponentsModel<C : ComponentApi> {
    val onCreated: EventSource<ComponentModel<C>>
    val onDeleted: EventSource<String>
    val all: Map<String, ComponentModel<C>>
    operator fun get(id: String): ComponentModel<C>?
}

class ComponentModel<C : ComponentApi> {
    val id: String
    val type: String
    val api: C?                                    // null when the catalog has no such component
    val properties: JsonObject                     // raw: bindings still {"path": ...}, children still ids
    val onUpdated: EventSource<ComponentModel<C>>
    fun toJson(): JsonObject
}

class JsonPointer {
    val segments: List<String>
    val isRoot: Boolean
    val parent: JsonPointer?
    fun child(segment: String): JsonPointer
    fun child(index: Int): JsonPointer
    fun contains(other: JsonPointer): Boolean
    fun overlaps(other: JsonPointer): Boolean
    companion object {
        val Root: JsonPointer
        fun parse(path: String): JsonPointer                                // throws A2uiDataError on a bad escape
        fun resolve(path: String, scope: JsonPointer = Root): JsonPointer   // relative paths against a scope
        fun isAbsolute(path: String): Boolean
        fun indexOf(segment: String): Int?
    }
}
```

Data writes follow the A2UI upsert rules: missing containers are created on the way (an index segment makes a list), writing through a string, number or boolean fails, `null` removes, and the segments `__proto__`, `constructor` and `prototype` are refused.


## Catalogs

A catalog is the contract between agent and renderer: components and functions under an id the agent names in `createSurface`.

```kotlin
class Catalog<out C : ComponentApi, out F : FunctionApi>(
    val id: String,
    components: List<C>,
    functions: List<F> = emptyList(),
    val themeSchema: ObjectSchema? = null,
    val aliases: Set<String> = emptySet(),
) {
    val components: Map<String, C>
    val functions: Map<String, F>
    fun answersTo(catalogId: String): Boolean
    fun <C2 : ComponentApi, F2 : FunctionImplementation> implementedBy(components: List<C2>, functions: List<F2>): Catalog<C2, F2>
                                         // exactly the declared names, each with the declared contract; else A2uiCatalogError.
                                         // Contracts ignore descriptions, titles, examples and how common-type $refs are spelled
    fun withId(id: String, vararg moreAliases: String): Catalog<C, F>
    fun toInlineJson(): JsonObject       // the inline form capabilities can carry
    companion object {
        fun fromJson(document: String): CatalogApi       // a published catalog JSON Schema; throws A2uiCatalogError
        fun fromJson(document: JsonObject): CatalogApi
    }
}
typealias CatalogApi = Catalog<ComponentApi, FunctionApi>

interface ComponentApi { val name: String; val schema: ObjectSchema }   // schema: the component's own properties

interface FunctionApi { val name: String; val returnType: FunctionReturnType; val args: ObjectSchema }
interface FunctionImplementation : FunctionApi {
    fun execute(args: FunctionArguments, context: FunctionContext): JsonElement?
}
fun FunctionApi.implementedBy(body: (FunctionArguments, FunctionContext) -> JsonElement?): FunctionImplementation

interface FunctionContext {
    fun resolve(value: JsonElement?): JsonElement?   // a binding, call or literal, in the caller's data scope
    val formatting: Formatting
    fun openUrl(url: String)                         // only http, https, mailto and tel reach the host; others are dropped
}
class FunctionArguments(val values: Map<String, JsonElement?>) {     // arguments already resolved
    operator fun get(name: String): JsonElement?
    fun has(name: String): Boolean
    fun string(name: String): String?
    fun number(name: String): Double?
    fun boolean(name: String): Boolean?
    fun list(name: String): List<JsonElement?>?
    fun require(function: String, name: String): JsonElement           // throws A2uiExpressionError when missing
}
enum class FunctionReturnType(val wireName: String) { String, Number, Boolean, Array, Object, Any, Void; companion object { fun of(wireName: kotlin.String?): FunctionReturnType } }

interface Formatting {
    fun formatNumber(value: Double, decimals: Int?, grouping: Boolean): String
    fun formatCurrency(value: Double, currency: String, decimals: Int?, grouping: Boolean): String   // ISO 4217 code
    fun formatDate(dateTime: LocalDateTime, pattern: String): String                                 // Unicode TR35 pattern
    fun pluralCategory(count: Double): PluralCategory
    companion object { val Default: Formatting }    // US English
}
enum class PluralCategory(val wireName: String) { Zero, One, Two, Few, Many, Other }
```

Schemas are read, never built: `Catalog.fromJson` parses the JSON Schema subset catalogs use.

```kotlin
sealed class Schema { val source: JsonObject; val description: String?; fun toJson(): JsonObject }
class StringSchema   : Schema { val enum: List<String>?; val const: String?; val pattern: String?; val default: String? }
class NumberSchema   : Schema { val integer: Boolean; val minimum: Double?; val maximum: Double?; val default: Double? }
class BooleanSchema  : Schema { val default: Boolean? }
class ArraySchema    : Schema { val items: Schema?; val minItems: Int? }
class ObjectSchema   : Schema { val properties: Map<String, Schema>; val required: Set<String>; val additionalProperties: Boolean }
class UnionSchema    : Schema { val options: List<Schema> }
class CommonTypeSchema : Schema { val type: CommonType }
class AnySchema      : Schema
enum class CommonType {
    ComponentId, ChildList, DataBinding, DynamicValue, DynamicString, DynamicNumber, DynamicBoolean,
    DynamicStringList, FunctionCall, Action, CheckRule, AccessibilityAttributes;
    val isDynamic: Boolean
}
```

The property's common type decides what a renderer receives for it (see [NodeProps](#nodeprops)): `ComponentId` and `ChildList` are children, `Dynamic*` are bindings, `Action` an action, a list of `CheckRule` the component's checks.

## BasicCatalog

```kotlin
object BasicCatalog {
    const val ID: String                      // "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
    val ALIASES: Set<String>                  // the v0_9_1 spelling, and v0_9/basic_catalog.json
    val api: CatalogApi                       // the published document: 18 components, 14 functions
    val functions: List<FunctionImplementation>   // required, regex, length, numeric, email, formatString, formatNumber,
                                                  // formatCurrency, formatDate, pluralize, openUrl, and, or, not
    fun component(name: String): ComponentApi     // throws IllegalArgumentException for an unknown name
    fun <C : ComponentApi> implementedBy(components: List<C>): Catalog<C, FunctionImplementation>
    val headless: Catalog<ComponentApi, FunctionImplementation>   // no views: validating or processing without drawing
}

object GuardedRegex {                         // the regex function's guards, for patterns a component carries
    const val MAX_PATTERN: Int = 256
    const val MAX_INPUT: Int = 10_000
    fun containsMatch(value: String, pattern: String): Boolean   // throws A2uiExpressionError for an unsafe or invalid pattern
}
```

Function behaviour matches the reference implementation: `openUrl` opens only http, https, mailto and tel links; `regex` refuses patterns that could backtrack catastrophically and stops a match after 100 ms; `formatDate` reads a timestamp's written wall-clock fields; `and` and `or` use JavaScript truthiness.

## Expressions and dynamic values

```kotlin
sealed interface DynamicValue {
    data class Literal(val value: JsonElement) : DynamicValue
    data class Binding(val path: String) : DynamicValue
    data class Call(val call: FunctionCall) : DynamicValue
    companion object {
        fun of(json: JsonElement?): DynamicValue
        fun bindingPath(json: JsonElement): String?   // the path of a {"path": ...} object, else null
    }
}
data class FunctionCall(val name: String, val args: JsonObject = JsonObject(emptyMap()), val returnType: String? = null) {
    companion object { fun of(json: JsonElement): FunctionCall? }
}
object ExpressionParser {                      // the `${...}` grammar of formatString
    const val MAX_DEPTH: Int = 100
    const val MAX_TEMPLATE_LENGTH: Int = 10_000
    const val MAX_PARTS: Int = 1_000
    fun parse(template: String): List<JsonElement>     // literal text, bindings and calls; throws A2uiParseError
    fun hasInterpolation(template: String): Boolean
}
```

## The node tree

A `NodeResolver` turns a surface's flat components and data into a live tree. `A2uiSurface` creates one; use it directly for a renderer of your own (SwiftUI, tests, a server-side snapshot).

```kotlin
class NodeResolver<C : ComponentApi>(
    val surface: SurfaceModel<C>,
    val maxNodes: Int = DEFAULT_MAX_NODES,      // past it, positions are Truncated placeholders, reported as LIMIT_EXCEEDED
) {
    val rootNode: Signal<ComponentNode<C>?>     // null until the root component arrives
    val nodeCount: Int
    val isDisposed: Boolean
    fun dispose()                               // also happens when the surface is deleted
    companion object { const val DEFAULT_MAX_NODES: Int = 10_000 }
}

class ComponentNode<C : ComponentApi> {
    val instanceId: String        // stable among siblings: key child views by it
    val id: String                // unique for this node object's life; never persist it
    val componentId: String
    val type: String              // the declared type; "Placeholder" for pending, cyclic or truncated
    val dataPath: String          // the data scope relative paths resolve in, such as "/items/2"
    val state: NodeState
    val impl: C?                  // the catalog's implementation; null for a placeholder
    val props: Signal<NodeProps<C>>   // emits once per change, with the complete new state
    val onDestroyed: EventSource<Unit>
    val isPlaceholder: Boolean
    val disposed: Boolean
    fun addCleanup(cleanup: () -> Unit)
    companion object { const val PLACEHOLDER_TYPE: String = "Placeholder" }
}
enum class NodeState { Resolved, Pending, UnknownType, Cyclic, Truncated }
```

`NodeProps`, the bindings and `NodeAction` are in [SKILL.md](SKILL.md#nodeprops).

## Errors

```kotlin
open class A2uiError(message: String, cause: Throwable? = null) : Exception
open class A2uiValidationError(message: String, val issues: List<ValidationIssue> = emptyList(), cause: Throwable? = null, val pointer: String? = null) : A2uiError
open class A2uiIntegrityError(message: String) : A2uiValidationError      // duplicate, dangling reference, missing root
open class A2uiRecursionError(message: String) : A2uiValidationError      // too deep, or a cycle
open class A2uiCatalogError(message: String) : A2uiError
open class A2uiDataError(message: String) : A2uiError
open class A2uiStateError(message: String) : A2uiError
open class A2uiParseError(message: String, cause: Throwable? = null) : A2uiError
open class A2uiExpressionError(message: String, cause: Throwable? = null) : A2uiError

data class ValidationIssue(val path: String, val code: String, val message: String) {
    companion object { const val MISSING_FIELD: String; const val INVALID_VALUE: String; const val TYPE_MISMATCH: String; const val UNKNOWN_FIELD: String }
}
```

## Reactive types

The core is synchronous and single-threaded: listeners run before the call that changed state returns.

```kotlin
interface Signal<out T> {                 // a value plus change notifications
    val value: T
    fun subscribe(listener: (T) -> Unit): Subscription   // not called on registration; read value first
}
class EventSource<T> { fun subscribe(listener: (T) -> Unit): Subscription }   // only its owning model emits
fun interface Subscription { fun unsubscribe() }   // idempotent
class SubscriptionBag : Subscription { fun add(subscription: Subscription) }
```
