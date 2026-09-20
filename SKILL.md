---
name: ilove-compose
description: Orchestrate and implement an existing Android XML/View/DataBinding screen migration to Jetpack Compose with staged legacy-truth, real-data, visual, and behavior parity gates. Use for code-led production migrations; not for greenfield UI or design-file implementation.
metadata:
  short-description: Staged lossless View-to-Compose migration
---

# I Love Compose

Migrate a reachable production View screen to one Compose tree. Treat this as a staged convergence task, not a one-pass rewrite followed by self-authored evidence. Compilation and Preview rendering prove mechanics, not parity.

## Roles and authority

The reachable legacy path is the product truth:

- appearance: XML, styles, dimensions, drawables, BindingAdapters, adapters, runtime mutations, and any trustworthy visual references;
- data: the actual producer, transformation, observation, refresh, loading, empty, error, and restoration paths;
- behavior: listeners, navigation, analytics, permissions, dialogs, pagination, media, animation, accessibility, and cleanup;
- scope: the requested runtime entry and its proven discriminators, not shared filenames.

The main/coordinating agent owns every publication gate and the final convergence review. If implementation is delegated, a worker may implement a bounded slice but may not approve its own baseline, parity, or completion. Do not run a parallel competing baseline or final review.

This skill owns migration code, production wiring, Preview coverage, executable logic verification, and source-level performance review. Device installation, screenshot infrastructure, and profiling remain coordinator-owned follow-ups unless separately requested.

## Required working artifacts

Create these in a task-owned evidence directory outside production sources:

- `scope-contract.json` (schema 4): frozen entry and replacement boundary;
- `baseline-assessment.json` (schema 1): per-state legacy truth level, evidence, failed capture attempts, and uncertainty;
- `legacy-inventory.json` (schema 2): reachable View/DataBinding inventory;
- `migration-slices.json` (schema 1): ordered vertical slices and their individual gate results;
- `migration-ledger.json` (schema 9): legacy-to-Compose mappings, real producer lineage, and behavior contracts;
- `preview-catalog.json` (schema 3) and `preview-summary.json`;
- `performance-audit.json` (schema 1);
- `convergence-review.md`: the coordinator's final source/data/visual/behavior review;
- `verification-summary.md`: commands, results, claim level, unresolved items, and handoff.

Read [references/orchestration.md](references/orchestration.md), [references/migration-audit.md](references/migration-audit.md), [references/compose-architecture.md](references/compose-architecture.md), and [references/verification-gates.md](references/verification-gates.md) before editing production code. Use `scripts/inventory_android_view.py` when a root XML exists.

## Orchestrated workflow

### 1. Isolate and freeze the target

Run `scripts/preflight_android_worktree.sh <primary-checkout> <worktree>` for a new worktree. Prove the runtime entry, shared consumers, build variant, and immutable baseline revision. Write `scope-contract.json` and build the unchanged target before implementation.

Do not silently narrow a whole-page request to a convenient subtree or widen a shared Fragment migration to every consumer.

### 2. Establish the best available legacy truth

For every acceptance state, try the evidence chain in order:

1. live legacy runtime on comparable device/account/data;
2. archived screenshots, recordings, approved product references, or test goldens;
3. reconstruction from reachable XML/resources/adapters/runtime mutations plus producer and behavior paths;
4. explicit unresolved uncertainty.

A missing legacy screenshot is not a blocker by itself. Record why stronger evidence is unavailable and continue with the strongest reachable level. Do not call source reconstruction a runtime comparison.

The coordinator publishes one concise baseline assessment before implementation: scope, evidence level by state, unavailable evidence, and uncertainties that can change the implementation. When a core visual language, data policy, or interaction outcome remains ambiguous, obtain user direction before implementing that part. Minor uncertainty may remain an explicit acceptance item.

### 3. Freeze data lineage before designing Compose state

Trace each displayed or interaction-driving value from its legacy producer through transformation and observation to its consumer. Record update timing and loading/empty/error policy. Only then design the Compose state boundary.

Do not invent a convenient aggregate state and later point the ledger back at legacy code. A new UI model is allowed only as a lossless projection whose every field has producer evidence and mapping evidence. Reuse existing ViewModel/Repo/adapter state when it already owns the contract. Production fixtures, fabricated counters, copied lists, and no-op terminal callbacks are hard failures.

### 4. Publish an ordered vertical-slice plan

