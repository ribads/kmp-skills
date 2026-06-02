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

`ShouldShowPermissionRationale` is **Android-only**. It is returned when the OS reports that a
rationale should be shown before re-requesting (and `contextUiDisplayed` is `false`). iOS never
produces it: the system handles rationale via its own pre-prompt and only ever returns `Success`
or `Denied`. Shared code must branch on all three results, but should treat
`ShouldShowPermissionRationale` as a softer, retry-able form of denial: on iOS the equivalent denial
surfaces as `Denied`.

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
