---
name: connectivity
description: Use when implementing network connectivity monitoring, online/offline detection, reachability, metered/unmetered awareness, or reacting to connectivity changes in a KMP project. Provides a one-shot status query and a cold Flow of status changes.
user-invocable: true
---

# core:connectivity — Connectivity Monitor

**Module**: `core:connectivity` | **Artifact**: `com.ribads.synapse:core-connectivity`
**Package**: `com.ribads.synapse.core.connectivity`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-connectivity:<version>")
}
```

Depends on `core:context` (Android only — auto-initialized via ContentProvider, nothing to call).

---

## When to use

- Online/offline banners and empty states
- Gating sync queues, uploads, or prefetching on connectivity
- Metered-awareness (skip large downloads on cellular)
- One-shot "am I online?" checks before kicking off work

Do **not** use for:

- Per-request failure handling — a satisfied network path does not guarantee a request succeeds; handle errors in the HTTP layer
- Broadcasting connectivity app-wide via an event bus — that is app wiring: bridge this monitor into `core:events` yourself (see Usage)
- Reachability of a *specific host* — this reports device-level connectivity only

---

## API

```kotlin
interface ConnectivityMonitor {
    /** One-shot snapshot. Ignores ConnectivityConfig.statusDebounce. */
    suspend fun current(): ConnectivityStatus

    /**
     * Cold flow of connectivity changes. Each collection registers the platform
     * callback and unregisters it when the collector is cancelled. Emits the
     * current status immediately on collection, then distinct changes.
     */
    fun observe(): Flow<ConnectivityStatus>
}

fun buildConnectivityMonitor(
    config: ConnectivityConfig = ConnectivityConfig(),
): ConnectivityMonitor

data class ConnectivityConfig(
    val requireValidatedConnection: Boolean = true,
    val statusDebounce: Duration = Duration.ZERO,
)

sealed interface ConnectivityStatus {
    data class Connected(
        val transport: Transport,
        val isMetered: Boolean,
    ) : ConnectivityStatus

    data object Disconnected : ConnectivityStatus
}

enum class Transport { WIFI, CELLULAR, ETHERNET, VPN, OTHER }
```

### Semantics

- **Cold flow** — every collection of `observe()` registers its own platform callback (Android `ConnectivityManager.registerDefaultNetworkCallback`, iOS `NWPathMonitor`); cancelling the collector unregisters it. There is no `release()` and no owned scope. To fan one registration out to many collectors, apply `shareIn`/`stateIn` at the call site.
- **Immediate first emission** — collectors always receive the current status right away (Android seeds from a synchronous query; iOS path monitors fire on start), even when `statusDebounce` is non-zero.
- **Distinct changes only** — consecutive equal statuses are collapsed.
- **`statusDebounce`** — a change must stay stable for the window before it is emitted; a flap that settles back to the already-delivered value emits nothing. Never delays the first emission. `current()` ignores it entirely. Android can report a brief `Disconnected` blip while switching networks (Wi-Fi ↔ cellular); 300–500ms smooths it.
- **`requireValidatedConnection`** — when `true` (default), Android only reports `Connected` for networks with `NET_CAPABILITY_VALIDATED` (actual internet reachability — filters captive portals and dead access points). No effect on iOS: a satisfied `NWPath` is the platform's only signal and already implies routability.
- **`current()`** — instant truth from the platform (Android `activeNetwork` capabilities; iOS first `NWPathMonitor` update), undecorated.

### Status mapping

| | Android | iOS |
|---|---|---|
| Connected | `NET_CAPABILITY_INTERNET` (+ `VALIDATED` per config) on the default network | `nw_path_status_satisfied` |
| `isMetered` | absence of `NET_CAPABILITY_NOT_METERED` | `isExpensive` (cellular, personal hotspot) |
| `WIFI` / `CELLULAR` / `ETHERNET` | `TRANSPORT_WIFI` / `TRANSPORT_CELLULAR` / `TRANSPORT_ETHERNET` | `wifi` / `cellular` / `wiredEthernet` interface types |
| `VPN` | `TRANSPORT_VPN` (checked first — VPN networks also report their underlying transport) | never — iOS has no VPN interface type; tunnels surface as the underlying transport or `OTHER` |

---

## Usage

### One-shot check

```kotlin
suspend fun upload(file: PlatformFile) {
    if (monitor.current() is ConnectivityStatus.Disconnected) {
        queueForLater(file)
        return
    }
    uploader.send(file)
}
```

### Observing for UI (shared, state-style)

```kotlin
class AppShellInteractor(
    monitor: ConnectivityMonitor,
    scope: CoroutineScope,
) {
    val isOnline: StateFlow<Boolean> =
        monitor.observe()
            .map { it is ConnectivityStatus.Connected }
            .stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue = true)
}
```

### Metered-aware work

```kotlin
monitor.observe()
    .filterIsInstance<ConnectivityStatus.Connected>()
    .filter { !it.isMetered }
    .onEach { prefetcher.run() }
    .launchIn(scope)
```

### Smoothing flapping networks

```kotlin
val monitor = buildConnectivityMonitor(
    ConnectivityConfig(statusDebounce = 400.milliseconds)
)
```

### Bridging into core:events

Connectivity deliberately does not depend on the event bus; the app owns the bridge:

```kotlin
class ConnectivityEventBridge(
    monitor: ConnectivityMonitor,
    publisher: EventPublisher,
    scope: CoroutineScope,
) {
    init {
        monitor.observe()
            .onEach { status ->
                publisher.tryEmit(
                    when (status) {
                        is ConnectivityStatus.Connected -> ConnectivityEvent.Restored
                        ConnectivityStatus.Disconnected -> ConnectivityEvent.Lost
                    }
                )
            }
            .launchIn(scope)
    }
}
```

---

## DI wiring (kotlin-inject)

```kotlin
import com.ribads.synapse.core.connectivity.ConnectivityConfig
import com.ribads.synapse.core.connectivity.ConnectivityMonitor
import com.ribads.synapse.core.connectivity.buildConnectivityMonitor
import com.ribads.synapse.core.discopes.SingletonScope
import me.tatarka.inject.annotations.Provides

interface ConnectivityComponent {

    @Provides
    @SingletonScope
    fun provideConnectivityMonitor(): ConnectivityMonitor =
        buildConnectivityMonitor(ConnectivityConfig(statusDebounce = 400.milliseconds))
}
```

The monitor is stateless and cheap to construct; a singleton is a convenience, not a requirement.

---

## Lifecycle & scoping

- No lifecycle to manage — registration lives and dies with each collection of `observe()`.
- Collectors bind to **their own** `CoroutineScope`; cancelling that scope unregisters the platform callback.
- Each concurrent collection holds its own platform registration. That is fine for a handful of collectors; for app-wide fan-out, `shareIn`/`stateIn` once (as in the Interactor example) so a single registration serves everyone.
- `current()` on iOS spins up a short-lived path monitor (milliseconds); on Android it is a synchronous query.

---

## Platforms

- **Android**: `ConnectivityManager` default-network callback. `ACCESS_NETWORK_STATE` is declared in the module manifest and merges into consumers automatically. minSdk 24. Requires `core:context` (auto-initialized).
- **iOS** (arm64, simulatorArm64): `NWPathMonitor` via the Network framework. No setup required.
