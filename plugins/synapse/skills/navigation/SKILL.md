---
name: navigation
description: Use when implementing screen navigation, typed routes, feature modules, back-stack results, or Compose navigation in a KMP project.
user-invocable: true
---

# ui:compose-presentation — Navigation & State Management

**Module**: `ui:compose-presentation` | **Artifact**: `com.ribads.synapse:ui-compose-presentation`
**Packages**: `com.ribads.synapse.ui.compose.presentation`, `com.ribads.synapse.ui.compose.presentation.feature`, `com.ribads.synapse.ui.compose.presentation.navigation`, `com.ribads.synapse.ui.compose.presentation.navigation.compose`; see [Imports](#imports)

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

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
import com.ribads.synapse.ui.compose.presentation.BackStackResultHandler
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import com.ribads.synapse.ui.compose.presentation.feature.NavFlow
import com.ribads.synapse.ui.compose.presentation.navigation.FlowPath
import com.ribads.synapse.ui.compose.presentation.navigation.LocalNavigationResultStore
import com.ribads.synapse.ui.compose.presentation.navigation.NavKey
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationResult
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationResultStore
import com.ribads.synapse.ui.compose.presentation.navigation.compose.BottomSheetAppearance
import com.ribads.synapse.ui.compose.presentation.navigation.compose.BottomSheetOptions
import com.ribads.synapse.ui.compose.presentation.navigation.compose.BottomSheetSceneStrategy
import com.ribads.synapse.ui.compose.presentation.navigation.compose.LocalBottomSheetAppearance
import com.ribads.synapse.ui.compose.presentation.navigation.compose.LocalNavContainerViewModelStoreOwner
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavContainer
import com.ribads.synapse.ui.compose.presentation.navigation.compose.PageTransition
import com.ribads.synapse.ui.compose.presentation.navigation.compose.bottomSheet
import com.ribads.synapse.ui.compose.presentation.navigation.compose.detailPane
import com.ribads.synapse.ui.compose.presentation.navigation.compose.dialog
import com.ribads.synapse.ui.compose.presentation.navigation.compose.fullScreen
import com.ribads.synapse.ui.compose.presentation.navigation.compose.isMultiPaneWindow
import com.ribads.synapse.ui.compose.presentation.navigation.compose.listPane
import com.ribads.synapse.ui.compose.presentation.navigation.compose.pageTransition

import com.ribads.synapse.ui.compose.presentation.navigation.compose.chromeContentPadding

// module ui:chrome
import com.ribads.synapse.ui.chrome.ChromeAction
import com.ribads.synapse.ui.chrome.ChromeEvent
import com.ribads.synapse.ui.chrome.ChromeIcon
import com.ribads.synapse.ui.chrome.ChromeLeading
import com.ribads.synapse.ui.chrome.ChromeMenuItem
import com.ribads.synapse.ui.chrome.ChromeRole
import com.ribads.synapse.ui.chrome.ChromeTitleDisplay
import com.ribads.synapse.ui.chrome.LocalNativeChromeInsets
import com.ribads.synapse.ui.chrome.LocalNativeChromeSink
import com.ribads.synapse.ui.chrome.NativeChromeSink
import com.ribads.synapse.ui.chrome.ScreenChrome
import com.ribads.synapse.ui.chrome.WithoutNativeChrome

// iosMain only
import com.ribads.synapse.ui.compose.presentation.navigation.native.NativeNavCoordinator
import com.ribads.synapse.ui.compose.presentation.navigation.native.NativeNavTab
import com.ribads.synapse.ui.compose.presentation.navigation.native.NativeTabIcon
import com.ribads.synapse.ui.compose.presentation.navigation.native.nativeShellViewController
```

`EntryProviderScope` is Jetpack Navigation 3's, not Synapse's: `import androidx.navigation3.runtime.EntryProviderScope`.

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
    data class PopToOrPushCommand(val key: NavKey) : NavigationCommand
    data class BackCommand(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class CloseFlow(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class CloseFeature(val result: NavigationResult = NavigationResult.Empty) : NavigationCommand
    data class FlowCompletionCommand(val key: NavKey) : NavigationCommand
    data class FeatureCommand(val featureName: String, val clearStack: Boolean = false) : NavigationCommand
    data class ExternalUriCommand(val uri: String) : NavigationCommand
}
```

- `ScreenCommand`: push `key`; with `clearStack`, reset the back stack so `key` becomes the only (root) entry.
- `PopToOrPushCommand`: show `key` without a second copy of it. When `key` (compared by equality, so arguments count) is already on the stack, everything above its last occurrence is popped, delivering no result; otherwise `key` is pushed. Use it for destinations reached from outside the current flow, such as a launcher shortcut, where pushing could duplicate an entry already on the stack.
- `BackCommand`: pop the current destination, delivering `result` to the one beneath. No-op on the last entry.
- `CloseFlow`: pop the nearest enclosing flow of the current destination (its contiguous run of entries, including any of its sub-flows'), delivering `result` to the revealed destination. The revealed destination may belong to any flow: a flow launched from another feature returns its result to the launching screen. No-op when the run spans the whole stack; throws `IllegalStateException` if no flow owns the current destination's key class.
- `CloseFeature`: same, but for the current destination's entire feature (the root ancestor flow's run).
- `FlowCompletionCommand`: replace the nearest enclosing flow's run with `key` (flow handoff); arguments travel as `key`'s constructor properties. When the run spans the whole stack, `key` becomes the only entry.
- `FeatureCommand`: switch to a registered flow by name; the host resolves `featureName` to that flow's `startKey`, so callers stay decoupled from other features' route types. Both top-level features and named sub-flows resolve. If that start key is already on the stack, everything above its last occurrence is trimmed instead of a second copy being pushed. An unknown name throws `IllegalArgumentException` (wiring bug, not a runtime condition). With `clearStack`, reset the back stack to that destination. Per-call arguments need a typed key via `ScreenCommand` instead.
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

Destinations render one at a time unless their metadata says otherwise: `dialog()` and `bottomSheet()` present as overlays, and a `listPane()`/`detailPane()` pair shares the window once it is wide enough for two. Overlays resolve first, so a sheet or dialog floats above whatever is beneath it, including a two-pane scene.

```kotlin
@Composable
fun NavContainer(
    startKey: NavKey,
    features: Collection<FeatureLauncher>,
    modifier: Modifier = Modifier,
    uriHandler: UriHandler = LocalUriHandler.current,
    pageTransition: PageTransition = PageTransition.Platform,
    onDestinationChanged: (key: NavKey, flowPath: FlowPath) -> Unit = { _, _ -> },
    bottomSheetAppearance: BottomSheetAppearance = BottomSheetAppearance(),
): NavigationDispatcher

@Immutable
class FlowPath {                                     // flow ancestry of a destination, root feature first
    val segments: List<String>
    val feature: String?                             // first segment, null when no flow owns the key
    val flow: String?                                // last segment (nearest enclosing flow)
}
```

`onDestinationChanged` fires with the top destination and its flow ancestry on every change; `flowPath.feature` drives bottom-bar selection and visibility without string routes. In a two-pane scene the top destination is the detail, not the list beside it.

Each destination has its own `LocalViewModelStoreOwner`, cleared when the destination leaves the back stack. State that several destinations share, and that has to survive a configuration change, belongs in the container's own store instead, which `NavContainer` provides to every destination:

```kotlin
val LocalNavContainerViewModelStoreOwner: ProvidableCompositionLocal<ViewModelStoreOwner?>   // null outside a NavContainer

val shared = viewModel(viewModelStoreOwner = LocalNavContainerViewModelStoreOwner.current!!, key = "checkout") { CheckoutState() }
```

Key such a ViewModel explicitly: every destination in the container resolves the same store, so a key is what keeps two features' ViewModels of one class apart. `renderedEntries` keeps each route's data store there.

`pageTransition` is the motion for destinations that do not choose their own (see [Transitions](#transitions)); `bottomSheetAppearance` styles every `bottomSheet()` destination. Destinations are clipped to the container's bounds, so give it an opaque background: a Synapse `Scaffold` around it provides one.

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

Entry metadata decides how a destination is presented. Pass it as `entry<X>(metadata = …) { ... }`; a destination with no metadata is a full screen.

```kotlin
fun dialog(properties: DialogProperties = DialogProperties()): Map<String, Any>
fun bottomSheet(): Map<String, Any>
fun bottomSheet(options: BottomSheetOptions): Map<String, Any>
fun bottomSheet(properties: ModalBottomSheetProperties): Map<String, Any>
fun listPane(sceneKey: Any = Unit, detailPlaceholder: @Composable () -> Unit = {}): Map<String, Any>
fun detailPane(sceneKey: Any = Unit): Map<String, Any>
fun pageTransition(transition: PageTransition): Map<String, Any>   // see Transitions
fun fullScreen(): Map<String, Any>                                 // pushed on the native iOS shell: no tab bar, navigation bar or system back

@Composable fun isMultiPaneWindow(): Boolean
```

Metadata maps combine with `+`, e.g. `listPane(MAIL_PANES) + pageTransition(PageTransition.None)`.

### Overlays

```kotlin
entry<ConfirmRoute>(metadata = dialog()) { ConfirmDialog() }
entry<FilterRoute>(metadata = bottomSheet()) { FilterScreen() }
```

```kotlin
data class BottomSheetOptions(                        // per destination, via bottomSheet(options)
    val skipPartiallyExpanded: Boolean = false,
    val isSwipeDismissible: Boolean = true,
    val showDragHandle: Boolean = true,                // false hides BottomSheetAppearance.dragHandle for this destination
    val properties: ModalBottomSheetProperties = ModalBottomSheetProperties(),
)

data class BottomSheetAppearance(                     // app-wide, via NavContainer(bottomSheetAppearance = ...)
    val containerColor: @Composable () -> Color = { BottomSheetDefaults.ContainerColor },
    val dragHandle: @Composable () -> Unit = { BottomSheetDefaults.DragHandle() },
    val contentColor: @Composable () -> Color = { contentColorFor(containerColor()) },
    val contentDecoration: @Composable (content: @Composable () -> Unit) -> Unit = { content -> content() },
    val shape: @Composable () -> Shape = { BottomSheetDefaults.ExpandedShape },     // the sheet's outline
    val scrimColor: @Composable () -> Color = { BottomSheetDefaults.ScrimColor },   // dims the content beneath
)
```

`bottomSheet()` renders the destination as a Material 3 modal bottom sheet; dismissing it (scrim tap, drag-down, or back) pops the back stack. `contentColor` defaults to Material's pairing for the container (on Android it also decides the sheet's status bar icon colour), and `contentDecoration` wraps every sheet's content, e.g. to provide the app's raised-surface theme context. The parameterless overload keeps callers clear of the `ExperimentalMaterial3Api` opt-in; take the `ModalBottomSheetProperties` overload only when you need to change them.

Lifecycle inside overlays differs by kind:

- **`bottomSheet()`**: Synapse's own scene hosts the sheet and gives its content a sheet-scoped `LocalLifecycleOwner`, so entry-scoped `viewModel { }` and lifecycle-aware collection inside the sheet resolve against the sheet, not the screen beneath it.
- **`dialog()`**: presented by Navigation 3's `DialogSceneStrategy`, unchanged. Synapse adds no lifecycle owner there, so a dialog's content gets whatever Navigation 3 and the platform `Dialog` provide; entry-scoped `viewModel { }` still comes from the entry's own decorators. Verify lifecycle-dependent behaviour in a dialog destination on each platform rather than assuming it matches a sheet.

**The destination already is the sheet.** Root a `bottomSheet()` screen in `TraySurface` (or `ScrollableTraySurface` for scrolling content, with `BottomSheetOptions(skipPartiallyExpanded = true, isSwipeDismissible = false, showDragHandle = false)`) from `/synapse:ui-components`. Never root it in `Tray` or `ScrollableTray`: those draw their own sheet, so the user gets a second sheet behind the first.

**One look for every sheet.** `NavContainer` also publishes `bottomSheetAppearance` as `LocalBottomSheetAppearance`, and Synapse's in-screen sheets (`Tray`, `ScrollableTray`, `DatePickerBottomSheet`) read it. Set the drag handle, colours and `contentDecoration` once on `NavContainer` and both kinds of sheet match. Apps on the Synapse theme pass `ThemedBottomSheetAppearance` from `/synapse:ui-components`, which paints `surface.raised` in the top corners of `roundShape`, dims the content with `overlay.scrim`, tints the handle with `border.primary` and wraps the content in `WithRaisedSurface`. Outside any `NavContainer` the local holds `BottomSheetAppearance()`.

```kotlin
val LocalBottomSheetAppearance: ProvidableCompositionLocal<BottomSheetAppearance>
```

**Your own `NavDisplay`.** `NavContainer` already registers the sheet strategy (ahead of Navigation 3's `DialogSceneStrategy` and the pane strategies), so most apps never touch it. An app that drives Navigation 3's `NavDisplay` itself registers it to get `bottomSheet()` destinations, first in the list so the sheet overlays the destination beneath it:

```kotlin
class BottomSheetSceneStrategy<T : Any>(
    appearance: BottomSheetAppearance = BottomSheetAppearance(),
) : SceneStrategy<T>                                   // androidx.navigation3.scene.SceneStrategy

NavDisplay(                                            // androidx.navigation3.ui.NavDisplay
    backStack = backStack,
    sceneStrategies = listOf(
        BottomSheetSceneStrategy<NavKey>(appearance = ThemedBottomSheetAppearance),
        DialogSceneStrategy<NavKey>(),
        SinglePaneSceneStrategy<NavKey>(),
    ),
    entryProvider = entryProvider { /* entries */ },
)
```

It returns a scene only when the top entry carries `bottomSheet()` metadata, and the sheet's dismissal calls the `NavDisplay`'s `onBack`. Provide `LocalBottomSheetAppearance` yourself in that setup if in-screen trays should match.

### List-detail

Mark the two halves of a list-detail pair and they share the window once it is wide enough for two panes:

```kotlin
private const val MAIL_PANES = "mail"

entry<InboxRoute>(metadata = listPane(MAIL_PANES) { NoMessageSelected() }) {
    InboxScreen(onMessage = { dispatcher.navigateTo(ScreenCommand(MessageRoute(it))) })
}
entry<MessageRoute>(metadata = detailPane(MAIL_PANES)) { key -> MessageScreen(id = key.id) }
```

Nothing about navigation changes: the detail is an ordinary destination pushed with `ScreenCommand`, with its own ViewModel store, saved state, and results. Only the layout adapts.

- **When two panes appear**: from the medium width class (~600dp) upwards, which covers tablets, unfolded foldables, desktop-size windows, and most phones in landscape. Narrower than that, the pair falls through to the single-pane strategy and navigates one screen at a time with the usual transitions.
- **Pairing**: the panes combine only while the `listPane` destination carrying the same `sceneKey` sits beneath the detail on the back stack. A detail reached any other way (pushed by another feature, deep-linked, stacked under a different pair) is a full screen. Give each pair its own `sceneKey`; the `Unit` default is a single app-wide pair.
- **Placeholder**: `detailPlaceholder` fills the detail pane while no detail destination is on the stack. It is not a destination, so it has no ViewModel store, no saved state, and cannot receive results. Keep it to empty-state content.
- **Back**: the two panes are one scene, so system back leaves the pair as a unit. From `[Home, Inbox, Message]` on a wide window it pops both `Message` and `Inbox` and reveals `Home`, and stacked details collapse together rather than stepping back through each other. When the pair is the whole back stack there is nothing to reveal, so the container does not handle back at all and the press falls through to the platform: give a detail that can be the root pair its own close affordance. Explicit `BackCommand` is unaffected on every window size, so a detail that closes itself with a result behaves the same everywhere.
- **Chrome**: `isMultiPaneWindow()` reports whether the current window would show two panes and recomposes across a fold, an unfold, and a rotation. Use it for shell chrome that has to differ between the two layouts; it reflects the window only, not what is on the back stack.

The adaptive dependency ships inside the module: consumers add nothing to their build and need no `ExperimentalMaterial3AdaptiveApi` opt-in.

## Transitions

Every destination animates with a `PageTransition` as it is pushed and popped, back gesture included. `NavContainer(pageTransition = …)` sets the default, `PageTransition.Platform`; a destination overrides it with `pageTransition(…)` metadata.

```kotlin
@Immutable
class PageTransition {                                // opaque: presets only
    companion object {
        val Platform: PageTransition                  // default
        val None: PageTransition
        val Fade: PageTransition
        val Modal: PageTransition
        @Deprecated val Hierarchical: PageTransition  // same instance as Platform
        @Deprecated val TopLevel: PageTransition      // same instance as None
    }
}

fun pageTransition(transition: PageTransition): Map<String, Any>
```

| Preset | iOS | Android |
|---|---|---|
| `Platform` | UIKit push: the new page slides in full width over 500ms while the old one shifts a quarter and dims; the edge swipe tracks the finger | Navigation 3's default: a 700ms crossfade; the back gesture shrinks the page while the previous one fades in |
| `None` | Instant | Instant |
| `Fade` | Material fade-through: the old page fades out (90ms), then the new one fades and scales in (220ms) | Same |
| `Modal` | Slides up (400ms) and back down (200ms); the back gesture shrinks it away | Same |

```kotlin
override fun EntryProviderScope<NavKey>.register(dispatcher: NavigationDispatcher) {
    entry<HomeTab>(metadata = pageTransition(PageTransition.None)) { HomeScreen() }        // tab root
    entry<ComposeRoute>(metadata = pageTransition(PageTransition.Modal)) { ComposeScreen() }
    entry<WelcomeRoute>(metadata = pageTransition(PageTransition.Fade)) { WelcomeScreen() }  // reached by replacing the stack
}
```

- **Who decides**: a pushed destination's transition runs as it is pushed; a popped destination's runs as it is popped, back gesture included. Replacing the stack (`clearStack`, `FlowCompletionCommand`) counts as a push. Mark tab roots with `None` and tab switches are instant in both directions, while the screens they push keep the platform motion.
- **Choose per destination, never from state**: do not pick the transition in `onDestinationChanged` or a ViewModel and feed it back into `NavContainer`. That callback fires after the transition has started, so every choice lands on the next navigation instead.
- **Two panes**: a `listPane`/`detailPane` pair sharing the window animates with the list's transition as the pair enters or leaves; details swap inside the pane without a page transition.
- **Overlays**: `bottomSheet()` and `dialog()` destinations ignore it and animate as sheets and dialogs.
- **Host**: destinations are clipped to the container's bounds, and crossfades (`Platform` on Android, `Fade`) show whatever is behind the container mid-transition. Give it an opaque background.
- **Custom motion**: Navigation 3's own metadata (`NavDisplay.transitionSpec { }`, `NavDisplay.popTransitionSpec { }`, `NavDisplay.predictivePopTransitionSpec { }`) takes precedence over `pageTransition(…)`. It is Compose-only.
- **Known limitations**: `Platform` on iOS slides in fixed screen directions, so right-to-left layouts push from the right while the swipe-back comes from the right edge. An iOS edge swipe also dismisses a `Modal` destination, which a native full-screen cover would not allow.

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
        viewModel.emit(HomeIntent.DetailReturned(result))
    }
}
```

Model each distinct result you return as its own type; several types stage independently for one owner, which is how a screen collects results from several sub-flows. The store lives only while hosted in a `NavContainer` (`LocalNavigationResultStore`), in memory only: staged results do not survive process death. System back delivers no result.

---

## Native iOS Navigation (Liquid Glass)

iOS 26 renders Liquid Glass only through native `TabView`/`NavigationStack`. The bridge hands navigation chrome to a SwiftUI shell while Compose keeps rendering screen content, one `UIViewController` per screen. Android and pre-iOS-26 keep the full-Compose `NavContainer` path unchanged.

### Screen chrome (commonMain contract)

Screens declare their navigation bar once as pure data; the active shell renders it. Under the native shell the declaration becomes the native bar (system back, toolbar buttons, Liquid Glass menus, live title updates); elsewhere it renders as a Compose `TopNavBar`. Screens never branch on which shell is active.

The contract lives in its own module, `ui:chrome`, because both the component library (which renders it as a `TopNavBar`) and the navigation host (which publishes it to a native shell) depend on it, and neither owns it. `ui:component` exposes it as an `api` dependency, so a screen that already uses `NavChrome` needs no extra coordinate.

```kotlin
// module ui:chrome, package com.ribads.synapse.ui.chrome

data class ScreenChrome(
    val title: String? = null,
    val subtitle: String? = null,                          // native bars only; the Compose top bar ignores it
    val titleDisplay: ChromeTitleDisplay = ChromeTitleDisplay.Inline,
    val leading: ChromeLeading? = ChromeLeading.Back,      // null = none on every shell
    val actions: List<ChromeAction> = emptyList(),         // leading-to-trailing order
)
// init validation: ids unique across actions and menu items.

enum class ChromeTitleDisplay { Inline, Large }            // Large = iOS large title; ignored elsewhere
enum class ChromeLeading { Back, Close }
enum class ChromeRole { Standard, Confirm, Destructive }   // Confirm = "Done"/"Save"; iOS renders it prominently

sealed interface ChromeAction {
    val id: String        // reported when chosen; unique within one ScreenChrome
    val title: String     // required, non-blank: button text, accessibility label of an icon button, overflow text
    val enabled: Boolean

    data class Button(
        override val id: String,
        override val title: String,
        val icon: ChromeIcon.Drawable? = null,             // null = text button
        val role: ChromeRole = ChromeRole.Standard,
        override val enabled: Boolean = true,
    ) : ChromeAction

    data class Menu(
        override val id: String,
        override val title: String,
        val icon: ChromeIcon.Drawable,
        val items: List<ChromeMenuItem>,                   // at least one
        override val enabled: Boolean = true,
    ) : ChromeAction
}

data class ChromeMenuItem(
    val id: String,
    val title: String,                                     // non-blank
    val icon: ChromeIcon? = null,
    val role: ChromeRole = ChromeRole.Standard,
    val enabled: Boolean = true,
)

sealed interface ChromeIcon {
    val sfSymbol: String?                                  // preferred by native iOS chrome (vibrancy, optical sizing)

    data class Drawable(                                   // renders on every platform
        val drawable: DrawableResource,
        override val sfSymbol: String? = null,
    ) : ChromeIcon

    data class SfSymbol(override val sfSymbol: String) : ChromeIcon   // native iOS only: menu items only, by type
}
```

Any mix of text and icon actions is valid. Every action carries a `title`, so an icon button is always labelled for accessibility. A drawable in any format `painterResource` understands (XML vector, SVG, bitmap) renders on the native bar; add an `sfSymbol` when a fitting symbol exists.

Declare it with `NavChrome` from `ui:component` (see `/synapse:ui-components`), in the Scaffold `topBar` slot. Build the model outside the composable:

```kotlin
private val memosChrome = ScreenChrome(
    title = "Voice memos",
    titleDisplay = ChromeTitleDisplay.Large,
    actions = listOf(
        ChromeAction.Menu(
            id = "more",
            title = "More",
            icon = ChromeIcon.Drawable(Res.drawable.ic_more, sfSymbol = "ellipsis.circle"),
            items = listOf(
                ChromeMenuItem("clear-all", "Clear all", icon = ChromeIcon.SfSymbol("trash"), role = ChromeRole.Destructive),
            ),
        ),
    ),
)

NavChrome(
    chrome = memosChrome,
    onLeadingClick = { dispatcher.navigateTo(NavigationCommand.BackCommand()) },
    onAction = { actionId -> /* handle by id */ },
)
```

The leading affordance:

- `ChromeLeading.Back` (default): the native shell draws and handles the system back itself and never calls `onLeadingClick` for it. The Compose top bar shows the back glyph only when `onLeadingClick` is non-null, so a tab root simply omits the handler. A system bar with no navigation stack behind it (a sink whose `handlesBack` is false) follows the Compose rule and reports the tap.
- `ChromeLeading.Close`: every shell renders a close button in place of back and reports the tap. It requires `onLeadingClick` (`NavChrome` fails fast without one).
- `null`: no leading affordance anywhere. The native shell hides its back button too, which also disables swipe-back, so the screen must offer another way out.

`NavChrome` is the bar of a screen: declare at most one per screen. A header inside a sheet or dialog always renders as a Compose `TopNavBar`: overlay destinations (`bottomSheet()`, `dialog()`) and Synapse trays never see the native bar (wrap a floating surface of your own in `WithoutNativeChrome` for the same), and a second `NavChrome` composed inside a screen that already holds the bar falls back to the Compose bar instead of vanishing. A `fullScreen()` destination has no native bar, so its `NavChrome` renders as a Compose `TopNavBar` too.

The seam chrome components publish through (only shells provide it; screens never touch it directly):

```kotlin
sealed interface ChromeEvent {
    data object LeadingClicked : ChromeEvent               // never sent for a Back the shell handles itself
    data class ActionSelected(val id: String) : ChromeEvent
}

interface NativeChromeSink {
    val handlesBack: Boolean get() = true                  // false = a bar with no stack behind it: Back is drawn as declared and reported
    fun update(owner: Any, chrome: ScreenChrome, onEvent: (ChromeEvent) -> Unit): Boolean   // true = owner holds the native bar
    fun clear(owner: Any)
}

val LocalNativeChromeSink: ProvidableCompositionLocal<NativeChromeSink?>   // null = render Compose chrome
val LocalNativeChromeInsets: ProvidableCompositionLocal<WindowInsets?>     // null = no native chrome overlap, or already applied

@Composable fun WithoutNativeChrome(content: @Composable () -> Unit)        // a surface floating over the screen: it can't take the native bar, and the native bars don't overlap it
```

### Content padding under native chrome

Synapse `Scaffold` applies the native chrome overlap (navigation bar at the top, floating glass tab bar at the bottom): its bars sit clear of the native chrome, and the `PaddingValues` it hands to content cover that chrome as well as the bars. A screen that honours the padding is correct on every shell with no shell-specific call.

Apply the padding inside the scroll container so content scrolls beneath the translucent bars yet rests clear of them:

```kotlin
Scaffold(topBar = { NavChrome(chrome = chrome, onLeadingClick = onBack) }) { padding ->
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(padding)
            .padding(Theme.spacing.x4),
    ) { /* content */ }
}

