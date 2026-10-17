---
name: playback
description: Use when implementing audio or video playback — music players, podcast playback, streaming audio/video, in-app video surfaces, lock-screen/Control-Center media controls, or background audio in a KMP project.
user-invocable: true
---

# core:playback + ui:playback — Media Playback

**Modules**: `core:playback` (engine, no UI deps) | `ui:playback` (Compose rendering)
**Artifacts**: `com.ribads.synapse:core-playback` | `com.ribads.synapse:ui-playback`
**Packages**: `com.ribads.synapse.core.playback`, `com.ribads.synapse.core.playback.model`, `com.ribads.synapse.ui.playback`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-playback:<version>")
    implementation("com.ribads.synapse:ui-playback:<version>")   // only for video rendering
}
```

`core:playback` depends on `core:context` (Android) and `core:audio-session` (iOS, see `/synapse:audio-session`). `ui:playback` depends on `core:playback` (api) and Compose.

Supports local files (WAV, MP3, AAC/M4A, OGG, FLAC, MP4, MOV) and remote media (progressive HTTP, HLS, DASH). Format is detected automatically — no explicit format selection.

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.playback.AudioPlayer
import com.ribads.synapse.core.playback.MediaPlayer
import com.ribads.synapse.core.playback.VideoPlayer
import com.ribads.synapse.core.playback.VideoSurface
import com.ribads.synapse.core.playback.buildAudioPlayer
import com.ribads.synapse.core.playback.buildPersistentAudioPlayer
import com.ribads.synapse.core.playback.buildVideoPlayer
import com.ribads.synapse.core.playback.model.AmplitudeConfig
import com.ribads.synapse.core.playback.model.AmplitudeInfo
import com.ribads.synapse.core.playback.model.AudioFocusStrategy
import com.ribads.synapse.core.playback.model.CommandResult
import com.ribads.synapse.core.playback.model.MediaMetadata
import com.ribads.synapse.core.playback.model.PlaybackCommand
import com.ribads.synapse.core.playback.model.PlaybackNotification
import com.ribads.synapse.core.playback.model.PlaybackSource
import com.ribads.synapse.core.playback.model.PlaybackState
import com.ribads.synapse.core.playback.model.PlayerConfig
import com.ribads.synapse.core.playback.model.PositionInfo
import com.ribads.synapse.core.playback.model.VideoSize
import com.ribads.synapse.ui.playback.VideoPlayerSurface
import com.ribads.synapse.ui.playback.VideoResizeMode
```

---

## Entry Points

```kotlin
// In-app audio player. Does NOT survive backgrounding. Use for sound effects,
// notification previews, short clips.
expect fun buildAudioPlayer(config: PlayerConfig = PlayerConfig()): AudioPlayer

// Persistent audio player — survives app backgrounding and integrates with platform
// media controls (Android foreground service + notification; iOS Control Center
// + lock screen via MPNowPlayingInfoCenter / MPRemoteCommandCenter).
expect fun buildPersistentAudioPlayer(
    config: PlayerConfig = PlayerConfig(),
    notification: PlaybackNotification,
): AudioPlayer

// In-app video player. Must be called from the main thread (the rendering output
// is a view-layer object). No persistent video variant yet (Picture-in-Picture is
// a planned follow-up). Nothing in this module pauses it on backgrounding: pause or
// release it from your lifecycle handling (see Platform Notes).
expect fun buildVideoPlayer(config: PlayerConfig = PlayerConfig()): VideoPlayer
```

**Platform requirements for `buildPersistentAudioPlayer`:**
- **Android**: Nothing to register. The service entry and the
  `FOREGROUND_SERVICE` / `FOREGROUND_SERVICE_MEDIA_PLAYBACK` permissions are
  declared in this library's manifest. Media-session notifications are exempt
  from the `POST_NOTIFICATIONS` runtime permission.
