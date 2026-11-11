# Components that remain understandable when changed

Apply the [common principles](../spec.md#common-design-principles) through real callers. A component should name a coherent responsibility, useful shared policy or genuinely variable region. Keep a direct expression inline when extraction only renames it; extraction does not require another state model, interface or file.

## Establish the contract at the caller

Make responsibility, consumed inputs, events and outer size clear from the API and body. A route may own a full state holder; a reusable leaf should receive the cohesive data and operations it needs. A section model or stateful editing owner can be appropriate when its responsibility and lifetime match the section. Avoid both universal statelessness and passing the whole page owner to every child.

Preserve required inputs through final consumers, including alternate artwork and state branches. Local mock data does not justify replacing configurable content with constants. Parse external configuration at its existing input boundary rather than exposing arbitrary raw input throughout visual components.

### Example: a leaf does not need the page owner

**Scenario:** a reusable title/action region consumes only a title and one action. The existing page owner still coordinates business state.

| Bad | Good |
| --- | --- |
| Pass the entire page owner; the leaf fetches the title and reaches into it to save. | Pass the title and typed action callback; the page connects that callback to its existing save operation. |
| Introduce an interface, adapter and wrapper that only forward those same two inputs for this single caller. | Call the leaf directly; add an adapter only when it translates a real API or lifecycle boundary. |

**Why / boundary:** callers expose the leaf's actual dependencies without adding a parallel architecture. Routes may still own a ViewModel, and a cohesive editor may own its editing state. An existing adapter with compatibility work is not a redundant wrapper.

## Preserve shared design decisions

Keep decisions that must change together in one suitable existing theme, resource or component definition. Extracting components must not duplicate their shared colors, shapes or state policy. Equal values with unrelated meanings need not share a constant.

Expose parameters for real variation, not every internal style value. Introduce a style object only for a coherent variation or shared policy; a few constants do not require a token framework. Parent placement and surrounding spacing remain with the parent. Respect [project resource and integration conventions](integration.md).

### Example: one shared style, deliberate variants

Two controls share the same focus/disabled treatment but display different content.

| Bad | Good |
| --- | --- |
| Copy colors, corner policy and disabled behavior into both, then patch only one. | Use the existing shared style/component for that policy; keep content differences explicit. |

Share the decision that must evolve together. Similar colors alone do not justify a universal component with unrelated mode flags.

## Size is part of the API

The parent normally allocates outer bounds and placement; the child arranges its contents and may own an intrinsic height, aspect ratio or minimum interaction size. Fixed dimensions are appropriate for actual fixed-size contracts.

Avoid independent width arguments and Modifier chains that ambiguously control the same extent. If both are required, distinguish preferred content size from allocated bounds. Keep movement of the whole component out of its internal coordinates. Use [layout relationships](layout.md) for remaining-space allocation and overflow.

### Example: a caller owns its allocated width

The parent must allocate a reusable field the remaining row width.

| Bad | Good |
| --- | --- |
| The field overrides caller allocation with an internal screen-width calculation. | The parent applies its weight/width contract; the field arranges its text and icon within that allocation. |

A documented fixed-size control may own its size. Do not remove a required fixed contract in the name of responsiveness.

## Modifier parameter defaults

For new or changed concrete UI composables with a caller-facing Modifier, use `modifier: Modifier = Modifier`, including private/internal helpers. Put it first among optional parameters, after required inputs/actions; primary content may remain last. A caller always supplying dimensions is not a reason to omit the default.

Use the empty Modifier default. A styled default is replaced when the caller supplies a modifier, so put component-owned drawing, clipping and intrinsic sizing in the body. Apply the caller modifier once to the active root of each relevant branch, in the intended order. Preserve parent-owned allocation at the caller.

### Example: intrinsic padding survives a caller modifier

**Scenario:** `Label` always owns its content padding; callers choose outer width. `inset` comes from the project's existing dimensions.

**Bad** — the caller's modifier replaces the padded default:

```kotlin
@Composable
private fun Label(
    text: String,
    inset: Dp,
    modifier: Modifier = Modifier.padding(inset),
) {
    Text(text = text, modifier = modifier)
}
```

**Good** — compose the caller's allocation with component-owned padding:

```kotlin
@Composable
private fun Label(
    text: String,
    inset: Dp,
    modifier: Modifier = Modifier,
) {
    Text(text = text, modifier = modifier.padding(inset))
}
```

**Why / boundary:** `Label(text, inset, modifier = Modifier.fillMaxWidth())` keeps the padding only in the second version. Parent placement/outer spacing still belongs at the caller; do not move every padding into the child.

Kotlin overrides inherit defaults; preserve fixed interface/expect-actual contracts under [fixed APIs](integration.md#fixed-apis-and-supported-variations). Do not add unused Modifier parameters to non-visual/value-producing functions or confuse a Modifier extension receiver with a missing UI parameter. Check omitted and explicit-modifier callers when changing the signature.

## Parameters should expose meaning

Use coherent existing models, explicit values or typed callbacks according to the actual responsibility. Do not group unrelated fields merely to lower parameter counts. A slot fits variable content; an ordinary parameter fits a fixed child with a changing value. Keep reusable frames independent of page-specific business decisions.

Use named arguments when adjacent same-typed values, booleans or callbacks would otherwise be ambiguous, and follow the project's formatter/conventions. There is no blanket requirement to name every argument or expand every short expression. Model mutually exclusive modes explicitly where it helps; one independent Boolean does not require a hierarchy.

When a Compose call supplies two or more Boolean arguments, name each supplied Boolean argument, including nullable flags and arguments with defaults. The caller should not need to remember their order. This applies to private/internal helpers as well as public components. A single supplied flag does not require a new wrapper, and independent flags remain independent; adding defaults or a state object solely to evade this requirement is not a correction.

Use typed in-process event payloads. Preserve required string protocols at their integration boundary with parsing there. Adding selection requires an authoritative selected identity and an operation, not a competing remembered selection in each item. Local press/animation state can remain local.

### Example: disambiguate neighboring flags

**Scenario:** an existing action API takes `enabled` and `pending` in that order. These are schematic calls to that existing API, not a new component to introduce.

| Bad | Good |
| --- | --- |
| `SaveAction(true, false, onSave)` hides which flag controls which behavior. | `SaveAction(enabled = true, pending = false, onClick = onSave)` exposes the distinction. |

**Why / boundary:** names remove ambiguity for adjacent flags. This does not require naming every argument or changing a clear, conventional call such as `Text(title)`.

## Semantic defaults and complete consumers

Defaults must preserve meaningful omitted-argument behavior. A required action must reach its owner rather than disappearing behind a no-op default. When action roles differ, use an explicit role or the project's semantic action API; an enum with the same unsafe default does not solve caller ambiguity. Keep defaults for genuinely shared behavior.

Apply label, style, enabled/pending policy and callback consistently through every intended rendering branch, including custom artwork. An icon-only action needs a meaningful semantic label, adequate hit bounds and correct modifier order; decorative children should not duplicate its description. Replacing an asset must not remove those action guarantees.

### Example: optional decoration is not an optional operation

A visible confirmation control must submit the current draft.

| Bad | Good |
| --- | --- |
| Give its required handler an empty default, or accept draft text but render a fixed label instead. | Require and connect the submission callback; consume supplied data. Default only the genuinely optional decoration. |

A harmless sample callback does not establish a safe production action default.

## Read the assembled code

Use project vocabulary and the local layout/style/event organization. Keep small expressions compact when clear; expand dense branching, multiple state writes or nested scope functions when they hide execution order or ownership. Explain non-obvious reasons or compatibility constraints in comments. Do not introduce wrappers solely to shorten a function.

Separate configuration parsing, default resolution and state transitions when they are distinct responsibilities. A class coordinating several features should keep each feature's state and operations cohesive. Do not split functions into forwarding helpers merely to reduce a count, or interpret a long but cohesive declarative layout as a runtime defect.

Read the section as well as its leaves: an explicit leaf API cannot make dependencies clear if the section retrieves arbitrary fields from a whole-page owner. Provide representative [Preview samples](previews.md) by visual significance, not one per helper.

### Example: a named operation earns its indirection

A click must submit an item ID to an existing owner.

| Bad | Good |
| --- | --- |
| Route it through `invokeAction(dispatchEvent(convertPayload(id)))` where none of those layers changes ownership or policy. | Use the existing owner callback directly; keep a named adapter only for a real type, permission or lifetime boundary. |

Direct code can still use meaningful domain operations. Do not bypass an established authorization or dispatch boundary.

## Semantic change surface

For a relevant small change, distinguish necessary feature edits from incidental synchronization or unrelated behavior changes. Shared consumers should follow the same intended definition; unrelated consumers should remain unaffected. File count, changed-line count and separate component files alone do not describe coupling.

### Example: one decision has one implementation owner

A shared input gains a new validation condition.

| Bad | Good |
| --- | --- |
| Duplicate the condition in each field, confirmation button and warning label. | Compute validation at its coherent owner and let the consumers render the result. |

More call-site edits are legitimate when APIs genuinely differ; centralization is useful only for the same policy.

## Event and state relay burden

Trace a local event to its owner and state back to consumers. Keep intermediaries that consume, adapt or coordinate that contract; reconsider wrappers that only force unrelated signatures to change. No fixed depth determines whether a chain is useful.

Reconsider owner placement, slots or composition before adding another relay. Passing a whole mutable owner or universal dispatcher can hide the same problem. CompositionLocal fits a justified [shared dependency scope](integration.md#scoped-dependencies), with visible provider/consumer and lifetime boundaries; it is not a shortcut for every callback chain.

### Example: preserve meaning through necessary relays

A leaf selects an entity by stable ID.

| Bad | Good |
| --- | --- |
| Turn the ID into Any, route through unused intermediate handlers, then cast it back. | Preserve the typed ID through required layout boundaries; remove relays that have no responsibility. |

Do not create a global owner/CompositionLocal just to shorten an already clear callback path.

## Naming and callable shape

Use entity-style uppercase names for Unit-returning UI Composables, and lowercase function-style names for value producers. Use `Local…` for CompositionLocal keys, present-tense event names such as `onClick`, and a `Composable` suffix for a custom `@ComposableTargetMarker` annotation. Preserve fixed external signatures and current project vocabulary.

Place required inputs/actions before optional parameters, with caller Modifier first among optional parameters and the primary composable content slot last. Make reusable component defaults accessible at the same supported API boundary as the component when callers need them. Do not expose unrelated internals merely to increase visibility.

| Situation | Bad | Good |
| --- | --- | --- |
| Unit UI emitter | `profileTitle` | `ProfileTitle` |
| Value-producing helper | `CurrentSpacing` | `currentSpacing` |
| Required action plus content | Hide `onClicked` as the trailing lambda after optional arguments | Put required `onClick` before optional Modifier; reserve the trailing slot for content |

Use named arguments where needed for clarity; a fixed platform/API signature takes precedence over restyling.

## Content and modifier composition

A reusable visual component has a coherent root and preserves the caller modifier at the active root in each relevant branch. Scope-specific content helpers may intentionally emit siblings. Separate UI emission from computed return values; a value-producing Composable need not emit UI.

Invoke each content slot at most once per execution path and preserve its intended identity across layout changes. Mutually exclusive branches need deliberate identity/lifetime handling; a stable single call site is often simpler. Use retained movable content only when actual movement requires it, with correct captures and lifetime.

A modifier factory preserves its receiver once. Reusing an independent immutable style chain is valid; applying the caller’s allocation to multiple descendants changes the component contract. Use an ordinary extension for pure chaining; choose a Node implementation when custom lifecycle/state behavior warrants it. Preserve required compatibility when replacing an existing composed modifier.

| Situation | Bad | Good |
| --- | --- | --- |
| Pure modifier extension | Return a new `Modifier` chain and discard `this` | Extend the incoming receiver once |
| One slot represents one child | Invoke `content()` twice on the same path | Invoke it once, or expose two genuinely distinct slots |
| Surface must clip its click indication | Add clipping after the clickable surface without considering its drawing bounds | Order clipping/click behavior to match the actual interaction and drawing contract |

Do not add empty wrappers or reorder all modifiers mechanically; measurement, interaction and drawing order have real effects.

## Input identity and defaults

Caller-owned entity/session IDs and externally meaningful clock values must have an explicit owner and lifetime. A random or current-time expression evaluated as a UI parameter default can silently introduce a new identity when callers omit it. Obtain such values at the owner that controls their intended creation/reset.

**Bad:** a presentation component defaults its entity ID to a new random UUID on each invocation. **Good:** the entity owner creates the ID once at the required lifetime and passes it to the component. A deferred callback that intentionally requests fresh randomness is a different operation.
