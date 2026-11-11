# Performance decisions with bounded complexity

Start from the real workload: input size, update frequency, visible content, resource lifetime and target devices. Identify the reachable operation and its owner. Fix evident unnecessary work without waiting for a benchmark, but distinguish that source correction from a measured speedup. Preserve correctness and understandable component contracts; optimization is not a reason to duplicate authoritative state.

## Choose work placement

Keep blocking IO, decoding and substantial data processing out of composition, layout and drawing callbacks. Use the existing repository/loader/worker boundary with suitable dispatching; a coroutine alone does not establish background execution. Keep small pure display expressions local. Moving every expression into a ViewModel adds coupling without necessarily reducing cost.

For repeated expensive transformations, choose an owner whose inputs and lifetime match the result. A local remembered result may suffice; shared business processing may belong upstream. Specify invalidation and retention before introducing another cache. Include relevant inputs and avoid in-place mutations that silently invalidate the assumption behind cached results. Consider key comparison and retained memory as costs too.

### Example: a coroutine is not proof of background work

A user action needs blocking decoding before its UI result is published.

| Bad | Good |
| --- | --- |
| Decode in composition or start a coroutine on the UI dispatcher and call the same blocking decoder. | Use the existing loader/worker boundary with suitable dispatching and cancellation, then publish the result through its owner. |

For cheap formatting, a direct pure expression can be clearer than extra jobs/caches. This source improvement is not a measured speedup.

## Observation and rendering

Trace which UI consumes frequently changing values. Narrow observation where it prevents unrelated work. For a value used only in placement or drawing, consider reading it in that phase instead of rebuilding composition, without changing the intended layout behavior. Use derived-state facilities only when their semantics and cost fit the update pattern; verify the project's Compose/compiler version before selecting APIs. Do not mechanically wrap cheap expressions in remember or add stability annotations to hide mutable contracts. These decisions follow the [Compose best practices](https://developer.android.com/develop/ui/compose/performance/bestpractices).

Do not move state ownership merely to lower a recomposition counter. A second local copy can lose synchronization; unnecessary indirection can make components harder to change. Inspect the work performed and then measure the implicated interaction when claiming improvement.

### Example: read placement-only scroll state in placement

Only a decorative element’s placement depends on a frequently changing scroll offset.

| Bad | Good |
| --- | --- |
| Read the offset into a top-level composable value used to rebuild unrelated content on every scroll. | When the real layout permits it, read inside the supported placement lambda, e.g. `Modifier.offset { IntOffset(0, -scrollState.value) }`. |

The lambda uses pixels and changes observation timing. Do not substitute it when composition/content or measurement genuinely depends on the value.

## Lists, layout and assets

Use bounded viewports and lazy composition when content scale warrants them; small fixed groups can remain ordinary rows or columns. Preserve entity identity across inserts/reorders, and distinguish item identity from content reuse categories. Inspect actual constraints before blaming a container for performance.

Prefer direct layout relationships. Add custom measurement, intrinsic queries or subcomposition only for a concrete requirement and examine their cost on the relevant path; their names alone do not prove a defect. Avoid measurement-to-state feedback that repeatedly invalidates the same layout.

Reuse the project's image pipeline after inspecting its sizing, transformations, cancellation and caching behavior. Choose image resolution for the displayed area and intended zoom, not automatically the original asset size. Do not create a second bitmap cache without a clear ownership, eviction and invalidation policy. Inspect repeated decoding and resource retention when they are implicated; do not claim a leak merely because an object survives one frame.

### Example: entity identity survives reordering

A lazy collection can reorder while rows hold entity-local UI state.

| Bad | Good |
| --- | --- |
| Use positions, constant keys or hashCode as entity identity. | Use a stable unique entity key and an appropriate content type only where reuse categories differ. |

Small fixed groups need not become lazy lists. Keys are not a substitute for required state restoration; use the project image pipeline and measured asset size inside rows.

## Effects and lifetime

Follow [state ownership and effects](state.md). Requests and subscriptions must not start as incidental rendering work. Keys should represent when work must restart; use appropriate cleanup when the owner ends. Keep business work alive only for its required lifetime. Entering or changing keys restarts a LaunchedEffect, and leaving composition cancels it, as described in the [effect documentation](https://developer.android.com/develop/ui/compose/side-effects). Do not replace a correct lifetime with a constant key merely to suppress repeated work.

Neither a read-only List parameter nor the absence of an optimization annotation independently proves a performance defect. Select representations and optimizations according to actual observation, workload and the resolved compiler/runtime behavior.

### Example: dispose an owned subscription

A composition-owned listener observes the currently selected source.

| Bad | Good |
| --- | --- |
| Register during every composition, or keep a constant key while the source changes. | Use the appropriate keyed lifecycle effect and remove that exact listener when its owner/source ends. |

A longer-lived business subscription belongs to its longer-lived owner. Do not cancel required background work just because a transient view disappears.

## Annotation promises and representations

Use `@Composable` when the function or its required API needs composition capability, including relevant default expressions. Use `@ReadOnlyComposable` only when its actual operations and callees honor that promise. Consider `@NonRestartableComposable` only for an appropriate delegation pattern; its absence alone is not evidence of poor performance.

Strong skipping changes the cost significance of inferred stability; it does not observe arbitrary mutable internals. Do not claim `@Stable` or `@Immutable` for data that breaks those contracts. A read-only collection interface does not guarantee immutable contents. Use the existing suitable representation; primitive state APIs can avoid boxing when supported and useful.

**Bad:** annotate a mutable model as immutable to conceal its update behavior. **Good:** preserve truthful annotations and observable publication, changing representation only when the actual contract/workload warrants it.
