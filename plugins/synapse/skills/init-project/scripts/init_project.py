#!/usr/bin/env python3
"""Generate a full Synapse KMP project with multi-module DDD architecture.

Creates the complete project scaffold:
  - Root build files (settings.gradle.kts, build.gradle.kts, gradle.properties, libs.versions.toml)
  - androidApp/ with MainActivity and Android application setup
  - composeApp/ with DI wiring, MVI main screen, navigation, platform code (KMP library)
  - compose-ui/ with theme layer
  - core/log module
  - domain/<name>/entities/ + domain/<name>/data/ per domain, plus domain/session/ with --with-session
  - features/<name>/usecase/ + features/<name>/ui/ per feature (with landing screen)
  - iosApp/ Swift files
"""

import argparse
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


SYNAPSE_METADATA_URL = (
    "https://repo1.maven.org/maven2/com/ribads/synapse/core-network/maven-metadata.xml"
)

CORE_NETWORK_UNRELEASED = "no release on Maven Central publishes core-network yet"


# ─── Helpers ───────────────────────────────────────────────────────────────────

class SynapseVersionLookupError(Exception):
    pass


def _fetch_metadata_xml() -> str:
    """Return the raw maven-metadata.xml body.

    Tries urllib first; on SSL trust issues (common with python.org builds on
    macOS that never ran ``Install Certificates.command``), falls back to
    ``curl``, which uses the system trust store.
    """
    request = urllib.request.Request(
        SYNAPSE_METADATA_URL,
        headers={"User-Agent": "synapse-init-project/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as http_error:
        if http_error.code == 404:
            raise SynapseVersionLookupError(CORE_NETWORK_UNRELEASED) from http_error
        raise SynapseVersionLookupError(str(http_error)) from http_error
    except OSError as urllib_error:
        if not shutil.which("curl"):
            raise SynapseVersionLookupError(f"{urllib_error}; curl is unavailable") from urllib_error
        try:
            result = subprocess.run(
                ["curl", "-fsSL", "--max-time", "10", SYNAPSE_METADATA_URL],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as curl_error:
            if "404" in curl_error.stderr:
                raise SynapseVersionLookupError(CORE_NETWORK_UNRELEASED) from curl_error
            raise SynapseVersionLookupError(
                f"{urllib_error}; curl failed: {curl_error.stderr.strip() or curl_error}"
            ) from curl_error
        return result.stdout


def fetch_latest_synapse_version() -> str:
    """Return the latest released Synapse version on Maven Central.

    Queries ``core-network``: generated projects depend on it, so only releases that publish it are usable.
    Raises ``SynapseVersionLookupError`` when the version cannot be resolved.
    """
    body = _fetch_metadata_xml()
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise SynapseVersionLookupError(f"unparseable maven-metadata.xml ({e})") from e
    version = root.findtext("versioning/release") or root.findtext("versioning/latest")
    if not version or not version.strip():
        raise SynapseVersionLookupError("maven-metadata.xml has no <release> or <latest>")
    return version.strip()


def resolve_synapse_version(requested: Optional[str]) -> str:
    if requested:
        return requested
    print("Resolving latest Synapse version from Maven Central...", flush=True)
    try:
        return fetch_latest_synapse_version()
    except SynapseVersionLookupError as e:
        print(
            f"error: could not resolve the latest Synapse release ({e}).\n"
            "       Re-run with --synapse-version <version>; published versions are listed at\n"
            f"       {SYNAPSE_METADATA_URL}",
            file=sys.stderr,
        )
        sys.exit(1)


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


TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_template(rel_path: str) -> str:
    """Read a template file from scripts/templates/<rel_path>."""
    return (TEMPLATES_DIR / rel_path).read_text()


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        print(f"  SKIP {path} (exists)", file=sys.stderr)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"))
    print(f"  wrote {path}")


def copy_template_file(src_rel: str, dest: Path, force: bool, executable: bool = False) -> None:
    """Copy a template file byte-for-byte (preserves binary content and line endings)."""
    if dest.exists() and not force:
        print(f"  SKIP {dest} (exists)", file=sys.stderr)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATES_DIR / src_rel, dest)
    if executable:
        dest.chmod(0o755)
    print(f"  wrote {dest}")


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
    }
}

include(":androidApp")
include(":composeApp")
include(":compose-ui")

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
android.dependency.useConstraints=true
'''

GITIGNORE = '''# Gradle
.gradle/
build/

# Kotlin
.kotlin/

# IntelliJ IDEA / Android Studio / Fleet
.idea/
.fleet/
*.iml
*.ipr
*.iws
out/

# Android & local machine config
local.properties
*.apk
*.aab
*.ap_
*.dex
captures/
.cxx/

