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
│   ├── build.gradle.kts                   # com.android.application plugin
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/<pkg>/app/
│       │   └── MainActivity.kt
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
│       │   ├── AppContext.kt              # expect class
│       │   ├── CoreComposeApp.kt          # ImageLoader, WithImagePainter, Theme, ToastHandler, RootScreen
│       │   ├── RootScreen.kt             # Scaffold + NavContainer (ThemedBottomSheetAppearance)
│       │   ├── di/
│       │   │   ├── RootAppBuilder.kt      # Builds the DI graph once per process (obtain)
│       │   │   ├── ComposeAppComponent.kt # Merges all feature modules
│       │   │   ├── NetworkComponent.kt    # CoreClient provider, one per graph
│       │   │   └── AppConfigurationProviderFactory.kt
│       │   └── ui/
│       │       ├── MainContract.kt        # Main screen IRSE-MVI
│       │       ├── MainInteractor.kt
│       │       ├── MainReducer.kt
│       │       ├── MainMapper.kt
│       │       ├── MainViewModel.kt
│       │       └── di/MainUiComponent.kt
│       ├── androidMain/kotlin/<pkg>/app/
│       │   └── AppContext.android.kt      # actual (Android Context)
│       └── iosMain/kotlin/<pkg>/app/
│           ├── AppContext.ios.kt          # actual (stub)
│           └── MainViewController.kt
│
├── compose-ui/                            # Theme layer
│   ├── build.gradle.kts
│   └── src/commonMain/kotlin/<pkg>/compose/ui/theme/
│       └── <Name>Theme.kt              # WithAppTheme root (light/dark ColorSchemes, typography, shapes)
│
├── core/
│   ├── network/                           # HTTP client (Ktor)
│   │   ├── build.gradle.kts
│   │   └── src/
│   │       ├── commonMain/kotlin/<pkg>/core/network/
│   │       │   ├── CoreClient.kt
│   │       │   ├── CoreClientImpl.kt     # Builds its HttpClient once
│   │       │   ├── HttpClient.kt         # expect/actual
│   │       │   └── CoreRequestError.kt
│   │       ├── jvmMain/kotlin/<pkg>/core/network/
│   │       │   └── HttpClient.jvm.kt
│   │       └── iosMain/kotlin/<pkg>/core/network/
│   │           └── HttpClient.ios.kt
│   ├── auth/                              # OAuth token storage
│   │   ├── build.gradle.kts
│   │   └── src/commonMain/kotlin/<pkg>/core/auth/
│   │       ├── OauthTokenProvider.kt
│   │       └── OauthToken.kt
│   ├── config/                            # App configuration
│   │   ├── build.gradle.kts
│   │   └── src/commonMain/kotlin/<pkg>/core/config/
│   │       ├── AppConfigurationProvider.kt
│   │       └── ConfigurationProperties.kt
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
│   └── data/                              # Implementations (androidMultiplatformLibrary)
│       ├── build.gradle.kts
│       └── src/commonMain/kotlin/<pkg>/domain/<name>/data/
│           ├── <Name>RepositoryImpl.kt
│           └── di/<Name>RepositoryProvidersImpl.kt
│
├── features/<name>/                       # One per --feature
│   ├── usecase/                           # Business logic
│   │   ├── build.gradle.kts
│   │   └── src/commonMain/kotlin/<pkg>/feature/<name>/usecase/
│   │       ├── Fetch<Name>UseCase.kt      # Public interface + internal impl
│   │       ├── <Name>Result.kt            # Sealed Success / Failure the use case returns
│   │       └── di/
│   │           ├── <Name>UseCaseModule.kt
│   │           └── <Name>UseCaseProvider.kt
│   └── ui/                                # IRSE-MVI screens + navigation (androidMultiplatformLibrary)
│       ├── build.gradle.kts
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
    │   └── Config.xcconfig                # PRODUCT_NAME, BUNDLE_IDENTIFIER, TEAM_ID
    ├── iosApp/
    │   ├── iOSApp.swift                   # @main App entry
    │   ├── ContentView.swift              # ComposeView wrapper for KMP UIViewController
    │   ├── Info.plist
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
    [--synapse-version <version>] \
    [--force]
