---
name: storage
description: Use when implementing key-value storage, persistent preferences, SharedPreferences, UserDefaults, or simple local data persistence in a KMP project.
user-invocable: true
---

# core:sharedpref — Key-Value Storage

**Module**: `core:sharedpref` | **Artifact**: `com.ribads.synapse:core-sharedpref`
**Package**: `com.ribads.synapse.core.sharedpref`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-sharedpref:<version>")
}
```

Depends on `core:context`.

---

## API

```kotlin
interface SharedPrefManager {
    fun <T : Any> get(key: String, defaultValue: T): T

    // Blocking writes — perform a synchronous, durable write on the calling thread.
    // Avoid on the main thread; prefer the await* variants from coroutine code.
    fun <T : Any> put(key: String, value: T): Boolean
    fun remove(key: String): Boolean
    fun clear(): Boolean

    // Suspending writes — run the synchronous write off the main thread (Dispatchers.Default).
    // The Result is success(true/false) for the write outcome, or failure if the write threw.
    // Cancellation propagates (it is not folded into the Result).
    suspend fun <T : Any> awaitPut(key: String, value: T): Result<Boolean>
    suspend fun awaitRemove(key: String): Result<Boolean>
    suspend fun awaitClear(): Result<Boolean>

    fun contains(key: String): Boolean
    fun <T : Any> getAsFlow(key: String, defaultValue: T): Flow<T>
    fun keys(): Set<String>

    companion object {
        val shared: SharedPrefManager     // Plaintext instance, name "synapse_prefs"
        val encrypted: SharedPrefManager  // Authenticated-encryption instance, name "synapse_secure_prefs"
    }
}

// Extension
fun SharedPrefManager.getStringOrNull(key: String): String?

// Factories for custom named stores
expect fun buildSharedPrefManager(name: String): SharedPrefManager
expect fun buildEncryptedSharedPrefManager(name: String): SharedPrefManager
```

**Supported types**: `String`, `Int`, `Long`, `Float`, `Double`, `Boolean`

Throws `IllegalArgumentException` if an unsupported type is passed to a blocking write or to `get`.

`get` returns `defaultValue` when the key is missing. Reading a key with a type other than the one
it was written with is misuse; on iOS such a mismatch returns `defaultValue` rather than a
secretly-null or coerced value. Always read a key with the same type it was written with.

`getAsFlow` reads and de-duplicates off the collector's thread, so it is safe to collect on the main
dispatcher.

---

## Platform Implementations

- **Android**: `SharedPreferences`
- **iOS**: `NSUserDefaults` (scoped to its own suite domain for `clear()` / `keys()`)
- **JVM**: `java.util.prefs.Preferences`

`encrypted` uses authenticated encryption on every platform: AES-256-GCM on Android and JVM,
AES-256-CBC with an HMAC-SHA256 integrity tag (Encrypt-then-MAC) on iOS. Keys are held in the
platform keystore/keychain. Tampered ciphertext is rejected and reads fall back to `defaultValue`.

---

## Usage

```kotlin
val prefs = SharedPrefManager.shared

// Write
prefs.put("username", "john")
prefs.put("age", 30)
prefs.put("premium", true)

// Write off the main thread (preferred in coroutines / MVI interactors)
suspend fun persist() {
    prefs.awaitPut("username", "john")
        .onFailure { /* surface or log the write failure */ }
}

// Read
val name = prefs.get("username", "")
val age = prefs.get("age", 0)

// Read nullable
val token = prefs.getStringOrNull("auth_token")

// Observe reactively (emits current value immediately, then on every change)
prefs.getAsFlow("username", "").collect { username ->
    updateUI(username)
}

// Check & remove
if (prefs.contains("temp_key")) {
    prefs.remove("temp_key")
}

// Custom named store
val authPrefs = buildSharedPrefManager(name = "auth_storage")
authPrefs.put("token", "abc123")
```
