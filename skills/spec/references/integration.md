# Fit the actual project

Read the project rules and find the reachable host, state owner and an analogous implementation. Inspect only the relevant capability index and source. A stale index is a lead, not proof of an API's current behavior.

## Establish the requested behavior

Record the required behavior and visual relationships, supported content/hosts, allowed variations and requirement source. Distinguish a product requirement, an approved design and a screenshot of an existing implementation. An existing implementation is a fidelity target only to the extent the task asks to preserve it; its incidental behavior is not automatically a new requirement. Apply explicit user decisions and project instruction priority when sources disagree. Continue independent implementation work, but keep the disputed requirement explicit rather than silently choosing an interpretation.

### Example: an old screenshot is not a new requirement

The explicit task changes a dismissal action while an older screenshot shows the previous behavior.

| Bad | Good |
| --- | --- |
| Preserve the old dismissal merely because it is visible in the screenshot. | Implement the explicit action requirement and preserve the screenshot’s still-applicable visual relationships. |

If authoritative requirements conflict, identify the unresolved choice rather than guessing a third behavior.

## Follow the active project conventions

Start with the changed module's instructions, formatter/configuration and a comparable production caller. Match domain names, file/component organization, state/event style, resource placement and dependency ownership where they fit the requested behavior. Reuse an existing abstraction when its actual contract fits; do not create a parallel architecture for a local UI change.

Mixed styles may reflect a migration or different responsibilities. Prefer explicit current project decisions and the active path for the same responsibility; neither the newest file nor the most common historical pattern automatically wins. When a compatibility wrapper or unusual convention has an unclear purpose that affects the change, inspect its relevant callers and a focused git log/blame/diff. Routine edits do not require a repository-wide history audit.

