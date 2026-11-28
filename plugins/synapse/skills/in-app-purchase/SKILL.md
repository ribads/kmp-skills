---
name: in-app-purchase
description: Use when an app sells its own digital goods (coins, credits, unlocks) through the phone's store in a KMP project: listing products with store prices, opening the purchase sheet, server-verified granting, consuming or acknowledging, pending payments and restoring what a person owns. Google Play Billing on Android; StoreKit 2 on iOS.
user-invocable: true
---

# core:in-app-purchase: Store purchases

**Module**: `core:in-app-purchase` | **Artifact**: `com.ribads.synapse:core-in-app-purchase`
**Packages**: `com.ribads.synapse.core.inapppurchase`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-in-app-purchase:<version>")
}
```

Every release is on Synapse's Maven repository, `https://maven.ribads.com`; Maven Central has major releases only. Declare it in `settings.gradle.kts` as an `exclusiveContent` repository filtered to `com.ribads.synapse`, and read the latest version from `https://maven.ribads.com/com/ribads/synapse/<artifact>/maven-metadata.xml`.

Depends on `core:context` (Android only: auto-initialized via ContentProvider, nothing to call). Built on Google Play Billing Library 9.1.0 (`billing-ktx`) on Android and StoreKit 2 (through the `StoreKitBridge` Swift package) on iOS 16+.

## Imports

Every public type is in `com.ribads.synapse.core.inapppurchase`:

```kotlin
import com.ribads.synapse.core.inapppurchase.AccountToken
import com.ribads.synapse.core.inapppurchase.InAppPurchaseException
import com.ribads.synapse.core.inapppurchase.InAppPurchases
import com.ribads.synapse.core.inapppurchase.PurchaseOutcome
import com.ribads.synapse.core.inapppurchase.Store
import com.ribads.synapse.core.inapppurchase.StoreFailure
import com.ribads.synapse.core.inapppurchase.StoreProduct
import com.ribads.synapse.core.inapppurchase.StorePurchase
```

## When to use

- Selling consumables (coins, credits) or non-consumables (an unlock) that are used inside the app.
- Showing products with the store's own price in the person's currency.
- Finishing purchases a server has verified, including ones paid while the app was closed.

Do not use for:
- Physical goods, services used outside the app, or card payments: `/synapse:payments` (Paystack).
- Subscriptions: not supported yet.
- Granting on the phone alone. The phone can be tampered with; a server verifies `StorePurchase.proof` with the store and grants.

## API

```kotlin
interface InAppPurchases {
    suspend fun products(ids: Set<String>): Result<List<StoreProduct>>
    suspend fun purchase(product: StoreProduct, account: AccountToken): Result<PurchaseOutcome>
    suspend fun purchases(): Result<List<StorePurchase>>
    suspend fun restore(): Result<List<StorePurchase>>
    suspend fun consume(purchase: StorePurchase.Paid): Result<Unit>
    suspend fun acknowledge(purchase: StorePurchase.Paid): Result<Unit>
    val updates: Flow<StorePurchase>

    companion object { val shared: InAppPurchases }
}

data class StoreProduct(
    val id: String, val title: String, val description: String,
    val displayPrice: String,   // the store's own formatting, e.g. "£1.99"
    val priceMicros: Long, val currencyCode: String,
)

enum class Store { GooglePlay, AppStore }

sealed class StorePurchase {   // store, productId, quantity, proof, account
    class Paid(..., val orderId: String?, val acknowledged: Boolean)
    class Pending(...)
}

sealed interface PurchaseOutcome {
    data class Purchased(val purchase: StorePurchase.Paid)
    data class Pending(val purchase: StorePurchase.Pending? = null)
    data object Cancelled
}

sealed interface StoreFailure {   // carried by InAppPurchaseException.failure
    Unavailable, ProductUnavailable, AlreadyOwned, Busy, Declined, Interrupted, Unexpected(detail)
}

@JvmInline value class AccountToken { companion object { fun parse(value: String): AccountToken? } }
```

### Semantics

