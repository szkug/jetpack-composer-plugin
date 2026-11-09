# Bundled rule artifacts and standalone runtimes

The unmodified rule JARs below are distributed with this plugin:

| Artifact | Upstream | License |
| --- | --- | --- |
| `com.slack.lint.compose:compose-lint-checks:1.6.1` | https://github.com/slackhq/compose-lints | Apache-2.0; Copyright 2023 Salesforce, Inc., Copyright 2022 Twitter, Inc. |
| `io.nlopez.compose.rules:detekt:0.6.8` | https://github.com/mrmans0n/compose-rules | Apache-2.0; maintained fork of Twitter Compose rules |
| `io.nlopez.compose.rules:common-detekt:0.6.8` | https://github.com/mrmans0n/compose-rules | Apache-2.0 |

License texts accompany the corresponding packages at `../rules/detekt-compose-rule/LICENSE` and `../rules/slack-compose-lint/LICENSE`. Exact downloaded Maven coordinates and binary SHA-256 values are pinned in `analyzers.lock.json` (bundled rules map and analyzer artifact lists). `composer-quality-rules.jar` is generated from this plugin's `../rules/custom-compose-rule/src/ComposerRules.kt`, provider service declaration and the single `../rules/detekt.yml`; source/config hashes are recorded in the same lock. It is intentionally distributed as a prebuilt rule artifact, not an application build output.

The Android Lint and detekt engine runtimes and their dependencies are downloaded unmodified from Google Maven / Maven Central during installation. Their original JAR metadata, licenses and notices remain intact. They are Java CLI libraries; the lock does not install AGP or the detekt Gradle plugin. Download hashes verify fixed bytes, not publisher identity.

Maintainers can rebuild the custom JAR using `python3 skills/verify/scripts/build_rule_jar.py --out /abs/new-rule.jar`. This invokes the pinned Kotlin compiler from the installed detekt runtime, never Gradle. Update the bundled JAR, source/config hashes and release version together after validating changes. Rule execution or installation must not silently recompile or bless drifted rules.
