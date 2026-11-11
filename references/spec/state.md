# State and interaction as one design

Start with the meaning of each value, not its Kotlin type or storage API. Identify business facts, uncommitted drafts, transient interaction state, runtime objects and derived display values. Decide which values must change consistently and which vary independently.

## Model facts before containers

Group fields when they form a meaningful snapshot or participate in coordinated updates. Use mutually exclusive alternatives when combinations are actually invalid. Independent dimensions should remain independently expressible. Existing domain models may already provide the needed contract; introduce a display projection only when it simplifies interpretation, combines sources or removes an unsuitable dependency.

Avoid independently writing a value that can be derived from authoritative inputs. A derived value still needs an explicit precedence rule when those inputs interact. A single large data class does not automatically provide consistency, and several state holders are not automatically inconsistent.

### Example: a derived count is not another state owner

**Scenario:** the caller supplies a new immutable `selectedIds` set when selection changes. The display is always its current count; no editing draft or delayed count is required. Snippets are inside the same Composable body.

**Bad** — the remembered initial count becomes stale:

```kotlin
var count by remember { mutableIntStateOf(selectedIds.size) }
Text(count.toString())
```

**Good** — derive the cheap display value from the current input:

```kotlin
val count = selectedIds.size
Text(count.toString())
```

**Why / boundary:** there is one selection authority and no extra write to synchronize. An independently editable draft needs its own state. This example does not make in-place edits to a non-observable collection observable, or require expensive computations to run uncached.

### Example: SDK state survives a view reload

**Scenario:** an embedded SDK session stays active while its native view reloads. Business phase and view loading describe independent facts.

| Bad | Good |
| --- | --- |
| Replace the authoritative business phase with `Loading` when the view reloads, losing whether the session was active. | Retain the accepted SDK phase and separate view-loading state; derive the visible content/overlay from both. |

**Why / boundary:** independent states can coexist without inventing contradictory writable flags. A new session may require a reset; a same-session reload may preserve state. Follow actual session identity and ordering guarantees, not a locally fabricated callback timestamp.

### Example: preserve positional identity

**Scenario:** positions 1 and 3 are occupied; position 2 must remain visibly empty. Position is an authoritative slot identity, not merely list order.

| Bad | Good |
| --- | --- |
| Sort occupants and use their list indices as positions, moving the third occupant into the second slot. | Render the declared slots and resolve each occupant by its authoritative position, retaining empty slots. |

**Why / boundary:** sorting does not represent holes. For a product that requires only an ordered participant list, compaction is valid; do not introduce fixed slots without that requirement.

## Ownership, authority and lifetime

Locate readers, writers and coordination needs. Choose an owner whose lifetime matches the requirement: a local composition, common parent, ordinary holder or existing business ViewModel/Plugin. “UI state” alone does not determine its location. Check entity switches, view recreation and external updates when relevant; persistence beyond those events must be intentional.

State ownership and permission to mutate it are related but separate. Define who creates, retains and resets a value, and what another component is allowed to do to it.

Keep business transitions at their responsible owner. A layout's click handler can invoke `leaveItem()` or adapt an event, rather than editing several business fields itself. A page-local help toggle can remain a direct local update. Read-only inputs and restricted setters are useful when they make this distinction enforceable; replacing every write with a universal dispatcher is not required.

| Conditions | A reasonable contract | Consequence to check |
|---|---|---|
| Owner must coordinate each edit with validation or related changes | Value/read-only state and operation callback | Callback must reach the authoritative update, not silently create a second copy |
| Parent and child intentionally co-edit a simple local draft | Shared MutableState or a local holder with explicit write authority | Shared writes are part of the contract; callers know who may write, how changes are observed and when the draft resets |
| Editing includes selection and composition behavior | A suitable editing state holder | Its lifetime and editing protocol fit the surrounding UI |
| Component edits privately and caller only needs a committed result | Local draft with submit/cancel | External refresh, cancel, failed submit and entity switch have defined meanings |

Passing State rather than a value can be useful when read placement matters. Choose it for an actual observation requirement, not as a universal signature. A callback restricts direct writes but does not by itself prove useful decoupling.

For a draft, distinguish the value at edit start, the current draft and the latest business value. Re-copying external data on every update can overwrite typing. Keeping a remembered draft forever can submit an edit for the wrong entity. Derive reset or conflict handling from the editing session's identity and requirements.

### Example: save the submitted edit, not the next edit

**Scenario:** an editor can switch entities or accept more typing while a save is pending. Only the matching editing session/request may update the visible save result.

| Bad | Good |
| --- | --- |
| Start a save, then read the current selected entity/draft again after suspension and mark that value as saved. | At submission capture entity identity, editing-session/request identity and draft value. Send that snapshot; apply completion to the visible editor only if the same session/request is still current. |
| Clear pending with a UI timer based on expected latency. | Let the matching request's actual completion/failure own pending state; put simulated delay inside an allowed mock operation. |

