# Incremental Android Lint CLI

Use the [native CLI installation/input guide](cli.md) and [Lint predicates and spec basis](lint-rules.md). The engine is standalone Android Lint, with bundled Slack Compose Lint 1.6.1 and any declared dependency lint registries. No AGP/Gradle plugin, task or init script is configured/executed.

```sh
compose-quality lint run --context /abs/compilation-context.json --base HEAD --out /abs/new-evidence-dir
```

Or use the skill's `scripts/incremental_lint.py run` directly. Both ensure the native CLI exists and create an external lint `--project` source-layout descriptor from real source, classpath, resource and manifest inputs. That XML is not a temporary build project. Register rule JARs in its `<lint-checks>` entries: the descriptor can override per-project `--lint-rule-jars` arguments. The helper registers sibling lint.jar files only for declared extracted classes.jar artifacts; include other project dependency registries explicitly when selected; installing Lint alone does not supply every AndroidX Compose detector.

`prepare` freezes inputs and writes command.json with native argv/cwd. Execute it, then `check --run-dir ... --exit-code ACTUAL_CLI_EXIT`. Preserve XML, context, diff manifest, receipt and result. Analyzer/parse failures and input drift fail verification. No source repair, device or Preview run is authorized.

Lint analyzes the declared compilation, then the helper filters explicit XML locations by Git-added/replacement lines. Pure renames/deletions add no eligible lines; new files are eligible in full. Unchanged and unlocated diagnostics remain in the evidence. The fixed incremental gate blocks warnings and errors/fatals; suggestions do not block. Exit 0/1/2 means incremental pass/block/execution-invalid, not whole-project cleanliness.

The scan uses an empty external baseline to expose findings for filtering. The built-in policy enables every registered rule, including default-disabled rules, using native registry severity in a generated override; project lint.xml activation/severity overrides are not authoritative. Explicit lint_config is rejected. Suppressed or missing coverage cannot earn a passed check. No project policy, baseline, build file or ordinary lint output is modified. Context completeness and selected-rule execution must be verified before publishing scores; an unlocated issue cannot be silently discarded.
