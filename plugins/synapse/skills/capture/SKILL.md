---
name: capture
description: Use when implementing camera capture, photo capture, video recording, in-app camera preview, or building a custom capture UI in a KMP project.
user-invocable: true
---

# core:capture + ui:capture — Camera Capture

**Modules**: `core:capture` (engine) + `ui:capture` (Compose components)
**Artifacts**: `com.ribads.synapse:core-capture`, `com.ribads.synapse:ui-capture`
**Packages**: `com.ribads.synapse.core.capture`, `com.ribads.synapse.core.capture.model`, `com.ribads.synapse.ui.capture`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-capture:<version>")
    implementation("com.ribads.synapse:ui-capture:<version>")  // optional, for Compose UI
}
```

`core:capture` depends on `core:context`. `ui:capture` depends on `core:capture` and `ui:element`.

The engine handles its own audio pipeline — no dependency on `core:record`. Audio is captured directly via CameraX's `Recorder` on Android and `AVCaptureSession` on iOS.

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.capture.CaptureController
import com.ribads.synapse.core.capture.CapturePreviewSurface
import com.ribads.synapse.core.capture.createCaptureController
import com.ribads.synapse.core.capture.requiredPermissions
import com.ribads.synapse.core.capture.model.CameraFacing
import com.ribads.synapse.core.capture.model.CaptureCapabilities
import com.ribads.synapse.core.capture.model.CaptureConfig
import com.ribads.synapse.core.capture.model.CaptureError
import com.ribads.synapse.core.capture.model.CaptureEvent
import com.ribads.synapse.core.capture.model.CaptureLifecycle
import com.ribads.synapse.core.capture.model.CaptureMode
import com.ribads.synapse.core.capture.model.CaptureOutcome
import com.ribads.synapse.core.capture.model.CapturePermission
import com.ribads.synapse.core.capture.model.CaptureSession
import com.ribads.synapse.core.capture.model.FlashMode
import com.ribads.synapse.core.capture.model.NormalizedPoint
import com.ribads.synapse.core.capture.model.PhotoOutcome
import com.ribads.synapse.core.capture.model.PhotoQuality
import com.ribads.synapse.core.capture.model.RecordingPhase
import com.ribads.synapse.core.capture.model.RecordingProgress
import com.ribads.synapse.core.capture.model.VideoOutcome
import com.ribads.synapse.core.capture.model.VideoQuality
import com.ribads.synapse.ui.capture.CaptureFlashButton
import com.ribads.synapse.ui.capture.CaptureFlipButton
import com.ribads.synapse.ui.capture.CaptureModeSelector
import com.ribads.synapse.ui.capture.CapturePreview
import com.ribads.synapse.ui.capture.CaptureScreen
import com.ribads.synapse.ui.capture.CaptureShutter
import com.ribads.synapse.ui.capture.CaptureShutterScope
import com.ribads.synapse.ui.capture.DefaultShutter
import com.ribads.synapse.ui.capture.captureTapToFocus
```

---

## Architecture in one paragraph

`CaptureController` is a stateful actor. Observable state lives in `session: StateFlow<CaptureSession>` — atomic across mode, facing, flash, zoom, recording, and **capabilities** (what the engine can do right now). One-shot signals that don't fit state-flow semantics — async focus completion, OS-initiated recording stops, engine-initiated auto-stops — flow through `events: Flow<CaptureEvent>`. Synchronous outcomes are returned from the suspending command itself via `Result<T>`. UI is *capability-driven*: chrome subscribes to `session.capabilities` and hides controls whose actions would fail, so the surface stays honest without consumers wiring per-action error handling.

---

## Entry Points

```kotlin
// Construct a controller. MUST be called on the main thread.
expect fun createCaptureController(config: CaptureConfig = CaptureConfig()): CaptureController

// Permissions required by a given config — request via your permission stack before start().
fun requiredPermissions(config: CaptureConfig): List<CapturePermission>
```

