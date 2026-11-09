---
name: impl
description: Implement, refactor or migrate Jetpack Compose UI using shared design contracts, with source review, native Lint/detekt verification and automatic in-scope correction/reverification by default.
---

# Compose implementation

## Understand the requested change

Identify required behavior, supported inputs, references, allowed mocks and the production entry. Read [spec](../spec/SKILL.md) and only the relevant standards. Apply the [common design principles](../spec/SKILL.md#common-design-principles), using comparable active-module code under [project conventions](../spec/references/integration.md#follow-the-active-project-conventions). Resolve actual component/resource APIs and state/host ownership before choosing abstractions. Scale planning to the task; routine edits do not need a design ledger.

## Implement the production path

Use the [implementation loop](references/realization.md) for new screens or material UI changes. Connect actual inputs and state to final component arguments, rendering and event consumers. A declared callback, style or resource is not complete until the intended production caller uses it.

Apply the relevant shared contracts:

- [Components and Modifier defaults](../spec/references/components.md): keep responsibility, outer size, shared styles and events understandable at the caller, including private/internal helper APIs.
- [Layout](../spec/references/layout.md) and [state](../spec/references/state.md): express real space relationships, preserve initial/restored/event invariants and give asynchronous work its intended owner and lifetime.
- [Integration](../spec/references/integration.md) and [images](../spec/references/images.md): reuse inspected project capabilities, implement real loader parameters and preserve host/overlay policy. Explain a concrete mismatch before replacing a project facility.
- [Preview samples](../spec/references/previews.md): provide/update representative production-calling sample code when supported and in scope.
- [Performance](../spec/references/performance.md): for relevant workloads, place work and observation appropriately without speculative caches or architecture changes.

When replacing/removing behavior, trace task-owned state, effects, resources and samples under the integration retirement guidance. Preserve unrelated changes and shared facilities still in use.

## Review and correct the source

Reopen the assembled source and trace changed inputs, callbacks, state transitions and final consumers. Check omitted and explicit Modifier calls, conditional branches, shared style consumers and removal paths where relevant. Walk one plausible local change when it helps expose incidental coupling; do not implement extra features for that walkthrough.

Apply the relevant source guidance at the actual declaration and call: required parameters precede the optional Modifier; neighboring flag arguments expose their names; effects match suspension, repetition and cleanup needs; parsers and state owners have coherent responsibilities. Read linked topics in manageable sections so truncated tool output does not silently omit a requirement. Reading a document is not evidence that the implementation satisfies it.

Read changed code from a maintainer’s perspective: do its names and arguments explain the operation, can the state/event path be followed, and does each added layer serve the task? Compare meaningful departures with the selected project precedent. Simplify concrete sources of confusion without cosmetic rewrites or deleting required behavior.

Repair confirmed in-scope implementation omissions and review the affected callers again. Keep permitted mocks and unresolved product decisions explicit. For review-only or frozen evaluation, preserve the candidate and follow the requested review scope. For an implementation task, in-scope correction is part of implementation; use [verify](../verify/SKILL.md) for each static scan. A standalone review or frozen evaluation remains read-only.

## Verify, correct and verify again by default

Implementation normally includes the [verification and correction loop](references/verification-loop.md). After source review, use [verify](../verify/SKILL.md) to run both native Lint and detekt on the current added/modified code with the actual compilation context. Repair confirmed in-scope findings and rerun the affected checks until final evidence covers the final source. Do not stop at compilation or a successful analyzer process exit while actionable findings remain.

This default is part of an implementation request; it does not need a second permission question. An explicit user restriction such as source-only work, read-only review or a frozen candidate takes precedence. Missing analysis inputs or unresolved applicability must be reported as incomplete, not silently skipped or replaced with guessed inputs.

The loop does not authorize device access, Preview rendering, changes to project checks or unrelated repairs. Perform project-required compilation and separately requested runtime acceptance under the task's own workflow. Numeric scoring belongs to [score](../score/SKILL.md) when requested, not to this implementation loop.

Deliver the implemented scope, final compile/scan status, evidence paths, correction summary and any unresolved constraints. Source review is not execution evidence. Keep failed/intermediate scan evidence distinguishable from the final passing or incomplete result.
