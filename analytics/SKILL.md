---
name: analytics
description: Use when implementing analytics event tracking, screen tracking, user properties, or Compose-integrated analytics in a KMP project.
user-invocable: true
---

# Analytics Modules

## core:analytics:base

**Package**: `com.ribads.synapse.core.analytics.base`

```kotlin
interface Analytics {
    fun setUserId(id: String)
    fun log(eventName: String, params: Map<String, AnalyticsParams> = mapOf())
    fun logScreen(screenName: String, screenClass: String)
    fun setUserProperties(key: String, params: AnalyticsParams)
}

sealed class AnalyticsParams {
    data class IntType(val value: Int) : AnalyticsParams()
    data class StringType(val value: String) : AnalyticsParams()
    data class BooleanType(val value: Boolean) : AnalyticsParams()
    val getAsStringValue: String
}
```

## core:analytics:compose

**Package**: `com.ribads.synapse.core.analytics.compose`

```kotlin
@Composable
fun WithAnalytics(analytics: Analytics, content: @Composable () -> Unit)

val LocalAnalyticsLogger: ProvidableCompositionLocal<Analytics>  // throws if not provided
```

---

## Usage

```kotlin
// Provide analytics to composition tree
WithAnalytics(analytics = myAnalyticsImpl) {
    App()
}

// Log events anywhere in composition
val analytics = LocalAnalyticsLogger.current
analytics.log("button_clicked", mapOf("button_id" to AnalyticsParams.StringType("submit")))
analytics.logScreen("HomeScreen", "HomeScreen")
analytics.setUserId("user_123")
analytics.setUserProperties("tier", AnalyticsParams.StringType("premium"))
```

Not published to Maven Central — use as source dependencies.
