---
name: audio-transcription
description: Use when implementing speech-to-text, voice transcription, audio transcription, real-time voice recognition, or offline audio file transcription in a KMP project. One Transcriber API with two on-device engines: Moonshine (the app ships or downloads the model) and the OS's own speech model (ML Kit GenAI Speech Recognition on Android, SpeechAnalyzer on iOS 26), which the OS downloads so the app ships none.
user-invocable: true
---

# Speech-to-Text Transcription

| Module | Artifact | Provides |
|---|---|---|
| `core:transcription` | `com.ribads.synapse:core-transcription` | The engine-agnostic API: `Transcriber`, `TranscriptionStream`, `Transcript` |
| `core:moonshine` | `com.ribads.synapse:core-moonshine` | The Moonshine engine, with models the app bundles or downloads |
| `core:platform-speech` | `com.ribads.synapse:core-platform-speech` | The OS's engine: ML Kit GenAI Speech Recognition (Android), SpeechAnalyzer (iOS 26+) |

Depend on the engines you use. Each exposes `core:transcription`, and through it
`kotlinx-coroutines-core`, as `api`:

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-moonshine:<version>")         // Moonshine
    implementation("com.ribads.synapse:core-platform-speech:<version>")   // the OS's model
}
```

Keep every transcription module on the same Synapse version: the engines share internal API with
`core:transcription` that has no compatibility guarantee across versions.

`core:moonshine` depends on `core:context` (Android).

### Choosing an engine

Both engines return the same `Transcriber`, so an app can use the OS's model where the device has it
and fall back to Moonshine elsewhere (see [Platform first, Moonshine fallback](#platform-first-moonshine-fallback)).

| | Moonshine | OS model, Android | OS model, iOS |
|---|---|---|---|
| Model | bundled or downloaded by the app | downloaded by the OS (AICore / Google) | downloaded by the OS, shared by apps |
| Added to the app | 13 to 18 MB of native code per ABI, plus the model | about 7.7 MB of class archives before R8 (ML Kit, Play services, Guava) | the SpeechAnalyzerBridge Swift package |
| Runs on | Android 8+, iOS | Android 12+; Advanced tier on Gemini Nano devices only | iOS 26+ |
| Recognitions at once | live stream and files overlap | one | one |
| In the background | yes | no: foreground app only | not verified |
| Line timing | always | start of finished live lines only | always |
| Word timing | start, end, confidence (model folder permitting) | start of each word, finished live lines only | start, end, confidence |
| Speakers, vocabulary bias | yes | no | no |

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
// core:transcription
import com.ribads.synapse.core.transcription.Transcriber
import com.ribads.synapse.core.transcription.TranscriptionStream
import com.ribads.synapse.core.transcription.completedLines
import com.ribads.synapse.core.transcription.decodePcm16
import com.ribads.synapse.core.transcription.model.SpeakerSpan
import com.ribads.synapse.core.transcription.model.StreamState
import com.ribads.synapse.core.transcription.model.Transcript
import com.ribads.synapse.core.transcription.model.TranscriptLine
import com.ribads.synapse.core.transcription.model.WordTiming

// core:moonshine
import com.ribads.synapse.core.moonshine.MoonshineTranscriber
import com.ribads.synapse.core.moonshine.loadTranscriber
import com.ribads.synapse.core.moonshine.model.ModelArch
import com.ribads.synapse.core.moonshine.model.ModelSource
import com.ribads.synapse.core.moonshine.model.MoonshineConfig
import com.ribads.synapse.core.moonshine.model.VocabularyBias

// core:platform-speech
import com.ribads.synapse.core.platformspeech.PlatformSpeechException
import com.ribads.synapse.core.platformspeech.PlatformSpeechModel
import com.ribads.synapse.core.platformspeech.buildPlatformSpeechModel
import com.ribads.synapse.core.platformspeech.model.DownloadProgress
import com.ribads.synapse.core.platformspeech.model.PlatformSpeechConfig
import com.ribads.synapse.core.platformspeech.model.PlatformSpeechFailure
import com.ribads.synapse.core.platformspeech.model.PlatformSpeechStatus
import com.ribads.synapse.core.platformspeech.model.SpeechTier
```

