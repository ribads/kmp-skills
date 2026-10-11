---
name: data-boundaries
description: "Use when deciding where a model, mapper, or error belongs across the layers of a Synapse KMP app: network DTOs, domain entities, use-case results, UI models. Covers what each module may import, what a UseCase returns, where exceptions are caught, where a domain failure becomes user-facing copy, and how to enforce all of it with Konsist. Trigger when adding a repository, use case, or model; when a layer needs data it cannot currently see; or when reviewing whether a type is leaking across a boundary."
user-invocable: true
---

# data-boundaries: Layer & Model Boundaries

The layering rules that keep a Synapse app's modules independently buildable and independently reasonable. `/mvi` covers the inside of a screen; this covers everything beneath it.

## When to use

- Adding a repository, data source, use case, or any model that crosses a module
- A layer needs data it cannot currently see, and you are deciding whether to widen a dependency or add a hop
- Reviewing a change for a boundary leak (a domain entity in a composable, a DTO in a Reducer)
- Setting up architecture tests on a new project

---

## The model chain

The same concept is represented five times on its way to the screen. Each hop exists to buy something specific:

```
ApiResponse  →  Dto  →  Entity  →  UseCase result  →  UI model
  (wire)      (data)   (domain)     (feature)         (screen)
```

| Hop | Buys you |
|---|---|
| `ApiResponse → Dto` | `@Serializable` / `@SerialName` never leave the datasource; wire nullability collapses once, here |
| `Dto → Entity` | Domain vocabulary and domain invariants; `String` dates become `Long` timestamps |
| `Entity → UseCase result` | A feature reshapes for its own needs and joins across repositories without the domain knowing either feature exists |
| `UseCase result → UI model` | `Clause` / `Image` / component models; nothing renderable survives as a raw `String` |

Five hops sounds like a lot until the wire format changes and exactly one mapper needs editing.

**Do not collapse a hop to save typing.** Collapsing `Dto → Entity` is how `@SerialName` ends up in domain code; collapsing `Entity → UseCase result` is how two features start fighting over one shared model.

### The same concept at each layer

```kotlin
// domain/product/data/…/datasource/api/model/ProductApiResponse.kt
@Serializable
internal data class ProductApiResponse(
    @SerialName("_id") val id: String,
    @SerialName("soldOut") val soldOut: Boolean? = null,
    @SerialName("createdAt") val createdAt: String,
)

// domain/product/data/…/datasource/dto/ProductDto.kt   (no annotations, nullability resolved)
internal data class ProductDto(val id: String, val soldOut: Boolean, val createdAt: String)

// domain/product/entities/…/ProductEntity.kt           (public, domain vocabulary)
data class ProductEntity(val id: String, val soldOut: Boolean, val createdAtTimestamp: Long)

// features/home/usecase/…/dto/Product.kt               (feature-shaped, cross-repo joins live here)
data class Product(val id: String, val soldOut: Boolean, val postedTimestamp: Long, val inCart: Boolean)

// features/home/ui/…/screens/feed/model/ProductItemModel.kt  (renderable)
@Immutable
internal data class ProductItemModel(val id: String, val title: Clause, val price: Clause, val image: Image)
```

### Visibility per layer

| Layer | Visibility | Why |
|---|---|---|
| `ApiResponse`, `Dto` | `internal` | Never leave their module |
| Entity, repository interface | `public` | The domain's whole purpose is to be consumed |
| UseCase DTO + interface | `public` | Must cross from `usecase` to `ui` |
| UI model, Contract, Screen, everything in the 7-file package | `internal` | Only `{Feature}Module` and `{Feature}FeatureLauncher` are public in a feature |

---

## What each module may import

