# Standalone Android Lint and detekt CLIs

The analyzers run directly as **`lint`** and **`detekt`**. No Gradle wrapper, Gradle task, init script, AGP plugin application or temporary build project is used by installation or scanning. `compose-quality` is an optional incremental-report/scoring helper; it is not required to use the native analyzers.

## Install missing tools automatically

```sh
sh /abs/plugin/install-analyzers.sh
lint --version
detekt --version
```

The plugin calls this bootstrap when an authorized check needs the tools. It detects compatible existing native commands and reuses them; otherwise it installs checksum-pinned upstream CLI runtime artifacts globally for the current user. Commands are placed at `~/.local/bin/lint` and `~/.local/bin/detekt`; private, versioned runtime files live under `~/.local/share/compose-quality/analyzers/`. It never applies an analyzer Gradle plugin or changes a project's build files/checks.

The JSON result returns each absolute executable. Use it immediately in the current process. If necessary, supported shell startup files receive one managed PATH block. An incompatible or unrelated existing command is preserved; use the returned private executable if a global name is occupied. No sudo or system package-manager changes are used. Corrupt installations fail explicitly and remain available for inspection.

```sh
sh /abs/plugin/install-analyzers.sh --check
sh /abs/plugin/install-analyzers.sh --tool detekt
sh /abs/plugin/install-analyzers.sh --bin-dir /abs/bin --data-dir /abs/analyzers
```

`--check` is read-only: 0 means ready, 1 means missing/incompatible, 2 means an environment/configuration error. Installation supports macOS/Linux and requires Python 3.9+ plus JDK 17+. It installs **the two analyzer CLIs**, not Python, a JDK, Android Studio, SDK platforms, adb or an emulator. First uncached installation needs access to Google Maven and Maven Central; subsequent scans use local artifacts. Existing Maven/Gradle caches are optional byte-verified download caches only, never execution dependencies.

## Bundled rules

- Android Lint: upstream standalone runtime `com.android.tools.lint:lint:32.4.0` (prints CLI version **9.4.0**) and bundled Slack Compose Lint **1.6.1**.
- detekt CLI **2.0.0-alpha.6**, maintained `io.nlopez.compose.rules:detekt:0.6.8` plus its `common-detekt` support JAR, and prebuilt custom Composer rules **1.4.1**.
- One bundled detekt YAML: 8 native, 38 maintained Compose and 19 custom rules, **65 enabled rules**. Source and prebuilt custom JAR/config fingerprints must agree.

The rule JARs are physically in the package. Analyzer runtime libraries are installed from a fixed artifact lock with SHA-256 checks, without resolving a project's Gradle dependencies. The launchers verify their installed runtime before invoking the upstream Java main class. They supply the bundled rule defaults; explicit caller configurations still need a separate reviewed profile. A compatible external CLI receives the same rule arguments from the incremental helper.

AndroidX libraries can ship additional official Compose lint checks. They are project-specific dependencies, not automatically implied by installing Android Lint. For declared extracted library `classes.jar` entries, the helper also registers a sibling `lint.jar` from that same artifact. Supply other selected dependency registries explicitly in `lint_rule_jars`; it never searches arbitrary caches. Never mark unavailable checks as executed.

## Full analysis needs compilation inputs

Removing Gradle integration does not remove the need for source roots, selected variant, resolved dependencies, generated declarations or SDK types. Use real IDE/build metadata or explicitly maintained compilation inputs. The helper does not run Gradle to obtain them, inspect arbitrary cache directories as an invented classpath, or silently downgrade to syntax-only analysis.

Example context, stored outside the worktree:

```json
{
  "schema_version": 1,
  "project": "/abs/android-project",
  "module": ":app",
  "module_dir": "app",
  "variant": "debug",
  "source_roots": ["app/src/main/java", "app/src/debug/kotlin"],
  "generated_sources": [],
  "classpath": ["/abs/resolved/compose-runtime.jar", "/abs/resolved/other-dependency.jar"],
  "jvm_target": "17",
  "language_version": "2.3",
  "provenance": "Describe the actual selected compilation metadata and its version here",
  "android": {
    "sdk": "/abs/android-sdk",
    "compile_sdk": "36",
    "manifest": "/abs/current/merged/AndroidManifest.xml",
    "resources": ["app/src/main/res"],
    "library": false
  },
  "lint_rule_jars": []
}
```

