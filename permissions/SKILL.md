---
name: permissions
description: Use when implementing runtime permission requests for audio, camera, media storage, video call, or location permissions in a KMP project.
user-invocable: true
---

# core:permissions — Runtime Permissions

**Module**: `core:permissions` | **Artifact**: `com.ribads.synapse:core-permissions`
**Packages**: `com.ribads.synapse.core.permissions`, `com.ribads.synapse.core.permissions.model`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-permissions:<version>")
}
```

Depends on `core:context`.

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.permissions.PermissionsManager
import com.ribads.synapse.core.permissions.buildPermissionsManager
import com.ribads.synapse.core.permissions.model.PermissionsRequest
import com.ribads.synapse.core.permissions.model.PermissionsResult
```

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

`contextUiDisplayed`: pass `true` once your UI has explained why the app needs the permission.
Android then goes straight to the system prompt; with `false` it may return
`ShouldShowPermissionRationale` instead of prompting (see below).

### PermissionsResult

```kotlin
sealed class PermissionsResult {
    data object ShouldShowPermissionRationale : PermissionsResult()
    data object Success : PermissionsResult()
    data object Denied : PermissionsResult()
}
```

`ShouldShowPermissionRationale` is **Android-only** and is not a denial: no system prompt was
shown. Android returns it when `contextUiDisplayed` is `false` and the user has declined the
permission before. Show your rationale, then request again with `contextUiDisplayed = true`.
Requesting again with `false` returns `ShouldShowPermissionRationale` every time, so the prompt
never appears. With `contextUiDisplayed = true` the result is only ever `Success` or `Denied`, and
iOS never produces it at all.

`Denied` may be final. iOS prompts once per permission and answers every later request with
`Denied` straight away; Android does the same after the user declines twice (Android 11+) or ticks
"Don't ask again". Tell the user they can enable the permission in system settings rather than
offering only a retry that may not prompt.

---

## Usage

```kotlin
val manager = PermissionsManager.shared

suspend fun requestMicrophone(rationaleShown: Boolean = false) {
    val request = PermissionsRequest.Audio(contextUiDisplayed = rationaleShown)
    when (manager.requestPermission(request)) {
        PermissionsResult.Success -> startRecording()
        PermissionsResult.ShouldShowPermissionRationale -> showRationale()
        PermissionsResult.Denied -> showDeniedMessage()
    }
}
```

`showRationale()` explains why the app needs the microphone, and its continue action calls
`requestMicrophone(rationaleShown = true)`. `showDeniedMessage()` points the user to system
settings. A screen that always explains the permission before asking passes `rationaleShown = true`
on the first call: `ShouldShowPermissionRationale` then never comes back, but the `when` must still
cover it.

Platform details:
- **Android**: Wraps `ActivityCompat` runtime permissions
- **iOS**: Wraps AVCaptureDevice, PHPhotoLibrary, CLLocationManager, etc.

### Per-request mapping

| Request | Android | iOS |
|---------|---------|-----|
| `Audio` | `RECORD_AUDIO` | microphone (`AVAudioSession`) |
| `Camera` | `CAMERA` | camera (`AVCaptureDevice`, video) |
| `MediaStorage` | none (modern photo-picker APIs) | photo library read/write (`PHPhotoLibrary`) |
| `VideoCall` | required `RECORD_AUDIO` + `CAMERA`; optional `READ_PHONE_STATE` + `BLUETOOTH_SCAN` (API 31+) | camera + microphone |
| `Location` | `ACCESS_FINE_LOCATION` + `ACCESS_COARSE_LOCATION` (foreground) | when-in-use (`CLLocationManager`) |

`VideoCall` succeeds once the **required** mic + camera are granted. The optional permissions are
still prompted on Android 12+ but declining them does not fail the request. Declare
`BLUETOOTH_SCAN` with `android:usesPermissionFlags="neverForLocation"` if the call does not derive
location from it; otherwise it triggers a runtime prompt.

`Location` requests **when-in-use** authorization only (no Always/background scope). The host app
**must** declare `NSLocationWhenInUseUsageDescription` in its `Info.plist`. Without that key iOS
silently suppresses the prompt; the request is bounded and resolves to `Denied` rather than hanging.

Required iOS `Info.plist` usage-description keys per request:

| Request | Info.plist key |
|---------|----------------|
| `Audio`, `VideoCall` | `NSMicrophoneUsageDescription` |
| `Camera`, `VideoCall` | `NSCameraUsageDescription` |
| `MediaStorage` | `NSPhotoLibraryUsageDescription` / `NSPhotoLibraryAddUsageDescription` |
| `Location` | `NSLocationWhenInUseUsageDescription` |
