# Custom Compose detekt predicates derived from spec

These 19 predicates implement a statically checkable subset of the linked spec requirements. `Composer` is the diagnostic namespace, not another implementation standard or scoring dimension. The provider is version 1.4.1 for detekt 2.0.0-alpha.6.

[Source and registration](../scripts/rules/custom-compose-rule/src/ComposerRules.kt), the [packaged JAR](../scripts/rules/custom-compose-rule/lib/composer-quality-rules.jar) and [configuration](../scripts/rules/detekt.yml) define actual execution. Symbol/type resolution and bounded traversal cannot prove requirements beyond their predicates. The [exception procedure](lint-rules.md#conflicts-and-exceptions) governs applicability without changing the source standard.

## Predicates and spec basis

### UntypedEventCallback

Basis: [spec: parameters should expose meaning](../../spec/references/components.md#parameters-should-expose-meaning).

Predicate: Resolved Composable callback input contains kotlin.Any, including nullable Any/type aliases.

Limit: Dynamic external APIs need an evidenced exception. This does not prove event semantics or extension compatibility.

### NondeterministicDefault

Basis: [spec: input identity and defaults](../../spec/references/components.md#input-identity-and-defaults).

Predicate: Listed resolved clock/UUID/global random calls evaluated directly in a Composable parameter default.

Limit: Default callback bodies are skipped. Seeded/local Random receivers are not treated as global randomness. Preview defaults belong to Preview rules. This is a policy signal, not proof that a caller observed a wrong value.

### NoOpActionDefault

Basis: [spec: semantic defaults and complete consumers](../../spec/references/components.md#semantic-defaults-and-complete-consumers).

Predicate: Non-private Composable onSubmit/onConfirm/onCommit/onDelete parameter has a resolved Unit callback type and empty literal default.

Limit: Frozen actionNames can be configured for a different profile. An intentionally optional action requires an exception, not a fabricated business failure. Nonempty bodies and forwarding callbacks are not proven correct by this rule.

### PositionalBooleanArguments

Basis: [spec: parameters should expose meaning](../../spec/references/components.md#parameters-should-expose-meaning).

Predicate: A resolved Composable call supplies at least two Boolean-typed arguments and at least one is positional. The resolved parameter types include nullable Boolean and type aliases; explicitly supplied defaulted parameters count. Report one finding per call, not per flag or declaration.

Limit: All-named calls, a single supplied Boolean, omitted defaults, non-Composable or unresolved calls are excluded. This checks call-site clarity, not declaration size or invalid state combinations. Separate calls need separate corrections; they remain separate findings. When the source declaration resolves, emit a composer-boolean-contract identity for that exact declaration (including overload identity). Scoring may group its occurrences under the documented style counting unit; unavailable source identity must not be guessed from names. No enum, wrapper or default parameter is required to satisfy it.

### RedundantSizeModifier

Basis: [spec: make dimension contracts executable](../../spec/references/layout.md#make-dimension-contracts-executable).

Predicate: Adjacent repeated sizing operations with identical positional literal dp arguments on the same recognized Modifier chain.

Limit: Named/reordered arguments, dynamic expressions, intervening modifiers and unrelated dp properties are excluded. No blanket ban on fixed sizes or custom offsets.

### BlockingCallInComposition

Basis: [spec: choose work placement](../../spec/references/performance.md#choose-work-placement).

Predicate: Listed blocking APIs in synchronous composition execution, including supported concrete helper paths up to depth three.

Limit: Ordinary event/effect callbacks and returned/stored lambdas are not executed composition work. Arbitrary HOF, virtual/recursive/deeper/external paths are outside proof. Direct Preview operations belong to Preview rules. A source finding does not measure frame time.

### NondeterministicPreview

Basis: [spec: use the real component](../../spec/references/previews.md#use-the-real-component).

Predicate: Listed nondeterministic calls in direct Preview/default fixture execution, including supported synchronous helper paths up to depth three.

Limit: Fixed-seed/local Random and deferred callbacks are excluded. Custom multipreview meta-annotations, virtual/recursive/deeper/external paths are outside proof. This source predicate does not certify rendering.

### PreviewEnvironmentDependency

Basis: [spec: use the real component](../../spec/references/previews.md#use-the-real-component).

Predicate: Recognized IO/environment/owner acquisition in direct Preview fixture execution, including supported helpers up to depth three.

Limit: Resources/theme context is not globally forbidden. Custom multipreview annotations and unknown source paths are outside proof; captured/returned callbacks are not execution. This is not general fixture-purity analysis.

### UnusedEventCallback

Basis: [spec: connect events to outcomes](../../spec/references/state.md#connect-events-to-outcomes).

Predicate: A resolved onX function parameter has no symbol references in the body or other parameter defaults.

Limit: References are symbol-based; shadowed names do not count. A reference does not prove invocation or reachability. Override/expect/actual signatures excluded; compatibility placeholders require evidence.

### UnusedUiParameter

Basis: [spec: semantic defaults and complete consumers](../../spec/references/components.md#semantic-defaults-and-complete-consumers).

Predicate: A non-function, non-Modifier UI input has no symbol references in the body or other parameter defaults; inherited contracts are excluded.

Limit: Function and Modifier parameters excluded (other rules own them); inherited signatures excluded. Referencing an input does not prove final propagation or semantic meaning.

### StateWriteInComposition

Basis: [spec: retained values and render time writes](../../spec/references/state.md#retained-values-and-render-time-writes).

Predicate: Recognized MutableState value/primitive/delegated writes in synchronous composition, subject to the narrow fresh-owned initialization exception below.

Limit: Ordinary variables/value properties are excluded. Unknown delegates, aliases, indirect write helpers and arbitrary lifetime semantics are outside proof. Fresh-state initialization has the specific exception below.

### CoroutineLaunchInComposition

Basis: [spec: connect events to outcomes](../../spec/references/state.md#connect-events-to-outcomes).

Predicate: Resolved launch/async invoked directly during composition; deferred event/effect lambdas are excluded.

Limit: Resolved kotlinx.coroutines launch/async directly in composable scopes; ordinary event/effect lambdas excluded. Helpers and resource cleanup are not traced.

### InvalidLayoutBounds

Basis: [spec: make dimension contracts executable](../../spec/references/layout.md#make-dimension-contracts-executable).

Predicate: Recognized literal negative padding or reversed min/max dp bounds.

Limit: Real Compose padding/absolutePadding and sizeIn/widthIn/heightIn/required variants, numeric literal AndroidX dp including negative/parenthesized values. Named range arguments are mapped. Dynamic expressions, resource sizes, custom dp and actual window geometry remain outside scope.

### ConstantLazyItemKey

Basis: [spec: lists layout and assets](../../spec/references/performance.md#lists-layout-and-assets).

Predicate: Constant literal/arithmetic/string key in recognized repeated lazy items, with named/positional argument resolution.

Limit: Variable/computed identities are not generally certified. A guaranteed singleton can justify an explicit exception; a constant-key finding does not establish an observed crash.

### UnkeyedRememberCapture

Basis: [spec: retained values and render time writes](../../spec/references/state.md#retained-values-and-render-time-writes).

Predicate: Resolved enclosing input/access-path capture in a remember calculation without sufficient exact/full keys; initial state-holder factories excluded.

Limit: State-holder initialization is excluded, preserving initial-only state. Spread key arrays, lambda-valued keys, indirect input dependencies and arbitrary derived-key equivalence are unknown. Fixed initial snapshots need an evidenced exception.

### DroppedEventCallback

Basis: [spec: connect events to outcomes](../../spec/references/state.md#connect-events-to-outcomes).

Predicate: Concrete non-Composable source helper forwarding up to depth three where every parameter-reference chain ends at an unused callback parameter.

Limit: Defaults that reference an earlier parameter count as use. Virtual/override/abstract/recursive/external/deeper paths are unknown. Aliases, transformed arguments and arbitrary business meaning are not proven. A deliberate compatibility/no-op sink needs evidence. Composable callee declarations remain owned by the existing unused-parameter rules.

### DroppedUiInput

Basis: [spec: semantic defaults and complete consumers](../../spec/references/components.md#semantic-defaults-and-complete-consumers).

Predicate: Equivalent bounded helper forwarding for non-function/non-Modifier data inputs, using resolved positional/named argument mapping.

Limit: Use the same traversal limits as DroppedEventCallback. A symbol read does not prove final business consumption. Repeated callers of one dropped leaf share a diagnostic identity; distinct leaf parameters remain distinct.

### WhitespaceLayoutSpacer

Basis: [spec: inline content and reserved space](../../spec/references/layout.md#inline-content-and-reserved-space).

Predicate: Resolved Material Text/BasicText containing only the supported literal spaces, tabs or nonbreaking spaces.

Limit: No dynamic strings, ordinary text, empty/newline text or same-named unrelated APIs. Deliberate text-metrics fixtures may be exempted with evidence. It does not prove all layout relationships.

### PreviewDuplicateBody

Basis: [spec: use the real component](../../spec/references/previews.md#use-the-real-component).

Predicate: Preview body token-identical to a same-file top-level production Composable body of at least 40 tokens; whitespace/comments ignored, string tokens preserved.

Limit: No cross-file/near-duplicate/semantic-equivalence claim. Short scaffolding excluded. Independent intentionally identical samples need evidence; no Preview is required solely to satisfy this detector.

## Bounded traversal and initialization

The single configuration fixes maxCallDepth=3. Virtual, recursive, unavailable or deeper paths remain unknown rather than proof of correctness. Direct-only checks do not inherit helper coverage from other rules. Static predicates cannot establish arbitrary cancellation/commit correctness, actual window retention or image workloads.

Inside a resolved remember calculation, an apply block on a direct constructor or known snapshot-state factory may initialize its own fresh state. Constructor members must themselves directly delegate to known fresh state factories. Writes through an existing receiver, an external qualified receiver, or a new wrapper borrowing caller state remain findings. This is not a blanket exception for every write inside remember.

Derive any future predicate from a specific spec requirement and supported project variations first. Document exact recognition, exclusions and unknown paths here; retain the implementation principle and its Bad/Good examples only at their spec topic. A new detection capability must not silently create an implementation requirement.
