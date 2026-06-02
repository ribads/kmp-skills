---
name: audio-playback
description: Use when implementing audio playback, music players, podcast playback, streaming audio, lock-screen/Control-Center media controls, or background audio in a KMP project.
user-invocable: true
---

# core:playback — Audio Playback

**Module**: `core:playback` | **Artifact**: `com.ribads.synapse:core-playback`
**Package**: `com.ribads.synapse.core.playback`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-playback:<version>")
}
```

Depends on `core:context`.

Supports local files (WAV, MP3, AAC/M4A, OGG, FLAC) and remote audio (progressive HTTP, HLS, DASH). Format is detected automatically — no explicit format selection.

---

## Entry Points

```kotlin
// In-app player — does NOT survive backgrounding. Use for sound effects,
// notification previews, short clips.
expect fun buildAudioPlayer(config: PlayerConfig = PlayerConfig()): AudioPlayer

// Persistent player — survives app backgrounding and integrates with platform
// media controls (Android foreground service + notification; iOS Control Center
// + lock screen via MPNowPlayingInfoCenter / MPRemoteCommandCenter).
expect fun buildPersistentAudioPlayer(
    config: PlayerConfig = PlayerConfig(),
    notification: PlaybackNotification,
): AudioPlayer
```

**Platform requirements for `buildPersistentAudioPlayer`:**
- **Android**: Nothing to register. Foreground-service entry and the
  `FOREGROUND_SERVICE` / `FOREGROUND_SERVICE_MEDIA_PLAYBACK` permissions are
  declared in this library's manifest.
- **iOS**: The consuming app must add `audio` to `UIBackgroundModes` in its
  `Info.plist`.

---

## AudioPlayer

```kotlin
interface AudioPlayer {
    val state: StateFlow<PlaybackState>
    val position: StateFlow<PositionInfo>
    val amplitudes: SharedFlow<AmplitudeInfo>
    val volume: StateFlow<Float>
    val playbackRate: StateFlow<Float>

    fun load(
        source: PlaybackSource,
        metadata: MediaMetadata = MediaMetadata(),
    ): CommandResult

    fun dispatch(command: PlaybackCommand): CommandResult

    suspend fun release()
}
```

`release()` is a `suspend fun`: it awaits engine/listener teardown (and, for
`buildPersistentAudioPlayer`, service detach) before returning, so callers can
deterministically sequence shutdown. Call it from a coroutine.

**Separation of concerns:**
- Lifecycle → `load` / `release`
- Runtime control → `dispatch(PlaybackCommand)` returns `CommandResult` (accept/reject)
- Observation → the five flows drive UI (scrubber, level meter, play/pause button)

Runtime errors (network, decode) surface on `state` as `PlaybackState.Error`.
`CommandResult.Failure` is reserved for command-acceptance rejection (bad ranges, released player).

---

## Models

### PlaybackCommand

```kotlin
sealed class PlaybackCommand {
    data object Play : PlaybackCommand()
    data object Pause : PlaybackCommand()
    data object Stop : PlaybackCommand()                       // resets position to 0, keeps source loaded
    data class SeekTo(val positionMs: Long) : PlaybackCommand()
    data class SetVolume(val volume: Float) : PlaybackCommand()       // 0.0..1.0
    data class SetPlaybackRate(val rate: Float) : PlaybackCommand()   // 0.25..4.0
}
```

`load` is intentionally NOT a command — it is lifecycle on `AudioPlayer.load`.

### PlaybackState

```kotlin
sealed class PlaybackState {
    data object Idle : PlaybackState()           // no source loaded
    data object Loading : PlaybackState()        // initial buffering
    data object Ready : PlaybackState()          // prepared, not yet playing
    data object Playing : PlaybackState()
    data object Paused : PlaybackState()
    data object Buffering : PlaybackState()      // stalled mid-stream (remote only)
    data object Ended : PlaybackState()          // reached end; replayable via Play
    data class Error(val cause: Throwable) : PlaybackState()
}
```

### PlaybackSource

```kotlin
sealed class PlaybackSource {
    data class LocalFile(val path: String) : PlaybackSource()

