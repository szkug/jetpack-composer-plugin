# Lint checks derived from spec

The implementation requirements are defined in [spec](../spec.md). This document maps them to bounded Android/Slack predicates; it does not introduce a second implementation standard. Use the source guidance at the linked topic when deciding intended behavior. The [adapter](incremental-lint.md) owns execution and changed-line filtering.

## Rule applicability

Use the actual project module/variant, resolved AndroidX registries, Slack 1.6.1 artifact, built-in options/severity (upstream defaults are metadata, not project opt-outs). The presence of a rule name or a registered registry is not proof it executed. Missing, disabled or suppressed coverage is distinct from clean execution. Analyzer warnings can approximate a broader spec requirement without proving its full semantics.

When a check is narrower than spec, report the remaining limit. When it is broader or incompatible with a supported spec/project case, preserve its raw finding/gate and resolve applicability through the exception procedure below. Do not rewrite spec, invent a business requirement or change source merely to fit a detector.

## Spec basis by check family

The L identifiers below remain frozen verification-group metadata used by existing profiles. They are not requirement IDs or directions back into spec.

| Group | Check family | Implementation basis |
| --- | --- | --- |
| L01 | Modifier APIs | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) |
| L02 | State creation and observation | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| L03 | Effect and producer behavior | [spec: connect events to outcomes](../spec/state.md#connect-events-to-outcomes) |
| L04 | Emission and slots | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| L05 | Dependencies and shared scope | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| L06 | Callable/Preview naming and signature shape | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| L07 | Observable configuration and resources | [spec: design for width and height separately](../spec/layout.md#design-for-width-and-height-separately) |
| L08 | Consumed host/layout/animation inputs | [spec: design for width and height separately](../spec/layout.md#design-for-width-and-height-separately) |
| L09 | Identity and bounded optimization hints | [spec: lists layout and assets](../spec/performance.md#lists-layout-and-assets) |
| L10 | Optional stability/design-system policy | [spec: fixed apis and supported variations](../spec/integration.md#fixed-apis-and-supported-variations) |

## Slack 1.6.1 predicates

All 24 published issue IDs are listed. Actual activation/severity comes from the frozen effective configuration; the two informational suggestions and three default-off policies are identified explicitly. The rule’s native outcome is preserved separately from semantic adjudication.

| Rule | Predicate and boundary | Basis |
| --- | --- | --- |
| ComposeModifierMissing | Missing caller Modifier on a qualifying public UI emitter; configured visibility/emitter exclusions apply. | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) |
| ComposeModifierWithoutDefault | Concrete Modifier parameter lacks the empty default; inherited/fixed signatures require applicability review. | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) |
| ComposeModifierReused | Caller Modifier is reused or dropped in recognized content-emitting branches. This does not prohibit independent immutable style-chain reuse. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ComposeModifierComposed | Use of composed modifier factories under Slack’s broad discouragement policy; broader than AndroidX’s unnecessary-use predicate. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ComposeMutableParameters | Configured mutable parameter types, including MutableState; intentionally shared editing can be a spec-compatible policy conflict (E1). | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| ComposeContentEmitterReturningValues | A qualifying Composable both emits UI and returns a value; configured emitter recognition bounds coverage. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ComposeMultipleContentEmitters | Multiple roots in a qualifying unscoped UI emitter; supported receiver scopes/configuration affect applicability. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| SlotReused | The same slot is called more than once on one execution path. One call in each mutually exclusive branch is allowed; movement identity is not established. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ComposeViewModelInjection | Recognized factory acquisition in a Composable body instead of a replaceable parameter. The detector does not infer architectural depth. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| ComposeViewModelForwarding | Whole ViewModel forwarding through recognized presentation calls; fixed host/owner contracts require scoped interpretation. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| ComposeCompositionLocalUsage | Local declaration outside the configured allowlist. A justified shared scope may conflict with this policy (E2). | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| ComposeCompositionLocalGetter | CompositionLocal creation through a getter; an allowed name does not resolve changing key identity. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| ComposeNamingUppercase | Unit UI-Composable naming; supported exclusions and fixed APIs bound applicability. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| ComposeNamingLowercase | Non-Unit value-Composable naming; separate from whether UI is emitted. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| ComposeParameterOrder | Required/optional Modifier/content ordering under this provider’s signature predicate. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| ComposePreviewNaming | Multipreview annotation suffix; this is not a universal Preview-function suffix requirement. | [spec: use the real component](../spec/previews.md#use-the-real-component) |
| ComposePreviewPublic | Ordinary Preview wrapper visibility; does not prove a render succeeded. | [spec: use the real component](../spec/previews.md#use-the-real-component) |
| ComposeItemKeyHashCode | Recognized hashCode item keys. Arbitrary alternate expressions are not proven unique or stable. | [spec: lists layout and assets](../spec/performance.md#lists-layout-and-assets) |
| ComposeRedundantComposable | Qualifying unnecessary Composable annotation; warning-level policy, not measured runtime cost. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| ComposeReadOnlyComposable | Informational missing-read-only suggestion for supported call/default patterns; no blanket annotation requirement. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| ComposeNonRestartableComposable | Informational qualifying-wrapper suggestion; no blanket annotation requirement or measured speedup. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| ComposeUnstableCollections | Collection stability check. Upstream default-disabled; our built-in full-registry policy enables it for implementation and scoring. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| ComposeUnstableReceiver | Opt-in unstable receiver policy; off by default. Observation correctness is a separate responsibility. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| ComposeM2Api | Opt-in Material generation restriction; off by default and cannot authorize an unrequested migration. | [spec: fixed apis and supported variations](../spec/integration.md#fixed-apis-and-supported-variations) |

## Official Compose registries

The official predicates depend on resolved AndroidX versions. This is a family map, not an exhaustive registry or proof that every named check exists in the evaluated context.

| Selected family | Basis | Limit |
| --- | --- | --- |
| ModifierParameter / factory receiver/return / SuspiciousModifierThen / UnnecessaryComposedModifier | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) | Factory/receiver and unnecessary-composed checks have different scopes from Slack’s blanket composed policy. |
| UnrememberedMutableState / RememberInComposition / MutableCollectionMutableState / StateFlowValueCalledInComposition | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) | State creation/observation patterns do not establish correct business ownership or all mutation paths. |
| CoroutineCreationDuringComposition / FlowOperatorInvokedInComposition / RememberReturnType / ProduceStateDoesNotAssignValue | [spec: connect events to outcomes](../spec/state.md#connect-events-to-outcomes) | Inspect supported indirect producers and actual effect ownership; a diagnostic is not proof of a runtime crash. |
| ComposableNaming / CompositionLocalNaming / ComposableLambdaParameterNaming / ComposableLambdaParameterPosition | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) | Resolved library version and fixed API constraints determine applicability. |
| NonObservableLocale / LocalContextConfigurationRead / LocalContextResourcesRead / LocalContextGetResourceValueCall / ConfigurationScreenWidthHeight | [spec: design for width and height separately](../spec/layout.md#design-for-width-and-height-separately) | Configuration observation checks do not prohibit an intentionally captured operation-specific snapshot. |
| UnusedBoxWithConstraintsScope / UnusedMaterial3ScaffoldPaddingParameter / animation target-state, key and modifier checks | [spec: design for width and height separately](../spec/layout.md#design-for-width-and-height-separately) | Trace real consumption without adding dummy reads; partial syntax recognition does not establish full layout correctness. |
| ConstantContentStateKeyInItemsCall / FrequentlyChangingValue / primitive state boxing checks | [spec: lists layout and assets](../spec/performance.md#lists-layout-and-assets) | Identity/update-pattern signals are not uniqueness or frame-time proofs; exact registry IDs and replacements are version-dependent. |

## Conflicts and exceptions

### E1 Shared editing and mutable parameters

Start from the [state ownership contract](../spec/state.md#ownership-authority-and-lifetime). Compare a mutable/state-parameter finding with the actual owner, permitted writers, reset identity and observation requirement. An accepted shared-editing API can conflict with an enabled convention; retain that conflict until its narrow policy disposition is evidenced. A local design explanation does not turn a failed native gate into a pass.

### E2 CompositionLocal and dependency visibility

Use [scoped dependencies](../spec/integration.md#scoped-dependencies) as the requirement. Check the actual provider/consumer scope and configured allowlist. A missing allowlist entry and an unstable Local key are different findings. An existing applicable project exception can be reused; adding an allowed name is a policy change, not authority granted by this document.

### E3 Optional stability and design-system policy

Use [annotation promises](../spec/performance.md#annotation-promises-and-representations) and [supported variations](../spec/integration.md#fixed-apis-and-supported-variations). Record actual compiler/design-system policy before applying opt-in diagnostics. A disabled policy is not an executed-clean result or a reason to alter the project. Informational optimization suggestions do not prove a performance defect.

### E4 Fixed APIs, legacy implementations and detector limits

Use [fixed APIs](../spec/integration.md#fixed-apis-and-supported-variations). Resolve signatures, call paths and configuration as needed to determine whether a detector’s premise holds. Broader discouraged-use policies and narrow unnecessary-use checks are not interchangeable. Avoid reclassifying a real source defect as an exception merely because it is old, or rewriting a valid API to satisfy a heuristic.

### Exception record and disposition

Record rule/provider/version, exact source scope, applicable spec/project behavior, detector mismatch or accepted policy variation, supporting evidence, project authority and revisit condition. Reuse applicable records. A suppression annotation, local preference or desire for a green report is not authority. Follow existing task/project authority for policy changes; otherwise leave the conflict unresolved.

Retain raw diagnostics and native/filtered gates beside adjudication. Distinguish confirmed violation, accepted exception, not applicable and unresolved conflict; missing coverage remains incomplete. Deduplication and deductions belong to score, with original evidence retained.

## Sources and version maintenance

- [Slack rules and options](https://slackhq.github.io/compose-lints/rules/) and [published 1.6.1 source artifact](https://repo.maven.apache.org/maven2/com/slack/lint/compose/compose-lint-checks/1.6.1/compose-lint-checks-1.6.1-sources.jar). Current web documentation can move ahead of this pinned mapping.
- AndroidX registries: [Runtime](https://github.com/androidx/androidx/blob/androidx-main/compose/runtime/runtime-lint/src/main/java/androidx/compose/runtime/lint/RuntimeIssueRegistry.kt), [UI](https://github.com/androidx/androidx/blob/androidx-main/compose/ui/ui-lint/src/main/java/androidx/compose/ui/lint/UiIssueRegistry.kt), [Foundation](https://github.com/androidx/androidx/blob/androidx-main/compose/foundation/foundation-lint/src/main/java/androidx/compose/foundation/lint/FoundationIssueRegistry.kt), [Animation](https://github.com/androidx/androidx/blob/androidx-main/compose/animation/animation-lint/src/main/java/androidx/compose/animation/lint/AnimationIssueRegistry.kt), [Material3](https://github.com/androidx/androidx/blob/androidx-main/compose/material3/material3-lint/src/main/java/androidx/compose/material3/lint/Material3IssueRegistry.kt). These main-branch references are discovery sources; use the project's resolved versions for decisions.

When the dependency versions change, check added/removed/renamed issues, defaults and options before updating this map. For example Slack's removed `ComposeRememberMissing` must not be enabled as a substitute for official `UnrememberedMutableState`; newer Foundation registries delegate formerly separate interaction-source/frequent-state checks to runtime checks. An unknown issue or checker-load problem is a tool/version question, not a source-code pass. This is a verification map covering all 24 Slack 1.6.1 issue IDs and selected official checks, not a claim of exhaustive AndroidX rule or runtime coverage.
