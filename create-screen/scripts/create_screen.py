#!/usr/bin/env python3
"""Generate a Synapse screen scaffold (7 files following the IRSE-MVI pattern).

Creates:
  {Name}Contract.kt    - Intent/Result/Effect/ViewState + Mapper interface
  {Name}Interactor.kt  - Wires intents via merge() + filterIsInstance
  {Name}Reducer.kt     - Pure state machine returning Reduction(State, Effects)
  {Name}Mapper.kt      - Contract.Mapper impl
  {Name}ViewModel.kt   - LifecycleViewModel boilerplate
  {Name}Screen.kt      - Compose entry, renders ViewState, emits Intents, collects Effects
  di/{Name}UiComponent.kt - kotlin-inject @Component with bindings
"""

import argparse
import sys
from pathlib import Path


def to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


CONTRACT = '''package __PACKAGE__

import androidx.compose.runtime.Immutable
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand

internal object __NAME__Contract {

    interface Mapper {
        fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded
        fun toResult(intent: Intent.Navigation): Result.NavigationRequested
    }

    sealed class Intent {
        data object LoadInitialData : Intent()
        sealed class Navigation : Intent() {
            data object Back : Navigation()
        }
    }

    sealed class Result {
        data object OnInitialDataLoaded : Result()
        data class NavigationRequested(val command: NavigationCommand) : Result()
    }

    sealed class Effect {
        data class Navigate(val command: NavigationCommand) : Effect()
    }

    @Immutable
    data class ViewState(
        val isLoading: Boolean = false,
    ) {
        companion object {
            val Default = ViewState()
        }
    }
}
'''

INTERACTOR = '''package __PACKAGE__

import com.ribads.synapse.ui.mvi.Interactor
import __PACKAGE__.__NAME__Contract.Intent
import __PACKAGE__.__NAME__Contract.Mapper
import __PACKAGE__.__NAME__Contract.Result
import __PACKAGE__.__NAME__Contract.ViewState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.merge
import me.tatarka.inject.annotations.Inject

internal class __NAME__Interactor @Inject constructor(
    private val mapper: Mapper,
) : Interactor<Intent, Result, ViewState> {

    override fun process(
        intents: Flow<Intent>,
        state: StateFlow<ViewState>,
    ): Flow<Result> {
        return merge(
            intents.filterIsInstance<Intent.LoadInitialData>().map(mapper::toResult),
            intents.filterIsInstance<Intent.Navigation>().map(mapper::toResult),
        )
    }
}
'''

REDUCER = '''package __PACKAGE__

import com.ribads.synapse.ui.mvi.Reducer
import com.ribads.synapse.ui.mvi.Reduction
import com.ribads.synapse.ui.mvi.noEffects
import com.ribads.synapse.ui.mvi.withEffect
import __PACKAGE__.__NAME__Contract.Effect
import __PACKAGE__.__NAME__Contract.Result
import __PACKAGE__.__NAME__Contract.ViewState
import me.tatarka.inject.annotations.Inject

internal class __NAME__Reducer @Inject constructor() : Reducer<ViewState, Result, Effect> {
    override fun reduce(
        state: ViewState,
        result: Result,
    ): Reduction<ViewState, Effect> {
        return when (result) {
            is Result.OnInitialDataLoaded -> state.noEffects()
            is Result.NavigationRequested -> state withEffect Effect.Navigate(result.command)
        }
    }
}
'''

MAPPER = '''package __PACKAGE__

import com.ribads.synapse.ui.compose.presentation.navigation.NavigationCommand
import __PACKAGE__.__NAME__Contract.Intent
import __PACKAGE__.__NAME__Contract.Mapper
import __PACKAGE__.__NAME__Contract.Result
import me.tatarka.inject.annotations.Inject

internal class __NAME__Mapper @Inject constructor() : Mapper {

    override fun toResult(intent: Intent.LoadInitialData): Result.OnInitialDataLoaded {
        return Result.OnInitialDataLoaded
    }

    override fun toResult(intent: Intent.Navigation): Result.NavigationRequested {
        return when (intent) {
            Intent.Navigation.Back -> Result.NavigationRequested(
                command = NavigationCommand.BackCommand(),
            )
        }
    }
}
'''

