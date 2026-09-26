---
name: context
description: Use when you need Android Context or Activity access in shared KMP code. Required dependency for core:file, core:permissions, core:record, core:sharedpref.
user-invocable: true
---

# core:context — Android Context Provider

**Module**: `core:context` | **Artifact**: `com.ribads.synapse:core-context`
**Package**: `com.ribads.synapse.core.context`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-context:<version>")
}
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

This module is a transitive dependency of `core:file`, `core:permissions`, `core:record`, and `core:sharedpref`. You rarely need to depend on it directly.
