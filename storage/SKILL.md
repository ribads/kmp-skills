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
    fun <T : Any> put(key: String, value: T): Boolean
    fun remove(key: String): Boolean
    fun clear(): Boolean
    fun contains(key: String): Boolean
    fun <T : Any> getAsFlow(key: String, defaultValue: T): Flow<T>
    fun keys(): Set<String>

    companion object {
        val shared: SharedPrefManager  // Default instance with name "synapse_prefs"
    }
}

// Extension
fun SharedPrefManager.getStringOrNull(key: String): String?

// Factory for custom named stores
expect fun buildSharedPrefManager(name: String): SharedPrefManager
```

**Supported types**: `String`, `Int`, `Long`, `Float`, `Double`, `Boolean`

Throws `IllegalArgumentException` if an unsupported type is passed.

---

## Platform Implementations

- **Android**: `SharedPreferences`
- **iOS**: `NSUserDefaults`
- **JVM**: `java.util.prefs.Preferences`

---

## Usage

```kotlin
val prefs = SharedPrefManager.shared

// Write
prefs.put("username", "john")
prefs.put("age", 30)
prefs.put("premium", true)

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
