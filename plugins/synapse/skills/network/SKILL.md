---
name: network
description: Use when building the HTTP client for a REST/JSON API, adding bearer-token auth with refresh, classifying failed requests into typed failures, logging HTTP traffic, or faking an API in tests in a KMP project. Ktor-based; provides buildHttpClient, NetworkConfig, AuthTokenSource and NetworkFailure. For online/offline detection use connectivity instead.
user-invocable: true
---

# core:network: HTTP Client

**Module**: `core:network` | **Artifact**: `com.ribads.synapse:core-network`
**Packages**: `com.ribads.synapse.core.network`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-network:<version>")
}
```

Exposes Ktor's `HttpClient` (`ktor-client-core` is an `api` dependency) and `kotlinx-serialization-json`. Brings the platform engines (OkHttp on Android, Darwin on iOS) and the `INTERNET` permission, so do not declare an engine yourself. Synapse builds against Ktor 3.6.0; keep any Ktor artifact you add, such as `ktor-client-mock`, on the same version.

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.network.AuthTokenSource
import com.ribads.synapse.core.network.AuthTokens
import com.ribads.synapse.core.network.HttpLogger
import com.ribads.synapse.core.network.HttpLogging
import com.ribads.synapse.core.network.NetworkConfig
import com.ribads.synapse.core.network.NetworkFailure
import com.ribads.synapse.core.network.buildHttpClient
import com.ribads.synapse.core.network.toNetworkFailure
```

---

## When to use

- Building the app's API client, once per process, in the composition root
- Bearer auth whose tokens refresh on a 401
- Turning a failed call into a typed failure at the repository's single catch point (see `/synapse:data-boundaries`)
- Faking the API in repository tests with `MockEngine`

Do **not** use for:

- Online/offline detection or reachability: that is `/synapse:connectivity`
- Image loading: `ui:element`'s Coil loader has its own fetcher and engines (see `/synapse:ui-element`)
- A second host with different auth: build a separate client with its own `NetworkConfig`, and never pass the API's `AuthTokenSource` to it

---

## API

```kotlin
data class NetworkConfig(
    val baseUrl: String,                                              // must end in "/"; throws otherwise
    val requestTimeoutMillis: Long = DEFAULT_REQUEST_TIMEOUT_MILLIS,  // 30_000
    val logging: HttpLogging = HttpLogging.None,
    val json: Json = DefaultJson,                                     // Json { ignoreUnknownKeys = true }
) {
    companion object {
        const val DEFAULT_REQUEST_TIMEOUT_MILLIS: Long = 30_000
        val DefaultJson: Json
    }
}

sealed interface HttpLogging {
    data object None : HttpLogging
    data class Headers(val logger: HttpLogger) : HttpLogging
    data class Body(val logger: HttpLogger) : HttpLogging
}

fun interface HttpLogger {
    fun log(message: String)
}

interface AuthTokenSource {
    suspend fun current(): AuthTokens?

    /** Returns null when the session cannot continue; throws to fail the request without ending the session. */
    suspend fun refresh(stale: AuthTokens): AuthTokens?
}

data class AuthTokens(
    val accessToken: String,
    val refreshToken: String?,
)

/** [configure] runs after the defaults; authentication belongs in [tokens], never in an `Auth` install there. */
fun buildHttpClient(
    config: NetworkConfig,
    tokens: AuthTokenSource? = null,
    configure: HttpClientConfig<*>.() -> Unit = {},
): HttpClient

/** Builds over a caller-owned engine: a `MockEngine` in tests, or a platform engine with pinning. */
fun buildHttpClient(
    engine: HttpClientEngine,
    config: NetworkConfig,
    tokens: AuthTokenSource? = null,
    configure: HttpClientConfig<*>.() -> Unit = {},
): HttpClient

sealed interface NetworkFailure {
    data object Offline : NetworkFailure
    data object Timeout : NetworkFailure
    data object Unauthorized : NetworkFailure
    data class Http(val status: Int) : NetworkFailure
    data object Malformed : NetworkFailure
    data object Unexpected : NetworkFailure
}

fun Throwable.toNetworkFailure(): NetworkFailure
```

---

## What the client does

- **Throws on non-2xx.** `expectSuccess = true`, so a 4xx or 5xx arrives at your catch point as a `ResponseException` instead of a response you have to inspect.
- **Resolves relative paths under `baseUrl`.** Write `client.get("products")`, with no leading slash. A leading slash resolves against the host and drops a base path such as `/v1/`.
- **Decodes JSON** with `config.json` through `ContentNegotiation`. The response must carry a JSON `Content-Type`.
- **Times out** after `requestTimeoutMillis`, which surfaces as `NetworkFailure.Timeout`.
- **Logs only when asked.** `HttpLogging.Headers` or `Body` sends each line to your `HttpLogger`. `Authorization` is always redacted. Bodies are not, so keep `Body` to debug builds and never log a client that carries credentials in bodies (a token endpoint).
- **Bearer auth**, only when `tokens` is passed:
  - The token is read from `current()` on every request, never cached by the client, so a sign-out or a refresh elsewhere applies to the next request.
  - It is attached only to requests whose host is `baseUrl`'s host. A request to any other host carries no token.
  - A 401 from the API host calls `refresh(stale)` once and retries with the new token. A 401 from another host is neither refreshed nor retried.
  - `refresh` returning null fails the request with the original 401 (`Unauthorized`). `refresh` throwing fails the request with that exception, so an offline refresh becomes `Offline`.
  - A refresh that has started is not cancelled when the caller is, so its result still gets stored.

