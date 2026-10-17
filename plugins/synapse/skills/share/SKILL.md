---
name: share
description: Use when implementing native sharing — share text, links, images, or video to WhatsApp, SMS/MMS, Instagram, Facebook, TikTok, X, or the system share sheet in a KMP project. Typed results, per-target capability queries, no third-party SDKs.
user-invocable: true
---

# core:share — Native Sharing

**Module**: `core:share` | **Artifact**: `com.ribads.synapse:core-share`
**Packages**: `com.ribads.synapse.core.share`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-share:<version>")
}
```

Depends on `core:context` (Android only — auto-initialized via ContentProvider, nothing to call).

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.share.ShareCompletion
import com.ribads.synapse.core.share.ShareContent
import com.ribads.synapse.core.share.ShareContentKind
import com.ribads.synapse.core.share.ShareMedia
import com.ribads.synapse.core.share.ShareResult
import com.ribads.synapse.core.share.ShareTarget
import com.ribads.synapse.core.share.Sharer
import com.ribads.synapse.core.share.buildSharer
import com.ribads.synapse.core.share.kind
```

---

## When to use

- Share buttons targeting a specific app (WhatsApp/Instagram/X/… rows in your own UI)
- The system share sheet, as a primary destination or as the fallback when a direct target fails
- Hiding or showing per-app share buttons via capability + installation queries
- Sharing links whose pages carry OpenGraph tags — receiving apps render the preview

Do **not** use for:

- In-app messaging or uploads to your own backend — this module hands content to *other* apps
- Guaranteed-delivery flows — `Success(HANDED_OFF)` only confirms the hand-off; whether the user actually posts/sends is unobservable
- Full-fidelity Facebook/TikTok share dialogs — those require the vendor SDKs, which this module deliberately excludes

---

## API

```kotlin
interface Sharer {
    /**
     * Shares content to a target. Suspends until the platform hand-off
     * completes (and, where observable, until the user finishes or cancels).
     * Must be called while the app is foregrounded with a resumed
     * Activity / key window.
     */
    suspend fun share(content: ShareContent, target: ShareTarget): ShareResult

    /**
     * Static capability: can this library deliver this kind to this target on
     * the current platform, assuming the app is installed? Pure and
     * synchronous — safe to call while composing UI.
     */
    fun supports(target: ShareTarget, kind: ShareContentKind): Boolean

    /**
     * True when the target is installed and supports at least one content
     * kind on this platform. Always true for SYSTEM_SHEET. On iOS this uses
     * canOpenURL — see Platforms for the required Info.plist entries.
     */
    suspend fun isAvailable(target: ShareTarget): Boolean

    /** Targets that both support the kind and are installed, in declaration order. */
    suspend fun availableTargets(kind: ShareContentKind): List<ShareTarget>

    companion object {
        val shared: Sharer by lazy { buildSharer() }
    }
}

fun buildSharer(): Sharer

enum class ShareTarget { WHATSAPP, SMS, INSTAGRAM, FACEBOOK, TIKTOK, X, SYSTEM_SHEET }

sealed interface ShareContent {
    /** Plain text. */
    data class Text(val text: String) : ShareContent

    /**
     * A URL. Receiving apps that understand links render an OpenGraph preview
     * of the page. [message] is optional accompanying text, dropped by targets
     * that strip it (e.g. Facebook keeps only the URL).
     */
    data class Link(val url: String, val message: String? = null) : ShareContent

    /** One or more images. Targets that only accept a single image reject counts > 1 with UnsupportedContent. */
    data class Images(val images: List<ShareMedia>, val caption: String? = null) : ShareContent {
        constructor(image: ShareMedia, caption: String? = null)
    }

    /** A single video. */
    data class Video(val video: ShareMedia, val caption: String? = null) : ShareContent
}

/**
 * A media file to share. [location] is an absolute file path on both
 * platforms; on Android it may also be an existing content:// URI. A publicly
 * reachable http(s) URL is accepted too: it is downloaded into the module's
 * share cache before hand-off (keyed by URL, so repeat shares reuse the
 * file), and a failed download surfaces as MediaUnavailable. Local files are
 * exposed to receiving apps through the module's own FileProvider —
 * no consumer setup required.
 */
data class ShareMedia(
    val location: String,
    /** MIME type; inferred from the file extension when null. */
    val mimeType: String? = null,
)

/** The shape of a ShareContent, used for capability queries. */
enum class ShareContentKind { TEXT, LINK, IMAGE, VIDEO }

val ShareContent.kind: ShareContentKind

sealed interface ShareResult {
    /** The content reached the target. */
    data class Success(val completion: ShareCompletion) : ShareResult

    /**
     * The user backed out. Only reported where the platform signals it
     * (iOS share sheet, iOS SMS composer); Android gives no such signal.
     */
    data object Cancelled : ShareResult

    sealed interface Failure : ShareResult {
        /** Target app is not installed (or, for SMS, the device cannot send messages). */
        data object AppNotInstalled : Failure

        /** This target cannot receive this content kind on this platform. Query Sharer.supports up front. */
        data object UnsupportedContent : Failure

        /** The content itself is malformed (blank text, non-http(s) URL, empty image list). */
        data class InvalidContent(val reason: String) : Failure

        /** A ShareMedia.location does not exist, could not be read, or a remote URL could not be downloaded. */
        data class MediaUnavailable(val location: String) : Failure

        /** The platform launch itself failed (no resumed Activity / no view controller / scheme open rejected). */
        data class LaunchFailed(val message: String? = null) : Failure
    }
}

enum class ShareCompletion {
    /** Content was handed to the target app; delivery/posting is unobservable. */
    HANDED_OFF,

    /** The platform confirmed the user completed the share. */
    CONFIRMED,
}
```

