"""Root Typer application and manifest-driven command registration.

The command tree is built from the reviewed command manifests so the registered
surface can never drift from the parity records: every non-alias command record
becomes exactly one Typer command at its manifest ``command_path``, and nothing
else is registered.

Every command exposes the global machine-output and agent-mode options
(``--output``, ``--no-input``, ``--no-progress``, ``--color``, ``--profile``,
``--project`` and the timeout family) so an autonomous agent gets deterministic,
promptless behavior on any command without reading source. Command-specific
positionals and options are added per family as each handler is implemented.
"""

from __future__ import annotations

import inspect
import re
import sys
import threading
from collections.abc import Callable, Sequence
from dataclasses import replace
from difflib import get_close_matches
from functools import cache
from typing import TYPE_CHECKING, Any

import typer
from typer._click import exceptions as _typer_click_exceptions
from typer._click.core import Command as _ClickCommand
from typer._click.core import Parameter as _ClickParameter
from typer.core import TyperCommand, TyperGroup

from mammoth_cli.app.help_text import (
    _GROUP_DESCRIPTIONS,
    _ROOT_HELP_PANELS,
    _ROOT_LEAF_HELP,
    _command_help,
    _group_description,
    _indexed_summary,
)
from mammoth_cli.app.options import (
    _SHARED_OPTION_PARAMS,
    _positional_param,
    _version_callback,
)
from mammoth_cli.app.tree import _command_tree
from mammoth_cli.app.usage import (
    _ABORT_ERRORS,
    _NO_ARGS_ERROR,
    _USAGE_ERRORS,
    _output_mode_from_argv,
    _unknown_flag_in,
    _unknown_option_report,
    _usage_error_report,
    missing_argument_hint,
)
from mammoth_cli.commands import BESPOKE
from mammoth_cli.errors.envelope import EXIT_INTERRUPT, EXIT_USAGE, CliError, cancelled_error
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.policy import (
    MACHINE_OUTPUTS,
)
from mammoth_cli.services.positional_spec import PositionalSpec
from mammoth_cli.services.positionals import resolve_positionals

if TYPE_CHECKING:
    from mammoth_cli.runtime.invocation import Invocation


class _LeafGroup(TyperGroup):
    """Group for a node that is also an invocable command with positionals.

    Click resolves the first bare token after a group as a subcommand name, so
    ``mammoth project resource-dependencies 3`` failed with ``No such command
    '3'`` even though the manifest (and every printed example) takes the
    project id positionally. When the leading token is not a registered
    subcommand, keep every token as an argument for the group callback instead;
    genuine subcommands (``... resource-dependencies update 3``) are unaffected.
    """

    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:
        # Click's parser consumes ``args`` in place; keep the tokens for the second parse.
        tokens = list(args)
        super().parse_args(ctx, args)
        protected = list(getattr(ctx, "_protected_args", ()) or ())
        if protected and protected[0] not in self.commands:
            # Leaf invocation. A group parser stops at the first bare token, so
            # options after the positional were left unparsed; parse again as a
            # plain command with interspersed options, keeping the bare tokens
            # as the callback's positional arguments.
            ctx.allow_interspersed_args = True
            ctx.args = _ClickCommand.parse_args(self, ctx, tokens)
            # Click's own attribute for the pending subcommand token (Click
            # >= 8.2 made it private); not an SDK member.
            setattr(ctx, "_protected_args", [])  # noqa: B010
        return list(ctx.args)