VIEW_MODEL = '''package __PACKAGE__

import com.ribads.synapse.ui.mvi.FlowViewModelArgs
import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.LifecycleViewModel
import com.ribads.synapse.ui.mvi.Reducer
import __PACKAGE__.__NAME__Contract.Effect
import __PACKAGE__.__NAME__Contract.Intent
import __PACKAGE__.__NAME__Contract.Result
import __PACKAGE__.__NAME__Contract.ViewState
import me.tatarka.inject.annotations.Inject

internal class __NAME__ViewModel @Inject constructor(
    initialState: ViewState,
    interactor: Interactor<Intent, Result, ViewState>,
    reducer: Reducer<ViewState, Result, Effect>,
) : LifecycleViewModel<Intent, Result, ViewState, Effect>(
    args = FlowViewModelArgs(
        initialState = initialState,
        reducer = reducer,
        interactor = interactor,
    ),
)
'''

SCREEN = '''package __PACKAGE__

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import com.ribads.synapse.ui.component.scaffold.Scaffold
import com.ribads.synapse.ui.compose.presentation.navigation.NavigationDispatcher
import com.ribads.synapse.ui.element.theme.Theme
import com.ribads.synapse.ui.mvi.CollectAsEffect
import com.ribads.synapse.ui.mvi.OnFirstComposition
import __PACKAGE__.__NAME__Contract.Effect
import __PACKAGE__.__NAME__Contract.Intent

@Composable
internal fun __NAME__Screen(
    viewModel: __NAME__ViewModel,
    navigationDispatcher: NavigationDispatcher,
) {
    val viewState by viewModel.state

    viewModel.OnFirstComposition(Intent.LoadInitialData)

    viewModel.effects.CollectAsEffect { effect ->
        when (effect) {
            is Effect.Navigate -> navigationDispatcher.navigateTo(effect.command)
        }
    }

    Scaffold(
        backgroundColor = Theme.colors.surface.primaryLight,
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = Theme.spacing.x6),
        ) {
            // TODO: Render UI from viewState and emit intents via viewModel.emit(...)
        }
    }
}
'''

UI_COMPONENT_NO_PROVIDER = '''package __PACKAGE__.di

import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.Reducer
import __PACKAGE__.__NAME__Contract.Effect
import __PACKAGE__.__NAME__Contract.Intent
import __PACKAGE__.__NAME__Contract.Mapper
import __PACKAGE__.__NAME__Contract.Result
import __PACKAGE__.__NAME__Contract.ViewState
import __PACKAGE__.__NAME__Interactor
import __PACKAGE__.__NAME__Mapper
import __PACKAGE__.__NAME__Reducer
import __PACKAGE__.__NAME__ViewModel
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
internal abstract class __NAME__UiComponent {
    abstract val viewModel: __NAME__ViewModel

    @Provides
    protected fun __NAME__Mapper.bind(): Mapper = this

    @Provides
    protected fun __NAME__Reducer.bind(): Reducer<ViewState, Result, Effect> = this

    @Provides
    fun __NAME__Interactor.bind(): Interactor<Intent, Result, ViewState> = this

    @Provides
    protected fun provideDefaultViewState(): ViewState = ViewState.Default
}
'''

UI_COMPONENT_WITH_PROVIDER = '''package __PACKAGE__.di

import com.ribads.synapse.ui.mvi.Interactor
import com.ribads.synapse.ui.mvi.Reducer
import __PACKAGE__.__NAME__Contract.Effect
import __PACKAGE__.__NAME__Contract.Intent
import __PACKAGE__.__NAME__Contract.Mapper
import __PACKAGE__.__NAME__Contract.Result
import __PACKAGE__.__NAME__Contract.ViewState
import __PACKAGE__.__NAME__Interactor
import __PACKAGE__.__NAME__Mapper
import __PACKAGE__.__NAME__Reducer
import __PACKAGE__.__NAME__ViewModel
import __PROVIDER_FQN__
import me.tatarka.inject.annotations.Component
import me.tatarka.inject.annotations.Provides

@Component
internal abstract class __NAME__UiComponent(
    @Component val useCaseProvider: __PROVIDER_SIMPLE__,
) {
    abstract val viewModel: __NAME__ViewModel

    @Provides
    protected fun __NAME__Mapper.bind(): Mapper = this

    @Provides
    protected fun __NAME__Reducer.bind(): Reducer<ViewState, Result, Effect> = this

    @Provides
    fun __NAME__Interactor.bind(): Interactor<Intent, Result, ViewState> = this

    @Provides
    protected fun provideDefaultViewState(): ViewState = ViewState.Default
}
'''