---

## CaptureController

```kotlin
interface CaptureController {
    val session: StateFlow<CaptureSession>
    val events: Flow<CaptureEvent>
    val previewSurface: CapturePreviewSurface

    suspend fun start(): Result<Unit>      // from Idle; again only to retry from Error
    suspend fun release()                   // suspends through encoder flush + photo settle

    suspend fun setMode(mode: CaptureMode): Result<Unit>
    suspend fun setFacing(facing: CameraFacing): Result<Unit>
    suspend fun setFlash(mode: FlashMode): Result<Unit>
    suspend fun setZoom(ratio: Float): Result<Float>             // returns clamped value
    suspend fun focus(point: NormalizedPoint): Result<Unit>      // outcome via events

    suspend fun capturePhoto(destination: String? = null): Result<PhotoOutcome>
    suspend fun startRecording(destination: String? = null): Result<Unit>
    suspend fun stopRecording(): Result<VideoOutcome>
}
```

### Contracts that matter

- **Start gating**: `start()` is valid from `Idle` (initial) and from `Error` (retry after a failed start or a runtime fault). It is rejected with `CaptureError.InvalidState` from `Initializing` / `Ready` (already in progress / already started) and from `Released` (terminally torn down: build a new controller via `createCaptureController`). Any `start()` failure moves `lifecycle` to `Error(cause)`.
- **Permission check**: `start()` checks `requiredPermissions(config)` without prompting, camera first, then microphone when `audioEnabled`. The first missing one is returned as `Result.failure(CaptureError.PermissionDenied(permission))` (lifecycle `Error`); request it and call `start()` again. On iOS a permission the user has not been asked for yet (`notDetermined`) counts as missing, so request permissions before the first `start()`.
- **While `Error`**: device commands (`setFacing`, `setFlash`, `setZoom`, `focus`, `capturePhoto`, `startRecording`) return `InvalidState`; `setMode` only records the mode; `release()` works from any state.
- **`release()`** suspends until in-flight recording flushes and in-flight photo capture completes. Safe to call from any state, including `Released`.
- **`setZoom`** returns the actually-applied (clamped) ratio so pinch gestures can match resistance to engine state without an extra read of `session`.
- **`focus`** suspends through the camera's focus + metering pass. `Result.success(Unit)` means the request was issued; whether the device achieved lock is delivered via `events` as `CaptureEvent.FocusCompleted(locked)`.
- **`setMode` / `setFacing`** are rejected during active recording (`InvalidState`). Consult `session.capabilities.canChangeMode` / `canChangeFacing` to render disabled state.
- **`setFlash`** accepts `FlashMode.Off` unconditionally. On both platforms, any other mode on a camera without a flash unit is rejected with `CaptureError.Unsupported` and `session.flash` is left unchanged (Android checks `CameraInfo.hasFlashUnit()`, iOS checks the mode against `session.capabilities.supportedFlashModes`). Cameras with no flash unit expose only `FlashMode.Off` in `supportedFlashModes`.
- **`setMode`** on iOS reconfigures a running session for the new mode's quality preset (`photoQuality` in photo mode, `videoQuality` in video mode), which briefly interrupts the preview. Android binds photo and video together, so a mode switch changes nothing on the camera.
- **Concurrent commands** serialize on the controller's internal mutex. State updates are atomic across every dimension of `CaptureSession`.
- **`stopRecording` returns `InvalidState`** if no recording is active — including when an OS interrupt or auto-stop already finalized the recording (the outcome of those exits is delivered via `events`).
- **Out-of-band recording ends**: OS interrupts → `CaptureEvent.RecordingInterrupted(outcome?, reason)`. Duration / file-size limit → `CaptureEvent.RecordingAutoStopped(outcome)`. `outcome` carries whatever the encoder finalized.

---

## CapturePreviewSurface

```kotlin
expect class CapturePreviewSurface
```

