---
name: permissions
description: Use when implementing runtime permission requests for audio, camera, media storage, video call, or location permissions in a KMP project.
user-invocable: true
---

# core:permissions — Runtime Permissions

**Module**: `core:permissions` | **Artifact**: `com.ribads.synapse:core-permissions`
**Package**: `com.ribads.synapse.core.permissions`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-permissions:<version>")
}
```

Depends on `core:context`.

---

## API

```kotlin
interface PermissionsManager {
    suspend fun requestPermission(request: PermissionsRequest): PermissionsResult

    companion object {
        val shared: PermissionsManager
    }
}

expect fun buildPermissionsManager(): PermissionsManager
```

### PermissionsRequest

```kotlin
sealed class PermissionsRequest(open val contextUiDisplayed: Boolean) {
    data class Audio(override val contextUiDisplayed: Boolean) : PermissionsRequest(contextUiDisplayed)
    data class Camera(override val contextUiDisplayed: Boolean) : PermissionsRequest(contextUiDisplayed)
    data class MediaStorage(override val contextUiDisplayed: Boolean) : PermissionsRequest(contextUiDisplayed)
    data class VideoCall(override val contextUiDisplayed: Boolean) : PermissionsRequest(contextUiDisplayed)
    data class Location(override val contextUiDisplayed: Boolean) : PermissionsRequest(contextUiDisplayed)
}
```

`contextUiDisplayed` — set `true` if you've already shown the user a rationale UI before requesting.

### PermissionsResult

```kotlin
sealed class PermissionsResult {
    data object ShouldShowPermissionRationale : PermissionsResult()
    data object Success : PermissionsResult()
    data object Denied : PermissionsResult()
}
```

---

## Usage

```kotlin
val manager = PermissionsManager.shared

val result = manager.requestPermission(PermissionsRequest.Audio(contextUiDisplayed = false))
when (result) {
    PermissionsResult.Success -> startRecording()
    PermissionsResult.Denied -> showDeniedMessage()
    PermissionsResult.ShouldShowPermissionRationale -> showRationale()
}
```

Platform details:
- **Android**: Wraps `ActivityCompat` runtime permissions
- **iOS**: Wraps AVCaptureDevice, PHPhotoLibrary, CLLocationManager, etc.
