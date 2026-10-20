# Usage Examples

## Buttons

```kotlin
PrimaryButton(
    model = "Submit".asText().asButton(),
    state = if (isLoading) ButtonState.Loading else ButtonState.Enabled,
    onClick = { viewModel.emit(Intent.OnSubmit) }
)
```

## Text Fields

```kotlin
LabelTextField(
    model = TextInputModel(label = "Email".asText(), value = email, placeholder = "Enter email".asText()),
    onValueChange = { email = it }
)
```

## Currency field

```kotlin
// Contract: a null amount is an empty field, so the placeholder shows until the user types.
val amount = CurrencyInputModel(
    label = Text.Localized(Res.string.amount),
    amount = CurrencyAmount(amount = null, currency = Currency.GBP),
    placeholder = Text.Localized(Res.string.amount_placeholder),
)

// Screen
CurrencyTextField(
    model = state.amount,
    onAmountChanged = { minorUnits -> viewModel.emit(Intent.OnAmountChanged(minorUnits)) },   // null when cleared
)
```

## Date Picker

```kotlin
DatePickerBottomSheet(
    isVisible = showPicker,
    model = DatePickerModel(selectedDate = selectedMs, minDate = null, maxDate = null),
    onDateSelected = { millis -> selectedMs = millis },
    onDismissRequest = { showPicker = false }
)

// Localized labels, built once in the contract or mapper
val datePicker = DatePickerModel(
    selectedDate = null, minDate = null, maxDate = null,
    monthLabels = listOf(Res.string.january, /* … */ Res.string.december).map { Text.Localized(it) },
    weekdayLabels = listOf(Res.string.sun, /* … */ Res.string.sat).map { Text.Localized(it) },   // Sunday first
    resetLabel = Text.Localized(Res.string.reset),
    doneLabel = Text.Localized(Res.string.done),
)
```

## Top Nav Bar

```kotlin
// The built-in back icon announces "Back"; give it a localized label for other languages
val topBar = TopNavBarModel.withTitle(
    title = Text.Localized(Res.string.settings),
    leadingIconType = NavBarIconType.Back,
    leadingIconLabel = Text.Localized(Res.string.back),
)

TopNavBar(model = state.topBar, onLeadingClick = { viewModel.emit(Intent.OnBackClick) })
```

## Scaffold

```kotlin
Scaffold(topBar = { /* toolbar */ }) { padding ->
    Column(Modifier.padding(padding)) { /* content */ }
}
```

## Bottom Navigation Bar

```kotlin
// The bar paints behind the system navigation bar and keeps its items above it: no navigationBarsPadding() needed.
Scaffold(
    bottomBar = {
        BottomNavigationBar(
            model = BottomNavigationBarModel(
                items = listOf(
                    BottomNavigationItem(
                        id = "home",
                        icon = Image.Glyph(Res.drawable.ic_home),
                        label = "Home".asText(),
                    ),
                    BottomNavigationItem(
                        id = "search",
                        icon = Image.Glyph(Res.drawable.ic_search),
                        label = "Search".asText(),
                    ),
                    BottomNavigationItem(
                        id = "inbox",
                        icon = Image.Glyph(Res.drawable.ic_inbox),
                        selectedIcon = Image.Glyph(Res.drawable.ic_inbox_filled),
                        label = "Inbox".asText(),
                        badge = BottomNavigationBadge.Count(3),
                    ),
                    BottomNavigationItem(
                        id = "profile",
                        icon = Image.Glyph(Res.drawable.ic_profile),
                        label = "Profile".asText(),
                        badge = BottomNavigationBadge.Dot,
                    ),
                ),
                selectedId = currentTab,
            ),
            onItemSelected = { id -> viewModel.emit(Intent.SwitchTab(id)) },
        )
    },
) { padding ->
    Column(Modifier.padding(padding)) { /* content */ }
}
```

## Liquid Glass Bottom Navigation Bar