    data class Remote(
        val url: String,
        val headers: Map<String, String> = emptyMap(),
    ) : PlaybackSource()
}
```

### CommandResult

```kotlin
sealed class CommandResult {
    data object Success : CommandResult()
    data class Failure(
        val message: String,
        val cause: Throwable? = null,
    ) : CommandResult()
}
```

### PositionInfo

```kotlin
data class PositionInfo(
    val currentMs: Long = 0L,
    val durationMs: Long = -1L,      // -1 when unknown (live streams, still preparing)
    val bufferedMs: Long = 0L,        // for "buffer ahead" scrubber indicator
)
```

### AmplitudeInfo

```kotlin
data class AmplitudeInfo(
    val rms: Float,            // 0.0..1.0, perceptual loudness
    val peak: Float,           // 0.0..1.0, for clipping indicators
    val timestampMs: Long,     // playback position at sample time
)
```

### MediaMetadata

```kotlin
data class MediaMetadata(
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    val artworkUrl: String? = null,
    val artworkBytes: ByteArray? = null,   // takes precedence over artworkUrl
    val durationMs: Long? = null,
)
```

Used by `buildPersistentAudioPlayer` for lock-screen / Now Playing / notification.
Ignored by `buildAudioPlayer`.

### PlayerConfig

```kotlin
data class PlayerConfig(
    val positionUpdateIntervalMs: Long = 250L,     // 4 Hz — smooth scrubber UI
    val amplitudeUpdateIntervalMs: Long = 50L,     // 20 Hz — waveform visualizer
    val enableAmplitude: Boolean = false,          // tap audio output for amplitudes
    val initialVolume: Float = 1.0f,
    val initialPlaybackRate: Float = 1.0f,
    val audioFocusStrategy: AudioFocusStrategy = AudioFocusStrategy.Standard,
)
```

### AudioFocusStrategy

```kotlin
enum class AudioFocusStrategy {
    Standard,     // cooperative: request exclusive focus while playing (default for media)
    Exclusive,    // take and hold focus (alarms, navigation prompts)
    Mixed,        // no focus request; audio mixes with other apps (UI SFX, ambient)
}
```

### PlaybackNotification

```kotlin
data class PlaybackNotification(
    val channelId: String,
    val channelName: String,
    val notificationId: Int = PLAYBACK_NOTIFICATION_ID,   // 1001
    val smallIconResId: Int? = null,
) {
    companion object {
        const val PLAYBACK_NOTIFICATION_ID: Int = 1001
    }
}
```

Only used on Android (accepted but ignored on iOS, where Control Center is driven
by `MediaMetadata`).

---

## Usage

```kotlin
// In-app playback
val player = buildAudioPlayer(PlayerConfig(enableAmplitude = true))
player.load(PlaybackSource.Remote("https://example.com/track.m4a"))
player.dispatch(PlaybackCommand.Play)

// Observe state
player.state.collect { state ->
    when (state) {
        PlaybackState.Playing -> showPlaying()
        PlaybackState.Buffering -> showSpinner()
        PlaybackState.Ended -> showReplay()
        is PlaybackState.Error -> showError(state.cause)
        else -> Unit
    }
}

// Scrubber UI
player.position.collect { info ->
    scrubber.update(current = info.currentMs, total = info.durationMs, buffered = info.bufferedMs)
}

// Waveform visualizer (enableAmplitude = true required)
player.amplitudes.collect { amp -> waveform.push(amp.rms) }

// Seek
player.dispatch(PlaybackCommand.SeekTo(30_000L))

// Clean up (suspends until teardown completes; call from a coroutine)
player.release()
```

```kotlin
// Persistent playback with lock-screen controls
val player = buildPersistentAudioPlayer(
    config = PlayerConfig(),
    notification = PlaybackNotification(
        channelId = "playback",
        channelName = "Audio playback",
        smallIconResId = R.drawable.ic_player,
    ),
)
player.load(
    source = PlaybackSource.Remote("https://cdn.example.com/ep-42.mp3"),
    metadata = MediaMetadata(
        title = "Episode 42",
        artist = "My Podcast",
        album = "Season 3",
        artworkBytes = coverPng,
    ),
)
player.dispatch(PlaybackCommand.Play)
// Audio continues when the app is backgrounded.
// Lock-screen / Control Center play/pause/seek buttons are wired automatically.
player.release() // suspends until the service detaches; call from a coroutine
```

---

## Platform Notes

- **Android amplitude**: implemented via an `AudioProcessor` tap on
  `DefaultAudioSink` (pass-through, computes RMS + peak per window).
- **iOS amplitude**: deferred. Reading AVPlayer PCM requires
  `MTAudioProcessingTap` which needs an Objective-C bridge. `amplitudes` is a
  live flow on iOS but never emits. UI code must handle "no amplitude samples"
  as a valid state (e.g. draw a flat line). Tracked for a follow-up.
- **Android engine**: Media3 ExoPlayer with HLS + DASH sources registered.
- **iOS engine**: `AVPlayer` + `AVURLAsset`; periodic time observer for
  position, state polling + `NSNotificationCenter` for terminal events.
- **iOS headers**: `PlaybackSource.Remote.headers` are applied via
  `AVURLAssetHTTPHeaderFieldsKey` on the asset options.