Respect required behavior and compatibility before stylistic uniformity. Preserve necessary host/SDK workarounds, but do not copy proven defects or retired patterns merely because they exist. If the existing approach cannot satisfy a concrete requirement, explain the mismatch and make the smallest justified departure. Keep unrelated restyling or migrations out of scope. Preserve [fixed APIs and supported variations](integration.md#fixed-apis-and-supported-variations) and explain any concrete incompatibility with the requested behavior.

### Example: migration direction beats a stale precedent

The active module has migrated image loading, while an archived screen still uses the previous wrapper.

| Bad | Good |
| --- | --- |
| Choose the old wrapper because its caller is shorter or more familiar. | Follow the proven current path and preserve its sizing/transform/lifecycle contract. |

An intentionally unmigrated host may require compatibility. Use relevant evidence, not a repository-wide stylistic majority vote.

## Reuse behavior, not names

Before wrapping or replacing an existing facility, inspect the behavior that matters to this task: constraints, placeholder/error handling, media scaling, request transformations, lifecycle and supported preview inputs. Follow the caller into the implementation when those semantics are hidden.

### Example: reuse an active facility rather than a familiar replacement

**Scenario:** an active module already has an image component that applies required URL transformations and default artwork, and its real API supports the new screen's needs.

| Bad | Good |
| --- | --- |
| Add a second loader/wrapper because its API is more familiar, dropping the existing transformation/default policy. | Use the active component following a comparable production caller, passing the screen's actual inputs. |
| Copy an older screen's workaround merely because it predates the current component. | Check current project/migration guidance; inspect the relevant history only if the workaround's continued purpose is unclear. |

**Why / boundary:** consistency preserves behavior, not just names. If the existing facility lacks a required capability or the workaround still serves a real compatibility need, retain/explain that constraint and make a focused change. Neither the newest implementation nor reuse itself is automatically correct.

For changed images or configured backgrounds, apply [the image control contracts](images.md): inspect the actual declaration and request behavior, then wire the supported parameters at the real caller according to avatar, background, content, action or decoration responsibility. Image composables and background modifiers are not interchangeable merely because both accept a model.

## Visual ownership

For explicitly requested reuse, follow the final production caller into the selected facility. Finding an existing button or promising to use it is insufficient if the delivered source still draws a replacement. Check required semantics such as loading, disabled behavior and spacing. If reuse cannot meet a confirmed requirement, explain the concrete limitation and the scoped alternative rather than silently bypassing the agreement.

When project instructions or other skills appear to demand duplicate configuration, distinguish shared component policy from page-specific variation. Apply instruction priority and the user's explicit requirements; keep unresolved conflicts visible. Do not invent page-specific resources simply to satisfy a generic naming checklist.

Identify what is supplied by the window/host, by the current component and by the asset itself. Inspect source assets when borders, gradients, text or dynamic regions might already be present. Drawing the same decoration twice changes the result even if both implementations individually match a reference.

Establish the requested appearance and decoration ownership. An old screenshot or source implementation must be identified as such; it is not automatically an approved design. Verify resolved asset pixels and drawing together rather than inferring appearance from a modifier or asset name.

Apply the project's resource policy. Local Compose constants, shared theme values, resource qualifiers and translated strings serve different needs. Do not create a token system solely because a screenshot contains numbers. Do not hardcode a genuinely configurable or localized value to simplify implementation.

### Example: one owner for modal dimming

The task uses a normal modal Dialog with the system scrim.

| Bad | Good |
| --- | --- |
| Disable default dimming and add another opaque page-covering layer without a custom-host requirement. | Keep the host’s supported dimming behavior; change it only for an explicit visual/window contract with one owner. |

Do not hide or remove the covered UI just to emulate a scrim. See the retained-page example below.

## Host and interop

Establish how the host constrains the composition and who owns insets, scrolling and background. For retained Views or SDK surfaces, identify creation, attachment, updates, detachment and release. Ownership should match the SDK and host's actual lifecycle; composition and Fragment/view lifetimes are not interchangeable.

An overlay rendered inside a constrained page and the same content in a Dialog or Popup do not necessarily share window bounds or environment. Establish the intended density, font scale, layout direction, insets and dimming at that boundary; preserve custom values only when they are part of the actual host contract. Keep window policy in the window/host layer instead of compensating inside every child. Derive the opening path from the normal page’s host rather than a standalone overlay sample.

Native Compose, AndroidView and retaining an existing screen are all options when they meet the task. Compare the concrete missing capability and integration cost. Do not assume a long image requires View interop or assume an SDK View can safely be recreated on every state change.

For a migration, trace the relevant existing behavior through the production route before replacing it. Include hidden dependency behavior such as saved drafts, request guards, image URL handling and visibility-dependent effects when that route uses them. Do not replicate dead code solely because it is present.

### Example: update the existing View through its supported lifecycle

A reused AndroidView must reflect the current input and release its listener when its supported host ends.

| Bad | Good |
| --- | --- |
| Set changing data only in factory, then accumulate a new listener on every update. | Use factory for creation, the appropriate update path for changing data, and supported reset/release or owner cleanup for listeners/resources. |

Follow the resolved AndroidView overload and actual host lifecycle. Do not assume every version exposes the same cleanup callbacks.

## Retire superseded behavior

When requirements remove or replace behavior, trace its producers, consumers, state, effects, persistence, adapters, resources and samples. Remove task-owned remnants only after checking remaining references and applicable variants; include framework registration, reflection or dynamic resource lookup when relevant. Search absence alone is not proof of dead code. Preserve unrelated user changes and shared facilities still needed elsewhere.

For example, removing a local registration cache may also retire a stored flag, a restore branch and cancellation shielding introduced solely for that cache. Keep any part that still serves an actual requirement. Update dependent source, comments and Previews with the current behavior. Do not turn this cleanup into a repository-wide refactor.

For the same business overlay, use one presentation/window policy for initial data and interactive opening. A fixture may initialize state, but should not select a different UI host or density path. If direct render samples need a different wrapper, keep that difference in evaluator/preview scaffolding, not business-state-dependent production branches. Inspect the parent's real limits when a requirement says the overlay covers the full window. Dismissal hit regions must cover the intended outside area, not just the panel's bounds.

### Example: replace a producer without running both

A new event source replaces a legacy source for the same owner operation.

| Bad | Good |
| --- | --- |
| Keep both registered so one event can cause duplicate writes. | Connect the intended active producer and remove the superseded registration where the migration actually replaces it. |

Retain a still-required compatibility path behind its real host/feature contract; declarations alone do not prove either source is active.

## Transient overlay ownership

Keep underlying page identity and state alive across a temporary overlay unless an explicit product transition replaces it. Modal input blocking does not require hiding the underlying drawing. Avoid conditional removal or transparent base content as a substitute for a backdrop. Pause work only when the required lifecycle says to pause it.

### Example: a dialog covers a page without replacing it

**Scenario:** opening an editor must retain the page's local scroll/selection state. In these Composable-body snippets, `pageContent` and `dialogContent` are existing Composable lambdas and `onDismiss` is the required dismissal callback.

**Bad** — opening the dialog removes the page from composition:

```kotlin
if (showDialog) {
    Dialog(onDismissRequest = onDismiss) { dialogContent() }
} else {
    pageContent()
}
```

**Good** — keep the page at its stable call site and add the dialog:

```kotlin
pageContent()
if (showDialog) {
    Dialog(onDismissRequest = onDismiss) { dialogContent() }
}
```

**Why / boundary:** the page's local state/effect lifetime is not discarded just to block input. Preserve native dimming unless a concrete requirement needs a replacement. Actual navigation replacing the page is a different contract, and retaining composition does not itself define pause/cancel policy for background work.

Start with the selected control's native dimming, input and dismissal behavior. Disable or replace a default only for a concrete required mismatch; assign the replacement to one host-level owner and check for missing/double dimming. Do not globally disable window dimming as a styling habit. A custom overlay must cover the intended outside hit area and distinguish outside dismissal from inside content and explicit close actions. Apply the same state and window ownership to opening, dismissal and any supported nested transient surfaces. A content-only sample must not substitute a different production host policy.

## Scoped dependencies

Acquire business owners and environment dependencies at the integration boundary that owns their lifecycle. Make dependencies replaceable where the component contract requires it; pass the values/operations used by reusable presentation children instead of forwarding an entire page owner.

A CompositionLocal is appropriate for a genuinely shared theme/environment scope. Keep the key stable, define its provider lifetime, and make consumer expectations and fallback/replacement behavior clear. Reuse an existing scope rather than introducing one merely to hide callback relays.

**Bad:** `val LocalEnvironment get() = compositionLocalOf { fallback }` creates a different key on each access. **Good:** initialize one stable key and provide its value from the actual shared owner. A stable key alone does not establish a correct provider scope.

## Fixed APIs and supported variations

Overrides, external interfaces, generated APIs and released public signatures can constrain names, defaults, parameter order and annotations. Preserve compilation and required compatibility; Kotlin override defaults belong to their owning declaration. Explain a concrete mismatch instead of inventing a signature that the API does not allow.

Keep the selected design system and approved migration boundary. Do not migrate unrelated Material APIs or add collection dependencies solely for a preferred style. Conversely, incompatible component/theme expectations still need resolution. A deliberate shared editing holder follows its ownership and observation contract in [state](state.md#ownership-authority-and-lifetime).

For a departure from general guidance, identify the required behavior, exact affected scope, applicable project decision and reason. Reuse an established decision when it applies. Do not turn one compatibility case into a blanket exemption, or replace a clear local decision with an obligatory design ledger.

## Failure handling and retained entry points

Handle or propagate failures according to the actual operation. An intentionally ignored failure needs a concrete reason; meaningless logging is not a substitute for recovery, and cancellation must retain its intended semantics.

Remove only proven task-owned dead helpers. Framework registrations, generated callers, reflection and private Preview functions can be valid entry points without ordinary direct callers. Preserve required entry paths while retiring actual remnants.

**Bad:** swallow every exception in an empty catch and continue as though the operation succeeded. **Good:** preserve cancellation and apply the specified failure/retry/propagation behavior; intentionally ignored failures remain narrow and explicit.
