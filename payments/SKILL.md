---
name: payments
description: "Use when implementing payment processing in a KMP project: Paystack card payments, mobile money (M-Pesa), the Paystack payment sheet, or transaction handling. Also use when asked for Stripe, because Synapse has no Stripe support: there is no Stripe artifact to depend on."
user-invocable: true
---

# Payment Modules: Paystack

## Dependencies

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:paystack-core:<version>")  // SDK: services, models, errors
    implementation("com.ribads.synapse:paystack-ui:<version>")    // payment sheet; exposes paystack-core as api
}
```

`paystack-core` declares `android.permission.INTERNET` in its Android manifest (and `paystack-ui` depends on it), so the app inherits the permission through manifest merging.

## Imports

Import each type from its package below.

| Package | Types |
|---|---|
| `com.ribads.synapse.paystack.core` | `Paystack`, `PaystackConfig`, `PaystackConfigBuilder`, `paystack` |
| `com.ribads.synapse.paystack.core.api.models` | `AccessCodeData`, `AddressState`, `CardParams`, `ChannelOptions`, `ChargeAuthorization`, `ChargeResponse`, `Customer`, `MobileMoneyChannelOption`, `MobileMoneyChargeResponse`, `PaymentChannel`, `PaystackDomain`, `PaystackError`, `RedirectAuthResponse`, `TransactionEvent`, `TransactionStatus`, `asPaystackError` |
| `com.ribads.synapse.paystack.core.api.services` | `CardPaymentService`, `MobileMoneyService`, `TransactionService` |
| `com.ribads.synapse.paystack.core.logging` | `Logger` |
| `com.ribads.synapse.paystack.ui` | `PaymentSheet` (androidMain only), `PaymentSheetContent`, `PaymentSheetResult`, `PaymentSheetResultCallback`, `PaymentSheetViewController` (iosMain only), `PaystackPaymentSheet`, `PaystackPaymentSheetState`, `rememberPaystackPaymentSheetState` |
| `com.ribads.synapse.paystack.ui.models` | `PaymentCompletionDetails` |

---

## Paystack (KMP)

### core:paystack:core: SDK Core

**Package**: `com.ribads.synapse.paystack.core`; see [Imports](#imports) for the rest

```kotlin
// --- Initialization ---

// DSL (returns the singleton and stores it)
val paystack = paystack {
    publicKey = "pk_test_xxxxxxxxxxxxxxxx"  // required, non-blank; use your test key in development
    enableLogging = false                   // default false
    sdkVersion = "0.0.1"                    // default "0.0.1"
}
// Or factory overloads
val paystack = Paystack.create(publicKey = "pk_test_xxxxxxxxxxxxxxxx", enableLogging = false)
val paystack = Paystack.create(config = PaystackConfig(publicKey = "pk_test_xxxxxxxxxxxxxxxx"))

// Every entry point validates the key: a blank publicKey throws PaystackError.InvalidKey
// and leaves the SDK uninitialized.

data class PaystackConfig(
    val publicKey: String,
    val enableLogging: Boolean = false,
    val sdkVersion: String = "0.0.1",
)

class Paystack /* private constructor */ {
    val config: PaystackConfig
    val logger: Logger
    val transactions: TransactionService
    val cards: CardPaymentService
    val mobileMoney: MobileMoneyService

    companion object {
        val instance: Paystack                 // throws PaystackError.NotInitialized before create()/paystack {}
        val isInitialized: Boolean
        fun create(config: PaystackConfig): Paystack   // throws PaystackError.InvalidKey for a blank key
        fun create(publicKey: String, enableLogging: Boolean = false): Paystack
        fun reset()
    }
}

class PaystackConfigBuilder {
    var publicKey: String = ""
    var enableLogging: Boolean = false
    var sdkVersion: String = "0.0.1"
}

fun paystack(block: PaystackConfigBuilder.() -> Unit): Paystack

// --- Services (accessed via Paystack instance; constructors are internal) ---