**Why / boundary:** a late response cannot mark a different edit as saved or clear a newer request's pending state. Use the existing owner's cancellation/error handling. Capturing a snapshot does not solve server ordering; preserve the project's conflict policy. If the product prevents switching/editing during save, do not introduce unsupported concurrency machinery.

Retain composition-owned state under its intended identity. Publish observable updates instead of mutating an unobserved collection in place. Read reactive streams through the project’s supported observation boundary; a one-time snapshot is appropriate only when the operation actually needs a snapshot.

## Connect events to outcomes

Trace a meaningful action from input to its resulting state or effect. Let local controls handle local interactions; let the appropriate business owner validate permissions and current conditions when an operation executes. A page may adapt specific callbacks to an existing dispatch API. Neither a universal Action type nor many callbacks is an end in itself.

Use stable entity identity when asynchronous results can outlive selection changes. Distinguish request pending state from the authoritative business result. Decide how duplicate input, cancellation, failure and late completion affect the current operation when these are reachable. Guarding against a repeated effect should not prevent a necessary state refresh.

Let the request lifecycle own its pending state. A presentation timer that independently clears the same flag introduces another writer and couples behavior to expected latency. If a mock needs a timed completion, put that timing in the mock operation and drive the UI through its ordinary completion path.

Choose effect ownership and keys from the work's identity and lifetime. Work launched by entering a composition must have appropriate cancellation and cleanup. An ordinary click need not travel through a Flow and collector unless that indirection serves an existing contract. Avoid introducing navigation, requests or subscriptions as incidental consequences of rendering.

Decide whether removing a control should cancel its work before choosing its coroutine scope. A request that should survive closing a transient editor belongs to a longer-lived owner; work that should be abandoned can belong to that editor. Do not let the location of `rememberCoroutineScope` accidentally decide the product behavior. When moving the control or replacing a popup with a window, revisit this lifetime rather than changing only its layout.

### Choose the effect for the work

Use LaunchedEffect when the work needs suspension, the effect's CoroutineScope/context, or cancellation/restart tied to its keys. A helper that launches into an already-owned external scope does not by itself need a second coroutine around the helper call.

For synchronous work after a successful composition, use SideEffect with the required repetition semantics. When the resolved Compose runtime supports keyed SideEffect, synchronous work that runs on entry/key changes can use that keyed API. An unkeyed SideEffect runs after every successful composition and is not an equivalent replacement for once-per-key work. On older runtimes, preserve the intended behavior instead of calling an unavailable API.

| Situation | Bad | Good |
| --- | --- | --- |
| Publish a synchronous owner update once per changed key | Add a coroutine solely to call the non-suspending update | Use the runtime-supported keyed synchronous effect with those keys |
| Collect a stream or wait before updating | Remove LaunchedEffect merely because its outer helper looks simple | Retain the coroutine, keys and cancellation boundary required by the actual work |
| Register a listener that must be removed | Treat registration as a one-way synchronous update | Use a lifecycle owner or DisposableEffect with the matching cleanup |

Inspect helper ownership and timing before replacing an effect. An optimization finding alone is not proof of a leak, repeated request or observed performance regression.

### Example: a callback reference is not a completed action

A Save button must commit the edited value.

| Bad | Good |
| --- | --- |
| Write `val ignored = onSave` or forward it to a helper that drops it. | Invoke the real save operation with the submitted value from the reachable click handler. |

Referencing a callback is not the same as invoking the required operation; its input and resulting state must remain connected.

## Keep value semantics consistent

Choose equality and normalization for domain values at the input boundary. Numerically equivalent values can have different representations (decimal scale, unit, case or identifier formatting); a candidate lookup must use the same semantics as the current selection. Do not normalize only one side of a comparison. Walk one concrete forward/backward selection and wraparound example through the actual code. Disabled controls guard repeated input, but do not prove the underlying state transition is correct.

### Example: use one meaning of empty input

A task treats whitespace-only names as invalid and saves trimmed names.

| Bad | Good |
| --- | --- |
| Validate the raw string in one branch, save a differently trimmed form in another, and display a third fallback. | Use the same declared normalization/value policy through validation, submission and result display. |

Preserve meaningful whitespace when the domain requires it; trimming is a scenario requirement, not a universal rule.

## Trace a complete operation

Keep business writes behind operations that preserve the model's invariants; UI assembly should invoke those operations rather than updating related facts separately. Derive values when they have no independent authority. For an asynchronous edit, capture the submitted value and the target identity; if an external update or target switch is reachable, decide which result may still be accepted. Handle an input absent from the allowed candidates explicitly rather than obtaining an accidental behavior from a failed index lookup. Do not invent elaborate concurrency machinery for operations the product does not have.

