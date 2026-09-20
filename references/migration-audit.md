# Migration audit schemas

All source evidence uses repository-relative `path:line`. Evidence must identify the concrete declaration or statement, not a broad file.

## `scope-contract.json` schema 4

```json
{
  "schemaVersion": 4,
  "baselineRevision": "full immutable commit",
  "allowedChangePrefixes": ["feature/src/"],
  "replacementBoundary": "Exact requested runtime surface",
  "targetEntries": [
    {
      "name": "MainActivity Me tab",
      "condition": "HomepageFrag with isHomepagePage == false",
      "entryEvidence": ["feature/src/.../HomepageFrag.kt:42"]
    }
  ],
  "preservedSharedEntries": [
    {
      "name": "Standalone homepage profile",
      "condition": "HomepageActivity creates HomepageFrag with isHomepagePage == true",
      "entryEvidence": ["feature/src/.../HomepageActivity.kt:88"]
    }
  ],
  "migrationRootLayouts": ["feature/src/main/res/layout/fragment_homepage.xml"],
  "acceptanceStates": ["loading", "logged-out", "loaded-empty", "loaded-populated", "error"]
}
```

The ledger `scope` fields must exactly match this file. Never widen scope because a class or layout is shared.

## `baseline-assessment.json` schema 1

Record the strongest evidence available for every acceptance state; do not require runtime screenshots when they cannot reasonably be obtained.

```json
{
  "schemaVersion": 1,
  "captureAttempts": [
    {
      "kind": "legacy-runtime",
      "result": "unavailable",
      "reason": "Baseline build cannot authenticate against the current environment."
    }
  ],
  "states": [
    {
      "name": "loaded-populated",
      "level": "source",
      "appearanceEvidence": ["feature/src/main/res/layout/fragment_me.xml:20"],
      "dataEvidence": ["feature/src/main/.../MeViewModel.kt:42"],
      "behaviorEvidence": ["feature/src/main/.../MeFragment.kt:190"],
      "referenceArtifacts": [],
      "uncertainties": ["Exact runtime font fallback is not independently observable."]
    }
  ]
}
```

Allowed levels are `runtime`, `reference`, `source`, and `unresolved`. State names must exactly cover `scope-contract.acceptanceStates`. Source evidence uses repository-relative `path:line`; `referenceArtifacts` use paths relative to the evidence directory. An empty `uncertainties` array is valid only when the recorded evidence actually resolves the state.

## `legacy-inventory.json` schema 2

Generate the XML portion with `inventory_android_view.py`, then extend it with proven code paths. Stable `inventoryId` values are required for every view, binding variable, and binding expression. Add code-derived items to the ledger rather than pretending the XML scanner found them.

## `migration-slices.json` schema 1

Slices are ordered, user-visible vertical contracts rather than implementation layers.

```json
{
  "schemaVersion": 1,
  "slices": [
    {
      "id": "profile-header",
      "name": "Profile identity header",
      "order": 1,
      "representative": true,
      "ledgerItemIds": ["view:profile_name"],
      "behaviorContractIds": ["edit-profile-navigation"],
      "acceptanceStates": ["loaded-populated"],
      "status": "passed",
      "gates": {
        "realData": "pass",
        "appearance": "pass",
        "behavior": "pass",
        "preview": "pass",
        "compile": "pass",
        "coordinatorReview": "pass"
      },
      "reviewNotes": "Producer lineage and source-reconstructed appearance were reviewed against the frozen baseline."
    }
  ]
}
```

Exactly one first-risk-bearing slice must be marked `representative`. Every ledger item and behavior contract belongs to one slice. `uncertain` is not a passing status; bound it as an explicit acceptance item before continuing.

## `migration-ledger.json` schema 9

```json
{
  "schemaVersion": 9,
  "scope": {
    "baselineRevision": "same as scope contract",
    "allowedChangePrefixes": ["feature/src/"],
    "replacementBoundary": "same as scope contract",
    "targetEntries": [],
    "preservedSharedEntries": [],
    "migrationRootLayouts": [],
    "legacyLayouts": [],
    "productionComposeRoots": ["feature/src/main/.../MeScreen.kt"]
  },
  "items": [
    {
      "id": "view:profile_name",
      "kind": "state",
      "status": "mapped",
      "legacyEvidence": ["feature/src/main/res/layout/...xml:31"],
      "producerEvidence": ["feature/src/main/.../MeViewModel.kt:42"],
      "mappingEvidence": ["feature/src/main/.../MeRoute.kt:38"],
      "composeEvidence": ["feature/src/main/.../MeHeader.kt:54"],
      "verificationEvidence": ["feature/src/test/.../MeReducerTest.kt:90"],
      "notes": "Name content and missing-value behavior are preserved."
    }
  ],
  "behaviorContracts": [
    {
      "id": "edit-profile-navigation",
      "kind": "navigation",
      "legacyEvidence": ["feature/src/main/.../HomepageFrag.kt:210"],
      "composeEvidence": ["feature/src/main/.../MeScreen.kt:95"],
      "terminalEffectEvidence": ["feature/src/main/.../HomepageFrag.kt:240"],
      "verificationEvidence": ["feature/src/test/.../MeEventTest.kt:70"],
      "notes": "The same action reaches the existing navigator once."
    }
  ],
  "baselineAssessment": "baseline-assessment.json",
  "migrationSlices": "migration-slices.json",
  "previewCatalog": "preview-catalog.json",
  "previewSummary": "preview-summary.json",
  "performanceAudit": "performance-audit.json"
}
```

