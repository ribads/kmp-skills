# Charts Reference

## Bar Chart

```kotlin
@Composable fun BarChart(
    model: BarChartModel, modifier: Modifier = Modifier,
    height: Dp = 240.dp, invertedColors: Boolean = isSystemInDarkTheme(),
)
```

## Line Chart

```kotlin
@Composable fun LineChart(
    model: LineChartModel, modifier: Modifier = Modifier,
    height: Dp = 240.dp, invertedColors: Boolean = isSystemInDarkTheme(),
)
```

## Pie Chart

```kotlin
@Composable fun PieChart(
    model: PieChartModel, modifier: Modifier = Modifier,
    invertedColors: Boolean = isSystemInDarkTheme(),
)
```

---

## Chart Models

```kotlin
@Immutable
data class ChartEntry(val value: Float, val label: String = "")

@Immutable
data class ChartSeries(
    val entries: List<ChartEntry>,
    val label: Clause? = null,
    val color: Color? = null,
)

@Immutable
data class PieSlice(
    val value: Float,
    val label: Clause? = null,
    val color: Color? = null,
)

@Immutable
data class PieChartModel(
    val slices: List<PieSlice>,
    val title: Clause? = null,
    val donutFraction: Float = 0f,       // 0f = full pie, 0.6f = typical donut
    val showPercentages: Boolean = true,
    val showLegend: Boolean = true,
    val animate: Boolean = true,
)

@Immutable
data class BarChartModel(
    val series: List<ChartSeries>,
    val title: Clause? = null,
    val showGrid: Boolean = true,
    val showValues: Boolean = false,
    val animate: Boolean = true,
    val cornerRadius: Float = 8f,
) {
    companion object {
        // Single-series convenience constructor
        operator fun invoke(
            entries: List<ChartEntry>, title: Clause? = null, color: Color? = null,
            showGrid: Boolean = true, showValues: Boolean = false,
            animate: Boolean = true, cornerRadius: Float = 8f,
        ): BarChartModel
    }
}

@Immutable
data class LineChartModel(
    val series: List<ChartSeries>,
    val title: Clause? = null,
    val showGrid: Boolean = true,
    val showDots: Boolean = true,
    val smoothCurve: Boolean = true,
    val showArea: Boolean = false,
    val animate: Boolean = true,
    val lineWidth: Float = 3f,
    val dotRadius: Float = 5f,
) {
    companion object {
        // Single-series convenience constructor
        operator fun invoke(
            entries: List<ChartEntry>, title: Clause? = null, color: Color? = null,
            showGrid: Boolean = true, showDots: Boolean = true,
            smoothCurve: Boolean = true, showArea: Boolean = false,
            animate: Boolean = true, lineWidth: Float = 3f, dotRadius: Float = 5f,
        ): LineChartModel
    }
}
```
