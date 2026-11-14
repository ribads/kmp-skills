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

Every release is on Synapse's Maven repository, `https://maven.ribads.com`; Maven Central has major releases only. Declare it in `settings.gradle.kts` as an `exclusiveContent` repository filtered to `com.ribads.synapse`, and read the latest version from `https://maven.ribads.com/com/ribads/synapse/<artifact>/maven-metadata.xml`.

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.context.AppContextProvider
import com.ribads.synapse.core.context.launchForResult   // androidMain only
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

### Results that survive recreation (Android)

```kotlin
// androidMain
suspend fun <I, O> ComponentActivity.launchForResult(contract: ActivityResultContract<I, O>, input: I): O
```

Launches `input` through `contract` and returns the result, even when the system recreates the activity (rotation, a
window resize, a font or locale change) while the screen it opened is showing: the activity recreated in its place takes
the request over under the same key and receives the result the system kept for it. A request registered with a random
key on one activity's `activityResultRegistry` instead waits forever once that activity is recreated. If the activity
finishes for good first, the result is the contract's own for a cancelled request (`parseResult(RESULT_CANCELED, null)`).
Cancelling the caller unregisters the request. `core:permissions` and `core:file` launch through it.

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