Opaque platform handle for the live camera preview. Owned by the `CaptureController`, exposed as `controller.previewSurface`, embedded by `ui:capture` (do not inspect from common code).

---

## Models

### CaptureConfig

```kotlin
data class CaptureConfig(
    val initialMode: CaptureMode = CaptureMode.Photo,
    val initialFacing: CameraFacing = CameraFacing.Back,
    val initialFlash: FlashMode = FlashMode.Off,
    val photoQuality: PhotoQuality = PhotoQuality.High,
    val videoQuality: VideoQuality = VideoQuality.FullHD,
    val audioEnabled: Boolean = true,
    val maxVideoDuration: Duration? = null,
    val outputDirectory: String? = null,
)
```

Quality settings, `audioEnabled`, and `outputDirectory` are fixed for the controller's lifetime. Mode, facing, flash, and zoom can be changed at runtime.

`outputDirectory` controls where the engine writes captures when no explicit destination is passed. `null` (the default) uses a `capture` folder inside the app's cache directory on Android (`<cacheDir>/capture`) and inside the temporary directory on iOS (`NSTemporaryDirectory()` + `capture`). The engine creates the directory if it doesn't exist and generates a fresh `IMG_<timestamp>.jpg` / `VID_<timestamp>.mp4` filename per capture.

`maxVideoDuration` triggers `CaptureEvent.RecordingAutoStopped` on hit.

### CaptureMode

```kotlin
enum class CaptureMode { Photo, Video }
```

### CameraFacing

```kotlin
enum class CameraFacing { Front, Back }
```

### FlashMode

```kotlin
enum class FlashMode {
    Off,
    On,
    Auto,
    Torch,  // continuous illumination — used during video recording
}
```

### PhotoQuality / VideoQuality

```kotlin
enum class PhotoQuality { Low, Medium, High, Max }

enum class VideoQuality {
    SD,        // ~480p
    HD,        // ~720p
    FullHD,    // ~1080p
    UltraHD,   // ~2160p / 4K
}
```

Mapped per platform to the closest available configuration. `CaptureSession` does not report the negotiated resolution.

| | Android | iOS |
|---|---|---|
| `PhotoQuality` | CameraX `ImageCapture` resolution target: Low 640x480, Medium 1280x960, High 2560x1440, Max 4096x3072 (closest lower, then higher, size) | Session preset in photo mode: Low `640x480`, Medium `1280x720`, High `High`, Max `Photo` |
| `VideoQuality` | CameraX `QualitySelector` (SD, HD, FHD, UHD) with lower-then-higher fallback | Session preset in video mode: SD `640x480`, HD `1280x720`, FullHD `1920x1080`, UltraHD `3840x2160` |

On iOS the preset for the current mode is applied at `start()` and on every `setMode`, and falls back to the `High` preset when the camera or the attached outputs refuse it (for example 4K on a front camera).

### CaptureSession

```kotlin
data class CaptureSession(
    val lifecycle: CaptureLifecycle = CaptureLifecycle.Idle,
    val mode: CaptureMode = CaptureMode.Photo,
    val facing: CameraFacing = CameraFacing.Back,
    val flash: FlashMode = FlashMode.Off,
    val zoom: Float = 1f,                                          // current zoom ratio
    val recording: RecordingProgress? = null,
    val capabilities: CaptureCapabilities = CaptureCapabilities(),
)
```

### CaptureCapabilities

```kotlin
data class CaptureCapabilities(
    val supportedFacings: Set<CameraFacing> = emptySet(),
    val supportedFlashModes: Set<FlashMode> = emptySet(),   // all modes with a flash unit, {Off} without, empty before start
    val zoomRange: ClosedFloatingPointRange<Float> = 1f..1f, // iOS caps the upper bound at 10x
    val supportsTapToFocus: Boolean = false,
    val canChangeMode: Boolean = true,    // false during recording
    val canChangeFacing: Boolean = true,  // false during recording
)
```