- **iOS**: The consuming app must add `audio` to `UIBackgroundModes` in its
  `Info.plist`.

**Android persistent lifecycle:** building the player only binds to the
`MediaSessionService`; it does not start a foreground service. Media3 posts the
media notification (play/pause/seek) once a loaded source is prepared, keeps the
service in the foreground while playback runs, and drops it back to the background
up to 10 minutes after playback pauses or ends. Only one persistent player at a
time: the service owns a single engine, so a second `buildPersistentAudioPlayer`
shares it and releasing either one stops the service.

**iOS audio session:** every iOS player (audio, persistent, video) activates the
shared `AVAudioSession` when it is built and holds it until `release()`, not only
while playing. With `Standard`/`Exclusive` focus, other apps' audio stops as soon
as the player is constructed. Build players when you are about to play and release
them when done.

---

## MediaPlayer

Base contract shared by audio and video. Playback semantics — sources, commands,
state machine — are identical across both.

```kotlin
interface MediaPlayer {
    val state: StateFlow<PlaybackState>
    val position: StateFlow<PositionInfo>
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
- Observation → the hot flows drive UI (scrubber, level meter, play/pause button)

Runtime errors (network, decode) surface on `state` as `PlaybackState.Error`.
`CommandResult.Failure` is reserved for command-acceptance rejection:
- `dispatch` rejects only an out-of-range value (`SetVolume` outside `0.0..1.0`,
  `SetPlaybackRate` outside `0.25..4.0`) or a released player. It does not check
  whether a source is loaded.
- `load` rejects a released player and, on iOS, a remote URL that cannot be parsed
  (Android reports an unusable URL as `PlaybackState.Error` instead).

## AudioPlayer

```kotlin
interface AudioPlayer : MediaPlayer {
    // Hot flow of amplitude samples for visualization. Only emits when
    // PlayerConfig.amplitude is set and audio is playing. Android only:
    // never emits on iOS.
    val amplitudes: SharedFlow<AmplitudeInfo>
}
```

## VideoPlayer

```kotlin
interface VideoPlayer : MediaPlayer {
    // Intrinsic dimensions of the loaded video track; null while unknown and
    // for audio-only sources. Resets to null on every load().
    val videoSize: StateFlow<VideoSize?>

    // Opaque platform rendering output, owned by the player. Render it with
    // ui:playback's VideoPlayerSurface — do not touch it directly.
    val surface: VideoSurface
}
```

`VideoSurface` is an `expect class` with no common members — on Android it holds
the engine's `SurfaceView`, on iOS a `UIView` hosting an `AVPlayerLayer`. Only
`ui:playback` reads through it.

---

## Compose rendering (ui:playback)

```kotlin
@Composable
fun VideoPlayerSurface(
    player: VideoPlayer,
    modifier: Modifier = Modifier,
    resizeMode: VideoResizeMode = VideoResizeMode.Fit,
)

