---
name: file-system
description: Use when implementing file picking, photo or video picking, camera capture (photo or video), document selection, listing the device's recent photos, or saving photos and videos to the photo library in a KMP project.
user-invocable: true
---

# core:file — File Picker & File Operations

**Module**: `core:file` | **Artifact**: `com.ribads.synapse:core-file`
**Packages**: `com.ribads.synapse.core.file`, `com.ribads.synapse.core.file.dto`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-file:<version>")
}
```

Depends on `core:context` and `core:permissions`.

## Platform setup

**Android**: nothing to declare. The module manifest registers its own FileProvider (`com.ribads.synapse.core.file.internal.SynapseFileProvider`, authority `${applicationId}.synapse.file.fileprovider`, paths `@xml/synapse_file_paths`), which camera captures are written through. It never collides with a FileProvider the app or `core:share` declares. An app that declared a `${applicationId}.provider` FileProvider only for `core:file` can remove it.

`Capture` launches the system camera app, which holds the camera permission itself. But when the app's own manifest declares `android.permission.CAMERA`, Android refuses to launch the capture intent until that permission is granted, and the request resolves to `Failure`: request `PermissionsRequest.Camera` (`core:permissions`) first.

**iOS**: `Info.plist` keys and runtime permissions per request:

| Request | `Info.plist` keys | Runtime permission |
|---------|-------------------|--------------------|
| `Media` | none | none (`PHPickerViewController` runs out of process) |
| `Capture(Photo)` | `NSCameraUsageDescription`, `NSPhotoLibraryAddUsageDescription` | camera: prompted by the capture itself. Add-only photo library: call `PhotoSaver.create().requestPhotoLibraryPermission()` before capturing |
| `Capture(Video)` | the above plus `NSMicrophoneUsageDescription` (the camera records audio) | as `Capture(Photo)`; the camera UI prompts for the microphone |
| `Document` | none | none |

Captures are saved to the photo library so the result is a `PHAsset` identifier. Capture never prompts for photo library access: without add-only access granted beforehand the save fails and the request resolves to `Failure` after the user has taken the shot. A denied camera, or a device with no camera (the simulator), resolves to `Failure` without presenting anything.

Resolving a `DeviceAsset` through `PHAsset` (as ui:element `Image.LocalIdentifier` does) reads the library, which needs read access: `NSPhotoLibraryUsageDescription` plus a granted `PermissionsRequest.MediaStorage`. For a gallery pick without that access, read the bytes with `LocalAssetInMemoryProvider.getImage`.

## Imports

Types live in more than one package. Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.file.FilePicker
import com.ribads.synapse.core.file.FilePickerRequest
import com.ribads.synapse.core.file.FilePickerResult
import com.ribads.synapse.core.file.ImageFileSize // iosMain only
import com.ribads.synapse.core.file.LocalAssetInMemoryProvider // iosMain only
import com.ribads.synapse.core.file.MediaReference
import com.ribads.synapse.core.file.PhotoLibrary
import com.ribads.synapse.core.file.PhotoSaver // iosMain only
import com.ribads.synapse.core.file.buildFilePicker
import com.ribads.synapse.core.file.dto.IosPickerResult // iosMain only
import com.ribads.synapse.core.file.dto.PermissionResult // iosMain only
```

---

## FilePicker (Common API)

```kotlin
interface FilePicker {
    // onImporting: once the user has chosen and the picker has closed, before an import copies (see "Importing picks")
    suspend fun execute(request: FilePickerRequest, onImporting: () -> Unit = {}): FilePickerResult

    companion object {
        val shared: FilePicker
    }
}

expect fun buildFilePicker(): FilePicker
```

`execute` presents the system UI and suspends until the user finishes with it. It switches to the main thread itself, so it can be called from any dispatcher. Platform errors (no live `ComponentActivity` on Android, no app to handle the intent, nothing to present from on iOS, a failed library save) resolve to `Failure` and are logged (`Log.e` with tag `FilePicker` on Android, `NSLog` on iOS). Cancelling the caller propagates the `CancellationException` rather than returning a result: iOS dismisses the picker, while Android cannot close the launched system activity and discards its result.

On iOS every picker presents from the key window's top-most presented view controller, so it works while a sheet or another modal is showing. When UIKit cannot present it (no key window, or the top controller is mid-transition), the request resolves to `Failure` instead of suspending forever.

### FilePickerRequest

```kotlin
sealed class FilePickerRequest {
    // Pick existing photos, videos, or both. quantity = the most items the user may select:
    // 1 opens a single-item picker, higher opens a multi-select picker capped at that many.
    // importTo copies every pick into that directory (see "Importing picks").
    // Throws IllegalArgumentException when types is empty or quantity < 1.
    data class Media(
        val types: Set<MediaType>,
        val quantity: Int = 1,
        val importTo: String? = null,
    ) : FilePickerRequest() {
        constructor(type: MediaType, quantity: Int = 1, importTo: String? = null)   // one type
    }
    // Take a photo or record a video with the system camera UI.
    data class Capture(val type: MediaType) : FilePickerRequest()
    data class Document(val mimeTypes: List<String> = listOf("application/pdf")) : FilePickerRequest()

    enum class MediaType { Photo, Video }
}
```

