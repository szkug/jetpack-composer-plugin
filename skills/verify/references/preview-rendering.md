# Render and inspect production Previews

This is an optional capability used only when Preview rendering/export or Preview-based verification is explicitly requested. It is not part of default implementation self-check. A claimed Preview-rendering verification requires actual rendered images of the selected production `@Preview` functions. An annotation, compilation, source walkthrough or device screenshot is not a Preview render. A missing renderer is an incomplete tool capability, not permission to call requested rendering complete. Repair the setup or report the exact blocker; do not silently fall back to a device. Device acceptance is a separate stage with its own authorization and device restrictions.

## Discover a usable backend

Prefer an existing project renderer that builds and exports the actual production Previews without GUI automation. The bundled [exporter](../scripts/render_preview.py) defaults to the official Android CLI **headless** backend, `android preview render`. This compiles the selected target and renders offscreen without Android Studio, an emulator or a device.

1. Use Python 3.9+ with Pillow. Inspect `android --version` and `android preview render --help`; require the actual `--fqn` and `--format` options. A successful exit from an unknown command is not capability evidence. Older CLI runtimes expose only `studio render-compose-preview`. Update the full official CLI within task permissions; downloading only its launcher can still execute an older cached runtime. Verify capabilities again. Do not silently switch to GUI clicks or ask the user to keep the desktop unlocked.
2. Identify the project build target and JVM Preview method with `android preview list` using an explicit build reference, for example `gradle:///absolute/project?:app`. Do not infer the JVM facade solely from the filename when `@file:JvmName`, classes or multi-previews can change it. The explicit build system avoids ambiguous workspace detection. Keep project build/Gradle output handling rules in force; CLI rendering builds its target internally.
3. Export into a new attempt directory. Select the actual module or supply `--reference` for a discovered explicit build reference. Use `--build-arg=VALUE` for build-system options and `--sdk` when discovery is insufficient. The first run may download official build/render packs; network/setup failure is distinct from a Preview failure. The exporter does not start the optional persistent rendering daemon.

```sh
python3 /path/to/skills/verify/scripts/render_preview.py \
  --project /absolute/project \
  --file app/src/main/java/example/Screen.kt \
  --fqn example.ScreenKt.ScreenPreview --module :app \
  --component-tree --output /absolute/evidence/screen-attempt-1
```

Paths and names above are examples. `--variant` only records a caller declaration; it does not select or verify a variant. Select the intended build target using capabilities of the installed CLI/build system and record unresolved variant provenance. The exporter requires structured success, at least one matching method result, no per-preview error, fresh fully decodable PNGs and unchanged source/build inputs during the call. It preserves every returned Preview variant in `images`; a singular `image` is supplied only when one was returned. An image hash alone does not establish source freshness or visual correctness.

## Explicit legacy Studio backend

Use `--backend studio --composable ScreenPreview` only when intentionally choosing the older integration. It requires the exact project to be READY in Android Studio and uses a per-user OS lock because Studio is shared. Confirm the intended active variant separately. Compile changed sources and production dependencies through the prescribed project build workflow before export; after a class-loading error, a completed command-line rebuild and one new export attempt may suffice. A READY status alone does not prove up-to-date classes.

If the build succeeds but rendering remains stale or fails, preserve the error and use the headless backend when available. Do not make clicking Build & Refresh, unlocking the computer, Run, or Apply Changes an automatic recovery step. A specific user-authorized IDE investigation is separate from unattended export. An old Studio CLI can return exit code 0 while printing `Error: ...`; the exporter treats that as failure.

For either backend, inspect the exported PNG, not an IDE screenshot. Preserve command/version, input snapshots, images, logs and any timeout output. Do not retry an unchanged failure indefinitely. Other existing renderers may be used with the same evidence requirements; do not force an AGP upgrade, add forbidden screenshot tests, or alter frozen inputs merely to obtain an image.

## Inspect the exported pixels

Open the exported PNG with the available image viewer. Check the actual production elements, layout relationships, sizes, typography, decoration and semantic visual states against the agreed target. Compare using matching data, host bounds, density, font scale, theme and direction. Missing assets, a blank image, unexpected loading or a placeholder hiding a broken success path fail the relevant check even if rendering succeeded.

Choose representative materially different states and a supported boundary from [Preview delivery](../../spec/references/previews.md). For multiple annotations/parameterized Previews, confirm which variant the backend exported; render explicitly named wrappers for required variants when selection is ambiguous. Do not infer coverage of all variants from one image.

Return confirmed in-scope differences to impl. After an authorized repair, rebuild affected dependencies and render again into a fresh directory; keep frozen review candidates unchanged. Inspect the new image; preserve before/after evidence where it explains the repair. Report source compilation, rendering and visual comparison separately, linking the actual images and any unresolved mismatches.

Preview uses a tooling context: successful resource resolution there does not prove that a production application ID/resource package lookup is correct. Trace the actual runtime resource owner separately. Preview callbacks and static images do not prove runtime interaction, SDK behavior, IME, true window dimming or lifecycle. For Dialog/Popup, render the real content composable under representative constraints; retain the real window host in production. Keep window-dependent acceptance separate. Never add a production `isPreview` branch or duplicate the target layout to manufacture a passing sample.