`com.ribads.synapse.core.transcription.engine` holds the API the engine modules share. It is
marked `@InternalTranscriptionApi` (an opt-in error): apps never use it.

---

## Transcriber (`core:transcription`)

```kotlin
interface Transcriber {
    // Live audio (e.g. a microphone). One stream at a time per Transcriber.
    suspend fun startStream(
        audio: Flow<FloatArray>,     // mono samples in [-1.0, 1.0]
        sampleRate: Int,             // rate of `audio` in Hz; any rate works, the engine converts it
        scope: CoroutineScope,       // owner of the stream; cancelling it stops the stream
    ): Result<TranscriptionStream>

    // A complete in-memory buffer of mono samples.
    suspend fun transcribe(samples: FloatArray, sampleRate: Int): Result<Transcript>

    // A file on disk. Supported formats depend on the engine. Timestamps are file-relative.
    suspend fun transcribeFile(path: String): Result<Transcript>

    // Stops any live stream (flushing it), then frees the engine. Idempotent; later calls fail.
    suspend fun release()
}
```

- All methods are safe from any thread; engine work runs on background dispatchers.
- `startStream` fails with `IllegalStateException` while another stream is running or after `release()`.
- Engines may limit how many recognitions run at once; a call beyond the limit fails with
  `IllegalStateException`. See each engine for its limit.
- `startStream` is for live audio. Some engines need it to arrive at real-time pace, so for audio that
  is already recorded use `transcribe` or `transcribeFile`.

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
returns that failure. When more than one thing fails, the first is the cause and the rest are attached
to it as suppressed exceptions.

## PCM bridge

```kotlin
// 16-bit little-endian PCM (core:record's AudioRecorder.audioChunks) -> mono floats.
// Interleaved channels are averaged; a frame split across chunks is reassembled. Cold operator.
fun Flow<ByteArray>.decodePcm16(channels: Int = 1): Flow<FloatArray>
```

## Transcript model

```kotlin
data class Transcript(val lines: List<TranscriptLine> = emptyList()) {
    val text: String   // line texts, trimmed, blank lines skipped, joined with " "
}

data class TranscriptLine(
    val id: Long,              // stable while a live line is refined
    val text: String,          // empty when the engine withdrew what it had heard
    val startTime: Float?,     // seconds from the start of the stream / file; null if the engine doesn't report it
    val duration: Float?,      // seconds; null if the engine doesn't report where the line ends
    val isComplete: Boolean,   // false while a live line can still change; speakers may change after
    val words: List<WordTiming> = emptyList(),
    val speakers: List<SpeakerSpan> = emptyList(),  // empty unless the engine identifies speakers
)

data class WordTiming(
    val word: String,
    val startTime: Float,
    val endTime: Float?,       // null if the engine reports only where words start
    val confidence: Float?,    // null if the engine reports none
)

data class SpeakerSpan(
    val speakerId: Long,       // the engine's id for the voice; stable within a live stream (opaque, may be negative)
    val speakerIndex: Int,     // order this stream / transcript first reported the speaker, from 0
    val startTime: Float,      // seconds from the start of the stream / file
    val duration: Float,       // seconds
    val textRange: IntRange?,  // characters of the line's `text` spoken in this span; null if unplaced
)

sealed interface StreamState {
    data object Running : StreamState
    data object Stopped : StreamState                       // stopped, audio completed, or scope cancelled
    data class Failed(val cause: Throwable) : StreamState   // transcript keeps what was heard before
}
```

What each engine reports:

