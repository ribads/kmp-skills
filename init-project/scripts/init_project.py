#!/usr/bin/env python3
"""Generate a full Synapse KMP project with multi-module DDD architecture.

Creates the complete project scaffold:
  - Root build files (settings.gradle.kts, build.gradle.kts, gradle.properties, libs.versions.toml)
  - androidApp/ with MainActivity and Android application setup
  - composeApp/ with DI wiring, MVI main screen, navigation, platform code (KMP library)
  - compose-ui/ with theme layer
  - core/ modules (network, auth, config, log)
  - domain/<name>/entities/ + domain/<name>/data/ per domain
  - features/<name>/usecase/ + features/<name>/ui/ per feature (with landing screen)
  - iosApp/ Swift files
"""

import argparse
import sys
from pathlib import Path


# ─── Helpers ───────────────────────────────────────────────────────────────────

def to_pascal(name: str) -> str:
    return name[0].upper() + name[1:] if name else name


def to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


def pkg_to_path(pkg: str) -> str:
    return pkg.replace(".", "/")


def render(template: str, ctx: dict) -> str:
    result = template
    for key, value in ctx.items():
        result = result.replace(f"__{key}__", value)
    return result


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        print(f"  SKIP {path} (exists)", file=sys.stderr)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"))
    print(f"  wrote {path}")


# ─── Root Build Files ──────────────────────────────────────────────────────────

SETTINGS_GRADLE = '''rootProject.name = "__PROJECT_NAME__"
enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

pluginManagement {
    repositories {
        google {
            mavenContent {
                includeGroupAndSubgroups("androidx")
                includeGroupAndSubgroups("com.android")
                includeGroupAndSubgroups("com.google")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositories {
        google {
            mavenContent {
                includeGroupAndSubgroups("androidx")
                includeGroupAndSubgroups("com.android")
                includeGroupAndSubgroups("com.google")
            }
        }
        mavenCentral()
        maven {
            url = uri("https://maven.pkg.github.com/ribads/outside-claude-api-server")
            credentials {
                username = providers.gradleProperty("gpr.user").orNull ?: System.getenv("GITHUB_ACTOR")
                password = providers.gradleProperty("gpr.key").orNull ?: System.getenv("GITHUB_TOKEN")
            }
        }
    }
}

include(":androidApp")
include(":composeApp")
include(":compose-ui")

include(":core:network")
include(":core:auth")
include(":core:config")
include(":core:log")

__DOMAIN_INCLUDES__
__FEATURE_INCLUDES__
'''

ROOT_BUILD_GRADLE = '''plugins {
    alias(libs.plugins.androidApplication) apply false
    alias(libs.plugins.androidLibrary) apply false
    alias(libs.plugins.androidMultiplatformLibrary) apply false
    alias(libs.plugins.composeMultiplatform) apply false
    alias(libs.plugins.composeCompiler) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.kotlinMultiplatform) apply false
    alias(libs.plugins.kotlin.android) apply false
}
'''

GRADLE_PROPERTIES = '''#Kotlin
kotlin.code.style=official
kotlin.daemon.jvmargs=-Xmx3072M

#Gradle
org.gradle.jvmargs=-Xmx4096M -Dfile.encoding=UTF-8
org.gradle.configuration-cache=true
org.gradle.caching=true

#Android
android.nonTransitiveRClass=true
android.useAndroidX=true
android.sdk.defaultTargetSdkToCompileSdkIfUnset=false
android.enableAppCompileTimeRClass=false
android.usesSdkInManifest.disallowed=false
android.uniquePackageNames=false
android.dependency.useConstraints=true
'''

GRADLE_WRAPPER_PROPERTIES = '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-9.4.1-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
'''

LIBS_VERSIONS_TOML = '''[versions]
agp = "9.1.0"
android-compileSdk = "36"
android-minSdk = "24"
android-targetSdk = "36"
androidx-activity = "1.13.0"
androidx-appcompat = "1.7.1"
androidx-core = "1.18.0"
androidx-lifecycle = "2.10.0"
composeMultiplatform = "1.10.3"
kotlin = "2.3.20"
synapse = "__SYNAPSE_VERSION__"
kotlinInject = "0.9.0"
ksp = "2.3.4"
ktor = "3.4.2"
composeNavigation = "2.9.2"
materialNavigation = "1.10.3"
coilCompose = "3.4.0"
coroutines = "1.10.2"
kermitLogger = "2.1.0"

[libraries]
kotlin-test = { module = "org.jetbrains.kotlin:kotlin-test", version.ref = "kotlin" }
androidx-core-ktx = { module = "androidx.core:core-ktx", version.ref = "androidx-core" }
androidx-appcompat = { module = "androidx.appcompat:appcompat", version.ref = "androidx-appcompat" }
androidx-activity-compose = { module = "androidx.activity:activity-compose", version.ref = "androidx-activity" }
androidx-lifecycle-viewmodelCompose = { module = "org.jetbrains.androidx.lifecycle:lifecycle-viewmodel-compose", version.ref = "androidx-lifecycle" }
androidx-lifecycle-runtimeCompose = { module = "org.jetbrains.androidx.lifecycle:lifecycle-runtime-compose", version.ref = "androidx-lifecycle" }
navigation-compose = { module = "org.jetbrains.androidx.navigation:navigation-compose", version.ref = "composeNavigation" }
material-navigation = { module = "org.jetbrains.compose.material:material-navigation", version.ref = "materialNavigation" }

coil-svg = { module = "io.coil-kt.coil3:coil-svg", version.ref = "coilCompose" }
coil-compose = { module = "io.coil-kt.coil3:coil-compose", version.ref = "coilCompose" }
coil-ktor = { module = "io.coil-kt.coil3:coil-network-ktor3", version.ref = "coilCompose" }

kermit-logger = { module = "co.touchlab:kermit", version.ref = "kermitLogger" }

coroutine-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }

ktor-client-core = { module = "io.ktor:ktor-client-core", version.ref = "ktor" }
ktor-client-okhttp = { module = "io.ktor:ktor-client-okhttp", version.ref = "ktor" }
ktor-client-darwin = { module = "io.ktor:ktor-client-darwin", version.ref = "ktor" }
ktor-client-android = { module = "io.ktor:ktor-client-android", version.ref = "ktor" }
ktor-client-logging = { module = "io.ktor:ktor-client-logging", version.ref = "ktor" }
ktor-serialization-kotlinx-json = { module = "io.ktor:ktor-serialization-kotlinx-json", version.ref = "ktor" }
ktor-content-negotiation = { module = "io.ktor:ktor-client-content-negotiation", version.ref = "ktor" }

synapse-ui-element = { module = "com.ribads.synapse:ui-element", version.ref = "synapse" }
synapse-ui-component = { module = "com.ribads.synapse:ui-component", version.ref = "synapse" }
synapse-ui-compose-presentation = { module = "com.ribads.synapse:ui-compose-presentation", version.ref = "synapse" }
synapse-ui-mvi = { module = "com.ribads.synapse:ui-mvi", version.ref = "synapse" }
synapse-core-discopes = { module = "com.ribads.synapse:core-discopes", version.ref = "synapse" }
synapse-core-datetime = { module = "com.ribads.synapse:core-datetime", version.ref = "synapse" }
synapse-core-shared-pref = { module = "com.ribads.synapse:core-sharedpref", version.ref = "synapse" }

kotlin-inject-compiler = { module = "me.tatarka.inject:kotlin-inject-compiler-ksp", version.ref = "kotlinInject" }
kotlin-inject-runtime = { module = "me.tatarka.inject:kotlin-inject-runtime", version.ref = "kotlinInject" }
kotlin-inject-runtime-kmp = { module = "me.tatarka.inject:kotlin-inject-runtime-kmp", version.ref = "kotlinInject" }

[plugins]
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
androidApplication = { id = "com.android.application", version.ref = "agp" }
androidLibrary = { id = "com.android.library", version.ref = "agp" }
androidMultiplatformLibrary = { id = "com.android.kotlin.multiplatform.library", version.ref = "agp" }
kotlinxSerialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
composeMultiplatform = { id = "org.jetbrains.compose", version.ref = "composeMultiplatform" }
composeCompiler = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }
kotlinMultiplatform = { id = "org.jetbrains.kotlin.multiplatform", version.ref = "kotlin" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
'''

# ─── androidApp ───────────────────────────────────────────────────────────────

ANDROID_APP_BUILD_GRADLE = '''plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
}

android {
    namespace = "__BASE_PACKAGE__.app"
    compileSdk = libs.versions.android.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "__BASE_PACKAGE__.app"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = libs.versions.android.targetSdk.get().toInt()
        versionCode = 1
        versionName = "1.0"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
    buildFeatures {
        buildConfig = true
        compose = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(projects.composeApp)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.activity.compose)
}
'''

ANDROID_MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:label="__PROJECT_NAME__"
        android:supportsRtl="true"
        android:theme="@style/Theme.__PROJECT_NAME__">

        <activity
            android:name="__BASE_PACKAGE__.app.MainActivity"
            android:exported="true"
            android:theme="@style/Theme.__PROJECT_NAME__">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

ANDROID_STRINGS_XML = '''<resources>
    <string name="app_name">__PROJECT_NAME__</string>
</resources>
'''

ANDROID_THEMES_XML = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.__PROJECT_NAME__" parent="Theme.AppCompat.Light.NoActionBar">
        <item name="android:statusBarColor">@android:color/transparent</item>
        <item name="android:navigationBarColor">@android:color/transparent</item>
    </style>
</resources>
'''

MAIN_ACTIVITY = '''package __APP_PACKAGE__

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        val appContext = AppContext(applicationContext)

        setContent {
            CoreComposeApp(appContext = appContext)
        }
    }
}
'''

# ─── composeApp ────────────────────────────────────────────────────────────────

COMPOSE_APP_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.ExperimentalKotlinGradlePluginApi
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask
import kotlin.jvm.java

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidMultiplatformLibrary)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.ksp)
}

