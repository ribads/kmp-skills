---
name: events
description: Use when implementing an app-wide event bus for cross-cutting signals — session/auth expiry, connectivity state, feature flags, global refresh triggers — that multiple modules subscribe to in a KMP project. Supports sticky (retained) events and interceptor middleware.
user-invocable: true
---

# core:events — App Event Bus

**Module**: `core:events` | **Artifact**: `com.ribads.synapse:core-events`
**Packages**: `com.ribads.synapse.core.events`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-events:<version>")
}
```

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.events.AppEvent
import com.ribads.synapse.core.events.EventBus
import com.ribads.synapse.core.events.EventInterceptor
import com.ribads.synapse.core.events.EventPublisher
import com.ribads.synapse.core.events.EventSubscriber
import com.ribads.synapse.core.events.StickyEvent
import com.ribads.synapse.core.events.events
import com.ribads.synapse.core.events.latest
import com.ribads.synapse.core.events.sticky
```

---

## When to use

Use for **cross-cutting signals** that multiple unrelated modules need to react to:

- Session / auth expiry (cleanup caches, dismiss sheets, navigate to login)
- Connectivity transitions (kick off sync queues, show offline banners)
- Feature-flag or theme-mode changes
- Global "refresh everything" triggers after a deep-link action

Do **not** use for:

- Feature-scoped communication — repositories, use cases, and MVI contracts are the correct home for that
- Replacing your analytics pipeline: analytics is fire-and-record-for-later, this is fire-and-react-now. Forward a subset of events to it from an interceptor instead
- Request/response or command patterns — the bus is fan-out and fire-and-forget; pick a repository for those

---

## API

```kotlin
interface AppEvent
interface StickyEvent : AppEvent

interface EventPublisher {
    suspend fun emit(event: AppEvent)
    fun tryEmit(event: AppEvent)
}

interface EventSubscriber {
    val events: Flow<AppEvent>
    fun <T : AppEvent> latest(type: KClass<T>): T?
    fun <T : AppEvent> sticky(type: KClass<T>): Flow<T>
}

fun interface EventInterceptor {
    suspend fun intercept(event: AppEvent)
}

interface EventBus : EventPublisher, EventSubscriber {
    companion object {
        fun create(
            scope: CoroutineScope,
            interceptors: List<EventInterceptor> = emptyList(),
        ): EventBus
    }
}

// Reified ergonomic helpers
inline fun <reified T : AppEvent> EventSubscriber.events(): Flow<T>
inline fun <reified T : AppEvent> EventSubscriber.latest(): T?
inline fun <reified T : AppEvent> EventSubscriber.sticky(): Flow<T>
```

### Semantics

- **Multi-subscriber fan-out** — every active subscriber receives every event. Backed by `MutableSharedFlow`, not `Channel`.
- **Regular events**: no replay. Late subscribers see only future emissions.
- **Sticky events** (`StickyEvent`): the bus retains the latest value per concrete class. Late subscribers to `sticky<T>()` / `latest<T>()` receive the last-known matching value. Non-sticky subscribers (`events<T>()`) still see every emission as it happens.
- **Buffered, drop-oldest overflow** — `extraBufferCapacity = 64`, `onBufferOverflow = DROP_OLDEST`. Emitters never suspend waiting on slow consumers.
- **Emission order** preserved per collector.
- **Hot** — the flow exists whether or not anyone is listening; emissions with no subscribers are simply dropped.

### `emit` vs `tryEmit`

- `emit(event)` — suspending. Use from coroutine scopes.
- `tryEmit(event)` — non-suspending; returns `Unit`. Because the buffer is drop-oldest it always delivers without suspending, so there is no success/failure to report. On overflow the **oldest** still-undelivered event is dropped, not the one you pass. Use from synchronous contexts (callbacks, interceptors). If you need confirmation an event was buffered, redesign the producer — the bus cannot report a drop.

Sticky retention happens for both — there is no separate sticky emit API. Detection is via the `StickyEvent` marker on the event type.

### Split capability interfaces

Inject the narrowest interface a consumer actually needs:

