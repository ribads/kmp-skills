---
name: audio-transcription
description: Use when implementing speech-to-text, voice transcription, audio transcription, real-time voice recognition, or offline audio file transcription in a KMP project. Uses Moonshine on-device engine.
user-invocable: true
---

# core:moonshine — Speech-to-Text Transcription

**Module**: `core:moonshine` | **Artifact**: `com.ribads.synapse:core-moonshine`
**Package**: `com.ribads.synapse.core.moonshine` (models in `com.ribads.synapse.core.moonshine.model`)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-moonshine:<version>")
}
```

Depends on `core:context` (Android). Exposes `kotlinx-coroutines-core` as `api`.

---

## Entry Point

```kotlin
// Loads the model and returns a ready Transcriber. Runs on Dispatchers.IO.
suspend fun loadTranscriber(config: TranscriberConfig): Result<Transcriber>
```

There is no half-built state: a `Transcriber` always has its model loaded. Load failures (missing
files, wrong `arch`) come back as `Result.failure`.

---

## Transcriber

```kotlin
interface Transcriber {
    // Live audio (e.g. a microphone). One stream at a time per Transcriber.
    suspend fun startStream(
        audio: Flow<FloatArray>,     // mono samples in [-1.0, 1.0]
        sampleRate: Int,             // rate of `audio` in Hz; Moonshine resamples to 16 kHz
        scope: CoroutineScope,       // owner of the stream; cancelling it stops the stream
    ): Result<TranscriptionStream>

    // A complete in-memory buffer of mono samples.
    suspend fun transcribe(samples: FloatArray, sampleRate: Int): Result<Transcript>

    // A file on disk. Format is detected from the contents; decoded and transcribed in bounded
    // windows, so memory does not grow with file length. Timestamps are file-relative.
    suspend fun transcribeFile(path: String): Result<Transcript>

    // Stops any live stream (flushing it), then frees the model. Idempotent; later calls fail.
    suspend fun release()
}
```

- All methods are safe from any thread; native work runs on background dispatchers.
- `startStream` fails with `IllegalStateException` while another stream is running or after `release()`.
- Live streams and file/buffer transcriptions may overlap. They share one engine that works one request
  at a time, so a long file transcription delays live updates.
- Supported files: WAV (PCM 8/16/24/32-bit, IEEE float 32/64-bit, WAVE_FORMAT_EXTENSIBLE, any channel
  count) is parsed directly; anything else goes through MediaCodec (Android: M4A/AAC, MP3, FLAC, Ogg, ...)
  or AVAudioFile (iOS: M4A/AAC, MP3, CAF, AIFF, ...). Multi-channel audio is averaged to mono.

## TranscriptionStream

```kotlin
interface TranscriptionStream {
    val transcript: StateFlow<Transcript>   // everything heard so far; final once state != Running
    val state: StateFlow<StreamState>
    suspend fun stop(): Result<Transcript>  // flushes the trailing line; idempotent
}

// Each line once, when it completes; finishes when the stream ends. Lossless (derived from
// `transcript`), and a late collector first receives the lines that completed before it.
val TranscriptionStream.completedLines: Flow<TranscriptLine>
```

A stream ends when `stop()` is called, its `audio` flow completes, or its `scope` is cancelled. Every
path flushes the trailing line into `transcript` before `state` changes. Failures of the audio flow or
the engine end the stream as `StreamState.Failed` and are **never thrown into `scope`**; `stop()` then
returns that failure.

## PCM bridge

```kotlin
// 16-bit little-endian PCM (core:record's AudioRecorder.audioChunks) -> mono floats.
// Interleaved channels are averaged; a frame split across chunks is reassembled. Cold operator.
fun Flow<ByteArray>.decodePcm16(channels: Int = 1): Flow<FloatArray>
```

---

## Models

```kotlin
data class TranscriberConfig(
    val model: ModelSource,
    val arch: ModelArch,                              // must match the files `model` points at
    val options: Map<String, String> = emptyMap(),    // raw Moonshine engine options, passed through
)

sealed interface ModelSource {
    data class Directory(val path: String) : ModelSource  // absolute path on the device
    data class Bundled(val path: String) : ModelSource    // Android assets/<path>, iOS <bundle>/<path>
}

enum class ModelArch { Tiny, Base, TinyStreaming, BaseStreaming, SmallStreaming, MediumStreaming }

data class Transcript(val lines: List<TranscriptLine> = emptyList()) {
    val text: String   // line texts, trimmed, blank lines skipped, joined with " "
}

data class TranscriptLine(
    val id: Long,              // stable while a live line is refined
    val text: String,
    val startTime: Float,      // seconds from the start of the stream / file
    val duration: Float,       // seconds
    val isComplete: Boolean,   // false while a live line can still change
    val words: List<WordTiming> = emptyList(),
    val speakerId: Long? = null,
)

data class WordTiming(
    val word: String,
    val startTime: Float,
    val endTime: Float,
    val confidence: Float,
)

