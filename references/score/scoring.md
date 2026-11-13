# Scoring policy and assessment procedure

Protocol v14 publishes independent Lint and detekt scores out of 100. Both use the same [built-in rule policy](../verify/rule-policy.json), activation, configuration and native severity as implementation verification. Projects cannot opt out or change severities. There is no cross-tool total or mean.

## Deduction and repair policy

```text
score = max(0, 100 - sum(deduction of each distinct confirmed failing rule))
```

| Classification | Native severity | Deduction | Implementation action |
| --- | --- | --- | --- |
| suggestion | Information / Informational / Hint | 1 | AI decides from code context; explain retained findings |
| warning | Warning | 2 | Must repair |
| error | Error / Fatal | 3 | Must repair |

One suggestion, one warning and one error yield 94 points. One or one hundred violations of the same rule lose its points once. Two different rules on the same defect each deduct independently. Diagnostic occurrences and defect groups remain visible. Retaining a valid suggestion does not waive its deduction. Missing related syntax does not alter the score or inventory; this protocol does not claim to measure applicability or code correctness as a percentage.

The [Lint mapping](lint-policy.json) and [detekt catalog](catalog.json) must match the shared policy. detekt native severities must match its catalog and bundled YAML. The fixed native scan gate blocks warnings and errors; suggestions do not block. A high score cannot override the repair gate.

## Complete shared execution

Lint enables every registered rule, including default-disabled and non-Compose rules. Native `--list` and `--show` discovery must agree, with raw outputs, hashes and rule-provider artifacts retained in `lint-inventory.json`. The generated override enforces registry severity for implementation and scoring. Project lint.xml cannot override activation/severity; explicit `lint_config` is rejected. Supply all dependency/custom rule JARs through actual compilation context; registry discovery cannot prove completeness of an incorrectly supplied context.

Freeze the complete inventory in `analyzer_profiles.android-lint.rule_inventory`. `rule_severities` must exactly equal its rules map. Lint `selected_rules` is forbidden. The report's `policy.ruleInventory`, provider identities, `policy.allRegisteredRulesExecuted` and execution severity receipt must agree. detekt `required_rules` must exactly equal the complete enabled catalog; disabled built-in rules remain disabled for both verification and scoring.

Manifest `rule_policy_sha256`, inventory `rule_policy_sha256` and report `policy.rulePolicySha256` bind execution and scoring to the same policy. Configuration, rule-provider or severity drift prevents publication. Scoring consumes verification evidence rather than enabling additional scoring-only rules.

## Evidence and publication

Freeze source/base, module/variant, actual compilation context, policy/configuration/artifact hashes and required execution coverage. Compared candidates share the same configuration and policy. Preserve frozen candidate source. Declare retrospective exposure; reuse valid unchanged evidence explicitly rather than claiming a fresh scan.

Apply changed-line filtering before counting. Retain matched, excluded and unlocated diagnostics, adjudications, occurrence counts and evidence-backed defect groups. Only proven false positives or documented fixed-contract exceptions may remove a charge; project preference and optional suggestion repair are not exemptions. An additional confirmed violation of an excepted rule still deducts.

Publish `score`, `starting_score`, `raw_deductions`, `applied_deductions`, `severity_counts`, `deductions_by_severity`, `failed_rule_count`, `total_rule_count`, `finding_count`, `defect_count` and repair gate. Each `rule_results` entry records classification, deduction, must-fix, execution status and diagnostics. Raw deductions may exceed 100; applied deductions are capped at 100 and score floors at zero.

Missing/unavailable/suppressed/unverified checks, unresolved diagnostics, analysis failures or source drift withhold the affected score. Observed deductions are lower bounds, not final grades. Preserve the full required inventory; incomplete checks are not passes. An available other-tool score remains visible with overall publication withheld. Runtime/build/business/visual acceptance remains separate. Report actual KMP source sets and type resolution; Android-only results do not establish commonMain coverage.

## Versions and commands

v14 replaces v13 weighted rule pass rates with deductions and a shared warning/error repair gate. Preserve historical manifests and results; old schemas are rejected rather than reinterpreted. A new assessment needs a separately identified v14 manifest and policy-bound execution evidence. Never relabel legacy receipts or silently change historical candidate scores.

```sh
compose-quality score manifest.json evidence.json
compose-quality compare manifest.json A.json B.json C.json
compose-quality compare manifest.json reviewer-a.json reviewer-b.json --agreement
```

`--diagnostic` permits incomplete output, not publication. `--agreement` needs identical source and raw evidence. Recalculation proves determinism, not independent review. No manual grades, category budgets, `--mean` or cross-tool totals. The [manifest](example-manifest.json) and [evidence](example-decisions.json) examples are synthetic format inputs.
