# Native detekt checks derived from spec

The implementation basis is [readable components](../../spec/references/components.md#read-the-assembled-code), appropriate API boundaries and explicit failure behavior. The [selected YAML](../scripts/rules/detekt.yml) operationalizes a bounded subset using eight native detekt 2.0.0-alpha.6 checks. Numeric thresholds are frozen verification policy, not universal implementation quotas or proof of runtime failure.

## Predicate inventory

| Rule | Configured predicate / limit | Basis |
| --- | --- | --- |
| CyclomaticComplexMethod | allowedComplexity: 15; ignoreNestingFunctions: true | [spec: read the assembled code](../../spec/references/components.md#read-the-assembled-code) |
| NestedBlockDepth | allowedDepth: 5 | [spec: read the assembled code](../../spec/references/components.md#read-the-assembled-code) |
| LongMethod | allowedLines: 80 | [spec: read the assembled code](../../spec/references/components.md#read-the-assembled-code) |
| LongParameterList | allowedFunctionParameters: 8; ignoreDefaultParameters: true | [spec: parameters should expose meaning](../../spec/references/components.md#parameters-should-expose-meaning) |
| TooManyFunctions | file: 15; class/interface/object/enum: 11 each; private/internal/deprecated/overridden functions count; declared Preview/multipreview exclusions | [spec: read the assembled code](../../spec/references/components.md#read-the-assembled-code) |
| FunctionNaming | Composable annotation excluded; Compose provider handles its separate naming shape | [spec: naming and callable shape](../../spec/references/components.md#naming-and-callable-shape) |
| UnusedPrivateFunction | Declared Preview/multipreview exclusions; reflection/generated entry points require interpretation | [spec: failure handling and retained entry points](../../spec/references/integration.md#failure-handling-and-retained-entry-points) |
| EmptyCatchBlock | Native ignored-exception-name/comment options affect applicability | [spec: failure handling and retained entry points](../../spec/references/integration.md#failure-handling-and-retained-entry-points) |

Use the engine’s actual counting semantics and effective configuration; all function-container limits are explicit in the selected YAML. A short illustrative snippet does not demonstrate crossing a line/complexity threshold. Successful syntax/type analysis does not establish arbitrary business reachability.

## Interpretation before scoring

Complexity and function counts are maintainability policy findings, not proof of broken behavior. Inspect the actual reported container: a class count is not a file count. Keep limits fixed across candidates. A valid fixed API or cohesive DSL exception needs specific source/project evidence and the same applicability procedure for every candidate; neither a low score nor an intention to raise it justifies an exception.

## Correspondence

L11 (control-flow complexity), L12 (size/API burden), L13 (naming/private references) and L14 (exception handling) are frozen verification-group metadata. Their linked requirements are in spec, not a second tool-specific implementation contract.

## Compatibility and exceptions

Apply the [diagnostic exception procedure](lint-rules.md#conflicts-and-exceptions). A cohesive declarative DSL, fixed API or framework entry may be a valid source design with a policy diagnostic. Preserve raw results and evidence; do not hide unchanged complexity in forwarding helpers or add dummy references to manufacture a pass. Do not blanket-exclude all Composables.

The [maintained provider](compose-rules.md) and [custom provider](custom-compose-rules.md) are loaded alongside these native rules in the same full-type-analysis invocation. Slack IDs are not valid detekt YAML rule names. Exact loaded artifacts/configuration and executed coverage are required before interpreting any zero-finding result.