`Media.types` decides what the picker offers: `setOf(Photo)` or `setOf(Video)` alone, or both together (Android `ImageAndVideo`, iOS `any(of: [images, videos])`).

`Media.quantity` is enforced as a selection limit on both platforms:
- **Android**: `1` uses `PickVisualMedia`; higher uses `PickMultipleVisualMedia(maxItems = quantity)`. The system photo picker also caps it at its own maximum (`MediaStore.getPickImagesMaxLimit()`). On devices without the photo picker the document-picker fallback cannot limit the selection, so the result is truncated to the first `quantity` items.
- **iOS**: `PHPickerConfiguration.selectionLimit = quantity`.

### Importing picks

With `Media.importTo`, every pick is copied into that directory (created when missing) and returned as `MediaReference.Uri` holding the copy's absolute path, named by a fresh id and its type's extension. Nothing then needs library access or a picker grant, so an app can keep picks in its own storage:

- **Android**: copied through the content resolver, so the copy outlives the photo picker's temporary read grant. The extension comes from the MIME type (`.bin` when it has none).
- **iOS**: the picker runs without a photo library (`PHPickerConfiguration()`), in the compatible representation mode, and each item provider's file representation is copied before the system deletes it: photos arrive as JPEG and videos as H.264, which every image and video stack reads. No Photos permission is needed.
- All or nothing: a failure or a cancellation part of the way through deletes the copies already made, and the request resolves to `Failure` (or propagates the cancellation).
- Progress: copying a long video can take seconds after the picker has closed. `execute`'s `onImporting` is called once, on the main thread, when the user has chosen and before the copying starts (never for a request without `importTo`, or one the user cancels), which is the moment to show that the app is still working.

### FilePickerResult

```kotlin
sealed class FilePickerResult {
    data class Success(val results: List<MediaReference>) : FilePickerResult()
    data object Failure : FilePickerResult()   // an error occurred
    data object Cancelled : FilePickerResult()  // user dismissed the picker
}

sealed interface MediaReference {
    val value: String  // stable, serialisable identity: a list, selection or upload key
    // A directly loadable URI/path: Android media/capture/document, and iOS documents.
    data class Uri(override val value: String) : MediaReference
    // A photo-library handle to resolve via the asset loader: iOS gallery/camera
    // picks return a PHAsset localIdentifier (render with ui:element Image.LocalIdentifier).
    data class DeviceAsset(override val value: String) : MediaReference
}
```

`Cancelled` is returned on both platforms when the user backs out of the picker; `Failure` is reserved for actual errors. `Document` always yields `MediaReference.Uri`; `Media`/`Capture` yield `MediaReference.Uri` on Android and `MediaReference.DeviceAsset` on iOS, for photos and videos alike.

What each result points at:

| Request | Android (`MediaReference.Uri`) | iOS |
|---------|-----------------------------|-----|
| `Media` | photo-picker `content://` URI | `DeviceAsset`: the picked asset's `PHAsset` local identifier |
| `Media` with `importTo` | absolute path of the copy in `importTo` | `Uri`: absolute path of the copy in `importTo` |
| `Capture(Photo)` | `content://<applicationId>.synapse.file.fileprovider/...` URI of a `.jpg` in the app-specific `getExternalFilesDir(Environment.DIRECTORY_PICTURES)` | `DeviceAsset` of the photo saved to the library |
| `Capture(Video)` | the same provider, a `.mp4` in `getExternalFilesDir(Environment.DIRECTORY_MOVIES)` | `DeviceAsset` of the video saved to the library |
| `Document` | `content://` URI with a persisted read grant | `Uri`: path of a copy in the app sandbox |

Android capture files stay until the app deletes them; a cancelled or failed capture deletes its empty file. iOS removes the camera's temporary movie file once the video is in the library.

---

## PhotoLibrary (Common API)

```kotlin
interface PhotoLibrary {
    // The newest photos first, at most limit. Throws IllegalStateException without
    // PermissionsRequest.PhotoLibrary, IllegalArgumentException when limit < 1.
    suspend fun recentPhotos(limit: Int): List<MediaReference>

    companion object {
        val shared: PhotoLibrary
    }
}
```

Reads the device's photo collection directly, for an in-app gallery rather than a system picker. It needs `PermissionsRequest.PhotoLibrary` granted first (`core:permissions`; Android manifest `READ_MEDIA_IMAGES` plus `READ_EXTERNAL_STORAGE` with `maxSdkVersion="32"`, iOS `NSPhotoLibraryUsageDescription`). It checks the grant itself and throws rather than return a partial library: without it, Android 10+ would list only the app's own photos and iOS nothing.