kotlin {
    android {
        androidResources { enable = true }
        namespace = "__BASE_PACKAGE__.composeapp"
        compileSdk = libs.versions.android.compileSdk.get().toInt()
        minSdk = libs.versions.android.minSdk.get().toInt()

        @OptIn(ExperimentalKotlinGradlePluginApi::class)
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_21)
        }
    }

    listOf(
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "ComposeApp"
            isStatic = true
        }
    }
    configureCommonMainKsp()
    sourceSets {
        androidMain.dependencies {
            implementation(compose.preview)
            implementation(compose.uiTooling)
            implementation(libs.androidx.appcompat)
            implementation(libs.androidx.activity.compose)
            implementation(libs.ktor.client.android)
            implementation(libs.coil.compose)
        }
        iosMain.dependencies {
            implementation(libs.ktor.client.darwin)
        }
        commonMain.dependencies {
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation(compose.components.resources)
            implementation(compose.components.uiToolingPreview)
            implementation(libs.androidx.lifecycle.viewmodelCompose)
            implementation(libs.androidx.lifecycle.runtimeCompose)
            implementation(libs.navigation.compose)
            implementation(libs.material.navigation)

            implementation(libs.coil.svg)
            implementation(libs.kotlin.inject.runtime.kmp)

            implementation(libs.synapse.ui.compose.presentation)
            implementation(libs.synapse.ui.mvi)
            implementation(libs.synapse.ui.element)
            implementation(libs.synapse.ui.component)
            implementation(libs.synapse.core.discopes)
            implementation(libs.synapse.core.datetime)
            implementation(libs.synapse.core.shared.pref)

            implementation(projects.core.auth)
            implementation(projects.core.config)
            implementation(projects.core.log)
            implementation(projects.core.network)

            implementation(projects.composeUi)

__COMPOSE_APP_DOMAIN_DEPS__
__COMPOSE_APP_FEATURE_DEPS__
        }
        commonTest.dependencies {
            implementation(libs.kotlin.test)
        }
    }
}

dependencies {
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}

fun KotlinMultiplatformExtension.configureCommonMainKsp() {
    sourceSets.named("commonMain").configure {
        kotlin.srcDir("build/generated/ksp/metadata/commonMain/kotlin")
    }

    project.tasks.withType(KotlinCompilationTask::class.java).configureEach {
        if (name != "kspCommonMainKotlinMetadata") {
            dependsOn("kspCommonMainKotlinMetadata")
        }
    }
}
'''

# ── composeApp: AppContext ──

APP_CONTEXT_EXPECT = '''package __APP_PACKAGE__

import __BASE_PACKAGE__.core.log.ErrorLogger

expect class AppContext constructor(any: Any)

internal expect fun buildErrorLogger(): ErrorLogger
'''

APP_CONTEXT_ANDROID = '''package __APP_PACKAGE__

import android.content.Context
import __BASE_PACKAGE__.core.log.ErrorLogger

actual class AppContext actual constructor(any: Any) {
    var context: Context
        private set

    init {
        context = any as Context
    }
}

internal actual fun buildErrorLogger(): ErrorLogger {
    return object : ErrorLogger {
        override fun log(message: String) {
            android.util.Log.e("__PROJECT_NAME__", message)
        }

        override fun log(exception: Exception) {
            android.util.Log.e("__PROJECT_NAME__", exception.message ?: "Unknown error", exception)
        }

        override fun log(throwable: Throwable) {
            android.util.Log.e("__PROJECT_NAME__", throwable.message ?: "Unknown error", throwable)
        }
    }
}
'''

APP_CONTEXT_IOS = '''package __APP_PACKAGE__

import __BASE_PACKAGE__.core.log.ErrorLogger
import platform.Foundation.NSLog

actual class AppContext actual constructor(any: Any)

internal actual fun buildErrorLogger(): ErrorLogger {
    return object : ErrorLogger {
        override fun log(message: String) {
            NSLog("__PROJECT_NAME__ error: %s", message)
        }

        override fun log(exception: Exception) {
            NSLog("__PROJECT_NAME__ error: %s", exception.message)
        }

        override fun log(throwable: Throwable) {
            NSLog("__PROJECT_NAME__ error: %s", throwable.message)
        }
    }
}
'''

# ── composeApp: CoreComposeApp ──

CORE_COMPOSE_APP = '''package __APP_PACKAGE__

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.lifecycle.viewmodel.compose.viewModel
import coil3.ImageLoader
import coil3.compose.setSingletonImageLoaderFactory
import coil3.memory.MemoryCache
import coil3.request.CachePolicy
import coil3.request.crossfade
import coil3.svg.SvgDecoder
import __APP_PACKAGE__.di.RootAppBuilder
import __BASE_PACKAGE__.compose.ui.theme.__PROJECT_NAME__Theme
import com.ribads.synapse.ui.element.image.ImagePainterFactory
import com.ribads.synapse.ui.element.image.WithImagePainter

@Composable
fun CoreComposeApp(appContext: AppContext) {
    val app = remember { RootAppBuilder.build(appContext) }

    setSingletonImageLoaderFactory { context ->
        ImageLoader.Builder(context)
            .components {
                add(SvgDecoder.Factory())
            }
            .memoryCachePolicy(CachePolicy.ENABLED)
            .memoryCache {
                MemoryCache.Builder()
                    .maxSizePercent(context, 0.3)
                    .strongReferencesEnabled(true)
                    .build()
            }
            .crossfade(true)
            .build()
    }

    val imagePainterFactory = ImagePainterFactory.createPainterFactory()

    WithImagePainter(imagePainterFactory = imagePainterFactory) {
        __PROJECT_NAME__Theme {
            RootScreen(
                viewModel = viewModel { app.mainViewModel },
                navigatorHost = app.root,
            )
        }
    }
}
'''

# ── composeApp: RootScreen ──

ROOT_SCREEN = '''package __APP_PACKAGE__

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material.navigation.ModalBottomSheetLayout
import androidx.compose.material.navigation.rememberBottomSheetNavigator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import __APP_PACKAGE__.ui.MainContract
import __APP_PACKAGE__.ui.MainViewModel
import __APP_PACKAGE__.ui.navigation.MainNavigationDispatcher
import com.ribads.synapse.ui.component.scaffold.Scaffold
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavContainer
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavigatorHost
import com.ribads.synapse.ui.compose.presentation.navigation.compose.rememberNavController
import com.ribads.synapse.ui.mvi.CollectAsEffect
import com.ribads.synapse.ui.mvi.OnFirstComposition

@Composable
internal fun RootScreen(
    viewModel: MainViewModel,
    navigatorHost: NavigatorHost.Root,
) {
    val viewState by remember { derivedStateOf { viewModel.state.value } }

    viewModel.OnFirstComposition(MainContract.Intent.Initial)

    Scaffold { paddingValues ->
        val bottomSheetNavigator = rememberBottomSheetNavigator()
        val navController =
            rememberNavController(arrayOf(bottomSheetNavigator)) { _, destination, _ ->
                val cRoute = "${destination.parent?.route}/${destination.route}"
                viewModel.emit(
                    intent = MainContract.Intent.RouteChanged(
                        previousRoute = viewState.currentRoute ?: "",
                        route = cRoute,
                    )
                )
            }

        val navDispatcher =
            remember { MainNavigationDispatcher(navController = navController) }

        viewModel.effects.CollectAsEffect { effect ->
            when (effect) {
                is MainContract.Effect.Navigate -> navDispatcher.navigateTo(effect.command)
            }
        }

        viewState.startDestinationRoute?.let { startRoute ->
            var route by rememberSaveable { mutableStateOf(startRoute) }
            if (route != startRoute) route = startRoute
            ModalBottomSheetLayout(bottomSheetNavigator) {
                NavContainer(
                    modifier = Modifier
                        .fillMaxHeight()
                        .fillMaxWidth()
                        .padding(paddingValues = paddingValues),
                    startDestination = route,
                    navigatorHost = navigatorHost,
                    navHostController = navController,
                    pageTransition = viewState.pageTransition,
                )
            }
        }
    }
}
'''

# ── composeApp: MainViewController (iOS) ──

MAIN_VIEW_CONTROLLER = '''package __APP_PACKAGE__

import androidx.compose.ui.window.ComposeUIViewController
import platform.UIKit.UIViewController

fun MainViewController(): UIViewController {
    val appContext = AppContext("ios")

    return ComposeUIViewController {
        CoreComposeApp(appContext = appContext)
    }
}
'''

# ── composeApp MVI (ui package) ──

MAIN_CONTRACT = '''package __APP_PACKAGE__.ui

import androidx.compose.runtime.Immutable
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand
import com.ribads.synapse.ui.compose.presentation.navigation.compose.PageTransition

internal interface MainContract {

    interface Mapper {
        fun toResult(intent: Intent.Initial): Result
        fun toResult(intent: Intent.RouteChanged): Result.RouteChanged
    }

    sealed class Intent {
        data object Initial : Intent()
        data class RouteChanged(val previousRoute: String, val route: String) : Intent()
    }

    sealed class Result {

        data class Initial(
            val startDestinationRoute: String,
        ) : Result()

        data class RouteChanged(
            val route: String,
            val pageTransition: PageTransition,
        ) : Result()
    }

    sealed class Effect {
        data class Navigate(val command: NavigationCommand) : Effect()
    }

    @Immutable
    data class ViewState(
        val startDestinationRoute: String? = null,
        val currentRoute: String?,
        val pageTransition: PageTransition,
    ) {
        companion object {
            val Default = ViewState(
                startDestinationRoute = null,
                currentRoute = null,
                pageTransition = PageTransition.Hierarchical,
            )
        }
    }
}
'''

MAIN_INTERACTOR = '''package __APP_PACKAGE__.ui

import __APP_PACKAGE__.ui.MainContract.Intent
import __APP_PACKAGE__.ui.MainContract.Mapper
import __APP_PACKAGE__.ui.MainContract.Result
import __APP_PACKAGE__.ui.MainContract.ViewState
import com.ribads.synapse.ui.mvi.Interactor
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.merge

