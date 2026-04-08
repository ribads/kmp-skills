---
name: datetime
description: Use when implementing date/time parsing, formatting, custom date format patterns, or timestamp manipulation in a KMP project.
user-invocable: true
---

# core:datetime — Date/Time Utilities

**Module**: `core:datetime` | **Artifact**: `com.ribads.synapse:core-datetime`
**Package**: `com.ribads.synapse.core.datetime`

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-datetime:<version>")
}
```

---

## API

```kotlin
interface DateTimeParser {
    fun parse(date: String, timeZone: TimeZone? = null): Long
    fun format(time: Long, format: String? = null, timeZone: TimeZone? = null): String

    companion object {
        const val ISO_FORMAT: String = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
        val UTC: TimeZone
        fun create(): DateTimeParser
    }
}
```

- `parse` — parses a date string to epoch milliseconds. Defaults to UTC.
- `format` — formats epoch millis to string. Defaults to `ISO_FORMAT` and UTC.

### Locale-Dependent Patterns

These pattern characters auto-delegate to platform-native formatters:
- `a` — AM/PM marker
- `E`, `e`, `c` — day of week names
- `MMM`, `MMMM` — abbreviated/full month names
- `LLL`, `LLLL` — standalone month names
- `zzz`, `zzzz` — timezone names

Standard numeric patterns (`dd`, `MM`, `yyyy`, `HH`, `mm`, `ss`) work cross-platform via kotlinx.datetime.

---

## Usage

```kotlin
val parser = DateTimeParser.create()

// Parse ISO date
val millis = parser.parse("2024-03-15T14:30:00.000Z")

// Format with custom pattern
val formatted = parser.format(millis, "dd MMM yyyy")          // "15 Mar 2024"
val withTime = parser.format(millis, "dd/MM/yyyy hh:mm a")    // "15/03/2024 02:30 PM"

// Format with timezone
val london = parser.format(millis, "HH:mm", TimeZone.of("Europe/London"))

// Parse with timezone
val eastern = parser.parse("2024-03-15T14:30:00.000Z", TimeZone.of("America/New_York"))
```

**Platforms**: JVM, iOS (arm64, x64, simulatorArm64). Uses `kotlinx.datetime.TimeZone`.