### Semantics

- **No exceptions, no auto-fallback** — `share()` always returns a `ShareResult`. Compose fallback at the call site, typically by retrying with `ShareTarget.SYSTEM_SHEET` (see Usage).
- **Gate order** — `InvalidContent` → `UnsupportedContent` → `AppNotInstalled` → delivery result. Capability is checked before installation, so Facebook-on-iOS returns `UnsupportedContent` even when uninstalled — installing would not fix it.
- **Remote media is materialized after the install gate** — http(s) media locations are downloaded into the share cache (URL-keyed, reused for ~24h) just before delivery, so nothing downloads for a share that cannot launch. The URL must be publicly fetchable: no auth headers or cookies are sent, and the host app's cleartext/ATS policy applies (prefer https). A failed download returns `MediaUnavailable(url)` and nothing launches.
- **`Success(HANDED_OFF)` vs `Success(CONFIRMED)`** — Android intents and iOS URL-scheme/Stories launches only confirm the hand-off; the iOS share sheet and iOS SMS composer confirm user completion. `Cancelled` is reported only where the platform signals it.
- **Captions and messages are best-effort** — Instagram and TikTok drop them; Facebook strips all prefilled text except a bare URL. That is documented target behavior, not a failure.
- **`supports()` is pure** — it answers from a static per-platform matrix and never touches the platform; `isAvailable()` adds the installation check.

### Capability matrix

| Target | Android | iOS | Notes |
|---|---|---|---|
| `WHATSAPP` | text, link, image, video | text, link | iOS via `whatsapp://send?text=`; media on iOS only through the sheet. Android falls back to WhatsApp Business if only it is installed. |
| `SMS` | text, link, image, video (MMS) | text, link, image, video | Android media goes to the default SMS app; iOS uses the Messages composer (CONFIRMED/Cancelled observable). |
| `INSTAGRAM` | image, video (feed composer) | image, video (Stories) | No text/links. Captions dropped. Best native surface differs per platform by design; iOS accepts a single media item only. |
| `FACEBOOK` | link, image, video | — | Facebook strips prefilled text everywhere; `Link` sends the URL only (OG preview). No SDK-free path on iOS. |
| `TIKTOK` | image, video (best-effort) | — | No SDK-free path on iOS. |
| `X` | text, link, image, video | text, link | iOS via `twitter://post?message=` (unowned scheme — expect `LaunchFailed` if it breaks, and fall back). |
| `SYSTEM_SHEET` | all | all | Android success is always `HANDED_OFF` (the chooser gives no result); iOS reports `CONFIRMED`/`Cancelled`. |