- **Every call returns `Result`**, failing with `InAppPurchaseException`; act on its `failure`. Cancellation is never caught.
- **`shared` is the only instance.** One store connection per process: a second would split `updates`.
- **`purchase`** looks the product up again (the price is the store's at that moment), opens the sheet over the active foreground screen (resumed Activity on Android, active `UIWindowScene` on iOS), and suspends until it closes. One sheet at a time: another call fails with `Busy`, as does a call while the app is not in the foreground. If the caller is cancelled while the sheet is open, a paid outcome arrives on `updates`.
- **`AccountToken`** is a UUID your server issues per account. The store keeps it with the purchase (Play's `obfuscatedExternalAccountId`, StoreKit 2's `appAccountToken`), so the server can credit the account that bought, whoever reports it. Never a user id or an email.
- **`purchases()`** is the source of truth: consumables not yet consumed, non-consumables owned (routine restore), and on Google Play payments still pending. Read it when the app starts and when it returns to the foreground.
- **`restore()`** syncs with the store and returns held purchases. On iOS it calls `AppStore.sync()` first, which may prompt for Apple Account authentication, so call it only from an explicit user-tapped "Restore purchases" action, never on launch. On Android it delegates to `purchases()`.
- **`updates`** is a hot, best-effort hint: a pending payment clearing (including Ask to Buy approval on iOS), a purchase made in the store, or a paid outcome whose caller left. React by reading `purchases()`.
- **`PurchaseOutcome.Pending.purchase`** carries the pending purchase record on Google Play, and is `null` on the App Store because StoreKit 2 issues no transaction until approval arrives on `updates`.
- **`consume` / `acknowledge`** finish a purchase once it has been granted (finishing the transaction in StoreKit 2 on iOS). Something the store already counts as done (your server consumed it first, or a transaction is already finished) is success. Google Play refunds a purchase that is neither within three days.
- **`StorePurchase.proof`** is the credential a server verifies: Google Play's purchase token on Android, or the StoreKit 2 signed transaction JWS on iOS (with `orderId` carrying Play's order id or StoreKit's transaction id). `toString()` leaves it out; never log it. Two purchases are equal when they share a store and a proof, so a pending Google Play purchase that clears equals its paid self.

| Failure | Meaning | What the app does |
|---|---|---|
| `Unavailable` | No store here: no Play Store, Screen Time / parental restrictions, or a restricted profile | Hide buying; offer another route |
| `ProductUnavailable` | Not sold here or not to this person | Drop the product |
| `AlreadyOwned` | An earlier purchase of it is not consumed yet | Settle `purchases()`, then try again |
| `Busy` | A sheet is open, or the app is not in the foreground | Ignore the tap |
| `Declined` | The payment method was declined | Say so; they can pick another |
| `Interrupted` | The store or the network failed (or Apple Account sign-in was cancelled during `restore()`) | Try again later |
| `Unexpected` | Anything else, `detail` for logs | Log it |

## Usage

### Products with store prices

```kotlin
val products = InAppPurchases.shared.products(setOf("coins_100", "coins_300")).getOrElse { return }
products.sortedBy { it.priceMicros }.forEach { show(it.title, it.displayPrice) }
```

### Buying, verified by a server

```kotlin
val account = AccountToken.parse(server.purchaseAccount()) ?: return
when (val outcome = InAppPurchases.shared.purchase(product, account).getOrElse { return show(it) }) {
    is PurchaseOutcome.Purchased -> settle(outcome.purchase)
    is PurchaseOutcome.Pending -> showPending()          // settled later, from purchases() / updates
    PurchaseOutcome.Cancelled -> Unit
}

suspend fun settle(purchase: StorePurchase.Paid) {
    // The server asks the store about purchase.proof (using purchase.store), credits the account the store names, and answers.
    if (server.report(purchase.store, purchase.productId, purchase.proof).credited) {
        InAppPurchases.shared.consume(purchase)          // acknowledge(...) for a non-consumable
    }
}
```

### Settling what arrived while the app was away

```kotlin
InAppPurchases.shared.purchases().getOrNull().orEmpty()
    .filterIsInstance<StorePurchase.Paid>()
    .forEach { settle(it) }
```

Run it at start, when an account signs in, when the app returns to the foreground, and on each `updates` emission. Serialise it with buying (a `Mutex`): the foreground return fires the moment the purchase sheet closes, while the purchase is still being reported.

### Explicit restore button

```kotlin
// Call only from an explicit user action (e.g. tapping "Restore purchases").
InAppPurchases.shared.restore()
    .onSuccess { held -> held.filterIsInstance<StorePurchase.Paid>().forEach { settle(it) } }
    .onFailure { show(it) }
```

## DI wiring (kotlin-inject)

```kotlin
import com.ribads.synapse.core.discopes.SingletonScope
import com.ribads.synapse.core.inapppurchase.InAppPurchases
import me.tatarka.inject.annotations.Provides

interface StoreComponent {

    @Provides
    @SingletonScope
    fun provideInAppPurchases(): InAppPurchases = InAppPurchases.shared
}
```

Keep it behind your own port in the data layer, so tests drive a fake and nothing above data names the store.

## Lifecycle & scoping

- Process-wide: the store connection opens on first use (Play reconnects when it drops; StoreKit starts observing `Transaction.updates`). Nothing to release.
- Report a purchase to the server from a scope that outlives the screen (a repository's), so a screen torn down mid-purchase does not strand it; `purchases()` catches anything that still slips through.
- `purchase` needs the app in the foreground (a resumed Activity on Android, an active `UIWindowScene` on iOS); everything else works from any scope.

## Platforms

### Android

- **minSdk 24**. Play Billing merges `com.android.vending.BILLING` into the app's manifest. Before products can be created, Play Console needs a build with that permission on a testing track. Create each product as a one-time product with one buy purchase option (legacy compatible) and multi-quantity off; product ids are permanent. A server verifies with `purchases.productsv2.getproductpurchasev2` and consumes with `purchases.products.consume`, through a service account given "View financial data" and "Manage orders" in Play Console.
- **Testing on Android**: purchases need an app with the same package name as one on Play. Add your Google account under License testing in Play Console: test cards then cost nothing, including the slow card for pending payments, and a debug build can buy. Everyone else is charged.

### iOS

- **Add the StoreKitBridge SPM dependency**: StoreKit 2 is Swift-only, so Kotlin/Native reaches it through the `StoreKitBridge` package's `@objc` layer. In Xcode: **File > Add Package Dependencies**, add:

```text
https://github.com/ribads/storekit-bridge-kmp
```

Select the `StoreKitBridge` library product, with the dependency rule **Up to Next Minor Version** from `0.0.1`. Requires a deployment target of iOS 16 or later and a static Kotlin framework (`isStatic = true`). An app only has to link the package if it reaches `InAppPurchases` (or exports `core:in-app-purchase` into its framework): Kotlin/Native drops bridge references nothing reaches.

- **Cinterop (already configured)**:
  - `core/in-app-purchase/src/nativeInterop/cinterop/StoreKitBridge.def`
  - `core/in-app-purchase/src/nativeInterop/cinterop/StoreKitBridge.h`

  iOS targets of this module compile on macOS only (cinterop cannot cross-compile).

- **App Store Connect & server verification**: enable the **In-App Purchase** capability on the iOS app target and create each product in App Store Connect as a Consumable or Non-Consumable. A server verifies `StorePurchase.proof` (the StoreKit 2 signed transaction JWS) with Apple's root CA (for example `@apple/app-store-server-library`'s `SignedDataVerifier`) or queries the App Store Server API using `orderId` (`transactionId`), confirming `bundleId`, `productId`, `environment`, and `appAccountToken`.
- **Testing on iOS**: add a StoreKit Configuration file (`.storekit`) to the Xcode scheme (**Edit Scheme > Run > Options > StoreKit Configuration**) to test purchases, consumables, non-consumables, Ask to Buy, and restore locally in the Simulator without App Store Connect. For end-to-end sandbox testing against App Store Connect, sign in with a Sandbox Apple Account on a device.
