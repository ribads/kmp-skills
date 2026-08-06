---
name: navigation
description: Use when implementing screen navigation, typed routes, feature modules, back-stack results, or Compose navigation in a KMP project.
user-invocable: true
---

# ui:compose-presentation — Navigation & State Management

**Module**: `ui:compose-presentation` | **Artifact**: `com.ribads.synapse:ui-compose-presentation`
**Package**: `com.ribads.synapse.ui.compose.presentation`

Built on **Jetpack Navigation 3** (`org.jetbrains.androidx.navigation3`). You own a typed back stack of `NavKey`s; the library wires the `NavDisplay`, entry-scoped ViewModels, saved state, scenes, and transitions, and exposes a small command-based seam (`NavigationDispatcher`) so screens stay decoupled from the engine.

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-compose-presentation:<version>")
}
```

Consumer modules that declare destinations also need the kotlinx-serialization plugin (routes are `@Serializable`):

```kotlin
plugins { alias(libs.plugins.kotlinSerialization) }
```

---

## Destinations are typed keys

A destination is an `@Serializable` type implementing `NavKey`, carrying its arguments as properties. No string routes, no argument bags.

```kotlin
typealias NavKey = androidx.navigation3.runtime.NavKey  // re-exported from Synapse

@Serializable data object HomeRoute : NavKey
@Serializable data class DetailRoute(val id: String) : NavKey
```

Each feature exposes a `SerializersModule` registering its keys polymorphically so they survive saved-state serialization on iOS/web (no reflection on native):

```kotlin
val serializers = SerializersModule {
    polymorphic(NavKey::class) {
        subclass(HomeRoute::class)
        subclass(DetailRoute::class)
    }
}
```

## Flows

Navigation is organised as a tree of flows. A `NavFlow` is a named group of destinations that is entered, closed, completed, and returns results as one unit; a feature is the root flow of its subtree and may nest child flows to any depth (a create feature hosting category and shipping sub-flows; a checkout flow hosting a wallet flow).

There is still exactly one flat back stack. Every `NavKey` class is owned by the flow whose `serializers` module registers it (one flow per key class; the host fails fast at startup on violations), and flow-scoped commands resolve the nearest enclosing flow of the visible destination from that ownership at dispatch time. A flow therefore closes correctly no matter how or where it was entered, including cross-feature launches and entry at a non-start destination.

```kotlin
interface NavFlow {
    val flowName: String                             // unique across the whole tree
    val startKey: NavKey                             // pushed when entered by name (FeatureCommand)
    val serializers: SerializersModule               // this flow's own keys only; also the ownership record
    val childFlows: List<NavFlow> get() = emptyList()
    fun EntryProviderScope<NavKey>.register(dispatcher: NavigationDispatcher)
}
```

## NavigationCommand

```kotlin
sealed interface NavigationCommand {
    data class ScreenCommand(val key: NavKey, val clearStack: Boolean = false) : NavigationCommand
    data class BackCommand(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class CloseFlow(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class CloseFeature(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class FlowCompletionCommand(val key: NavKey) : NavigationCommand
    data class FeatureCommand(val featureName: String, val clearStack: Boolean = false) : NavigationCommand
    data class ExternalUriCommand(val uri: String) : NavigationCommand
}
```

- `ScreenCommand`: push `key`; with `clearStack`, reset the back stack so `key` becomes the only (root) entry.
- `BackCommand`: pop the current destination, delivering `result` to the one beneath. No-op on the last entry.
- `CloseFlow`: pop the nearest enclosing flow of the current destination (its contiguous run of entries, including any of its sub-flows'), delivering `result` to the revealed destination. The revealed destination may belong to any flow: a flow launched from another feature returns its result to the launching screen. No-op when the run spans the whole stack; throws `IllegalStateException` if no flow owns the current destination's key class.
- `CloseFeature`: same, but for the current destination's entire feature (the root ancestor flow's run).
- `FlowCompletionCommand`: replace the nearest enclosing flow's run with `key` (flow handoff); arguments travel as `key`'s constructor properties. When the run spans the whole stack, `key` becomes the only entry.
- `FeatureCommand`: switch to a registered flow by name; the host resolves `featureName` to that flow's `startKey`, so callers stay decoupled from other features' route types. Both top-level features and named sub-flows resolve. An unknown name throws `IllegalArgumentException` (wiring bug, not a runtime condition). With `clearStack`, reset the back stack to that destination. Per-call arguments need a typed key via `ScreenCommand` instead.
- `ExternalUriCommand`: open `uri` outside the app.

## NavigationDispatcher

The seam screens use. The interface never changes; the implementation is provided by `NavContainer`.

```kotlin
interface NavigationDispatcher {
    fun navigateTo(command: NavigationCommand)
}
```

In an MVI screen, collect a navigation effect and forward it:

```kotlin
viewModel.effects.CollectAsEffect { effect ->
    when (effect) {
        is Effect.Navigate -> navigationDispatcher.navigateTo(effect.command)
    }
}
```

## FeatureLauncher

The root `NavFlow` of a feature subtree. Injected into the app's `Map<String, FeatureLauncher>`; the host registers its destinations and those of every flow reachable through `childFlows`, depth-first.

```kotlin
interface FeatureLauncher : NavFlow {
    val featureName: String                          // DI map key / analytics
    override val flowName: String get() = featureName
    // inherited from NavFlow: startKey, serializers, childFlows, register
}
```

```kotlin
@Inject
internal class HomeFeatureLauncher(
    private val viewModelProviders: ViewModelProviders,
) : FeatureLauncher {
    override val featureName = "home"
    override val startKey: NavKey = HomeRoute
    override val serializers = SerializersModule {
        polymorphic(NavKey::class) {
            subclass(HomeRoute::class)
            subclass(DetailRoute::class)
        }
    }
    override fun EntryProviderScope<NavKey>.register(dispatcher: NavigationDispatcher) {
        entry<HomeRoute> {
            HomeScreen(viewModel { viewModelProviders.homeViewModel() }, dispatcher)
        }
        entry<DetailRoute> { key ->                 // typed args arrive as the destructured key
            DetailScreen(id = key.id, dispatcher = dispatcher)
        }
        entry<FilterRoute>(metadata = dialog()) {    // present as a dialog
            FilterDialog(dispatcher)
        }
    }
}
```

`viewModel { ... }` inside an `entry` block is scoped to that entry (its ViewModel store is cleared when the entry leaves the back stack).

### Nested flows

A feature with a multi-step sub-flow that hands a typed result back to its caller:

```kotlin
@Serializable data object ShippingAddressRoute : NavKey
@Serializable data class ShippingOptionsRoute(val addressId: String) : NavKey
data class ShippingResult(val addressId: String, val option: String) : NavigationResult

internal class ShippingFlow : NavFlow {
    override val flowName = "shipping"
    override val startKey: NavKey = ShippingAddressRoute
    override val serializers = SerializersModule {
        polymorphic(NavKey::class) {
            subclass(ShippingAddressRoute::class)
            subclass(ShippingOptionsRoute::class)
        }
    }
    override fun EntryProviderScope<NavKey>.register(dispatcher: NavigationDispatcher) {
        entry<ShippingAddressRoute> { /* next step via ScreenCommand(ShippingOptionsRoute(id)) */ }
        entry<ShippingOptionsRoute> { key ->
            ShippingOptionsScreen(onPicked = { option ->
                // Pops the whole shipping run; the launching screen gets the result.
                dispatcher.navigateTo(NavigationCommand.CloseFlow(ShippingResult(key.addressId, option)))
            })
        }
    }
}

internal class CreateFeatureLauncher : FeatureLauncher {
    override val featureName = "create"
    override val childFlows: List<NavFlow> = listOf(ShippingFlow())
    // startKey, serializers (the feature's own keys only), register as usual
}
```

Rules the host enforces at startup: flow names are unique across the tree; a `NavKey` class is registered by exactly one flow's `serializers`; a flow's `startKey` class must be in its own module; a `NavFlow` instance appears once in the tree. Any screen may launch any flow (`ScreenCommand` with its exported start key, or `FeatureCommand` by name); `CloseFlow` always returns to whatever screen sat beneath the flow's entries.

## NavContainer

Owns the back stack and renders it. Returns the single `NavigationDispatcher` for routing app-level effects. System back and sheet dismissal dispatch through the same dispatcher (as `BackCommand`), so back behaves identically on every path.

```kotlin
@Composable
fun NavContainer(
    startKey: NavKey,
    features: Collection<FeatureLauncher>,
    modifier: Modifier = Modifier,
    uriHandler: UriHandler = LocalUriHandler.current,
    pageTransition: PageTransition = PageTransition.Hierarchical,
    onDestinationChanged: (key: NavKey, flowPath: FlowPath) -> Unit = { _, _ -> },
): NavigationDispatcher

enum class PageTransition { TopLevel, Hierarchical }

@Immutable
class FlowPath {                                     // flow ancestry of a destination, root feature first
    val segments: List<String>
    val feature: String?                             // first segment, null when no flow owns the key
    val flow: String?                                // last segment (nearest enclosing flow)
}
```

`onDestinationChanged` fires with the top destination and its flow ancestry on every change; `flowPath.feature` drives bottom-bar selection and visibility without string routes.

```kotlin
@Composable
fun App(features: Collection<FeatureLauncher>) {
    NavContainer(
        startKey = HomeRoute,
        features = features,
        modifier = Modifier.fillMaxSize(),
        onDestinationChanged = { key, flowPath -> /* analytics, bottom bar */ },
    )
}
```

## Scenes

```kotlin
fun dialog(properties: DialogProperties = DialogProperties()): Map<String, Any>
fun bottomSheet(): Map<String, Any>
```

Pass as `entry<X>(metadata = …) { ... }` to present a destination as an overlay rather than a full screen:

```kotlin
entry<ConfirmRoute>(metadata = dialog()) { ConfirmDialog() }
entry<FilterRoute>(metadata = bottomSheet()) { FilterScreen() }
```

`bottomSheet()` renders the destination as a Material 3 modal bottom sheet; dismissing it (scrim tap, drag-down, or back) pops the back stack. Both overlays host their content with a sheet/dialog-scoped lifecycle, so entry-scoped `viewModel { }` works inside them.

## Back-stack results

Results are typed and addressed by their `NavigationResult` subtype and the receiving destination's key (observe → process → remove, single delivery).

```kotlin
interface NavigationResult { data object Empty : NavigationResult }

@Composable
inline fun <reified T : NavigationResult> BackStackResultHandler(
    owner: NavKey,
    store: NavigationResultStore = LocalNavigationResultStore.current,
    crossinline onResult: (T) -> Unit,
)

@Stable
interface NavigationResultStore {
    fun deliver(owner: NavKey, result: NavigationResult)
    fun peek(owner: NavKey, type: KClass<out NavigationResult>): NavigationResult?  // snapshot-backed, reactive in composition
    fun consume(owner: NavKey, type: KClass<out NavigationResult>)
}

val LocalNavigationResultStore: ProvidableCompositionLocal<NavigationResultStore>
```

The child returns a result by popping with it (`BackCommand` for one screen, `CloseFlow`/`CloseFeature` for a whole flow); the parent observes it by type:

```kotlin
@Serializable data class DetailResult(val picked: String) : NavigationResult

// child screen:
dispatcher.navigateTo(NavigationCommand.BackCommand(result = DetailResult(picked = "x")))
// child flow (pops every entry of the flow, result lands on the launching screen):
dispatcher.navigateTo(NavigationCommand.CloseFlow(result = DetailResult(picked = "x")))

// parent (inside its own entry block, passing the entry's key as owner):
entry<HomeRoute> { key ->
    HomeScreen(...)
    BackStackResultHandler<DetailResult>(owner = key) { result ->
        viewModel.onIntent(HomeIntent.DetailReturned(result))
    }
}
```

Model each distinct result you return as its own type; several types stage independently for one owner, which is how a screen collects results from several sub-flows. The store lives only while hosted in a `NavContainer` (`LocalNavigationResultStore`), in memory only: staged results do not survive process death. System back delivers no result.

---

## Usage

```kotlin
// 1. Define routes (in the feature module, with the kotlinx-serialization plugin applied)
@Serializable data object HomeRoute : NavKey
@Serializable data class DetailRoute(val id: String) : NavKey

// 2. Contribute them via a FeatureLauncher (see above), provided into Map<String, FeatureLauncher> via DI.

// 3. Host them
val dispatcher = NavContainer(startKey = HomeRoute, features = appFeatures)

// 4. Navigate (typed)
dispatcher.navigateTo(NavigationCommand.ScreenCommand(DetailRoute(id = "123")))
dispatcher.navigateTo(NavigationCommand.BackCommand())
dispatcher.navigateTo(NavigationCommand.CloseFlow(ShippingResult(addressId, option)))   // end a flow with a result
dispatcher.navigateTo(NavigationCommand.FlowCompletionCommand(ConfirmationRoute(id)))   // replace a flow
dispatcher.navigateTo(NavigationCommand.FeatureCommand("checkout"))                     // enter a flow by name
dispatcher.navigateTo(NavigationCommand.ExternalUriCommand("https://example.com"))
```
