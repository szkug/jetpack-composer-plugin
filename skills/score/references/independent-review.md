# Independent review of frozen scoring evidence

Use this procedure only when an independent review is requested or otherwise authorized. Review the same frozen source and evidence under the same [scoring policy](scoring.md). Independent review concerns diagnostic applicability, scope, grouping and evidence completeness; it does not introduce manual quality grades or new implementation tasks.

## Prepare the evidence

Supply the frozen manifest, source/base identity, actual module/variant and compilation context, original reports/receipts and supporting source. Preserve failures, unlocated findings, accepted exceptions and missing coverage. Keep prior verdicts and author identity out of the review packet when feasible, without removing context needed to understand the code. Disclose prior exposure and any identifying information that remains.

## Review independently

Use a separate evaluator context only when authorized. A request for review does not itself authorize creating a user-owned chat or delegating further. Keep access within the supplied scope; do not describe prompt restrictions as a filesystem sandbox or imply that separate contexts are independent models.

Resolve findings against the actual source and the verification rule's spec basis. Retain raw diagnostics and native gates when recording a proven duplicate, exception, false positive or unresolved issue. Do not modify the candidate, collect new device/Preview evidence or change thresholds as a review action. If the supplied evidence is insufficient, record the limitation.

## Preserve and compare decisions

Save the independent decision record before sharing earlier verdicts. Use `compose-quality compare manifest.json first-review.json independent-review.json --agreement` only for the same frozen source and raw evidence. Repeating the calculator checks determinism, not reviewer independence.

Reconcile disagreements using source/evidence, retaining the initial records and reasons for any revised decision. A new evidence set is a new assessment input, not a silent replacement. Report the actual review mode, isolation limits, unresolved findings and both independent analyzer scores/gates.