LazyColumn(contentPadding = padding + PaddingValues(Theme.spacing.x4)) { /* items */ }
```

A screen that does not scroll pads its root with `Modifier.padding(padding)`. A Compose `bottomBar` (a chat input) needs nothing: the Scaffold lifts it above the tab bar.

For a screen without a `Scaffold`:

```kotlin
// commonMain, package com.ribads.synapse.ui.compose.presentation.navigation.compose
@Composable
fun chromeContentPadding(
    start: Dp = 0.dp, top: Dp = 0.dp, end: Dp = 0.dp, bottom: Dp = 0.dp,
    chromeSides: WindowInsetsSides = WindowInsetsSides.Top + WindowInsetsSides.Bottom,
): PaddingValues   // visual padding + native chrome overlap, read lazily so layout follows live chrome changes
```

Inside a `Scaffold` the overlap counts as applied, so `chromeContentPadding` returns the visual padding alone there and the two can never double up.

### iOS bridge API (iosMain, package `...navigation.native`)

The SwiftUI shell ships as the `SynapseNativeNav` Swift package. Kotlin calls it through cinterop and the package knows nothing about Kotlin, so an app carries no shell code of its own.

```kotlin
class NativeNavTab(
    val featureName: String,   // FeatureLauncher.featureName; doubles as tab id
    val title: String,         // native tab bar label + the tab root's fallback navigation title
    val icon: NativeTabIcon,
) {
    constructor(featureName: String, title: StringResource, icon: NativeTabIcon)   // the title from a Compose string resource
}

