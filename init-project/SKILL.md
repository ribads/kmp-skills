---
name: init-project
description: Use when initializing a new KMP project with Synapse libraries. Generates the full multi-module DDD architecture (core, domain, features, androidApp, composeApp, compose-ui, iosApp) with IRSE-MVI wiring, kotlin-inject DI, and Compose Multiplatform navigation — all from templates.
user-invocable: true
---

# init-project — Synapse KMP Project Scaffold

Generates a complete Kotlin Multiplatform project with the canonical Synapse multi-module DDD architecture. Uses heavy templating — Claude runs a Python script, not freehand code generation.

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
│       └── res/values/
│           ├── strings.xml
│           └── themes.xml
│
├── composeApp/                             # KMP library — DI wiring + shared app logic
│   ├── build.gradle.kts                   # androidMultiplatformLibrary plugin
│   └── src/
│       ├── commonMain/kotlin/<pkg>/app/
│       │   ├── AppContext.kt              # expect class
│       │   ├── CoreComposeApp.kt          # Coil, WithImagePainter, Theme, RootScreen
│       │   ├── RootScreen.kt             # Scaffold + NavContainer
│       │   ├── di/
│       │   │   ├── RootAppBuilder.kt      # Assembles entire DI graph
│       │   │   ├── ComposeAppComponent.kt # Merges all feature modules
│       │   │   ├── NetworkComponent.kt    # CoreClient provider
│       │   │   └── AppConfigurationProviderFactory.kt
│       │   └── ui/
│       │       ├── MainContract.kt        # Main screen IRSE-MVI
���       │       ├── MainInteractor.kt
│       │       ├── MainReducer.kt
│       │       ├── MainMapper.kt
│       │       ├── MainViewModel.kt
│       │       ├── di/MainUiComponent.kt
│       │       └── navigation/
│       │           ├── MainNavigatorHost.kt
│       │           └── MainNavigationDispatcher.kt
│       ├── androidMain/kotlin/<pkg>/app/
│       │   └── AppContext.android.kt      # actual (Android Context)
│       └── iosMain/kotlin/<pkg>/app/
│           ├── AppContext.ios.kt          # actual (stub)
│           └── MainViewController.kt
│
├── compose-ui/                            # Theme layer
│   ├── build.gradle.kts
│   └── src/commonMain/kotlin/<pkg>/compose/ui/theme/
│       └── <Name>Theme.kt              # WithTheme wrapper (colors, typography, shapes)
│
├── core/
│   ├── network/                           # HTTP client (Ktor)
│   │   ├── build.gradle.kts
│   │   └── src/
│   │       ├── commonMain/kotlin/<pkg>/core/network/
│   │       │   ├── CoreClient.kt
│   │       │   ├── CoreClientImpl.kt
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
│   ├── entities/                          # Interfaces + sealed results
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
│   │       ├── Fetch<Name>UseCase.kt
│   │       └── di/
���   │           ├── <Name>UseCaseModule.kt
│   │           └── <Name>UseCaseProvider.kt
│   └── ui/                                # IRSE-MVI screens + navigation (androidMultiplatformLibrary)
│       ├── build.gradle.kts
│       └── src/commonMain/kotlin/<pkg>/feature/<name>/ui/
│           ├── launcher/<Name>FeatureLauncher.kt
│           ├── navigation/
│           │   ├── <Name>NavigationHost.kt
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

`scripts/init_project.py` — Python 3, stdlib only. Static template files live in `scripts/templates/<area>/` and are loaded via `load_template()`. iOS templates are in `scripts/templates/ios/`.

