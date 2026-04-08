---
name: audio-recorder
description: Use when implementing audio recording, microphone capture, voice recording, WAV/AAC recording, or audio data streaming in a KMP project.
user-invocable: true
---

# core:record — Audio Recording

**Module**: `core:record` | **Artifact**: `com.ribads.synapse:core-record`
**Package**: `com.ribads.synapse.core.record`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-record:<version>")
}
```

Depends on `core:context`.

---

## Entry Points

```kotlin
// Create a recorder
expect fun buildAudioRecorder(config: RecordingConfig = RecordingConfig.Wav()): AudioRecorder

// Create a persistent recorder (survives backgrounding via foreground service on Android)
expect fun buildPersistentAudioRecorder(config: RecordingConfig = RecordingConfig.Wav()): PersistentAudioRecorder

// Export a recording to the device's media library
expect suspend fun exportRecording(
    output: RecordingOutput,
    displayName: String,
    directory: String? = null,
    deleteSource: Boolean = false,
): Result<String>
```

---

## AudioRecorder

```kotlin
interface AudioRecorder {
    val state: StateFlow<RecordingState>
    val audioChunks: SharedFlow<ByteArray>

    fun start(): Result<Unit>
    fun pause(): Result<Unit>
    fun resume(): Result<Unit>
    suspend fun stop(): Result<RecordingOutput>
    fun release()
}
```

## PersistentAudioRecorder

```kotlin
interface PersistentAudioRecorder {
    val recorder: AudioRecorder
    val isBound: Boolean

    suspend fun bind(notification: Any? = null)  // Android: pass a Notification object
    fun unbind()
}
```

---

## Models

### RecordingConfig

```kotlin
sealed class RecordingConfig {
    abstract val sampleRate: Int
    abstract val channels: Int
    abstract val decibelUpdateIntervalMs: Long
    abstract val outputDirectory: String?
    abstract val outputFormat: OutputFormat

    data class Wav(
        override val sampleRate: Int = 16_000,
        override val channels: Int = 1,
        val bitDepth: Int = 16,
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
    data class Error(val cause: Throwable) : RecordingState()
}
```

---

## Usage

```kotlin
// Basic WAV recording
val recorder = buildAudioRecorder(RecordingConfig.Wav(sampleRate = 16_000))
recorder.start()

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
persistent.bind(notification = myNotification)
persistent.recorder.start()
// ... survives app backgrounding
persistent.recorder.stop()
persistent.unbind()
```