```

### Arguments

| Flag | Required | Meaning |
|---|---|---|
| `--name` | yes | PascalCase project name (e.g. `MyApp`). Sets the root project name, `<Name>Theme`, the `<Name>App` graph holder, the Android label and window theme, and the iOS `PRODUCT_NAME`. It does **not** name the iOS framework: that is always `ComposeApp`, which the Swift templates `import`. |
| `--package` | yes | Base Kotlin package (e.g. `com.example.myapp`). All modules derive their packages from this. |
| `--output` | yes | Absolute path where the project directory will be created. |
| `--domains` | yes | Comma-separated domain names in lowercase (e.g. `auth,profile,orders`). Each gets `entities/` + `data/` modules. |
| `--features` | yes | Comma-separated feature names in lowercase (e.g. `auth,home,profile`). Each gets `usecase/` + `ui/` modules with a landing screen. The first one is the start feature. |
| `--synapse-version` | no | Synapse library version. Defaults to the latest release on Maven Central (`com.ribads.synapse:ui-element` `maven-metadata.xml`). If that lookup fails (offline, proxy, TLS), the script exits with an error and writes nothing; re-run with an explicit version. There is no built-in fallback version. |
| `--force` | no | Overwrite existing files. Otherwise aborts if output dir already has a `settings.gradle.kts`. |

### Example

```sh
python3 "${CLAUDE_SKILL_DIR}/scripts/init_project.py" \
    --name Outside \
    --package com.outside \
    --output /Users/ribads/Projects/outside-new \
    --domains auth,activities,profile,messaging \
    --features auth,discover,profile,notifications,activities,create,settings