enum class VideoResizeMode {
    Fit,      // whole frame visible; letterbox/pillarbox on mismatch
    Crop,     // cover the bounds; overflow clipped
    Stretch,  // distort to exactly fill the bounds
}
```

- The surface renders black until the engine delivers the first frame.
- One surface per player: compose `VideoPlayerSurface` at most once per player
  at a time — two simultaneous compositions fight over the platform view.
- The composable has no chrome. Overlay controls/spinners/errors yourself by
  observing `player.state` in a `Box` above the surface.

---

## Models

### PlaybackCommand

```kotlin
sealed class PlaybackCommand {
    data object Play : PlaybackCommand()                       // from Ended, restarts from the beginning
    data object Pause : PlaybackCommand()
    data object Stop : PlaybackCommand()                       // pauses, resets position to 0, state -> Ready
    data class SeekTo(val positionMs: Long) : PlaybackCommand()
    data class SetVolume(val volume: Float) : PlaybackCommand()       // 0.0..1.0
    data class SetPlaybackRate(val rate: Float) : PlaybackCommand()   // 0.25..4.0
}
```

`load` is intentionally NOT a command — it is lifecycle on `MediaPlayer.load`.

### PlaybackState

```kotlin
sealed class PlaybackState {
    data object Idle : PlaybackState()           // no source loaded (initial state)
    data object Loading : PlaybackState()        // initial buffering
    data object Ready : PlaybackState()          // prepared, not yet playing; also the state after Stop
    data object Playing : PlaybackState()
    data object Paused : PlaybackState()
    data object Buffering : PlaybackState()      // stalled mid-stream (remote only)
    data object Ended : PlaybackState()          // reached end; Play restarts from 0, SeekTo/Stop also leave it
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
    val bufferedMs: Long = 0L,        // position buffered up to (absolute, >= currentMs)
)
```

`bufferedMs` is a position from the start, not a length ahead of `currentMs`. It
equals `durationMs` once the whole source is loaded. On iOS it is the end of the
`AVPlayerItem.loadedTimeRanges` range that contains the playhead, refreshed with
each position tick (so it does not advance while paused).

### VideoSize

```kotlin
data class VideoSize(
    val width: Int,                    // frame width in pixels
    val height: Int,                   // frame height in pixels
    val pixelAspectRatio: Float = 1f,  // non-1 for anamorphic streams (Android only)
) {
    val aspectRatio: Float             // display ratio (width * par / height); 0 when degenerate
}
```

Lay out with `aspectRatio`, which is correct on both platforms. Android reports
the decoded frame size plus the stream's pixel aspect ratio. iOS reports
`AVPlayerItem.presentationSize`, which already has the pixel aspect ratio applied,
so `pixelAspectRatio` is always `1` there.

### AmplitudeInfo

```kotlin
data class AmplitudeInfo(
    val rms: Float,            // 0.0..1.0, perceptual loudness
    val peak: Float,           // 0.0..1.0, for clipping indicators
    val timestampMs: Long,     // wall-clock epoch ms when computed (not a playback position)
)
```

Samples are computed as audio is decoded, slightly ahead of when it is heard.

### MediaMetadata

```kotlin
data class MediaMetadata(
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    val artworkUrl: String? = null,        // http, https or file URL; fetched in the background
    val artworkBytes: ByteArray? = null,   // takes precedence over artworkUrl
    val durationMs: Long? = null,
)
```

Used by `buildPersistentAudioPlayer` for lock-screen / Now Playing / notification.
Ignored by the in-app players. `artworkUrl` is fetched after `load` on both
platforms; a failed fetch leaves the lock screen or notification without artwork.

### PlayerConfig

```kotlin
data class PlayerConfig(
    val positionUpdateIntervalMs: Long = 250L,     // 4 Hz — smooth scrubber UI
    val initialVolume: Float = 1.0f,
    val initialPlaybackRate: Float = 1.0f,
    val audioFocusStrategy: AudioFocusStrategy = AudioFocusStrategy.Standard,
    val amplitude: AmplitudeConfig? = null,        // set to enable the amplitude tap (audio players only)
)
```

### AmplitudeConfig

```kotlin
data class AmplitudeConfig(
    val updateIntervalMs: Long = 50L,   // 20 Hz — waveform visualizer cadence
)
```

Presence on `PlayerConfig.amplitude` enables the audio-output tap; `null` leaves
the pipeline untouched. Video players ignore it, and iOS players never emit
samples (see Platform Notes).

### AudioFocusStrategy

```kotlin
enum class AudioFocusStrategy {
    Standard,     // cooperative focus; other apps' audio stops (default for media)
    Exclusive,    // currently identical to Standard on both platforms
    Mixed,        // no focus request; audio mixes with other apps (UI SFX, ambient)
}
```

- **Standard**: Android requests `AUDIOFOCUS_GAIN` when playback starts and keeps
  it while paused. The player pauses when another app takes focus, pauses and
  resumes around a transient interruption, and ducks for notification sounds. iOS
  holds a non-mixable `Playback` session from construction until `release()`;
  interruptions such as calls pause playback, which does not resume on its own.
- **Exclusive**: behaves exactly like `Standard`. Neither platform lets an app keep
  audio against calls, alarms or other apps taking focus, so there is no stronger
  guarantee to map it to. Do not rely on it for alarms or navigation prompts.
- **Mixed**: Android makes no focus request; iOS sets `MixWithOthers`.

Applies to video players too: a video's audio track competes for focus the same
way music does.

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
by `MediaMetadata`). If no channel with `channelId` exists, the service creates it
with `IMPORTANCE_LOW` and `channelName`; create the channel yourself first to choose
a different importance or add a description.

---

## Usage

```kotlin
// In-app audio playback
val player = buildAudioPlayer(PlayerConfig(amplitude = AmplitudeConfig()))
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