| Field | Moonshine | OS model, Android | OS model, iOS |
|---|---|---|---|
| `TranscriptLine.startTime` | always | finished live lines (their first word); null otherwise | always |
| `TranscriptLine.duration` | always | never | always |
| `TranscriptLine.words` | when the model folder has a word-timestamp decoder | finished live lines | always |
| `WordTiming.endTime`, `confidence` | always | never | always |
| `TranscriptLine.speakers` | when `diarizationModel` is set | never | never |

---

## Moonshine engine (`core:moonshine`)

### Entry point

```kotlin
// Loads the model and returns a ready transcriber. Runs on Dispatchers.IO.
suspend fun loadTranscriber(config: MoonshineConfig): Result<MoonshineTranscriber>

interface MoonshineTranscriber : Transcriber {
    // Replaces the vocabulary bias, from the next audio decoded (a running stream included).
    // Streaming architectures only.
    suspend fun setVocabularyBias(bias: VocabularyBias): Result<Unit>
}
```

There is no half-built state: a `MoonshineTranscriber` always has its model loaded. Load failures
(missing files, wrong `arch`) come back as `Result.failure`.

- `setVocabularyBias` fails with `IllegalStateException` when `arch.isStreaming` is false (`Tiny`, `Base`)
  or after `release()`. It never rewrites text already transcribed.
- Live streams and file/buffer transcriptions may overlap. They share one engine that works one request
  at a time, so a long file transcription delays live updates.
- Any sample rate works: Moonshine resamples to 16 kHz.
- Supported files: on Android, WAV (PCM 8/16/24/32-bit, IEEE float 32/64-bit, WAVE_FORMAT_EXTENSIBLE, any
  channel count) is parsed directly and anything else goes through MediaCodec (M4A/AAC, MP3, FLAC, Ogg, ...).
  On iOS every format, WAV included, goes through AVAudioFile (WAV, M4A/AAC, MP3, CAF, AIFF, ...).
  Multi-channel audio is averaged to mono.
- File windows: `transcribeFile` hands the engine 1,920,000 frames per window (plus 5 s of overlap), counted
  at the file's own sample rate. That is two minutes only for 16 kHz audio: 40 s at 48 kHz, 4 minutes at
  8 kHz.

### Models

```kotlin
data class MoonshineConfig(
    val model: ModelSource,
    val arch: ModelArch,                              // must match the files `model` points at
    val options: Map<String, String> = emptyMap(),    // raw Moonshine engine options, passed through
    val diarizationModel: ModelSource? = null,        // speaker identification models; null = off
)

sealed interface ModelSource {
    data class Directory(val path: String) : ModelSource  // absolute path on the device
    data class Bundled(val path: String) : ModelSource    // Android assets/<path>, iOS <bundle>/<path>
}

enum class ModelArch(val isStreaming: Boolean) {
    Tiny(isStreaming = false),
    Base(isStreaming = false),
    TinyStreaming(isStreaming = true),
    BaseStreaming(isStreaming = true),
    SmallStreaming(isStreaming = true),
    MediumStreaming(isStreaming = true),
}

sealed interface VocabularyBias {
    data object None : VocabularyBias
    // Spelled and capitalized as they should appear. Throws IllegalArgumentException on a comma.
    data class Terms(val terms: List<String>) : VocabularyBias
    // Unusual words are picked out of `text` (the document on screen, a meeting agenda, ...).
    // Throws IllegalArgumentException unless maxTerms > 0.
    data class Context(val text: String, val maxTerms: Int = DEFAULT_MAX_TERMS) : VocabularyBias {
        companion object { const val DEFAULT_MAX_TERMS = 200 }
    }
}
```

### Usage

#### Live microphone transcription (with `core:record`)

No engine owns a microphone. Feed it any `Flow<FloatArray>`; for `core:record`, bridge the
16-bit PCM chunks with `decodePcm16` and pass the recorder's real sample rate and channel count.

