# Two-tool static scoring

Use the [scoring policy](score/scoring.md). Lint and detekt independently start at 100: `max(0, 100 - sum(distinct failing rule deductions))`. Suggestion=1, warning=2, error=3. Repeated findings of one rule deduct once; separate rules deduct independently. There is no cross-tool total or mean.

Implementation verification and scoring share [rule-policy.json](verify/rule-policy.json), the complete Lint registry and the exact enabled detekt catalog/YAML. Project activation/severity overrides are forbidden. Warning/error findings must be repaired during implementation; suggestions require a contextual fix/retain decision, with retained reasons recorded and one-point deductions preserved.

Publish deduction/severity counts, failed/total rules, diagnostic counts and repair gates. Missing execution, source drift, configuration/policy mismatch or unresolved applicability withholds the affected score. Retain an available other-tool score with the assessment incomplete. Static scores do not establish business/runtime/UI acceptance.

Use `compose-quality score` or `compose-quality compare`. Preserve frozen candidates and original evidence. Do not repair code, access devices or export Previews as a scoring action.

## Evidence handoff

Use valid packets from [verify](verify.md). New scans must use that same entry point and built-in policy; scoring does not enable extra rules. Reuse unchanged valid evidence explicitly. For authorized independent review, follow [independent review](score/independent-review.md). Do not create chats or delegate without authorization.

For requested visual comparisons, use the [chart exporter](score/charts.md): `compose-quality chart chart.json --out-prefix reports/score-comparison`. It groups by metric and preserves configured scenario names/order.
