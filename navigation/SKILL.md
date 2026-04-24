---
name: navigation
description: Use when implementing screen navigation, route management, deep links, feature modules, Parcelize, or Compose navigation in a KMP project.
user-invocable: true
---

# ui:compose-presentation — Navigation & State Management

**Module**: `ui:compose-presentation` | **Artifact**: `com.ribads.synapse:ui-compose-presentation`
**Package**: `com.ribads.synapse.ui.compose.presentation`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:ui-compose-presentation:<version>")
}
```

---

## NavigationCommand

```kotlin
sealed class NavigationCommand {
    data class ScreenCommand(val route: String, val clearStack: Boolean = false, val arguments: Map<String, NavigationArgument> = emptyMap()) : NavigationCommand()
    data class BackCommand(val result: Map<String, NavigationArgument> = emptyMap()) : NavigationCommand()
    data class CloseFeature(val result: Map<String, NavigationArgument> = emptyMap()) : NavigationCommand()
    data class FlowCompletionCommand(val route: String, val arguments: Map<String, NavigationArgument> = emptyMap()) : NavigationCommand()
    data class FeatureCommand(val featureName: String, val clearStack: Boolean = false, val arguments: Map<String, NavigationArgument> = emptyMap()) : NavigationCommand()
    data class ExternalUriCommand(val uri: String) : NavigationCommand()
}

sealed class NavigationArgument {
    data class StringArgument(val value: String) : NavigationArgument()
    data class IntArgument(val value: Int) : NavigationArgument()
    data class FloatArgument(val value: Float) : NavigationArgument()
    data class BooleanArgument(val value: Boolean) : NavigationArgument()
    data class ParcelableArgument(val value: MyParcelable) : NavigationArgument()
}
```

## NavigationDispatcher

```kotlin
interface NavigationDispatcher {
    fun navigateTo(command: NavigationCommand)
}

class ComposeNavigationDispatcher(
    private val screenNavigationController: NavController,
    private val uriHandler: UriHandler,
    private val addArgs: NavBackStackEntry.(Map<String, NavigationArgument>) -> Unit,
) : NavigationDispatcher {
    override fun navigateTo(command: NavigationCommand)

    companion object {
        fun addArguments(backStackEntry: NavBackStackEntry, args: Map<String, NavigationArgument>)
    }
}
```

## NavContainer & NavigatorHost

```kotlin
sealed interface NavigatorHost {
    fun buildGraph(builder: NavGraphBuilder, navigationDispatcher: NavigationDispatcher)
    interface Root : NavigatorHost
    interface Child : NavigatorHost
}

@Composable
fun NavContainer(
    modifier: Modifier, startDestination: String, navigatorHost: NavigatorHost.Root,
    navHostController: NavHostController, uriHandler: UriHandler = LocalUriHandler.current,
    pageTransition: PageTransition = PageTransition.Hierarchical,
)

@Composable
fun rememberNavController(
    navigators: Array<Navigator<out NavDestination>> = emptyArray(),
    onDestinationChangedListener: NavController.OnDestinationChangedListener
): NavHostController

enum class PageTransition { TopLevel, Hierarchical }
```

## NavGraphBuilder Extensions

```kotlin
fun NavGraphBuilder.composable(route: String, arguments: List<NamedNavArgument> = emptyList(), deepLinks: List<NavDeepLink> = emptyList(), content: @Composable (NavBackStackEntry) -> Unit)
fun NavGraphBuilder.modal(route: String, arguments: List<NamedNavArgument> = emptyList(), deepLinks: List<NavDeepLink> = emptyList(), content: @Composable (NavBackStackEntry) -> Unit)
```

## BackStackEntry Extensions

```kotlin
fun NavBackStackEntry.requireStringParameter(paramName: String): String
fun NavBackStackEntry.requireBooleanParameter(paramName: String, defaultValue: Boolean? = null): Boolean
fun SavedState.getString(key: String): String?
@Composable fun SavedStateHandle.getString(key: String, remove: Boolean = false): String?
@Composable fun <T> SavedStateHandle.get(key: String, remove: Boolean = false): T?
```

## Feature Launcher

```kotlin
interface FeatureLauncher {
    val featureName: String
    fun navigationGraph(): NavigatorHost.Child
}
```

## Parcelize (Cross-Platform)

```kotlin
@OptionalExpectation expect annotation class Parcelize()
expect interface MyParcelable
expect annotation class MyIgnoredOnParcel()
// Android: typealias to kotlinx.parcelize.Parcelize + Parcelable
// iOS: typealias to com.arkivanov.parcelize.darwin
```

### Consumer setup (required for `ParcelableArgument`)

`kotlin-parcelize` is a compiler plugin, and the plugin matches annotations by literal FQN — it does NOT follow typealiases. Consumer modules that pass `ParcelableArgument` must apply the plugin AND register Synapse's `@Parcelize` as an additional annotation, otherwise `@Parcelize`-annotated classes compile to plain data classes and the argument crashes at runtime.

In every consumer module whose Android target compiles `@Parcelize` classes:

```kotlin
plugins {
    id("kotlin-parcelize")
}

kotlin {
    android {
        @OptIn(ExperimentalKotlinGradlePluginApi::class)
        compilerOptions {
            freeCompilerArgs.addAll(
                "-P",
                "plugin:org.jetbrains.kotlin.parcelize:additionalAnnotation=com.ribads.synapse.ui.compose.presentation.navigation.Parcelize"
            )
        }
    }
    sourceSets {
        iosMain.dependencies {
            implementation("com.arkivanov.parcelize.darwin:runtime:<version>")
        }
    }
}
```

Then in `commonMain`:

```kotlin
import com.ribads.synapse.ui.compose.presentation.navigation.MyParcelable
import com.ribads.synapse.ui.compose.presentation.navigation.Parcelize

@Parcelize
data class DetailArgs(val id: String, val title: String) : MyParcelable

NavigationCommand.ScreenCommand(
    route = "detail",
    arguments = mapOf("args" to NavigationArgument.ParcelableArgument(DetailArgs("1", "Hi")))
)
```

---

## Usage

```kotlin
// Define a NavigatorHost
class MainNavigator @Inject constructor() : NavigatorHost.Root {
    override fun buildGraph(builder: NavGraphBuilder, navigationDispatcher: NavigationDispatcher) {
        builder.composable("home") { HomeScreen(navigationDispatcher) }
        builder.composable("detail/{id}") { entry ->
            DetailScreen(id = entry.requireStringParameter("id"))
        }
        builder.modal("settings") { SettingsScreen() }
    }
}

// Set up NavContainer
@Composable
fun App(navigator: MainNavigator) {
    val navController = rememberNavController(
        onDestinationChangedListener = { _, dest, _ -> /* analytics */ }
    )
    NavContainer(
        modifier = Modifier.fillMaxSize(),
        startDestination = "home",
        navigatorHost = navigator,
        navHostController = navController,
        pageTransition = PageTransition.Hierarchical,
    )
}

// Navigate
navigationDispatcher.navigateTo(NavigationCommand.ScreenCommand(
    route = "detail/123",
    arguments = mapOf("title" to NavigationArgument.StringArgument("My Item"))
))
navigationDispatcher.navigateTo(NavigationCommand.BackCommand())
navigationDispatcher.navigateTo(NavigationCommand.ExternalUriCommand("https://example.com"))
```