class TransactionService {
    suspend fun verifyAccessCode(accessCode: String): Result<AccessCodeData>
    suspend fun checkPendingCharge(accessCode: String): Result<ChargeResponse>
    fun getSupportedPaymentChannels(): List<PaymentChannel>
    fun transactionEvents(channelName: String): Flow<Result<TransactionEvent>>
}

class CardPaymentService {
    suspend fun charge(
        accessCode: String,
        cardParams: CardParams,
        encryptionKey: String,
    ): Result<ChargeResponse>
    suspend fun authenticateWithPin(accessCode: String, pin: String, encryptionKey: String): Result<ChargeResponse>
    suspend fun authenticateWithOtp(accessCode: String, otp: String): Result<ChargeResponse>
    suspend fun authenticateWithPhone(accessCode: String, phoneNumber: String): Result<ChargeResponse>
    suspend fun authenticateWithAddress(
        accessCode: String,
        address: String,
        city: String,
        state: String,
        zipCode: String,
    ): Result<ChargeResponse>
    suspend fun authenticateWithBirthday(accessCode: String, day: String, month: String, year: String): Result<ChargeResponse>
    suspend fun getAddressStates(countryCode: String): Result<List<AddressState>>
    fun redirectAuthResults(transactionId: String): Flow<Result<RedirectAuthResponse>>
}

class MobileMoneyService {
    suspend fun charge(
        transactionId: String,
        provider: String,
        phone: String? = null,
    ): Result<MobileMoneyChargeResponse>
}

// --- Logging ---

interface Logger {
    fun debug(message: String?)
    fun error(throwable: Throwable? = null, message: String?)
}

// --- Errors ---

sealed class PaystackError(
    override val message: String,
    override val cause: Throwable? = null,
) : Exception(message, cause) {
    class NotInitialized(
        message: String = "Paystack SDK has not been initialized. Call paystack { } or Paystack.create() first.",
    ) : PaystackError(message)
    class InvalidKey(message: String = "Invalid or missing Paystack API Key.") : PaystackError(message)
    class Network(message: String, cause: Throwable? = null) : PaystackError(message, cause)
    class Api(message: String, val statusCode: Int? = null) : PaystackError(message)
    class NoResponseBody(message: String = "No response body returned by the server.") : PaystackError(message)
    class Authentication(message: String, cause: Throwable? = null) : PaystackError(message, cause)
    class Unknown(message: String = "An unexpected error occurred.", cause: Throwable? = null) : PaystackError(message, cause)
}

fun Throwable.asPaystackError(): PaystackError
```

**When each error is raised**:

| Error | Raised when |
|---|---|
| `NotInitialized` | `Paystack.instance` is read before `paystack { }` / `Paystack.create()`. The payment sheet reports it as `PaymentSheetResult.Failed` instead of crashing. |
| `InvalidKey` | The public key is blank at configuration (thrown), or the API answers HTTP 401 (returned as a `Result` failure). |
| `Network` | Connection, DNS, TLS or timeout failure (any `kotlinx.io.IOException`, which includes Ktor's request, connect and socket timeouts), or a lost realtime connection. |
| `Api` | Any other non-2xx response; `statusCode` is the HTTP status. |
| `NoResponseBody` | A 2xx response without a `data` payload. |
| `Authentication` | A card authentication step was rejected locally (an invalid date of birth). |
| `Unknown` | Anything else, including an undecodable payload; the original throwable is the `cause`. |

`asPaystackError()` applies this mapping and rethrows `CancellationException`, so a cancelled call cancels its caller instead of surfacing as a payment error. Every `Result` failure and every failed event from the services below is a `PaystackError`.

**Realtime flows** (`transactionEvents`, `redirectAuthResults`): cold flows that subscribe on collection and unsubscribe when collection stops. A payload that fails to decode is emitted as `Result.failure(PaystackError.Unknown)` and the stream continues. A lost connection is emitted as one final `Result.failure(PaystackError.Network)` and the flow completes, so `first()` always returns. On Android the Pusher client first retries a dropped connection on its own, so the failure arrives once it gives up; on iOS there is no retry and the first socket error ends the flow.

**Models** (package `com.ribads.synapse.paystack.core.api.models`, all `@Serializable`):

```kotlin
data class AccessCodeData(
    val id: String, val accessCode: String, val amount: Long,
    val currency: String, val domain: PaystackDomain, val email: String,
    val merchantName: String, val reference: String, val encryptionKey: String,
    val channelOptions: ChannelOptions,
) { val isTestTransaction: Boolean; val channels: List<PaymentChannel> }

