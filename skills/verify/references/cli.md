# Standalone analyzer installation and execution

Use the [CLI guide](../../../CLI.md). When authorized checks need tools, first run `sh /abs/plugin/install-analyzers.sh`: detect/reuse compatible Android Lint and detekt CLIs or install missing pinned versions for the current user. Use the returned absolute executables. Bundled maintained Compose, Slack Compose Lint and custom Composer JARs require no project Gradle integration.

`lint`/`detekt` are the real upstream CLIs. The optional `compose-quality` helper only prepares explicit analysis inputs, invokes these CLIs, filters Git changes and scores evidence. `install-cli.sh` can install that helper together with both tools. No Gradle/AGP tasks, init scripts or temporary Gradle projects are allowed in this execution path.

Supply an actual compilation-context JSON with source roots, classpath, module/variant and SDK/manifest/resources as needed. Obtain existing trustworthy metadata; do not guess a classpath or execute a hidden build. Missing or unsupported context fails explicitly. Context hashes prove stability, not completeness; review provenance before scoring. Native `prepare` outputs command.json; `check` accepts `--exit-code` from the actual CLI execution.

Installers need Python 3.9+ and JDK 17+. They install the analyzer CLIs, not the language/Android development environment. The installers and analyzers do not edit source or operate devices/Previews. For implementation tasks, impl owns the default diagnostic-guided correction loop.
