# Verification gates

Run gates in order. A later pass does not erase an earlier failure. Route failures back to the earliest owning gate and rerun affected downstream gates.

## Gate 0 — isolation and unchanged baseline

- Worktree preflight matches the immutable base revision.
- Scope names the exact target entry, variant, preserved consumers, and acceptance states.
- The unchanged target builds, or an unrelated baseline failure is recorded without migration edits.

## Gate 1 — legacy-truth publication

- `baseline-assessment.json` covers every acceptance state.
- Runtime/reference capture was attempted only where proportionate; fallback reasons are explicit.
- Appearance, data, and behavior evidence are separated.
- `source` evidence is not described as a runtime comparison.
- Material uncertainty was resolved by the user or remains a named acceptance item.

No production implementation begins before this gate passes.

## Gate 2 — inventory and real-data lineage

- Target and preserved entries are proven through runtime conditions.
- Recursive XML/DataBinding, adapter, imperative mutation, and behavior inventory is complete.
- Every displayed or interaction-driving value traces from its real producer through update timing and policy to the legacy consumer.
- Proposed Compose state is a lossless mapping; no production fixture, copied list/counter, or convenient reduced state replaces the real contract.
- Loading, empty, error, refresh, paging, restoration, and media policies are mapped where reachable.

## Gate 3 — vertical-slice plan

- Slices are user-visible contracts, not UI/data/test implementation layers.
- Each slice closes appearance, real data, behavior, Preview, and focused verification together.
- The representative first slice exercises a dominant or risky page assumption.
- Every inventory item and behavior contract has one slice owner.

## Gate 4 — per-slice convergence

For each slice, before starting the next:

- production receives every displayed value from its proven producer;
- relevant terminal effects are executable and tested;
- production components are rendered by Preview without a copied UI;
- appearance is compared against the strongest recorded evidence;
- compile, render, and focused tests pass;
- the coordinator independently reviews the actual source and result;
- status is `passed`, not merely generated, compiled, or uncertain.

When legacy runtime visuals are unavailable and dominant styling remains uncertain, obtain user feedback on the representative slice before propagating it, unless autonomous source-led completion was explicitly requested.

## Gate 5 — exhaustive Preview and implementation performance

- Every production surface and independently stateful/interactive component is directly previewed or concretely parent-covered.
- Every UI-state field and reachable equivalence class maps to rendered scenarios.
- Preview fixtures are test-only and never cited as production data evidence.
- State ownership, recomposition boundary, collection identity, media bounds, effect lifetime, and expensive-work placement are evidence-backed.
- No runtime performance claim is based on Preview rendering.

## Gate 6 — final atomic replacement

- Only the frozen target entry selects the Compose tree.
- Preserved shared entries remain unchanged.
- No hidden legacy fallback, duplicate UI tree, or partial placeholder remains.
- Obsolete code is removed only after proving no preserved caller.
- Relevant compile, focused unit, and applicable host/integration tests pass.
- Preview summary matches the final catalog and revision.
- `scripts/validate_migration_ledger.py` exits zero.

## Gate 7 — coordinator convergence and claim

- The coordinator personally reviews legacy-to-new and new-to-legacy mappings.
- Every Compose state field has a real producer and equivalent update policy.
- Every event reaches the original or approved terminal effect.
- Every surface is judged against the strongest available baseline level.
- `convergence-review.md` names unresolved items and contains no hidden blocker.
- `verification-summary.md` uses only `source-reconstructed`, `reference-compared`, `runtime-compared`, or `user-accepted` at the level actually supported.

The structural validator cannot pass this semantic gate by itself.

## Minimum commands

Use repository-specific tasks. At minimum run:

1. unchanged baseline compile;
2. compile plus focused state/event tests for each completed vertical slice;
3. applicable host/integration tests;
4. Preview compilation/render for every catalog scenario;
5. migration-ledger validator;
6. final status and diff-path audit.

If Preview rendering or runtime comparison is unavailable, record the precise limitation and use the corresponding lower claim level. Do not reduce coverage or silently upgrade confidence.