### `toNetworkFailure()` mapping

| Throwable | `NetworkFailure` |
|---|---|
| `ResponseException` with status 401 | `Unauthorized` |
| any other `ResponseException` | `Http(status)` |
| `HttpRequestTimeoutException`, `ConnectTimeoutException`, `SocketTimeoutException` | `Timeout` |
| `ContentConvertException`, `NoTransformationFoundException`, `SerializationException` | `Malformed` |
| any other `kotlinx.io.IOException` | `Offline` |
| anything else | `Unexpected` |

Rethrow `CancellationException` before calling it: it would map to `Unexpected`.

---

## Usage

### Composition root

```kotlin
val client = buildHttpClient(
    config = NetworkConfig(
        baseUrl = environment.apiBaseUrl,
        logging = if (environment.verboseNetworkLogging) HttpLogging.Body(KermitHttpLogger) else HttpLogging.None,
    ),
    tokens = sessionTokens,   // omit for an API without credentials
)
```

Build one client for the API and hand it to every data source. The base URL comes from the platform (build type, xcconfig), never from shared code; `/synapse:init-project` wires exactly this.

### Data source and repository

```kotlin
internal class ProductDataSource(private val client: HttpClient) {
    suspend fun fetch(): List<ProductApiResponse> = client.get("products").body()
}

override suspend fun fetch(): ProductsEntityResult = runCatching {
    ProductsEntityResult.Success(dataSource.fetch().map { it.toEntity() })
}.getOrElse {
    if (it is CancellationException) throw it
    logger.log(it)
    ProductsEntityResult.Failure(it.toNetworkFailure().toProductFailureReason())
}
```

Translate `NetworkFailure` into the domain's own reason in the repository; entities never import it. `/synapse:data-boundaries` has the full chain.

### Implementing `AuthTokenSource`

```kotlin
internal class SessionAuthTokenSource(
    private val store: TokenStore,
    private val refreshApi: TokenRefreshDataSource,   // uses a client built WITHOUT tokens
) : AuthTokenSource {

    override suspend fun current(): AuthTokens? = store.read()

    override suspend fun refresh(stale: AuthTokens): AuthTokens? {
        val refreshToken = stale.refreshToken ?: return signOut()
        val renewed = runCatching { refreshApi.refresh(refreshToken) }.getOrElse { failure ->
            if (failure is CancellationException) throw failure
            if (failure.toNetworkFailure().isRejection()) return signOut()   // 400, 401, 403
            throw failure                                                      // offline: keep the session
        }
        store.write(renewed)
        return renewed
    }
}
```

- Call the token endpoint through a second client built **without** `tokens` and with `HttpLogging.None`. Through the API client, a 401 from the token endpoint would trigger another refresh, and body logging would print the tokens.
- Store the renewed tokens before returning them.
- Return null only when the server rejects the refresh token. Throw for anything transient, so a flaky network does not sign the user out.

`/init-project --with-session` generates a complete implementation with encrypted storage and tests.

### Adding request defaults or plugins

```kotlin
val client = buildHttpClient(config, tokens) {
    defaultRequest { header("X-Client-Version", appVersion) }
}
```

`configure` runs after the defaults, so it adds to them. Two things do not go there: authentication (pass `tokens`) and the JSON format (pass `json` in `NetworkConfig`, because a second JSON converter would never be reached).

### A custom engine (certificate pinning)

```kotlin
// androidMain; add io.ktor:ktor-client-okhttp at Synapse's Ktor version
val engine = OkHttp.create { config { certificatePinner(pinner) } }
val client = buildHttpClient(engine, config, tokens)
```

---

## Testing

```kotlin
commonTest.dependencies {
    implementation("io.ktor:ktor-client-mock:3.6.0")
}
```

```kotlin
val client = buildHttpClient(
    engine = MockEngine { request ->
        respond(
            content = """[{"id":"1","name":"First"}]""",
            status = HttpStatusCode.OK,
            headers = headersOf(HttpHeaders.ContentType, "application/json"),
        )
    },
    config = NetworkConfig(baseUrl = "https://api.example.test/"),
)
```

The client under test is the production one, so `expectSuccess`, JSON decoding and `toNetworkFailure()` behave as they do in the app. Throw from the handler to simulate a transport failure: `throw IOException("unreachable")` becomes `Offline`.

---

## Related skills

- `/synapse:data-boundaries`: where the catch lives and how `NetworkFailure` becomes a domain reason
- `/synapse:init-project`: generates the composition root, a worked repository and the optional session domain on top of this module
- `/synapse:connectivity`: device-level online/offline status
- `/synapse:server-driven-ui`: its gateway `OperationHandler` example reaches this client through a use case, so renderer operations share the app's auth and failure handling
