---
name: audio-transcription
description: Use when implementing speech-to-text, voice transcription, audio transcription, real-time voice recognition, or offline audio file transcription in a KMP project. Uses Moonshine on-device engine.
user-invocable: true
---

# core:moonshine — Speech-to-Text Transcription

**Module**: `core:moonshine` | **Artifact**: `com.ribads.synapse:core-moonshine`
**Package**: `com.ribads.synapse.core.moonshine`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-moonshine:<version>")
}
```

---

## Core Interfaces

### Transcriber

```kotlin
interface Transcriber {
    val events: Flow<TranscriptEvent>
    val isActive: StateFlow<Boolean>
    fun start(audioChunks: SharedFlow<FloatArray>, scope: CoroutineScope)
    suspend fun stop()
    suspend fun transcribeFile(filePath: String, format: AudioFormat = AudioFormat.WAV): Result<List<TranscriptLine>>
    fun release()
}
```

### LocalTranscriber (extends Transcriber)

```kotlin
interface LocalTranscriber : Transcriber {
    suspend fun loadModel(modelPath: String, context: Any? = null)
}

expect fun buildLocalTranscriber(options: TranscriberOptions): LocalTranscriber
```

### TranscriberSession

```kotlin
interface TranscriberSession {
    val transcriber: Transcriber
    val lines: StateFlow<List<TranscriptLine>>
    val isActive: StateFlow<Boolean>
    val currentSessionId: String?
    fun start(audioChunks: SharedFlow<FloatArray>, scope: CoroutineScope): String
    suspend fun stop(): Result<SessionResult>
}

fun TranscriberSession(transcriber: Transcriber): TranscriberSession
```

### AudioCapture

```kotlin
interface AudioCapture {
    val isAvailable: Flow<Boolean>
    val audioChunks: SharedFlow<FloatArray>
    fun start()
    fun stop()
    fun release()
}

expect fun buildAudioCapture(): AudioCapture
```

### AudioSession

```kotlin
class AudioSession(audioCapture: AudioCapture) {
    val audioChunks: SharedFlow<FloatArray>
    val sessionAudio: StateFlow<ByteArray?>
    val isRecording: StateFlow<Boolean>
    fun startSession(scope: CoroutineScope)
    fun stopSession(): ByteArray
    fun release()
}
```

### WavDecoder

```kotlin
expect object WavDecoder {
    fun decode(filePath: String): FloatArray
}
```

### Utility

```kotlin
fun SharedFlow<ByteArray>.pcmBytesToFloat(scope: CoroutineScope): SharedFlow<FloatArray>
```

---

## Models

```kotlin
sealed interface TranscriptEvent {
    val line: TranscriptLine
    data class LineStarted(override val line: TranscriptLine) : TranscriptEvent
    data class LineUpdated(override val line: TranscriptLine) : TranscriptEvent
    data class LineTextChanged(override val line: TranscriptLine) : TranscriptEvent
    data class LineCompleted(override val line: TranscriptLine) : TranscriptEvent
}

data class TranscriptLine(
    val id: Long,
    val text: String,
    val startTime: Float,
    val duration: Float,
    val isComplete: Boolean,
    val words: List<WordTiming> = emptyList(),
    val speakerId: Long? = null,
)

data class WordTiming(
    val word: String,
    val startTime: Float,
    val endTime: Float,
    val confidence: Float,
)

data class SessionResult(
    val sessionId: String,
    val lines: List<TranscriptLine>,
)

data class TranscriberOptions(
    val modelArch: ModelArch,
    val extraOptions: Map<String, String> = emptyMap(),
)

enum class ModelArch(val value: Int) {
    Tiny(0), Base(1), TinyStreaming(2), BaseStreaming(3), SmallStreaming(4), MediumStreaming(5)
}

enum class AudioFormat { WAV, AAC_M4A }
```

---

## Usage

### Real-time microphone transcription

```kotlin
val transcriber = buildLocalTranscriber(TranscriberOptions(modelArch = ModelArch.BaseStreaming))
transcriber.loadModel(modelPath = "/path/to/model")

val capture = buildAudioCapture()
val session = TranscriberSession(transcriber)

capture.start()
val sessionId = session.start(capture.audioChunks, viewModelScope)

// Observe transcript events
session.lines.collect { lines ->
    lines.forEach { line -> println("${line.text} (complete=${line.isComplete})") }
}

