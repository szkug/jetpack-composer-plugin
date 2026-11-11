# Analyzer execution evidence

Use this document to validate Lint/detekt outputs. It defines evidence for actual static scans, not a separate design or runtime review workflow.

## Inputs and identity

Preserve the source snapshot and Git base/diff, actual module/variant, declared source roots, full dependency/classpath provenance, compiler settings, Android SDK inputs, effective configuration and selected rule IDs. Freeze analyzer, plugin JAR, custom-source and configuration hashes. The [native CLI guide](cli.md) defines input requirements; hashes prove identity, not that undeclared dependencies are absent.

Read effective rule options, severity overrides, lint configuration, baselines and suppressions when interpreting coverage. Disabled, unavailable, suppressed, baseline-filtered and outside-diff checks are not equivalent to executed clean checks. Missing type-analysis inputs or a failed rule/configuration load cannot become a pass.

## Execution and reports

Keep the actual command, exit status, logs, receipt, raw XML/SARIF and filtered result. Confirm files belong to this execution and input snapshot; retain failures rather than replacing them with an empty successful report. Verify enabled-rule coverage against the frozen profile; SARIF registration alone does not prove execution.

Distinguish analyzer execution failure, raw gate outcome and the changed-line gate. A complete scan may legitimately report code violations and fail its gate. A filtered pass says nothing about excluded unchanged code. Keep unlocated diagnostics visible and resolve their scope before publishing a complete score.

## Diagnostic interpretation and exceptions

For a reported finding, retain its actual rule ID, severity, source location/range, message and analyzer attribution. Follow the resolved declaration/call only as needed to confirm applicability or a suspected false positive. Do not infer a runtime crash or frame-time loss from a convention or bounded static predicate.

Use [E1–E4](lint-rules.md#conflicts-and-exceptions) for justified conflicts. An exception needs exact scope, the required behavior/fixed API, source evidence, project authority and its reason. A local preference or suppression annotation alone is not authority. Preserve original diagnostics and gate results beside any adjudication.

Record proven duplicate identities without hiding raw findings. Similar names or the same line do not establish equivalence. Deduction policy, per-tool grouping and cross-tool presentation belong to [score](../score.md); do not introduce a manual readability/layout grade.

## Scoring handoff and limits

Supply both analyzer packets under the [scoring policy](../score/scoring.md), including their full/diff-filtered reports and execution receipts. Source drift, unsupported context, incomplete selected coverage or unresolved diagnostics withhold the affected score. An available other-tool result can remain visible with the assessment marked incomplete.

The [boundary ledger](acceptance-boundaries.json) records static limits and requirements outside the numeric profile. Its entries do not schedule a manual checklist. Business/runtime checks occur only under a separately required task scope; neither their absence nor a quiet static report establishes a business pass.

Keep evaluated source and original checks unchanged. After an authorized repair, preserve the prior packet and collect fresh evidence for the affected scope. Historical receipts retain their original context and are not relabeled as fresh CLI execution.

## Coverage and boundary definitions

[coverage.json](coverage.json) records the selected atomic detector contracts and rule links. [acceptance-boundaries.json](acceptance-boundaries.json) records broader semantic requirements, retired workflows and known static limits. Their roles differ: completing a selected predicate does not complete every broader requirement it supports. Keep these definitions under verify and pass their identities to score.

The [maintained Compose registry](compose-rules-registry.json) records exact rule identities, activation, severity and potential overlaps. It is verification metadata, not another implementation standard or deduction table. Requirement guidance remains in spec; numeric deductions remain in score.

Use these machine-readable definitions as the single maintained coverage/boundary inventory. Do not duplicate them into a separate manually maintained requirement matrix. When selecting or extending a predicate, link its spec basis in the appropriate verification rule document and disclose unsupported cases.
