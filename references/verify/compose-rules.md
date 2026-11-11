# Maintained Compose detekt checks derived from spec

The maintained provider is `io.nlopez.compose.rules:detekt:0.6.8` for detekt `2.0.0-alpha.6`. It supplies candidate predicates for the linked spec requirements; it is not an independent source of implementation requirements.

The [single YAML](../../scripts/verify/rules/detekt.yml) explicitly declares 43 rules: 38 enabled (34 warnings and four informational hints), five disabled. The [registry](compose-rules-registry.json) preserves exact IDs, severities and potential overlaps. Effective selected policy and execution evidence determine coverage; no automatic correction is enabled.

Five opt-in policies require applicable project choices: ComposableNestingDepth, CompositionLocalAllowlist, Material2, PreviewNaming and UnstableCollections. Apply [exception adjudication](lint-rules.md#conflicts-and-exceptions) where a predicate overreaches a valid spec/project case. Do not silently alter requirements, configuration or a native result.

## Verification groups

L15–L21 are existing profile metadata, not spec requirements.

| Group | Basis |
| --- | --- |
| L15 | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| L16 | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| L17 | [spec: retained values and render time writes](../spec/state.md#retained-values-and-render-time-writes) |
| L18 | [spec: connect events to outcomes](../spec/state.md#connect-events-to-outcomes) |
| L19 | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| L20 | [spec: use the real component](../spec/previews.md#use-the-real-component) |
| L21 | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |

## Predicate inventory

Each row describes the recognized source situation and its spec basis. A quiet result proves neither broader business correctness nor requirements outside the predicate.

### API and content

| Rule / policy | Recognized situation and boundary | Basis |
| --- | --- | --- |
| ComposableAnnotationNaming | A `@ComposableTargetMarker` annotation is named `VectorTarget`. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| ComposableNaming | Use lowercase for a Unit UI emitter or uppercase for a value producer. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| ComposableNestingDepth — off | When explicitly enabled, a Composable exceeds its declared nesting threshold. Off by default; a project-specific threshold is needed. | [spec: read the assembled code](../spec/components.md#read-the-assembled-code) |
| ComposableParamOrder | Place an optional styling argument ahead of Modifier. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| CompositionLocalAllowlist — off | With a selected allowlist, declare an unapproved Local. Off by default; do not assume an empty allowlist is an approved ban. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| CompositionLocalNaming | Name a composition-local key `AppTheme` rather than a `Local…` name. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| ConditionHoist | A qualifying empty-policy `Box { if (visible) Text(title) }` has only that conditional child. Ignores supported explicit layout arguments/other content; removing an empty container must not violate intended geometry. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ContentEmitterReturningValues | Emit UI and return a result from the same Composable. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ContentSlotReused | Use the same slot in two call sites, even `if (wide) { …content()… } else { …content()… }`. Counts multiple slot references even in exclusive branches, unlike Slack’s per-path predicate. Valid identity-preserving movement may require scoped adjudication. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ContentTrailingLambda | Put `content: @Composable () -> Unit` before later ordinary parameters. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |

### Defaults, effects and annotations

| Rule / policy | Recognized situation and boundary | Basis |
| --- | --- | --- |
| DefaultsVisibility | A public component uses a private matching `ComponentDefaults` object for caller-relevant defaults. Checks matching Defaults objects referenced by same-file component defaults/body; caller relevance and fixed visibility constraints still need interpretation. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| InvalidReadOnlyComposable | Mark an accessor read-only while it performs Compose operations that are not read-only. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| LambdaParameterEventTrailing | In a UI emitter with Modifier, leave required non-Composable `onClick` as the final parameter. Applies to required trailing non-composable lambdas in recognized UI emitters with Modifier; defaulted callbacks differ. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |
| LambdaParameterInRestartableEffect | Capture a changing callback parameter in a long-running effect without a matching key or current-value holder. Key/restart versus current-callback retention depends on the work contract; neither is universal. | [spec: connect events to outcomes](../spec/state.md#connect-events-to-outcomes) |
| Material2 — off | Under an enabled M3-only policy, use M2 components. Off by default; cannot authorize a migration. | [spec: fixed apis and supported variations](../spec/integration.md#fixed-apis-and-supported-variations) |
| MissingNonRestartableComposable — info | A qualifying wrapper lacks the optimization annotation. Information only; qualifying body/default patterns do not measure a speedup. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| MissingReadOnlyComposable — info | A qualifying accessor only performs permitted read-only composition reads but lacks the annotation. Information only; not every Composable can truthfully be read-only. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |

### Modifier

| Rule / policy | Recognized situation and boundary | Basis |
| --- | --- | --- |
| ModifierClickableOrder | Put `clickable` before a later shape modifier such as `clip(shape)` in the checked chain. Checks recognized shape/click ordering; not a universal modifier sort or runtime geometry proof. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ModifierComposed | Use a discouraged composed modifier factory. Broader discouragement policy; retain necessary lifecycle/API compatibility evidence. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ModifierMissing | A qualifying UI emitter offers no caller Modifier. | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) |
| ModifierNaming | Name the primary caller Modifier `styleModifier`. | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) |
| ModifierNotUsedAtRoot | Accept Modifier but attach it only to an inner Text beneath the component root. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ModifierReused | Apply the caller’s modifier to multiple sibling/descendant nodes. Caller allocation differs from an independent immutable style chain. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ModifierShouldBeForwardedToEveryBranch | One content-emitting branch forwards Modifier and the alternate branch drops it. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| ModifierWithoutDefault | Declare a concrete caller modifier without a default. | [spec: modifier parameter defaults](../spec/components.md#modifier-parameter-defaults) |

### State and events

| Rule / policy | Recognized situation and boundary | Basis |
| --- | --- | --- |
| MultipleEmitters | An unscoped reusable UI function emits multiple unrelated roots. | [spec: content and modifier composition](../spec/components.md#content-and-modifier-composition) |
| MutableParams | Accept a configured inherently mutable collection/object at a reusable rendering boundary. A spec-compatible shared owner may need E1 policy disposition. | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| MutableStateAutoboxing — info | Create generic primitive state such as `mutableStateOf(0)` where the primitive API is available. Information only; actual primitive API availability and use sites matter. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| MutableStateParam | Accept `MutableState<String>` just to read text and report edits. A spec-compatible shared editing owner may need E1 policy disposition. | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| ParameterNaming | Use a callback name such as `onClicked`. | [spec: naming and callable shape](../spec/components.md#naming-and-callable-shape) |

### Preview and retained values

| Rule / policy | Recognized situation and boundary | Basis |
| --- | --- | --- |
| PreviewAnnotationNaming | Name a multipreview annotation `ScreenSizes`. | [spec: use the real component](../spec/previews.md#use-the-real-component) |
| PreviewNaming — off | With a selected naming policy, a Preview function lacks its configured prefix/suffix. Off by default; configured naming policy is not a universal function suffix. | [spec: use the real component](../spec/previews.md#use-the-real-component) |
| PreviewPublic | An ordinary Preview wrapper is public. | [spec: use the real component](../spec/previews.md#use-the-real-component) |
| RememberContentMissing | Recreate `movableContentOf { … }` on each composition. Retention alone does not refresh frozen captures. | [spec: retained values and render time writes](../spec/state.md#retained-values-and-render-time-writes) |
| RememberMissing | Construct composition-owned state without retention. Retention alone does not establish the correct reset identity. | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| StaleRememberUpdatedStateInRemember | Read `current.value` eagerly inside `remember { current.value }` after obtaining it from rememberUpdatedState. Eager snapshot capture differs from reading the current value on invocation. | [spec: retained values and render time writes](../spec/state.md#retained-values-and-render-time-writes) |

### Observation and dependencies

| Rule / policy | Recognized situation and boundary | Basis |
| --- | --- | --- |
| StateParam | Accept `State<T>` at an ordinary value-rendering boundary. The textual state-parameter convention can reject a valid deferred-observation boundary; it does not establish full type/alias equivalence. | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| UnnecessaryComposable — info | Annotate a helper that uses no Compose capability. Information only; inspect body, defaults and required API. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| UnnecessaryLaunchedEffect | On a resolved runtime supporting keyed SideEffect, use a qualifying LaunchedEffect body that only calls non-suspending operations. Requires resolved runtime support for keyed SideEffect and a qualifying non-suspending body. Preserve required timing/lifetime. | [spec: choose the effect for the work](../spec/state.md#choose-the-effect-for-the-work) |
| UnstableCollections — off | Under an opted-in policy, accept a general collection with no guaranteed immutable contract. Off by default; compiler/project policy affects significance. | [spec: annotation promises and representations](../spec/performance.md#annotation-promises-and-representations) |
| VarsWithoutStateBacking | Declare a local `var expanded = false` in Composable scope and expect observable retained UI state. Composition-local state expectations differ from ordinary event-local computation. | [spec: ownership authority and lifetime](../spec/state.md#ownership-authority-and-lifetime) |
| ViewModelForwarding | Pass a whole ViewModel through UI presentation children. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |
| ViewModelInjection | Acquire a recognized ViewModel factory in the function body rather than a replaceable parameter. Recognized factory configuration bounds coverage; architectural depth is not inferred. | [spec: scoped dependencies](../spec/integration.md#scoped-dependencies) |

Sources: [maintained project](https://github.com/mrmans0n/compose-rules), [0.6.8 release matrix](https://github.com/mrmans0n/compose-rules/releases/tag/v0.6.8), [published POM](https://repo.maven.apache.org/maven2/io/nlopez/compose/rules/detekt/0.6.8/detekt-0.6.8.pom), [versioned source](https://github.com/mrmans0n/compose-rules/tree/v0.6.8/rules/detekt), [usage](https://mrmans0n.github.io/compose-rules/detekt/).
