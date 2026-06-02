---
name: file-system
description: Use when implementing file picking, photo picking, camera capture, document selection, or saving photos in a KMP project.
user-invocable: true
---

# core:file — File Picker & File Operations

**Module**: `core:file` | **Artifact**: `com.ribads.synapse:core-file`
**Package**: `com.ribads.synapse.core.file`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-file:<version>")
}
```

Depends on `core:context`.

---

## FilePicker (Common API)

```kotlin
interface FilePicker {
    suspend fun execute(request: FilePickerRequest): FilePickerResult

    companion object {
        val shared: FilePicker
    }
}
```

### FilePickerRequest

```kotlin
sealed class FilePickerRequest {
    data class Media(val type: MediaType, val quantity: Int = 1) : FilePickerRequest()
    data class Capture(val type: MediaType) : FilePickerRequest()
    data class Document(val mimeTypes: List<String> = listOf("application/pdf")) : FilePickerRequest()

    enum class MediaType { Photo, Video }
}
```

### FilePickerResult

```kotlin
sealed class FilePickerResult {
    data class Success(val paths: List<ImageResult>) : FilePickerResult()
    data object Failure : FilePickerResult()   // an error occurred
    data object Cancelled : FilePickerResult()  // user dismissed the picker
}

sealed class ImageResult {
    // A directly loadable URI/path: Android media/capture/document, and iOS documents.
    data class Url(val path: String) : ImageResult()
    // A platform asset identifier to resolve via the asset loader: iOS gallery/camera
    // picks return a PHAsset localIdentifier (render with ui:element Image.LocalIdentifier).
    data class NativeIdentifier(val identifier: String) : ImageResult()
}
```

`Cancelled` is returned on both platforms when the user backs out of the picker; `Failure` is reserved for actual errors. `Document` always yields `ImageResult.Url`; `Media`/`Capture` yield `ImageResult.Url` on Android and `ImageResult.NativeIdentifier` on iOS.

---

## iOS-Only APIs

```kotlin
data class ImageFileSize(val width: Double, val height: Double)

interface LocalAssetInMemoryProvider {
    // Single-shot: a successful read decodes the bytes and evicts the entry.
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

    companion object {
        fun create(): PhotoSaver
    }
}

enum class PermissionResult { Granted, NotGranted }
```

---

## Usage

```kotlin
// Pick a single photo
val result = FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Photo))
when (result) {
    is FilePickerResult.Success -> {
        when (val asset = result.paths.first()) {
            // Android media/capture/document and iOS documents.
            is ImageResult.Url -> loadImage(asset.path)
            // iOS gallery/camera: a PHAsset localIdentifier. Render it with the
            // ui:element image stack (Image.LocalIdentifier resolves it via PHAsset).
            is ImageResult.NativeIdentifier -> showAsset(Image.LocalIdentifier(asset.identifier))
        }
    }
    FilePickerResult.Cancelled -> { /* user dismissed the picker */ }
    FilePickerResult.Failure -> { /* error */ }
}

// Pick multiple photos
FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Photo, quantity = 5))

// Pick a video from the gallery
FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Video))

// Capture photo with camera
FilePicker.shared.execute(FilePickerRequest.Capture(type = MediaType.Photo))

// Pick a document (mimeTypes honored on both platforms)
FilePicker.shared.execute(FilePickerRequest.Document(mimeTypes = listOf("application/pdf", "text/plain")))
```