Recomputed by the engine on `start()` completion, every `setFacing` (flash availability swings with the active lens), recording start/stop transitions, and platform-reported zoom-range updates.

### CaptureLifecycle

```kotlin
sealed class CaptureLifecycle {
    data object Idle : CaptureLifecycle()
    data object Initializing : CaptureLifecycle()
    data object Ready : CaptureLifecycle()
    data class Error(val cause: CaptureError) : CaptureLifecycle()
    data object Released : CaptureLifecycle()
}
```

Transition graph: `Idle -> Initializing -> Ready -> Released`. `Error` is reachable from any non-terminal state (a failed `start()`, including `PermissionDenied`, or a runtime session fault). It is recoverable: `start()` may be re-invoked from `Error` to retry initialization, while device commands return `InvalidState` until it succeeds. (`release` then rebuild is also fine.)

### RecordingProgress

```kotlin
data class RecordingProgress(
    val phase: RecordingPhase,
    val elapsedMs: Long,
    val filePath: String,
)

enum class RecordingPhase {
    Active,      // frames being captured + encoded
    Finalizing,  // stop() called; flushing + finalizing the container
}
```

### NormalizedPoint

```kotlin
data class NormalizedPoint(val x: Float, val y: Float) {
    init { require(x in 0f..1f && y in 0f..1f) }
}
```

Preview-relative point, `(0, 0)` at top-left. Construction validates the range — `IllegalArgumentException` for out-of-bounds — so engine code never has to recheck.

### CaptureOutcome

Sealed parent of every result the controller can produce.

```kotlin
sealed interface CaptureOutcome {
    val filePath: String
}
```

### PhotoOutcome

```kotlin
data class PhotoOutcome(
    override val filePath: String,
    val width: Int,
    val height: Int,
    val rotationDegrees: Int,
) : CaptureOutcome
```

`rotationDegrees`: clockwise rotation that should be applied when rendering. CameraX writes rotation in EXIF; AVFoundation writes upright pixels with `rotation = 0`.

### VideoOutcome

```kotlin
data class VideoOutcome(
    override val filePath: String,
    val durationMs: Long,
    val sizeBytes: Long,
) : CaptureOutcome
```

### CaptureEvent

```kotlin
sealed interface CaptureEvent {
    data class FocusCompleted(val locked: Boolean) : CaptureEvent
    data class RecordingInterrupted(
        val outcome: VideoOutcome?,
        val reason: CaptureError,
    ) : CaptureEvent
    data class RecordingAutoStopped(val outcome: VideoOutcome) : CaptureEvent
}
```

Hot stream with a small buffer. Late subscribers see future emissions only. Use for one-shot signals that don't fit `StateFlow` semantics — state lives on `session`.

### CaptureError

```kotlin
sealed class CaptureError(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class PermissionDenied(val permission: CapturePermission) : CaptureError(...)
    class CameraUnavailable(cause: Throwable? = null) : CaptureError(...)
    class NoCamera(val facing: CameraFacing) : CaptureError(...)
    class IoError(cause: Throwable) : CaptureError(...)
    class Interrupted(reason: String? = null) : CaptureError(...)
    class InvalidState(message: String) : CaptureError(...)
    class Unsupported(message: String) : CaptureError(...)
}
```

Returned inside `Result.failure` from suspending operations and surfaced via `CaptureLifecycle.Error` for start failures and runtime session faults.

### CapturePermission

```kotlin
enum class CapturePermission { Camera, Microphone }
```

The engine does **not** request permissions. Use `requiredPermissions(config)` to compute the list, then request via `core:permissions` (or your preferred stack) before invoking `start()`.

---

## ui:capture — Compose components

`ui:capture` ships flat, composable building blocks plus one opinionated assembly (`CaptureScreen`). There are no slots: customize by composing the parts yourself rather than overriding hooks.

