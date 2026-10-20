---
name: init-project
description: Use when initializing a new KMP project with Synapse libraries. Generates the full multi-module DDD architecture (core, domain, features, androidApp, composeApp, compose-ui, iosApp) with IRSE-MVI wiring, kotlin-inject DI, and Compose Multiplatform navigation, all from templates.
user-invocable: true
---

# init-project: Synapse KMP Project Scaffold

Generates a complete Kotlin Multiplatform project with the canonical Synapse multi-module DDD architecture. Uses heavy templating: Claude runs a Python script, not freehand code generation.

## What it creates

```
<project>/
├── settings.gradle.kts
├── build.gradle.kts
├── gradle.properties
├── .gitignore                             # Gradle, Android, Xcode, IDE ignores
├── gradlew                                # Gradle wrapper script (chmod +x)
├── gradlew.bat
├── gradle/libs.versions.toml
├── gradle/wrapper/gradle-wrapper.properties
├── gradle/wrapper/gradle-wrapper.jar
│
├── androidApp/                             # Android application module
│   ├── build.gradle.kts                   # com.android.application; API_BASE_URL per build type
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/<pkg>/app/
│       │   └── MainActivity.kt            # Builds AppEnvironment from BuildConfig
│       └── res/
│           ├── values/
│           │   ├── strings.xml
│           │   ├── themes.xml             # DayNight window theme
│           │   └── colors.xml             # window_background = light surface.primary
│           └── values-night/
│               └── colors.xml             # window_background = dark surface.primary
│
├── composeApp/                             # KMP library: DI wiring + shared app logic
│   ├── build.gradle.kts                   # androidMultiplatformLibrary plugin
│   └── src/
│       ├── commonMain/kotlin/<pkg>/app/
│       │   ├── AppEnvironment.kt          # apiBaseUrl + verboseNetworkLogging, read by each platform
│       │   ├── CoreComposeApp.kt          # ImageLoader, WithImagePainter, Theme, ToastHandler, RootScreen
│       │   ├── RootScreen.kt             # Scaffold + NavContainer (ThemedBottomSheetAppearance)
│       │   ├── di/
│       │   │   ├── RootAppBuilder.kt      # Builds the graph once per process: logger, HttpClient, domains, features
│       │   │   ├── ComposeAppComponent.kt # Merges all feature modules
│       │   │   ├── NetworkConfigs.kt      # AppEnvironment.toNetworkConfig(), Kermit-backed HttpLogger
│       │   │   └── ErrorLoggers.kt        # Kermit-backed ErrorLogger
│       │   └── ui/
│       │       ├── MainContract.kt        # Main screen IRSE-MVI
│       │       ├── MainInteractor.kt
│       │       ├── MainReducer.kt
│       │       ├── MainMapper.kt
│       │       ├── MainViewModel.kt
│       │       └── di/MainUiComponent.kt
│       └── iosMain/kotlin/<pkg>/app/
│           └── MainViewController.kt      # Builds AppEnvironment from Info.plist
│
├── compose-ui/                            # Theme layer
│   ├── build.gradle.kts
│   └── src/commonMain/kotlin/<pkg>/compose/ui/theme/
│       └── <Name>Theme.kt              # WithAppTheme root (light/dark ColorSchemes, typography, shapes)
│
├── core/
│   └── log/                               # Error logging
│       ├── build.gradle.kts
│       └── src/commonMain/kotlin/<pkg>/core/log/
│           └── ErrorLogger.kt
│
├── domain/<name>/                         # One per --domain
│   ├── entities/                          # Repository interface + its providers interface
│   │   ├── build.gradle.kts
│   │   └── src/commonMain/kotlin/<pkg>/domain/<name>/entities/
│   │       ├── <Name>Repository.kt
│   │       └── di/<Name>RepositoryProviders.kt
│   └── data/                              # Implementations (androidMultiplatformLibrary, host tests)
│       ├── build.gradle.kts
│       └── src/commonMain/kotlin/<pkg>/domain/<name>/data/
│           ├── <Name>RepositoryImpl.kt
│           └── di/<Name>RepositoryProvidersImpl.kt   # Takes HttpClient + ErrorLogger
│
├── domain/<first-domain>/                 # The first --domain is a worked example of the whole chain
│   ├── entities/…/                        # <Name>Entity, <Name>EntityResult, <Name>FailureReason, <Name>Repository.fetch()
│   └── data/…/
│       ├── datasource/api/model/<Name>ApiResponse.kt   # internal @Serializable wire model
│       ├── datasource/dto/<Name>Dto.kt                 # internal, nullability resolved
│       ├── datasource/<Name>DataSource.kt              # internal, HttpClient, relative path "<name>"
│       ├── <Name>RepositoryImpl.kt                     # The single catch: log, map NetworkFailure to a reason
│       ├── di/<Name>RepositoryProvidersImpl.kt
│       └── commonTest/…/<Name>RepositoryImplTest.kt    # MockEngine: success, offline, 401, malformed, cancellation
│
├── domain/session/                        # Only with --with-session
│   ├── entities/…/                        # SessionRepository (observeSignedIn, establish, signOut), SessionTokens
│   └── data/…/
│       ├── datasource/TokenStore.kt                  # Encrypted prefs, one JSON value, StateFlow cache
│       ├── datasource/TokenRefreshDataSource.kt      # POST auth/refresh
│       ├── SessionAuthTokenSource.kt                 # AuthTokenSource the HttpClient's bearer auth reads
│       ├── SessionRepositoryImpl.kt
│       ├── di/SessionRepositoryProvidersImpl.kt      # Exposes authTokenSource
│       └── commonTest/…/SessionAuthTokenSourceTest.kt
│
├── features/<name>/                       # One per --feature; the first one's use case reads the first domain
│   ├── usecase/                           # Business logic
│   │   ├── build.gradle.kts
│   │   └── src/commonMain/kotlin/<pkg>/feature/<name>/usecase/
│   │       ├── Fetch<Name>UseCase.kt      # Public interface + internal impl
│   │       ├── <Name>Result.kt            # Sealed Success / Failure the use case returns
│   │       └── di/
│   │           ├── <Name>UseCaseModule.kt
│   │           └── <Name>UseCaseProvider.kt
│   └── ui/                                # IRSE-MVI screens + navigation (androidMultiplatformLibrary)
│       ├── build.gradle.kts                # Res class in <pkg>.feature.<name>.ui.resources
│       ├── src/commonMain/composeResources/values/strings.xml   # Landing failure copy
│       └── src/commonMain/kotlin/<pkg>/feature/<name>/ui/
│           ├── launcher/<Name>FeatureLauncher.kt
│           ├── navigation/
│           │   └── ViewModelProviders.kt
│           ├── di/
│           │   ├── <Name>Module.kt
│           │   └── <Name>ViewModelComponent.kt
│           └── screens/landing/           # First screen scaffold (7 IRSE-MVI files)
│               ├── LandingScreenContract.kt
│               ├── LandingScreenInteractor.kt
│               ├── LandingScreenReducer.kt
│               ├── LandingScreenMapper.kt
│               ├── LandingScreenViewModel.kt
│               ├── LandingScreen.kt
│               └── di/LandingScreenUiComponent.kt
│
└── iosApp/                                # Xcode project (objectVersion = 77)
    ├── Configuration/
    │   └── Config.xcconfig                # PRODUCT_NAME, BUNDLE_IDENTIFIER, TEAM_ID, API_BASE_URL per configuration
    ├── iosApp/
    │   ├── iOSApp.swift                   # @main App entry
    │   ├── ContentView.swift              # ComposeView wrapper for KMP UIViewController
    │   ├── Info.plist                     # ApiBaseUrl, VerboseNetworkLogging from the xcconfig
    │   ├── Assets.xcassets/               # AccentColor + AppIcon stubs
    │   └── Preview Content/Preview Assets.xcassets/
    └── iosApp.xcodeproj/
        ├── project.pbxproj                # PBXFileSystemSynchronizedRootGroup-based
        └── project.xcworkspace/contents.xcworkspacedata
```