| Module | May depend on | Must never import |
|---|---|---|
| `domain/*/entities` | coroutines, DI runtime | serialization, ktor, SQL, Compose, any formatter |
| `domain/*/data` | its own entities, network, database | Compose, `ui:*`, any feature |
| `features/*/usecase` | `domain/*/entities` only | `domain/*/data`, any `*RepositoryImpl`, Compose, `ui:element` |
| `features/*/ui` | its own `usecase`, `compose-ui`, Synapse `ui:*` | **any** `domain.*`, anything named `*Repository` |
| `features/*/ui-api` | primitives and navigation keys | `domain.*`, `*.usecase.*` |
| `core/*`, `compose-ui/` | Synapse and platform APIs | `domain.*`, `features.*` |

The first line of enforcement is the module graph: if `features/home/ui/build.gradle.kts` never declares `implementation(projects.domain.product.entities)`, the import cannot compile. Keep it that way. Do not add a dependency to make one import work.

`features/*/ui-api` is the **only** type a feature may hand to another feature. Keep it to primitives and `NavKey`s; pre-format anything the receiver cannot re-derive.

---

## UseCase contract

```kotlin
interface FetchProductsUseCase {
    suspend fun execute(nextPageToken: String?): ProductsResult
}

internal class FetchProductsUseCaseImpl @Inject constructor(
    private val repository: ProductRepository,
    private val mapper: ProductMapper,
) : FetchProductsUseCase {
    override suspend fun execute(nextPageToken: String?): ProductsResult =
        repository.fetch(nextPageToken).let(mapper::map)
}
```

- **Public interface, `internal` `@Inject` implementation.**
- **Exactly one operation**: `suspend fun execute(...)`, or `fun observe*(...): Flow<T>` for a stream. Two operations means two use cases.
- **Returns a feature-owned sealed result.** Never `kotlin.Result<T>`, never a domain entity, never null-as-error.
- **Cross-repository joins happen here and nowhere else.** A repository must not know about another aggregate; a mapper must not do I/O. The use case is the only place that legitimately reads two sources and combines them.

```kotlin
sealed class ProductsResult {
    data class Success(val products: List<Product>, val nextPageToken: String?) : ProductsResult()
    data object Failure : ProductsResult()
}
```

---

## Error boundary

**`RepositoryImpl` is the single place that catches.** It logs and returns a failure variant. Above it nothing catches, because above it nothing throws.

```kotlin
internal class ProductRepositoryImpl @Inject constructor(
    private val dataSource: ProductDataSource,
    private val mapper: ProductDtoToEntityMapper,
    private val errorLogger: ErrorLogger,
) : ProductRepository {

    override suspend fun fetch(token: String?): ProductsEntityResult = runCatching {
        dataSource.fetchProducts(token).let(mapper::map)
    }.getOrElse {
        errorLogger.log(it)
        ProductsEntityResult.Failure
    }

    override fun observe(id: String): Flow<ProductEntityResult> = flow {
        emit(dataSource.fetchProduct(id).let(mapper::map))
    }.catch {
        errorLogger.log(it)
        emit(ProductEntityResult.Failure)
    }
}
```

A `try/catch` in a use case, an interactor, or a composable is a smell: it means an exception escaped the boundary, or someone is defending against one that cannot arrive.

### Failures carry types, not strings

```kotlin
data object Failure : LoginResult()                             // default
data class Failure(val reason: LoginFailureReason) : LoginResult()  // when the caller must branch
data class Failure(val message: String) : LoginResult()         // never
```

A message from a network response is not user-facing copy: it is unlocalized, untested, and written by a backend that does not know your product voice. Carry a typed reason and let the screen decide what to say.

### The full path of one error

```
Exception
  └─ RepositoryImpl catches → ErrorLogger.log(it) → EntityResult.Failure
       └─ usecase mapper → FeatureResult.Failure
            └─ screen Mapper → Result.OnLoadFailed(ToastModel(Text.Localized(Res.string.…), ToastIntent.Error))
                 └─ Reducer → state withEffect Effect.ShowToast(result.toast)
                      └─ Screen → toaster.show(effect.model)
```

