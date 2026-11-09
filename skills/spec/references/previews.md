# Preview sample code

For new or materially changed pages and independently meaningful visual components, provide or update representative Previews when the project supports them and the task does not exclude them. A trivial helper does not need its own wrapper. Follow existing tooling/source-set conventions. Preview sample declarations describe representative source inputs; rendering and device behavior require their own evidence.

## Use the real component

Use private, clearly named Preview functions that call production components with deterministic sample inputs. Reuse production theme/style definitions and representative host constraints. Do not copy layouts, colors or business state machines into sample code. Keep short fixtures local; use a fixture file or PreviewParameterProvider only when it removes meaningful repetition.

Supply plain data and safe callbacks rather than starting login, network, persistence or the full dependency graph. If a visual control requires its entire business owner, consider whether a plain rendering boundary fits its actual responsibility. Do not distort a justified stateful component just to shorten a sample. Put unavoidable SDK/platform stand-ins at a narrow boundary and make their limitations explicit. Do not add production isPreview branches to fabricate sample behavior.

Static appearance samples may use no-op callbacks. Interactive samples need minimal local state connected through real callbacks; they are not a replacement implementation of server behavior. Keep ordinary sample wrappers private. Name multipreview annotations with a Preview/Previews suffix; use the project’s function-naming convention without imposing an extra universal suffix on every sample function.

### Example: a sample calls the production control

The project supports a Preview for a profile card.

| Bad | Good |
| --- | --- |
| Copy its Row/Text layout into a sample, obtain its live ViewModel and generate the current user/time. | Call the real card under the production theme with fixed representative plain data and safe sample callbacks. |

Static samples may use no-op actions; interactive samples connect minimal local state. A sample declaration alone does not prove successful rendering.

## Cover meaningful UI differences

Choose supported states with materially different output: loading, failure/retry, empty/content, selection and disabled/saving where applicable. Do not invent unsupported states or generate every parameter combination. Component samples express local differences; assembled page samples express spacing, optional regions and available-space relationships. Keep both only when they serve distinct purposes.

Represent task-relevant differences: measurement/content variation, overflow policy, conditional anchors, decoration variants and changing action semantics. Keep variations reachable through real component inputs rather than hardcoding a desired sample layout.

Choose dimensions from the actual sizing contract. A fixed-width control uses that width; responsive content uses representative supported bounds. Add long-text, large-font, theme or direction samples where relevant. A populated happy-path sample does not represent required error/missing-artwork states. Revisit samples when shared style or supported states change.

Keep Dialog/Popup content samples distinct from the production window host. Preview declarations describe sample inputs; they do not establish successful rendering or runtime window/lifecycle behavior.

### Example: sample meaningful supported branches

The control supports normal, long-label and unavailable-image output in a constrained host.

| Bad | Good |
| --- | --- |
| Show only the short happy path, or enumerate every Boolean combination including invalid states. | Choose those supported cases through the component’s real inputs and actual host bounds. |

Add other states only when they change required output. Dialog content Preview does not establish window dimming, dismissal or page-state retention.