data class CardParams(
    val number: String, val cvv: String,
    val expiryMonth: String, val expiryYear: String, val pin: String? = null,
)

data class ChargeResponse(
    val status: TransactionStatus, val amount: Long, val currency: String,
    val reference: String, val channel: PaymentChannel, val domain: PaystackDomain,
    val transactionDate: String, val gatewayResponse: String,
    val fees: Long? = 0, val metadata: Map<String, String>? = null,
    val customer: Customer? = null, val message: String? = null,
    val displayText: String? = null, val authUrl: String? = null,
    val authorization: ChargeAuthorization? = null,
)

data class MobileMoneyChargeResponse(
    val channelName: String, val displayParams: DisplayParams,
    val phone: String? = null, val provider: String, val transactionId: String,
) {
    data class DisplayParams(
        val message: String, val timer: Int, val type: DisplayType,
        val paybillNumber: String? = null, val accountNumber: String? = null,
    )
    enum class DisplayType {
        ENTER_NUMBER,                        // "enter_number": ask for the phone number
        POP,                                 // "pop": push sent to the phone; show message, wait timer seconds
        MPESA_OFFLINE_PAYMENT_INSTRUCTIONS,  // "mpesa_offline_payment_instructions": paybill + account number
        UNSUPPORTED,                         // any other value the server sends
    }
}

data class TransactionEvent(val status: TransactionStatus, val message: String? = null)

data class RedirectAuthResponse(
    val status: TransactionStatus, val transactionId: String? = null,
    val message: String? = null, val response: String? = null,
) { val reference: String? }

data class AddressState(val name: String, val slug: String, val abbreviation: String)
data class Customer(/* firstName, lastName, email, customerCode, phone, metadata, riskAction, all String? */)
data class ChannelOptions(/* bankTransfer, ussd, qr, card: List<String>?; mobileMoney: List<MobileMoneyChannelOption>? */)
data class ChargeAuthorization(
    val code: String? = null, val bin: String? = null, val last4: String? = null,
    val expiryMonth: String? = null, val expiryYear: String? = null, val cardType: String? = null,
    val countryCode: String? = null, val bank: String? = null, val brand: String? = null,
    val reusable: Boolean? = null, val signature: String? = null,
)
data class MobileMoneyChannelOption(
    val key: String, val value: String, val isNew: Boolean, val phoneNumberRegex: String,
)

enum class PaymentChannel { CARD, MOBILE_MONEY, UNKNOWN }   // companion.supported = [CARD, MOBILE_MONEY]
enum class PaystackDomain { LIVE, TEST }
enum class TransactionStatus {
    Success, Failed, Pending, Timeout, SentOtp, SendBirthday,
    SendPin, SendAddress, SendPhone, OpenUrl, Requery, Unknown
}
```

**Architecture**: Suspend functions returning `Result<T>`, Flow-based events, sealed error hierarchy, no callbacks. `EventManager`, `EncryptionManager`, `PaystackApi`, and the HTTP/encryption/event factory functions are `internal`, not part of the public surface.

**Platform details**:
- Android: OkHttp + Pusher Java client
- iOS: Darwin HTTP engine + URLSessionWebSocketTask
- Encryption: RSA-OAEP (javax.crypto on Android, Security framework on iOS)

### core:paystack:ui: Payment Screens

**Package**: `com.ribads.synapse.paystack.ui`

```kotlin
// --- Compose Multiplatform modal entry point (recommended) ---

