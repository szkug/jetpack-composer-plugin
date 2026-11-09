# Finish implementation with verified corrections

This is the default continuation of an implementation task. Follow explicit user scope restrictions first; do not apply it to frozen or review-only code.

## Establish inputs once

Use the task's Git base, actual module/variant and trustworthy compilation-context metadata. Look for existing documented context before asking for missing information. Read the verify CLI guide and use native Lint/detekt with the bundled profile; do not add Gradle lint plugins, create a substitute project or guess dependencies. An authorized project compilation is a separate action, not a hidden analyzer step. Missing or stale metadata blocks a verified delivery until resolved.

Keep the base, selected rules and thresholds fixed during correction. Run evidence must live outside the Git worktree in distinct directories. Record source/configuration/artifact identities and retain failed runs rather than overwriting them.

## Read diagnostics, repair the implementation

Run both analyzers through verify and inspect matched, excluded, unlocated and execution-error results. Exit zero only means no configured gate blockers; it does not mean no actionable warnings. Confirm applicability against spec and project constraints. Fix in-scope Error/Fatal and actionable Warning findings, including warnings that would deduct points; optional Hint/Information suggestions need not trigger cosmetic edits.

Correct the cause at declarations, callers, state/effect owners or real data consumers. A grouped style charge still requires correction at every affected call. Preserve behavior and required APIs. Do not disable rules, raise thresholds, add blanket suppressions/baselines, remove functionality, add meaningless defaults or split into empty forwarding helpers to obtain a pass. An actual fixed-contract exception needs narrow evidence and authority under verify; unresolved cases remain explicit.

For analyzer execution errors, correct supported tooling/input problems and rerun; do not alter business code to hide a failed scan. Leave unchanged historical findings outside the task, while reporting them separately. Do not enable analyzer autoCorrect: source repairs are deliberate impl edits informed by diagnostics.

## Reverify and finish

After a repair, inspect its callers and rerun the affected tools against the new source. Finish with valid results from both tools for the final source/context; reuse a result only when verify proves its relevant inputs unchanged. If compilation is required, confirm the final source builds as well. A loop is complete when there are no unresolved in-scope actionable findings and no execution/coverage gaps; an evidenced accepted exception must be visible.

If a blocker requires missing user information, or the same diagnosis persists across two attempted corrections without progress, stop that loop and report the concrete blocker and attempted corrections. Do not cycle indefinitely, declare success or weaken policy. Continue independent work that is still possible. Default completion does not include numeric scoring, device acceptance or Preview rendering.
