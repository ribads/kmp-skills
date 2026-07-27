---
name: create-screen
description: Use when scaffolding a new screen in a Synapse-based KMP app. Generates the 7-file IRSE-MVI screen package (Contract, Interactor, Reducer, Mapper, ViewModel, Screen, di/UiComponent) via a script.
user-invocable: true
---

# create-screen — Synapse IRSE-MVI Screen Scaffold

Generates the canonical 7-file screen package used in Synapse apps. Every screen in a Synapse project follows the same IRSE-MVI structure — this skill eliminates the boilerplate.

## What it creates

```
<package>/
├── {Name}Contract.kt         sealed Intent, sealed Result, sealed Effect, @Immutable ViewState, Mapper interface
├── {Name}Interactor.kt       Interactor<Intent, Result, State> — merge() + filterIsInstance routing, StateFlow-aware
├── {Name}Reducer.kt          Reducer<ViewState, Result, Effect> — pure state machine returning Reduction
├── {Name}Mapper.kt           Contract.Mapper impl — intent/domain → Result conversion
├── {Name}ViewModel.kt        LifecycleViewModel boilerplate (4 type params)
├── {Name}Screen.kt           @Composable — Scaffold, OnFirstComposition, CollectAsEffect for navigation
└── di/{Name}UiComponent.kt   @Component kotlin-inject with @Provides bindings
```

The scaffold ships with the baseline intents every Synapse screen needs:
`LoadInitialData`, `Navigation.Back`, an `Effect.Navigate(NavigationCommand)` effect, and the `OnFirstComposition` + `effects.CollectAsEffect` wiring in the composable.

## Script

`scripts/create_screen.py` — Python 3, stdlib only.

```
python3 .claude/skills/create-screen/scripts/create_screen.py \
    --name <PascalCaseName> \
    --package <full.kotlin.package> \
    (--dir <abs/output/dir> | --src <abs/src/commonMain/kotlin>) \
    [--use-case-provider <com.example.FooUseCaseProvider>] \
    [--force]
```

### Arguments

| Flag | Required | Meaning |
|---|---|---|
| `--name` | yes | PascalCase screen name. Used as class prefix (`Login` → `LoginContract`, `LoginScreen`, …). |
| `--package` | yes | Full Kotlin package the files go in, e.g. `com.outside.feature.auth.ui.screens.login`. |
| `--dir` | either `--dir` or `--src` | Absolute directory where files will be written. Takes precedence over `--src`. |
| `--src` | either `--dir` or `--src` | Absolute source root (e.g. `.../src/commonMain/kotlin`). Output dir is computed as `src / package.replace('.', '/')`. |
| `--use-case-provider` | no | Fully-qualified UseCaseProvider to inject into the UiComponent via `@Component val useCaseProvider`. Omit for screens without domain dependencies. |
| `--force` | no | Overwrite existing files. Otherwise the script aborts without writing anything if any target file already exists. |

### Example

```sh
python3 .claude/skills/create-screen/scripts/create_screen.py \
    --name Profile \
    --package com.outside.feature.profile.ui.screens.profile \
    --src /Users/ribads/Projects/outside/features/profile/ui/src/commonMain/kotlin \
    --use-case-provider com.outside.feature.profile.usecase.di.ProfileUseCaseProvider
```

## When to use

Invoke this skill whenever a user asks to create, add, or scaffold a new screen in a KMP project that uses Synapse. Prefer running the script over hand-writing the 7 files — that's the whole point.

## Conventions the scaffold already bakes in

Do not undo these while filling the scaffold in. They are the house style, documented in `/mvi`:

- `internal object {Name}Contract` with members in the order `Mapper` → `Intent` → `Result` → `Effect` → `ViewState`
- `@Immutable` `ViewState` with `companion object { val Default }`
- A `Mapper` interface in the Contract plus a pure `{Name}Mapper` implementation
- `process()` as a single `merge(...)` of `filterIsInstance` registrations, declared last in the Interactor
- A `Reducer` returning `Reduction` via `noEffects()` / `withEffect`
- A ViewModel with no body; it only wires `FlowViewModelArgs`
- The `.bind()` binding pattern in `{Name}UiComponent`, with `provideDefaultViewState()`
- A Screen that reads `val viewState by viewModel.state`, calls `OnFirstComposition`, and consumes `effects.CollectAsEffect`

## After running the script

The generated files are a minimal compiling scaffold. The user still needs to:

1. Add `{Name}UiComponent` to the feature's `ViewModelComponent` so the screen gets constructed.
2. Declare `@Serializable data object {Name}Route : NavKey`, register `entry<{Name}Route>` in the feature's `FeatureLauncher.register`, and add the route to that feature's `serializers` module.
3. Extend `{Name}Contract.Intent` / `Result` / `Effect` / `ViewState` with the feature-specific fields, using component models on `ViewState`, not primitives.
4. Wire any UseCases through the `Mapper` + `Interactor`.

When helping the user wire these up, reach for:
- `/build-screen`: the end-to-end workflow, component picker, and definition-of-done checklist
- `/mvi`: Contract shape, Mapper/Interactor/Reducer rules, Effect vs. state
- `/navigation`: `FeatureLauncher`, typed `NavKey` routes, `NavigationCommand`
- `/data-boundaries`: what the screen may import, and what a UseCase returns
- `/di-scopes` — `@SingletonScope`, kotlin-inject wiring
- `/ui-components` / `/ui-element` — Scaffold, ButtonModel, TextInputModel, Theme, Clause
- `/component-authoring`: writing a composable Synapse doesn't ship
