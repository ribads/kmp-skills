---
name: di-scopes
description: Use when setting up dependency injection scopes with kotlin-inject in a KMP project. Provides the SingletonScope annotation.
user-invocable: true
---

# core:discopes — DI Scope Annotations

**Module**: `core:discopes` | **Artifact**: `com.ribads.synapse:core-discopes`
**Packages**: `com.ribads.synapse.core.discopes`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-discopes:<version>")
}
```

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.discopes.SingletonScope
```

---

## API

```kotlin
@Scope
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.PROPERTY_GETTER)
annotation class SingletonScope
```

That's the entire public API. This module provides a single scope annotation for use with kotlin-inject.

---

## Usage

```kotlin
// Mark a component as singleton-scoped
@SingletonScope
@Component
abstract class AppComponent {
    abstract val repository: MyRepository
}

// Mark a provided binding as singleton
@SingletonScope
@Provides
fun provideHttpClient(): HttpClient = HttpClient { /* config */ }

// Mark a class as singleton
@SingletonScope
@Inject
class MyRepository(private val api: ApiService)
```

Requires kotlin-inject KSP plugin in your build for code generation.
