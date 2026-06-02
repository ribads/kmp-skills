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
// DSL initialization
val paystack = paystack { publicKey = "pk_live_..." }
// Or factory
val paystack = Paystack.create(publicKey = "pk_live_...")

// Services
class TransactionService { suspend fun charge(...): Result<ChargeResponse> }
class CardPaymentService { suspend fun chargeCard(...): Result<ChargeResponse> }
class MobileMoneyService { suspend fun chargeMobileMoney(...): Result<ChargeResponse> }

// Event streaming
class EventManager { fun subscribe(): Flow<String> }

// Errors
sealed class PaystackError {
    class Api(val message: String, val code: Int) : PaystackError()
    class Network(val cause: Throwable) : PaystackError()
    class Authentication(val message: String) : PaystackError()
    object NoResponseBody : PaystackError()
}
```

**Architecture**: Suspend functions returning `Result<T>`, Flow-based events, sealed error hierarchy, no callbacks.

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
    val isPresented: Boolean
    fun present(accessCode: String)
    // dismiss() is internal — sheet manages its own lifecycle
}

@Composable
fun PaystackPaymentSheet(
    state: PaystackPaymentSheetState,
    onResult: (PaymentSheetResult) -> Unit,
)

// --- Low-level composable (embed in your own container) ---

@Composable
fun PaymentSheetContent(
    accessCode: String,
    onResult: (PaymentSheetResult) -> Unit,
    modifier: Modifier = Modifier,
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

// Android: PaymentSheet(activity: ComponentActivity, callback) → launch(accessCode)
// iOS: PaymentSheetViewController(accessCode, onResult) → UIViewController
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

---

## Stripe

### core:payment:stripe — Stripe SDK Wrapper

**Package**: `com.ribads.synapse.core.payment.stripe`

Wraps Stripe Android SDK for payment processing.
- Android: `stripe.android.sdk`
- Payment initialization and method management
