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
    fun parse(date: String): Long
    fun format(time: Long, format: String? = null, timeZone: TimeZone? = null): String

    companion object {
        const val ISO_FORMAT: String = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
        val UTC: TimeZone
        fun create(): DateTimeParser
    }
}
```

- `parse` — parses an ISO 8601 date-time string to epoch milliseconds. The instant is fixed by the offset carried in the string (trailing `Z` or numeric offset), so the result is timezone-independent.
- `format` — formats epoch millis to string. Defaults to `ISO_FORMAT` and UTC.

### Locale-Dependent Patterns

These pattern characters auto-delegate to platform-native formatters:
- `a` — AM/PM marker
- `h`, `k`, `K` — 12-hour / clock-hour fields (e.g. `hh:mm`, `h:mm a`)
- `E`, `e`, `c` — day of week names
- `G` — era
- `MMM`, `MMMM` — abbreviated/full month names
- `LLL`, `LLLL` — standalone month names
- `zzz`, `zzzz` — timezone names

Standard numeric patterns (`dd`, `MM`, `yyyy`, `HH`, `mm`, `ss`) work cross-platform via kotlinx.datetime.

---

## Usage

```kotlin
val parser = DateTimeParser.create()

// Parse ISO date — the trailing 'Z' (or numeric offset) fixes the instant
val millis = parser.parse("2024-03-15T14:30:00.000Z")
val withOffset = parser.parse("2024-03-15T14:30:00.000+03:00")

// Format with custom pattern
val formatted = parser.format(millis, "dd MMM yyyy")          // "15 Mar 2024"
val withTime = parser.format(millis, "dd/MM/yyyy hh:mm a")    // "15/03/2024 02:30 PM"
val time12h = parser.format(millis, "hh:mm")                  // "02:30"

// Format with timezone
val london = parser.format(millis, "HH:mm", TimeZone.of("Europe/London"))
```

**Platforms**: JVM, iOS (arm64, x64, simulatorArm64). Uses `kotlinx.datetime.TimeZone`.
