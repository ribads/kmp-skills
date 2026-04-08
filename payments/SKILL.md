---
name: payments
description: Use when implementing payment processing, Paystack integration, Stripe integration, card payments, mobile money, payment sheets, or transaction handling in a KMP project.
user-invocable: true
---

# Payment Modules — Paystack & Stripe

## Paystack (KMP)

### core:paystack:core — SDK Core

**Package**: `com.synapse.paystack.core`

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

**Package**: `com.synapse.paystack.ui`

```kotlin
// Compose Multiplatform payment UI
@Composable
fun PaymentSheetContent(...)

// Result handling
sealed class PaymentSheetResult {
    data class Completed(val reference: String) : PaymentSheetResult()
    data object Cancelled : PaymentSheetResult()
    data class Failed(val error: PaystackError) : PaymentSheetResult()
}

// Platform entry points
// Android: PaymentSheetActivity (ComponentActivity)
// iOS: PaymentSheetViewController() factory
// Android public API: PaymentSheet with ActivityResultLauncher
```

**Screens**: Card payments (number/expiry/CVV, PIN, OTP, phone, address, DOB, 3DS), M-Pesa (online/offline)

### core:payment:paystack — High-level Wrapper

Composes `core:paystack:core` + `core:paystack:ui` into a single integration point.

---

## Stripe

### core:payment:stripe — Stripe SDK Wrapper

**Package**: `com.ribads.synapse.core.payment.stripe`

Wraps Stripe Android SDK for payment processing.
- Android: `stripe.android.sdk`
- Payment initialization and method management