```kotlin
// Floating-island placement: the padding lifts the island off the screen's edges. It keeps clear of the system
// navigation bar by itself.
Scaffold(
    bottomBar = {
        LiquidGlassBottomNavigationBar(
            model = BottomNavigationBarModel(
                items = listOf(
                    BottomNavigationItem(
                        id = "home",
                        icon = Image.Glyph(Res.drawable.ic_home),
                        label = "Home".asText(),
                    ),
                    BottomNavigationItem(
                        id = "discover",
                        icon = Image.Glyph(Res.drawable.ic_compass),
                        label = "Discover".asText(),
                    ),
                    BottomNavigationItem(
                        id = "library",
                        icon = Image.Glyph(Res.drawable.ic_library),
                        selectedIcon = Image.Glyph(Res.drawable.ic_library_filled),
                        label = "Library".asText(),
                        badge = BottomNavigationBadge.Count(12),
                    ),
                ),
                selectedId = currentTab,
            ),
            modifier = Modifier.padding(
                horizontal = Theme.spacing.x4,
                vertical = Theme.spacing.x2,
            ),
            onItemSelected = { id -> viewModel.emit(Intent.SwitchTab(id)) },
        )
    },
) { padding ->
    Column(Modifier.padding(padding)) { /* content */ }
}
```

## Tray

```kotlin
// Tray with a sticky primary action
Tray(
    onDismissRequest = { viewModel.emit(Intent.DismissSheet) },
    stickyBottom = {
        PrimaryButton(
            model = "Confirm".asText().asButton(),
            onClick = { viewModel.emit(Intent.Confirm) }
        )
    }
) {
    Column { /* form fields */ }
}

// ScrollableTray wrapping a LazyColumn — caller renders its own close button
ScrollableTray(onDismissRequest = { viewModel.emit(Intent.DismissSheet) }) {
    Column {
        Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
            IconButton(onClick = { viewModel.emit(Intent.DismissSheet) }) { /* close icon */ }
        }
        LazyColumn { items(rows) { RowItem(it) } }
    }
}

// A screen that is itself a bottomSheet() destination: navigation draws the sheet
// entry<PriceRoute>(metadata = bottomSheet()) { PriceScreen(...) }
TraySurface {
    Column { /* header, options */ }
}
```

## Checkbox

```kotlin
LabelCheckbox(
    model = CheckboxModel(label = "Accept terms".asText(), checked = isChecked),
    onCheckedChange = { isChecked = it }
)
```

## Progress

```kotlin
ProgressBar(
    model = ProgressBarModel(value = 75f, max = 100f, label = "Upload".asText(), showPercentage = true)
)

CircularProgress(
    model = CircularProgressModel(value = 72f, max = 100f, label = "Daily Goal".asText())
)
```

## Rating

```kotlin
RatingInput(
    model = RatingInputModel(rating = 3, maxStars = 5),
    onRatingChange = { newRating -> rating = newRating }
)
```

## Chips

```kotlin
// Single select. Tapping the selected chip again clears it, so the new selection can be empty:
// read it with firstOrNull(). To keep a selection at all times, ignore the empty set instead:
// onSelectionChange = { keys -> keys.firstOrNull()?.let { selectedSize = it } }
// selectedSize: String?
ChipGroup(
    model = ChipGroupModel(
        options = listOf(ChipOption("s", "Small".asText()), ChipOption("m", "Medium".asText()), ChipOption("l", "Large".asText())),
        selectedKeys = setOfNotNull(selectedSize),
    ),
    onSelectionChange = { selectedSize = it.firstOrNull() }
)

// Multi select
ChipGroup(
    model = ChipGroupModel(
        options = listOf(ChipOption("a", "Android".asText()), ChipOption("i", "iOS".asText()), ChipOption("w", "Web".asText())),
        selectedKeys = selectedPlatforms,
        multiSelect = true,
    ),
    onSelectionChange = { selectedPlatforms = it }
)
```

## Tab Layout

```kotlin
TabLayout(
    model = TabLayoutModel(tabs = listOf(TabItem("Overview".asText()), TabItem("Details".asText())), selectedIndex = tab),
    onTabSelected = { tab = it },
) { selectedIndex ->
    when (selectedIndex) {
        0 -> OverviewContent()
        1 -> DetailsContent()
    }
}
```

## Liquid Glass Tab Layout

```kotlin
LiquidGlassTabLayout(
    model = TabLayoutModel(
        tabs = listOf(TabItem("Day".asText()), TabItem("Week".asText()), TabItem("Month".asText())),
        selectedIndex = range,
    ),
    modifier = Modifier.padding(horizontal = Theme.spacing.x4),
    onTabSelected = { range = it },
) { selectedIndex ->
    when (selectedIndex) {
        0 -> DayChart()
        1 -> WeekChart()
        2 -> MonthChart()
    }
}
```

## Radio Group