```kotlin
val transcriber = loadTranscriber(
    MoonshineConfig(model = ModelSource.Bundled("base-en"), arch = ModelArch.Base),
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

#### Reacting to finished lines (e.g. voice commands)

```kotlin
viewModelScope.launch {
    stream.completedLines.collect { line -> handleCommand(line.text) }
}
```

#### File transcription

```kotlin
transcriber.transcribeFile("/path/to/memo.m4a")
    .onSuccess { transcript -> transcript.lines.forEach { println("${it.startTime}s: ${it.text}") } }
```

#### Who said what (speaker identification)

Point `diarizationModel` at a folder holding Moonshine's diarization models (`segmentation.ort` and
`embedding.ort`, about 8 MB, from Moonshine's diarization model download). Loading fails if they are missing.

```kotlin
val transcriber = loadTranscriber(
    MoonshineConfig(
        model = ModelSource.Bundled("base-en"),
        arch = ModelArch.Base,
        diarizationModel = ModelSource.Bundled("diarization"),
    ),
).getOrThrow()

stream.transcript.collect { transcript ->
    transcript.lines.forEach { line ->
        line.speakers.forEach { span ->
            val words = span.textRange?.let(line.text::substring) ?: line.text
            println("Speaker ${span.speakerIndex + 1}: $words")
        }
    }
}
```

- Render from `transcript`, not from `completedLines` alone: speaker spans for roughly the last two minutes
  are revised as more of each voice is heard, so a line can change speakers after it completes.
- Spans follow the audio, not sentence boundaries: a line can carry several spans, including short blips
  attributed to another voice. Pick the longest span when a line needs a single speaker.
- `textRange` needs word timestamps, which need the model folder's word-timestamp decoder
  (`decoder_with_attention.ort` or `alignment_model.ort` for `Tiny`/`Base`,
  `decoder_kv_with_attention.ort` for streaming models). Without it every `textRange` is null.
- `speakerIndex` restarts at 0 for every stream and every `transcribe` / `transcribeFile` result, even
  though Moonshine's own counter keeps running across the transcriber's lifetime.

#### Vocabulary bias (streaming models)

```kotlin
// A known list: contact names, product names, jargon.
transcriber.setVocabularyBias(VocabularyBias.Terms(listOf("Kubernetes", "Ceph", "Adaeze")))

// Or hand over context and let Moonshine pick the unusual words.
transcriber.setVocabularyBias(VocabularyBias.Context(documentOnScreen, maxTerms = 50))

