# Layout relationships before coordinates

Identify the available space and its owner, then determine which elements flow, overlap, repeat, anchor to another region, or occupy remaining space. A design coordinate records one result. Code should express the relationship that must survive a relevant change.

Choose inline text content, a separate region or an overlay from their actual relationship; do not simulate reserved geometry with glyph whitespace. Keep the relationship valid for the supported content and host bounds.

## Start with the simplest relationship

| Relationship | Starting choice | What should remain easy to change |
| --- | --- | --- |
| Sequential content | Row or Column with spacing/alignment | Reorder a child or change its content without recomputing sibling positions |
| Fixed leading/trailing content and flexible middle | Row/Column with remaining-space allocation | Enlarge one region and let the flexible region adapt |
| Background, badge or intentional overlap | Box and local alignment/offset | Move decoration relative to the correct owner |
| Repetition with bounded viewport | An appropriate lazy/grid/scrolling container | Preserve identity, allocation and overflow rules |
| Multiple interdependent anchors or cross-region alignments | ConstraintLayout | Express links, chains or barriers instead of manually synchronizing coordinates |
| Measurement not expressible by these relationships | Focused custom layout | Explain the missing measurement capability and keep it local |

Do not turn an ordinary vertical form into a constraint graph. Conversely, when multiple elements depend on each other's edges, prefer ConstraintLayout where available to express those dependencies rather than compensating offsets or deep incidental nesting; another implementation is acceptable when it expresses the relationships clearly and preserves the required change boundaries. The API name alone does not establish a suitable relationship. Check whether the project provides the required dependency before adopting it. Replacing offset with padding does not remove coordinate coupling.

### Example: choose by relationship, not by count

A label and a value form a simple horizontal row.

| Bad | Good |
| --- | --- |
| Introduce absolute offsets or a constraint graph solely because there are two children. | Use a Row with the required allocation and spacing. |

Interdependent anchors can justify ConstraintLayout; overlay composition can justify Box. Neither is intrinsically a failure.

## Inline content and reserved space