internal class MainInteractor constructor(
    private val mapper: Mapper,
) : Interactor<Intent, Result, ViewState> {

    override fun process(
        intents: Flow<Intent>,
        state: StateFlow<ViewState>,
    ): Flow<Result> {
        return merge(
            intents.filterIsInstance<Intent.Initial>().map(mapper::toResult),
            intents.filterIsInstance<Intent.RouteChanged>().map(mapper::toResult),
        )
    }
}
'''

MAIN_REDUCER = '''package __APP_PACKAGE__.ui

import __APP_PACKAGE__.ui.MainContract.Effect
import __APP_PACKAGE__.ui.MainContract.Result
import __APP_PACKAGE__.ui.MainContract.ViewState
import com.ribads.synapse.ui.mvi.Reducer
import com.ribads.synapse.ui.mvi.Reduction
import com.ribads.synapse.ui.mvi.noEffects

internal class MainReducer constructor() : Reducer<ViewState, Result, Effect> {
    override fun reduce(state: ViewState, result: Result): Reduction<ViewState, Effect> {
        return when (result) {
            is Result.Initial -> state.copy(startDestinationRoute = result.startDestinationRoute).noEffects()
            is Result.RouteChanged -> state.copy(
                currentRoute = result.route,
                pageTransition = result.pageTransition,
            ).noEffects()
        }
    }
}
'''

MAIN_MAPPER = '''package __APP_PACKAGE__.ui

import __APP_PACKAGE__.ui.MainContract.Intent
import __APP_PACKAGE__.ui.MainContract.Mapper
import __APP_PACKAGE__.ui.MainContract.Result
import com.ribads.synapse.ui.compose.presentation.navigation.compose.PageTransition
import me.tatarka.inject.annotations.Inject

internal class MainMapper @Inject constructor() : Mapper {

    override fun toResult(intent: Intent.Initial): Result {
        return Result.Initial(startDestinationRoute = "__FIRST_FEATURE__")
    }

    override fun toResult(intent: Intent.RouteChanged) = Result.RouteChanged(
        route = intent.route,
        pageTransition = PageTransition.Hierarchical,
    )
}
'''

MAIN_VIEW_MODEL = '''package __APP_PACKAGE__.ui

import com.ribads.synapse.ui.mvi.FlowViewModelArgs
import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.LifecycleViewModel
import com.ribads.synapse.ui.mvi.Reducer
import me.tatarka.inject.annotations.Inject

@Inject
internal class MainViewModel constructor(
    initialState: MainContract.ViewState,
    interactor: Interactor<MainContract.Intent, MainContract.Result, MainContract.ViewState>,
    reducer: Reducer<MainContract.ViewState, MainContract.Result, MainContract.Effect>,
) : LifecycleViewModel<MainContract.Intent, MainContract.Result, MainContract.ViewState, MainContract.Effect>(
    args = FlowViewModelArgs(
        initialState = initialState,
        reducer = reducer,
        interactor = interactor,
    ),
)
'''

MAIN_UI_COMPONENT = '''package __APP_PACKAGE__.ui.di

import __APP_PACKAGE__.ui.MainContract.Effect
import __APP_PACKAGE__.ui.MainContract.Intent
import __APP_PACKAGE__.ui.MainContract.Result
import __APP_PACKAGE__.ui.MainContract.ViewState
import __APP_PACKAGE__.ui.MainInteractor
import __APP_PACKAGE__.ui.MainMapper
import __APP_PACKAGE__.ui.MainReducer
import __APP_PACKAGE__.ui.MainViewModel
import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.Reducer
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
internal abstract class MainUiComponent {
    abstract val viewModel: MainViewModel

    @Provides
    protected fun provideDefaultState(): ViewState = ViewState.Default

    @Provides
    protected fun provideInteractor(): Interactor<Intent, Result, ViewState> =
        MainInteractor(mapper = MainMapper())

    @Provides
    fun provideReducer(): Reducer<ViewState, Result, Effect> = MainReducer()
}
'''

# ── composeApp: Navigation ──

MAIN_NAVIGATOR_HOST = '''package __APP_PACKAGE__.ui.navigation

import androidx.navigation.NavGraphBuilder
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavigatorHost
import me.tatarka.inject.annotations.Inject
import kotlin.jvm.JvmSuppressWildcards

@Inject
internal class MainNavigatorHost constructor(
    private val launcher: Map<String, @JvmSuppressWildcards FeatureLauncher>,
) : NavigatorHost.Root {

    override fun buildGraph(builder: NavGraphBuilder, navigationDispatcher: NavigationDispatcher) {
        launcher
            .map { launcher -> launcher.value }
            .map { navigationHost -> navigationHost.navigationGraph() }
            .onEach { navigationHost: NavigatorHost.Child ->
                navigationHost.buildGraph(builder, navigationDispatcher)
            }
    }
}
'''

MAIN_NAVIGATION_DISPATCHER = '''package __APP_PACKAGE__.ui.navigation

import androidx.navigation.NavController
import androidx.navigation.NavOptionsBuilder
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import me.tatarka.inject.annotations.Inject

internal class NavigationNotSupportedException(message: String) : Exception(message)

internal class MainNavigationDispatcher @Inject constructor(
    private val navController: NavController,
    private val builderProducer: NavOptionsBuilderProducer = NavOptionsBuilderProducer(navController = navController),
) : NavigationDispatcher {

    override fun navigateTo(command: NavigationCommand) {
        when (command) {
            is NavigationCommand.FeatureCommand -> {
                when (command.clearStack) {
                    true -> navController.navigate(
                        route = command.featureName,
                        builder = builderProducer::navOptionsBuilder,
                    )
                    false -> navController.navigate(route = command.featureName)
                }
            }
            else -> throw NavigationNotSupportedException(message = "navigation to $command is not supported")
        }
    }
}

internal class NavOptionsBuilderProducer(
    private val navController: NavController,
) {
    fun navOptionsBuilder(builder: NavOptionsBuilder) {
        var popResult = navController.popBackStack()
        while (popResult) {
            popResult = navController.popBackStack()
        }
    }
}
'''

# ── composeApp: DI ──

NETWORK_COMPONENT = '''package __APP_PACKAGE__.di

import __BASE_PACKAGE__.core.auth.OauthTokenProvider
import __BASE_PACKAGE__.core.network.CoreClient
import __BASE_PACKAGE__.core.network.CoreClientImpl
import com.ribads.synapse.core.discopes.SingletonScope
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@SingletonScope
@Component
internal abstract class NetworkComponent(
    private val tokenProvider: OauthTokenProvider,
) {
    abstract val client: CoreClient

    @SingletonScope
    @Provides
    fun provideCoreClient(): CoreClient =
        CoreClientImpl(tokenProvider, buildAppConfigurationProvider())
}
'''

# ── RootAppBuilder (assembled dynamically) ──

ROOT_APP_BUILDER_HEAD = '''package __APP_PACKAGE__.di

import __APP_PACKAGE__.AppContext
import __APP_PACKAGE__.buildErrorLogger
import __APP_PACKAGE__.ui.MainViewModel
import __APP_PACKAGE__.ui.di.MainUiComponent
import __APP_PACKAGE__.ui.di.create
import __BASE_PACKAGE__.core.auth.OauthTokenProvider
'''

ROOT_APP_BUILDER_DOMAIN_IMPORT = '''import __BASE_PACKAGE__.domain.__DOMAIN__.data.di.__DOMAIN_PASCAL__RepositoryProvidersImpl
import __BASE_PACKAGE__.domain.__DOMAIN__.data.di.create
'''

ROOT_APP_BUILDER_FEATURE_IMPORT = '''import __BASE_PACKAGE__.feature.__FEATURE__.ui.di.__FEATURE_PASCAL__Module
import __BASE_PACKAGE__.feature.__FEATURE__.ui.di.create
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.__FEATURE_PASCAL__UseCaseModule
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.create
'''

ROOT_APP_BUILDER_CLASS = '''import com.ribads.synapse.core.sharedpref.buildSharedPrefManager
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavigatorHost

internal class __PROJECT_NAME__App(
    val root: NavigatorHost.Root,
    val mainViewModel: MainViewModel,
)

internal object RootAppBuilder {

    fun build(appContext: AppContext): __PROJECT_NAME__App {

        val authTokenStorage = buildSharedPrefManager("__PROJECT_NAME_LOWER__")
        val tokenProvider = OauthTokenProvider.create(authTokenStorage)
        val networkComponent = NetworkComponent::class.create(tokenProvider)
        val errorLogger = buildErrorLogger()

__DOMAIN_BUILDS__
__FEATURE_BUILDS__
        val mainViewModel = MainUiComponent::class.create()

        val appComponent = ComposeAppComponent::class.create(
__FEATURE_PARAMS__
        )

        return __PROJECT_NAME__App(
            root = appComponent.root,
            mainViewModel = mainViewModel.viewModel,
        )
    }
}
'''

# ── ComposeAppComponent (assembled dynamically) ──

COMPOSE_APP_COMPONENT_HEAD = '''package __APP_PACKAGE__.di

import __APP_PACKAGE__.ui.navigation.MainNavigatorHost
'''

COMPOSE_APP_COMPONENT_FEATURE_IMPORT = '''import __BASE_PACKAGE__.feature.__FEATURE__.ui.di.__FEATURE_PASCAL__Module
'''

COMPOSE_APP_COMPONENT_CLASS = '''import com.ribads.synapse.core.discopes.SingletonScope
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavigatorHost
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@SingletonScope
@Component
internal abstract class ComposeAppComponent(
__FEATURE_CONSTRUCTOR_PARAMS__
) {
    abstract val root: NavigatorHost.Root

    protected val MainNavigatorHost.bind: NavigatorHost.Root
        @Provides get() = this

    @Provides
    fun provideFeatures(): Map<String, FeatureLauncher> =
__FEATURE_MAP_ENTRIES__
}
'''

# ─── compose-ui ───────────────────────────────────────────────────────────────

COMPOSE_UI_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.ExperimentalKotlinGradlePluginApi
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidMultiplatformLibrary)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
}

kotlin {
    android {
        androidResources { enable = true }
        namespace = "__BASE_PACKAGE__.compose.ui"
        compileSdk = libs.versions.android.compileSdk.get().toInt()
        minSdk = libs.versions.android.minSdk.get().toInt()

        @OptIn(ExperimentalKotlinGradlePluginApi::class)
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_21)
        }
    }

    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "ComposeUi"
            isStatic = true
        }
    }

    sourceSets {
        androidMain.dependencies {
            implementation(compose.preview)
            implementation(libs.androidx.activity.compose)
        }
        commonMain.dependencies {
            api(compose.runtime)
            api(compose.foundation)
            api(compose.material)
            api(compose.material3)
            api(compose.ui)
            implementation(compose.components.resources)
            api(compose.components.uiToolingPreview)

            implementation(libs.synapse.ui.element)
            implementation(libs.synapse.ui.component)
        }
    }
}
'''

