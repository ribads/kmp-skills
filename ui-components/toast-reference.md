# Toast Reference

Synapse's toast system is a **CompositionLocal-based controller + handler**. Wrap the app root in `ToastHandler { }` once; any composable beneath can pull `Toast.current` to show/dismiss toasts. Multiple toasts are rendered in a vertical stack; the controller drives enter/exit with spring animations.

## Architecture

```
ToastHandler (at root) ──► provides LocalToastController
                           renders ToastOverlay on top of content
                                           │
                                           ├── Top position (default): oldest at top, newest appended below
                                           └── Bottom position: oldest at bottom, newest appended above

Any @Composable ──► Toast.current.show(ToastModel(...))
                    Toast.current.dismiss(id) / dismissAll()
```

Stacking is FIFO visualised from anchor outward. When a toast expires (duration) or is dismissed (swipe / `dismiss(id)`), all siblings reflow with a spring animation to close the gap.

## Model

```kotlin
@Stable
data class ToastModel(
    val message: Clause,
    val intent: ToastIntent = ToastIntent.Info,
    val duration: ToastDuration = ToastDuration.Short,
    val leadingIcon: Image? = null,
)

enum class ToastIntent { Info, Success, Warning, Error }

enum class ToastDuration(val millis: Long) {
    Short(2_500L),
    Long(4_000L),
    Indefinite(5_000_000L),   // sentinel — `Indefinite` is checked by enum identity, no auto-dismiss
}

enum class ToastPosition { Top, Bottom }

@JvmInline value class ToastId(val value: Long)

@Immutable
data class ToastSnapshot(
    val id: ToastId,
    val model: ToastModel,
    val visible: Boolean = true,   // false during exit animation (still in list until animation completes)
)
```

## Controller

```kotlin
@Stable
interface ToastController {
    val toasts: State<List<ToastSnapshot>>
    fun show(model: ToastModel): ToastId
    fun dismiss(id: ToastId)
    fun dismissAll()
}

val LocalToastController: ProvidableCompositionLocal<ToastController>

object Toast {
    val current: ToastController
        @Composable get
}
```

- `show()` returns the `ToastId` — capture it to dismiss the toast programmatically (e.g., cancel an `Indefinite` toast when a network request completes).
- `dismiss()` flips `visible = false` and removes the snapshot after the exit animation (400ms) so the fade/shrink plays. A second `dismiss(id)` for the same id is a no-op.
- `dismissAll()` clears everything with animation.
- Controller lives as long as its `ToastHandler`. Not a singleton — two `ToastHandler`s yield two controllers.

## Handler

```kotlin
@Composable fun ToastHandler(
    modifier: Modifier = Modifier,
    position: ToastPosition = ToastPosition.Top,
    style: ToastStyle = ToastDefaults.style(),
    content: @Composable () -> Unit,
)
```

- Wraps `content` in a `Box(fillMaxSize)` with the toast overlay z-ordered on top.
- Applies the relevant `WindowInsets` automatically (`statusBars` for Top, `navigationBars` for Bottom).
- Caller controls theming via `style` — all defaults read from `Theme`.

## Modal surfaces (trays, sheets, dialogs)

The overlay is part of the host window's composition. Compose renders the modal surfaces in a **separate window stacked above that composition**: `Tray`, `ScrollableTray`, and `DatePickerBottomSheet` go through Material3 `ModalBottomSheet` (a top-level `Dialog`), and `ConfirmDialog` uses a `Popup`. A toast shown while any of them is open is painted behind it (behind the scrim) and only becomes visible once the surface closes. This is the same constraint that applies to Material's own `SnackbarHost`.

Calling `Toast.current.show(...)` from inside a tray or dialog does not change this. The controller state is shared across the window boundary, but the overlay still draws in the host window, beneath the surface.

For feedback while a modal surface is open, render the message inside that surface's own content instead of relying on the global toast.

## Style

