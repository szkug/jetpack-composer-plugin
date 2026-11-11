# Two-tool static scoring

Use the [scoring policy](score/scoring.md). The only numeric results are Lint and detekt, each calculated from distinct evidence-backed defects. Category labels do not carry grades, budgets or weights; no combined total or mean is calculated.

[Catalog](score/catalog.json) and [Lint policy](score/lint-policy.json) define deductions. Consume verification-owned [coverage](verify/coverage.json), [boundaries](verify/acceptance-boundaries.json) and execution evidence. Do not redefine implementation requirements or analyzer predicates here.

Freeze actual source/base, module/variant, tool/configuration/artifact identities and evidence policy. Missing execution, source drift or unresolved diagnostic applicability withholds the affected tool score; preserve an available other-tool result with the assessment marked incomplete. Keep gates separate from numeric publication. Static results do not establish business/runtime acceptance.

Use `compose-quality score` or `compose-quality compare`. No manual grades, category budgets or aggregate are accepted. Preserve frozen candidates and original evidence. Do not repair code, access devices or export Previews as a scoring action.

## Evidence handoff

Use valid packets from [verify](verify.md). If new scans are required, continue there for native CLI setup, context validation and evidence collection, then return here for calculation. Reuse unchanged valid evidence when it answers the task, labeling it as reuse.

For authorized independent review, follow [independent review](score/independent-review.md). Repeated calculation proves determinism only. Do not create chats or delegate without authorization.