APP_THEME = '''package __BASE_PACKAGE__.compose.ui.theme

import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ribads.synapse.ui.element.theme.Border
import com.ribads.synapse.ui.element.theme.Colors
import com.ribads.synapse.ui.element.theme.Element
import com.ribads.synapse.ui.element.theme.ElementInteractive
import com.ribads.synapse.ui.element.theme.IntentPalette
import com.ribads.synapse.ui.element.theme.Intents
import com.ribads.synapse.ui.element.theme.Shadow
import com.ribads.synapse.ui.element.theme.Shape
import com.ribads.synapse.ui.element.theme.Surface
import com.ribads.synapse.ui.element.theme.SurfaceInteractive
import com.ribads.synapse.ui.element.theme.Typography
import com.ribads.synapse.ui.element.theme.WithTheme

@Composable
fun __PROJECT_NAME__Theme(
    content: @Composable () -> Unit,
) {
    val colors = Colors(
        surface = Surface(
            primaryLight = Color(0xFFFAFAFA),
            secondaryLight = Color(0xFFF5F5F5),
            subtleLight = Color(0xFFE0E0E0),
            primaryDark = Color(0xFF121212),
            secondaryDark = Color(0xFF1E1E1E),
            subtleDark = Color(0xFF2C2C2C),
        ),
        surfaceInteractive = SurfaceInteractive(
            enabledOnLight = Color(0xFF6366F1),
            disabledOnLight = Color(0xFF6366F1).copy(alpha = 0.2f),
            hoverTapOnLight = Color(0xFF818CF8),
            enabledOnDark = Color(0xFF6366F1),
            hoverTapOnDark = Color(0xFF4F46E5),
            disabledOnDark = Color(0xFF374151),
        ),
        border = Border(
            primaryOnLight = Color(0xFFE0E0E0),
            secondaryOnLight = Color(0xFF9CA3AF),
            emphasisOnLight = Color(0xFF6366F1),
            primaryOnDark = Color(0xFF374151),
            secondaryOnDark = Color(0xFF4B5563),
            emphasisOnDark = Color(0xFFFFFFFF),
        ),
        element = Element(
            primaryOnLight = Color(0xFF111827),
            secondaryOnLight = Color(0xFF6B7280),
            primaryOnDark = Color(0xFFFFFFFF),
            secondaryOnDark = Color(0xFF9CA3AF),
        ),
        elementInteractive = ElementInteractive(
            enabledOnLight = Color(0xFFFFFFFF),
            disabledOnLight = Color(0xFFFFFFFF),
            hoverTapOnLight = Color(0xFF6366F1),
            enabledOnDark = Color(0xFF111827),
            hoverTapOnDark = Color(0xFF9CA3AF),
            disabledOnDark = Color(0xFF374151),
        ),
        shadow = Shadow(
            spotOnDark = Color(0x33000000),
            spotOnLight = Color(0x1A000000),
        ),
        intents = Intents(
            accent = IntentPalette(
                contentOnLight = Color(0xFF6366F1),
                contentOnDark = Color(0xFF818CF8),
                surfaceOnLight = Color(0xFFEEF2FF),
                surfaceOnDark = Color(0xFF312E81),
                borderOnLight = Color(0xFF6366F1),
                borderOnDark = Color(0xFF818CF8),
            ),
            success = IntentPalette(
                contentOnLight = Color(0xFF059669),
                contentOnDark = Color(0xFF34D399),
                surfaceOnLight = Color(0xFFECFDF5),
                surfaceOnDark = Color(0xFF064E3B),
                borderOnLight = Color(0xFF059669),
                borderOnDark = Color(0xFF34D399),
            ),
            error = IntentPalette(
                contentOnLight = Color(0xFFDC2626),
                contentOnDark = Color(0xFFFCA5A5),
                surfaceOnLight = Color(0xFFFEF2F2),
                surfaceOnDark = Color(0xFF7F1D1D),
                borderOnLight = Color(0xFFDC2626),
                borderOnDark = Color(0xFFFCA5A5),
            ),
            warning = IntentPalette(
                contentOnLight = Color(0xFFD97706),
                contentOnDark = Color(0xFFFCD34D),
                surfaceOnLight = Color(0xFFFFFBEB),
                surfaceOnDark = Color(0xFF78350F),
                borderOnLight = Color(0xFFD97706),
                borderOnDark = Color(0xFFFCD34D),
            ),
        ),
    )

    val typography = Typography(
        h1 = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Bold,
            fontSize = 40.sp,
            color = colors.element.primaryOnLight,
        ),
        h2 = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.SemiBold,
            fontSize = 32.sp,
            color = colors.element.primaryOnLight,
        ),
        h3 = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Medium,
            fontSize = 24.sp,
            color = colors.element.primaryOnLight,
        ),
        h4 = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Medium,
            fontSize = 18.sp,
            color = colors.element.primaryOnLight,
        ),
        headingS = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Normal,
            fontSize = 14.sp,
            color = colors.element.primaryOnLight,
        ),
        headingM = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.SemiBold,
            fontSize = 16.sp,
            color = colors.element.primaryOnLight,
        ),
        body = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.SemiBold,
            fontSize = 16.sp,
            color = colors.element.secondaryOnLight,
        ),
        bodyM = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Medium,
            fontSize = 16.sp,
            color = colors.element.secondaryOnLight,
        ),
        bodyS = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Normal,
            fontSize = 14.sp,
            lineHeight = 20.sp,
            color = colors.element.secondaryOnLight,
        ),
        bodyXs = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Normal,
            fontSize = 12.sp,
            color = colors.element.secondaryOnLight,
        ),
        labelS = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Normal,
            fontSize = 12.sp,
            color = colors.element.secondaryOnLight,
        ),
        labelXs = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.Normal,
            fontSize = 10.sp,
            color = colors.element.secondaryOnLight,
        ),
        button = TextStyle(
            fontFamily = FontFamily.Default,
            fontWeight = FontWeight.SemiBold,
            fontSize = 16.sp,
            color = colors.elementInteractive.enabledOnLight,
        ),
    )

    val shape = Shape(
        buttonShape = RoundedCornerShape(percent = 50),
        circleShape = RoundedCornerShape(50),
        roundShape = RoundedCornerShape(16.dp),
        imageShape = CircleShape,
        card = RoundedCornerShape(8.dp),
        textShape = RoundedCornerShape(4.dp),
        chipShape = RoundedCornerShape(8.dp),
    )

    WithTheme(
        colors = colors,
        typography = typography,
        content = content,
        shape = shape,
    )
}
'''

# ─── core modules ─────────────────────────────────────────────────────────────

# core:network — Pure KMP (jvm + iOS), no Android plugin
CORE_NETWORK_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.kotlinxSerialization)
    alias(libs.plugins.ksp)
}

kotlin {
    jvm()
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "CoreNetwork"
            isStatic = true
        }
    }
    sourceSets {
        commonMain.dependencies {
            implementation(libs.coroutine.core)
            implementation(libs.ktor.client.core)
            implementation(libs.ktor.content.negotiation)
            implementation(libs.ktor.client.logging)
            implementation(libs.kermit.logger)
            api(libs.ktor.serialization.kotlinx.json)
            implementation(libs.kotlin.inject.runtime.kmp)
            implementation(project(":core:auth"))
            api(libs.synapse.core.discopes)
            api(project(":core:config"))
            api(project(":core:log"))
        }
        jvmMain.dependencies {
            implementation(libs.ktor.client.okhttp)
        }
        iosMain.dependencies {
            implementation(libs.ktor.client.darwin)
        }
    }
}

dependencies {
    add("commonMainImplementation", libs.ktor.client.core)
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}
'''

# core:auth — KMP with KSP
CORE_AUTH_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.kotlinxSerialization)
    alias(libs.plugins.ksp)
}

kotlin {
    jvm()
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    )
    configureCommonMainKsp()
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(libs.coroutine.core)
                implementation(libs.kotlin.inject.runtime.kmp)
                implementation(libs.synapse.core.shared.pref)
                implementation(libs.ktor.serialization.kotlinx.json)
            }
        }
    }
}

dependencies {
    kspCommonMainMetadata(libs.kotlin.inject.compiler)
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}

fun KotlinMultiplatformExtension.configureCommonMainKsp() {
    sourceSets.named("commonMain").configure {
        kotlin.srcDir("build/generated/ksp/metadata/commonMain/kotlin")
    }
    project.tasks.withType(KotlinCompilationTask::class.java).configureEach {
        if (name != "kspCommonMainKotlinMetadata") {
            dependsOn("kspCommonMainKotlinMetadata")
        }
    }
}
'''

# core:config — Plain KMP, no KSP
CORE_CONFIG_BUILD_GRADLE = '''plugins {
    alias(libs.plugins.kotlinMultiplatform)
}

kotlin {
    jvm()
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "CoreConfig"
            isStatic = true
        }
    }
    sourceSets {
        commonMain.dependencies {
        }
    }
}
'''

# core:log — KMP with KSP
CORE_LOG_BUILD_GRADLE = '''plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.ksp)
}

kotlin {
    jvm()
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "core.discopes"
            isStatic = true
        }
    }
    sourceSets {
        commonMain.dependencies {
            implementation(libs.kotlin.inject.runtime.kmp)
        }
    }
}

dependencies {
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}
'''

# ── Core Kotlin sources ──

