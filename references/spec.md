# Compose specification

Specify the behavior and ownership that the implementation must preserve. Requirements come from the user's task and the actual project contracts; examples and preferred APIs do not create extra product requirements. A small edit needs only its relevant standards.

## Common design principles

Apply these before selecting a component pattern:

| Principle | Implementation decision |
| --- | --- |
| Concise | Introduce only concepts, parameters and layers needed by the current behavior. Extract repeated policy or a coherent responsibility; keep a direct expression local when a wrapper adds no meaning. A little duplication can be clearer than a generalization with unrelated options. |
| Human-readable | Use the project's vocabulary and names that expose intent. Make inputs, actions and state owners understandable at their callers. Follow local formatting; expand expressions when compression obscures branches or writes. Comments explain reasons, constraints and non-obvious behavior rather than restating syntax. |
| Direct | Let readers follow input -> state/operation owner -> output. Each adapter or forwarding layer should serve a real boundary, coordination or lifecycle need. Prefer a direct callback for a local event unless an existing project contract requires dispatch; do not shorten a chain by hiding dependencies. |
| Consistent with project history | Follow the active module's established naming, organization, state/event patterns and shared facilities. Use comparable production callers and explicit migration direction to interpret mixed historical styles; investigate relevant history only when the reason matters. Preserve necessary compatibility without copying known defects or retired patterns. |

These principles do not impose line/file/layer quotas or permit bypassing correctness or explicit project requirements. Resolve conflicts using [project integration](spec/integration.md#follow-the-active-project-conventions) and its fixed-contract guidance. Keep departures small and explain their concrete reason; do not restyle unrelated code to express personal preference.

## Select the relevant standards

- [Components](spec/components.md): responsibility, typed inputs/events, meaningful defaults, shared style ownership, outer size and Modifier contracts.
- [Layout](spec/layout.md): flow/overlap/anchors, parent constraints, width and height allocation, content priority and overflow.
- [State](spec/state.md): authoritative facts, drafts, derived values, write authority, initialization, reset identity, effects and asynchronous operations.
- [Integration](spec/integration.md): active project conventions and history, existing components/resources, host/window ownership, View interoperability and retirement of replaced behavior.
- [Images](spec/images.md): role-specific loading/fallback, accepted models, geometry and semantics through the selected project's real API.
- [Performance](spec/performance.md): work placement, observation, caching/invalidation, collection identity and resource lifetime.
- [Previews](spec/previews.md): representative production-calling sample code when supported; sample delivery does not request rendering.

Examples sit beside the relevant implementation principle. Bad/Good pairs apply to the same stated scenario; illustrative names and dimensions are not project APIs or universal defaults. Use the project’s actual declarations and resource policy.

For a multi-region screen start with Components and Layout. Add State for interactions, Integration for a host/Dialog/Popup/adapter, and Images for changed image responsibilities. Do not read every reference for a local change.


## Apply the contracts

Inspect actual definitions and production callers before selecting an abstraction. Keep requirement -> owner -> caller -> final consumer connected. More classes, fewer lines, universal statelessness or one preferred API do not establish correctness. Preserve deliberate variations and fixed API contracts; explain concrete exceptions rather than making superficial changes to satisfy a convention.

These standards define intended implementation behavior. Requirements come from the task and applicable project contracts; the available checking tools do not define or expand them.