sealed interface StreamState {
    data object Running : StreamState
    data object Stopped : StreamState                       // stopped, audio completed, or scope cancelled
    data class Failed(val cause: Throwable) : StreamState   // transcript keeps what was heard before
}
```

---

## Usage

### Live microphone transcription (with `core:record`)

This module does not own a microphone. Feed it any `Flow<FloatArray>`; for `core:record`, bridge the
16-bit PCM chunks with `decodePcm16` and pass the recorder's real sample rate and channel count.

```kotlin
val transcriber = loadTranscriber(
    TranscriberConfig(model = ModelSource.Bundled("base-en"), arch = ModelArch.Base),
).getOrElse { return showError(it) }

val config = RecordingConfig.Wav()
val recorder = buildAudioRecorder(config)
val stream = transcriber.startStream(
    audio = recorder.audioChunks.decodePcm16(channels = config.channels),
    sampleRate = config.sampleRate,
    scope = viewModelScope,
).getOrElse { return showError(it) }
recorder.start()

// Live UI
viewModelScope.launch {
    stream.transcript.collect { transcript -> render(transcript.lines) }
}

// Stop the recorder first so no new audio arrives, then the stream
recorder.stop()
stream.stop()
    .onSuccess { transcript -> save(transcript.text) }
    .onFailure { showError(it) }

// When the feature is done with the model
transcriber.release()
```

### Reacting to finished lines (e.g. voice commands)

```kotlin
viewModelScope.launch {
    stream.completedLines.collect { line -> handleCommand(line.text) }
}
```

### File transcription

```kotlin
transcriber.transcribeFile("/path/to/memo.m4a")
    .onSuccess { transcript -> transcript.lines.forEach { println("${it.startTime}s: ${it.text}") } }
```

---

## Platform Setup

### Android

#### 1. Ship or download the model

Bundled: put the model folder for your `arch`, exactly as exported, under the app's assets and pass the
folder name:

```
composeApp/src/androidMain/assets/base-en/
├── encoder_model.ort
├── decoder_model_merged.ort
└── tokenizer.bin
```

```kotlin
ModelSource.Bundled("base-en")
```

Moonshine loads models from a directory, so the first load after each install or update copies the
folder to `noBackupFilesDir/moonshine-models/<path>` and later loads reuse that copy. Any architecture
works because the whole folder is copied. The copy costs the model's size in disk space; to avoid it,
download the model at runtime and use `ModelSource.Directory(absolutePath)`.

`core:context` must be initialized for bundled models (it initializes itself through its manifest
provider).

#### 2. ABI

The `moonshine-voice` AAR ships `arm64-v8a` native libraries only. Run on a physical device or an
arm64 emulator image.

#### 3. Permissions

Declared by the app module, not this library: `RECORD_AUDIO` for live microphone audio (see
`/audio-recorder`). File and buffer transcription need no permission.

#### 4. minSdk override

The `moonshine-voice` AAR declares `minSdk 35`. The module's manifest already includes:

```xml
<uses-sdk tools:overrideLibrary="ai.moonshine.voice" />
```

No action needed unless you remove or recreate the module manifest.

### iOS

#### 1. Add the MoonshineVoiceBridge SPM dependency

Kotlin/Native can only interop with Objective-C, but MoonshineVoice is pure Swift. The
`MoonshineVoiceBridge` SPM package provides the `@objc` bridging layer and pulls in `MoonshineVoice`
transitively.

In Xcode: **File > Add Package Dependencies**, add:

```
https://github.com/ribads/moonshine-bridge-kmp
```

Select the `MoonshineVoiceBridge` library product.

#### 2. Cinterop (already configured)

The module ships the cinterop definition and ObjC header:

- `core/moonshine/src/nativeInterop/cinterop/MoonshineVoice.def`
- `core/moonshine/src/nativeInterop/cinterop/MoonshineVoiceBridge.h`

The module's `build.gradle.kts` configures cinterop automatically. iOS targets of this module compile on
macOS only (cinterop cannot cross-compile).

#### 3. Bundle the model

Add the model folder to the Xcode target as a **folder reference** (blue folder, "Create folder
references") so its directory structure survives the copy, and check it is listed under
**Build Phases > Copy Bundle Resources**:

```
iosApp/iosApp/Model/base-en/
├── encoder_model.ort
├── decoder_model_merged.ort
└── tokenizer.bin
```

```kotlin
ModelSource.Bundled("Model/base-en")   // resolved against NSBundle.mainBundle.resourcePath
```

#### 4. Microphone permission (live audio only)

In `Info.plist`:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for speech-to-text transcription.</string>
```

---

## Key Notes

- **Sample rate**: always pass the real rate of the audio. Moonshine resamples internally; a wrong rate
  produces garbage, not an error.
- **Arch must match the files**: non-streaming (`Tiny`, `Base`) and streaming (`*Streaming`) models are
  exported as different file sets. Pass the `arch` the folder was exported for; a mismatch either fails
  `loadTranscriber` or transcribes badly.
- **Errors**: every call returns `Result`; cancellation of the caller is rethrown, never reported as a
  failure. A live stream's failure surfaces in `state` and `stop()`, never in the caller's scope.
- **iOS throughput**: the Swift bridge takes `[Float]`, so each sample is boxed to `NSNumber` on its way to
  the engine. Fine for live audio; file transcription bounds this to one window (2 minutes at 16 kHz) at a
  time.
- **Lifecycle**: load once per feature, `release()` when done. Releasing stops and flushes any live stream
  first.
