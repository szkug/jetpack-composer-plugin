---
name: jetpack-composer
description: Compatibility entry for the public Compose implementation workflow; route to the maintained impl skill and its shared standards.
---

# Compose compatibility entry

For implementation, read [the maintained impl skill](skills/impl/SKILL.md) and resolve its references relative to that file's directory. For Lint/detekt scans and diagnostic evidence use [verify](skills/verify/SKILL.md); for requested scoring use [score](skills/score/SKILL.md). Shared standards live in [spec](skills/spec/SKILL.md).

The plugin manifest exposes the four skills under `skills/`. This entry preserves direct repository-root use without duplicating their instructions.

For authorized static checks install/reuse the real Android Lint and detekt CLIs using `install-analyzers.sh`; see the [CLI guide](CLI.md). Native analysis has no Gradle/AGP plugin integration. The optional compose-quality helper handles incremental reports and scoring.