```

Omit `--synapse-version` to use the latest published release. Pass it explicitly to pin a version or to generate without network access.

## Gradle conventions

The generated project targets **Gradle 9.5.0** with **Kotlin 2.4.10**, **KSP 2.3.6**, **AGP 9.3.1** and **Compose Multiplatform 1.12.0-beta03**, matching the toolchain Synapse is built with.

Key conventions:
- **`androidApp`** is a separate module using `com.android.application` plugin. It contains `MainActivity`, `AndroidManifest.xml`, and Android resources
- **`composeApp`** is a KMP library using `com.android.kotlin.multiplatform.library` (not `com.android.application`)
- **Android config lives inside `kotlin {}` block**: `kotlin { android { namespace = "..."; compileSdk = ...; minSdk = ... } }`
- **`androidResources { enable = true }`** for modules that need Android resources
- **JVM target is 21** (`JvmTarget.JVM_21`, `JavaVersion.VERSION_21`)
- **MVI files go in `ui/` package** (e.g., `app.ui.MainContract`), not `mvi/`
- **Landing screen files use `LandingScreen` prefix** (e.g., `LandingScreenContract`, `LandingScreenViewModel`)
- **`kotlin-inject-runtime-kmp`** is used instead of `kotlin-inject-runtime`
- **Modules with kotlin-inject codegen** (`composeApp`, `core:network`, `core:auth`, each `domain/*/data`, each `features/*/usecase` and `features/*/ui`) declare `add("kspCommonMainMetadata", libs.kotlin.inject.compiler)` and call `configureCommonMainKsp()`, which puts the generated sources on the common compile path. The project has no `build-logic`, so the script writes an identical copy of that function at the bottom of each of those build files. Change it in every copy, or move it into a convention plugin once the project grows one.

## Runtime wiring

What the generated app already does, so you build on it instead of re-adding it:

- **One DI graph per process.** `CoreComposeApp` calls `RootAppBuilder.obtain(appContext)`, which builds the graph on first use and returns the same instance afterwards, so activity recreation (rotation, dark-mode switch, fold) never duplicates `@SingletonScope` objects. `<Name>App.mainViewModel` is a factory, so a new `ViewModelStore` gets a fresh `MainViewModel`.
- **Toasts work from any screen.** `ToastHandler` wraps `RootScreen` inside `<Name>Theme`, so `Toast.current` resolves everywhere below it (see `/synapse:ui-components`).
- **Images.** The singleton Coil `ImageLoader` calls `installSynapseImageComponents()` (from `ui:element`) in shared code, so `Image.LocalIdentifier` (Photos assets on iOS) loads. SVG decoding comes from the `coil-svg` dependency, which registers itself.
- **One `HttpClient`.** `NetworkComponent` provides `CoreClient` as a `@SingletonScope` binding, and `CoreClientImpl` builds its `HttpClient` once at construction. It lives as long as the graph, which is the process. Read tokens per request (a Ktor `Auth` or `defaultRequest` plugin reading `OauthTokenProvider`), not when the client is built.
- **Use case to screen.** Each feature's `Fetch<Name>UseCase.execute()` returns the feature-owned sealed `<Name>Result` (`Success` / `Failure`), never `kotlin.Result`. The landing screen's `loadInitialDataProcessor` calls it on `LoadInitialData` and `LandingScreenMapper` maps it to `OnInitialDataLoaded` / `OnInitialDataFailed`, following `/synapse:data-boundaries` and `/synapse:mvi`.

## When to use

Invoke this skill whenever a user wants to:
- Create a new KMP project that uses Synapse
- Initialize a project with the multi-module DDD architecture
- Bootstrap a new app with IRSE-MVI, kotlin-inject DI, and Compose Multiplatform navigation

Always run the script rather than hand-writing the scaffold; that is the whole point.

## After running the script

The script generates a compiling skeleton. Synapse artifacts resolve from Maven Central (already configured in `settings.gradle.kts`), so no extra credentials are needed for a default build. The user still needs to:

1. **Customize the theme.** Edit `compose-ui/.../<Name>Theme.kt` with brand colours for both the light and dark schemes, fonts and shapes. The app follows the device appearance (`Appearance.System`); pass another `Appearance` to `<Name>Theme` to fix it or to drive it from a user setting. Keep `window_background` in `androidApp/src/main/res/values{,-night}/colors.xml` equal to each scheme's `surface.primary`.
2. **Add fonts.** Place `.ttf`/`.otf` files in `compose-ui/src/commonMain/composeResources/font/`.
3. **Wire real repositories.** The data layer is empty placeholders marked with `// TODO` comments (repository interfaces and implementations, `Fetch<Name>UseCaseImpl`, the `HttpClient` engine setup). Fill them in, then connect each domain's `RepositoryProvidersImpl` to the use-case module that needs it, following the commented-out wiring in `RootAppBuilder.build()`.
4. **Add screens.** Use `/synapse:create-screen` to add more screens to existing features.
5. **Set Xcode `TEAM_ID`.** Open `iosApp/Configuration/Config.xcconfig` and fill in your Apple Developer team identifier; it feeds `DEVELOPMENT_TEAM` for code signing (leave blank for simulator-only builds).
6. **Add app icon images.** Drop 1024×1024 PNGs into `iosApp/iosApp/Assets.xcassets/AppIcon.appiconset/` and update its `Contents.json`.
7. **Open in Android Studio / Fleet.** Sync Gradle, then run on Android. For iOS, open `iosApp/iosApp.xcodeproj` in Xcode.
8. **Add architecture tests.** The script does not scaffold them. Add a `konsist` JVM module enforcing the layer boundaries (feature UI must not import `domain.*` or any `*Repository`; `usecase` must not reach into the data layer; one `execute`/`observe*` per use case). The module graph blocks cross-module leaks on its own, but Konsist catches the rest and keeps them caught. `/synapse:data-boundaries` has the tests to copy.

## Related skills

- `/synapse:create-screen`: Add a new IRSE-MVI screen to an existing feature
- `/synapse:build-screen`: End-to-end screen build workflow
- `/synapse:mvi`: IRSE-MVI APIs (Intent → Interactor → Result → Reducer → State/Effect)
- `/synapse:data-boundaries`: Layer rules, UseCase and error contracts, Konsist enforcement
- `/synapse:navigation`: FeatureLauncher, typed NavKey routes, NavigationCommand
- `/synapse:di-scopes`: SingletonScope, kotlin-inject wiring
- `/synapse:ui-element`: Theme, Colors, Typography, Shape, `installSynapseImageComponents`
- `/synapse:ui-components`: Scaffold, Card, Tray, inputs, buttons, ToastHandler
- `/synapse:component-authoring`: Building app-level composables in `compose-ui/`
