# Realize the contract at the final consumer

Use this loop for new screens and material visual changes. It is a working method, not a requirement to produce a separate checklist document or use a particular tool. Respect task exclusions.

## Choose representative paths

Before extracting components, identify the required visual regions, relationships, resource sources and materially different states from the task. For each changed decision, select inputs that exercise both outcomes: an action changing meaning, optional content present/absent, configured/default artwork, or the open/dismiss state branches of an overlay over a retained page. Include a supported layout boundary where content competes for space. Do not invent unsupported states or test a Cartesian product of parameters.

Resolve resource identifiers using the actual resource owner and installed/build configuration. A source namespace, application ID and a resource package are not interchangeable. Prefer project-supported typed references for bundled assets; when dynamic lookup is required, trace a representative known-valid identifier through the resolver to the model. Do not let placeholder handling conceal a broken configured-resource path. Use [image contracts](spec/images.md) for role-specific loading/failure behavior.

## Implement the assembled relationships

Connect input -> state owner -> actual call arguments -> rendering and input consumers. When action meaning changes, inspect the selected label, role/style, enabled state and handler together. Do not assume a required enum parameter guarantees the caller passes the correct value. Shared style/resource changes must reach every in-scope rendering branch, including custom artwork.

Allocate space from the visual relationship: content flow, a reserved leading/trailing region, or intentional overlap. Do not repair one reference image with whitespace, unrelated sibling offsets, disappearing content or a second fixture-only layout. Match typography and decoration as well as outer geometry; inspect asset contributions before adding drawing.

For transient overlays, keep presentation state separate from underlying page identity. Retain the base content and its scroll, selection and draft state unless the product requires navigation/replacement. Do not remove the base or set its alpha to zero just to create a clean backdrop. Visibility, composition lifetime and input blocking are separate decisions. Use [host integration](spec/integration.md) for window policy and dismissal ownership.


## Review the assembled source

Trace the selected branches through the final callers. Check label, role/style, enabled/pending state and handler together; confirm custom artwork consumes the same intended policy. Correct source omissions and recheck affected callers. Static scans belong to [verify](verify.md); compilation and rendered/runtime acceptance follow the task’s separately authorized workflow. Source review does not establish any of those execution results.
