---
name: audio-recorder
description: Use when implementing audio recording, microphone capture, voice recording, WAV/AAC recording, or audio data streaming in a KMP project.
user-invocable: true
---

# core:record: Audio Recording

**Module**: `core:record` | **Artifact**: `com.ribads.synapse:core-record`
**Packages**: `com.ribads.synapse.core.record`, `com.ribads.synapse.core.record.model`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-record:<version>")
}
```

Depends on `core:context` (Android) and `core:audio-session` (iOS, see `/synapse:audio-session`): on iOS the
recorder acquires the shared `AVAudioSession` through `AudioSessionCoordinator` for the duration of
each recording (and the persistent recorder for as long as it is bound), so it coexists with
`core:playback` and `core:moonshine`.

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.record.AudioRecorder
import com.ribads.synapse.core.record.PersistentAudioRecorder
import com.ribads.synapse.core.record.buildAudioRecorder
import com.ribads.synapse.core.record.buildPersistentAudioRecorder
import com.ribads.synapse.core.record.exportRecording
import com.ribads.synapse.core.record.model.OutputFormat
import com.ribads.synapse.core.record.model.RecordingConfig
import com.ribads.synapse.core.record.model.RecordingOutput
import com.ribads.synapse.core.record.model.RecordingState
```

iOS-only types from `core:audio-session` that this skill mentions (`iosMain` only):

```kotlin
import com.ribads.synapse.core.audiosession.AudioSessionCoordinator
import com.ribads.synapse.core.audiosession.AudioSessionException   // thrown by PersistentAudioRecorder.bind() on iOS
```

---

## App setup

The module does not request permissions itself (use `/synapse:permissions`), and it does not declare
`RECORD_AUDIO`.

**Android** (`AndroidManifest.xml` of the app):
- Declare `android.permission.RECORD_AUDIO` and request it at runtime before `start()` / `bind()`.
- Persistent recorder on Android 13+: declare `android.permission.POST_NOTIFICATIONS` and request it
  at runtime, otherwise the foreground service runs but its notification is not shown.
- Call `PersistentAudioRecorder.bind()` while the app is in the foreground: Android restricts
  starting a microphone foreground service from the background.
- The library already declares `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_MICROPHONE` and the
  recording service.

**iOS** (`Info.plist`):
- `NSMicrophoneUsageDescription` (required for any recording).
- `UIBackgroundModes` containing `audio` (persistent recorder only).
- `UIFileSharingEnabled` **and** `LSSupportsOpeningDocumentsInPlace` set to `YES` if exported
  recordings should be visible in the Files app.

---

## Entry Points

```kotlin
// Create a recorder
expect fun buildAudioRecorder(config: RecordingConfig = RecordingConfig.Wav()): AudioRecorder

// Create a persistent recorder (survives backgrounding via foreground service on Android)
expect fun buildPersistentAudioRecorder(config: RecordingConfig = RecordingConfig.Wav()): PersistentAudioRecorder

// Export a recording to a user-visible location
expect suspend fun exportRecording(
    output: RecordingOutput,
    displayName: String,          // without extension; appended from output.format
    directory: String? = null,    // Android: MediaStore relative path (default "Music"); iOS: subfolder of Documents
    deleteSource: Boolean = false,
): Result<String>                 // Android: content URI; iOS: absolute file path
```

---

## AudioRecorder

```kotlin
interface AudioRecorder {
    val state: StateFlow<RecordingState>
    val audioChunks: SharedFlow<ByteArray>  // 16-bit LE PCM at config.sampleRate, interleaved for stereo;
                                            // lossy under backpressure: drops oldest chunks (file unaffected)

    fun start(): Result<Unit>
    fun pause(): Result<Unit>
    fun resume(): Result<Unit>
    suspend fun stop(): Result<RecordingOutput>
    suspend fun release()  // finalizes an in-progress recording, then suspends until the capture loop has exited
}
```

