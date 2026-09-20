# Compose migration architecture

## Route, Screen, component

Use the smallest architecture that preserves the existing contract:

```kotlin
@Composable
fun FeatureRoute(
    viewModel: FeatureViewModel,
    navigator: FeatureNavigator,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    FeatureScreen(
        state = state,
        onEvent = { event ->
            when (event) {
                is FeatureEvent.Navigate -> navigator.open(event.destination)
                else -> viewModel.onEvent(event)
            }
        },
    )
}

@Composable
fun FeatureScreen(
    state: FeatureUiState,
    onEvent: (FeatureEvent) -> Unit,
    modifier: Modifier = Modifier,
) { /* production UI */ }
```

- Route/host owns lifecycle collection, dependency access, navigation, analytics, permissions, and other terminal effects.
- Screen is a plain function of immutable state and explicit events; it is the main page Preview and UI-test seam.
- Components own coherent visual and interaction contracts, accept a caller-placeable root `Modifier`, and expose events rather than business dependencies.

Do not create a wrapper per XML node. Extract a component when it has independent state/interaction, repeated semantics and structure, or a visually coherent contract worth reviewing directly.

## State and effects

- Each state value has one lowest responsible owner. Hoist only when a parent coordinates it or production persistence requires it.
- Prefer immutable UI state and stable collections. Do not annotate an unstable contract merely to affect skipping.
- Keep one source of truth; do not mirror ViewModel state into local `remember` state without an explicit synchronization contract.
- Use `rememberSaveable` only for UI state whose restoration semantics match the legacy behavior.
- Key `LaunchedEffect`, `DisposableEffect`, and `produceState` to the semantic inputs that should restart or dispose the work.
- Use `rememberUpdatedState` when a long-lived effect must invoke the latest callback without restarting.
- Use `derivedStateOf` only when it reduces expensive or high-frequency invalidation, not as decoration.

## Component APIs

- Put `modifier: Modifier = Modifier` on public visual components and apply it once to the root.
- The component owns invariant layout and semantics. Variable visual regions use typed slots.
- Prefer a sealed state/event model over many correlated Boolean flags.
- Avoid APIs that permit impossible combinations. Model mutually exclusive branches explicitly.
- Keep slot lambdas narrowly scoped and stable. Do not leak internal layout coordinates or mutable implementation objects.
- Reuse existing project components only after comparing semantics, supported states, dimensions, typography, and interaction behavior.

## DataBinding migration

Translate each binding expression deliberately:

- visibility expression -> explicit Compose branch with the same null/empty policy;
- text/resource formatting -> resource-backed formatting at the appropriate UI boundary;
- BindingAdapter -> component parameter, modifier, or host-side state transformation depending on ownership;
- two-way binding -> state plus explicit event, with the same debounce/validation/commit timing;
- listener expression -> typed event routed to the original terminal behavior;
- lifecycle owner/observable binding -> lifecycle-aware state collection at Route/host.

Do not carry a BindingAdapter into Compose as a generic helper if it mixes data policy, navigation, analytics, and rendering. Separate those responsibilities while keeping behavior identical.

## Preview construction

Every Preview calls a production Screen or production component. Fixtures belong in Preview/test code:

```kotlin
@Preview(name = "Loaded · long text · dark", uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun FeatureLoadedLongDarkPreview() {
    AppTheme {
        FeatureScreen(
            state = FeaturePreviewFixtures.loadedLongText,
            onEvent = {},
        )
    }
}
```

The no-op event is allowed only inside Preview/test code. Use a typed fixture factory or `PreviewParameterProvider` so component and screen scenarios share canonical data. A Preview wrapper may provide theme, size, direction, or font scale; it may not restyle or reconstruct production content.

## Performance design

Treat performance as an architectural property:

- Read fast-changing state close to where it is displayed.
- Split only at meaningful invalidation or ownership boundaries; excessive tiny composables are not automatically faster.
- Give lazy items stable domain identity and `contentType` where item families differ.
- Precompute sorting, grouping, decoding, and domain transformations outside composition.
- Bound image requests to display needs and preserve the legacy loading/error policy.
- Make frequently passed models immutable and callbacks stable by construction; verify before annotating stability.
- Ensure effect and animation lifetimes match visible ownership and do not restart because a wrapper object was recreated.
- Include stress fixtures that reveal clipping and structural cost, but leave runtime measurement to the coordinator.

## Scroll and retained View hosts

When a View host retains an app bar, pager, or nested scrolling parent, explicitly map drag, fling, restoration, insets, and tab switching. Test return-to-page and configuration restoration. Do not assume a `ComposeView` automatically reproduces `NestedScrollView` or `RecyclerView` behavior.