Split by independently reviewable user-visible contracts, not XML containers. Each slice must include, in the same unit:

- legacy appearance/resources and supported variants;
- real producer-to-UI data flow;
- interactions through terminal effects;
- production component and Preview scenarios;
- focused executable verification.

Choose the first slice to expose the page's dominant styling and data architecture. Do not implement the whole page before learning whether that representative slice is faithful.

### 5. Converge one slice at a time

For a slice:

1. map its frozen legacy items, producers, and behaviors;
2. implement production wiring and appearance together;
3. add production-component Previews and focused state/event tests;
4. compile and render the affected scenarios;
5. have the coordinator inspect source lineage and compare visuals against the strongest available baseline;
6. record pass, uncertainty, or failure in `migration-slices.json`.

Do not start the next slice while the current one has a known data, behavior, or style mismatch. When runtime visual evidence is unavailable, expose the first representative slice for user review before expanding the same uncertain visual decisions across the page, unless the user explicitly asks for autonomous source-led completion.

Preview fixtures explore states; they never establish that production receives those values. Screenshot tests protect the new rendering from regression; they do not prove equivalence to the legacy rendering unless they use an independently obtained legacy oracle.

### 6. Preserve behavior and performance

At the Screen seam, prove state rendering and event dispatch. At the host/ViewModel seam, prove the terminal result. Preserve lifecycle collection, debounce, idempotency, restoration, nested scroll, accessibility, media failure, pagination, and cleanup where reachable.

Record state ownership, recomposition boundaries, collection identity, media bounds, effect lifetimes, and expensive-work placement. Do not infer runtime performance from Preview or annotations.

### 7. Replace atomically and run convergence review

Keep one production tree. Remove legacy code only after proving no preserved consumer reaches it. Run the ordered gates in [references/verification-gates.md](references/verification-gates.md), then `scripts/validate_migration_ledger.py`.

Before declaring completion, the coordinator personally reviews the merged implementation in both directions:

1. legacy item/state/behavior -> exactly one mapped or intentionally removed outcome;
2. Compose state field -> a proven legacy producer and equivalent update policy;
3. event -> its original terminal effect;
4. rendered surface -> the strongest available appearance evidence;
5. unresolved item -> an explicit limitation or user acceptance item.

The validator checks structural consistency only. It cannot approve visual similarity, producer semantics, or terminal behavior.

## Failure routing

Route a failed check back to its owning stage instead of patching the final screen blindly:

- wrong scope/shared consumer -> scope gate;
- wrong style, spacing, asset, typography, or visibility -> baseline/inventory gate;
- fake, stale, missing, or differently timed data -> data-lineage gate;
- click stops at a callback or changes outcome -> behavior gate;
- Preview passes but runtime differs -> production-wiring/lifecycle gate;
- user rejects a representative slice -> revise its baseline interpretation, then re-review dependent slices.

After correction, rerun that gate and every downstream gate it invalidates.

## Claim levels

Use the strongest claim actually supported:

- `source-reconstructed`: matched reachable source/resources and executable logic, with stated visual uncertainty;
- `reference-compared`: compared against archived/approved visual references;
- `runtime-compared`: compared legacy and Compose under documented comparable runtime state;
- `user-accepted`: user explicitly accepted the delivered runtime result.

Build success, Preview success, screenshot generation, ledger validation, or device installation alone never upgrades the claim level.

## Hard failures

- Implementation begins before scope, baseline assessment, and data lineage are established.
- The whole page is implemented before the first uncertain representative slice is reviewed.
- A Compose state field lacks a proven legacy producer or changes loading/empty/error/update semantics without an approved requirement.
- Production contains demo data, copied counters/lists, no-op events, disconnected terminal effects, or a hidden legacy fallback.
- Preview or new screenshot goldens are presented as independent legacy truth.
- An implementer approves their own delegated slice without coordinator review.
- Known mismatches are relabeled as complete because compilation, Preview, or a structural validator passes.
- Completion is claimed above the recorded evidence level.

## Completion contract

Completion requires all slices to pass their individual data, visual, behavior, Preview, and compile gates; the final atomic replacement to pass relevant tests; preserved consumers to remain proven; the coordinator convergence review to contain no undisclosed blocker; and the final claim to match the available baseline evidence. Unresolved visual details may be delivered only as named acceptance items, never as lossless parity.