class _EnvelopeGroup(TyperGroup):
    """Root group that renders Click usage errors as the machine error envelope.

    It also materialises top-level command groups lazily (see
    :func:`_load_top_level_group`): ``list_commands`` and ``get_command`` know
    every group by name from the manifest, but a group's Click tree is only
    built when it is invoked, completed or listed in ``--help``. Reading
    ``commands`` directly materialises them all, so tools that walk the tree
    still see the full surface.

    Click's standalone error handling prints a human ``Usage: ... Error: ...``
    message and exits, even under ``--output json``: an agent driving the CLI
    then receives un-parseable prose (or, for a leaf that also parents
    subcommands, a raw ``No such command`` error) instead of the stable JSON
    envelope every handler-level failure emits. This override intercepts every
    usage error (Typer's vendored ``UsageError``) raised anywhere in the command
    tree and, when a machine output was requested, emits the same envelope
    contract. Human output is unchanged (Click's own rendering is reused).

    The interception runs Click's machinery with ``standalone_mode=False`` so
    usage errors propagate here rather than being printed by Click, then restores
    the ``SystemExit`` contract the console entry point and the test runner rely
    on.
    """

    @property  # type: ignore[override]
    def commands(self) -> dict[str, Any]:
        loaded: dict[str, Any] = self.__dict__.setdefault("_eager_commands", {})
        for name in _LAZY_GROUP_NAMES:
            if name not in loaded:
                loaded[name] = _load_lazy_root(name)
        return loaded

    @commands.setter
    def commands(self, value: Any) -> None:
        self.__dict__["_eager_commands"] = dict(value or {})

    def list_commands(self, ctx: Any) -> list[str]:
        eager = self.__dict__.get("_eager_commands", {})
        # Top-level leaves list ahead of groups, the order they were registered in.
        lazy = sorted(_LAZY_GROUP_NAMES, key=lambda name: name not in _LAZY_LEAF_IDS)
        return [*eager, *(name for name in lazy if name not in eager)]

    def get_command(self, ctx: Any, cmd_name: str) -> Any:
        eager: dict[str, Any] = self.__dict__.setdefault("_eager_commands", {})
        if cmd_name not in eager and cmd_name in _LAZY_GROUP_NAMES:
            if self.__dict__.get("_listing_help"):
                if cmd_name in _LAZY_LEAF_IDS:
                    return _root_leaf_stub(cmd_name)
                return _group_stub(cmd_name)
            eager[cmd_name] = _load_lazy_root(cmd_name)
        return eager.get(cmd_name)

    def resolve_command(self, ctx: Any, args: list[str]) -> Any:
        # Typer's override suggests close names from ``self.commands``, which
        # builds every group; the names alone are all a suggestion needs.
        try:
            return self._click_resolve_command(ctx, args)
        except _typer_click_exceptions.UsageError as error:
            if self.suggest_commands and args:
                matches = get_close_matches(args[0], self.list_commands(ctx))
                if matches:
                    suggestions = ", ".join(f"{m!r}" for m in matches)
                    error.message = f"{error.message.rstrip('.')}. Did you mean {suggestions}?"
            raise

    def format_help(self, ctx: Any, formatter: Any) -> None:
        # Root ``--help`` only needs each group's name, panel and one-line
        # description; building all ~550 commands to print them cost seconds.
        self.__dict__["_listing_help"] = True
        try:
            super().format_help(ctx, formatter)
        finally:
            self.__dict__["_listing_help"] = False

    def main(self, *args: Any, **kwargs: Any) -> Any:
        if not kwargs.get("standalone_mode", True):
            return super().main(*args, **kwargs)
        kwargs["standalone_mode"] = False
        try:
            result = super().main(*args, **kwargs)
        except _USAGE_ERRORS as error:
            argv = _argv_of(args, kwargs)
            self.render_usage_error(error, argv)
            raise SystemExit(getattr(error, "exit_code", EXIT_USAGE)) from None
        except _ABORT_ERRORS:
            mode = _output_mode_from_argv(_argv_of(args, kwargs))
            if mode in MACHINE_OUTPUTS or mode == "yaml":
                from mammoth_cli.output.emit import emit_error

                emit_error(cancelled_error(), machine=True, output=mode)
                raise SystemExit(EXIT_INTERRUPT) from None
            typer.echo("Aborted!", err=True)
            raise SystemExit(1) from None
        # Under standalone_mode=False a normal return is either None (success) or
        # an int exit code (a click Exit, e.g. --help/--version or our own
        # CliError path). Re-raise SystemExit so both the console script and the
        # in-process test runner observe the exit status as before.
        raise SystemExit(result if isinstance(result, int) else 0)

    def render_usage_error(self, error: Any, argv: Sequence[str] | None) -> None:
        """Emit a usage error as the JSON envelope (machine) or Click prose (human).

        A *missing required argument* is reported with the stable
        ``missing_argument`` code that the handler-level ``_require_*`` helpers
        also raise, so the machine error contract is identical whether a required
        positional is now enforced natively by Typer (a Click-layer
        ``MissingParameter``, the common case since positionals are declared with
        their real requiredness) or by a handler that reads it from
        ``extra_args``. Every other usage error (unknown command, bad option or
        argument value, an id read as a subcommand) stays ``usage_error``.

        Two Click messages are unusable as-is and are replaced by
        :func:`_usage_error_report`: the empty one a group raises when invoked
        with no subcommand, and the "No such command '--profile'" a global
        option written before the command produces.
        """
        tokens = list(argv) if argv is not None else sys.argv[1:]
        # Missing required parameters must not be rewritten by the generic
        # group-level classifier (schema get and nested commands rely on the
        # stable missing_argument envelope).
        error_message = error.format_message()
        is_missing_parameter = (
            isinstance(error, _typer_click_exceptions.MissingParameter)
            or error.__class__.__name__ == "MissingParameter"
            or bool(re.match(r"^Missing argument '[^']+'\.", error_message))
        )
        report = None if is_missing_parameter else _usage_error_report(error, tokens)
        if is_missing_parameter and (option := _unknown_flag_in(error, tokens)):
            # A misspelt flag is the first thing to fix, ahead of a missing argument.
            report = _unknown_option_report(error, option)
        mode = _output_mode_from_argv(argv)
        if mode in MACHINE_OUTPUTS or mode == "yaml":
            if report is None:
                missing = is_missing_parameter
                if missing:
                    report = CliError(
                        code="missing_argument",
                        message=error_message,
                        exit_status=EXIT_USAGE,
                        hint=missing_argument_hint(tokens),
                    )
                elif isinstance(error, _typer_click_exceptions.NoSuchOption):
                    option = getattr(error, "option_name", None) or "unknown"
                    report = _unknown_option_report(error, option)
                elif isinstance(error, _typer_click_exceptions.BadParameter):
                    # With optional typed positionals Click may consume an
                    # unknown option token as the positional value. Only
                    # classify an argv flag that is not a known global option;
                    # a known option's malformed value remains usage_error.
                    option = _unknown_flag_in(error, tokens)
                    if option:
                        report = _unknown_option_report(error, option)
                    else:
                        report = CliError(
                            code="usage_error",
                            message=error.format_message(),
                            exit_status=EXIT_USAGE,
                            hint="Check the command schema with 'mammoth schema get'.",
                        )
                else:
                    report = CliError(
                        code="missing_argument" if missing else "usage_error",
                        message=error.format_message(),
                        exit_status=EXIT_USAGE,
                        hint="Check the command schema with 'mammoth schema get'.",
                    )
            from mammoth_cli.output.emit import emit_error

            emit_error(report, machine=True, output=mode)
        elif report is None:
            error.show()
            if is_missing_parameter:
                typer.echo(missing_argument_hint(tokens), err=True)
        else:
            # A no-subcommand error arrives with the help text already on
            # screen, so repeating "run --help" below it would be noise.
            no_args = _NO_ARGS_ERROR is not None and isinstance(error, _NO_ARGS_ERROR)
            ctx = getattr(error, "ctx", None)
            if ctx is not None and not no_args:
                # Click's own usage line first, as its prose error has it.
                typer.echo(ctx.get_usage(), err=True)
            typer.echo(f"Error: {report.message}", err=True)
            if report.hint and not no_args:
                typer.echo(report.hint, err=True)
            for command in report.recovery_commands:
                typer.echo(f"  try: {command}", err=True)