CORE_CLIENT = '''package __BASE_PACKAGE__.core.network

import io.ktor.client.HttpClient

interface CoreClient {
    val httpClient: HttpClient
}
'''

CORE_CLIENT_IMPL = '''package __BASE_PACKAGE__.core.network

import __BASE_PACKAGE__.core.auth.OauthTokenProvider
import __BASE_PACKAGE__.core.config.AppConfigurationProvider
import io.ktor.client.HttpClient

internal class CoreClientImpl(
    private val tokenProvider: OauthTokenProvider,
    private val configProvider: AppConfigurationProvider,
) : CoreClient {
    override val httpClient: HttpClient
        get() = createHttpClient(tokenProvider, configProvider)
}
'''

HTTP_CLIENT_EXPECT = '''package __BASE_PACKAGE__.core.network

import __BASE_PACKAGE__.core.auth.OauthTokenProvider
import __BASE_PACKAGE__.core.config.AppConfigurationProvider
import io.ktor.client.HttpClient

internal expect fun createHttpClient(
    tokenProvider: OauthTokenProvider,
    configProvider: AppConfigurationProvider,
): HttpClient
'''

HTTP_CLIENT_JVM = '''package __BASE_PACKAGE__.core.network

import __BASE_PACKAGE__.core.auth.OauthTokenProvider
import __BASE_PACKAGE__.core.config.AppConfigurationProvider
import io.ktor.client.HttpClient
import io.ktor.client.engine.okhttp.OkHttp

internal actual fun createHttpClient(
    tokenProvider: OauthTokenProvider,
    configProvider: AppConfigurationProvider,
): HttpClient {
    return HttpClient(OkHttp) {
        // TODO: configure engine, install plugins, etc.
    }
}
'''

HTTP_CLIENT_IOS = '''package __BASE_PACKAGE__.core.network

import __BASE_PACKAGE__.core.auth.OauthTokenProvider
import __BASE_PACKAGE__.core.config.AppConfigurationProvider
import io.ktor.client.HttpClient
import io.ktor.client.engine.darwin.Darwin

internal actual fun createHttpClient(
    tokenProvider: OauthTokenProvider,
    configProvider: AppConfigurationProvider,
): HttpClient {
    return HttpClient(Darwin) {
        // TODO: configure engine, install plugins, etc.
    }
}
'''

CORE_REQUEST_ERROR = '''package __BASE_PACKAGE__.core.network

sealed class CoreRequestError {
    data class HttpError(val code: Int, val message: String) : CoreRequestError()
    data class NetworkError(val throwable: Throwable) : CoreRequestError()
    data object Unknown : CoreRequestError()
}
'''

OAUTH_TOKEN = '''package __BASE_PACKAGE__.core.auth

import kotlinx.serialization.Serializable

@Serializable
data class OauthToken(
    val accessToken: String,
    val refreshToken: String?,
    val expiresIn: Long?,
)
'''

OAUTH_TOKEN_PROVIDER = '''package __BASE_PACKAGE__.core.auth

import com.ribads.synapse.core.sharedpref.SharedPrefManager
import me.tatarka.inject.annotations.Inject

class OauthTokenProvider @Inject constructor(
    private val storage: SharedPrefManager,
) {
    fun getAccessToken(): String? = storage.getString("access_token")
    fun setAccessToken(token: String) = storage.putString("access_token", token)
    fun clear() = storage.clear()

    companion object {
        fun create(storage: SharedPrefManager): OauthTokenProvider =
            OauthTokenProvider(storage)
    }
}
'''

APP_CONFIGURATION_PROVIDER = '''package __BASE_PACKAGE__.core.config

interface AppConfigurationProvider {
    val baseUrl: String
}
'''

CONFIGURATION_PROPERTIES = '''package __BASE_PACKAGE__.core.config

data class ConfigurationProperties(
    override val baseUrl: String,
) : AppConfigurationProvider
'''

BUILD_APP_CONFIGURATION_PROVIDER = '''package __APP_PACKAGE__.di

import __BASE_PACKAGE__.core.config.AppConfigurationProvider
import __BASE_PACKAGE__.core.config.ConfigurationProperties

internal fun buildAppConfigurationProvider(): AppConfigurationProvider {
    return ConfigurationProperties(
        baseUrl = "https://api.example.com",
    )
}
'''

ERROR_LOGGER = '''package __BASE_PACKAGE__.core.log

interface ErrorLogger {
    fun log(message: String)
    fun log(exception: Exception)
    fun log(throwable: Throwable)
}
'''

# ─── domain modules ───────────────────────────────────────────────────────────

DOMAIN_ENTITIES_BUILD_GRADLE = '''plugins {
    alias(libs.plugins.kotlinMultiplatform)
}

kotlin {
    jvm()
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    )
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(libs.coroutine.core)
                implementation(libs.kotlin.inject.runtime.kmp)
            }
        }
    }
}
'''

DOMAIN_REPOSITORY = '''package __BASE_PACKAGE__.domain.__DOMAIN__.entities

interface __DOMAIN_PASCAL__Repository {
    // TODO: define repository methods
}
'''

DOMAIN_REPOSITORY_PROVIDERS = '''package __BASE_PACKAGE__.domain.__DOMAIN__.entities.di

import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository

interface __DOMAIN_PASCAL__RepositoryProviders {
    val __DOMAIN_CAMEL__Repository: __DOMAIN_PASCAL__Repository
}
'''

DOMAIN_DATA_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.ExperimentalKotlinGradlePluginApi
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    alias(libs.plugins.androidMultiplatformLibrary)
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.ksp)
    alias(libs.plugins.kotlinxSerialization)
}

kotlin {
    android {
        namespace = "__BASE_PACKAGE__.domain.__DOMAIN__"
        compileSdk = libs.versions.android.compileSdk.get().toInt()
        minSdk = libs.versions.android.minSdk.get().toInt()

        @OptIn(ExperimentalKotlinGradlePluginApi::class)
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_21)
        }
    }

    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "domain-__DOMAIN__"
            isStatic = true
        }
    }

    configureCommonMainKsp()
    sourceSets {
        androidMain.dependencies {
            implementation(libs.ktor.client.okhttp)
        }
        iosMain.dependencies {
            implementation(libs.ktor.client.darwin)
        }
        commonMain.dependencies {
            implementation(libs.kermit.logger)
            implementation(libs.coil.ktor)
            implementation(libs.kotlin.inject.runtime.kmp)
            implementation(libs.synapse.core.datetime)
            implementation(libs.synapse.core.discopes)
            implementation(project(":core:network"))
        }
    }
}

dependencies {
    kspCommonMainMetadata(libs.kotlin.inject.compiler)
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
    add("commonMainApi", project(":domain:__DOMAIN__:entities"))
}

fun KotlinMultiplatformExtension.configureCommonMainKsp() {
    sourceSets.named("commonMain").configure {
        kotlin.srcDir("build/generated/ksp/metadata/commonMain/kotlin")
    }
    project.tasks.withType(KotlinCompilationTask::class.java).configureEach {
        if (name != "kspCommonMainKotlinMetadata") {
            dependsOn("kspCommonMainKotlinMetadata")
        }
    }
}
'''

DOMAIN_REPOSITORY_IMPL = '''package __BASE_PACKAGE__.domain.__DOMAIN__.data

import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository

internal class __DOMAIN_PASCAL__RepositoryImpl : __DOMAIN_PASCAL__Repository {
    // TODO: implement repository methods
}
'''

DOMAIN_REPOSITORY_PROVIDERS_IMPL = '''package __BASE_PACKAGE__.domain.__DOMAIN__.data.di

import __BASE_PACKAGE__.core.network.CoreClient
import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.__DOMAIN__.data.__DOMAIN_PASCAL__RepositoryImpl
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.di.__DOMAIN_PASCAL__RepositoryProviders
import com.ribads.synapse.core.discopes.SingletonScope
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
@SingletonScope
abstract class __DOMAIN_PASCAL__RepositoryProvidersImpl(
    private val client: CoreClient,
    private val logger: ErrorLogger,
) : __DOMAIN_PASCAL__RepositoryProviders {

    @Provides
    internal fun provide__DOMAIN_PASCAL__Repository(): __DOMAIN_PASCAL__Repository =
        __DOMAIN_PASCAL__RepositoryImpl()
}
'''

# ─── feature modules ──────────────────────────────────────────────────────────

FEATURE_USECASE_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.ksp)
}

kotlin {
    jvm()
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    )
    configureCommonMainKsp()
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(libs.coroutine.core)
                implementation(libs.kotlin.inject.runtime.kmp)
                implementation(libs.synapse.core.discopes)
__USECASE_DOMAIN_DEPS__
            }
        }
    }
}

dependencies {
    kspCommonMainMetadata(libs.kotlin.inject.compiler)
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}

fun KotlinMultiplatformExtension.configureCommonMainKsp() {
    sourceSets.named("commonMain").configure {
        kotlin.srcDir("build/generated/ksp/metadata/commonMain/kotlin")
    }
    project.tasks.withType(KotlinCompilationTask::class.java).configureEach {
        if (name != "kspCommonMainKotlinMetadata") {
            dependsOn("kspCommonMainKotlinMetadata")
        }
    }
}
'''

FEATURE_FETCH_USE_CASE = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase

interface Fetch__FEATURE_PASCAL__UseCase {
    suspend fun execute(): Result<Unit>
}

internal class Fetch__FEATURE_PASCAL__UseCaseImpl : Fetch__FEATURE_PASCAL__UseCase {
    override suspend fun execute(): Result<Unit> {
        // TODO: implement
        return Result.success(Unit)
    }
}
'''

FEATURE_USE_CASE_PROVIDER = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase.di

import __BASE_PACKAGE__.feature.__FEATURE__.usecase.Fetch__FEATURE_PASCAL__UseCase

interface __FEATURE_PASCAL__UseCaseProvider {
    val fetch__FEATURE_PASCAL__UseCase: Fetch__FEATURE_PASCAL__UseCase
}
'''

FEATURE_USE_CASE_MODULE = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase.di