- `EventPublisher` — emit-only (producers, interceptors-as-emitters)
- `EventSubscriber` — listen-only (Interactors, ViewModels)
- `EventBus` — both (DI bindings, test fixtures)

---

## Defining events

Events are defined **per feature**, not in `core:events`. Use a `sealed interface` rooted at either `AppEvent` (one-shot) or `StickyEvent` (retained):

```kotlin
// One-shot — no replay
sealed interface SessionEvent : AppEvent {
    data object Expired : SessionEvent
    data object LoggedOut : SessionEvent
    data class Refreshed(val expiresAt: Long) : SessionEvent
}

// Retained — late subscribers see latest value
sealed interface ConnectivityEvent : StickyEvent {
    data object Lost : ConnectivityEvent
    data object Restored : ConnectivityEvent
}
```

Kotlin's sealed hierarchies are module-local, so keep each sealed root in the module that owns the concept. `core:events` only owns the `AppEvent` / `StickyEvent` markers and the bus itself.

### Sticky semantics in detail

Sticky retention is **keyed by the event's concrete class**. Emitting a new instance of the same concrete class replaces the stored value. `latest<SuperType>()` and `sticky<SuperType>()` return the most recently retained event whose concrete class IS-A `SuperType`.

```kotlin
bus.emit(ConnectivityEvent.Lost)        // stored: Lost
bus.emit(ConnectivityEvent.Restored)    // stored: Restored (different concrete class)
bus.latest<ConnectivityEvent>()         // Restored — most recent of any subtype
bus.latest<ConnectivityEvent.Lost>()    // Lost — Lost was never replaced at its key

bus.emit(ConnectivityEvent.Restored)    // same concrete class — replaces stored Restored
bus.sticky<ConnectivityEvent>()         // emits Restored, conflates duplicates
```

`sticky<T>()` applies `distinctUntilChanged`, so re-emitting the same value does not re-surface it. If you need every emission, subscribe via `events<T>()` instead.

---

## Usage

### Publishing (one-shot)

```kotlin
class AuthInterceptor(private val publisher: EventPublisher) {
    fun onResponse(response: Response) {
        if (response.status == 401) {
            publisher.tryEmit(SessionEvent.Expired)
        }
    }
}
```

### Publishing (sticky state)

Bridge `core:connectivity` (`/connectivity`) into the bus so features react via sticky events:

```kotlin
class ConnectivityEventBridge(
    monitor: ConnectivityMonitor,   // from core:connectivity
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

### Subscribing (one-shot, typed)

```kotlin
class AppShellInteractor(
    private val subscriber: EventSubscriber,
    private val scope: CoroutineScope,
) {
    init {
        subscriber.events<SessionEvent>()
            .onEach { event ->
                when (event) {
                    SessionEvent.Expired -> promptReLogin()
                    SessionEvent.LoggedOut -> clearCaches()
                    is SessionEvent.Refreshed -> rescheduleRefresh(event.expiresAt)
                }
            }
            .launchIn(scope)
    }
}
```

### Subscribing (sticky, with replay of latest)

```kotlin
class SyncInteractor(
    private val subscriber: EventSubscriber,
    private val scope: CoroutineScope,
) {
    init {
        // Collector is called immediately with the most recent Restored/Lost,
        // then again for every change.
        subscriber.sticky<ConnectivityEvent>()
            .onEach { event ->
                when (event) {
                    ConnectivityEvent.Restored -> flushQueue()
                    ConnectivityEvent.Lost -> pauseQueue()
                }
            }
            .launchIn(scope)
    }

    // One-shot read of the current state — for UI composition, no subscription
    fun isOnline(): Boolean =
        subscriber.latest<ConnectivityEvent>() == ConnectivityEvent.Restored
}
```

### Subscribing (raw, for debug observability)

```kotlin
subscriber.events
    .onEach { logger.debug("event: $it") }
    .launchIn(debugScope)