- **Android**: `MediaStore.Images` by `DATE_ADDED` descending, on `Dispatchers.IO`; `MediaReference.Uri` content URIs.
- **iOS**: `PHAsset` images by `creationDate` descending, with `fetchLimit = limit`; `MediaReference.DeviceAsset` identifiers, read through `PHAsset` like a capture result.

Bound `limit` to what a screen can show: the list is held in memory.

---

## iOS-Only APIs

```kotlin
// Pixel bounds. Throws IllegalArgumentException unless width > 0 and height > 0.
data class ImageFileSize(val width: Double, val height: Double)

interface LocalAssetInMemoryProvider {
    // Repeatable: reading a pick keeps it, so a thumbnail and the upload can share it.
    suspend fun getImage(localIdentifier: String, size: ImageFileSize? = null): ByteArray?
    fun save(localIdentifier: String, pickerResult: PHPickerResult)
    fun remove(localIdentifier: String)
    fun clear()

    companion object {
        val shared: LocalAssetInMemoryProvider
    }
}

interface PhotoSaver {
    fun getPhotoLibraryPermissionStatus(): PermissionResult
    suspend fun requestPhotoLibraryPermission(): Boolean
    suspend fun saveImage(image: UIImage): Result<String?>
    suspend fun saveVideo(fileUrl: NSURL): Result<String?>

    companion object {
        fun create(): PhotoSaver
    }
}
```

`LocalAssetInMemoryProvider` holds the `PHPickerResult` of every `Media` pick (the 16 most recently used), keyed by its local identifier. Reading a pick keeps it and makes it the most recently used; `remove` and `clear` release picks early. `getImage` returns null when the identifier was never cached, was removed, has been evicted, or has no image representation (video picks). With `size = null` the bytes are the image as encoded in the library (for example HEIC). With a `size` the image is scaled down to fit within `size` pixels, aspect ratio kept and never upscaled, and returned as JPEG (transparency is not preserved).

`PhotoSaver` uses add-only photo library access (`NSPhotoLibraryAddUsageDescription`):
- `getPhotoLibraryPermissionStatus()`: `Granted` for authorized or limited add-only access, otherwise `NotGranted`. Never prompts.
- `requestPhotoLibraryPermission()`: prompts when undetermined and returns whether access is granted. When it is not, it also opens the app's page in Settings.
- `saveImage` / `saveVideo`: add the photo, or copy the video file at `fileUrl` (left in place), to the library and return the new asset's `localIdentifier`. Both fail without prompting when add-only access is not granted.

`PermissionResult` and `IosPickerResult` live in the `com.ribads.synapse.core.file.dto` package; the other iOS types are in `com.ribads.synapse.core.file`.

```kotlin
package com.ribads.synapse.core.file.dto

enum class PermissionResult { Granted, NotGranted }

sealed class IosPickerResult {
    data class Success(val identifiers: List<String>) : IosPickerResult()
    data class Failure(val message: String) : IosPickerResult()
    object Cancelled : IosPickerResult()
}
```

---

## Usage

```kotlin
// Pick a single photo
val result = FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Photo))
when (result) {
    is FilePickerResult.Success -> {
        when (val asset = result.results.first()) {
            // Android media/capture/document and iOS documents.
            is MediaReference.Uri -> loadImage(asset.value)
            // iOS gallery/camera: a PHAsset localIdentifier. Render it with the
            // ui:element image stack (Image.LocalIdentifier resolves it via PHAsset).
            is MediaReference.DeviceAsset -> showAsset(Image.LocalIdentifier(asset.value))
        }
    }
    FilePickerResult.Cancelled -> { /* user dismissed the picker */ }
    FilePickerResult.Failure -> { /* error */ }
}

// Pick up to 5 photos
FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Photo, quantity = 5))

// Pick a video from the gallery
FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Video))

// Pick up to 20 photos or videos and keep copies in the app's own storage
FilePicker.shared.execute(
    FilePickerRequest.Media(types = setOf(MediaType.Photo, MediaType.Video), quantity = 20, importTo = "$filesDir/picks"),
)

// Capture a photo or record a video with the camera
FilePicker.shared.execute(FilePickerRequest.Capture(type = MediaType.Photo))
FilePicker.shared.execute(FilePickerRequest.Capture(type = MediaType.Video))

// Pick a document (mimeTypes honored on both platforms)
FilePicker.shared.execute(FilePickerRequest.Document(mimeTypes = listOf("application/pdf", "text/plain")))
```

On iOS, grant add-only library access before a capture, from `iosMain` (for example behind an `expect` function or a platform-provided interface your common code depends on):

```kotlin
// iosMain
suspend fun prepareCapture(): Boolean = PhotoSaver.create().requestPhotoLibraryPermission()
```

Capture only when it returns `true`: otherwise the camera still opens, and the request resolves to `Failure` once the shot is taken.