// Off.
transcriber.setVocabularyBias(VocabularyBias.None)
```

Strength is the load-time `keyterm_boost` option (default `2.0`, the most accurate setting for the
listed terms); lower it through `MoonshineConfig.options` if general accuracy matters more.

### Platform Setup

#### Android

##### 1. Ship or download the model

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

##### 2. ABI

The `moonshine-voice` AAR ships `arm64-v8a`, `armeabi-v7a` and `x86_64` native libraries, 13 to 18 MB
uncompressed per ABI.

##### 3. What `moonshine-voice` adds to the app

The AAR's manifest merges into the app: `RECORD_AUDIO`, `INTERNET` and `ACCESS_NETWORK_STATE`
permissions, plus `ai.moonshine.voice.MicrophonePermissionActivity`. It also brings `appcompat`,
`material`, `okhttp` and `work-runtime` as runtime dependencies. This module uses none of them (it never
downloads models or touches the microphone), and does not strip them, because a library-level
`tools:node="remove"` would also remove the same permissions other libraries declare. An app that does not
want them removes them in its own manifest:

```xml
<uses-permission android:name="android.permission.INTERNET" tools:node="remove" />
<activity android:name="ai.moonshine.voice.MicrophonePermissionActivity" tools:node="remove" />
```

Keep `RECORD_AUDIO` for live microphone audio (see `/synapse:audio-recorder`); file and buffer transcription need
no permission.

##### 4. minSdk override

The `moonshine-voice` AAR declares `minSdk 26`. The module's manifest already includes:

```xml
<uses-sdk tools:overrideLibrary="ai.moonshine.voice" />
```

No action needed unless you remove or recreate the module manifest.

#### iOS

##### 1. Add the MoonshineVoiceBridge SPM dependency

Kotlin/Native can only interop with Objective-C, but MoonshineVoice is pure Swift. The
`MoonshineVoiceBridge` SPM package provides the `@objc` bridging layer and pulls in `MoonshineVoice`
transitively.

In Xcode: **File > Add Package Dependencies**, add:

```
https://github.com/ribads/moonshine-bridge-kmp
```

Select the `MoonshineVoiceBridge` library product, with the dependency rule **Up to Next Minor Version**
from `0.0.2`. Bridge `0.0.2` wraps moonshine-swift `0.1.x` and is the first release this module's
header matches: `0.0.1` fails to link (`MVBSpeakerSpan` is missing), and a newer minor may fail at runtime.

An app only has to link the bridge if it calls `loadTranscriber` (or exports `core:moonshine` into its
framework): Kotlin/Native drops the bridge references that nothing reaches.

##### 2. Cinterop (already configured)

The module ships the cinterop definition and ObjC header:

- `core/moonshine/src/nativeInterop/cinterop/MoonshineVoice.def`
- `core/moonshine/src/nativeInterop/cinterop/MoonshineVoiceBridge.h`

The module's `build.gradle.kts` configures cinterop automatically. iOS targets of this module compile on
macOS only (cinterop cannot cross-compile).

##### 3. Bundle the model

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

##### 4. Microphone permission (live audio only)

In `Info.plist`:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for speech-to-text transcription.</string>
```

### Key Notes

- **Sample rate**: always pass the real rate of the audio. Moonshine resamples internally; a wrong rate
  produces garbage, not an error.
- **Arch must match the files**: non-streaming (`Tiny`, `Base`) and streaming (`*Streaming`) models are
  exported as different file sets. Pass the `arch` the folder was exported for; a mismatch either fails
  `loadTranscriber` or transcribes badly.
- **Errors**: every call returns `Result`; cancellation of the caller is rethrown, never reported as a
  failure. A live stream's failure surfaces in `state` and `stop()`, never in the caller's scope.
- **Speakers in files**: `transcribeFile` transcribes in windows of 1,920,000 frames (two minutes at 16 kHz,
  shorter for higher sample rates), and each window identifies speakers on its own. In files longer than
  one window, the same voice can come back under a new
  `speakerId` (and so a new `speakerIndex`) in each window. Live streams keep voices consistent for the
  whole stream.
- **Speaker cost**: identification runs inside every transcription pass and its cost grows with session
  length; tune it with the raw `diarization_cluster_window_sec` and `diarization_cluster_cadence` options.
- **Lifecycle**: load once per feature, `release()` when done. Releasing stops and flushes any live stream
  first.

---

## OS model engine (`core:platform-speech`)

### Entry point

```kotlin
// Cheap: nothing is checked or loaded until a call. Holds no OS resources.
fun buildPlatformSpeechModel(config: PlatformSpeechConfig): PlatformSpeechModel

interface PlatformSpeechModel {
    val config: PlatformSpeechConfig

    // A failure means the OS could not be asked (often temporary), not that the model is unsupported.
    suspend fun status(): Result<PlatformSpeechStatus>

    // Downloads and installs the model; joins a download already running. onProgress runs in the
    // caller's coroutine, one call at a time; updates arriving meanwhile are merged into the next.
    suspend fun download(onProgress: suspend (DownloadProgress) -> Unit = {}): Result<Unit>

    // A ready Transcriber; release it when done. Fails with NotInstalled unless status() is
    // Available, and with Unsupported when it is Unsupported.
    suspend fun load(): Result<Transcriber>
}
```

