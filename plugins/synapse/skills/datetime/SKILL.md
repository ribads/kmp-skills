---
name: datetime
description: Use when implementing date/time parsing, formatting, custom date format patterns, or timestamp manipulation in a KMP project.
user-invocable: true
---

# core:datetime — Date/Time Utilities

**Module**: `core:datetime` | **Artifact**: `com.ribads.synapse:core-datetime`
**Packages**: `com.ribads.synapse.core.datetime`; see [Imports](#imports)

```kotlin
commonMain.dependencies {
    implementation("com.ribads.synapse:core-datetime:<version>")
}
```

## Imports

Import them from exactly these paths:

```kotlin
import com.ribads.synapse.core.datetime.DateTimeParser
import com.ribads.synapse.core.datetime.DeviceTimeZone
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

```kotlin
object DeviceTimeZone {
    fun current(): TimeZone
}
```

- `parse`: parses an ISO 8601 date-time string to epoch milliseconds. The instant is fixed by the offset carried in the string (trailing `Z` or numeric offset), so the result is timezone-independent.
- `format`: formats epoch millis to string. Defaults to `ISO_FORMAT` and UTC. Formatters are built once per pattern, time zone and locale and reused, so formatting in a list costs no more per row than the first call.
- `DeviceTimeZone.current()`: the zone the device is set to. Prefer it to `TimeZone.currentSystemDefault()` on any path that runs often: on iOS that call reloads the zone's rules each time (over half a millisecond), while `DeviceTimeZone` resolves the zone once and again only after the system reports a change.

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

On JVM the native formatter is `SimpleDateFormat` with `Locale.getDefault()`; on iOS it is `NSDateFormatter` with the device locale. The browser (wasmJs) has neither, so Synapse renders these fields itself, with fixed output:

- Month and day names are English, whatever the browser locale (`MMM` gives `Mar`, `EEEE` gives `Friday`).
- `a` is always `AM` / `PM` and `G` is always `AD`.
- `zzz` and `zzzz` print the time-zone ID (`Europe/London`), not a zone name or abbreviation.

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

**Platforms**: JVM (Android apps consume the JVM artifact; there is no separate Android target), iOS (`iosArm64`, `iosSimulatorArm64`), and wasmJs (browser, with the locale limits above). Uses `kotlinx.datetime.TimeZone`.