sealed interface NativeTabIcon {
    data class SfSymbol(val name: String) : NativeTabIcon                  // preferred: full Liquid Glass treatment
    data class Resource(val drawable: DrawableResource) : NativeTabIcon    // any painterResource format, XML vectors included
}

class NativeNavCoordinator(
    featureLaunchers: Collection<FeatureLauncher>,                            // same set the full-Compose NavContainer registers
    tabs: List<NativeNavTab>,                                                 // non-empty, unique, each names a registered feature
    bottomSheetAppearance: BottomSheetAppearance = BottomSheetAppearance(),   // every sheet's look, as on NavContainer
    screenDecorator: @Composable (content: @Composable () -> Unit) -> Unit,   // theme/toast/image-loader environment per screen; sees LocalNativeChromeInsets
) {
    fun setTabBadge(tabFeatureName: String, badge: String?)                   // app-driven native tab badge
    fun navigate(command: NavigationCommand)                                  // from outside any screen: runs on the selected tab, as its top screen would
}

fun nativeShellViewController(coordinator: () -> NativeNavCoordinator): UIViewController?   // null below iOS 26; coordinator runs only where the shell can

class DrawableRasterizer { fun image(drawable: DrawableResource): UIImage }   // a Compose drawable as a UIImage, for native chrome; main thread only
```

Create one coordinator per shell session; every call must be on the main thread (checked). Construction fails fast on an empty tab list, duplicate tabs, or a tab naming no registered feature. Kotlin owns each tab's path and publishes it whole; SwiftUI reports its own pops (back chevron, swipe-back) back, and the two reconcile by entry identity.

Command translation is shared with the full-Compose dispatcher: both apply edits planned by one internal `StackPlanner` over one flat stack, and differ only in that a tab's root is permanent. A tab's stack is its native entries, each followed by its open overlays, so a command behaves as it does in `NavContainer` whether or not an overlay is open. Only the top screen of a tab can navigate: a command from a covered or already popped screen is ignored, so a double tap can't pop two screens, and a second command from a screen the first one moved off the top does nothing (use `FlowCompletionCommand` or `clearStack` to replace a screen). A destination registered with `bottomSheet()`/`dialog()` metadata always opens as a Compose overlay over the screen left on top; any other destination is a native push. `ScreenCommand` pushes, and `clearStack` resets the tab to its root first (naming that root pops back to it, with no second copy); `BackCommand` closes an open overlay, otherwise it is a native pop, and either way delivers its result to the destination revealed (`BackStackResultHandler` works unchanged); `FeatureCommand` naming another tab selects it, naming the tab the screen is on pops back to its root, and `clearStack` resets the target tab; any other registered flow name (sub-flows included, since flow names are unique tree-wide) pops back to the flow's existing root if present, else opens its start key (`clearStack` resets first); unknown names fail fast on both shells. Flow scopes resolve through the same `FlowRegistry`, from the top destination, an open overlay included: `CloseFlow` pops the nearest enclosing flow's contiguous run; `CloseFeature` pops its root feature's run, sub-flows included; closing the tab's own feature pops to the tab root, which always survives. `FlowCompletionCommand` is the same pop plus the next key, and never replaces a tab root; `ExternalUriCommand` opens the URI outside the app.

A pushed `fullScreen()` destination shows no tab bar or navigation bar and has no system back, so the screen must offer its own way out. On a tab's root it changes nothing, and `NavContainer` ignores it.

`NativeNavCoordinator.navigate` is for what comes from outside any screen, such as a shortcut or a link. It can run before the shell attaches, so an app can open on a screen above a tab's root.

### Consumer setup

A project generated with `/init-project --tabs` already has both steps, and its developer writes no Swift. For an existing project:

**1. Add the SynapseNativeNav SPM dependency.** In Xcode: **File > Add Package Dependencies**, add:

```
https://github.com/ribads/synapse-native-nav-kmp
```

Select the `SynapseNativeNav` library product, with the dependency rule **Up to Next Minor Version** from `0.0.2`. Build with the Xcode 26 SDK or later. The package links into apps with a deployment target down to iOS 16; below iOS 26 `nativeShellViewController` returns null.

An app only has to link the package if it calls `nativeShellViewController` (or exports `ui-compose-presentation` into its framework). Bridge references that nothing reaches are dropped, by Kotlin/Native in Release and by Xcode's default dead stripping in Debug, so an app that turns `DEAD_CODE_STRIPPING` off must link the package too.

**2. Kotlin root (app's iosMain):**

```kotlin
private fun createAppNavCoordinator(): NativeNavCoordinator {
    val component = AppComponent::class.create()
    return NativeNavCoordinator(
        featureLaunchers = component.features.values,
        tabs = listOf(
            NativeNavTab(featureName = "home", title = "Home", icon = NativeTabIcon.SfSymbol("house")),
            NativeNavTab(featureName = "memos", title = "Memos", icon = NativeTabIcon.Resource(Res.drawable.ic_mic)),
        ),
        bottomSheetAppearance = ThemedBottomSheetAppearance,
        screenDecorator = { content -> AppTheme { ToastHandler { content() } } },
    )
}

