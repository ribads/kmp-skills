---
name: component-authoring
description: "Use when writing a new @Composable that Synapse does not already provide: an app-level component in compose-ui/, or a screen-local section composable in a feature's ui/ module. Covers the escape-hatch gate, file and package layout, parameter ordering, callback naming, model design (Clause over String, sealed variants, Placeholder), colour roles and fixed-appearance regions, and size constants. Trigger when reaching for a custom composable, reviewing one, or deciding whether to promote a component to a shared module."
user-invocable: true
---

# component-authoring: Building App-Level Composables

How to write a `@Composable` that Synapse does not ship, so it behaves like one that does. Everything here mirrors the contract `ui:component` follows internally, so a caller should not be able to tell your component from a Synapse one.

For the catalog of components that already exist, invoke `/ui-components`. For `Clause`, `Image`, and `Theme`, invoke `/ui-element`.

---

## The gate

Before writing any new composable, in order:

1. **Is there a direct match in `/ui-components`?** The catalog is 40+ components; check it.
2. **Can Synapse primitives be composed?** `Card` + `Image` + `Text` covers most "custom" cards.
3. **Does the app's `compose-ui/` already have a wrapper?**

Only then write something new. A one-off layout is not a component. Build it inside the feature first, and promote it when a second feature needs it.

## Where it goes

| Scope | Location |
|---|---|
| Reusable across screens in this app | the app's `compose-ui/` module |
| This screen only | the feature's `ui/` module, in a `section/` subpackage beside the screen |
| Reusable across apps | `ui:component` in Synapse, and then `/ui-components` must be updated in the same PR |

Never inline a multi-element custom composable into `{Name}Screen.kt`. The Screen composes sections; it does not contain them.

---

## File & package layout

```
component/<family>/
├── <Family>.kt              # the one public composable + its private sub-composables
├── model/<Family>Model.kt   # the model(s) the composable accepts
└── internal/<Family>Colors.kt   # colours + CompositionLocal, internal
```

- **One public composable per file**, named after the file. Size variants of the same component (`PrimaryButton` / `SmallButton`) may share a file; unrelated components may not.
- **Private sub-composables live in the same file as their parent.** A `private fun Placeholder(...)` beside the `Item` it shadows is easier to keep in sync than one two directories away.
- **Models go in `model/`**, one file per family. There is no global `ui/models/` bucket.
- **`internal/` holds what the family needs and nobody else may touch**: colours, painters, measurement helpers.

Feature-side, a screen package adds `section/` for its composables and `model/` for its UI models, beside the 7 MVI files.

---

## The composable contract

### Parameter order

```kotlin
@Composable
fun ProductCard(
    model: ProductCardModel,                          // 1. the model, first
    modifier: Modifier = Modifier,                    // 2. modifier, always second
    style: CardStyle = CardStyle.Regular,             // 3. config with defaults
    onClick: OptionalClickCallback,                   // 4. callbacks
    onFavouriteClick: (id: String) -> Unit,
)
```

Note that **required callbacks sit after defaulted config parameters.** That is a deliberate departure from the stock Compose convention of trailing lambdas: it forces callers to pass callbacks as named arguments, which reads better at four callbacks than a pile of trailing braces.

**Containers are the exception.** A component whose job is to wrap content has no model, leads with `modifier`, and ends with a trailing `content` slot:

```kotlin
@Composable
fun Panel(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
)
```