- The `Transcriber` from `load()` runs **one recognition at a time** (a live stream, a buffer or a file);
  a second fails with `IllegalStateException`.
- `release()` stops and flushes a live stream, and fails a buffer or file transcription still running with
  `IllegalStateException`.
- `stop()` (and `release()`) wait at most 5 s for the OS's last results. Past that the stream ends as
  `StreamState.Failed` and the trailing line stays incomplete.

### Models

```kotlin
data class PlatformSpeechConfig(
    val locale: String,                       // BCP 47, e.g. "en-US"; throws IllegalArgumentException if blank
    val tier: SpeechTier = SpeechTier.Advanced,
)

enum class SpeechTier { Advanced, Basic }   // no fallback: a device without the tier reports Unsupported

enum class PlatformSpeechStatus { Unsupported, Downloadable, Downloading, Available }

data class DownloadProgress(val fraction: Float?)   // 0 to 1; null while the size is unknown; never decreases

class PlatformSpeechException(
    val failure: PlatformSpeechFailure,
    message: String,
    cause: Throwable? = null,                 // the OS's own error, when it is a Throwable
) : Exception(message, cause)

sealed interface PlatformSpeechFailure {
    data object Unsupported : PlatformSpeechFailure          // use another engine
    data object NotInstalled : PlatformSpeechFailure         // download first (the OS may also have removed it)
    data class Busy(val retryAfter: Duration?) : PlatformSpeechFailure   // try again later
    data object Backgrounded : PlatformSpeechFailure         // Android: only the foreground app may use the model
    data object QuotaExceeded : PlatformSpeechFailure        // the app's long-term (e.g. daily) allowance is used up
    data object InsufficientStorage : PlatformSpeechFailure  // no room to download the model
    data object NeedsUpdate : PlatformSpeechFailure          // the OS's speech components need an update
    data object InputTooLarge : PlatformSpeechFailure        // audio too long for one request
    data object InputTooSmall : PlatformSpeechFailure        // audio too short to transcribe
    data object Rejected : PlatformSpeechFailure             // content policy; a live transcript may end early
    data object Unexpected : PlatformSpeechFailure           // anything else
}
```

| Tier | Android | iOS 26+ |
|---|---|---|
| `Advanced` | ML Kit `MODE_ADVANCED`: Gemini Nano through AICore, on Pixel 10/11, Galaxy S26 and other Gemini Nano devices; 21 locales | `SpeechTranscriber`, on hardware where `SpeechTranscriber.isAvailable` |
| `Basic` | ML Kit `MODE_BASIC`: Android 12+ (API 31); 15 locales | `DictationTranscriber`, the on-device dictation model, older hardware too |

Locale tags differ by OS: Android's Advanced tier lists Mandarin as `cmn-Hans-CN`. iOS uses the closest
locale its model supports.

### Usage

#### Platform first, Moonshine fallback

Try the tiers in order, download when the OS offers the model, and fall back to Moonshine:

```kotlin
suspend fun loadBestTranscriber(onDownload: suspend (DownloadProgress) -> Unit): Result<Transcriber> {
    for (tier in listOf(SpeechTier.Advanced, SpeechTier.Basic)) {
        val model = buildPlatformSpeechModel(PlatformSpeechConfig("en-US", tier))
        val loaded = when (model.status().getOrNull()) {
            PlatformSpeechStatus.Available -> model.load()
            PlatformSpeechStatus.Downloadable, PlatformSpeechStatus.Downloading ->
                model.download(onDownload).fold(onSuccess = { model.load() }, onFailure = { Result.failure(it) })
            PlatformSpeechStatus.Unsupported, null -> continue
        }
        if (loaded.isSuccess) return loaded
    }
    return loadTranscriber(MoonshineConfig(model = ModelSource.Bundled("base-en"), arch = ModelArch.Base))
}
```