---

## Usage

### Direct share with sheet fallback

```kotlin
suspend fun shareToWhatsApp(link: ShareContent.Link): ShareResult {
    val result = Sharer.shared.share(link, ShareTarget.WHATSAPP)
    return when (result) {
        is ShareResult.Failure.AppNotInstalled,
        is ShareResult.Failure.LaunchFailed,
        -> Sharer.shared.share(link, ShareTarget.SYSTEM_SHEET)

        else -> result
    }
}
```

### Building a share row from availability

```kotlin
// In the Interactor: resolve once, render buttons only for what can succeed.
val targets: List<ShareTarget> = sharer.availableTargets(ShareContentKind.IMAGE)
```

### Link with OpenGraph preview

```kotlin
sharer.share(
    ShareContent.Link(
        url = "https://example.com/article/42",
        message = "Worth a read",
    ),
    ShareTarget.SYSTEM_SHEET,
)
```

### Image with caption

```kotlin
sharer.share(
    ShareContent.Images(ShareMedia("/data/user/0/…/files/render.png"), caption = "Made with Outside"),
    ShareTarget.INSTAGRAM,
)
```

### Remote image (downloaded for you)

```kotlin
// http(s) locations are fetched into the share cache before hand-off;
// repeat shares of the same URL reuse the cached file.
sharer.share(
    ShareContent.Images(ShareMedia("https://cdn.example.com/products/42.jpg"), caption = "Look at this"),
    ShareTarget.INSTAGRAM,
)
```

### Hiding unsupported buttons at compose time

```kotlin
// supports() is synchronous and platform-static: TikTok never shows on iOS.
if (sharer.supports(ShareTarget.TIKTOK, ShareContentKind.VIDEO)) {
    // render the TikTok button
}
```

---

## DI wiring (kotlin-inject)

```kotlin
import com.ribads.synapse.core.discopes.SingletonScope
import com.ribads.synapse.core.share.Sharer
import com.ribads.synapse.core.share.buildSharer
import me.tatarka.inject.annotations.Provides

interface ShareComponent {

    @Provides
    @SingletonScope
    fun provideSharer(): Sharer = buildSharer()
}
```

The sharer is stateless and cheap to construct; a singleton is a convenience, not a requirement.

---

## Lifecycle & scoping

- Stateless — no `release()`, no owned scope.
- Call `share()` only while the app is foregrounded: it needs a resumed Activity (Android) or a key window (iOS) and returns `LaunchFailed` otherwise.
- `share()` suspends until the hand-off (and user completion where observable). Cancelling the calling scope dismisses the iOS share sheet / SMS composer; on Android the launched app is outside the caller's control.

---

## Platforms

- **Android**: minSdk 24. Zero consumer setup: the module manifest ships the Android 11+ `<queries>` package-visibility block for all six apps, its own FileProvider (`${applicationId}.synapse.share.fileprovider`), and `android.permission.INTERNET` for remote media downloads, all merged into the app's manifest. Local paths outside app storage and foreign `content://` URIs are copied into a provider-served cache (cleaned after 24h) before sharing; remote http(s) media downloads land in the same cache. Android 9+ blocks cleartext http downloads by default, and http-to-https redirects are not followed: use https URLs. Requires `core:context` (auto-initialized).
- **iOS** (arm64, simulatorArm64): the host app must declare the query schemes in `Info.plist`, or `isAvailable`/direct shares report `AppNotInstalled`:

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>whatsapp</string>
    <string>instagram-stories</string>
    <string>twitter</string>
</array>
```

Instagram Stories sharing places the media on the general pasteboard (5-minute expiration) per Meta's documented contract; no Info.plist key is needed for that beyond the scheme above.