**Error contract** (consistent with the `Result` return types):
- Call failures are returned as `Result.failure` and leave `state` unchanged:
  - `start()`: already recording, recorder released, unsupported config (channels not 1 or 2,
    `Wav.bitDepth` not 16, sample rate not positive), output directory or file cannot be created,
    microphone or audio engine fails to start. A failed start leaves no file behind.
  - `pause()` / `resume()`: wrong state.
  - `stop()`: not recording/paused (after a mid-recording failure it returns that failure's cause).
- Failures **after** a recording started are emitted as `RecordingState.Error(cause)`: the
  microphone or audio engine stops delivering audio, a file write fails, or the file cannot be
  finalized (also returned by `stop()` in that case). The recorder has already released the
  microphone and finalized the partial file where possible. `start()` is allowed again from `Error`.

**Lifecycle:**
- `start()` is allowed from `Idle` and `Error`.
- `release()` finalizes a recording still in progress (the file stays at the path the last
  `Recording`/`Paused` state reported, and is not deleted), moves `state` to `Idle` (or `Error`
  if finalizing fails), and makes the instance unusable: later `start()` calls fail.

## PersistentAudioRecorder

```kotlin
interface PersistentAudioRecorder {
    val recorder: AudioRecorder     // throws IllegalStateException before bind()
    val isBound: Boolean

    suspend fun bind(notification: Any? = null)
    suspend fun unbind()            // suspends through the underlying recorder.release()
}
```

`bind(notification)`:
- **Android**: starts and binds the foreground service and suspends until the recorder is ready.
  Pass an `android.app.Notification`, or `null` to use a default ongoing "Recording" notification
  on a low-importance channel with ID `audio_recording` (created if missing). Any other type throws
  `IllegalStateException`, as does a failure to bind the service.
- **iOS**: acquires a background-capable audio session; `notification` is ignored. Throws
  `AudioSessionException` if the session cannot be activated.

---

## Models

### RecordingConfig

```kotlin
sealed class RecordingConfig {
    abstract val sampleRate: Int                 // Hz, must be positive
    abstract val channels: Int                   // 1 (mono) or 2 (stereo, interleaved); others fail start()
    abstract val decibelUpdateIntervalMs: Long   // 0 disables Recording-state updates
    abstract val outputDirectory: String?        // created if missing; null = platform cache/temp dir
    abstract val outputFormat: OutputFormat

    data class Wav(
        override val sampleRate: Int = 16_000,
        override val channels: Int = 1,
        val bitDepth: Int = 16,                  // must be 16 (capture is 16-bit); others fail start()
        override val decibelUpdateIntervalMs: Long = 100L,
        override val outputDirectory: String? = null,
    ) : RecordingConfig()

    data class AacM4a(
        override val sampleRate: Int = 16_000,
        override val channels: Int = 1,
        val bitRate: Int = 64_000,
        override val decibelUpdateIntervalMs: Long = 100L,
        override val outputDirectory: String? = null,
    ) : RecordingConfig()
}
```

- Default directory: the app's cache directory on Android, `NSTemporaryDirectory()` on iOS.
- File names: `rec_<epochMs>_<8 random hex chars>.<wav|m4a>`, unique even for recorders started in
  the same millisecond.
- Stereo: Android records the microphone in stereo; iOS maps the hardware input to the requested
  channel count (a mono microphone is duplicated into both channels, extra hardware channels are
  dropped). Mono averages every input channel.

### OutputFormat

```kotlin
enum class OutputFormat(val fileExtension: String, val mimeType: String) {
    WAV(fileExtension = "wav", mimeType = "audio/wav"),
    AAC_M4A(fileExtension = "m4a", mimeType = "audio/mp4"),
}
```

### RecordingOutput

```kotlin
data class RecordingOutput(
    val filePath: String,
    val durationMs: Long,
    val sampleRate: Int,
    val format: OutputFormat = OutputFormat.WAV,
)
```

### RecordingState

```kotlin
sealed class RecordingState {
    data object Idle : RecordingState()
    data class Recording(val decibelLevel: Float, val durationMs: Long, val filePath: String) : RecordingState()
    data class Paused(val durationMs: Long, val filePath: String) : RecordingState()
    data class Error(val cause: Throwable) : RecordingState()   // mid-recording failure; see Error contract
}
```

---

## Usage

```kotlin
// Basic WAV recording
val recorder = buildAudioRecorder(RecordingConfig.Wav(sampleRate = 16_000))
recorder.start().onFailure { showError(it) }

// Observe state
recorder.state.collect { state ->
    when (state) {
        is RecordingState.Recording -> updateUI(state.decibelLevel, state.durationMs)
        is RecordingState.Paused -> showPaused()
        is RecordingState.Error -> showError(state.cause)
        RecordingState.Idle -> showIdle()
    }
}

// Stream raw PCM chunks (e.g., for live transcription)
recorder.audioChunks.collect { pcmBytes -> /* process */ }

// Stop and get output
val result = recorder.stop()
result.onSuccess { output ->
    println("Recorded ${output.durationMs}ms to ${output.filePath}")
    // Export to media library
    exportRecording(output, displayName = "My Recording")
}
recorder.release()

// Persistent recording (Android foreground service)
val persistent = buildPersistentAudioRecorder(RecordingConfig.AacM4a(bitRate = 128_000))
persistent.bind(notification = myNotification)   // or null for the default notification
persistent.recorder.start()
// ... survives app backgrounding
persistent.recorder.stop()
persistent.unbind()
```

---

## Platform Notes

- **Android capture**: `AudioRecord` (16-bit PCM) from `MediaRecorder.AudioSource.MIC`; WAV is
  written directly, AAC goes through `MediaCodec` + `MediaMuxer`.
- **iOS capture**: `AVAudioEngine` input tap at the hardware rate, linearly resampled to
  `sampleRate` and converted to 16-bit PCM off the audio thread. WAV is written with
  `NSFileHandle`, AAC with `AVAudioFile`.
- **iOS AAC finalization**: on iOS 18+ the `.m4a` is closed when `stop()` returns. On earlier iOS
  versions `AVAudioFile` has no `close()`, so the file is only completed when the Kotlin/Native
  garbage collector releases the writer, some time after `stop()` returns; prefer WAV if you read
  the file immediately on iOS 17 or earlier.
- **iOS pause**: the engine keeps running while paused (frames are discarded), so the microphone
  indicator stays on.