Ask the user before a download, especially on a metered network (`/synapse:connectivity` reports it). Because
`onDownload` runs in the caller's coroutine, an MVI interactor can emit from it:
`flow { loadBestTranscriber { emit(Result.OnModelDownloading(it.fraction)) } }`.

Live streams, buffers and files then work exactly as in the [Moonshine usage](#usage) above.

#### Reacting to the OS's failures

```kotlin
stream.state.collect { state ->
    val failure = ((state as? StreamState.Failed)?.cause as? PlatformSpeechException)?.failure
    when (failure) {
        PlatformSpeechFailure.Backgrounded -> showMessage("Transcription pauses while the app is in the background")
        is PlatformSpeechFailure.Busy -> retryAfter(failure.retryAfter)
        PlatformSpeechFailure.NotInstalled -> offerDownload()
        else -> Unit
    }
}
```

### Platform Setup

#### Android

- **API levels**: the engine reports `Unsupported` below Android 12 without loading ML Kit's classes. ML Kit
  declares minSdk 26; the module's manifest overrides it (`com.google.mlkit.genai.speechrecognition`,
  `com.google.mlkit.genai.common`), so apps down to the repo's minSdk build.
- **ML Kit is alpha** (`genai-speech-recognition` 1.0.0-alpha2, pinned): no SLA, breaking changes possible.
- **Foreground only**: ML Kit GenAI runs only while the app is the top foreground app, foreground services
  included; otherwise the stream fails with `Backgrounded`. Use Moonshine for background recording
  (`buildPersistentAudioRecorder`).
- **Live audio at real-time pace**: feeding a stream much faster than real time overflows ML Kit's buffer
  and fails it. Use `transcribe` / `transcribeFile` for recorded audio.
- **Files**: MP3, WAV, FLAC, M4A and OGG, recognized by the file extension. Buffer and file results carry
  no timing.
- **Merged into the app**: `INTERNET` and `ACCESS_NETWORK_STATE`, `<queries>` for `com.google.android.tts`
  and `com.google.android.aicore`, ML Kit's `MlKitInitProvider` and `MlKitComponentDiscoveryService`, Play
  services' `GoogleApiActivity`, and datatransport's scheduling components. ML Kit reports usage
  through datatransport: declare it in the Play Data safety form (Google's ML Kit data disclosure lists
  what it sends).
- Devices with an unlocked bootloader are not supported. Google's GenAI use policy applies.
- Keep `RECORD_AUDIO` for live microphone audio (see `/synapse:audio-recorder`).

#### iOS

##### 1. Add the SpeechAnalyzerBridge SPM dependency

SpeechAnalyzer is Swift-only, so Kotlin/Native reaches it through the `SpeechAnalyzerBridge` package's
`@objc` layer. In Xcode: **File > Add Package Dependencies**, add:

```
https://github.com/ribads/speech-analyzer-bridge-kmp
```

Select the `SpeechAnalyzerBridge` library product, with the dependency rule **Up to Next Minor Version**
from `0.0.1`. Build with the Xcode 26 SDK or later. The package links into apps with a deployment target
down to iOS 16; below iOS 26 every status is `Unsupported`.

An app only has to link the package if it calls into `core:platform-speech` (or exports it into its
framework): Kotlin/Native drops the bridge references that nothing reaches.

##### 2. Cinterop (already configured)

- `core/platform-speech/src/nativeInterop/cinterop/SpeechAnalyzerBridge.def`
- `core/platform-speech/src/nativeInterop/cinterop/SpeechAnalyzerBridge.h`

iOS targets of this module compile on macOS only.

##### 3. Permissions

`NSMicrophoneUsageDescription` for live microphone audio. SpeechAnalyzer does not use the speech
recognition permission, so no `NSSpeechRecognitionUsageDescription` is needed.

##### 4. Models

The OS downloads and updates the models and shares them between apps; they do not count toward the app's
size. Each locale the app installs is reserved against a per-app limit that persists across launches.