```
python3 .claude/skills/init-project/scripts/init_project.py \
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
| `--name` | yes | PascalCase project name (e.g. `MyApp`). Used for root project name, framework base name, theme name. |
| `--package` | yes | Base Kotlin package (e.g. `com.example.myapp`). All modules derive their packages from this. |
| `--output` | yes | Absolute path where the project directory will be created. |
| `--domains` | yes | Comma-separated domain names in lowercase (e.g. `auth,profile,orders`). Each gets `entities/` + `data/` modules. |
| `--features` | yes | Comma-separated feature names in lowercase (e.g. `auth,home,profile`). Each gets `usecase/` + `ui/` modules with a landing screen. |
| `--synapse-version` | no | Synapse library version. Defaults to the latest release resolved from Maven Central (`com.ribads.synapse:ui-element` `maven-metadata.xml`); falls back to a pinned version if the lookup fails. |
| `--force` | no | Overwrite existing files. Otherwise aborts if output dir already has a `settings.gradle.kts`. |

### Example

```sh
python3 .claude/skills/init-project/scripts/init_project.py \
    --name Outside \
    --package com.outside \
    --output /Users/ribads/Projects/outside-new \
    --domains auth,activities,profile,messaging \
    --features auth,discover,profile,notifications,activities,create,settings
```

Omit `--synapse-version` to use the latest published release. Pass it explicitly only when pinning to a specific version.

## Gradle conventions

The generated project targets **Gradle 9.4.1** with **Kotlin 2.3.21** and **KSP 2.3.4**.

Key conventions:
- **`androidApp`** is a separate module using `com.android.application` plugin — it contains `MainActivity`, `AndroidManifest.xml`, and Android resources
- **`composeApp`** is a KMP library using `com.android.kotlin.multiplatform.library` (not `com.android.application`)
- **Android config lives inside `kotlin {}` block**: `kotlin { android { namespace = "..."; compileSdk = ...; minSdk = ... } }`
- **`androidResources { enable = true }`** for modules that need Android resources
- **JVM target is 21** (`JvmTarget.JVM_21`, `JavaVersion.VERSION_21`)
- **MVI files go in `ui/` package** (e.g., `app.ui.MainContract`), not `mvi/`
- **Landing screen files use `LandingScreen` prefix** (e.g., `LandingScreenContract`, `LandingScreenViewModel`)
- **`kotlin-inject-runtime-kmp`** is used instead of `kotlin-inject-runtime`
- **Modules with kotlin-inject codegen** declare `add("kspCommonMainMetadata", libs.kotlin.inject.compiler)` and call the shared `configureCommonMainKsp()` helper, which puts the generated sources on the common compile path

## When to use

Invoke this skill whenever a user wants to:
- Create a new KMP project that uses Synapse
- Initialize a project with the multi-module DDD architecture
- Bootstrap a new app with IRSE-MVI, kotlin-inject DI, and Compose Multiplatform navigation

Always run the script rather than hand-writing the scaffold — that's the whole point.

## After running the script

The script generates a compiling skeleton. Synapse artifacts resolve from Maven Central (already configured in `settings.gradle.kts`), so no extra credentials are needed for a default build. The user still needs to:

1. **Customize the theme** — edit `compose-ui/.../<Name>Theme.kt` with brand colors, fonts, shapes.
2. **Add fonts** — place `.ttf`/`.otf` files in `compose-ui/src/commonMain/composeResources/font/`.
3. **Wire real repositories** — replace `TODO()` stubs in the data layer, then connect each domain's `RepositoryProvidersImpl` to the use-case module that needs it (see the `// TODO` in `RootAppBuilder.build()`).
4. **Add screens** — use `/create-screen` to add more screens to existing features.
5. **Set Xcode `TEAM_ID`** — open `iosApp/Configuration/Config.xcconfig` and fill in your Apple Developer team identifier; it feeds `DEVELOPMENT_TEAM` for code signing (leave blank for simulator-only builds).
6. **Add app icon images** — drop 1024×1024 PNGs into `iosApp/iosApp/Assets.xcassets/AppIcon.appiconset/` and update its `Contents.json`.
7. **Open in Android Studio / Fleet** — sync Gradle, then run on Android. For iOS, open `iosApp/iosApp.xcodeproj` in Xcode.

## Related skills

- `/create-screen` — Add a new IRSE-MVI screen to an existing feature
- `/mvi` — IRSE-MVI APIs (Intent → Interactor → Result → Reducer → State/Effect)
- `/navigation` — NavigatorHost, FeatureLauncher, NavigationCommand
- `/di-scopes` — SingletonScope, kotlin-inject wiring
- `/ui-element` — Theme, Colors, Typography, Shape
- `/ui-components` — Scaffold, Card, Tray, inputs, buttons