// Stop
val result = session.stop()
capture.stop()
result.onSuccess { println("Session ${it.sessionId}: ${it.lines.size} lines") }
```

### Offline file transcription

```kotlin
val transcriber = buildLocalTranscriber(TranscriberOptions(modelArch = ModelArch.Base))
transcriber.loadModel(modelPath = "/path/to/model")

val result = transcriber.transcribeFile("/path/to/audio.wav")
result.onSuccess { lines ->
    lines.forEach { println("${it.startTime}s: ${it.text}") }
}
```

### Using AudioSession for managed capture

```kotlin
val capture = buildAudioCapture()
val audioSession = AudioSession(capture)

audioSession.startSession(viewModelScope)
// audioSession.audioChunks flows to transcriber
// audioSession.sessionAudio accumulates all audio bytes
val allAudio = audioSession.stopSession()
audioSession.release()
```

---

## Platform Setup

### Android

#### 1. Add model files to assets

Place Moonshine model files in your app module's assets:

```
composeApp/src/androidMain/assets/base-en/
├── encoder_model.ort
├── decoder_model_merged.ort
└── tokenizer.bin
```

The asset path passed to `loadModel()` should be the folder name (e.g. `"base-en"`).

#### 2. Declare permissions in AndroidManifest.xml

In your **app module's** manifest (not the library module):

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

`POST_NOTIFICATIONS` is required on API 33+ because the permissions framework maps audio permission to both.

#### 3. minSdk override

The `moonshine-voice` AAR declares `minSdk 35`. The moonshine module's manifest already includes:

```xml
<uses-sdk tools:overrideLibrary="ai.moonshine.voice" />
```

No action needed unless you remove or recreate the module manifest.

#### 4. Usage

```kotlin
val options = TranscriberOptions(modelArch = ModelArch.Base)
val transcriber = buildLocalTranscriber(options)
transcriber.loadModel("base-en", context = activity)

val capture = buildAudioCapture()
capture.start()
transcriber.start(capture.audioChunks, coroutineScope)
```

### iOS

#### 1. Add MoonshineVoiceBridge SPM dependency

Kotlin/Native can only interop with Objective-C, but MoonshineVoice is pure Swift. The `MoonshineVoiceBridge` SPM package provides the required `@objc` bridging layer and pulls in `MoonshineVoice` transitively.

In Xcode: **File > Add Package Dependencies**, add:

```
https://github.com/ribads/moonshine-bridge-kmp
```

Select the `MoonshineVoiceBridge` library product.

#### 2. Cinterop (already configured)

The module ships with the cinterop definition and ObjC header:

- `core/moonshine/src/nativeInterop/cinterop/MoonshineVoice.def`
- `core/moonshine/src/nativeInterop/cinterop/MoonshineVoiceBridge.h`

The module's `build.gradle.kts` configures cinterop automatically. The cinterop package name comes from the `.def` filename, so Kotlin imports use `import MoonshineVoice.MVBTranscriber`, etc.

#### 3. Add model files to Xcode bundle

Add model files directly to your Xcode target (not inside a folder reference — Xcode flattens folder references):

```
iosApp/iosApp/Model/base-en/
├── encoder.ort
├── decoder_model_merged.ort
├── frontend.ort
├── adapter.ort
├── streaming_config.json
└── tokenizer.bin
```

Ensure all files are listed under **Build Phases > Copy Bundle Resources**. Use `NSBundle.mainBundle.resourcePath` as the model path, not a subdirectory.

#### 4. Add microphone permission

In `Info.plist`:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for speech-to-text transcription.</string>
```

#### 5. Usage

```kotlin
val options = TranscriberOptions(modelArch = ModelArch.Base)
val transcriber = buildLocalTranscriber(options)
transcriber.loadModel(NSBundle.mainBundle.resourcePath!!)

val capture = buildAudioCapture()
capture.start()
transcriber.start(capture.audioChunks, coroutineScope)
```

---

## Key Notes

- **ModelArch**: Use `ModelArch.Base` for non-streaming `base-en` models. `ModelArch.BaseStreaming` is for streaming-specific model files.
- **AudioCapture**: Records at the device's native sample rate and downsamples to 16kHz mono internally. Call `onPermissionGranted()` after microphone permission is obtained.
- **AudioSession**: Wraps `AudioCapture` and accumulates audio chunks. On `stop()`, it converts the buffered float32 PCM to int16 PCM bytes.
- **WavDecoder**: Use `WavDecoder.decode(filePath)` to decode a `.wav` file into a `FloatArray` for offline transcription via `transcriber.transcribeFile()`.
- **Event flow**: Collect from `transcriber.events` (not `AudioSession.events`) to receive `TranscriptEvent` updates.
