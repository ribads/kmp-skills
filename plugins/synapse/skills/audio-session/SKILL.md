---
name: audio-session
description: Use when coordinating the iOS AVAudioSession (category/activation) across multiple audio features so recording and playback share one session without clobbering each other. iOS-only; used internally by core:record and core:playback.
user-invocable: true
---

# core:audio-session — iOS AVAudioSession Coordination

**Module**: `core:audio-session` | **Artifact**: `com.ribads.synapse:core-audio-session`
**Packages**: `com.ribads.synapse.core.audiosession`; see [Imports](#imports)

```kotlin
iosMain.dependencies {
    implementation("com.ribads.synapse:core-audio-session:<version>")
}
```

The single owner of `AVAudioSession` configuration across Synapse audio modules. iOS's audio
session is a process-global shared resource: the last component to call `setCategory` wins, so a
recorder starting up can silently disable an active player. This coordinator computes the union of
active uses, applies the most permissive category + options, and only deactivates the session when
the last holder releases its token. `core:record` and `core:playback` use it internally — you
rarely need it directly.

Android has no equivalent (it uses per-component audio focus), so this module has no Android target.

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.audiosession.AudioSessionCoordinator // iosMain only
import com.ribads.synapse.core.audiosession.AudioSessionException // iosMain only
```

---

## API

```kotlin
object AudioSessionCoordinator {
    enum class Use {
        Record,            // PlayAndRecord, default to speaker
        BackgroundRecord,  // PlayAndRecord, speaker, allow Bluetooth (needs `audio` UIBackgroundMode)
        Playback,          // Playback, no microphone
        MixedPlayback,     // Playback + MixWithOthers
    }

    class Token  // opaque receipt for an active acquisition; pass back to release()

    /**
     * Acquire the session for [use]; reconciles with any other active uses, applies the most
     * permissive category + options, and activates the session. Returns a [Token] for [release].
     * @throws AudioSessionException if the category change or activation is rejected (no token is
     *   registered in that case, so a returned Token always reflects an active session).
     */
    fun acquire(use: Use): Token

    /** Release a token; reconfigures for the remaining uses, or deactivates the session if it was
     *  the last. No-op if already released. Best-effort: never throws. */
    fun release(token: Token)
}

/** Raised when AVAudioSession rejects a category change or activation. Carries the platform NSError. */
class AudioSessionException : Exception {
    val nsError: platform.Foundation.NSError?
}
```

Thread-safe via `NSLock`; callable from any dispatcher.

---

## Usage

```kotlin
// In an iOS recorder / player actual:
private var token: AudioSessionCoordinator.Token? = null

fun start() {
    token = AudioSessionCoordinator.acquire(AudioSessionCoordinator.Use.Record)
    // ... configure AVAudioEngine / AVPlayer ...
}

fun stop() {
    token?.let { AudioSessionCoordinator.release(it) }
    token = null
}
```

Acquire when starting audio I/O, release on teardown. Multiple holders coexist (e.g. a player and
a recorder): the coordinator selects `PlayAndRecord` while both are active and reverts when one
releases. Handle (or deliberately propagate) `AudioSessionException` from `acquire` — a failed
activation means another app holds an exclusive, non-mixable session.