So the full rule is: `model`, `modifier`, config, callbacks, `content`, dropping whichever do not apply. There is no appearance or colour-inversion parameter: see [Colours](#colours).

Synapse's own module holds this at roughly 80%. The known deviations are `Divider` (leads with `color`) and the `field/` family (buries `modifier`). Match the rule above for new components rather than the nearest existing file.

### Callback naming

| Situation | Name |
|---|---|
| Exactly one action | `onClick` |
| Several actions | name by **slot**, not by intent: `onLeadingClick`, `onTrailingIconClick`, `onItemSelected` |
| Value edits | `onValueChange`, `onCheckedChange`, `on<Thing>Changed` |
| Sheet / dialog dismissal | `onDismissRequest`, always |

Name callbacks for the widget, not the consequence: `onTrailingIconClick`, not `onShareClick`. The component does not know it is sharing, and the next screen that reuses it will not be.

Optional click handlers use the `ui:element` typealias so the disabled state is expressible:

```kotlin
typealias OptionalClickCallback = (() -> Unit)?
fun OptionalClickCallback.isEnabled(): Boolean = this != null
```

Callbacks with parameters name them, so call sites read: `onChipClick: (itemId: String, isChecked: Boolean) -> Unit`.

### Slots

Reserve `@Composable` slots for **structural containers** (`Scaffold`, `Tray`, `Panel`) and for **escape hatches on inputs** (a text field's `leadingContent`). Leaf components (buttons, chips, pills, list rows, cards) take a model, never a slot. A slot on a leaf component is how a design system stops being one.

Scope your slots when the content belongs to a layout: `content: @Composable ColumnScope.() -> Unit`.

### Stateless by default

Components render what they are given and report events upward. State lives in `ViewState`.

- **No stateful/stateless pairs**, no `rememberFooState()` factories in public API. Synapse has exactly one, and it is `internal`.
- **No `rememberSaveable`.** Restoration is the ViewModel's problem, not the component's.
- Genuinely local, non-semantic state is fine: focus, password visibility, whether a dropdown is expanded, an in-progress drag.

The one sanctioned exception is a **keyed mirror** for optimistic feedback, when a control must respond before the intent round-trips:

```kotlin
var isChecked by remember(model.checked) { mutableStateOf(model.checked) }
```

Keying on the model field means a new model resets the mirror. Only use it when the local copy is actually mutated. `remember(x) { mutableStateOf(x) }` for a value you only read is just `x` with extra steps.

### No domain models

A component takes UI models. If a composable's signature mentions a domain entity or a use-case DTO, the translation that should have happened in the Mapper has leaked into the view layer. See `/data-boundaries`.

---

## Models

### One model, not a parameter list

If a component renders more than two pieces of content, bundle them:

```kotlin
@Immutable
data class ProductCardModel(
    val id: String,
    val title: Clause,
    val price: Clause,
    val image: Image,
    val badge: Clause? = null,
)
```

Only genuinely atomic controls take primitives: `Switch(checked: Boolean, …)`, `Text(clause: Clause, …)`.

Annotate `@Immutable` when every field is deeply immutable, `@Stable` when a field is a holder whose identity is stable but whose contents can change. Getting this right is what keeps recomposition scoped.

### `Clause`, not `String`

Every piece of user-visible text is a `Clause`; every image is an `Image`. Never a raw `String` or a URL string in a model. That is what lets money, timestamps, inline icons, and localized copy all flow through one channel and get formatted at render time. See `/ui-element`.

### Sealed for variants, enum for states

```kotlin
sealed class ListItemModel
@Immutable data class ActionListItem(…) : ListItemModel()
@Immutable data class CheckableListItem(…) : ListItemModel()

enum class ButtonState { Enabled, Disabled, Loading }
```

**Sealed** when variants render *structurally differently*: the component does one exhaustive `when (model)` and delegates to a private per-variant composable. **Enum** when it is the same rendering in a different visual state.

### `Placeholder` as a first-class variant

Model loading, do not flag it:

```kotlin
@Immutable
sealed class FeedItemModel {
    data class Item(val id: String, val title: Clause) : FeedItemModel()
    data class Placeholder(val id: String) : FeedItemModel()
}
```

```kotlin
when (model) {
    is FeedItemModel.Item        -> Item(model = model, modifier = modifier, onClick = onClick)
    is FeedItemModel.Placeholder -> Placeholder(modifier = modifier)
}

@Composable
private fun Placeholder(modifier: Modifier = Modifier) {
    Box(modifier.height(PlaceholderHeight).fillMaxWidth().shimmer())
}
```

The screen then seeds `ViewState.Default` with a list of `Placeholder`s and the first frame is a skeleton instead of blank space. Give placeholders a stable `id` so they can key a `LazyColumn`.

Synapse ships no loading-box or error-box component, so build these on `Modifier.shimmer()` and `EmptyState` from `ui:component`.

### Companion factories and defaults

Give models the constructors their call sites actually want:

```kotlin
@Immutable
data class ErrorCardModel(
    val image: Image = Image.Glyph(Res.drawable.ic_error),
    val title: Clause = Text.Localized(Res.string.error_title),
    val subtitle: Clause,
    val action: ButtonModel = ButtonModel(title = Text.Localized(Res.string.retry)),
) {
    companion object {
        fun withMessage(subtitle: Clause) = ErrorCardModel(subtitle = subtitle)
    }
}
```

A caller that only knows the error message should only have to pass the error message.

---

## Colours

Every colour comes from a role in `Theme.colors.*`. The theme resolved the appearance before the component runs, so a role read is correct in light and dark without branching. Resolve once at the top of the component and hand the result down through a CompositionLocal rather than threading colours into every sub-composable:

```kotlin
// internal/ProductCardColors.kt
@Immutable
internal data class ProductCardColors(
    val titleColor: Color = Color.Unspecified,
    val backgroundColor: Color = Color.Unspecified,
)

internal val LocalProductCardColorsProvider = compositionLocalOf { ProductCardColors() }

@Composable
internal fun ProvideProductCardColors(colors: ProductCardColors, content: @Composable () -> Unit) =
    CompositionLocalProvider(LocalProductCardColorsProvider provides colors, content = content)

@Composable
internal fun componentColors() = ProductCardColors(
    titleColor = Theme.colors.element.primary,
    backgroundColor = Theme.colors.surface.secondary,
)
```

```kotlin
ProvideProductCardColors(colors = componentColors()) {
    when (model) { … }
}
```

- **Pick the role for its meaning, not its current value.** Text and icons on the canvas are `element.*`; a layered card is `surface.secondary`; outlines are `border.*`; an enabled or pressed control background is `surfaceInteractive.*` with `elementInteractive.*` on it; anything carrying an intent reads `intents.<intent>.*`. A role picked because it happens to look right in one appearance will be wrong in the other.
- **Sheets, dialogs and menus** paint `surface.raised` and wrap their content in `WithRaisedSurface`, so children that paint `surface.primary` match the container.
- **A container that paints a background provides `LocalContentColor`** for its content, so text and glyphs without explicit colours stay readable on it.
- **Icons take an `Image` and draw it with `Icon(image, tint = ...)`.** A `Glyph` follows the tint (pass the per-state colour); an `Artwork` is drawn as authored. Do not add a "tint this icon" flag: the image type is that decision.
- **Never branch on the appearance to pick a colour** (`isSystemInDarkTheme()`, `Theme.isDark`), and never take an `invertedColors`-style parameter. A caller that needs a region in a fixed appearance (controls over a photo, a camera overlay, a video scrubber) wraps it in `WithAppearance(Appearance.Dark)`, and the component inside just reads roles. `Theme.isDark` is only for choosing a dark asset variant or configuring UI that does not read Synapse roles.
- **No colour literals** outside the app's theme definition. The exception is a categorical data palette (chart series), which needs a variant per appearance.

---

## Sizes and constants

Layout spacing comes from `Theme.spacing.*`, a 4dp-based scale of `x1 … x10, x12, x14, x16, x18, x22, x24, x32` (it is deliberately not contiguous; there is no `x11`).

**Component-intrinsic geometry is not spacing** and does not belong in the token scale. Give it a file-level named constant:

```kotlin
private val StarSize = 28.dp
private val ThumbRadius = 10.dp
private const val AnimationDurationMs = 600
```

PascalCase for `Dp` values, and put them at the top of the file. Raw `.dp` inline is acceptable only for hairline borders, `Canvas` stroke widths via `.dp.toPx()`, and `WindowInsets(0.dp)`.

Typography is always `Theme.typography.<token>`; use `.copy(color = …)` for tweaks, never a fresh `TextStyle`. Raw `.sp` is legitimate only for `Canvas` text that cannot take a `TextStyle`.

Raw `Color(0xFF…)` has essentially one legitimate use: a categorical series ramp for charts, where the semantic token system has nothing to offer. Everything else is `Theme.colors.*`.

---

## Promotion

A component earns its way up one level at a time: screen `section/` → app `compose-ui/` → `ui:component`. Promote on the **second** real consumer, not the first hypothetical one.

Promoting into `ui:component` means it is Synapse public API: update `/ui-components` (the catalog table and the relevant `*-reference.md`) in the same PR. App-level composables in `compose-ui/` are not Synapse API and do not belong in that skill.

---

## Rules

- **Check `/ui-components` first.** Compose primitives before writing anything new.
- **One public composable per file**, private sub-composables beside it, models in `model/`, internals in `internal/`.
- **`model`, `modifier`, config, callbacks, `content`.** Containers drop `model` and lead with `modifier`.
- **Name callbacks for the slot, not the consequence.** `onDismissRequest` for every dismissal.
- **Slots for containers only.** Leaf components take a model.
- **Stateless.** No stateful/stateless pairs, no `rememberSaveable`, no public `rememberXState()`.
- **Never accept a domain model or use-case DTO.**
- **`Clause` for text, `Image` for images**, never a raw `String`.
- **Sealed for structural variants, enum for visual states**, `Placeholder` as a real variant.
- **Colours through `Theme.colors` roles and a per-component CompositionLocal.** Never branch on the appearance; fixed-appearance regions are the caller's `WithAppearance`.
- **Named file-level constants for intrinsic geometry**, `Theme.spacing` for layout.
- **Promote on the second consumer**, and update `/ui-components` when a component lands in `ui:component`.
