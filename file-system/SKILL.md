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
    data object Failure : FilePickerResult()
    data object Cancelled : FilePickerResult()
}

sealed class ImageResult {
    data class Url(val path: String) : ImageResult()
    data class NativeIdentifier(val identifier: String) : ImageResult()
}
```

---

## iOS-Only APIs

```kotlin
data class ImageFileSize(val width: Double, val height: Double)

interface LocalAssetInMemoryProvider {
    suspend fun getImage(localIdentifier: String, size: ImageFileSize? = null): ByteArray?
    fun save(localIdentifier: String, pickerResult: PHPickerResult): Boolean

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
        val path = result.paths.first()
        when (path) {
            is ImageResult.Url -> loadImage(path.path)
            is ImageResult.NativeIdentifier -> loadByIdentifier(path.identifier)
        }
    }
    FilePickerResult.Cancelled -> { /* user cancelled */ }
    FilePickerResult.Failure -> { /* error */ }
}

// Pick multiple photos
FilePicker.shared.execute(FilePickerRequest.Media(type = MediaType.Photo, quantity = 5))

// Capture photo with camera
FilePicker.shared.execute(FilePickerRequest.Capture(type = MediaType.Photo))

// Pick a document
FilePicker.shared.execute(FilePickerRequest.Document(mimeTypes = listOf("application/pdf", "text/plain")))
```