For mixed text and composable content, consider inline text content with an explicit placeholder when the element belongs to the text flow; use a separate layout region when it has independent alignment, and an overlay when overlap is intentional. In Compose, `AnnotatedString` with `InlineTextContent` is one option for inline content, not a mandatory API for every icon beside text. See the [official inline-content contract](https://developer.android.com/reference/kotlin/androidx/compose/foundation/text/InlineTextContent). Leading spaces, line breaks or offsets must not stand in for a measurement dependency; intentional textual whitespace and intentional decorative offsets remain valid.

### Example: reserve space through measurement

A trailing badge needs a measured region alongside variable text.

| Bad | Good |
| --- | --- |
| Pad the text with spaces or reserve pixels based on one screenshot. | Allocate the badge region through layout; use actual inline-content measurement when it must participate in text flow. |

Plain typographic whitespace inside real text remains valid; use layout allocation when the purpose is reserving space.

## Keep placement with the parent and arrangement with the child

A parent owns the order and placement of regions. A child owns the layout inside its allocated bounds. If moving a child requires editing that child's internal coordinates, the boundary likely mixes these responsibilities.

### Example: changing title width without moving the trailing region manually

**Scenario:** a single-line title receives remaining width; trailing metadata reserves `trailingWidth`. The parent supplies bounded width sufficient for both regions, and title truncation is allowed. The 180dp below is an incidental reference-image coordinate.

**Bad** — title allocation and metadata position must be synchronized by hand:

```kotlin
Box(Modifier.fillMaxWidth()) {
    Text(title, Modifier.width(180.dp), maxLines = 1, overflow = TextOverflow.Ellipsis)
    Text(metadata, Modifier.offset(x = 180.dp).width(trailingWidth))
}
```

**Good** — express the allocation in the layout:

```kotlin
Row(Modifier.fillMaxWidth()) {
    Text(title, Modifier.weight(1f), maxLines = 1, overflow = TextOverflow.Ellipsis)
    Text(metadata, Modifier.width(trailingWidth))
}
```

**Why / boundary:** the title receives the actual remaining space when the host or trailing width changes. A smaller unsupported host still needs a product-defined fallback; weight does not solve every width. Fixed offsets remain valid for intentional decoration tied to a local owner.

Keep shared dimensions as one source or derive one from the other when they express a real dependency. For example, a progress bar below a centered image should be linked to the image's bottom or derived from the same size contract. A separately maintained magic offset is easy to miss when changing the image. A centered Column of both elements instead centers their combined bounds; it is appropriate only if that is the intended invariant.

## Design for width and height separately

For the relevant host range, decide:

- Which dimensions follow content, which are allocated, and which have a justified fixed/minimum/maximum size?
- Which region receives remaining space? What remains visible when that space decreases?
- Below the usable minimum, does content wrap, switch arrangement, scroll, or use another supported presentation?

### Example: an editor in a short supported window

**Scenario:** Save/Cancel must remain visible while editing fields may scroll. The host supplies bounded height large enough for the required header and actions.

| Bad | Good |
| --- | --- |
| Place fields and actions at fixed vertical offsets; adding help text requires moving both manually. | Let a Column measure header/help and actions, and allocate bounded remaining height to scrollable fields. |
| Make only the inner fields scroll while the outer dialog keeps a height larger than its host. | Bound the outer content to the real available height; keep required actions outside the field scroller. |

**Why / boundary:** content growth changes allocation rather than synchronized coordinates. A maximum width does not constrain height. If even the fixed regions cannot fit, use the product's supported alternate presentation; do not claim scrolling alone solves it.

Minimum width/height should protect a real content or interaction requirement. Forcing requiredSize larger than the parent does not establish adaptation. Make overflow behavior deliberate. Whole-canvas scaling can fit a genuine fixed-coordinate scene; ordinary text, forms and controls also have readability, font scale and touch-size constraints, so shrinking them together needs justification.

A repeating group may use equal shares at one item count and fixed-width scrolling at another. Establish the allocation rule independently of item identity/order. Font scale, long text and RTL can invalidate a layout that merely tracks screen width.

## Decoration is not content measurement

Inspect visible pixels and transparent asset margins before changing component geometry to compensate for artwork. Separate an overlay's canvas from the content it decorates. Check clipping at the child and its ancestors. Different artwork can legitimately share a content layout or require a deliberate variant; neither assumption follows from asset names alone.

Give host insets and constraints one explicit owner and consume them at the intended layout boundary. Each animation content instance renders its provided target state, since outgoing and incoming states may coexist. Use observable configuration/resource APIs for values that must change with the host; a deliberately captured operation-specific snapshot has a different lifetime.

### Example: transparent artwork does not define the hit region

A decorative asset contains transparent outer margins around a visible button surface.

| Bad | Good |
| --- | --- |
| Use the full image bounds as the only source of content padding and hit size. | Keep the interaction/content geometry explicit; fit the artwork using its intended crop/insets. |

Do not crop a required decoration merely to simplify measurement, or enlarge a control beyond the supported design without a requirement.

## Challenge the assembly

Trace a relevant change in source: moving an element, enlarging a trailing region, adding a line or reducing supported host height. The parent and a standalone sample can supply different constraints; use the production host contract from [integration](integration.md).

### Example: optional content changes the constraints

A header must remain usable with a longer title and a missing leading action.

| Bad | Good |
| --- | --- |
| Keep the title offset anchored to the removed action’s old screenshot position. | Express the required alignment against the remaining real parent/regions and apply the actual overflow policy. |

The assembled layout matters; individually reasonable children can still compete for the same space.

## Preserve the unaffected assembly

When relocating one action, compare the old and new positions of its siblings at the normal supported size before introducing a fallback for narrower space. A new row or extra header height may make an action reachable but unnecessarily move every section or hide the primary action below the fold. Use the available normal-size space first; make any necessary narrow-size reflow explicit. Stacked outline/fill text must use identical content and measurement constraints so their glyphs coincide.

### Example: local content changes stay local

Only a card’s subtitle becomes optional.

| Bad | Good |
| --- | --- |
| Rewrite the surrounding page allocation and fixed footer to accommodate the card. | Let the card express its optional region within the existing page contract; change the parent only if its assumptions are actually invalid. |

A documented parent constraint defect can require a parent change. Avoid incidental whole-page redesign.

## Make dimension contracts executable

For a reusable region, accept the caller's Modifier on its root and distinguish its preferred extent from hard bounds imposed by its parent. Keep a dimension shared by dependent artwork and content in one meaningful local value. Avoid moving all numbers into an undifferentiated constants file; name sizes only when that reveals ownership or a relationship.

When subtracting occupied widths, specify the remaining region's lower bound and what happens before it becomes negative or too small for its content. Choose reflow, scrolling or a supported minimum at that boundary; clamping alone must not silently hide required content. Inspect the supported smallest and largest hosts and normal dimensions after a local change. Constraints belong to the region whose siblings depend on them, not to unrelated leaf components.

### Example: derive one boundary rather than duplicate constants

Two adjacent regions share the same available width with a specified gap.

| Bad | Good |
| --- | --- |
| Assign independent constants whose sum only happens to fit the reference window. | Use the parent’s supported constraints and one relationship for allocation and gap. |

Named dimensions still belong in project resources/theme policy. A formula is not inherently better for a genuinely fixed-size asset.

## Centered content with side actions

For a centered logo/title and independently sized side controls, establish whether the center is relative to the whole parent or the remaining free space. Reserve the side regions and define the supported narrow-width fallback before they intersect. A plain Row may change the centering invariant; independent Box alignment may overlap. Use simple flow/overlay where it preserves the relationship, and explicit interdependent constraints when needed. Reflow, reduced optional content or scrolling must follow the actual product priorities, not silently remove required actions.

For conditional regions, define whether absence releases space, preserves a reserved slot or changes the anchor. Apply that decision at actual callers; neither matching an incidental coordinate nor automatically re-centering establishes correctness.

### Example: define what centered means

A title must stay centered in the whole header while side actions have unequal widths.

| Bad | Good |
| --- | --- |
| Center it only in the remaining Row space, shifting it toward the smaller side. | Use a parent-centered region plus sufficient exclusion space for the actual actions, with explicit truncation/collision behavior. |

If the requirement instead centers within available content space, the Row solution may already be correct.

## Scope sizing checks to the product contract

Determine whether the region is intentionally fixed-size or responsive before designing boundary samples. Inspect how the code enforces that contract and how its real parent supplies constraints. Do not require a fixed-size business scene to reflow at unsupported small windows. For responsive UI, provide production Previews at the relevant supported bounds and inspect allocation/overflow relationships in source. Window-dependent sizing must follow the production host contract, not just a sample’s bounds.

### Example: fixed and responsive contracts differ

The supported host specifies a fixed-size compact control.

| Bad | Good |
| --- | --- |
| Stretch it to every screen width to satisfy a universal adaptation rule. | Preserve its specified size and handle supported text/host variations within that contract. |

Responsive pages still need both width and height policies; do not use a fixed-control exception for an entire page.