Paths other than `project` resolve relative to the project; a relative `project` resolves relative to the context file. Supply only existing selected source roots and the **complete actual classpath**, not the two illustrative JARs above. For Android Lint use the selected dependency libraries with full classes/registries, not a stripped compile-only API classpath: runtime manifest classes and embedded AndroidX lint checks may otherwise be absent. Classpath entries must be resolved classes directories/JARs, not AAR archives. Optional fields: `api_version`, `jdk_home`, `lint_config`. Unsupported fields/options fail rather than being ignored. Unsupported Kotlin compiler options/context structures require explicit support before claiming complete coverage.

The context file supplies analysis inputs, **not Gradle configuration**. Generated R/BuildConfig declarations, dependency modules, variant overlays and manifests must correspond to the selected compilation. Existing artifacts may be reused if current; the CLI does not compile the app to refresh them. A supplied `provenance` string is not proof of completeness: reviewers must verify the selected context before publishing scores. Missing inputs block analysis; hashes detect changes, not missing undeclared dependencies.

## Incremental scans and scoring

Native tools can be invoked directly with their documented flags. For Git filtering/evidence, use the bundled helper scripts, or optionally install the convenience command:

```sh
sh /abs/plugin/install-cli.sh
compose-quality lint --context /abs/context.json --base origin/main --merge-base
compose-quality detekt --context /abs/context.json --base origin/main --merge-base
compose-quality score manifest.json evidence.json
compose-quality compare manifest.json A-evidence.json B-evidence.json C-evidence.json
```

`install-cli.sh` ensures the optional helper **and both native CLIs**. Equivalent plugin-side calls are `python3 /abs/plugin/skills/verify/scripts/incremental_lint.py run --context /abs/context.json` and the corresponding `incremental_detekt.py`. The helper performs the same direct native CLI execution; it has no Gradle backend.

`prepare` creates a fresh external directory and prints a `command_file` containing argv and cwd. Execute that native argv, then use `check --run-dir /abs/run --exit-code ACTUAL_CLI_EXIT`. There is no `--gradle-exit-code` interface. `run` performs these steps itself and keeps analyzer output in `analyzer.log`.

The Android Lint `--project` XML is an external **source-layout descriptor**, not a generated Gradle project. It includes actual source/resource/manifest/classpath entries and `<lint-checks>` registries. For this upstream CLI, a descriptor's rule entries override the per-project `--lint-rule-jars` setting; the helper explicitly writes the bundled and declared dependency registries into the descriptor. No project file is modified.

Both tools analyze the declared compilation; only findings with a diagnostic location starting on a Git-added/modified line enter the incremental gate. Preserve unchanged/unlocated diagnostics. Sources, context, configurations, rules, runtime artifacts and relevant Java environment are frozen and checked for drift. The CLI does not auto-fix source or operate devices/Previews; impl owns the default implementation correction loop. Exit 0 means no blocking matched diagnostics; 1 means a failed incremental gate; 2 means invalid execution/evidence. The native tools have their own exit codes; the helper runs full reports before applying its incremental gate.

Scoring retains the v12 policy: separate Lint/detekt numbers, no category grades or total. Native CLI receipts identify `standalone-cli`, declared compilation provenance and exact inputs; they never claim Gradle evaluated the project. Full selected-rule execution and context completeness need evidence. Missing/unavailable/suppressed/unverified rules withhold the affected score. Legacy frozen reports retain their historical provenance and scores; do not relabel them as native CLI runs.

## Distribution and maintenance

```sh
python3 skills/verify/scripts/build_cli.py --out /abs/new-release.tar.gz
```

The relocatable archive includes both installers, engines, pinned artifact lock, rule JARs/source, YAML and score policies. Analyzer runtime dependencies download during installation rather than inflating every plugin bundle. Build/installation checks file integrity; hashes do not establish publisher authentication. See [third-party notices](skills/verify/scripts/runtime/THIRD_PARTY.md). Publishing is separate from building.

Upstream interfaces: [detekt CLI](https://detekt.dev/docs/next/gettingstarted/cli/), [Android Lint CLI flags](https://android.googlesource.com/platform/tools/base/+/e8f252c955da33ef6e65991b32086ca0e12a1722/lint/docs/usage/flags.md.html), [Lint source-layout descriptors](https://android.googlesource.com/platform/tools/base/+/986f289a7429218e68ea2605aee640334ed1baae/lint/cli/src/main/java/com/android/tools/lint/ProjectInitializer.kt).
