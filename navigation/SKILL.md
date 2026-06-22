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

## NavigationCommand

```kotlin
sealed interface NavigationCommand {
    data class ScreenCommand(val key: NavKey, val clearStack: Boolean = false) : NavigationCommand
    data class BackCommand(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class CloseFeature(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class FlowCompletionCommand(val key: NavKey) : NavigationCommand
    data class FeatureCommand(val featureName: String, val clearStack: Boolean = false) : NavigationCommand
    data class ExternalUriCommand(val uri: String) : NavigationCommand
}
```

- `ScreenCommand` — push `key`; with `clearStack`, reset the back stack so `key` becomes the only (root) entry.
- `BackCommand` — pop the current destination, delivering `result` to the one beneath.
- `CloseFeature` — pop the current feature's subtree entirely, delivering `result` beneath it.
- `FlowCompletionCommand` — replace the current feature subtree with `key` (flow handoff).
- `FeatureCommand` — switch to a top-level feature by its `featureName`; the host resolves it to that feature's `startKey`, so callers stay decoupled from other features' route types. With `clearStack`, reset the back stack to it.
- `ExternalUriCommand` — open `uri` outside the app.

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

Each feature module contributes its destinations, serializers, and start key. Injected into the app's `Map<String, FeatureLauncher>`.

```kotlin
interface FeatureLauncher {
    val featureName: String                          // DI map key / analytics
    val startKey: NavKey                             // shown when entered as a top-level entry point
    val serializers: SerializersModule              // polymorphic NavKey registration (iOS/web saved state)
    fun EntryProviderScope<NavKey>.register(dispatcher: NavigationDispatcher)
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

## NavContainer

Owns the back stack and renders it. Returns the single `NavigationDispatcher` for routing app-level effects.

```kotlin
@Composable
fun NavContainer(
    startKey: NavKey,
    features: Collection<FeatureLauncher>,
    modifier: Modifier = Modifier,
    uriHandler: UriHandler = LocalUriHandler.current,
    pageTransition: PageTransition = PageTransition.Hierarchical,
    onKeyChanged: (NavKey) -> Unit = {},            // called with the top destination on every change
): NavigationDispatcher

enum class PageTransition { TopLevel, Hierarchical }
```

```kotlin
@Composable
fun App(features: Collection<FeatureLauncher>) {
    NavContainer(
        startKey = HomeRoute,
        features = features,
        modifier = Modifier.fillMaxSize(),
        onKeyChanged = { key -> /* analytics */ },
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
```

The child returns a result by popping with it; the parent observes it by type:

```kotlin
@Serializable data class DetailResult(val picked: String) : NavigationResult

// child:
dispatcher.navigateTo(NavigationCommand.BackCommand(result = DetailResult(picked = "x")))

// parent (inside its own entry block, passing the entry's key as owner):
entry<HomeRoute> { key ->
    HomeScreen(...)
    BackStackResultHandler<DetailResult>(owner = key) { result ->
        viewModel.onIntent(HomeIntent.DetailReturned(result))
    }
}
```

Model each distinct result you return as its own type. The store lives only while hosted in a `NavContainer` (`LocalNavigationResultStore`).

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
dispatcher.navigateTo(NavigationCommand.ExternalUriCommand("https://example.com"))
```
