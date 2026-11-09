# Scoring policy and assessment procedure

There are two independent scores: Lint and detekt. Category labels help locate diagnostics; they have no grades, budgets or denominator. No combined total, weighted aggregate or mean is defined. Implementation requirements come from spec; verification defines their supported static predicates.

## Deduction policy

| Score | Authoritative policy | Calculation |
| --- | --- | --- |
| Lint | [lint-policy.json](lint-policy.json): severity deductions and diagnostic grouping | max(0, 100 - distinct defect deductions) |
| detekt | [catalog.json](catalog.json): each rule’s impact, deduction, ownership priority and rationale | max(0, 100 - distinct defect deductions) |

These JSON files are the authoritative numeric definitions. Do not maintain another handwritten rule/point table or tune weights after seeing a candidate’s result. The declared weights are policy choices, not empirical quality probabilities.

Within each tool, one proven defect is charged once at the highest applicable deduction. Analyzer-proven identical discarded leaf parameters group automatically; other equivalence, scope and false-positive decisions need source evidence. Cross-tool counterparts stay visible in both independent records and are never summed or averaged. Raw analyzer severity and gate outcomes remain visible even when detekt’s scoring impact classification differs.

## Counting units

A diagnostic occurrence and a scoring unit are separate. Preserve every source location and show both occurrence count and charged-unit count. Start at 100 and subtract the declared distinct-unit deductions; this is not `100 × correctness rate` and selected rule count is not an opportunity denominator.

For `PositionalBooleanArguments`, the unit is one resolved source callable contract in the assessed scope. Repeated unnamed-flag calls to that same declaration cost 5 once; every affected caller still needs correction. Different declarations/overloads/receiver types cost separately. The analyzer's `composer-boolean-contract` identity is required for automatic grouping; never group by simple name, file, or rule alone. Without a proven identity, preserve per-diagnostic charges and disclose that limit. Apply changed-line filtering before grouping.

This style-policy grouping does not assert a common runtime cause or a single-edit fix. It does not apply to independent state, lifecycle, dropped-data or other correctness failures. Other rules retain their documented owner/defect units. No global per-rule cap is introduced. A frozen policy must say which unit it uses before comparing candidates; changing the unit requires a new assessment, preserving earlier results.

## Freeze scope and evidence

Before a prospective comparison, freeze source/base, module/variant, actual compilation context, rule/configuration/artifact hashes, selected execution coverage and evidence policy. Declare retrospective exposure otherwise. Reuse verified unchanged evidence when appropriate, explicitly labeling reuse; do not describe reused reports as new scans or repair frozen candidates.

Verification owns the [coverage catalog](../../verify/references/coverage.json), [acceptance boundaries](../../verify/references/acceptance-boundaries.json), [diagnostic evidence](../../verify/references/evidence.md) and [compilation receipts](../../verify/references/cli.md). Consume their frozen data and actual execution records. Score does not redefine checks, add manual requirements or turn unknown coverage into a passed check.

Missing, suppressed or unverified selected checks, source drift, analysis failures and unresolved diagnostics withhold the affected tool score. An available other-tool result can remain visible as an explicitly incomplete assessment. Preserve original findings, receipts, exception evidence and duplicate identities.

## Gates and publication

Gate status and evidence completeness are separate from the numeric scores. The current gate policy treats Lint errors or high-impact detekt findings as failed, major findings as changes required, and moderate/minor findings as requiring review. A complete numeric report is not a passed delivery.

Business/runtime acceptance is separately scoped and unscored. Do not infer it from a clean static report or add a numeric visual score. Preview declarations do not authorize rendering/device work. Mark unperformed external checks as not assessed and retain known limits alongside both tool results.

## Commands and current examples

```sh
compose-quality score manifest.json evidence.json
compose-quality compare manifest.json A.json B.json C.json
compose-quality compare manifest.json reviewer-a.json reviewer-b.json --agreement
```

`--diagnostic` permits explicitly incomplete results; it does not make them publishable final scores. `--agreement` requires identical frozen source and raw evidence. Repeat calculation demonstrates determinism, not an independent review; use the [independent review procedure](independent-review.md) only when authorized. No `--mean`, manually supplied grades or category budgets are accepted.

The [manifest](example-manifest.json) and [evidence](example-decisions.json) examples are synthetic format/calibration inputs, not project acceptance results. File names identify roles; schema/policy versions and hashes inside the data identify the frozen protocol. The distributed calculator accepts only its current schema. Historical reproduction uses an external frozen archive.