def render(template: str, ctx: dict) -> str:
    result = template
    for key, value in ctx.items():
        result = result.replace(f"__{key}__", value)
    return result


def resolve_output_dir(args) -> Path:
    if args.dir:
        return Path(args.dir).expanduser().resolve()
    if args.src:
        src = Path(args.src).expanduser().resolve()
        return src.joinpath(*args.package.split("."))
    print("error: must provide either --dir or --src", file=sys.stderr)
    sys.exit(2)


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        print(f"error: {path} already exists (use --force to overwrite)", file=sys.stderr)
        sys.exit(1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Synapse screen scaffold (7 files, IRSE-MVI pattern).",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="PascalCase screen name, e.g. Login, Profile, OrderDetails",
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Full package for the screen, e.g. com.outside.feature.auth.ui.screens.login",
    )
    parser.add_argument(
        "--dir",
        help="Absolute directory to write screen files into (takes precedence over --src)",
    )
    parser.add_argument(
        "--src",
        help="Source root, e.g. .../src/commonMain/kotlin. Combined with --package to compute output dir.",
    )
    parser.add_argument(
        "--use-case-provider",
        help="Optional fully-qualified UseCaseProvider for DI, e.g. com.outside.feature.auth.usecase.di.AuthUseCaseProvider",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    args = parser.parse_args()

    name: str = args.name
    if not name or not name[0].isupper():
        print("error: --name must be PascalCase, e.g. Login", file=sys.stderr)
        sys.exit(2)

    package: str = args.package.strip().strip(".")
    output_dir = resolve_output_dir(args)

    ctx = {"NAME": name, "CAMEL": to_camel(name), "PACKAGE": package}

    provider_fqn = args.use_case_provider
    if provider_fqn:
        provider_simple = provider_fqn.rsplit(".", 1)[-1]
        ui_component_template = UI_COMPONENT_WITH_PROVIDER
        ctx["PROVIDER_FQN"] = provider_fqn
        ctx["PROVIDER_SIMPLE"] = provider_simple
    else:
        ui_component_template = UI_COMPONENT_NO_PROVIDER

    files = [
        (output_dir / f"{name}Contract.kt", CONTRACT),
        (output_dir / f"{name}Interactor.kt", INTERACTOR),
        (output_dir / f"{name}Reducer.kt", REDUCER),
        (output_dir / f"{name}Mapper.kt", MAPPER),
        (output_dir / f"{name}ViewModel.kt", VIEW_MODEL),
        (output_dir / f"{name}Screen.kt", SCREEN),
        (output_dir / "di" / f"{name}UiComponent.kt", ui_component_template),
    ]

    # Pre-check for collisions so we fail before writing anything.
    if not args.force:
        for path, _ in files:
            if path.exists():
                print(f"error: {path} already exists (use --force to overwrite)", file=sys.stderr)
                sys.exit(1)

    print(f"Generating {name} screen in {output_dir}")
    for path, template in files:
        write_file(path, render(template, ctx), args.force)

    print()
    print("Done. Next steps:")
    print(f"  1. Add {name}UiComponent to your feature's ViewModelComponent.")
    print(f"  2. Add `@Serializable data object {name}Route : NavKey`, register `entry<{name}Route>` in your")
    print(f"     feature's FeatureLauncher.register, and add {name}Route to that feature's `serializers`.")
    print(f"  3. Extend {name}Contract.Intent/Result/Effect/ViewState with feature-specific state.")
    print(f"  4. Wire UseCases through the Mapper + Interactor.")


if __name__ == "__main__":
    main()