```kotlin
// Vertical
RadioGroup(
    model = RadioGroupModel(
        options = listOf(RadioOption("sm", "Small".asText()), RadioOption("md", "Medium".asText()), RadioOption("lg", "Large".asText())),
        selectedKey = selectedSize,
    ),
    onSelectionChange = { selectedSize = it }
)

// Horizontal
RadioGroup(
    model = RadioGroupModel(
        options = listOf(RadioOption("y", "Yes".asText()), RadioOption("n", "No".asText())),
        selectedKey = answer,
    ),
    horizontal = true,
    onSelectionChange = { answer = it }
)
```

## Slider

```kotlin
Slider(
    model = SliderModel(value = severity, min = 1f, max = 10f, step = 1f, label = "Severity".asText(), showValue = true),
    onValueChange = { severity = it }
)
```

## Stepper

```kotlin
Stepper(
    model = StepperModel(value = quantity, min = 0, max = 20, step = 1, label = "Quantity".asText()),
    onValueChange = { quantity = it }
)
```

## Timer

```kotlin
Timer(
    model = TimerModel(elapsedMs = elapsed, running = isRunning, label = "Workout".asText()),
    onStartStop = { isRunning = !isRunning },
    onReset = { elapsed = 0L; isRunning = false }
)
```

## Time Picker

```kotlin
TimePicker(
    model = TimePickerModel(hour = hour, minute = minute, is24Hour = true, label = "Alarm".asText()),
    onTimeChange = { h, m -> hour = h; minute = m }
)
```

## Confirm Dialog

```kotlin
ConfirmDialog(
    model = ConfirmDialogModel(
        title = "Delete item?".asText(),
        message = "This action cannot be undone.".asText(),
        confirmLabel = "Delete".asText(),
        cancelLabel = "Cancel".asText(),
    ),
    onConfirm = { viewModel.emit(Intent.ConfirmDelete) },
    onCancel = { showDialog = false }
)
```

## Empty State

```kotlin
EmptyState(
    model = EmptyStateModel(
        icon = Image.Glyph(Res.drawable.ic_empty),
        title = "No items yet".asText(),
        subtitle = "Add your first item to get started".asText(),
        actionLabel = "Add Item".asText(),
    ),
    onActionClick = { viewModel.emit(Intent.AddItem) }
)
```

---

## Chat

### ChatTextArea

```kotlin
// Basic input with camera and mic actions
ChatTextArea(
    model = ChatTextAreaModel(
        value = inputText,
        placeholder = "Message".asText(),
        actions = listOf(
            ChatInputAction(id = "camera", image = Image.Glyph(Res.drawable.ic_camera)),
            ChatInputAction(id = "mic", image = Image.Glyph(Res.drawable.ic_mic)),
        ),
    ),
    onValueChange = { inputText = it },
    onSend = { viewModel.emit(Intent.SendMessage(inputText)) },
    onActionClick = { actionId ->
        when (actionId) {
            "camera" -> viewModel.emit(Intent.OpenCamera)
            "mic" -> viewModel.emit(Intent.StartRecording)
        }
    },
)

// With attachments
ChatTextArea(
    model = ChatTextAreaModel(
        value = inputText,
        placeholder = "Message".asText(),
        attachments = listOf(
            ChatAttachment.Image(id = "1", image = Image.Bitmap(filePath = photoPath)),
            ChatAttachment.Audio(id = "2", durationMs = 15_000),
        ),
        actions = listOf(
            ChatInputAction(id = "camera", image = Image.Glyph(Res.drawable.ic_camera)),
        ),
    ),
    onValueChange = { inputText = it },
    onSend = { viewModel.emit(Intent.SendMessage(inputText)) },
    onRemoveAttachment = { attachment -> viewModel.emit(Intent.RemoveAttachment(attachment.id)) },
    onActionClick = { actionId -> /* handle */ },
)
```

### MessageBubble