import __BASE_PACKAGE__.feature.__FEATURE__.usecase.Fetch__FEATURE_PASCAL__UseCase
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.Fetch__FEATURE_PASCAL__UseCaseImpl
import com.ribads.synapse.core.discopes.SingletonScope
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@SingletonScope
@Component
abstract class __FEATURE_PASCAL__UseCaseModule : __FEATURE_PASCAL__UseCaseProvider {

    @Provides
    fun provideFetch__FEATURE_PASCAL__UseCase(): Fetch__FEATURE_PASCAL__UseCase =
        Fetch__FEATURE_PASCAL__UseCaseImpl()
}
'''

FEATURE_UI_BUILD_GRADLE = '''import org.jetbrains.kotlin.gradle.ExperimentalKotlinGradlePluginApi
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidMultiplatformLibrary)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.ksp)
}

kotlin {
    android {
        androidResources { enable = true }
        namespace = "__BASE_PACKAGE__.feature.__FEATURE__.ui"
        compileSdk = libs.versions.android.compileSdk.get().toInt()
        minSdk = libs.versions.android.minSdk.get().toInt()

        @OptIn(ExperimentalKotlinGradlePluginApi::class)
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_21)
        }
    }

    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "Feature__FEATURE_PASCAL__Ui"
            isStatic = true
        }
    }

    configureCommonMainKsp()
    sourceSets {
        val androidMain by getting {
            dependencies {
                implementation(compose.uiTooling)
                implementation(libs.androidx.activity.compose)
            }
        }
        commonMain.dependencies {
            implementation(compose.components.resources)
            implementation(libs.androidx.lifecycle.viewmodelCompose)
            implementation(libs.navigation.compose)

            implementation(libs.kotlin.inject.runtime.kmp)

            implementation(projects.composeUi)
            implementation(projects.features.__FEATURE__.usecase)

            implementation(libs.synapse.ui.mvi)
            implementation(libs.synapse.ui.element)
            implementation(libs.synapse.ui.component)
            implementation(libs.synapse.ui.compose.presentation)
            implementation(libs.synapse.core.datetime)
        }
    }
}

dependencies {
    kspCommonMainMetadata(libs.kotlin.inject.compiler)
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}

fun KotlinMultiplatformExtension.configureCommonMainKsp() {
    sourceSets.named("commonMain").configure {
        kotlin.srcDir("build/generated/ksp/metadata/commonMain/kotlin")
    }
    project.tasks.withType(KotlinCompilationTask::class.java).configureEach {
        if (name != "kspCommonMainKotlinMetadata") {
            dependsOn("kspCommonMainKotlinMetadata")
        }
    }
}
'''

# ── Feature UI: FeatureLauncher ──

FEATURE_LAUNCHER = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.launcher

import __BASE_PACKAGE__.feature.__FEATURE__.ui.navigation.__FEATURE_PASCAL__NavigationHost
import __BASE_PACKAGE__.feature.__FEATURE__.ui.navigation.ViewModelProviders
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavigatorHost
import me.tatarka.inject.annotations.Inject

internal class __FEATURE_PASCAL__FeatureLauncher @Inject constructor(
    private val viewModelProviders: ViewModelProviders,
) : FeatureLauncher {

    override val featureName: String = FEATURE_NAME

    override fun navigationGraph(): NavigatorHost.Child {
        return __FEATURE_PASCAL__NavigationHost(viewModelProviders = viewModelProviders)
    }

    companion object {
        internal const val FEATURE_NAME = "__FEATURE__"
    }
}
'''

# ── Feature UI: ViewModelProviders ──

FEATURE_VIEW_MODEL_PROVIDERS = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.navigation

import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenViewModel

internal interface ViewModelProviders {
    val landingScreenViewModel: () -> LandingScreenViewModel
}
'''

# ── Feature UI: NavigationHost ──

FEATURE_NAVIGATION_HOST = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.navigation

import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.navigation
import __BASE_PACKAGE__.feature.__FEATURE__.ui.launcher.__FEATURE_PASCAL__FeatureLauncher
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreen
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavigatorHost
import com.ribads.synapse.ui.compose.presentation.navigation.compose.composable

internal class __FEATURE_PASCAL__NavigationHost(
    private val viewModelProviders: ViewModelProviders,
) : NavigatorHost.Child {

    override fun buildGraph(
        builder: NavGraphBuilder,
        navigationDispatcher: NavigationDispatcher,
    ) {
        builder.navigation(route = ROOT_ROUTE, startDestination = "landing") {
            composable(route = "landing") {
                LandingScreen(
                    viewModel = viewModel { viewModelProviders.landingScreenViewModel.invoke() },
                    navigationDispatcher = navigationDispatcher,
                )
            }
        }
    }

    companion object {
        private const val ROOT_ROUTE = __FEATURE_PASCAL__FeatureLauncher.FEATURE_NAME
    }
}
'''

# ── Feature UI: DI Module ──

FEATURE_MODULE = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.di

import __BASE_PACKAGE__.feature.__FEATURE__.ui.launcher.__FEATURE_PASCAL__FeatureLauncher
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.di.LandingScreenUiComponent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.di.create
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.__FEATURE_PASCAL__UseCaseModule
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.IntoMap
import me.tatarka.inject.annotations.Provides

@Component
abstract class __FEATURE_PASCAL__Module(@Component val useCaseModule: __FEATURE_PASCAL__UseCaseModule) {
    abstract val features: Map<String, FeatureLauncher>

    @Provides
    @IntoMap
    protected fun provideFeatureLauncher(launcher: FeatureLauncher): Pair<String, FeatureLauncher> =
        __FEATURE_PASCAL__FeatureLauncher.FEATURE_NAME to launcher

    @Provides
    internal fun provideViewModelComponent(): __FEATURE_PASCAL__ViewModelComponent =
        __FEATURE_PASCAL__ViewModelComponent::class.create(
            landingScreenUiComponent = LandingScreenUiComponent::class.create(useCaseModule),
        )

    @Provides
    internal fun provideFeatureLauncher(
        viewModelProviders: __FEATURE_PASCAL__ViewModelComponent,
    ): FeatureLauncher = __FEATURE_PASCAL__FeatureLauncher(viewModelProviders = viewModelProviders)
}
'''

# ── Feature UI: ViewModelComponent ──

FEATURE_VIEW_MODEL_COMPONENT = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.di

import __BASE_PACKAGE__.feature.__FEATURE__.ui.navigation.ViewModelProviders
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenViewModel
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.di.LandingScreenUiComponent
import me.tatarka.inject.annotations.Component

@Component
internal abstract class __FEATURE_PASCAL__ViewModelComponent(
    private val landingScreenUiComponent: LandingScreenUiComponent,
) : ViewModelProviders {

    override val landingScreenViewModel: () -> LandingScreenViewModel
        get() = { landingScreenUiComponent.viewModel }
}
'''

# ── Feature UI: Landing Screen (IRSE-MVI 7 files) ──

LANDING_CONTRACT = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import androidx.compose.runtime.Immutable
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand

internal object LandingScreenContract {

    interface Mapper {
        fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded
        fun toResult(intent: Intent.Navigation): Result.NavigationRequested
    }

    sealed class Intent {
        data object LoadInitialData : Intent()
        sealed class Navigation : Intent() {
            data object Back : Navigation()
        }
    }

    sealed class Result {
        data object OnInitialDataLoaded : Result()
        data class NavigationRequested(val command: NavigationCommand) : Result()
    }

    sealed class Effect {
        data class Navigate(val command: NavigationCommand) : Effect()
    }

    @Immutable
    data class ViewState(
        val isLoading: Boolean = false,
    ) {
        companion object {
            val Default = ViewState()
        }
    }
}
'''

LANDING_INTERACTOR = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import com.ribads.synapse.ui.mvi.Interactor
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Mapper
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Result
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.ViewState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.merge
import me.tatarka.inject.annotations.Inject

internal class LandingScreenInteractor @Inject constructor(
    private val mapper: Mapper,
) : Interactor<Intent, Result, ViewState> {

    override fun process(
        intents: Flow<Intent>,
        state: StateFlow<ViewState>,
    ): Flow<Result> {
        return merge(
            intents.filterIsInstance<Intent.LoadInitialData>().map(mapper::toResult),
            intents.filterIsInstance<Intent.Navigation>().map(mapper::toResult),
        )
    }
}
'''

LANDING_REDUCER = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import com.ribads.synapse.ui.mvi.Reducer
import com.ribads.synapse.ui.mvi.Reduction
import com.ribads.synapse.ui.mvi.noEffects
import com.ribads.synapse.ui.mvi.withEffect
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Effect
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Result
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.ViewState
import me.tatarka.inject.annotations.Inject

internal class LandingScreenReducer @Inject constructor() : Reducer<ViewState, Result, Effect> {
    override fun reduce(state: ViewState, result: Result): Reduction<ViewState, Effect> {
        return when (result) {
            is Result.OnInitialDataLoaded -> state.noEffects()
            is Result.NavigationRequested -> state withEffect Effect.Navigate(result.command)
        }
    }
}
'''

LANDING_MAPPER = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Mapper
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Result
import me.tatarka.inject.annotations.Inject

internal class LandingScreenMapper @Inject constructor() : Mapper {

    override fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded {
        return Result.OnInitialDataLoaded
    }

    override fun toResult(intent: Intent.Navigation): Result.NavigationRequested {
        return when (intent) {
            Intent.Navigation.Back -> Result.NavigationRequested(
                command = NavigationCommand.BackCommand(),
            )
        }
    }
}
'''

LANDING_VIEW_MODEL = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import com.ribads.synapse.ui.mvi.FlowViewModelArgs
import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.LifecycleViewModel
import com.ribads.synapse.ui.mvi.Reducer
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Effect
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Result
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.ViewState
import me.tatarka.inject.annotations.Inject

