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

On Android `requestPermission` needs a live `ComponentActivity` (`AppContextProvider.currentActivity`, see `/synapse:context`) to show the prompt, and **throws `IllegalStateException`** when there is none (for example when called before any `ComponentActivity` has resumed, or after the tracked one is destroyed). iOS needs no activity and never throws.

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

### Android manifest

The module ships **no** `AndroidManifest.xml`, so the app must declare every permission it requests.
Android denies an undeclared permission without showing a prompt, so a missing required entry makes
the request return `Denied` every time.

| Request | Declare in the app manifest |
|---------|-----------------------------|
| `Audio` | `RECORD_AUDIO` |
| `Camera` | `CAMERA` |
| `MediaStorage` | nothing |
| `VideoCall` | `RECORD_AUDIO`, `CAMERA`; optionally `READ_PHONE_STATE` and `BLUETOOTH_SCAN` (API 31+) |
| `Location` | `ACCESS_COARSE_LOCATION`; add `ACCESS_FINE_LOCATION` to let the user grant precise location |

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_PHONE_STATE" />
<uses-permission
    android:name="android.permission.BLUETOOTH_SCAN"
    android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

Declare only the entries for the requests the app makes.

### Per-request mapping

| Request | Android | iOS |
|---------|---------|-----|
| `Audio` | `RECORD_AUDIO` | microphone (`AVAudioSession`) |
| `Camera` | `CAMERA` | camera (`AVCaptureDevice`, video) |
| `MediaStorage` | none (modern photo-picker APIs) | photo library read/write (`PHPhotoLibrary`) |
| `VideoCall` | required `RECORD_AUDIO` + `CAMERA`; optional `READ_PHONE_STATE` + `BLUETOOTH_SCAN` (API 31+ only) | camera + microphone |
| `Location` | required `ACCESS_COARSE_LOCATION`; optional `ACCESS_FINE_LOCATION` (foreground only) | when-in-use (`CLLocationManager`), either accuracy |

A request succeeds once its **required** permissions are granted. Optional permissions are prompted
together with the required ones, but declining them does not fail the request. Once every required
permission is held the request returns `Success` straight away, without prompting for the optional
ones again.

`VideoCall` on API 31+ is the only request with optional call-state and Bluetooth permissions, and the
only one `neverForLocation` concerns. `BLUETOOTH_SCAN` is a runtime permission (the "Nearby devices"
prompt) whether or not the flag is set: `android:usesPermissionFlags="neverForLocation"` only asserts
that the app never derives physical location from scan results, and Android then filters some BLE
beacons out of those results. Below API 31 `VideoCall` requests only mic + camera.

`Location` returns `Success` when the user grants **approximate** location: on Android 12+ the dialog
offers precise or approximate, and either grant succeeds, matching iOS, where when-in-use
authorization succeeds with full or reduced accuracy. An app that needs precise location must check
`ACCESS_FINE_LOCATION` (Android) or `CLLocationManager.accuracyAuthorization` (iOS) itself; once
approximate is held, `Location` returns `Success` without prompting again.

`Location` requests **when-in-use** authorization only (no Always/background scope). The host app
**must** declare `NSLocationWhenInUseUsageDescription` in its `Info.plist`. Without that key iOS
silently suppresses the prompt; the request is bounded and resolves to `Denied` rather than hanging.

Required iOS `Info.plist` usage-description keys per request:

| Request | Info.plist key |
|---------|----------------|
| `Audio`, `VideoCall` | `NSMicrophoneUsageDescription` |
| `Camera`, `VideoCall` | `NSCameraUsageDescription` |
| `MediaStorage` | `NSPhotoLibraryUsageDescription` (read-write access; `NSPhotoLibraryAddUsageDescription` is not used) |
| `Location` | `NSLocationWhenInUseUsageDescription` |