# Xcode / iOS
**/xcuserdata/
**/*.xcuserstate
DerivedData/
*.ipa
.swiftpm/

# macOS
.DS_Store

# Logs
*.log
'''

GRADLE_WRAPPER_PROPERTIES = '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-9.6.0-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
'''

LIBS_VERSIONS_TOML = '''[versions]
agp = "9.4.1"
android-compileSdk = "37"
android-minSdk = "24"
android-targetSdk = "37"
androidx-activity = "1.13.0"
androidx-appcompat = "1.8.0"
androidx-core = "1.19.1"
androidx-lifecycle = "2.11.0"
composeMultiplatform = "1.12.2"
kotlin = "2.4.21"
synapse = "__SYNAPSE_VERSION__"
kotlinInject = "0.9.0"
ksp = "2.3.6"
ktor = "3.6.0"
coilCompose = "3.6.3"
coroutines = "1.11.0"
kermitLogger = "2.1.0"
kotlinxSerialization = "1.11.0"

[libraries]
kotlin-test = { module = "org.jetbrains.kotlin:kotlin-test", version.ref = "kotlin" }
androidx-core-ktx = { module = "androidx.core:core-ktx", version.ref = "androidx-core" }
androidx-appcompat = { module = "androidx.appcompat:appcompat", version.ref = "androidx-appcompat" }
androidx-activity-compose = { module = "androidx.activity:activity-compose", version.ref = "androidx-activity" }
androidx-lifecycle-viewmodelCompose = { module = "org.jetbrains.androidx.lifecycle:lifecycle-viewmodel-compose", version.ref = "androidx-lifecycle" }
androidx-lifecycle-runtimeCompose = { module = "org.jetbrains.androidx.lifecycle:lifecycle-runtime-compose", version.ref = "androidx-lifecycle" }

coil-svg = { module = "io.coil-kt.coil3:coil-svg", version.ref = "coilCompose" }
coil-compose = { module = "io.coil-kt.coil3:coil-compose", version.ref = "coilCompose" }

kermit-logger = { module = "co.touchlab:kermit", version.ref = "kermitLogger" }

coroutine-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
kotlinx-coroutines-test = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-test", version.ref = "coroutines" }

kotlinx-serialization-json = { module = "org.jetbrains.kotlinx:kotlinx-serialization-json", version.ref = "kotlinxSerialization" }

ktor-client-mock = { module = "io.ktor:ktor-client-mock", version.ref = "ktor" }

synapse-ui-element = { module = "com.ribads.synapse:ui-element", version.ref = "synapse" }
synapse-ui-component = { module = "com.ribads.synapse:ui-component", version.ref = "synapse" }
synapse-ui-compose-presentation = { module = "com.ribads.synapse:ui-compose-presentation", version.ref = "synapse" }
synapse-ui-mvi = { module = "com.ribads.synapse:ui-mvi", version.ref = "synapse" }
synapse-core-discopes = { module = "com.ribads.synapse:core-discopes", version.ref = "synapse" }
synapse-core-datetime = { module = "com.ribads.synapse:core-datetime", version.ref = "synapse" }
synapse-core-network = { module = "com.ribads.synapse:core-network", version.ref = "synapse" }
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
'''

CONFIGURE_COMMON_MAIN_KSP = '''
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
        getByName("debug") {
            buildConfigField("String", "API_BASE_URL", "\\"https://api.dev.example.com/\\"")
        }
        getByName("release") {
            isMinifyEnabled = false
            buildConfigField("String", "API_BASE_URL", "\\"https://api.example.com/\\"")
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
    <style name="Theme.__PROJECT_NAME__" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="android:windowBackground">@color/window_background</item>
        <item name="android:statusBarColor">@android:color/transparent</item>
        <item name="android:navigationBarColor">@android:color/transparent</item>
    </style>
</resources>
'''

# Matches surface.primary in APP_THEME's light and dark schemes, so the window behind the first frame agrees.
ANDROID_COLORS_XML = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="window_background">#FAFAFA</color>
</resources>
'''

ANDROID_COLORS_NIGHT_XML = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="window_background">#121212</color>
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

        val environment = AppEnvironment(
            apiBaseUrl = BuildConfig.API_BASE_URL,
            verboseNetworkLogging = BuildConfig.DEBUG,
        )

        setContent {
            CoreComposeApp(environment = environment)
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
    alias(libs.plugins.kotlinxSerialization)
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
            implementation(libs.coil.compose)
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

            implementation(libs.coil.svg)
            implementation(libs.kermit.logger)
            implementation(libs.kotlin.inject.runtime.kmp)

            implementation(libs.synapse.ui.compose.presentation)
            implementation(libs.synapse.ui.mvi)
            implementation(libs.synapse.ui.element)
            implementation(libs.synapse.ui.component)
            implementation(libs.synapse.core.discopes)
            implementation(libs.synapse.core.datetime)
            implementation(libs.synapse.core.network)__COMPOSE_APP_SESSION_DEPS__

            implementation(projects.core.log)

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
''' + CONFIGURE_COMMON_MAIN_KSP

# ── composeApp: CoreComposeApp ──

CORE_COMPOSE_APP = '''package __APP_PACKAGE__

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import coil3.ImageLoader
import coil3.PlatformContext
import coil3.compose.setSingletonImageLoaderFactory
import coil3.memory.MemoryCache
import coil3.request.CachePolicy
import coil3.request.crossfade
import __APP_PACKAGE__.di.RootAppBuilder
import __BASE_PACKAGE__.compose.ui.theme.__PROJECT_NAME__Theme
import com.ribads.synapse.ui.component.toast.ToastHandler
import com.ribads.synapse.ui.element.image.ImagePainterFactory
import com.ribads.synapse.ui.element.image.WithImagePainter
import com.ribads.synapse.ui.element.image.installSynapseImageComponents

private const val MEMORY_CACHE_MAX_SIZE_PERCENT = 0.3

@Composable
fun CoreComposeApp(environment: AppEnvironment) {
    val app = RootAppBuilder.obtain(environment)

    setSingletonImageLoaderFactory(::buildImageLoader)

    val imagePainterFactory = ImagePainterFactory.createPainterFactory()

    WithImagePainter(imagePainterFactory = imagePainterFactory) {
        __PROJECT_NAME__Theme {
            ToastHandler {
                RootScreen(
                    viewModel = viewModel { app.mainViewModel() },
                    features = app.features,
                )
            }
        }
    }
}

private fun buildImageLoader(context: PlatformContext): ImageLoader =
    ImageLoader.Builder(context)
        .installSynapseImageComponents()
        .memoryCachePolicy(CachePolicy.ENABLED)
        .memoryCache {
            MemoryCache.Builder()
                .maxSizePercent(context, MEMORY_CACHE_MAX_SIZE_PERCENT)
                .strongReferencesEnabled(true)
                .build()
        }
        .crossfade(true)
        .build()
'''

# ── composeApp: RootScreen ──

ROOT_SCREEN = '''package __APP_PACKAGE__

import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import __APP_PACKAGE__.ui.MainContract
import __APP_PACKAGE__.ui.MainViewModel
import com.ribads.synapse.ui.component.scaffold.Scaffold
import com.ribads.synapse.ui.component.tray.ThemedBottomSheetAppearance
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import com.ribads.synapse.ui.compose.presentation.navigation.compose.NavContainer
import com.ribads.synapse.ui.mvi.CollectAsEffect
import com.ribads.synapse.ui.mvi.OnFirstComposition

@Composable
internal fun RootScreen(
    viewModel: MainViewModel,
    features: Collection<FeatureLauncher>,
) {
    val viewState by remember { derivedStateOf { viewModel.state.value } }

    viewModel.OnFirstComposition(MainContract.Intent.Initial)

    Scaffold { paddingValues ->
        val startKey = viewState.startFeatureName?.let { name ->
            features.firstOrNull { it.featureName == name }?.startKey
        }
        startKey?.let { key ->
            val navDispatcher = NavContainer(
                startKey = key,
                features = features,
                modifier = Modifier
                    .fillMaxHeight()
                    .fillMaxWidth()
                    .padding(paddingValues = paddingValues),
                onDestinationChanged = { changed, _ ->
                    viewModel.emit(intent = MainContract.Intent.RouteChanged(key = changed))
                },
                bottomSheetAppearance = ThemedBottomSheetAppearance,
            )

            viewModel.effects.CollectAsEffect { effect ->
                when (effect) {
                    is MainContract.Effect.Navigate -> navDispatcher.navigateTo(effect.command)
                }
            }
        }
    }
}
'''

# ── composeApp: MainViewController (iOS) ──

MAIN_VIEW_CONTROLLER = '''package __APP_PACKAGE__

import androidx.compose.ui.window.ComposeUIViewController
import platform.Foundation.NSBundle
import platform.UIKit.UIViewController

private const val API_BASE_URL_KEY = "ApiBaseUrl"
private const val VERBOSE_NETWORK_LOGGING_KEY = "VerboseNetworkLogging"
private const val XCCONFIG_YES = "YES"

fun MainViewController(): UIViewController {
    val environment = AppEnvironment(
        apiBaseUrl = infoPlistString(API_BASE_URL_KEY),
        verboseNetworkLogging = infoPlistString(VERBOSE_NETWORK_LOGGING_KEY) == XCCONFIG_YES,
    )

    return ComposeUIViewController {
        CoreComposeApp(environment = environment)
    }
}

private fun infoPlistString(key: String): String =
    (NSBundle.mainBundle.objectForInfoDictionaryKey(key) as? String)
        ?.takeIf { it.isNotBlank() }
        ?: error("Info.plist has no value for $key; set it in iosApp/Configuration/Config.xcconfig")
'''

# ── composeApp MVI (ui package) ──

MAIN_CONTRACT = '''package __APP_PACKAGE__.ui

import androidx.compose.runtime.Immutable
import com.ribads.synapse.ui.compose.presentation.navigation.NavKey
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand

internal interface MainContract {

    interface Mapper {
        fun toResult(intent: Intent.Initial): Result
        fun toResult(intent: Intent.RouteChanged): Result.RouteChanged
    }

    sealed class Intent {
        data object Initial : Intent()
        data class RouteChanged(val key: NavKey) : Intent()
    }

    sealed class Result {

        data class Initial(
            val startFeatureName: String,
        ) : Result()

        data class RouteChanged(
            val key: NavKey,
        ) : Result()
    }

    sealed class Effect {
        data class Navigate(val command: NavigationCommand) : Effect()
    }

    @Immutable
    data class ViewState(
        val startFeatureName: String? = null,
        val currentKey: NavKey? = null,
    ) {
        companion object {
            val Default = ViewState()
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
            is Result.Initial -> state.copy(startFeatureName = result.startFeatureName).noEffects()
            is Result.RouteChanged -> state.copy(currentKey = result.key).noEffects()
        }
    }
}
'''

MAIN_MAPPER = '''package __APP_PACKAGE__.ui

import __APP_PACKAGE__.ui.MainContract.Intent
import __APP_PACKAGE__.ui.MainContract.Mapper
import __APP_PACKAGE__.ui.MainContract.Result
import me.tatarka.inject.annotations.Inject

internal class MainMapper @Inject constructor() : Mapper {

    override fun toResult(intent: Intent.Initial): Result {
        return Result.Initial(startFeatureName = "__FIRST_FEATURE__")
    }

    override fun toResult(intent: Intent.RouteChanged) = Result.RouteChanged(key = intent.key)
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

# ── RootAppBuilder (assembled dynamically) ──

ROOT_APP_BUILDER_PACKAGE = '''package __APP_PACKAGE__.di

'''

ROOT_APP_BUILDER_IMPORT = '''import __APP_PACKAGE__.AppEnvironment
import __APP_PACKAGE__.ui.MainViewModel
import __APP_PACKAGE__.ui.di.MainUiComponent
import __APP_PACKAGE__.ui.di.create
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
'''

ROOT_APP_BUILDER_SESSION_IMPORT = '''import __BASE_PACKAGE__.domain.session.data.di.SessionRepositoryProvidersImpl
import __BASE_PACKAGE__.domain.session.data.di.create
'''

ROOT_APP_BUILDER_DOMAIN_IMPORT = '''import __BASE_PACKAGE__.domain.__DOMAIN__.data.di.__DOMAIN_PASCAL__RepositoryProvidersImpl
import __BASE_PACKAGE__.domain.__DOMAIN__.data.di.create
'''

ROOT_APP_BUILDER_FEATURE_IMPORT = '''import __BASE_PACKAGE__.feature.__FEATURE__.ui.di.__FEATURE_PASCAL__Module
import __BASE_PACKAGE__.feature.__FEATURE__.ui.di.create
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.__FEATURE_PASCAL__UseCaseModule
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.create
'''

ROOT_APP_BUILDER_NETWORK_IMPORT = '''import com.ribads.synapse.core.network.buildHttpClient
'''

ROOT_APP_BUILDER_SESSION_NETWORK_IMPORT = '''import com.ribads.synapse.core.network.HttpLogging
import com.ribads.synapse.core.network.buildHttpClient
import com.ribads.synapse.core.sharedpref.buildEncryptedSharedPrefManager
'''

ROOT_APP_BUILDER_CLASS = '''
internal class __PROJECT_NAME__App(
    val features: Collection<FeatureLauncher>,
    val mainViewModel: () -> MainViewModel,
)

internal object RootAppBuilder {

    private var app: __PROJECT_NAME__App? = null

    fun obtain(environment: AppEnvironment): __PROJECT_NAME__App = app ?: build(environment).also { app = it }

    private fun build(environment: AppEnvironment): __PROJECT_NAME__App {
        val errorLogger = buildErrorLogger()
        val networkConfig = environment.toNetworkConfig()
__NETWORK_BUILD__
__DOMAIN_BUILD__
__FEATURE_BUILDS__
        val mainUiComponent = MainUiComponent::class.create()

        val appComponent = ComposeAppComponent::class.create(
__FEATURE_PARAMS__
        )

        return __PROJECT_NAME__App(
            features = appComponent.features.values,
            mainViewModel = { mainUiComponent.viewModel },
        )
    }
}
'''

ROOT_APP_BUILDER_NETWORK = '''        val httpClient = buildHttpClient(networkConfig)
'''

ROOT_APP_BUILDER_SESSION_NETWORK = '''        val sessionRepositories = SessionRepositoryProvidersImpl::class.create(
            tokenEndpointClient = buildHttpClient(networkConfig.copy(logging = HttpLogging.None)),
            storage = buildEncryptedSharedPrefManager("__PROJECT_NAME_LOWER___session"),
            logger = errorLogger,
        )
        val httpClient = buildHttpClient(networkConfig, sessionRepositories.authTokenSource)
'''

ROOT_APP_BUILDER_DOMAIN = '''        val __DOMAIN_CAMEL__Repositories = __DOMAIN_PASCAL__RepositoryProvidersImpl::class.create(
            client = httpClient,
            logger = errorLogger,
        )
'''

# ── ComposeAppComponent (assembled dynamically) ──

COMPOSE_APP_COMPONENT_HEAD = '''package __APP_PACKAGE__.di
'''

COMPOSE_APP_COMPONENT_FEATURE_IMPORT = '''import __BASE_PACKAGE__.feature.__FEATURE__.ui.di.__FEATURE_PASCAL__Module
'''

COMPOSE_APP_COMPONENT_CLASS = '''import com.ribads.synapse.core.discopes.SingletonScope
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@SingletonScope
@Component
internal abstract class ComposeAppComponent(
__FEATURE_CONSTRUCTOR_PARAMS__
) {
    abstract val features: Map<String, FeatureLauncher>

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
import com.ribads.synapse.ui.element.theme.Appearance
import com.ribads.synapse.ui.element.theme.Border
import com.ribads.synapse.ui.element.theme.ColorSchemes
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
import com.ribads.synapse.ui.element.theme.WithAppTheme

@Composable
fun __PROJECT_NAME__Theme(
    appearance: Appearance = Appearance.System,
    content: @Composable () -> Unit,
) {
    WithAppTheme(
        appearance = appearance,
        colorSchemes = AppColorSchemes,
        typography = AppTypography,
        shape = AppShape,
        content = content,
    )
}

private val LightColors = Colors(
    surface = Surface(
        primary = Color(0xFFFAFAFA),
        secondary = Color(0xFFF5F5F5),
        subtle = Color(0xFFE0E0E0),
        raised = Color(0xFFFFFFFF),
        skeleton = Color(0xFFE0E0E0),
    ),
    surfaceInteractive = SurfaceInteractive(
        enabled = Color(0xFF6366F1),
        hoverTap = Color(0xFF818CF8),
        disabled = Color(0xFF6366F1).copy(alpha = 0.2f),
    ),
    border = Border(
        primary = Color(0xFFE0E0E0),
        secondary = Color(0xFF9CA3AF),
        emphasis = Color(0xFF6366F1),
    ),
    element = Element(
        primary = Color(0xFF111827),
        secondary = Color(0xFF6B7280),
    ),
    elementInteractive = ElementInteractive(
        enabled = Color(0xFFFFFFFF),
        hoverTap = Color(0xFF6366F1),
        disabled = Color(0xFF6B7280),
    ),
    shadow = Shadow(spot = Color(0x1A000000)),
    intents = Intents(
        accent = IntentPalette(content = Color(0xFF6366F1), surface = Color(0xFFEEF2FF), border = Color(0xFF6366F1)),
        success = IntentPalette(content = Color(0xFF059669), surface = Color(0xFFECFDF5), border = Color(0xFF059669)),
        error = IntentPalette(content = Color(0xFFDC2626), surface = Color(0xFFFEF2F2), border = Color(0xFFDC2626)),
        warning = IntentPalette(content = Color(0xFFD97706), surface = Color(0xFFFFFBEB), border = Color(0xFFD97706)),
    ),
)

private val DarkColors = Colors(
    surface = Surface(
        primary = Color(0xFF121212),
        secondary = Color(0xFF1E1E1E),
        subtle = Color(0xFF2C2C2C),
        raised = Color(0xFF1E1E1E),
        skeleton = Color(0xFF2C2C2C),
    ),
    surfaceInteractive = SurfaceInteractive(
        enabled = Color(0xFF6366F1),
        hoverTap = Color(0xFF4F46E5),
        disabled = Color(0xFF374151),
    ),
    border = Border(
        primary = Color(0xFF374151),
        secondary = Color(0xFF4B5563),
        emphasis = Color(0xFFFFFFFF),
    ),
    element = Element(
        primary = Color(0xFFFFFFFF),
        secondary = Color(0xFF9CA3AF),
    ),
    elementInteractive = ElementInteractive(
        enabled = Color(0xFF111827),
        hoverTap = Color(0xFF9CA3AF),
        disabled = Color(0xFF9CA3AF),
    ),
    shadow = Shadow(spot = Color(0x33000000)),
    intents = Intents(
        accent = IntentPalette(content = Color(0xFF818CF8), surface = Color(0xFF312E81), border = Color(0xFF818CF8)),
        success = IntentPalette(content = Color(0xFF34D399), surface = Color(0xFF064E3B), border = Color(0xFF34D399)),
        error = IntentPalette(content = Color(0xFFFCA5A5), surface = Color(0xFF7F1D1D), border = Color(0xFFFCA5A5)),
        warning = IntentPalette(content = Color(0xFFFCD34D), surface = Color(0xFF78350F), border = Color(0xFFFCD34D)),
    ),
)

private val AppColorSchemes = ColorSchemes(light = LightColors, dark = DarkColors)

private val AppTypography = Typography(
    h1 = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 40.sp),
    h2 = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 32.sp),
    h3 = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Medium, fontSize = 24.sp),
    h4 = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Medium, fontSize = 18.sp),
    headingS = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 14.sp),
    headingM = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
    body = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
    bodyM = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Medium, fontSize = 16.sp),
    bodyS = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 14.sp, lineHeight = 20.sp),
    bodyXs = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 12.sp),
    labelS = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 12.sp),
    labelXs = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 10.sp),
    button = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
)

private val AppShape = Shape(
    buttonShape = RoundedCornerShape(percent = 50),
    circleShape = RoundedCornerShape(50),
    roundShape = RoundedCornerShape(16.dp),
    imageShape = CircleShape,
    card = RoundedCornerShape(8.dp),
    textShape = RoundedCornerShape(12.dp),
    chipShape = RoundedCornerShape(8.dp),
)
'''

# ─── core modules ─────────────────────────────────────────────────────────────

CORE_LOG_BUILD_GRADLE = '''plugins {
    alias(libs.plugins.kotlinMultiplatform)
}

kotlin {
    jvm()
    listOf(
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "CoreLog"
            isStatic = true
        }
    }
}
'''

ERROR_LOGGER = '''package __BASE_PACKAGE__.core.log

interface ErrorLogger {
    fun log(message: String)
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

        withHostTest {}
    }

    listOf(
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
        commonMain.dependencies {
            implementation(libs.kotlin.inject.runtime.kmp)
            implementation(libs.kotlinx.serialization.json)
            implementation(libs.synapse.core.datetime)
            implementation(libs.synapse.core.discopes)
            implementation(libs.synapse.core.network)
            implementation(project(":core:log"))__DATA_EXTRA_DEPS__
        }
        commonTest.dependencies {
            implementation(libs.kotlin.test)
            implementation(libs.ktor.client.mock)
            implementation(libs.kotlinx.coroutines.test)
        }
    }
}

dependencies {
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
    add("commonMainApi", project(":domain:__DOMAIN__:entities"))
}
''' + CONFIGURE_COMMON_MAIN_KSP

DOMAIN_REPOSITORY_IMPL = '''package __BASE_PACKAGE__.domain.__DOMAIN__.data

import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository

internal class __DOMAIN_PASCAL__RepositoryImpl : __DOMAIN_PASCAL__Repository {
    // TODO: implement repository methods
}
'''

DOMAIN_REPOSITORY_PROVIDERS_IMPL = '''package __BASE_PACKAGE__.domain.__DOMAIN__.data.di

import __BASE_PACKAGE__.core.log.ErrorLogger
import __BASE_PACKAGE__.domain.__DOMAIN__.data.__DOMAIN_PASCAL__RepositoryImpl
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.di.__DOMAIN_PASCAL__RepositoryProviders
import com.ribads.synapse.core.discopes.SingletonScope
import io.ktor.client.HttpClient
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
@SingletonScope
abstract class __DOMAIN_PASCAL__RepositoryProvidersImpl(
    private val client: HttpClient,
    private val logger: ErrorLogger,
) : __DOMAIN_PASCAL__RepositoryProviders {

    @SingletonScope
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
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}
''' + CONFIGURE_COMMON_MAIN_KSP

FEATURE_FETCH_USE_CASE = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase

import me.tatarka.inject.annotations.Inject

interface Fetch__FEATURE_PASCAL__UseCase {
    suspend fun execute(): __FEATURE_PASCAL__Result
}

internal class Fetch__FEATURE_PASCAL__UseCaseImpl @Inject constructor() : Fetch__FEATURE_PASCAL__UseCase {
    // TODO: map a repository result into __FEATURE_PASCAL__Result
    override suspend fun execute(): __FEATURE_PASCAL__Result = __FEATURE_PASCAL__Result.Success
}
'''

FEATURE_FETCH_USE_CASE_WIRED = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase

import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__EntityResult
import __BASE_PACKAGE__.domain.__DOMAIN__.entities.__DOMAIN_PASCAL__Repository
import me.tatarka.inject.annotations.Inject

interface Fetch__FEATURE_PASCAL__UseCase {
    suspend fun execute(): __FEATURE_PASCAL__Result
}

internal class Fetch__FEATURE_PASCAL__UseCaseImpl @Inject constructor(
    private val repository: __DOMAIN_PASCAL__Repository,
) : Fetch__FEATURE_PASCAL__UseCase {

    override suspend fun execute(): __FEATURE_PASCAL__Result = when (repository.fetch()) {
        is __DOMAIN_PASCAL__EntityResult.Success -> __FEATURE_PASCAL__Result.Success
        is __DOMAIN_PASCAL__EntityResult.Failure -> __FEATURE_PASCAL__Result.Failure
    }
}
'''

FEATURE_USE_CASE_RESULT = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase

sealed class __FEATURE_PASCAL__Result {
    data object Success : __FEATURE_PASCAL__Result()
    data object Failure : __FEATURE_PASCAL__Result()
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
    internal fun Fetch__FEATURE_PASCAL__UseCaseImpl.bind(): Fetch__FEATURE_PASCAL__UseCase = this
}
'''

FEATURE_USE_CASE_MODULE_WIRED = '''package __BASE_PACKAGE__.feature.__FEATURE__.usecase.di

import __BASE_PACKAGE__.domain.__DOMAIN__.entities.di.__DOMAIN_PASCAL__RepositoryProviders
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.Fetch__FEATURE_PASCAL__UseCase
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.Fetch__FEATURE_PASCAL__UseCaseImpl
import com.ribads.synapse.core.discopes.SingletonScope
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@SingletonScope
@Component
abstract class __FEATURE_PASCAL__UseCaseModule(
    @Component val repositories: __DOMAIN_PASCAL__RepositoryProviders,
) : __FEATURE_PASCAL__UseCaseProvider {

    @Provides
    internal fun Fetch__FEATURE_PASCAL__UseCaseImpl.bind(): Fetch__FEATURE_PASCAL__UseCase = this
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
    alias(libs.plugins.kotlinxSerialization)
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

compose.resources {
    packageOfResClass = "__BASE_PACKAGE__.feature.__FEATURE__.ui.resources"
}

dependencies {
    add("kspCommonMainMetadata", libs.kotlin.inject.compiler)
}
''' + CONFIGURE_COMMON_MAIN_KSP

# ── Feature UI: FeatureLauncher ──

FEATURE_LAUNCHER = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.launcher

import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.EntryProviderScope
import __BASE_PACKAGE__.feature.__FEATURE__.ui.navigation.ViewModelProviders
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreen
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import com.ribads.synapse.ui.compose.presentation.navigation.NavKey
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import kotlinx.serialization.Serializable
import kotlinx.serialization.modules.SerializersModule
import kotlinx.serialization.modules.polymorphic
import kotlinx.serialization.modules.subclass

@Serializable
internal data object __FEATURE_PASCAL__LandingRoute : NavKey

internal class __FEATURE_PASCAL__FeatureLauncher constructor(
    private val viewModelProviders: ViewModelProviders,
) : FeatureLauncher {

    override val featureName: String = FEATURE_NAME

    override val startKey: NavKey = __FEATURE_PASCAL__LandingRoute

    override val serializers: SerializersModule = SerializersModule {
        polymorphic(NavKey::class) {
            subclass(__FEATURE_PASCAL__LandingRoute::class)
        }
    }

    override fun EntryProviderScope<NavKey>.register(dispatcher: NavigationDispatcher) {
        entry<__FEATURE_PASCAL__LandingRoute> {
            LandingScreen(
                viewModel = viewModel { viewModelProviders.landingScreenViewModel.invoke() },
                navigationDispatcher = dispatcher,
            )
        }
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

# ── Feature UI: DI Module ──

FEATURE_MODULE = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.di

import __BASE_PACKAGE__.feature.__FEATURE__.ui.launcher.__FEATURE_PASCAL__FeatureLauncher
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.di.LandingScreenUiComponent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.di.create
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.__FEATURE_PASCAL__UseCaseProvider
import com.ribads.synapse.ui.compose.presentation.feature.FeatureLauncher
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.IntoMap
import me.tatarka.inject.annotations.Provides

@Component
abstract class __FEATURE_PASCAL__Module(@Component val useCaseProvider: __FEATURE_PASCAL__UseCaseProvider) {
    abstract val features: Map<String, FeatureLauncher>

    @Provides
    @IntoMap
    protected fun provideFeatureLauncher(launcher: FeatureLauncher): Pair<String, FeatureLauncher> =
        __FEATURE_PASCAL__FeatureLauncher.FEATURE_NAME to launcher

    @Provides
    internal fun provideViewModelComponent(): __FEATURE_PASCAL__ViewModelComponent =
        __FEATURE_PASCAL__ViewModelComponent::class.create(
            landingScreenUiComponent = LandingScreenUiComponent::class.create(useCaseProvider),
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
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.__FEATURE_PASCAL__Result
import com.ribads.synapse.ui.component.emptystate.model.EmptyStateModel
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand

internal object LandingScreenContract {

    interface Mapper {
        fun toResult(result: __FEATURE_PASCAL__Result): Result
        fun toResult(intent: Intent.Navigation): Result.NavigationRequested
    }

    sealed class Intent {
        data object LoadInitialData : Intent()
        sealed class Navigation : Intent() {
            data object Back : Navigation()
        }
    }

    sealed class Result {
        data object OnInitialDataLoading : Result()
        data object OnInitialDataLoaded : Result()
        data class OnInitialDataFailed(val model: EmptyStateModel) : Result()
        data class NavigationRequested(val command: NavigationCommand) : Result()
    }

    sealed class Effect {
        data class Navigate(val command: NavigationCommand) : Effect()
    }

    @Immutable
    data class ViewState(
        val content: Content,
    ) {
        sealed class Content {
            data object Loading : Content()
            data object Loaded : Content()
            data class Failed(val model: EmptyStateModel) : Content()
        }

        companion object {
            val Default = ViewState(content = Content.Loading)
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
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.Fetch__FEATURE_PASCAL__UseCase
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.merge
import me.tatarka.inject.annotations.Inject

internal class LandingScreenInteractor @Inject constructor(
    private val fetch__FEATURE_PASCAL__UseCase: Fetch__FEATURE_PASCAL__UseCase,
    private val mapper: Mapper,
) : Interactor<Intent, Result, ViewState> {

    @OptIn(ExperimentalCoroutinesApi::class)
    private fun loadInitialDataProcessor(upstream: Flow<Intent.LoadInitialData>): Flow<Result> =
        upstream.flatMapLatest {
            flow {
                emit(Result.OnInitialDataLoading)
                emit(mapper.toResult(fetch__FEATURE_PASCAL__UseCase.execute()))
            }
        }

    override fun process(
        intents: Flow<Intent>,
        state: StateFlow<ViewState>,
    ): Flow<Result> {
        return merge(
            intents.filterIsInstance<Intent.LoadInitialData>().let(::loadInitialDataProcessor),
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
            is Result.OnInitialDataLoading -> state.copy(content = ViewState.Content.Loading).noEffects()
            is Result.OnInitialDataLoaded -> state.copy(content = ViewState.Content.Loaded).noEffects()
            is Result.OnInitialDataFailed -> state.copy(content = ViewState.Content.Failed(result.model)).noEffects()
            is Result.NavigationRequested -> state withEffect Effect.Navigate(result.command)
        }
    }
}
'''

LANDING_MAPPER = '''package __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing

import com.ribads.synapse.ui.component.emptystate.model.EmptyStateModel
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand
import com.ribads.synapse.ui.element.text.Text
import __BASE_PACKAGE__.feature.__FEATURE__.ui.resources.Res
import __BASE_PACKAGE__.feature.__FEATURE__.ui.resources.landing_failed_title
import __BASE_PACKAGE__.feature.__FEATURE__.ui.resources.landing_retry
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Mapper
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Result
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.__FEATURE_PASCAL__Result
import me.tatarka.inject.annotations.Inject

internal class LandingScreenMapper @Inject constructor() : Mapper {

    override fun toResult(result: __FEATURE_PASCAL__Result): Result = when (result) {
        __FEATURE_PASCAL__Result.Success -> Result.OnInitialDataLoaded
        __FEATURE_PASCAL__Result.Failure -> Result.OnInitialDataFailed(
            EmptyStateModel(
                title = Text.Localized(Res.string.landing_failed_title),
                actionLabel = Text.Localized(Res.string.landing_retry),
            ),
        )
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

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.ribads.synapse.ui.component.emptystate.EmptyState
import com.ribads.synapse.ui.component.progress.CircularProgress
import com.ribads.synapse.ui.component.progress.model.CircularProgressModel
import com.ribads.synapse.ui.component.scaffold.Scaffold
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import com.ribads.synapse.ui.element.theme.Theme
import com.ribads.synapse.ui.mvi.CollectAsEffect
import com.ribads.synapse.ui.mvi.OnFirstComposition
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Effect
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.Intent
import __BASE_PACKAGE__.feature.__FEATURE__.ui.screens.landing.LandingScreenContract.ViewState

private const val LOADING_ARC_FRACTION = 0.5f

private val LoadingProgress = CircularProgressModel(value = LOADING_ARC_FRACTION, showPercentage = false)

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

    Scaffold { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = Theme.spacing.x6),
            contentAlignment = Alignment.Center,
        ) {
            when (val content = viewState.content) {
                ViewState.Content.Loading -> CircularProgress(model = LoadingProgress)
                is ViewState.Content.Failed -> EmptyState(
                    model = content.model,
                    onActionClick = { viewModel.emit(Intent.LoadInitialData) },
                )
                ViewState.Content.Loaded -> {
                    // TODO: Build __FEATURE_PASCAL__ landing screen UI
                }
            }
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
import __BASE_PACKAGE__.feature.__FEATURE__.usecase.di.__FEATURE_PASCAL__UseCaseProvider
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
internal abstract class LandingScreenUiComponent(
    @Component val useCaseProvider: __FEATURE_PASCAL__UseCaseProvider,
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
# Templates live in scripts/templates/ios/: loaded via load_template() at runtime.

# ─── Main Generator ───────────────────────────────────────────────────────────

SESSION_DOMAIN = "session"


def fail(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def render_template(rel_path: str, ctx: dict) -> str:
    return render(load_template(rel_path), ctx)


def kotlin_dir(module: Path, source_set: str, package: str) -> Path:
    return module / "src" / source_set / "kotlin" / pkg_to_path(package)


def domain_ctx(ctx: dict, domain: str, data_extra_deps: str = "") -> dict:
    return {
        **ctx,
        "DOMAIN": domain,
        "DOMAIN_PASCAL": to_pascal(domain),
        "DOMAIN_CAMEL": to_camel(domain),
        "DATA_EXTRA_DEPS": data_extra_deps,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Synapse KMP project with multi-module DDD architecture.",
    )
    parser.add_argument("--name", required=True, help="PascalCase project name, e.g. MyApp")
    parser.add_argument("--package", required=True, help="Base Kotlin package, e.g. com.example.myapp")
    parser.add_argument("--output", required=True, help="Absolute path to create project in")
    parser.add_argument("--domains", required=True, help="Comma-separated domain names (lowercase)")
    parser.add_argument("--features", required=True, help="Comma-separated feature names (lowercase)")
    parser.add_argument(
        "--with-session",
        action="store_true",
        help="Generate domain/session: encrypted token storage, bearer auth and token refresh",
    )
    parser.add_argument(
        "--synapse-version",
        default=None,
        help="Synapse library version. Defaults to the latest release on Maven Central; "
        "generation fails if that lookup fails.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def write_root(out: Path, ctx: dict, domains: list, features: list, with_session: bool, force: bool) -> None:
    included_domains = domains + ([SESSION_DOMAIN] if with_session else [])
    ctx = {
        **ctx,
        "DOMAIN_INCLUDES": "\n".join(
            f'include(":domain:{d}:entities")\ninclude(":domain:{d}:data")' for d in included_domains
        ),
        "FEATURE_INCLUDES": "\n".join(
            f'include(":features:{f}:ui")\ninclude(":features:{f}:usecase")' for f in features
        ),
    }
    write_file(out / "settings.gradle.kts", render(SETTINGS_GRADLE, ctx), force)
    write_file(out / "build.gradle.kts", ROOT_BUILD_GRADLE, force)
    write_file(out / "gradle.properties", GRADLE_PROPERTIES, force)
    write_file(out / ".gitignore", GITIGNORE, force)
    write_file(out / "gradle" / "libs.versions.toml", render(LIBS_VERSIONS_TOML, ctx), force)
    write_file(out / "gradle" / "wrapper" / "gradle-wrapper.properties", GRADLE_WRAPPER_PROPERTIES, force)
    copy_template_file("gradle/wrapper/gradle-wrapper.jar", out / "gradle" / "wrapper" / "gradle-wrapper.jar", force)
    copy_template_file("gradle/gradlew", out / "gradlew", force, executable=True)
    copy_template_file("gradle/gradlew.bat", out / "gradlew.bat", force)


def write_android_app(out: Path, ctx: dict, force: bool) -> None:
    android_app = out / "androidApp"
    res = android_app / "src" / "main" / "res"
    write_file(android_app / "build.gradle.kts", render(ANDROID_APP_BUILD_GRADLE, ctx), force)
    write_file(android_app / "src" / "main" / "AndroidManifest.xml", render(ANDROID_MANIFEST, ctx), force)
    write_file(res / "values" / "strings.xml", render(ANDROID_STRINGS_XML, ctx), force)
    write_file(res / "values" / "themes.xml", render(ANDROID_THEMES_XML, ctx), force)
    write_file(res / "values" / "colors.xml", ANDROID_COLORS_XML, force)
    write_file(res / "values-night" / "colors.xml", ANDROID_COLORS_NIGHT_XML, force)
    write_file(
        android_app / "src" / "main" / "java" / pkg_to_path(ctx["APP_PACKAGE"]) / "MainActivity.kt",
        render(MAIN_ACTIVITY, ctx),
        force,
    )


def build_root_app_builder(ctx: dict, example_domain: str, features: list, with_session: bool) -> str:
    dctx = domain_ctx(ctx, example_domain)
    imports = ROOT_APP_BUILDER_IMPORT
    if with_session:
        imports += ROOT_APP_BUILDER_SESSION_IMPORT
    imports += render(ROOT_APP_BUILDER_DOMAIN_IMPORT, dctx)
    for f in features:
        imports += render(ROOT_APP_BUILDER_FEATURE_IMPORT, {**ctx, "FEATURE": f, "FEATURE_PASCAL": to_pascal(f)})
    imports += ROOT_APP_BUILDER_SESSION_NETWORK_IMPORT if with_session else ROOT_APP_BUILDER_NETWORK_IMPORT

    feature_builds = []
    for index, f in enumerate(features):
        repositories = f"repositories = {to_camel(example_domain)}Repositories" if index == 0 else ""
        feature_builds.append(
            f"        val {to_camel(f)}Module = {to_pascal(f)}Module::class.create(\n"
            f"            useCaseProvider = {to_pascal(f)}UseCaseModule::class.create({repositories}),\n"
            "        )\n"
        )

    network = ROOT_APP_BUILDER_SESSION_NETWORK if with_session else ROOT_APP_BUILDER_NETWORK
    sorted_imports = "".join(f"{line}\n" for line in sorted(set(render(imports, ctx).splitlines())))
    return render(ROOT_APP_BUILDER_PACKAGE, ctx) + sorted_imports + render(ROOT_APP_BUILDER_CLASS, {
        **ctx,
        "NETWORK_BUILD": render(network, ctx),
        "DOMAIN_BUILD": render(ROOT_APP_BUILDER_DOMAIN, dctx),
        "FEATURE_BUILDS": "\n".join(feature_builds),
        "FEATURE_PARAMS": "\n".join(f"            {to_camel(f)}Module = {to_camel(f)}Module," for f in features),
    })


def build_compose_app_component(ctx: dict, features: list) -> str:
    component = COMPOSE_APP_COMPONENT_HEAD
    for f in features:
        component += render(COMPOSE_APP_COMPONENT_FEATURE_IMPORT, {**ctx, "FEATURE": f, "FEATURE_PASCAL": to_pascal(f)})
    return render(component + COMPOSE_APP_COMPONENT_CLASS, {
        **ctx,
        "FEATURE_CONSTRUCTOR_PARAMS": "\n".join(
            f"    private val {to_camel(f)}Module: {to_pascal(f)}Module," for f in features
        ),
        "FEATURE_MAP_ENTRIES": " +\n".join(f"        {to_camel(f)}Module.features" for f in features),
    })


def write_compose_app(out: Path, ctx: dict, domains: list, features: list, with_session: bool, force: bool) -> None:
    data_modules = domains + ([SESSION_DOMAIN] if with_session else [])
    ctx = {
        **ctx,
        "COMPOSE_APP_DOMAIN_DEPS": "\n".join(
            f"            implementation(projects.domain.{d}.data)" for d in data_modules
        ),
        "COMPOSE_APP_FEATURE_DEPS": "\n".join(
            f"            implementation(projects.features.{f}.ui)\n            implementation(projects.features.{f}.usecase)"
            for f in features
        ),
        "COMPOSE_APP_SESSION_DEPS": "\n            implementation(libs.synapse.core.shared.pref)" if with_session else "",
    }

    compose_app = out / "composeApp"
    common_src = kotlin_dir(compose_app, "commonMain", ctx["APP_PACKAGE"])
    ios_src = kotlin_dir(compose_app, "iosMain", ctx["APP_PACKAGE"])

    write_file(compose_app / "build.gradle.kts", render(COMPOSE_APP_BUILD_GRADLE, ctx), force)
    write_file(common_src / "AppEnvironment.kt", render_template("composeapp/AppEnvironment.kt", ctx), force)
    write_file(common_src / "CoreComposeApp.kt", render(CORE_COMPOSE_APP, ctx), force)
    write_file(common_src / "RootScreen.kt", render(ROOT_SCREEN, ctx), force)
    write_file(ios_src / "MainViewController.kt", render(MAIN_VIEW_CONTROLLER, ctx), force)

    write_file(common_src / "ui" / "MainContract.kt", render(MAIN_CONTRACT, ctx), force)
    write_file(common_src / "ui" / "MainInteractor.kt", render(MAIN_INTERACTOR, ctx), force)
    write_file(common_src / "ui" / "MainReducer.kt", render(MAIN_REDUCER, ctx), force)
    write_file(common_src / "ui" / "MainMapper.kt", render(MAIN_MAPPER, ctx), force)
    write_file(common_src / "ui" / "MainViewModel.kt", render(MAIN_VIEW_MODEL, ctx), force)
    write_file(common_src / "ui" / "di" / "MainUiComponent.kt", render(MAIN_UI_COMPONENT, ctx), force)

    write_file(common_src / "di" / "ErrorLoggers.kt", render_template("composeapp/ErrorLoggers.kt", ctx), force)
    write_file(common_src / "di" / "NetworkConfigs.kt", render_template("composeapp/NetworkConfigs.kt", ctx), force)
    write_file(
        common_src / "di" / "RootAppBuilder.kt",
        build_root_app_builder(ctx, domains[0], features, with_session),
        force,
    )
    write_file(common_src / "di" / "ComposeAppComponent.kt", build_compose_app_component(ctx, features), force)


def write_compose_ui(out: Path, ctx: dict, force: bool) -> None:
    compose_ui = out / "compose-ui"
    theme_dir = kotlin_dir(compose_ui, "commonMain", f"{ctx['BASE_PACKAGE']}.compose.ui.theme")
    write_file(compose_ui / "build.gradle.kts", render(COMPOSE_UI_BUILD_GRADLE, ctx), force)
    write_file(theme_dir / f"{ctx['PROJECT_NAME']}Theme.kt", render(APP_THEME, ctx), force)


def write_core(out: Path, ctx: dict, force: bool) -> None:
    log = out / "core" / "log"
    write_file(log / "build.gradle.kts", CORE_LOG_BUILD_GRADLE, force)
    write_file(kotlin_dir(log, "commonMain", f"{ctx['BASE_PACKAGE']}.core.log") / "ErrorLogger.kt", render(ERROR_LOGGER, ctx), force)


def write_domain(out: Path, ctx: dict, domain: str, worked_example: bool, force: bool) -> None:
    dctx = domain_ctx(ctx, domain)
    dp = dctx["DOMAIN_PASCAL"]

    entities = out / "domain" / domain / "entities"
    entities_src = kotlin_dir(entities, "commonMain", f"{ctx['BASE_PACKAGE']}.domain.{domain}.entities")
    write_file(entities / "build.gradle.kts", DOMAIN_ENTITIES_BUILD_GRADLE, force)
    write_file(entities_src / "di" / f"{dp}RepositoryProviders.kt", render(DOMAIN_REPOSITORY_PROVIDERS, dctx), force)

    data = out / "domain" / domain / "data"
    data_pkg = f"{ctx['BASE_PACKAGE']}.domain.{domain}.data"
    data_src = kotlin_dir(data, "commonMain", data_pkg)
    write_file(data / "build.gradle.kts", render(DOMAIN_DATA_BUILD_GRADLE, dctx), force)

    if not worked_example:
        write_file(entities_src / f"{dp}Repository.kt", render(DOMAIN_REPOSITORY, dctx), force)
        write_file(data_src / f"{dp}RepositoryImpl.kt", render(DOMAIN_REPOSITORY_IMPL, dctx), force)
        write_file(data_src / "di" / f"{dp}RepositoryProvidersImpl.kt", render(DOMAIN_REPOSITORY_PROVIDERS_IMPL, dctx), force)
        return

    for template, target in (
        ("Entity.kt", f"{dp}Entity.kt"),
        ("EntityResult.kt", f"{dp}EntityResult.kt"),
        ("FailureReason.kt", f"{dp}FailureReason.kt"),
        ("Repository.kt", f"{dp}Repository.kt"),
    ):
        write_file(entities_src / target, render_template(f"domain/example/entities/{template}", dctx), force)

    for template, target in (
        ("ApiResponse.kt", Path("datasource") / "api" / "model" / f"{dp}ApiResponse.kt"),
        ("Dto.kt", Path("datasource") / "dto" / f"{dp}Dto.kt"),
        ("DataSource.kt", Path("datasource") / f"{dp}DataSource.kt"),
        ("RepositoryImpl.kt", Path(f"{dp}RepositoryImpl.kt")),
        ("RepositoryProvidersImpl.kt", Path("di") / f"{dp}RepositoryProvidersImpl.kt"),
    ):
        write_file(data_src / target, render_template(f"domain/example/data/{template}", dctx), force)

    write_file(
        kotlin_dir(data, "commonTest", data_pkg) / f"{dp}RepositoryImplTest.kt",
        render_template("domain/example/test/RepositoryImplTest.kt", dctx),
        force,
    )


def write_session(out: Path, ctx: dict, force: bool) -> None:
    sctx = domain_ctx(ctx, SESSION_DOMAIN, data_extra_deps="\n            implementation(libs.synapse.core.shared.pref)")

    entities = out / "domain" / SESSION_DOMAIN / "entities"
    entities_src = kotlin_dir(entities, "commonMain", f"{ctx['BASE_PACKAGE']}.domain.{SESSION_DOMAIN}.entities")
    write_file(entities / "build.gradle.kts", DOMAIN_ENTITIES_BUILD_GRADLE, force)
    for template, target in (
        ("SessionTokens.kt", Path("SessionTokens.kt")),
        ("SessionRepository.kt", Path("SessionRepository.kt")),
        ("SessionRepositoryProviders.kt", Path("di") / "SessionRepositoryProviders.kt"),
    ):
        write_file(entities_src / target, render_template(f"session/entities/{template}", sctx), force)

    data = out / "domain" / SESSION_DOMAIN / "data"
    data_pkg = f"{ctx['BASE_PACKAGE']}.domain.{SESSION_DOMAIN}.data"
    data_src = kotlin_dir(data, "commonMain", data_pkg)
    write_file(data / "build.gradle.kts", render(DOMAIN_DATA_BUILD_GRADLE, sctx), force)
    for template, target in (
        ("StoredTokens.kt", Path("datasource") / "model" / "StoredTokens.kt"),
        ("TokenStore.kt", Path("datasource") / "TokenStore.kt"),
        ("RefreshModels.kt", Path("datasource") / "api" / "model" / "RefreshModels.kt"),
        ("TokenRefreshDataSource.kt", Path("datasource") / "TokenRefreshDataSource.kt"),
        ("SessionAuthTokenSource.kt", Path("SessionAuthTokenSource.kt")),
        ("SessionRepositoryImpl.kt", Path("SessionRepositoryImpl.kt")),
        ("SessionRepositoryProvidersImpl.kt", Path("di") / "SessionRepositoryProvidersImpl.kt"),
    ):
        write_file(data_src / target, render_template(f"session/data/{template}", sctx), force)

    write_file(
        kotlin_dir(data, "commonTest", data_pkg) / "SessionAuthTokenSourceTest.kt",
        render_template("session/test/SessionAuthTokenSourceTest.kt", sctx),
        force,
    )


def write_feature(out: Path, ctx: dict, feature: str, wired_domain: Optional[str], force: bool) -> None:
    fctx = {**ctx, "FEATURE": feature, "FEATURE_PASCAL": to_pascal(feature), "FEATURE_CAMEL": to_camel(feature)}
    fp = fctx["FEATURE_PASCAL"]
    if wired_domain:
        fctx = domain_ctx(fctx, wired_domain)
        fctx["USECASE_DOMAIN_DEPS"] = f"                implementation(projects.domain.{wired_domain}.entities)"
        fetch_use_case, use_case_module = FEATURE_FETCH_USE_CASE_WIRED, FEATURE_USE_CASE_MODULE_WIRED
    else:
        fctx["USECASE_DOMAIN_DEPS"] = "                // TODO: add domain entity dependencies"
        fetch_use_case, use_case_module = FEATURE_FETCH_USE_CASE, FEATURE_USE_CASE_MODULE

    usecase = out / "features" / feature / "usecase"
    usecase_src = kotlin_dir(usecase, "commonMain", f"{ctx['BASE_PACKAGE']}.feature.{feature}.usecase")
    write_file(usecase / "build.gradle.kts", render(FEATURE_USECASE_BUILD_GRADLE, fctx), force)
    write_file(usecase_src / f"Fetch{fp}UseCase.kt", render(fetch_use_case, fctx), force)
    write_file(usecase_src / f"{fp}Result.kt", render(FEATURE_USE_CASE_RESULT, fctx), force)
    write_file(usecase_src / "di" / f"{fp}UseCaseProvider.kt", render(FEATURE_USE_CASE_PROVIDER, fctx), force)
    write_file(usecase_src / "di" / f"{fp}UseCaseModule.kt", render(use_case_module, fctx), force)

    ui = out / "features" / feature / "ui"
    ui_src = kotlin_dir(ui, "commonMain", f"{ctx['BASE_PACKAGE']}.feature.{feature}.ui")
    write_file(ui / "build.gradle.kts", render(FEATURE_UI_BUILD_GRADLE, fctx), force)
    write_file(
        ui / "src" / "commonMain" / "composeResources" / "values" / "strings.xml",
        load_template("feature/strings.xml"),
        force,
    )
    write_file(ui_src / "launcher" / f"{fp}FeatureLauncher.kt", render(FEATURE_LAUNCHER, fctx), force)
    write_file(ui_src / "navigation" / "ViewModelProviders.kt", render(FEATURE_VIEW_MODEL_PROVIDERS, fctx), force)
    write_file(ui_src / "di" / f"{fp}Module.kt", render(FEATURE_MODULE, fctx), force)
    write_file(ui_src / "di" / f"{fp}ViewModelComponent.kt", render(FEATURE_VIEW_MODEL_COMPONENT, fctx), force)

    landing = ui_src / "screens" / "landing"
    write_file(landing / "LandingScreenContract.kt", render(LANDING_CONTRACT, fctx), force)
    write_file(landing / "LandingScreenInteractor.kt", render(LANDING_INTERACTOR, fctx), force)
    write_file(landing / "LandingScreenReducer.kt", render(LANDING_REDUCER, fctx), force)
    write_file(landing / "LandingScreenMapper.kt", render(LANDING_MAPPER, fctx), force)
    write_file(landing / "LandingScreenViewModel.kt", render(LANDING_VIEW_MODEL, fctx), force)
    write_file(landing / "LandingScreen.kt", render(LANDING_SCREEN, fctx), force)
    write_file(landing / "di" / "LandingScreenUiComponent.kt", render(LANDING_UI_COMPONENT, fctx), force)


def write_ios_app(out: Path, ctx: dict, force: bool) -> None:
    ios_root = out / "iosApp"
    ios_src = ios_root / "iosApp"
    ios_xcodeproj = ios_root / "iosApp.xcodeproj"
    ios_assets = ios_src / "Assets.xcassets"

    write_file(ios_src / "iOSApp.swift", load_template("ios/iOSApp.swift"), force)
    write_file(ios_src / "ContentView.swift", load_template("ios/ContentView.swift"), force)
    write_file(ios_src / "Info.plist", load_template("ios/Info.plist"), force)

    # Xcode complains if AppIcon/AccentColor are missing, so these are empty stubs.
    write_file(ios_assets / "Contents.json", load_template("ios/Assets.Contents.json"), force)
    write_file(ios_assets / "AccentColor.colorset" / "Contents.json", load_template("ios/AccentColor.Contents.json"), force)
    write_file(ios_assets / "AppIcon.appiconset" / "Contents.json", load_template("ios/AppIcon.Contents.json"), force)
    write_file(
        ios_src / "Preview Content" / "Preview Assets.xcassets" / "Contents.json",
        load_template("ios/PreviewAssets.Contents.json"),
        force,
    )

    write_file(ios_root / "Configuration" / "Config.xcconfig", render_template("ios/Config.xcconfig", ctx), force)
    write_file(ios_xcodeproj / "project.pbxproj", render_template("ios/project.pbxproj", ctx), force)
    write_file(ios_xcodeproj / "project.xcworkspace" / "contents.xcworkspacedata", load_template("ios/contents.xcworkspacedata"), force)


def main() -> None:
    args = parse_args()

    name: str = args.name
    base_pkg: str = args.package.strip().strip(".")
    out = Path(args.output).expanduser().resolve()
    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    features = [f.strip() for f in args.features.split(",") if f.strip()]
    with_session: bool = args.with_session
    force: bool = args.force

    if not name or not name[0].isupper():
        fail("--name must be PascalCase, e.g. MyApp")
    if not domains:
        fail("--domains needs at least one domain; the first one is generated as the worked data-layer example")
    if not features:
        fail("--features needs at least one feature; the first one is the start feature")
    if with_session and SESSION_DOMAIN in domains:
        fail(f"--with-session generates domain/{SESSION_DOMAIN}; remove '{SESSION_DOMAIN}' from --domains")
    if not force and (out / "settings.gradle.kts").exists():
        fail(f"{out}/settings.gradle.kts already exists (use --force to overwrite)", code=1)

    ctx = {
        "PROJECT_NAME": name,
        "PROJECT_NAME_LOWER": name.lower(),
        "BASE_PACKAGE": base_pkg,
        "APP_PACKAGE": f"{base_pkg}.app",
        "SYNAPSE_VERSION": resolve_synapse_version(args.synapse_version),
        "FIRST_FEATURE": features[0],
    }

    print(f"Generating {name} project in {out}")
    print(f"  Package: {base_pkg}")
    print(f"  Domains: {', '.join(domains)}{f' (+ {SESSION_DOMAIN})' if with_session else ''}")
    print(f"  Features: {', '.join(features)}")
    print()

    write_root(out, ctx, domains, features, with_session, force)
    write_android_app(out, ctx, force)
    write_compose_app(out, ctx, domains, features, with_session, force)
    write_compose_ui(out, ctx, force)
    write_core(out, ctx, force)
    for index, domain in enumerate(domains):
        write_domain(out, ctx, domain, worked_example=index == 0, force=force)
    if with_session:
        write_session(out, ctx, force)
    for index, feature in enumerate(features):
        write_feature(out, ctx, feature, wired_domain=domains[0] if index == 0 else None, force=force)
    write_ios_app(out, ctx, force)

    domain_modules = 2 * (len(domains) + (1 if with_session else 0))
    total_modules = 1 + domain_modules + 2 * len(features) + 3  # core:log + domains + features + androidApp, composeApp, compose-ui
    print()
    print(f"Done. Generated {total_modules} modules.")
    print()
    print("Next steps:")
    print(f"  1. cd {out}")
    print("  2. Set API_BASE_URL per build type in androidApp/build.gradle.kts and iosApp/Configuration/Config.xcconfig")
    print(f"  3. Customize the theme in compose-ui/.../theme/{name}Theme.kt")
    print(f"  4. Replace the worked example in domain/{domains[0]}/ with your real endpoint, then wire the other domains")
    print("  5. Open in Android Studio / Fleet and sync Gradle")


if __name__ == "__main__":
    main()
