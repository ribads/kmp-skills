---
name: payments
description: Use when implementing payment processing, Paystack integration, Stripe integration, card payments, mobile money, payment sheets, or transaction handling in a KMP project.
user-invocable: true
---

# Payment Modules — Paystack & Stripe

## Paystack (KMP)

### core:paystack:core — SDK Core

**Package**: `com.ribads.synapse.paystack.core`

```kotlin
// --- Initialization ---

// DSL (returns the singleton and stores it)
val paystack = paystack {
    publicKey = "pk_live_..."      // required, non-blank
    enableLogging = false           // default false
    sdkVersion = "0.0.1"            // default "0.0.1"
}
// Or factory overloads
val paystack = Paystack.create(publicKey = "pk_live_...", enableLogging = false)
val paystack = Paystack.create(config = PaystackConfig(publicKey = "pk_live_..."))

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
        val instance: Paystack                 // throws if not initialized
        val isInitialized: Boolean
        fun create(config: PaystackConfig): Paystack
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
    class NotInitialized(message: String = "Paystack SDK has not been initialized.") : PaystackError(message)
    class InvalidKey(message: String = "Invalid or missing Paystack API Key.") : PaystackError(message)
    class Network(message: String, cause: Throwable? = null) : PaystackError(message, cause)
    class Api(message: String, val statusCode: Int? = null) : PaystackError(message)
    class NoResponseBody(message: String = "No response body returned by the server.") : PaystackError(message)
    class Authentication(message: String, cause: Throwable? = null) : PaystackError(message, cause)
    class Unknown(message: String = "An unexpected error occurred.", cause: Throwable? = null) : PaystackError(message, cause)
}

fun Throwable.asPaystackError(): PaystackError
```

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
) // nested: DisplayParams, enum DisplayType { ENTER_NUMBER, POP, ... }

data class TransactionEvent(val status: TransactionStatus, val message: String? = null)

data class RedirectAuthResponse(
    val status: TransactionStatus, val transactionId: String? = null,
    val message: String? = null, val response: String? = null,
) { val reference: String? }

data class AddressState(val name: String, val slug: String, val abbreviation: String)
data class Customer(/* firstName, lastName, email, customerCode, phone, metadata, riskAction — all String? */)
data class ChannelOptions(/* bankTransfer, ussd, qr, card: List<String>?; mobileMoney: List<MobileMoneyChannelOption>? */)
data class ChargeAuthorization(/* code, bin, last4, expiryMonth, expiryYear, cardType, countryCode, bank — all String? */)
data class MobileMoneyChannelOption(/* ... */)

enum class PaymentChannel { CARD, MOBILE_MONEY, UNKNOWN }   // companion.supported = [CARD, MOBILE_MONEY]
enum class PaystackDomain { LIVE, TEST }
enum class TransactionStatus {
    Success, Failed, Pending, Timeout, SentOtp, SendBirthday,
    SendPin, SendAddress, SendPhone, OpenUrl, Requery, Unknown
}
```

**Architecture**: Suspend functions returning `Result<T>`, Flow-based events, sealed error hierarchy, no callbacks. `EventManager`, `EncryptionManager`, `PaystackApi`, and the HTTP/encryption/event factory functions are `internal` — not part of the public surface.

**Platform details**:
- Android: OkHttp + Pusher Java client
- iOS: Darwin HTTP engine + URLSessionWebSocketTask
- Encryption: RSA-OAEP (javax.crypto on Android, Security framework on iOS)

### core:paystack:ui — Payment Screens

**Package**: `com.ribads.synapse.paystack.ui`

```kotlin
// --- Compose Multiplatform modal entry point (recommended) ---

@Composable
fun rememberPaystackPaymentSheetState(): PaystackPaymentSheetState

@Stable
class PaystackPaymentSheetState {
    // constructor is internal — obtain via rememberPaystackPaymentSheetState()
    val isPresented: Boolean
    fun present(accessCode: String)
    // dismiss() is internal — sheet manages its own lifecycle
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
    data class Failed(val error: Throwable, val reference: String?) : PaymentSheetResult()
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
paystack { publicKey = "pk_live_..." }

// 2. In a composable
val state = rememberPaystackPaymentSheetState()

Button(onClick = { state.present(accessCode = "xxx") }) { ... }

PaystackPaymentSheet(
    state = state,
    onResult = { result ->
        when (result) {
            is PaymentSheetResult.Completed -> { /* result.details.reference */ }
            is PaymentSheetResult.Failed    -> { /* result.error */ }
            is PaymentSheetResult.Cancelled -> { /* user dismissed */ }
        }
    },
)
```

**Screens**: Card payments (number/expiry/CVV, PIN, OTP, phone, address, DOB, 3DS), M-Pesa (online/offline)

**Appearance**: the flow has its own light and dark Paystack palettes and never reads the host's Synapse theme. `darkTheme` picks one and defaults to the platform's appearance. Inside a Synapse app, pass `darkTheme = Theme.isDark` so the sheet follows an appearance the app sets itself (an in-app light/dark switch). The platform entry points follow the platform: `PaymentSheet` runs its own activity with a DayNight window, which follows the app's night mode on Android 12+ (set by `WithAppTheme`) and the device below that, and `PaymentSheetViewController` follows the presenting window's `overrideUserInterfaceStyle`.

---

## Stripe

### core:payment:stripe — Stripe SDK Wrapper (scaffold only)

**Package / namespace**: `com.ribads.synapse.core.payment.stripe`
**Gradle path**: `:core:payment:stripe`

> Status: the module is registered in `settings.gradle.kts` and has a Gradle build
> configured, but it currently contains **no source code** (no `src/`). There is no
> public API to consume yet.

Build configuration (`build.gradle.kts`):
- KMP targets: Android + iOS (iosX64, iosArm64, iosSimulatorArm64)
- iOS framework: `baseName = "CorePayment"`, `isStatic = true`
- Dependencies — androidMain: `stripe-android-sdk`, `androidx-appcompat`; commonMain: `coroutines-core`

When implementation lands, document the public surface here.
