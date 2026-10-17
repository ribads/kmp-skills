# Chat Reference

## ChatTextArea

Chat-optimised text input with a spacious text field on top and an action toolbar below with caller-defined action icons and an animated send button.

Actions are data-driven via `ChatInputAction` on the model, making the toolbar fully extensible without changing the composable signature.

```kotlin
@Composable fun ChatTextArea(
    model: ChatTextAreaModel,
    modifier: Modifier = Modifier,
    maxLines: Int = 6,
    onValueChange: (String) -> Unit,
    onSend: () -> Unit,
    onRemoveAttachment: ((ChatAttachment) -> Unit)? = null,
    onActionClick: ((actionId: String) -> Unit)? = null,
)

@Stable
data class ChatTextAreaModel(
    val value: String,
    val placeholder: Clause,
    val attachments: List<ChatAttachment> = emptyList(),
    val actions: List<ChatInputAction> = emptyList(),
    val sendLabel: Clause = "Send".asText(),   // the send button's screen-reader label
)

@Immutable
data class ChatInputAction(
    val id: String,
    val image: Image,                            // its contentDescription is the action's screen-reader label
    val enabled: Boolean = true,
)
```

### Attachments

The component displays attachment previews but does not pick or record media — that is the caller's responsibility.

```kotlin
@Immutable
sealed interface ChatAttachment {
    val id: String

    /** Image thumbnail preview. */
    @Immutable
    data class Image(
        override val id: String,
        val image: com.ribads.synapse.ui.element.image.Image,
    ) : ChatAttachment

    /** Audio recording shown as a compact chip with a mic icon and duration. */
    @Immutable
    data class Audio(
        override val id: String,
        val durationMs: Long,
    ) : ChatAttachment
}
```

### Visual details

- 24dp corner radius container with 0.5dp border
- `animateContentSize` with spring for smooth height transitions
- Attachment strip: horizontal scrollable row of 56dp image thumbnails and audio chips, each with an 18dp circle remove button
- Send button: 34dp circle with Canvas arrow icon, spring bounce scale animation (appears when input has content). While shown it is announced as a button labelled `sendLabel`; while hidden it is neither tappable nor announced.
- Action icons: 22dp; a `Glyph` is tinted with `element.secondary`, an `Artwork` is drawn as authored. A disabled action ignores taps and dims only its tint (35% alpha), so a disabled `Glyph` fades but a disabled `Artwork` looks the same as an enabled one; use glyphs for actions that can be disabled.

---

## MessageBubble

A single chat message bubble supporting text, images, and audio.

The bubble renders with asymmetric corner radii (18dp large, 4dp tail) that tighten on the sender edge when `isGrouped` is true, giving a smooth cascading look for consecutive messages from the same sender.

The caller is responsible for horizontal alignment (start for incoming, end for outgoing).

```kotlin
@Composable fun MessageBubble(
    model: MessageBubbleModel,
    modifier: Modifier = Modifier,
    onImageClick: ((index: Int) -> Unit)? = null,
    onPlayPause: (() -> Unit)? = null,
)

@Stable
data class MessageBubbleModel(
    val text: Clause? = null,
    val images: List<Image> = emptyList(),
    val audio: MessageAudio? = null,
    val timestamp: Clause,
    val variant: MessageVariant,
    val status: MessageStatus? = null,
    val isGrouped: Boolean = false,
)

enum class MessageVariant { Outgoing, Incoming }

enum class MessageStatus { Sending, Sent, Delivered, Read, Failed }

@Stable
data class MessageAudio(
    val durationMs: Long,
    val progress: Float = 0f,
    val isPlaying: Boolean = false,
    val waveform: List<Float> = emptyList(),
)
```

### Visual details

- Max bubble width: 280dp
- Asymmetric corners: 18dp (large) / 4dp (tail on sender side); grouped messages tighten both sender corners
- Images render edge-to-edge inside the clipped bubble
- Image grid layouts: 1 image (16:10), 2 images (side-by-side squares), 3 images (1 large + 2 stacked), 4+ images (2x2 grid with "+N" overlay)
- Audio waveform with play/pause Canvas icon and progress-based coloring
- Canvas-drawn status indicators: dot (Sending), single check (Sent), double check (Delivered), double check in accent (Read), exclamation (Failed)
- Rich text via `Clause` — supports `TextFormat.Bold`, `Italic`, `BoldItalic`, `Mention`, `Emphasis`, `Success`, `Error`, `Caution`, etc.
