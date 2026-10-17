---
name: context
description: Use when you need Android Context or Activity access in shared KMP code. Dependency of core:capture, core:connectivity, core:file, core:moonshine, core:paystack:ui, core:permissions, core:playback, core:record, core:share and core:sharedpref.
user-invocable: true
---

# core:context — Android Context Provider

**Module**: `core:context` | **Artifact**: `com.ribads.synapse:core-context`
**Packages**: `com.ribads.synapse.core.context`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-context:<version>")
}
```

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.context.AppContextProvider
```

---

## API

```kotlin
expect object AppContextProvider {
    val applicationContext: Any?   // Android: android.content.Context, iOS: null
    val currentActivity: Any?     // Android: androidx.activity.ComponentActivity or null, iOS: null
}
```

Auto-initialized on Android via a `ContentProvider` registered in the manifest — no manual setup needed.

On Android, `currentActivity` is the most recently resumed `ComponentActivity` that is still alive. It stays set while that activity is paused or stopped (for example behind a permission prompt, or while the camera app is open), so a launch chained after a prompt's result still finds it. It is cleared when the activity is destroyed.

## Usage

```kotlin
// In platform-specific code (androidMain)
val context = AppContextProvider.applicationContext as Context
val activity = AppContextProvider.currentActivity as? ComponentActivity
```

Every Synapse module that needs a `Context` or the current activity depends on it, so you rarely need to depend on it directly:

| Module | Artifact | Source set | Exposed to your code |
|--------|----------|------------|----------------------|
| `core:capture` | `core-capture` | `androidMain`, `iosMain` | no (`implementation`) |
| `core:connectivity` | `core-connectivity` | `androidMain` | no (`implementation`) |
| `core:file` | `core-file` | `commonMain` | yes (`api`) |
| `core:moonshine` | `core-moonshine` | `androidMain` | no (`implementation`) |
| `core:paystack:ui` | `paystack-ui` | `androidMain` | no (`implementation`) |
| `core:permissions` | `core-permissions` | `commonMain` | yes (`api`) |
| `core:playback` | `core-playback` | `androidMain` | no (`implementation`) |
| `core:record` | `core-record` | `androidMain` | no (`implementation`) |
| `core:share` | `core-share` | `androidMain` | no (`implementation`) |
| `core:sharedpref` | `core-sharedpref` | `androidMain` | Android source sets only (`api`) |

The `ContentProvider` initializer runs whenever any of them is in the app. To reference `AppContextProvider` from your own code without one of the `api` modules, declare `core-context` yourself.