def _argv_of(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Sequence[str] | None:
    """The argv a ``main`` call was given: the ``args`` keyword, else the first positional.

    Args:
        args: The positional arguments of the ``main`` call.
        kwargs: The keyword arguments of the ``main`` call.

    Returns:
        The argv tokens, or None when the call used ``sys.argv``.
    """
    argv = kwargs.get("args")
    if argv is None:
        argv = args[0] if args else None
    return argv


def _build_leaf(command_id: str, *, is_group_callback: bool = False) -> Callable[..., None]:
    """Return a Typer callback bound to one manifest command id.

    Every callback shares the same global-option signature so ``--help`` for any
    command advertises the machine-output and agent-mode contract, and declares
    one native Typer ``Argument`` per positional derived for the command (see
    :func:`mammoth_cli.services.positionals.resolve_positionals`), so its
    ``--help`` shows an Arguments panel and the parsed values route into
    :attr:`Invocation.positionals` — a single, code-derived source of truth for
    the command's positional shape.

    The parsed positionals are also mirrored, in declared order, into
    :attr:`Invocation.extra_args` ahead of any genuine surplus tokens. Handlers
    may read them positionally (``extra_args``) or by name
    (:meth:`Invocation.positional`); both views come from the same declaration,
    so they cannot drift, and the surplus/id checks in
    :mod:`mammoth_cli.runtime.strict` and :mod:`mammoth_cli.runtime.validate`
    (which align a command's derived positionals against ``extra_args``) keep
    working unchanged.

    When ``is_group_callback`` is set the command sits at a node that also has
    subcommands; the callback then only runs when no subcommand is invoked and
    declares no positionals.
    """
    positionals: tuple[PositionalSpec, ...] = (
        () if is_group_callback else resolve_positionals(command_id)
    )
    positional_names = tuple(spec.name for spec in positionals)

    def leaf(**params: Any) -> None:
        from mammoth_cli.runtime.invocation import Invocation

        ctx: typer.Context = params.pop("ctx")
        if is_group_callback and ctx.invoked_subcommand is not None:
            return
        resolved = {name: params.pop(name) for name in positional_names}
        present = {name: value for name, value in resolved.items() if value is not None}
        # Mirror the bound positionals (in declared order) into extra_args ahead
        # of any genuine surplus tokens, so handlers reading extra_args by index
        # and the derived-positional surplus/id checks both keep working.
        mirrored = [str(resolved[name]) for name in positional_names if resolved[name] is not None]
        invocation = Invocation(
            command_id=command_id,
            positionals=present,
            extra_args=[*mirrored, *ctx.args],
            **params,
        )
        _execute(invocation)

    signature_params = [
        inspect.Parameter("ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=typer.Context),
        *(_positional_param(spec) for spec in positionals),
        *_SHARED_OPTION_PARAMS,
    ]
    leaf.__signature__ = inspect.Signature(signature_params)  # type: ignore[attr-defined]
    leaf.__annotations__ = {param.name: param.annotation for param in signature_params}
    leaf.__name__ = "cmd_" + command_id.replace(".", "_").replace("-", "_")
    return leaf


def _execute(invocation: Invocation) -> None:
    """Run one command: dispatch to its handler and render the envelope."""
    # Freeze the fallback profile before opening a service.  A recovery command
    # must inspect the same account that submitted/observed a job, rather than
    # resolving the mutable selected-profile pointer after an interrupt.
    from mammoth_cli.context import profiles
    from mammoth_cli.runtime import executor, leaf
    from mammoth_cli.runtime.compact import FULL_FLAG, FULL_FLAG_COMMANDS
    from mammoth_cli.runtime.reveal import REVEAL_COMMANDS, REVEAL_FLAG

    if invocation.profile is None:
        invocation = replace(invocation, profile=profiles.get_selected(), profile_is_default=True)
    if invocation.command_id in FULL_FLAG_COMMANDS and FULL_FLAG in invocation.extra_args:
        invocation = replace(
            invocation,
            extra_args=[arg for arg in invocation.extra_args if arg != FULL_FLAG],
            full_output=True,
        )
    if invocation.command_id in REVEAL_COMMANDS and REVEAL_FLAG in invocation.extra_args:
        invocation = replace(
            invocation,
            extra_args=[arg for arg in invocation.extra_args if arg != REVEAL_FLAG],
            reveal_secrets=True,
        )

    executor.run(
        invocation.command_id,
        invocation.output,
        leaf.producer(invocation),
        agent_mode=invocation.no_input,
        invocation=invocation,
        profile=invocation.profile,
        interceptors=leaf.LEAF_INTERCEPTORS,
    )


def _leaf_context_settings(command_id: str) -> dict[str, bool]:
    """Click settings for one command: a bespoke command declares every option it
    accepts, so Click itself rejects an unknown one; a generic leaf collects its
    trailing tokens and validates them in :func:`validate_extra_args`."""
    if command_id in BESPOKE:
        return {}
    return {"allow_extra_args": True, "ignore_unknown_options": True}


def _group_typer(tokens: tuple[str, ...], command_id: str | None) -> typer.Typer:
    if command_id is not None:
        # This node is both a group and an invocable command.
        sub = typer.Typer(
            cls=_LeafGroup,
            no_args_is_help=False,
            invoke_without_command=True,
            context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
        )
        sub.callback()(_build_leaf(command_id, is_group_callback=True))
        return sub
    return typer.Typer(
        help=_group_description(tokens),
        no_args_is_help=True,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )


def _lazy_help_command(command_id: str) -> type[TyperCommand]:
    """A command class whose help is read from the handler only when printed.

    Building a group registers every command in it; reading each help text up
    front imports every handler module of the group, though a run uses one.
    """

    class LazyHelpCommand(TyperCommand):
        @property
        def help(self) -> str | None:
            return _command_help(command_id, command_by_id(command_id))

        @help.setter
        def help(self, value: str | None) -> None:
            """Ignore the registration-time placeholder; the handler is the source."""

        @property
        def short_help(self) -> str | None:
            """The group listing prints only the first paragraph, which is the summary."""
            return _indexed_summary(command_id)

        @short_help.setter
        def short_help(self, value: str | None) -> None:
            """Ignore the registration-time value; the handler is the source."""

    return LazyHelpCommand


#: Guards the lazy builds below. Re-entrant: building a command can build another.
_BUILD_LOCK = threading.RLock()


def _unbuilt_leaf() -> None:
    """Registration placeholder: a lazy leaf takes its real callback from the built command."""


def _lazy_leaf_command(command_id: str) -> type[TyperCommand]:
    """A generic leaf whose parameters and callback are built when first read.

    Building a leaf derives its positionals from the SDK signature, which
    imports the SDK model modules. A group's ``--help`` lists names and help
    only, so it never reads them; a run reads them for the one command used.
    """

    class LazyLeafCommand(_lazy_help_command(command_id)):  # type: ignore[misc]
        _built: _ClickCommand | None = None

        def _real(self) -> _ClickCommand:
            built = self._built
            if built is not None:
                return built
            # Double-checked: a host's worker threads may reach a first use together.
            with _BUILD_LOCK:
                built = self._built
                if built is None:
                    built = self._built = self._build()
            return built

        def _build(self) -> _ClickCommand:
            from typer.models import CommandInfo

            info = CommandInfo(
                name=self.name,
                callback=_build_leaf(command_id),
                # The help text is read from this class's lazy ``help`` property; building
                # it here would import the contract and schema layers on every run.
                help="",
                rich_help_panel=self.rich_help_panel,
                context_settings=_leaf_context_settings(command_id),
            )
            return typer.main.get_command_from_info(
                info,
                pretty_exceptions_short=_LAZY_SETTINGS["pretty_exceptions_short"],
                rich_markup_mode=self.rich_markup_mode,
            )

        @property
        def params(self) -> list[_ClickParameter]:
            return self._real().params

        @params.setter
        def params(self, value: list[_ClickParameter]) -> None:
            """Ignore the registration-time parameters; the built command owns them."""

        @property
        def callback(self) -> Any:
            return self._real().callback

        @callback.setter
        def callback(self, value: Any) -> None:
            """Ignore the registration-time placeholder callback."""

    return LazyLeafCommand


def _populate(base: tuple[str, ...], group: typer.Typer) -> None:
    """Register every command below ``base`` (exclusive) on ``group``."""
    path_to_command, containers = _command_tree()
    groups: dict[tuple[str, ...], typer.Typer] = {base: group}

    def _group_for(tokens: tuple[str, ...]) -> typer.Typer:
        if tokens in groups:
            return groups[tokens]
        parent = _group_for(tokens[:-1])
        sub = _group_typer(tokens, path_to_command.get(tokens))
        top_level = tokens[0]
        parent.add_typer(
            sub,
            name=tokens[-1],
            help=_group_description(tokens),
            rich_help_panel=_ROOT_HELP_PANELS.get(top_level) if len(tokens) == 1 else None,
        )
        groups[tokens] = sub
        return sub

    below = {t: c for t, c in path_to_command.items() if t[: len(base)] == base and t != base}
    # Ensure every container group exists (parents before children).
    for tokens in sorted((t for t in below if t in containers), key=len):
        _group_for(tokens)

    # Register every non-container command as a leaf under its parent group.
    # A command_id with a bespoke, fully-typed callback overrides the generic
    # leaf at the same registered name and path; the manifest-driven surface
    # is otherwise unchanged.
    for tokens, command_id in sorted(below.items()):
        if tokens in containers:
            continue
        bespoke = BESPOKE.get(command_id)
        _group_for(tokens[:-1]).command(
            name=tokens[-1],
            cls=_lazy_help_command(command_id) if bespoke else _lazy_leaf_command(command_id),
            help="",
            rich_help_panel=_ROOT_HELP_PANELS.get(tokens[0]) if len(tokens) == 1 else None,
            context_settings=_leaf_context_settings(command_id),
        )(bespoke or _unbuilt_leaf)


@cache
def _top_level_typer(name: str) -> typer.Typer:
    """Build (once) the Typer sub-app for one top-level command group."""
    path_to_command, _ = _command_tree()
    sub = _group_typer((name,), path_to_command.get((name,)))
    _populate((name,), sub)
    return sub


#: Groups kept out of ``mammoth --help`` until their backend is generally available.
#: They still run when typed; only the listing hides them.
_HIDDEN_UNTIL_GA = frozenset({"agent"})

# Top-level groups are converted to Click on first use. Building the leaf
# callbacks and ``--help`` text for all ~550 commands, then letting Typer
# convert every one of them, used to cost most of the CLI's start-up time on
# every invocation; a run touches one group.
_LAZY_GROUP_NAMES: list[str] = []
_LAZY_SETTINGS: dict[str, Any] = {}


def _load_top_level_group(name: str) -> Any:
    from typer.models import TyperInfo

    info = TyperInfo(
        _top_level_typer(name),
        name=name,
        help=_GROUP_DESCRIPTIONS.get(name, f"Commands for {name}."),
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        hidden=name in _HIDDEN_UNTIL_GA,
    )
    return typer.main.get_group_from_info(info, **_LAZY_SETTINGS)


_LAZY_LEAF_IDS: dict[str, str] = {}


def _load_root_leaf(name: str) -> Any:
    from typer.models import CommandInfo

    command_id = _LAZY_LEAF_IDS[name]
    info = CommandInfo(
        name=name,
        callback=BESPOKE.get(command_id) or _build_leaf(command_id),
        help=_command_help(command_id, command_by_id(command_id)),
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        context_settings=_leaf_context_settings(command_id),
    )
    return typer.main.get_command_from_info(
        info,
        pretty_exceptions_short=_LAZY_SETTINGS["pretty_exceptions_short"],
        rich_markup_mode=_LAZY_SETTINGS["rich_markup_mode"],
    )


def _root_leaf_stub(name: str) -> Any:
    """A placeholder leaf carrying only what the root ``--help`` listing prints."""
    return TyperCommand(
        name=name,
        help=_ROOT_LEAF_HELP[name],
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        rich_markup_mode=_LAZY_SETTINGS["rich_markup_mode"],
    )


def _load_lazy_root(name: str) -> Any:
    return _load_root_leaf(name) if name in _LAZY_LEAF_IDS else _load_top_level_group(name)


def _group_stub(name: str) -> Any:
    """A placeholder group carrying only what the root ``--help`` listing prints."""
    return TyperGroup(
        name=name,
        help=_GROUP_DESCRIPTIONS.get(name, f"Commands for {name}."),
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        rich_markup_mode=_LAZY_SETTINGS["rich_markup_mode"],
        hidden=name in _HIDDEN_UNTIL_GA,
    )


def build_app() -> typer.Typer:
    """Construct the Typer command tree from the command manifests.

    Top-level leaves (``doctor``, ``version``, ...) are registered here; every
    top-level group is materialised by :class:`_EnvelopeGroup` on demand.
    """
    root = typer.Typer(
        name="mammoth",
        help=(
            "Command-line interface for the Mammoth Analytics platform.\n\n"
            "Start with 'mammoth doctor' to check access, 'mammoth schema find QUERY' "
            "to locate a command, and 'mammoth schema get COMMAND_ID' for its full input schema."
        ),
        no_args_is_help=True,
        add_completion=True,
        cls=_EnvelopeGroup,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )

    @root.callback()
    def _root(
        version: bool = typer.Option(
            False, "--version", callback=_version_callback, is_eager=True, help="Show version."
        ),
    ) -> None:
        """Root callback holding eager global options."""

    path_to_command, containers = _command_tree()
    top_names = sorted({tokens[0] for tokens in path_to_command})
    lazy: list[str] = []
    for name in top_names:
        if (name,) in containers or (name,) not in path_to_command:
            lazy.append(name)
            continue
        _LAZY_LEAF_IDS[name] = path_to_command[(name,)]
        lazy.append(name)
    _LAZY_GROUP_NAMES[:] = lazy
    _LAZY_SETTINGS.update(
        pretty_exceptions_short=root.pretty_exceptions_short,
        rich_markup_mode=root.rich_markup_mode,
        suggest_commands=root.suggest_commands,
    )
    return root


def registered_command_paths() -> set[str]:
    """Return every registered command path by walking the built Typer trees.

    Container commands (a node that is both a group and invocable) are counted
    by their own path as well as their subcommands.
    """
    paths: set[str] = set()

    def walk(instance: typer.Typer, prefix: tuple[str, ...]) -> None:
        for command in instance.registered_commands:
            name = command.name or (command.callback.__name__ if command.callback else None)
            if name:
                paths.add(" ".join((*prefix, name)))
        for group in instance.registered_groups:
            sub = group.typer_instance
            name = group.name
            if sub is None or not name:
                continue
            node = (*prefix, name)
            if sub.registered_callback is not None:
                paths.add(" ".join(node))
            walk(sub, node)

    walk(app, ())
    for name in _LAZY_GROUP_NAMES:
        if name in _LAZY_LEAF_IDS:
            paths.add(name)
            continue
        sub = _top_level_typer(name)
        if sub.registered_callback is not None:
            paths.add(name)
        walk(sub, (name,))
    return paths


_ROOT_COMMAND: Any = None


def _root_click_command() -> Any:
    """Build (once) and cache the fully resolved Click command tree.

    ``typer.main.get_command`` walks and converts every registered Typer
    sub-app into its Click representation; over the full manifest-driven tree
    that is expensive enough that recomputing it per lookup made a full sweep
    over every command (see the contract test) take minutes. Cached because
    the tree is fixed for the process lifetime (:data:`app` is built once at
    import time). Built under a lock, so a host's threads making their first call
    together share one tree instead of each building their own.
    """
    global _ROOT_COMMAND
    root = _ROOT_COMMAND
    if root is not None:
        return root
    with _BUILD_LOCK:
        if _ROOT_COMMAND is None:
            built: Any = typer.main.get_command(app)
            built.commands  # noqa: B018 -- materialise every lazy top-level group
            _ROOT_COMMAND = built
        return _ROOT_COMMAND


def command_option_names(command_path: str) -> set[str]:
    """Return every declared option flag for one registered command path.

    Walks the built Click command tree by ``command_path`` tokens (for example
    ``"view transform bulk-replace"``) and collects each parameter's option
    strings (``"--output"``, ``"-o"``, ...). This is a structural check: it
    reads the already-parsed command declaration, so it is fast and immune to
    the rendered-width and terminal-detection nondeterminism of asserting on
    rendered ``--help`` text. Command nodes are walked duck-typed (via their
    ``commands`` mapping) rather than by an ``isinstance`` check against
    ``click``'s public types, since Typer's pinned version resolves its command
    tree through its own vendored click fork (``typer._click``), whose classes
    are not the public ``click`` package's.

    Args:
        command_path: The space-separated manifest command path.

    Returns:
        The union of every parameter's primary and secondary option strings
        declared on that command (or group callback).

    Raises:
        ValueError: When ``command_path`` does not resolve to a registered
            command.
    """
    command: Any = _root_click_command()
    for token in command_path.split():
        subcommands: dict[str, Any] | None = getattr(command, "commands", None)
        if subcommands is None or token not in subcommands:
            raise ValueError(f"'{command_path}' is not a registered command path.")
        command = subcommands[token]
    names: set[str] = set()
    for param in command.params:
        names.update(getattr(param, "opts", ()))
        names.update(getattr(param, "secondary_opts", ()))
    return names


app = build_app()


def main() -> Any:
    """Console-script entry point."""
    return app()


if __name__ == "__main__":  # pragma: no cover
    main()