@Composable
fun rememberPaystackPaymentSheetState(): PaystackPaymentSheetState

@Stable
class PaystackPaymentSheetState {
    // constructor is internal; obtain via rememberPaystackPaymentSheetState()
    val isPresented: Boolean
    fun present(accessCode: String)
    // dismiss() is internal; the sheet manages its own lifecycle
}

@Composable
fun PaystackPaymentSheet(
    state: PaystackPaymentSheetState,
    onResult: (PaymentSheetResult) -> Unit,
    darkTheme: Boolean = isSystemInDarkTheme(),
)

// --- Low-level composable (embed in your own container) ---

@Composable
fun PaymentSheetContent(
    accessCode: String,
    onResult: (PaymentSheetResult) -> Unit,
    modifier: Modifier = Modifier,
    darkTheme: Boolean = isSystemInDarkTheme(),
)

// --- Result types ---

sealed class PaymentSheetResult {
    data class Completed(val details: PaymentCompletionDetails) : PaymentSheetResult()
    data object Cancelled : PaymentSheetResult()
    data class Failed(val error: PaystackError, val reference: String?) : PaymentSheetResult()
}

data class PaymentCompletionDetails(val reference: String)

typealias PaymentSheetResultCallback = (PaymentSheetResult) -> Unit

// --- Platform entry points ---

// Android (androidMain):
class PaymentSheet(activity: ComponentActivity, callback: PaymentSheetResultCallback) {
    fun launch(accessCode: String)
}
// iOS (iosMain):
fun PaymentSheetViewController(
    accessCode: String,
    onResult: (PaymentSheetResult) -> Unit,
): UIViewController
```

**Usage**:
```kotlin
// 1. Initialize once at app startup
paystack { publicKey = "pk_test_xxxxxxxxxxxxxxxx" }

// 2. In a composable
val state = rememberPaystackPaymentSheetState()

Button(onClick = { state.present(accessCode = "xxx") }) { ... }

PaystackPaymentSheet(
    state = state,
    onResult = { result ->
        when (result) {
            is PaymentSheetResult.Completed -> { /* result.details.reference */ }
            is PaymentSheetResult.Failed    -> { /* result.error is a PaystackError */ }
            is PaymentSheetResult.Cancelled -> { /* user dismissed */ }
        }
    },
)
```

**Screens**: Card payments (number/expiry/CVV, PIN, OTP, phone, address, DOB, 3DS) and mobile money. The sheet supports **M-Pesa only** for mobile money (online STK push and offline paybill); choosing any other mobile money provider on the transaction shows "This payment channel is not supported". For other providers, build your own flow on `MobileMoneyService` and `TransactionService.transactionEvents`.

**Errors from the sheet**: `Failed.error` is always a `PaystackError` (see the table above). Missing initialization arrives as `Failed(PaystackError.NotInitialized(), reference = null)` rather than a crash. On Android, `PaymentSheet` runs the flow in its own activity, so the error keeps its subtype, message and `Api.statusCode` but not its `cause`. A network failure while charging a card or waiting for M-Pesa stays in the flow with retry options; a failure loading the transaction, a timed-out charge, `InvalidKey` and `NotInitialized` end the sheet with `Failed`.

**Appearance**: the flow has its own light and dark Paystack palettes and never reads the host's Synapse theme. `darkTheme` picks one and defaults to the platform's appearance. Inside a Synapse app, pass `darkTheme = Theme.isDark` so the sheet follows an appearance the app sets itself (an in-app light/dark switch). The platform entry points follow the platform: `PaymentSheet` runs its own activity with a DayNight window, which follows the app's night mode on Android 12+ (set by `WithAppTheme`) and the device below that, and `PaymentSheetViewController` follows the presenting window's `overrideUserInterfaceStyle`.

---

## Stripe

Synapse does not support Stripe. The repository has an empty `:core:payment:stripe` Gradle module with no source code, and nothing is published for it, so there is no artifact to depend on and no API to call. Use Stripe's own SDKs directly if a project needs Stripe.