### Example: an absent candidate needs defined behavior

A selection is restored after its candidate was removed.

| Bad | Good |
| --- | --- |
| Use the missing index as an accidental fallback or silently select a different entity. | Apply the required invalid-selection policy explicitly before saving or rendering a selected result. |

Reuse the actual owner operation. Do not add concurrency or generic state-machine machinery for a synchronous selection.

## Reachable transitions and removal

Trace each required dynamic transition from an actual event source through its owner to the rendered state. When external transport is mocked, supply an appropriate mock producer through the ordinary owner; an unused update method is only an integration hook. Distinguish a fixture's resolved display state from the rule that derives it from live inputs. Implement the derivation when the task includes it.

All ways of ending a presentation—its action, Back, outside click, timer and external update—must apply their intended business transition. Share the semantic operation where the outcome should match; do not equate clearing overlay visibility with finishing the underlying operation. Keep a covered page composed when its local scroll/effect/SDK lifetime must survive an overlay. Effect keys identify inputs whose changes should cancel and restart the work. When a callback or value must stay current while the operation continues, use `rememberUpdatedState` or an appropriate observable input instead of restarting it. See the [official effect lifetime example](https://developer.android.com/develop/ui/compose/side-effects#rememberupdatedstate).

### Example: restart work only when its identity changes

A delayed UI operation belongs to an entity; its completion callback can change while waiting.

| Bad | Good |
| --- | --- |
| Use a constant effect key across entity switches, or key on every callback replacement and keep restarting the delay. | Key work on the entity/session identity; when it must continue, obtain the latest callback with the supported current-value pattern. |

If callback replacement is intended to restart the operation, include it in the keys instead. An effect is not a substitute for an event-owned request.

## Apply invariants at every entry

Initial input, restored state and subsequent events must obey the same applicable state constraints. Identify what empty, missing or invalid data means before entering a phase, and what its timer/completion will do next. For example, guarding an empty result on a later update does not protect an initially empty highlight phase that advances into that result. Reuse a focused validation/transition operation when it prevents divergent paths; do not introduce a generic state machine just for symmetry. Derive fallback, skip or empty-state behavior from requirements, and keep unresolved product choices explicit.

### Example: restoration uses the same valid phases

An empty candidate set cannot enter the active-selection phase.

| Bad | Good |
| --- | --- |
| Guard only the later update event but restore directly into active selection with no candidates. | Apply the same allowed transition/fallback to initialization, restoration and later updates. |

The fallback comes from the task. The rule does not require a new generic transition framework.

## State extension and impact boundaries

When extending state, identify new authoritative facts separately from derived values, duplicated storage and synchronization rules. Assess whether the structure groups responsibility/lifetime coherently and expresses relevant mutually exclusive alternatives without accidental invalid combinations. More fields or holders are not inherently worse; additional independent writers, mirrored facts and bidirectional synchronization need a concrete purpose.

Trace a changed value to consumers, derived values, effects and reset/removal/entity-switch paths. Compare intended effects with unintended changes in unrelated regions. A feature-wide theme legitimately has broad consumers; local selection should not silently alter unrelated business state. Trace event parameter or semantic changes through producers, relays and handlers in the same way. Recomposition scope is useful evidence of observation placement, but a performance impact needs separate measurement. Use the [relay guidance](components.md#event-and-state-relay-burden) for intermediate state/operation forwarding.

### Example: do not mirror an authoritative selection

A new badge needs to display the selected count.

| Bad | Good |
| --- | --- |
| Add a second mutable count plus synchronization from select, deselect, clear and restore handlers. | Derive it from the authoritative selection, as in the [count pair](state.md#example-a-derived-count-is-not-another-state-owner). |

A separately authoritative server count is a different fact and may legitimately need its own lifetime.

## Retained values and render-time writes

Composition describes output from current inputs. Perform transitions in the appropriate event/effect owner rather than writing existing observable state while assembling UI. Initializing newly created, privately owned state is different from mutating a caller-owned state object hidden inside a new wrapper.

Remembered computations must follow the inputs that can change their result. Keep cheap derived expressions direct; when retention is useful, use the actual invalidation keys. Initial-only drafts intentionally capture a start value and reset by editing-session identity rather than every keystroke or external refresh.

| Situation | Bad | Good |
| --- | --- | --- |
| Changing display input | `remember { title.uppercase() }` freezes the first title | Derive directly, or retain under the relevant input keys when justified |
| Existing visible state | Assign `expanded.value = true` while composing | Apply the transition at its intended event/effect owner |
| Long-running work needs a current callback | Cache the value read from `rememberUpdatedState` inside an unkeyed remember | Read the current callback when invoking it, preserving the required work lifetime |

A retained value is not automatically observable. Match snapshot publication, collection updates and read placement to the actual consumer.