**A domain error becomes user-facing copy in exactly one place: the screen Mapper.** That is also the only place `Res.string` is legal outside `ViewState.Default`.

---

## Formatting ownership

| Concern | Parsed / produced in | Formatted in | Never in |
|---|---|---|---|
| Dates | `domain/*/data` (`String` → `Long`) | screen Mapper (`Long` → `Text.Timestamp` or a `DateTimeFormatter`) | usecase, Reducer, Interactor, Screen |
| Money | stored as minor units (`Long`) end to end | never; emit `Text.Money(amount, currency)` and let the renderer format | anywhere that produces a currency string |
| Copy | n/a | screen Mapper, via `Text.Localized(Res.string.…)` | domain, usecase, Screen |

See `/ui-element` for why `Text.Money` and `Text.Timestamp` are declarations rather than formatted strings.

---

## Enforcing it

Module boundaries catch cross-module leaks. Konsist catches the rest: same-module violations and conventions the compiler cannot see.

```kotlin
// konsist/build.gradle.kts
plugins { alias(libs.plugins.kotlin.jvm) }
dependencies {
    testImplementation(libs.konsist)   // com.lemonappdev:konsist, pin the current release
    testImplementation(libs.kotlin.test)
}
```

```kotlin
class LayerBoundaryTest {

    private fun featureUiFiles() = Konsist.scopeFromProject().files
        .filter { it.path.contains("/features/") && it.path.contains("/ui/src/") }

    @Test
    fun `feature ui must not depend on the domain layer`() {
        featureUiFiles().assertFalse { file ->
            file.imports.any { it.name.startsWith("com.example.domain.") }
        }
    }

    @Test
    fun `feature ui must not touch repositories directly`() {
        featureUiFiles().assertFalse { file ->
            file.imports.any { it.name.substringAfterLast('.').endsWith("Repository") }
        }
    }

    @Test
    fun `usecase must not reach into the data layer`() {
        Konsist.scopeFromProject().files
            .filter { it.path.contains("/usecase/src/") }
            .assertFalse { file ->
                file.imports.any { it.name.contains(".data.") || it.name.endsWith("RepositoryImpl") }
            }
    }
}
```

```kotlin
class UseCaseConventionTest {

    // RATCHET TO EMPTY. Never add a new entry. Fix the use case instead.
    private val legacyMultiOperation = setOf<String>()

    @Test
    fun `a use case exposes exactly one execute or observe operation`() {
        Konsist.scopeFromProject().interfaces()
            .filter { it.name.endsWith("UseCase") && it.name !in legacyMultiOperation }
            .assertTrue { useCase ->
                useCase.functions().singleOrNull()
                    ?.let { it.name == "execute" || it.name.startsWith("observe") } == true
            }
    }
}
```

The allowlist ratchet is the pattern worth copying: when you adopt a rule on an existing codebase, seed the set with today's violations, forbid additions in a comment, and drain it over time. A rule with an empty allowlist and three exceptions scattered through the code is a rule nobody trusts.

`/init-project` does not scaffold this module; add it once per project.

---

## Rules

- **Five hops, no shortcuts.** `ApiResponse → Dto → Entity → UseCase result → UI model`.
- **`@Serializable` lives only on wire models**, inside the datasource package, `internal`.
- **Domain entities import nothing but coroutines and DI.** No serialization, no Compose, no formatters.
- **Feature UI never imports `domain.*` or anything named `*Repository`.** It talks to its own use cases and nothing else.
- **A use case returns a feature-owned sealed result** and exposes one `execute`/`observe*` operation.
- **Cross-repository joins belong in a use case**, never in a repository or a mapper.
- **`RepositoryImpl` is the only place that catches.** Log there, return a failure variant, and let every layer above stay exception-free.
- **Failures carry typed reasons, never strings.** Copy is chosen in the screen Mapper.
- **Money stays in minor units**; dates stay as timestamps. Formatting happens at render time.
- **Enforce with Konsist**, and ratchet allowlists to empty.