// Waveform visualizer (config.amplitude required)
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

```kotlin
// Video playback in Compose
val scope = rememberCoroutineScope()
val player = remember { buildVideoPlayer() }   // main thread
LaunchedEffect(player) {
    player.load(PlaybackSource.Remote("https://cdn.example.com/trailer.mp4"))
    player.dispatch(PlaybackCommand.Play)
}
DisposableEffect(player) {
    onDispose { scope.launch { player.release() } }
}

Box(Modifier.fillMaxSize()) {
    VideoPlayerSurface(
        player = player,
        modifier = Modifier.fillMaxSize(),
        resizeMode = VideoResizeMode.Fit,
    )
    val state by player.state.collectAsState()
    if (state is PlaybackState.Buffering) {
        CircularProgressIndicator(Modifier.align(Alignment.Center))
    }
}

// Inline player card sized to the video's own proportions (16:9 until known)
val videoSize by player.videoSize.collectAsState()
VideoPlayerSurface(
    player = player,
    modifier = Modifier
        .fillMaxWidth()
        .aspectRatio(videoSize?.aspectRatio?.takeIf { it > 0f } ?: 16f / 9f),
)
```

---

## Platform Notes

- **Android engine**: Media3 ExoPlayer with HLS + DASH sources registered. One
  engine backs both audio and video players; video renders into a `SurfaceView`
  owned by the player.
- **iOS engine**: `AVPlayer` + `AVURLAsset`; periodic time observer for
  position, state polling + `NSNotificationCenter` for terminal events. Video
  renders through an `AVPlayerLayer` hosted in the player-owned view.
- **Video backgrounding**: nothing in this module pauses video when the app
  backgrounds. Pause or release the player from your lifecycle handling (for
  example `ON_STOP`); otherwise, on Android, the audio track keeps playing. iOS
  pauses a player whose video is on screen when the app backgrounds.
  Picture-in-Picture and persistent video are follow-ups.
- **Android amplitude**: implemented via an `AudioProcessor` tap on
  `DefaultAudioSink` (pass-through, computes RMS + peak per window).
- **iOS amplitude**: not implemented. Reading AVPlayer PCM requires an
  `MTAudioProcessingTap` (unavailable for HLS sources). `amplitudes` is a live
  flow on iOS but never emits. UI code must handle "no amplitude samples" as a
  valid state (e.g. draw a flat line).
- **iOS Now Playing**: the persistent player reports a playback rate of `0` to
  `MPNowPlayingInfoCenter` while not playing, so the lock-screen scrubber stops
  while paused.
- **iOS video size**: AVFoundation exposes no notification for
  presentation-size resolution, so `videoSize` rides the engine's 100 ms state
  poll; expect it to resolve within a tick of `Ready`.
- **iOS headers**: `PlaybackSource.Remote.headers` are applied via
  `AVURLAssetHTTPHeaderFieldsKey` on the asset options.