## Script

`scripts/init_project.py`: Python 3.9 or newer, stdlib only (macOS's bundled `/usr/bin/python3` is enough). Static template files live in `scripts/templates/<area>/` and are loaded via `load_template()`. iOS templates are in `scripts/templates/ios/`.

```
python3 "${CLAUDE_SKILL_DIR}/scripts/init_project.py" \
    --name <PascalCaseName> \
    --package <base.package> \
    --output <abs/path/to/project> \
    --domains <comma,separated,domain,names> \
    --features <comma,separated,feature,names> \
    [--with-session] \
    [--synapse-version <version>] \
    [--force]
```

### Arguments

| Flag | Required | Meaning |
|---|---|---|
| `--name` | yes | PascalCase project name (e.g. `MyApp`). Sets the root project name, `<Name>Theme`, the `<Name>App` graph holder, the Android label and window theme, and the iOS `PRODUCT_NAME`. It does **not** name the iOS framework: that is always `ComposeApp`, which the Swift templates `import`. |
| `--package` | yes | Base Kotlin package (e.g. `com.example.myapp`). All modules derive their packages from this. |
| `--output` | yes | Absolute path where the project directory will be created. |
| `--domains` | yes | Comma-separated domain names in lowercase (e.g. `catalog,profile,orders`), at least one. Each gets `entities/` + `data/` modules. The first one is generated as a worked example of the whole data chain and is read by the first feature. |
| `--features` | yes | Comma-separated feature names in lowercase (e.g. `auth,home,profile`), at least one. Each gets `usecase/` + `ui/` modules with a landing screen. The first one is the start feature. |
| `--with-session` | no | Also generate `domain/session`: encrypted token storage, an `AuthTokenSource` for bearer auth, and token refresh. Exits with status 2 if `session` is also in `--domains`. Without it, the `HttpClient` sends no credentials. |
| `--synapse-version` | no | Synapse library version. Defaults to the latest release on Maven Central (`com.ribads.synapse:core-network` `maven-metadata.xml`), so a release without `core-network` is never picked. If that lookup fails (offline, proxy, TLS, or no release publishes `core-network`), the script exits with an error and writes nothing; re-run with an explicit version. There is no built-in fallback version. |
| `--force` | no | Overwrite existing files. Otherwise aborts if output dir already has a `settings.gradle.kts`. |

### Example

```sh
python3 "${CLAUDE_SKILL_DIR}/scripts/init_project.py" \
    --name Outside \
    --package com.outside \
    --output /Users/ribads/Projects/outside-new \
    --domains activities,profile,messaging \
    --features discover,profile,notifications,activities,create,settings \
    --with-session
```

Omit `--synapse-version` to use the latest published release. Pass it explicitly to pin a version or to generate without network access.

## Gradle conventions

The generated project targets **Gradle 9.6.0** with **Kotlin 2.4.21**, **KSP 2.3.6**, **AGP 9.4.1** and **Compose Multiplatform 1.12.2**, matching the toolchain Synapse is built with.

Key conventions:
- **`androidApp`** is a separate module using `com.android.application` plugin. It contains `MainActivity`, `AndroidManifest.xml`, and Android resources
- **`composeApp`** is a KMP library using `com.android.kotlin.multiplatform.library` (not `com.android.application`)
- **Android config lives inside `kotlin {}` block**: `kotlin { android { namespace = "..."; compileSdk = ...; minSdk = ... } }`
- **`androidResources { enable = true }`** for modules that need Android resources
- **JVM target is 21** (`JvmTarget.JVM_21`, `JavaVersion.VERSION_21`)
- **MVI files go in `ui/` package** (e.g., `app.ui.MainContract`), not `mvi/`
- **Landing screen files use `LandingScreen` prefix** (e.g., `LandingScreenContract`, `LandingScreenViewModel`)
- **`kotlin-inject-runtime-kmp`** is used instead of `kotlin-inject-runtime`
- **Modules with kotlin-inject codegen** (`composeApp`, each `domain/*/data`, each `features/*/usecase` and `features/*/ui`) declare `add("kspCommonMainMetadata", libs.kotlin.inject.compiler)` and call `configureCommonMainKsp()`, which puts the generated sources on the common compile path. The project has no `build-logic`, so the script writes an identical copy of that function at the bottom of each of those build files. Change it in every copy, or move it into a convention plugin once the project grows one.

## Runtime wiring

What the generated app already does, so you build on it instead of re-adding it:

- **Environment comes from the platform.** `androidApp` declares `API_BASE_URL` per build type (`buildConfigField`), and `MainActivity` builds `AppEnvironment(BuildConfig.API_BASE_URL, BuildConfig.DEBUG)`. On iOS, `Config.xcconfig` sets `API_BASE_URL` and `VERBOSE_NETWORK_LOGGING` per configuration, `Info.plist` exposes them as `ApiBaseUrl` and `VerboseNetworkLogging`, and `MainViewController()` reads them. A missing or blank key fails at launch. Shared code never hardcodes a URL.
- **One DI graph per process.** `CoreComposeApp(environment)` calls `RootAppBuilder.obtain(environment)`, which builds the graph on first use and returns the same instance afterwards, so activity recreation (rotation, dark-mode switch, fold) never duplicates `@SingletonScope` objects. `<Name>App.mainViewModel` is a factory, so a new `ViewModelStore` gets a fresh `MainViewModel`.
- **One `HttpClient`, from `/synapse:network`.** `RootAppBuilder` builds it once with `buildHttpClient(environment.toNetworkConfig(), tokens)` and hands it to each domain's `RepositoryProvidersImpl`. It sets the base URL (request paths are relative, with no leading slash), JSON, the request timeout and `expectSuccess`. When `verboseNetworkLogging` is on it logs bodies through Kermit, with `Authorization` redacted. The project declares no Ktor engine of its own. Do not build a second client for API traffic.
- **Bearer auth stays on the API host.** When an `AuthTokenSource` is passed, the token is read per request (no client-side caching) and attached only to requests whose host is the base URL's host. A 401 from that host triggers one `refresh`; a 401 from any other host is never refreshed or retried with the token. Without a token source, the `Auth` plugin is not installed at all.
- **Failures are classified once.** `Throwable.toNetworkFailure()` (from `/synapse:network`) maps Ktor exceptions to `NetworkFailure` (`Offline`, `Timeout`, `Unauthorized`, `Http(status)`, `Malformed`, `Unexpected`). The repository is the single catch point: it rethrows `CancellationException`, logs, and maps the failure to a domain reason (see `/synapse:data-boundaries`).
- **Session** (with `--with-session`). `domain/session/data` stores both tokens as one value in `buildEncryptedSharedPrefManager("<name>_session")`, implements `AuthTokenSource`, and refreshes through `POST auth/refresh` on a separate client with logging off. A 400, 401 or 403 from refresh ends the session; any other failure, such as offline, fails the request and keeps the session. `SessionRepository.establish(tokens)` is how a sign-in flow saves tokens.
- **Toasts work from any screen.** `ToastHandler` wraps `RootScreen` inside `<Name>Theme`, so `Toast.current` resolves everywhere below it (see `/synapse:ui-components`).
- **Images.** The singleton Coil `ImageLoader` calls `installSynapseImageComponents()` (from `ui:element`) in shared code, so `Image.LocalIdentifier` (Photos assets on iOS) loads. `ui:element` brings Coil's network fetcher and engines, so image loading never goes through the API client. SVG decoding comes from the `coil-svg` dependency, which registers itself.
- **Use case to screen.** The first feature's `Fetch<Name>UseCaseImpl` reads the first domain's repository and returns the feature-owned sealed `<Name>Result` (`Success` / `Failure`), never `kotlin.Result`. The landing screen shows Loading, then the content or an `EmptyState` with a retry action, following `/synapse:data-boundaries` and `/synapse:mvi`. Feature UI modules depend only on `<Name>UseCaseProvider`, so they never see domain types.

## When to use

Invoke this skill whenever a user wants to:
- Create a new KMP project that uses Synapse
- Initialize a project with the multi-module DDD architecture
- Bootstrap a new app with IRSE-MVI, kotlin-inject DI, and Compose Multiplatform navigation

Always run the script rather than hand-writing the scaffold; that is the whole point.

## After running the script

The script generates a compiling skeleton. Synapse artifacts resolve from Maven Central (already configured in `settings.gradle.kts`), so no extra credentials are needed for a default build. The user still needs to:

1. **Set the API base URLs.** Replace the placeholder hosts in `androidApp/build.gradle.kts` (`buildConfigField` per build type) and `iosApp/Configuration/Config.xcconfig` (`API_BASE_URL[config=…]`). Keep the trailing `/`. In the xcconfig, write `https:/$()/host/`: `//` starts a comment there, and `$()` breaks it up. Add product flavors or Xcode configurations the same way when you need more environments.
2. **Customize the theme.** Edit `compose-ui/.../<Name>Theme.kt` with brand colours for both the light and dark schemes, fonts and shapes. The app follows the device appearance (`Appearance.System`); pass another `Appearance` to `<Name>Theme` to fix it or to drive it from a user setting. Keep `window_background` in `androidApp/src/main/res/values{,-night}/colors.xml` equal to each scheme's `surface.primary`.
3. **Add fonts.** Place `.ttf`/`.otf` files in `compose-ui/src/commonMain/composeResources/font/`.
4. **Replace the worked example.** The first domain fetches a placeholder `GET <name>` list. Point its `DataSource`, `ApiResponse` and `Entity` at a real endpoint, and give the first feature's `<Name>Result.Success` the data its screen needs. Follow the same chain in the other domains (their repositories are empty `// TODO` skeletons), then pass each domain's `RepositoryProvidersImpl` into the use-case module that needs it, as `RootAppBuilder.build()` does for the first one.
5. **Wire sign-in** (with `--with-session`). Point `TokenRefreshDataSource` and its models at your token endpoint, and call `SessionRepository.establish(tokens)` from your sign-in use case.
6. **Add screens.** Use `/synapse:create-screen` to add more screens to existing features.
7. **Set Xcode `TEAM_ID`.** Open `iosApp/Configuration/Config.xcconfig` and fill in your Apple Developer team identifier; it feeds `DEVELOPMENT_TEAM` for code signing (leave blank for simulator-only builds).
8. **Add app icon images.** Drop 1024×1024 PNGs into `iosApp/iosApp/Assets.xcassets/AppIcon.appiconset/` and update its `Contents.json`.
9. **Open in Android Studio / Fleet.** Sync Gradle, then run on Android. For iOS, open `iosApp/iosApp.xcodeproj` in Xcode. Run the generated tests with `./gradlew testAndroidHostTest`.
10. **Add architecture tests.** The script does not scaffold them. Add a `konsist` JVM module enforcing the layer boundaries (feature UI must not import `domain.*` or any `*Repository`; `usecase` must not reach into the data layer; one `execute`/`observe*` per use case). The module graph blocks cross-module leaks on its own, but Konsist catches the rest and keeps them caught. `/synapse:data-boundaries` has the tests to copy.

## Related skills

- `/synapse:create-screen`: Add a new IRSE-MVI screen to an existing feature
- `/synapse:build-screen`: End-to-end screen build workflow
- `/synapse:mvi`: IRSE-MVI APIs (Intent → Interactor → Result → Reducer → State/Effect)
- `/synapse:data-boundaries`: Layer rules, UseCase and error contracts, Konsist enforcement
- `/synapse:network`: `buildHttpClient`, `NetworkConfig`, `AuthTokenSource`, `NetworkFailure`
- `/synapse:navigation`: FeatureLauncher, typed NavKey routes, NavigationCommand
- `/synapse:di-scopes`: SingletonScope, kotlin-inject wiring
- `/synapse:ui-element`: Theme, Colors, Typography, Shape, `installSynapseImageComponents`
- `/synapse:ui-components`: Scaffold, Card, Tray, inputs, buttons, ToastHandler
- `/synapse:component-authoring`: Building app-level composables in `compose-ui/`