fun MainViewController(): UIViewController =
    nativeShellViewController(::createAppNavCoordinator) ?: ComposeUIViewController { App() }
```

Keep ONE tab list in your commonMain (featureName + title + Compose icon) and map it here: the same list drives the Compose bottom bar on Android/pre-iOS-26 and the native TabView on iOS 26. Screen titles and toolbar actions come from each screen's `NavChrome` declaration; the factory carries no display strings beyond tab titles.

**Insets**: the shell reports how far the native bars overlap each hosted screen. The bridge publishes them through `LocalNativeChromeInsets`, where `Scaffold` applies them, and they update live. The `screenDecorator` sees them too, so a `ToastHandler` in it shows toasts clear of the bars; a `fullScreen()` destination has none.

The Synapse showcase demonstrates the full pattern: `ShowcaseTabs.kt` (shared config, one raster and one XML vector tab icon), `ShowcaseRoot.kt` (full-Compose shell with `BottomNavigationBar` + `FeatureCommand` tab switching), `NativeShell.kt` (iOS coordinator factory), `features/common/DemoTopBar.kt` (`NavChrome` wrapper), `VoiceMemosFeatureLauncher.kt` (large title + destructive toolbar menu), `ChatFeatureLauncher.kt` (text toolbar button + pinned bottom input), `booking/TravellerDetailsFlow.kt` (a sheet whose `NavChrome` header renders as Compose chrome with a close button).

### v1 limitations
- `bottomSheet()`/`dialog()` destinations render as Compose overlays, not native sheets.
- No process-death restoration of the native stack.
- Late async pushes land on the tab that dispatched them, not the visible tab; `FlowCompletionCommand` never replaces a tab root; the system back button and swipe-back bypass `onLeadingClick` and deliver no back-stack result (parity with Android system back).
- Each entry on a native stack keeps its (frozen) Compose composition alive while covered.
- A screen's chrome lands one composition frame after its push: the native bar starts blank and fills in immediately.

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
dispatcher.navigateTo(NavigationCommand.PopToOrPushCommand(DetailRoute(id = "123")))  // reuse it if already open
dispatcher.navigateTo(NavigationCommand.BackCommand())
dispatcher.navigateTo(NavigationCommand.CloseFlow(ShippingResult(addressId, option)))   // end a flow with a result
dispatcher.navigateTo(NavigationCommand.FlowCompletionCommand(ConfirmationRoute(id)))   // replace a flow
dispatcher.navigateTo(NavigationCommand.FeatureCommand("checkout"))                     // enter a flow by name
dispatcher.navigateTo(NavigationCommand.ExternalUriCommand("https://example.com"))
```