```kotlin
// Simple text message
MessageBubble(
    model = MessageBubbleModel(
        text = "Hello!".asText(),
        timestamp = "9:41 AM".asText(),
        variant = MessageVariant.Outgoing,
        status = MessageStatus.Read,
    ),
)

// Rich text with formatting
MessageBubble(
    model = MessageBubbleModel(
        text = Text.listOf(
            "Hey ".asText(),
            "@Kenny".asText(format = TextFormat.Mention),
            "! The new feature is ".asText(),
            "ready".asText(format = TextFormat.Bold),
        ),
        timestamp = "9:42 AM".asText(),
        variant = MessageVariant.Incoming,
    ),
)

// With images
MessageBubble(
    model = MessageBubbleModel(
        text = "Check these out".asText(),
        images = listOf(
            Image.Bitmap(filePath = "https://example.com/photo1.jpg"),
            Image.Bitmap(filePath = "https://example.com/photo2.jpg"),
        ),
        timestamp = "9:43 AM".asText(),
        variant = MessageVariant.Outgoing,
        status = MessageStatus.Delivered,
    ),
    onImageClick = { index -> viewModel.emit(Intent.OpenImage(index)) },
)

// With audio
MessageBubble(
    model = MessageBubbleModel(
        audio = MessageAudio(
            durationMs = 34_000,
            progress = 0.4f,
            isPlaying = true,
            waveform = waveformData,
        ),
        timestamp = "9:44 AM".asText(),
        variant = MessageVariant.Outgoing,
        status = MessageStatus.Delivered,
    ),
    onPlayPause = { viewModel.emit(Intent.TogglePlayback) },
)

// Grouped consecutive messages (tightened corners)
MessageBubble(
    model = MessageBubbleModel(
        text = "First message".asText(),
        timestamp = "9:45 AM".asText(),
        variant = MessageVariant.Incoming,
    ),
)
MessageBubble(
    model = MessageBubbleModel(
        text = "Second message from same sender".asText(),
        timestamp = "9:45 AM".asText(),
        variant = MessageVariant.Incoming,
        isGrouped = true, // tightens the sender-side top corner
    ),
)
```

---

## Charts

### Bar Chart

```kotlin
// Simple
BarChart(
    model = BarChartModel(
        entries = listOf(
            ChartEntry(value = 45f, label = "Mon"),
            ChartEntry(value = 80f, label = "Tue"),
            ChartEntry(value = 65f, label = "Wed"),
            ChartEntry(value = 90f, label = "Thu"),
            ChartEntry(value = 55f, label = "Fri"),
        ),
        title = "Weekly Sales".asText(),
        showValues = true,
    )
)

// Multi-series grouped
BarChart(
    model = BarChartModel(
        series = listOf(
            ChartSeries(
                entries = listOf(ChartEntry(120f, "Q1"), ChartEntry(180f, "Q2"), ChartEntry(150f, "Q3")),
                label = "Revenue".asText(),
            ),
            ChartSeries(
                entries = listOf(ChartEntry(80f, "Q1"), ChartEntry(110f, "Q2"), ChartEntry(95f, "Q3")),
                label = "Costs".asText(),
            ),
        ),
        title = "Quarterly Report".asText(),
    )
)
```

### Line Chart

```kotlin
// With area fill
LineChart(
    model = LineChartModel(
        entries = listOf(
            ChartEntry(20f, "Jan"), ChartEntry(35f, "Feb"), ChartEntry(28f, "Mar"),
            ChartEntry(50f, "Apr"), ChartEntry(42f, "May"), ChartEntry(60f, "Jun"),
        ),
        title = "Growth Trend".asText(),
        showArea = true,
    )
)

// Multi-series
LineChart(
    model = LineChartModel(
        series = listOf(
            ChartSeries(
                entries = listOf(ChartEntry(10f, "W1"), ChartEntry(30f, "W2"), ChartEntry(25f, "W3"), ChartEntry(45f, "W4")),
                label = "Users".asText(),
            ),
            ChartSeries(
                entries = listOf(ChartEntry(5f, "W1"), ChartEntry(15f, "W2"), ChartEntry(20f, "W3"), ChartEntry(35f, "W4")),
                label = "Sessions".asText(),
            ),
        ),
        title = "Weekly Metrics".asText(),
        showArea = true,
        smoothCurve = true,
    )
)
```

### Pie Chart

```kotlin
// Simple
PieChart(
    model = PieChartModel(
        slices = listOf(
            PieSlice(value = 35f, label = "Mobile".asText()),
            PieSlice(value = 30f, label = "Desktop".asText()),
            PieSlice(value = 20f, label = "Tablet".asText()),
            PieSlice(value = 15f, label = "Other".asText()),
        ),
        title = "Traffic Sources".asText(),
    )
)

// Donut
PieChart(
    model = PieChartModel(
        slices = listOf(
            PieSlice(value = 72f, label = "Complete".asText(), color = Color(0xFF34D399)),
            PieSlice(value = 28f, label = "Remaining".asText(), color = Color(0xFFE2E8F0)),
        ),
        title = "Progress".asText(),
        donutFraction = 0.6f,
    )
)
```