Every control subscribes to `session.capabilities` and **renders nothing** when its action is unavailable: recording hides the mode and flip controls, a single-facing device hides the flip control, and a camera without a flash unit hides the flash control. Hiding controls makes the failing action impossible to invoke, which is the cleanest error handling there is.

### CapturePreview

```kotlin
@Composable
fun CapturePreview(controller: CaptureController, modifier: Modifier = Modifier)
```

Renders the live preview only. Tap-to-focus is opt-in via the modifier — chain it where you want the gesture:

```kotlin
CapturePreview(controller, Modifier.fillMaxSize().captureTapToFocus(controller))
```

### Modifier.captureTapToFocus

```kotlin
fun Modifier.captureTapToFocus(controller: CaptureController): Modifier
```

Opt-in tap-to-focus. Applies to any element sized to the preview; the gesture forwards normalized coordinates to `controller.focus()`. Out-of-bounds taps are clamped. Focus completion is delivered via `CaptureEvent.FocusCompleted` — the modifier installs the gesture but does not subscribe to the event stream; surface the indicator from the caller.

### CaptureShutter

```kotlin
@Composable
fun CaptureShutter(
    controller: CaptureController,
    onCaptured: (Result<CaptureOutcome>) -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable CaptureShutterScope.() -> Unit = { DefaultShutter() },
)
```

Photo/video state-machine shutter. Tapping the rendered content does the right thing for the current session:

- Photo mode → `capturePhoto()`. Resolves `onCaptured` with the photo outcome.
- Video mode, no recording → `startRecording()`. **Does not fire `onCaptured`** (no outcome yet — observe `session.recording`).
- Video mode, recording → `stopRecording()`. Resolves `onCaptured` with the video outcome.

Failures resolve `onCaptured` with `Result.failure`. Out-of-band exits (OS interrupts, duration auto-stops) come through `controller.events`, not `onCaptured`.

### CaptureShutterScope

```kotlin
@Stable
interface CaptureShutterScope {
    val session: CaptureSession
    fun trigger()
}
```

Receiver scope for the `content` slot of `CaptureShutter`. Reads inside the composable register snapshot subscriptions on `session`; `trigger()` fires the appropriate engine call.

### DefaultShutter

```kotlin
@Composable
fun CaptureShutterScope.DefaultShutter(modifier: Modifier = Modifier)
```

Opinionated default visual. Extension on `CaptureShutterScope` so it's callable as `DefaultShutter()` from inside a `content = { DefaultShutter() }` slot.

- Photo: solid white circle.
- Video idle: red circle.
- Video recording: red rounded square.

### CaptureFlashButton

```kotlin
@Composable
fun CaptureFlashButton(controller: CaptureController, modifier: Modifier = Modifier)
```

Flash-mode toggle. Cycles through the natural sequence for the **currently active** capture mode: Off → Auto → On → Off for photo, Off → Torch → Off for video. **Renders nothing** when the active camera has no flash unit, that is when `session.capabilities.supportedFlashModes` offers nothing besides `FlashMode.Off` (including before `start()` completes). The signal is `CameraInfo.hasFlashUnit()` on Android and `AVCaptureDevice.hasTorch` on iOS, so emulators and simulators without a flash hide the button.

### CaptureFlipButton

```kotlin
@Composable
fun CaptureFlipButton(controller: CaptureController, modifier: Modifier = Modifier)
```

Camera flip. Hidden when the device exposes fewer than two facings or while a recording is active.

### CaptureModeSelector

```kotlin
@Composable
fun CaptureModeSelector(controller: CaptureController, modifier: Modifier = Modifier)
```

Photo / Video toggle. Hidden while a recording is active.

### CaptureScreen

```kotlin
@Composable
fun CaptureScreen(
    controller: CaptureController,
    modifier: Modifier = Modifier,
    onCaptured: (CaptureOutcome) -> Unit = {},
    onError: (CaptureError) -> Unit = {},
)
```

