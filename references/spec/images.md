# Images: actual controls, parameters and behavior

Use this reference when implementing or reviewing images, configured backgrounds or image-backed actions. Select the existing project control before prescribing loading behavior. Apply only task-required states; a permitted offline adapter or excluded network/failure path does not acquire new acceptance requirements.

## Inspect the API, then write the caller

Find the real component/modifier declaration, its request implementation and an analogous production caller. Establish accepted models, empty-model behavior, placeholder and failure parameters, scaling/cropping, accessibility, and any URL transformation/degradation policy the task depends on. A name or a preview rendering is insufficient evidence of network behavior.

Distinguish an image composable from a background painter/modifier and an interactive control. They may use different request engines and expose different parameters. Do not invent an error-resource parameter, retry action or loading callback because another library offers one. When the required behavior is unavailable, use another suitable existing project API or explain the concrete gap before adding a narrowly scoped adapter. Do not replace a project loader with a different library merely to get familiar parameters.

At the actual caller, express: **selected control -> model -> applicable placeholder/failure parameters -> size/clip/scale -> semantics/action**. A short source walkthrough is enough; no separate inventory or wrapper is required. Inspect only relevant capabilities and states, not every image facility in the repository.

### Example: an API name does not establish its fallback behavior

The active project has an image wrapper used by production callers.

| Bad | Good |
| --- | --- |
| Invent `placeholder`/`imageModel` arguments or switch wrappers without checking their supported models and transformations. | Read the declaration and current callers; configure only the actual supported fallback/model path. |

The same library name can hide project-specific transforms or cache policy. Do not copy its API into this public specification.

## Choose behavior by responsibility

| Responsibility | Implementation decision at the actual caller |
| --- | --- |
| Avatar or identity thumbnail | Reuse the project's business default resource. Where supported and required, pass it explicitly for empty/loading and failure; retain allocated size and clipping across states. Choose Crop/Fit from the intended artwork. Give the image a meaningful description or keep it silent when adjacent semantics already convey identity. |
| Configured panel/background | Separate absent configuration from an unresolved, loading or failed configured model. Determine whether local color/artwork stays under the image or is replaced on success. Use the selected API's supported fallback mechanism; do not assume a nonblank string proves successful loading. Preserve transparent regions and avoid duplicate frames/borders when configured artwork already owns them. |
| Image carrying content, such as instructions or a poster | Preserve the required content and aspect/reading policy. Decide empty/error presentation and retry from product requirements and the available loader. An avatar default cannot stand in for missing instructional content; a retry button requires a real supported retry action. |
| Image-backed action | Keep purpose, click/disabled/pending behavior and hit bounds at the action boundary. Loading or replacing artwork must not silently remove the action contract. A static bundled drawable need not acquire an asynchronous loading state. |
| Decorative image | Use silent semantics. Omission on failure can be valid when the decoration is optional; do not apply an avatar placeholder or error message universally. |

Defaults and error assets can differ. Resource choice belongs to the project's actual component/product contract, not a universal rule that every image must show the same placeholder.

### Example: missing artwork has role-specific behavior

A content image, an illustrated action and a decoration all fail to load.

| Bad | Good |
| --- | --- |
| Show the same avatar silhouette for all three, or remove the action and its label when its art fails. | Use content-specific unavailable/retry UI when required; retain the action’s label, semantics and intended enabled state; omit optional decoration while preserving underlying geometry/color. |

Avatar identity placeholders and persistent background colors are illustrated below. Failure does not itself authorize retry or change a business action’s enabled state.

## Make implementation concrete in the target project

Keep project component names, resource identifiers, sizes and loader-specific parameter names in the target project's implementation, not in this public specification. Discover them from that project's actual declarations and analogous callers. Do not introduce a fictional universal image API or a new dependency to make an example fit.

### Example: an avatar needs an identity placeholder

**Scenario:** the product requires the existing default avatar for empty/loading/failed models. The chosen avatar component or loader has been inspected for those behaviors.

| Bad | Good |
| --- | --- |
| Pass only the remote model and assume failure automatically selects the business avatar; or invent an error parameter copied from another loader. | Reuse the avatar component that already owns this policy. Otherwise supply the actual loader's supported placeholder/failure inputs with the existing default resource, retaining the same bounds and clipping. |

**Why / boundary:** the required resource reaches a real rendering path. Empty/loading and failure may need different parameters. If the chosen API cannot express the required state, identify that gap and use a suitable existing API or scoped adapter; no fictional universal signature is prescribed here.

### Example: a background needs a persistent base color

**Scenario:** a panel must retain its existing base color during loading/failure and through transparent pixels after success. The configured image is an overlay on that base.

| Bad | Good |
| --- | --- |
| Draw the base color only when the model string is empty; remove it as soon as a URL exists. | Keep the base color on the container and layer the selected background API above it, preserving the actual crop/alpha behavior. |
| Use the default avatar as a universal image-error fallback. | Keep the panel's required base treatment; use failure-specific artwork only if the product requires it and the API supports it. |

**Why / boundary:** configured does not mean loaded, and transparent success still exposes the base. If successful artwork must replace the base entirely, follow that different layering contract. Do not assume a background modifier exposes an image component's failure callbacks.
