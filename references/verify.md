# Compose static verification

## Derive checks from the specification

[spec](spec.md) defines intended implementation behavior under the task and applicable project contracts. Select and maintain verification predicates from those requirements. Read the relevant spec topic first when establishing applicability; tool availability or an upstream default does not create a new source requirement.

Use the verification-owned [Lint](verify/lint-rules.md), [native detekt](verify/detekt-rules.md), [maintained Compose](verify/compose-rules.md) and [custom Compose](verify/custom-compose-rules.md) maps for the requirement basis, exact recognition and limitations. A normal scan uses the selected frozen profile; it does not regenerate rules or change thresholds per candidate.

If a predicate covers only part of a requirement, report that boundary. If it overreaches a valid requirement/project variation, retain the raw result and resolve applicability with evidence. Do not rewrite spec to fit a tool, treat missing coverage as success, or fill the gap with a new manual score. Changes to a profile must remain explicit and consistently applied to compared candidates.

## Establish scan inputs

Identify the source snapshot, Git base, changed-line scope, actual module/variant and selected rule profile. Use explicit verified compilation metadata: source roots, dependencies, compiler settings and Android SDK inputs. Read the [CLI guide](verify/cli.md) for the schema and bootstrap. Missing inputs block the scan; do not infer them by running Gradle or creating a substitute project.

This procedure verifies configured static rules. It does not add a parallel manual quality audit, business acceptance checklist, Preview render or device session. Project-required compilation and separately requested functional/runtime acceptance still follow their own task/project workflow; a static pass does not establish those results.

## Run the native analyzers

Use the [Lint adapter](verify/incremental-lint.md) and [detekt adapter](verify/incremental-detekt.md). The bootstrap detects or installs compatible native CLIs with the bundled rule packages. Scans execute without AGP/detekt Gradle plugins and preserve the project's existing checks.

Analyze the declared context, then filter diagnostics to added/modified lines. A changed-line pass is not a full-project pass. detekt uses complete type analysis, including syntax checks in the same invocation; there is no reduced-analysis fallback. Reuse unchanged valid evidence where appropriate, identifying it as reuse rather than a new scan.

## Validate results

Follow [analyzer evidence requirements](verify/evidence.md). Check actual execution, source/context/config/artifact identity, selected-rule coverage and generated reports before interpreting a clean result. A registered rule, empty report or successful process exit alone does not establish complete coverage.

Retain matched, excluded and unlocated diagnostics plus execution errors separately. Inspect source only as needed to interpret a reported diagnostic, scope, duplicate or exception. Use the verification maps and their linked spec basis to interpret applicability; do not replace tool results with a manually filled design checklist.

Respect accepted, narrowly scoped exceptions with source evidence and project authority. Do not disable rules, generate baselines or alter source to manufacture a pass. Unknown coverage or unresolved scope remains incomplete.

## Report and hand off

Report each analyzer's version/profile, source/base/module/variant, scan scope, raw exit and filtered gate, report locations, diagnostics and unresolved limitations. Supply valid evidence packets to [score](score.md) when scoring is requested; verify does not assign points.

Return confirmed in-scope source defects to the [implementation workflow](../SKILL.md). Implementation requests use its default correction/reverification loop; the verification procedure itself remains read-only. Standalone verification does not authorize edits. Preserve frozen or review-only candidates. After authorized changes, rerun the affected checks against the new snapshot; old reports are not current evidence.

Lint/detekt results cover their executed predicates, not arbitrary business correctness, rendered appearance, performance or the broader readability principles in spec. Report those limits without adding manual grades or treating unmeasured behavior as passed.