internal class LandingScreenViewModel @Inject constructor(
    initialState: ViewState,
    interactor: Interactor<Intent, Result, ViewState>,
    reducer: Reducer<ViewState, Result, Effect>,
) : LifecycleViewModel<Intent, Result, ViewState, Effect>(
    args = FlowViewModelArgs(
        initialState = initialState,
        reducer = reducer,
        interactor = interactor,
    ),
)
'''

LANDING_SCREEN = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import com.ribads.synapse.ui.component.scaffold.Scaffold
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import com.ribads.synapse.ui.element.theme.Theme
import com.ribads.synapse.ui.mvi.CollectAsEffect
import com.ribads.synapse.ui.mvi.OnFirstComposition
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Effect
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent

@Composable
internal fun LandingScreen(
    viewModel: LandingScreenViewModel,
    navigationDispatcher: NavigationDispatcher,
) {
    val viewState by remember { derivedStateOf { viewModel.state.value } }

    viewModel.OnFirstComposition(Intent.LoadInitialData)

    viewModel.effects.CollectAsEffect { effect ->
        when (effect) {
            is Effect.Navigate -> navigationDispatcher.navigateTo(effect.command)
        }
    }

    Scaffold(
        backgroundColor = Theme.colors.surface.primaryLight,
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = Theme.spacing.x6),
        ) {
            // TODO: Build __FEATURE_PASCAL__ landing screen UI
        }
    }
}
'''

LANDING_UI_COMPONENT = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.di

import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.Reducer
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Effect
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Mapper
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Result
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.ViewState
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenInteractor
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenMapper
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenReducer
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenViewModel
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.__FEATURE_PASCAL__UseCaseModule
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
internal abstract class LandingScreenUiComponent(
    @Component val useCaseModule: __FEATURE_PASCAL__UseCaseModule,
) {
    abstract val viewModel: LandingScreenViewModel

    @Provides
    protected fun LandingScreenMapper.bind(): Mapper = this

    @Provides
    protected fun LandingScreenReducer.bind(): Reducer<ViewState, Result, Effect> = this

    @Provides
    fun LandingScreenInteractor.bind(): Interactor<Intent, Result, ViewState> = this

    @Provides
    protected fun provideDefaultViewState(): ViewState = ViewState.Default
}
'''

# ─── iOS App ───────────────────────────────────────────────────────────────────

IOS_APP_SWIFT = '''import SwiftUI
import ComposeApp

@main
struct iOSApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
'''

CONTENT_VIEW_SWIFT = '''import UIKit
import SwiftUI
import ComposeApp

struct ComposeView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        MainViewControllerKt.MainViewController()
    }

    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
}