```kotlin
@Immutable
data class ToastStyle(
    val info: ToastIntentStyle,
    val success: ToastIntentStyle,
    val warning: ToastIntentStyle,
    val error: ToastIntentStyle,
    val shape: Shape,
    val contentPadding: PaddingValues,
    val iconSize: Dp,
    val messageStyle: TextStyle,
    val elevation: Dp,
) {
    fun styleFor(intent: ToastIntent): ToastIntentStyle
}

@Immutable
data class ToastIntentStyle(
    val background: Color,
    val content: Color,     // message text and a Glyph icon
    val border: Color,
)

object ToastDefaults {
    @Composable fun style(
        shape: Shape = Theme.shape.card,
        contentPadding: PaddingValues = PaddingValues(
            horizontal = Theme.spacing.x4, vertical = Theme.spacing.x3,
        ),
        iconSize: Dp = 20.dp,
        messageStyle: TextStyle = Theme.typography.body,
        elevation: Dp = 4.dp,
        info: ToastIntentStyle = /* from Theme.colors.intents.accent */,
        success: ToastIntentStyle = /* from Theme.colors.intents.success */,
        warning: ToastIntentStyle = /* from Theme.colors.intents.warning */,
        error: ToastIntentStyle = /* from Theme.colors.intents.error */,
    ): ToastStyle
}
```

Defaults map each intent's palette from `Theme.colors.intents.{accent,success,warning,error}` for the current appearance: `background = surface`, `content = content`, `border = border`. Override one intent by constructing a `ToastIntentStyle` yourself and passing just that param to `ToastDefaults.style(...)`. `style()` is composable, so build the override from roles and it stays correct in both appearances.

## Behaviour

| Aspect | Default |
|---|---|
| Stacking | Oldest at anchor, newest furthest from anchor. Reflow on removal with spring. |
| Enter animation | `fadeIn` + `slideInVertically` (from anchor edge) + `expandVertically`, all spring. |
| Exit animation | `fadeOut` + `slideOutHorizontally` (off right edge) + `shrinkVertically`, all spring. |
| Swipe-to-dismiss | Horizontal drag, threshold 40% of width. Snaps back with spring if below threshold. |
| Tap-to-dismiss | Off. |
| Queue / cap | None — caller discipline. |
| Icon tinting | A `Glyph` leading icon is tinted with the intent style's `content`; an `Artwork` is drawn as authored. |

## Usage

**Root setup:**
```kotlin
SynapseTheme {
    ToastHandler(position = ToastPosition.Top) {
        MainNavigatorHost(...)
    }
}
```

**From any composable:**
```kotlin
val toaster = Toast.current
Button(onClick = {
    toaster.show(ToastModel(
        message = "Saved".asText(),
        intent = ToastIntent.Success,
    ))
}) { ... }
```

**From an MVI screen effect (capture outside `CollectAsEffect` — the lambda is not `@Composable`):**
```kotlin
val toaster = Toast.current
viewModel.effects.CollectAsEffect { effect ->
    when (effect) {
        is Effect.ShowToast -> toaster.show(effect.toast)
    }
}
```

**Indefinite toast with programmatic dismiss:**
```kotlin
val id = toaster.show(ToastModel(
    message = "Uploading…".asText(),
    intent = ToastIntent.Info,
    duration = ToastDuration.Indefinite,
))
// later:
toaster.dismiss(id)
```

**Custom style override:**
```kotlin
ToastHandler(
    style = ToastDefaults.style(
        shape = RoundedCornerShape(24.dp),
        error = ToastIntentStyle(
            background = Theme.colors.intents.error.content,
            content = Theme.colors.surface.primary,
            border = Color.Transparent,
        ),
    ),
) { ... }
```

## Hard rules

1. **One `ToastHandler` per app root.** Nesting yields separate controllers and duplicate toasts.
2. **`Toast.current` panics** if no handler is above it in the tree — the error message points to the fix.
3. **Build `ToastModel` outside composables** — in the Contract, Mapper, or effect emission. Do not inline inside `@Composable`.
4. **`Indefinite` toasts must be dismissed explicitly** — use the returned `ToastId`.
5. **Toasts do not paint over open trays, sheets, or dialogs.** Those render in a separate window above the host composition; surface in-sheet feedback inside the sheet's own content.
