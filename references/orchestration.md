# Migration orchestration and correction gates

Use this reference to keep implementation, evidence, and acceptance from becoming one self-confirming loop.

## Publication barriers

### Baseline barrier

Publish one complete baseline assessment only after scope, acceptance states, reachable appearance sources, data producers, behavior paths, and failed runtime/reference capture attempts have been examined. Do not publish a provisional assessment while another analysis is pending.

The assessment states:

- the exact runtime entry and preserved shared consumers;
- evidence level for each acceptance state;
- which appearance properties are directly known versus reconstructed;
- which data states are reproducible;
- which uncertainties can change implementation decisions.

If uncertainty affects the page's dominant style, core data semantics, or interaction outcome, pause that portion for user direction. Do not require a legacy screenshot when source reconstruction is sufficient and uncertainty is localized.

### Slice-plan barrier

The coordinator owns one ordered plan. Each slice must be independently reviewable and must close appearance, real data, behavior, Preview, and tests together. A layer-first plan such as "build all composables, then wire data" fails this barrier.

The first slice should test the riskiest reusable assumption: dominant card/header styling, list architecture, retained View interop, or state ownership. Avoid choosing a trivial icon merely to pass the checkpoint.

### Slice barrier

A slice may pass only when:

- every displayed value reaches production from its proven producer;
- loading, empty, error, refresh, and restoration policies relevant to the slice match;
- visual decisions trace to the strongest baseline evidence;
- events reach terminal effects;
- production components are used by Preview and tests;
- compile/render/focused tests pass;
- the coordinator reviews the result independently of implementation notes.

`uncertain` is not `passed`. It may proceed only when the uncertainty is explicitly bounded and either user-approved or intentionally deferred as an acceptance item.

### Final publication barrier

Before final output, the coordinator reviews the actual merged source and artifacts, not only worker summaries or validator output. Check both directions:

1. Every legacy contract has a disposition.
2. Every new state field, effect, resource decision, and navigation path has legacy or approved-requirement authority.
3. Every slice has one visible result and no known mismatch hidden by a later slice.
4. The chosen claim level is supported for every acceptance state.

## Baseline fallback semantics

Evidence levels are ordered, not interchangeable:

| Level | Evidence | Permitted conclusion |
|---|---|---|
| `runtime` | Legacy runtime captured with documented device/account/data context | Runtime comparison for that state |
| `reference` | Archived screenshot, recording, approved design/product image, or independent golden | Reference comparison for visible properties |
| `source` | Reachable XML, resources, adapters, mutations, and call/data paths | Source reconstruction only |
| `unresolved` | Insufficient or conflicting evidence | No parity claim; user decision or named acceptance item |

Record failed attempts only when they explain why the workflow moved down the chain. Do not spend disproportionate time resurrecting an unavailable legacy environment if source evidence can support the requested decision.

## Data-lineage review

For each rendered state field record:

```text
legacy producer -> transformations -> lifecycle/update trigger -> legacy consumer
                -> Compose mapping -> Compose consumer
```

Compare null/default handling, ordering, filtering, paging identity, cache freshness, loading/error policy, and update timing. A source line that merely declares a similarly named property is not producer evidence.

When a legacy Adapter owns rendering policy, either retain it through interop or explicitly migrate its item model, branching, resources, and callbacks. Do not replace it with a smaller demo list because the Screen API is easier to preview.

## Corrective loop

When a review fails:

1. classify the mismatch by owning gate;
2. invalidate the failed slice and dependent decisions;
3. correct the earliest wrong artifact or assumption;
4. rerun the failed gate and downstream checks;
5. update evidence and claim level.

Do not normalize repeated late discoveries. If two independent data or style contracts are first discovered during final review, stop finalization and repeat the baseline/data completeness pass.
