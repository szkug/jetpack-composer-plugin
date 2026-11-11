# Incremental detekt CLI

Use the [native CLI installation/input guide](cli.md) and [detekt predicates and spec basis](detekt-rules.md). The actual engine is detekt CLI 2.0.0-alpha.6, with bundled maintained Compose 0.6.8 and custom Composer 1.4.1 JARs and one YAML. The Gradle plugin/task/init-script integration has been removed.

```sh
compose-quality detekt run --context /abs/compilation-context.json --base HEAD --out /abs/new-evidence-dir
```

Or use the skill's `scripts/incremental_detekt.py run` directly. Both ensure the native CLI exists, pass `--analysis-mode full`, actual source/classpath/language/JVM inputs, bundled plugins/config and SARIF output. `--fail-on-severity Never` only lets the full report be produced; the helper applies the requested incremental gate afterward. There is no auto-correct, baseline suppression, syntax fallback or replacement project. Ordinary project checks are untouched.

`prepare` freezes inputs and writes a native argv to command.json. Execute it and use `check --run-dir ... --exit-code ACTUAL_CLI_EXIT`. A missing report, source/context/runtime/config drift or CLI execution error fails verification. Source and classpath are explicit compilation inputs; do not claim Gradle selected them or that their existence alone proves completeness.

Gate findings only when an explicit SARIF startLine falls on an added/modified Git line. Declaration endLine does not expand eligibility. New files are all new lines; pure renames/deletions add no checked lines. Preserve unchanged and unlocated diagnostics. Exit 0/1/2 means incremental pass/block/execution-invalid. Default blocks errors; `--fail-level warning` also blocks warnings.

Publish only with exact selected-rule inventory/execution evidence, source/base and config/artifact hashes. Zero findings are not evidence a missing rule ran. V12 requires all 65 selected rules enabled, full analysis, reviewed context and independent gate evidence. Historical Gradle reports remain historical; rescanning with native CLI is a new evidence set, not a receipt edit.