```

---

## Interceptors

Interceptors are side-effect observers invoked in parallel with normal subscribers. Registered once at bus construction. Common uses:

- Debug-build logging of every event
- Forwarding a marked subset of events to the app's analytics or crash reporter
- Recording crash breadcrumbs
- Powering a live dev-overlay feed

```kotlin
class DebugLogInterceptor(private val log: (String) -> Unit) : EventInterceptor {
    override suspend fun intercept(event: AppEvent) {
        log("[bus] $event")
    }
}

class RecentEventsInterceptor(private val capacity: Int) : EventInterceptor {
    private val _recent = MutableStateFlow<List<AppEvent>>(emptyList())
    val recent: StateFlow<List<AppEvent>> = _recent.asStateFlow()

    override suspend fun intercept(event: AppEvent) {
        _recent.update { (it + event).takeLast(capacity) }
    }
}

val recentEvents = RecentEventsInterceptor(capacity = 50)   // feeds a dev overlay or crash breadcrumbs

val bus = EventBus.create(
    scope = appScope,
    interceptors = listOf(
        DebugLogInterceptor(log = ::println),
        recentEvents,
    ),
)
```

To forward events elsewhere (analytics, a crash reporter), give the events that should leave the app a marker interface extending `AppEvent` and check for it in `intercept`, so the bus never needs to know about the receiving SDK.

Semantics:

- Interceptors **cannot** filter, transform, or short-circuit events — they run as independent collectors on the bus's `scope`. To block or mutate events, do it at the producer.
- Exceptions thrown from `intercept` are **swallowed** per interceptor — one throwing interceptor never kills the others or the subscribers. `CancellationException` is the exception: it is re-thrown so scope teardown and the interceptor's own structured cleanup still run.
- **Per-interceptor isolation** — each interceptor drains its own drop-oldest mailbox, so a slow `intercept` only drops *its own* events and never causes drops for other interceptors or normal subscribers.
- **No startup gap** — interceptor collection subscribes synchronously during `EventBus.create`, so an interceptor observes every event from bus construction onward, including events emitted in the same tick the bus is built.
- Dispatch order between interceptors and normal subscribers is **not guaranteed**. Do not rely on interceptor-before-subscriber ordering.
- Cancelling the `scope` passed to `create` tears down all interceptor collectors. External subscribers keep their own scopes and are unaffected.

---

## DI wiring (kotlin-inject)

```kotlin
import com.ribads.synapse.core.discopes.SingletonScope
import com.ribads.synapse.core.events.EventBus
import com.ribads.synapse.core.events.EventInterceptor
import com.ribads.synapse.core.events.EventPublisher
import com.ribads.synapse.core.events.EventSubscriber
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import me.tatarka.inject.annotations.Provides

interface EventsComponent {

    @Provides
    @SingletonScope
    fun provideBusScope(): CoroutineScope =
        CoroutineScope(Dispatchers.Default + SupervisorJob())

    @Provides
    @SingletonScope
    fun provideEventBus(
        scope: CoroutineScope,
        interceptors: Set<EventInterceptor>,
    ): EventBus = EventBus.create(scope, interceptors.toList())

    @Provides
    fun provideEventPublisher(bus: EventBus): EventPublisher = bus

    @Provides
    fun provideEventSubscriber(bus: EventBus): EventSubscriber = bus
}
```

Interceptors are contributed from feature modules via a multi-binding (`Set<EventInterceptor>`) so adding a new interceptor does not require touching the events module.

---

## Lifecycle & scoping

- The bus itself is a hot singleton; it holds no subscriber state.
- External subscribers bind collection to **their own** `CoroutineScope` (`viewModelScope`, an Interactor scope). Cancelling that scope cancels the subscription.
- The `scope` passed to `EventBus.create` is used **only** for running interceptors. Cancelling it tears down interceptors without affecting external subscribers.
- Forgetting to scope a subscriber leaks the collector for the lifetime of the bus (i.e. the app).

---

## Platforms

JVM (Android apps consume the JVM artifact; there is no separate Android target) and iOS (`iosArm64`, `iosSimulatorArm64`). Pure Kotlin, backed by `kotlinx.coroutines` `MutableSharedFlow` + `MutableStateFlow`.
