---
name: create-screen
description: Use when scaffolding a new screen in a Synapse-based KMP app. Generates the 7-file IRS-MVI screen package (Contract, Interactor, Reducer, Mapper, ViewModel, Screen, di/UiComponent) via a script.
user-invocable: true
---

# create-screen — Synapse IRS-MVI Screen Scaffold

Generates the canonical 7-file screen package used in Synapse apps. Every screen in a Synapse project follows the same IRS-MVI structure — this skill eliminates the boilerplate.

## What it creates

```
<package>/
├── {Name}Contract.kt         sealed Intent, sealed Result, @Immutable ViewState, Mapper interface
├── {Name}Interactor.kt       Interactor<Intent, Result> — merge() + filterIsInstance routing
├── {Name}Reducer.kt          Reducer<ViewState, Result> — pure state machine
├── {Name}Mapper.kt           Contract.Mapper impl — intent/domain → Result conversion
├── {Name}ViewModel.kt        LifecycleViewModel boilerplate
├── {Name}Screen.kt           @Composable — Scaffold, derivedStateOf, navigationCommand handling
└── di/{Name}UiComponent.kt   @Component kotlin-inject with @Provides bindings
```

The scaffold ships with the baseline intents every Synapse screen needs:
`LoadInitialData`, `Navigation.Done`, `Navigation.Back`, a `NavigationCommand?` on the ViewState, and the `isFirstIntent` + `navigationCommand.let { ... }` wiring in the composable.

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

## After running the script

The script prints a short checklist. The files it generates are a minimal compiling scaffold; the user still needs to:

1. Add `{Name}UiComponent` to the feature's `ViewModelComponent` so the screen gets constructed.
2. Register the screen's route in the feature's `NavigatorHost` (`FeatureLauncher.navigationGraph()`).
3. Extend `{Name}Contract.Intent` / `Result` / `ViewState` with the feature-specific fields.
4. Wire any UseCases through the `Mapper` + `Interactor`.

When helping the user wire these up, reach for:
- `/mvi` — IRS-MVI APIs
- `/navigation` — `NavigatorHost`, `FeatureLauncher`, `NavigationCommand`
- `/di-scopes` — `@SingletonScope`, kotlin-inject wiring
- `/ui-components` / `/ui-element` — Scaffold, ButtonModel, TextInputModel, Theme, Clause