struct ContentView: View {
    var body: some View {
        ComposeView()
            .ignoresSafeArea()
    }
}
'''

# ─── Main Generator ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Synapse KMP project with multi-module DDD architecture.",
    )
    parser.add_argument("--name", required=True, help="PascalCase project name, e.g. MyApp")
    parser.add_argument("--package", required=True, help="Base Kotlin package, e.g. com.example.myapp")
    parser.add_argument("--output", required=True, help="Absolute path to create project in")
    parser.add_argument("--domains", required=True, help="Comma-separated domain names (lowercase)")
    parser.add_argument("--features", required=True, help="Comma-separated feature names (lowercase)")
    parser.add_argument("--synapse-version", default="0.0.17-alpha1", help="Synapse library version")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    name: str = args.name
    base_pkg: str = args.package.strip().strip(".")
    out = Path(args.output).expanduser().resolve()
    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    features = [f.strip() for f in args.features.split(",") if f.strip()]
    synapse_version = args.synapse_version
    force = args.force

    if not name or not name[0].isupper():
        print("error: --name must be PascalCase, e.g. MyApp", file=sys.stderr)
        sys.exit(2)

    if not force and (out / "settings.gradle.kts").exists():
        print(f"error: {out}/settings.gradle.kts already exists (use --force to overwrite)", file=sys.stderr)
        sys.exit(1)

    app_pkg = f"{base_pkg}.app"
    app_pkg_path = pkg_to_path(app_pkg)
    base_pkg_path = pkg_to_path(base_pkg)

    ctx = {
        "PROJECT_NAME": name,
        "PROJECT_NAME_LOWER": name.lower(),
        "BASE_PACKAGE": base_pkg,
        "APP_PACKAGE": app_pkg,
        "SYNAPSE_VERSION": synapse_version,
        "FIRST_FEATURE": features[0] if features else "home",
    }

    print(f"Generating {name} project in {out}")
    print(f"  Package: {base_pkg}")
    print(f"  Domains: {', '.join(domains)}")
    print(f"  Features: {', '.join(features)}")
    print()

    # ── Root build files ──
    domain_includes = "\n".join(
        f'include(":domain:{d}:entities")\ninclude(":domain:{d}:data")'
        for d in domains
    )
    feature_includes = "\n".join(
        f'include(":features:{f}:ui")\ninclude(":features:{f}:usecase")'
        for f in features
    )
    ctx["DOMAIN_INCLUDES"] = domain_includes
    ctx["FEATURE_INCLUDES"] = feature_includes

    write_file(out / "settings.gradle.kts", render(SETTINGS_GRADLE, ctx), force)
    write_file(out / "build.gradle.kts", ROOT_BUILD_GRADLE, force)
    write_file(out / "gradle.properties", GRADLE_PROPERTIES, force)
    write_file(out / "gradle" / "libs.versions.toml", render(LIBS_VERSIONS_TOML, ctx), force)
    write_file(out / "gradle" / "wrapper" / "gradle-wrapper.properties", GRADLE_WRAPPER_PROPERTIES, force)

    # ── androidApp ──
    android_app = out / "androidApp"
    android_app_src = android_app / "src" / "main" / "java" / app_pkg_path
    write_file(android_app / "build.gradle.kts", render(ANDROID_APP_BUILD_GRADLE, ctx), force)
    write_file(android_app / "src" / "main" / "AndroidManifest.xml", render(ANDROID_MANIFEST, ctx), force)
    write_file(android_app / "src" / "main" / "res" / "values" / "strings.xml", render(ANDROID_STRINGS_XML, ctx), force)
    write_file(android_app / "src" / "main" / "res" / "values" / "themes.xml", render(ANDROID_THEMES_XML, ctx), force)
    write_file(android_app_src / "MainActivity.kt", render(MAIN_ACTIVITY, ctx), force)

    # ── composeApp ──
    domain_deps = "\n".join(
        f"            implementation(projects.domain.{d}.data)" for d in domains
    )
    feature_deps = "\n".join(
        f"            implementation(projects.features.{f}.ui)\n            implementation(projects.features.{f}.usecase)"
        for f in features
    )
    ctx["COMPOSE_APP_DOMAIN_DEPS"] = domain_deps
    ctx["COMPOSE_APP_FEATURE_DEPS"] = feature_deps

    compose_app = out / "composeApp"
    common_src = compose_app / "src" / "commonMain" / "kotlin" / app_pkg_path
    android_src = compose_app / "src" / "androidMain" / "kotlin" / app_pkg_path
    ios_src = compose_app / "src" / "iosMain" / "kotlin" / app_pkg_path

    write_file(compose_app / "build.gradle.kts", render(COMPOSE_APP_BUILD_GRADLE, ctx), force)

    write_file(common_src / "AppContext.kt", render(APP_CONTEXT_EXPECT, ctx), force)
    write_file(android_src / "AppContext.android.kt", render(APP_CONTEXT_ANDROID, ctx), force)
    write_file(ios_src / "AppContext.ios.kt", render(APP_CONTEXT_IOS, ctx), force)

    write_file(ios_src / "MainViewController.kt", render(MAIN_VIEW_CONTROLLER, ctx), force)

    write_file(common_src / "CoreComposeApp.kt", render(CORE_COMPOSE_APP, ctx), force)
    write_file(common_src / "RootScreen.kt", render(ROOT_SCREEN, ctx), force)

    # MVI (in ui package)
    write_file(common_src / "ui" / "MainContract.kt", render(MAIN_CONTRACT, ctx), force)
    write_file(common_src / "ui" / "MainInteractor.kt", render(MAIN_INTERACTOR, ctx), force)
    write_file(common_src / "ui" / "MainReducer.kt", render(MAIN_REDUCER, ctx), force)
    write_file(common_src / "ui" / "MainMapper.kt", render(MAIN_MAPPER, ctx), force)
    write_file(common_src / "ui" / "MainViewModel.kt", render(MAIN_VIEW_MODEL, ctx), force)
    write_file(common_src / "ui" / "di" / "MainUiComponent.kt", render(MAIN_UI_COMPONENT, ctx), force)

    # Navigation (in ui/navigation)
    write_file(common_src / "ui" / "navigation" / "MainNavigatorHost.kt", render(MAIN_NAVIGATOR_HOST, ctx), force)
    write_file(common_src / "ui" / "navigation" / "MainNavigationDispatcher.kt", render(MAIN_NAVIGATION_DISPATCHER, ctx), force)

    # DI
    write_file(common_src / "di" / "NetworkComponent.kt", render(NETWORK_COMPONENT, ctx), force)
    write_file(common_src / "di" / "AppConfigurationProvider.kt", render(BUILD_APP_CONFIGURATION_PROVIDER, ctx), force)

    # DI: RootAppBuilder
    rab_imports = ROOT_APP_BUILDER_HEAD
    for d in domains:
        rab_imports += render(ROOT_APP_BUILDER_DOMAIN_IMPORT, {**ctx, "DOMAIN": d, "DOMAIN_PASCAL": to_pascal(d)})
    for f in features:
        rab_imports += render(ROOT_APP_BUILDER_FEATURE_IMPORT, {**ctx, "FEATURE": f, "FEATURE_PASCAL": to_pascal(f)})

    domain_builds = ""
    for d in domains:
        dp = to_pascal(d)
        dc = to_camel(d)
        domain_builds += f"        val {dc}Repositories = {dp}RepositoryProvidersImpl::class.create(\n"
        domain_builds += f"            client = networkComponent.client,\n"
        domain_builds += f"            logger = errorLogger,\n"
        domain_builds += f"        )\n\n"

    feature_builds = ""
    for f in features:
        fp = to_pascal(f)
        fc = to_camel(f)
        feature_builds += f"        val {fc}Module = {fp}Module::class.create(\n"
        feature_builds += f"            useCaseModule = {fp}UseCaseModule::class.create(),\n"
        feature_builds += f"        )\n\n"

    feature_params = ",\n".join(
        f"            {to_camel(f)}Module = {to_camel(f)}Module" for f in features
    )

    ctx["DOMAIN_BUILDS"] = domain_builds
    ctx["FEATURE_BUILDS"] = feature_builds
    ctx["FEATURE_PARAMS"] = feature_params

    write_file(common_src / "di" / "RootAppBuilder.kt", render(rab_imports + ROOT_APP_BUILDER_CLASS, ctx), force)

    # DI: ComposeAppComponent
    cac = COMPOSE_APP_COMPONENT_HEAD
    for f in features:
        cac += render(COMPOSE_APP_COMPONENT_FEATURE_IMPORT, {**ctx, "FEATURE": f, "FEATURE_PASCAL": to_pascal(f)})

    constructor_params = "\n".join(
        f"    private val {to_camel(f)}Module: {to_pascal(f)}Module," for f in features
    )
    map_entries = " +\n".join(
        f"        {to_camel(f)}Module.features" for f in features
    )

    ctx["FEATURE_CONSTRUCTOR_PARAMS"] = constructor_params
    ctx["FEATURE_MAP_ENTRIES"] = map_entries

    write_file(common_src / "di" / "ComposeAppComponent.kt", render(cac + COMPOSE_APP_COMPONENT_CLASS, ctx), force)

    # ── compose-ui ──
    compose_ui = out / "compose-ui"
    theme_path = compose_ui / "src" / "commonMain" / "kotlin" / base_pkg_path / "compose" / "ui" / "theme"
    write_file(compose_ui / "build.gradle.kts", render(COMPOSE_UI_BUILD_GRADLE, ctx), force)
    write_file(theme_path / f"{name}Theme.kt", render(APP_THEME, ctx), force)

    # ── core modules ──

    # core:network
    core_net = out / "core" / "network"
    core_net_pkg = f"{base_pkg}.core.network"
    core_net_common = core_net / "src" / "commonMain" / "kotlin" / pkg_to_path(core_net_pkg)
    core_net_jvm = core_net / "src" / "jvmMain" / "kotlin" / pkg_to_path(core_net_pkg)
    core_net_ios = core_net / "src" / "iosMain" / "kotlin" / pkg_to_path(core_net_pkg)

    write_file(core_net / "build.gradle.kts", CORE_NETWORK_BUILD_GRADLE, force)
    write_file(core_net_common / "CoreClient.kt", render(CORE_CLIENT, ctx), force)
    write_file(core_net_common / "CoreClientImpl.kt", render(CORE_CLIENT_IMPL, ctx), force)
    write_file(core_net_common / "HttpClient.kt", render(HTTP_CLIENT_EXPECT, ctx), force)
    write_file(core_net_common / "CoreRequestError.kt", render(CORE_REQUEST_ERROR, ctx), force)
    write_file(core_net_jvm / "HttpClient.jvm.kt", render(HTTP_CLIENT_JVM, ctx), force)
    write_file(core_net_ios / "HttpClient.ios.kt", render(HTTP_CLIENT_IOS, ctx), force)

    # core:auth
    core_auth = out / "core" / "auth"
    core_auth_pkg = f"{base_pkg}.core.auth"
    core_auth_common = core_auth / "src" / "commonMain" / "kotlin" / pkg_to_path(core_auth_pkg)

    write_file(core_auth / "build.gradle.kts", CORE_AUTH_BUILD_GRADLE, force)
    write_file(core_auth_common / "OauthToken.kt", render(OAUTH_TOKEN, ctx), force)
    write_file(core_auth_common / "OauthTokenProvider.kt", render(OAUTH_TOKEN_PROVIDER, ctx), force)

    # core:config
    core_config = out / "core" / "config"
    core_config_pkg = f"{base_pkg}.core.config"
    core_config_common = core_config / "src" / "commonMain" / "kotlin" / pkg_to_path(core_config_pkg)

    write_file(core_config / "build.gradle.kts", CORE_CONFIG_BUILD_GRADLE, force)
    write_file(core_config_common / "AppConfigurationProvider.kt", render(APP_CONFIGURATION_PROVIDER, ctx), force)
    write_file(core_config_common / "ConfigurationProperties.kt", render(CONFIGURATION_PROPERTIES, ctx), force)

    # core:log
    core_log = out / "core" / "log"
    core_log_pkg = f"{base_pkg}.core.log"
    core_log_common = core_log / "src" / "commonMain" / "kotlin" / pkg_to_path(core_log_pkg)

    write_file(core_log / "build.gradle.kts", CORE_LOG_BUILD_GRADLE, force)
    write_file(core_log_common / "ErrorLogger.kt", render(ERROR_LOGGER, ctx), force)

    # ── domain modules ──
    for d in domains:
        dp = to_pascal(d)
        dc = to_camel(d)
        dctx = {**ctx, "DOMAIN": d, "DOMAIN_PASCAL": dp, "DOMAIN_CAMEL": dc}

        # entities
        ent = out / "domain" / d / "entities"
        ent_src = ent / "src" / "commonMain" / "kotlin" / base_pkg_path / "domain" / d / "entities"
        write_file(ent / "build.gradle.kts", DOMAIN_ENTITIES_BUILD_GRADLE, force)
        write_file(ent_src / f"{dp}Repository.kt", render(DOMAIN_REPOSITORY, dctx), force)
        write_file(ent_src / "di" / f"{dp}RepositoryProviders.kt", render(DOMAIN_REPOSITORY_PROVIDERS, dctx), force)

        # data
        dat = out / "domain" / d / "data"
        dat_src = dat / "src" / "commonMain" / "kotlin" / base_pkg_path / "domain" / d / "data"
        write_file(dat / "build.gradle.kts", render(DOMAIN_DATA_BUILD_GRADLE, dctx), force)
        write_file(dat_src / f"{dp}RepositoryImpl.kt", render(DOMAIN_REPOSITORY_IMPL, dctx), force)
        write_file(dat_src / "di" / f"{dp}RepositoryProvidersImpl.kt", render(DOMAIN_REPOSITORY_PROVIDERS_IMPL, dctx), force)

    # ── feature modules ──
    for f in features:
        fp = to_pascal(f)
        fc = to_camel(f)
        fctx = {**ctx, "FEATURE": f, "FEATURE_PASCAL": fp, "FEATURE_CAMEL": fc}

        # usecase
        uc = out / "features" / f / "usecase"
        uc_src = uc / "src" / "commonMain" / "kotlin" / base_pkg_path / "feature" / f / "usecase"

        fctx["USECASE_DOMAIN_DEPS"] = "            // TODO: add domain entity dependencies"

        write_file(uc / "build.gradle.kts", render(FEATURE_USECASE_BUILD_GRADLE, fctx), force)
        write_file(uc_src / f"Fetch{fp}UseCase.kt", render(FEATURE_FETCH_USE_CASE, fctx), force)
        write_file(uc_src / "di" / f"{fp}UseCaseProvider.kt", render(FEATURE_USE_CASE_PROVIDER, fctx), force)
        write_file(uc_src / "di" / f"{fp}UseCaseModule.kt", render(FEATURE_USE_CASE_MODULE, fctx), force)

        # ui
        ui = out / "features" / f / "ui"
        ui_src = ui / "src" / "commonMain" / "kotlin" / base_pkg_path / "feature" / f / "ui"

        write_file(ui / "build.gradle.kts", render(FEATURE_UI_BUILD_GRADLE, fctx), force)
        write_file(ui_src / "launcher" / f"{fp}FeatureLauncher.kt", render(FEATURE_LAUNCHER, fctx), force)
        write_file(ui_src / "navigation" / "ViewModelProviders.kt", render(FEATURE_VIEW_MODEL_PROVIDERS, fctx), force)
        write_file(ui_src / "navigation" / f"{fp}NavigationHost.kt", render(FEATURE_NAVIGATION_HOST, fctx), force)
        write_file(ui_src / "di" / f"{fp}Module.kt", render(FEATURE_MODULE, fctx), force)
        write_file(ui_src / "di" / f"{fp}ViewModelComponent.kt", render(FEATURE_VIEW_MODEL_COMPONENT, fctx), force)

        # landing screen (7 IRSE-MVI files)
        landing = ui_src / "screens" / "landing"
        write_file(landing / "LandingScreenContract.kt", render(LANDING_CONTRACT, fctx), force)
        write_file(landing / "LandingScreenInteractor.kt", render(LANDING_INTERACTOR, fctx), force)
        write_file(landing / "LandingScreenReducer.kt", render(LANDING_REDUCER, fctx), force)
        write_file(landing / "LandingScreenMapper.kt", render(LANDING_MAPPER, fctx), force)
        write_file(landing / "LandingScreenViewModel.kt", render(LANDING_VIEW_MODEL, fctx), force)
        write_file(landing / "LandingScreen.kt", render(LANDING_SCREEN, fctx), force)
        write_file(landing / "di" / "LandingScreenUiComponent.kt", render(LANDING_UI_COMPONENT, fctx), force)

    # ── iosApp ──
    ios_app = out / "iosApp" / "iosApp"
    write_file(ios_app / "iOSApp.swift", IOS_APP_SWIFT, force)
    write_file(ios_app / "ContentView.swift", CONTENT_VIEW_SWIFT, force)

    # ── Done ──
    print()
    total_domains = len(domains)
    total_features = len(features)
    total_modules = 4 + (total_domains * 2) + (total_features * 2) + 3  # core(4) + domains + features + androidApp + composeApp + compose-ui
    print(f"Done. Generated {total_modules} modules.")
    print()
    print("Next steps:")
    print(f"  1. cd {out}")
    print(f"  2. Configure GitHub Packages credentials for Synapse artifacts")
    print(f"  3. Customize the theme in compose-ui/.../theme/{name}Theme.kt")
    print(f"  4. Add custom fonts to compose-ui/src/commonMain/composeResources/font/")
    print(f"  5. Wire real repositories in domain/*/data/ implementations")
    print(f"  6. Open in Android Studio / Fleet and sync Gradle")


if __name__ == "__main__":
    main()