Opinionated full-screen capture surface. No slots — it composes the building blocks above. Reach for it when you want the standard chrome out of the box.

- `onCaptured` fires for photo captures, user-initiated stop-recording, and engine-initiated auto-stops (duration / file-size).
- `onError` fires for capture failures and OS-initiated recording interruptions.
- Renders in a dark `WithAppearance` region, so it needs a Synapse theme (`WithAppTheme` or `WithTheme`) above it. It does not touch the system bars, because only the host knows whether it sits behind them. A host that shows it edge to edge keeps the bar icons light with a claim (see `/synapse:ui-element`):

  ```kotlin
  WithAppearance(Appearance.Dark) {
      ThemedSystemBars()
      CaptureScreen(controller = controller, modifier = Modifier.fillMaxSize())
  }
  ```

When you need a custom layout, a recording-timer overlay, or branded chrome — drop `CaptureScreen` and assemble from the parts yourself (see [Headless](#headless--custom-chrome-no-capturescreen) below).

---

## Permissions

Add these to the consuming app's manifest / Info.plist.

**Android (`AndroidManifest.xml`)**:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-feature android:name="android.hardware.camera" android:required="false" />
```

**iOS (`Info.plist`)**:

```xml
<key>NSCameraUsageDescription</key>
<string>Used to capture photos and videos.</string>
<key>NSMicrophoneUsageDescription</key>
<string>Used to record audio with video.</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Used by camera capture to read media metadata during photo capture.</string>
<key>NSPhotoLibraryAddUsageDescription</key>
<string>Used to save captured photos and videos.</string>
```

The last two keys are required even though `core:capture` writes only to app-private storage — iOS frameworks along the `AVCapturePhotoOutput` path probe photo-library metadata internally, and the privacy check crashes the app at runtime if the strings are absent.

The engine checks, but never requests, the runtime permissions in `start()` and returns the first missing one as `Result.failure(CaptureError.PermissionDenied(permission))`. On iOS a permission that has not been requested yet counts as missing, so request permissions before calling `start()`.

---

## Usage

### Basic photo + video screen

```kotlin
@Composable
fun MyCaptureScreen() {
    val controller = remember { createCaptureController(CaptureConfig()) }
    val scope = rememberCoroutineScope()

    DisposableEffect(controller) {
        scope.launch { controller.start() }
        onDispose { scope.launch { controller.release() } }
    }

    CaptureScreen(
        controller = controller,
        onCaptured = { outcome ->
            when (outcome) {
                is PhotoOutcome -> /* outcome.filePath, .width, .height, .rotationDegrees */
                is VideoOutcome -> /* outcome.filePath, .durationMs, .sizeBytes */
            }
        },
        onError = { error -> /* surface error */ },
    )
}
```

### Custom output directory

```kotlin
val controller = remember {
    createCaptureController(
        CaptureConfig(outputDirectory = "${myAppFilesDir()}/captures"),
    )
}
```

### Custom destination per call

```kotlin
val outcome = controller.capturePhoto(destination = "${dir()}/${entity.id}.jpg")
```

### Custom shutter (CaptureShutter slot)

```kotlin
CaptureShutter(
    controller = controller,
    onCaptured = { /* same Result<CaptureOutcome> shape */ },
) {
    // 'this' is CaptureShutterScope — access session, call trigger().
    MyBrandedShutter(
        isRecording = session.recording != null,
        torchActive = session.flash == FlashMode.Torch,
        onTap = ::trigger,
    )
}
```

### Recording-timer overlay (no CaptureScreen)

```kotlin
val session by controller.session.collectAsState()

Box(Modifier.fillMaxSize()) {
    CapturePreview(controller, Modifier.fillMaxSize().captureTapToFocus(controller))
    CaptureFlashButton(controller, Modifier.align(Alignment.TopEnd).padding(16.dp))

    session.recording?.let { rec ->
        Text(
            text = formatDuration(rec.elapsedMs),
            modifier = Modifier.align(Alignment.TopCenter).padding(top = 24.dp),
            color = Color.Red,
        )
    }

    Column(
        Modifier.align(Alignment.BottomCenter).padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CaptureModeSelector(controller)
        Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
            Box(Modifier.size(48.dp)) { CaptureFlipButton(controller) }
            CaptureShutter(controller, onCaptured = { /* ... */ })
            Spacer(Modifier.size(48.dp))
        }
    }
}
```

### Listening for engine events

```kotlin
LaunchedEffect(controller) {
    controller.events.collect { event ->
        when (event) {
            is CaptureEvent.FocusCompleted -> if (event.locked) showFocusRing()
            is CaptureEvent.RecordingInterrupted -> {
                toast("Recording interrupted: ${event.reason.message}")
                event.outcome?.let { saveOrDiscard(it) }
            }
            is CaptureEvent.RecordingAutoStopped -> handleOutcome(event.outcome)
        }
    }
}
```

### Permissions before start

```kotlin
val controller = remember { createCaptureController(config) }
val permissions = requiredPermissions(config)
// permissions: List<CapturePermission> — translate via core:permissions to your platform flow

if (allGranted) {
    LaunchedEffect(controller) {
        controller.start()
    }
}
```

### Headless / custom chrome (no CaptureScreen)

```kotlin
Box {
    CapturePreview(controller, Modifier.fillMaxSize().captureTapToFocus(controller))
    // Compose any building blocks you want, or call controller methods directly.
}
```

---

## Platform Notes

### Android (CameraX)

- Backed by `LifecycleCameraController`. The controller manages its own internal `LifecycleOwner`; consumers don't need an `Activity`/`Fragment` reference.
- Photo + video use cases are bound concurrently. Devices below CameraX's `LIMITED` hardware tier may not support this; on such devices, the controller falls back internally.
- Photo files are written as JPEG with EXIF orientation metadata. `PhotoOutcome.rotationDegrees` reflects the EXIF value.
- `CaptureEvent.FocusCompleted.locked` reflects the real `FocusMeteringResult.isFocusSuccessful` from CameraX.

### iOS (AVFoundation)

- Backed by `AVCaptureSession`. Configuration runs on a background queue to avoid blocking the main thread on `startRunning()` / `stopRunning()`.
- `RecordingProgress.elapsedMs` is polled every 100 ms from `AVCaptureMovieFileOutput.recordedDuration` (AVFoundation does not emit periodic progress events natively).
- Photo files are written as JPEG. `PhotoOutcome.rotationDegrees` is `0` — `UIImage` decodes upright pixels.
- `setFacing()` reconfigures the session in place. Brief preview interruption is expected during the swap.
- A session interruption (app backgrounded, incoming call, another app claiming the camera) does **not** move the controller off `Ready`: AVFoundation pauses and then resumes the session itself, and the controller keeps accepting commands across the gap (a command issued mid-interruption fails with a typed `CaptureError`, not a misleading "not started"). An unrecoverable session fault (hardware error, media-services reset), reported via `AVCaptureSessionRuntimeErrorNotification`, transitions `lifecycle` to `CaptureLifecycle.Error`: call `start()` to retry, or release and rebuild.
- Session presets follow the current mode (see the quality table above); `setFacing` re-applies the preset for the new camera, falling back to `High` when the new camera refuses it.
- Zoom: `CaptureCapabilities.zoomRange` caps the upper bound at 10x even when `maxAvailableVideoZoomFactor` reports more.
- `CaptureEvent.FocusCompleted.locked` reflects *request acceptance*, not actual lock acquisition — KVO on `AVCaptureDevice.adjustingFocus` is on the roadmap.
- `CaptureCapabilities.supportedFlashModes` uses `device.hasTorch` as the proxy for "this lens has an illuminator." Most current devices ship flash + torch together; treating them as one signal keeps the model simple and matches what user-facing UIs care about.