Allowed item kinds are `state`, `visibility`, `event`, `side-effect`, `navigation`, `list`, `binding-expression`, `binding-adapter`, `analytics`, `accessibility`, `lifecycle`, `resource`, and `layout`. Final statuses are `mapped` and `intentionally-removed`. Behavioral mappings require executable test evidence. Navigation, analytics, event, and side-effect contracts require terminal-effect evidence.

Every mapped state-like item also requires `producerEvidence` and `mappingEvidence`. Producer evidence must identify the real legacy source/update path, not a similarly named declaration. Mapping evidence must identify the production transformation/collection into Compose. The validator checks that these fields exist and resolve; the coordinator must judge their semantics.

## `preview-catalog.json` schema 3

```json
{
  "schemaVersion": 3,
  "productionScreenEvidence": ["feature/src/main/.../MeScreen.kt:30"],
  "fixtureFactoryEvidence": ["feature/src/testFixtures/.../MePreviewFixtures.kt:12"],
  "requiredCoverage": ["all production surfaces", "all state fields", "all reachable branches"],
  "notApplicable": [],
  "surfaces": [
    {
      "id": "me-screen",
      "kind": "screen",
      "productionEvidence": ["feature/src/main/.../MeScreen.kt:30"],
      "ledgerItemIds": ["view:profile_name"],
      "scenarioNames": ["loaded-short", "loaded-long-dark"]
    }
  ],
  "excludedComposables": [
    {
      "productionEvidence": "feature/src/main/.../MeScreen.kt:180",
      "rationale": "Private pass-through helper with no state, visual ownership, or interaction contract; directly covered by me-screen."
    }
  ],
  "stateFields": [
    {
      "path": "MeUiState.displayName",
      "type": "String",
      "productionEvidence": ["feature/src/main/.../MeUiState.kt:14"],
      "ledgerItemIds": ["view:profile_name"],
      "cases": [
        {"valueClass": "blank", "scenarioNames": ["loaded-blank"]},
        {"valueClass": "short", "scenarioNames": ["loaded-short"]},
        {"valueClass": "long", "scenarioNames": ["loaded-long-dark"]}
      ]
    }
  ],
  "scenarios": [
    {
      "name": "loaded-short",
      "acceptanceStateName": "loaded-populated",
      "previewEvidence": "feature/src/main/.../MePreviews.kt:28",
      "productionScreenCallEvidence": "feature/src/main/.../MePreviews.kt:32",
      "previewImage": "previews/loaded-short.png",
      "surfaceIds": ["me-screen"],
      "coverage": ["displayName:short", "media:loaded"]
    }
  ]
}
```

Every production Composable under `productionComposeRoots` must be represented by `surfaces` or `excludedComposables`. Every ledger item must be attached to a surface. Every state-like ledger item must also be attached to a `stateFields` entry. Every state field case and acceptance state must resolve to an existing scenario.

## `preview-summary.json`

```json
{
  "status": "passed",
  "sourceRevision": "final revision",
  "compiled": true,
  "renderedScenarioNames": ["loaded-short"],
  "coveredSurfaceIds": ["me-screen"],
  "coveredStateFieldPaths": ["MeUiState.displayName"],
  "usesSharedProductionComponents": true,
  "containsPreviewOnlyUi": false,
  "visualReview": "pass"
}
```

The three coverage arrays must exactly equal the catalog. A stale subset does not pass.

## `performance-audit.json` schema 1

```json
{
  "schemaVersion": 1,
  "sourceRevision": "final revision",
  "status": "pass",
  "surfaces": [
    {
      "surfaceId": "me-screen",
      "productionEvidence": ["feature/src/main/.../MeScreen.kt:30"],
      "stateReadOwnership": "Route collects once; rapidly changing scroll state is read in the owning section.",
      "recompositionBoundary": "Header, counters, and feed receive independent immutable inputs.",
      "stabilityContract": "Immutable UI models and persistent identity; no assertion-only stability annotations.",
      "collectionPolicy": "Stable item keys and content types; lazy rendering only for unbounded feed content.",
      "mediaPolicy": "Requests are size-bounded and preserve loading, failure, and missing-media states.",
      "effectAnimationPolicy": "Effects use semantic keys and stop when their visible owner leaves composition.",
      "expensiveWorkPolicy": "Sorting, mapping, decoding, and service access occur outside Compose phases.",
      "stressScenarioNames": ["loaded-long-dark"]
    }
  ],
  "measurementHandoff": [
    {
      "surfaceId": "me-screen",
      "transition": "Open Me tab and scroll populated content",
      "invariant": "No repeated decoding, unstable list identity, or whole-screen invalidation from local interaction."
    }
  ]
}
```

This is a source-level audit, not a benchmark result. Runtime measurement remains outside this skill.
