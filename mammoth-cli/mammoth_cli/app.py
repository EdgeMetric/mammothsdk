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
import sys
from collections.abc import Callable, Sequence
from functools import cache
from typing import Annotated, Any

import typer
from typer._click import exceptions as _typer_click_exceptions
from typer.core import TyperGroup

from mammoth_cli import __version__
from mammoth_cli.commands import BESPOKE
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError, not_implemented_error
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.output.policy import (
    COLOR_MODES,
    MACHINE_OUTPUTS,
    OUTPUT_AUTO,
    SELECTABLE_OUTPUTS,
    VALID_OUTPUTS,
    resolve_output,
)
from mammoth_cli.runtime import executor, validate
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_extra_args
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals

OUTPUT_MODES = VALID_OUTPUTS

# Typer (pinned >=0.27,<0.28) ships a *vendored* click fork (``typer._click``)
# and does NOT depend on the external ``click`` package. Command resolution
# raises that fork's ``UsageError``/``Abort``, so the interceptor keys on the
# vendored classes only -- importing the external ``click`` here would add a
# phantom dependency that is absent from a clean wheel install.
_USAGE_ERRORS: tuple[type[BaseException], ...] = (_typer_click_exceptions.UsageError,)
_ABORT_ERRORS: tuple[type[BaseException], ...] = (_typer_click_exceptions.Abort,)


def _output_mode_from_argv(argv: Sequence[str] | None) -> str:
    """Recover the requested ``--output`` mode from raw argv tokens.

    Used when a Click ``UsageError`` is raised *before* the per-command option
    is parsed (an unknown command, an unexpected argument, a bad option value),
    so the top-level error renderer can still honor the machine-output contract.
    Defaults to the same ``auto`` default the ``--output`` option declares, then
    resolves it against whether stdout is a terminal — so a piped invocation
    gets the machine envelope even for an error raised before option parsing.
    """
    tokens = list(argv) if argv is not None else sys.argv[1:]
    mode = OUTPUT_AUTO
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--output", "-o"):
            if index + 1 < len(tokens):
                mode = tokens[index + 1]
            index += 2
            continue
        if token.startswith("--output="):
            mode = token.split("=", 1)[1]
        elif token.startswith("-o") and len(token) > 2:
            mode = token[2:]
        index += 1
    return resolve_output(mode, is_tty=sys.stdout.isatty())


class _EnvelopeGroup(TyperGroup):
    """Root group that renders Click usage errors as the machine error envelope.

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

    def main(self, *args: Any, **kwargs: Any) -> Any:
        if not kwargs.get("standalone_mode", True):
            return super().main(*args, **kwargs)
        kwargs["standalone_mode"] = False
        try:
            result = super().main(*args, **kwargs)
        except _USAGE_ERRORS as error:
            argv = kwargs.get("args")
            if argv is None:
                argv = args[0] if args else None
            self._render_usage_error(error, argv)
            raise SystemExit(getattr(error, "exit_code", EXIT_USAGE)) from None
        except _ABORT_ERRORS:
            typer.echo("Aborted!", err=True)
            raise SystemExit(1) from None
        # Under standalone_mode=False a normal return is either None (success) or
        # an int exit code (a click Exit, e.g. --help/--version or our own
        # CliError path). Re-raise SystemExit so both the console script and the
        # in-process test runner observe the exit status as before.
        raise SystemExit(result if isinstance(result, int) else 0)

    def _render_usage_error(self, error: Any, argv: Sequence[str] | None) -> None:
        """Emit a usage error as the JSON envelope (machine) or Click prose (human).

        A *missing required argument* is reported with the stable
        ``missing_argument`` code that the handler-level ``_require_*`` helpers
        also raise, so the machine error contract is identical whether a required
        positional is now enforced natively by Typer (a Click-layer
        ``MissingParameter``, the common case since positionals are declared with
        their real requiredness) or by a handler that reads it from
        ``extra_args``. Every other usage error (unknown command, bad option or
        argument value, an id read as a subcommand) stays ``usage_error``.
        """
        if _output_mode_from_argv(argv) in MACHINE_OUTPUTS:
            missing = isinstance(error, _typer_click_exceptions.MissingParameter)
            executor.emit_error(
                CliError(
                    code="missing_argument" if missing else "usage_error",
                    message=error.format_message(),
                    exit_status=EXIT_USAGE,
                    hint="Check the command schema with 'mammoth schema get'.",
                ),
                machine=True,
            )
        else:
            error.show()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit(0)


def _shared_option_params() -> list[inspect.Parameter]:
    """Build the global-option parameters shared by every command.

    These are the machine-output and agent-mode options every command exposes.
    They are declared once, as :class:`inspect.Parameter`s, so a dynamically
    synthesized command signature can splice them in after any positionals while
    keeping the option contract in exactly one place.
    """
    p = inspect.Parameter

    def opt(name: str, default: Any, annotation: Any) -> inspect.Parameter:
        return p(name, p.POSITIONAL_OR_KEYWORD, default=default, annotation=annotation)

    return [
        opt(
            "output",
            OUTPUT_AUTO,
            Annotated[
                str,
                typer.Option(
                    "--output",
                    "-o",
                    help="Output format. 'auto' picks a table on a terminal, JSON when piped.",
                    metavar="|".join(SELECTABLE_OUTPUTS),
                ),
            ],
        ),
        opt(
            "profile",
            None,
            Annotated[str | None, typer.Option("--profile", help="Credential profile name.")],
        ),
        opt(
            "project",
            None,
            Annotated[int | None, typer.Option("--project", help="Active project id override.")],
        ),
        opt(
            "timeout",
            None,
            Annotated[float | None, typer.Option("--timeout", help="Per-request timeout seconds.")],
        ),
        opt(
            "job_timeout",
            None,
            Annotated[
                float | None, typer.Option("--job-timeout", help="Job wait timeout seconds.")
            ],
        ),
        opt(
            "pipeline_timeout",
            None,
            Annotated[
                float | None,
                typer.Option("--pipeline-timeout", help="Pipeline wait timeout seconds."),
            ],
        ),
        opt(
            "color",
            "auto",
            Annotated[
                str, typer.Option("--color", help="Color policy.", metavar="|".join(COLOR_MODES))
            ],
        ),
        opt(
            "no_input",
            False,
            Annotated[bool, typer.Option("--no-input", help="Never prompt; fail instead.")],
        ),
        opt(
            "no_progress",
            False,
            Annotated[bool, typer.Option("--no-progress", help="Never render progress.")],
        ),
        opt(
            "debug",
            False,
            Annotated[bool, typer.Option("--debug", help="Emit diagnostic detail to stderr.")],
        ),
        opt(
            "yes",
            False,
            Annotated[
                bool, typer.Option("--yes", "-y", help="Confirm a mutation without prompting.")
            ],
        ),
        opt(
            "confirm",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--confirm", help="Exact target name required for high-impact actions."
                ),
            ],
        ),
        opt(
            "input_file",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--input", help="Strict JSON/YAML request document, or '-' for stdin."
                ),
            ],
        ),
        opt(
            "input_format",
            None,
            Annotated[
                str | None,
                typer.Option("--input-format", help="Required for stdin: json or yaml."),
            ],
        ),
    ]


_SHARED_OPTION_PARAMS = _shared_option_params()


def _positional_param(spec: PositionalSpec) -> inspect.Parameter:
    """Build a Typer ``Argument`` parameter for one positional spec.

    The argument is declared with the spec's native scalar type (``int`` or
    ``str``) and its native requiredness, so ``--help`` shows the truth: a
    required id renders as ``DATASET_ID`` / ``<int>`` (not an optional
    ``[DATASET_ID]`` / ``<str>``) and Typer enforces both presence and type at
    parse time. A missing or ill-typed *required* positional raises a Click-layer
    usage error that :class:`_EnvelopeGroup` renders as the stable JSON envelope
    under a machine ``--output`` (``missing_argument`` for an absent one,
    ``usage_error`` for a bad value), preserving the machine error contract. An
    *optional* positional keeps a ``None`` default and an ``Optional`` annotation;
    the handler fills it from ``--input`` or resolved context when omitted.
    """
    if spec.required:
        return inspect.Parameter(
            spec.name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[spec.type, typer.Argument(help=spec.help, metavar=spec.metavar)],
        )
    return inspect.Parameter(
        spec.name,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=None,
        annotation=Annotated[
            spec.type | None, typer.Argument(help=spec.help, metavar=spec.metavar)
        ],
    )


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

    def producer() -> tuple[Any, dict[str, Any]]:
        validate.validate_invocation(invocation)
        validate_extra_args(invocation.command_id, invocation.extra_args)
        validate.validate_positional_ids(invocation.command_id, invocation.extra_args)
        handler = HANDLERS.get(invocation.command_id)
        if handler is None:
            record = command_by_id(invocation.command_id)
            sdk_symbol = record.get("sdk_symbol", "") if record else ""
            raise not_implemented_error(invocation.command_id, sdk_symbol)
        return handler(invocation)

    executor.run(invocation.command_id, invocation.output, producer)


def _command_help(command_id: str, record: dict[str, Any] | None) -> str | None:
    """Build a command's user-facing ``--help`` summary.

    Kept deliberately distinct from ``known_restrictions`` (internal review and
    planning notes), which used to be shown here verbatim and leaked plan-document
    prose -- e.g. "specified in plan 02's ... contract" -- into the user-facing
    ``--help``. Instead the summary is the backing handler's docstring first line
    (actionable field guidance such as "``columns``/``mapping`` required"),
    followed by the manifest's runnable ``agent_example``, which already encodes
    every required positional and ``--input`` field. ``known_restrictions``
    remains available to machines through ``schema get``.
    """
    parts: list[str] = []
    handler = HANDLERS.get(command_id) or BESPOKE.get(command_id)
    doc = inspect.getdoc(handler) if handler is not None else None
    if doc:
        # First non-empty line, with RST inline-code backticks flattened to plain
        # quotes so the help reads as prose rather than reStructuredText.
        summary = doc.strip().splitlines()[0].strip().replace("``", "'")
        if summary:
            parts.append(summary)
    example = (record or {}).get("agent_example")
    if example:
        parts.append(f"Example: {example}")
    return "\n\n".join(parts) or None


def build_app() -> typer.Typer:
    """Construct the full Typer command tree from the command manifests."""
    root = typer.Typer(
        name="mammoth",
        help="Command-line interface for the Mammoth Analytics platform.",
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

    records = [r for r in load_commands() if r.get("disposition") != "alias"]
    path_to_command: dict[tuple[str, ...], str] = {
        tuple(r["command_path"].split()): r["command_id"] for r in records
    }
    all_paths = set(path_to_command)
    # A "container command" sits at a node that also has deeper subcommands
    # (e.g. `dataset file-settings`, which also has `... undo` / `... update`).
    containers = {
        tokens
        for tokens in all_paths
        if any(other != tokens and other[: len(tokens)] == tokens for other in all_paths)
    }

    groups: dict[tuple[str, ...], typer.Typer] = {(): root}

    def _make_group(tokens: tuple[str, ...]) -> typer.Typer:
        command_id = path_to_command.get(tokens)
        if command_id is not None:
            # This node is both a group and an invocable command.
            sub = typer.Typer(
                no_args_is_help=False,
                invoke_without_command=True,
                context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
            )
            sub.callback()(_build_leaf(command_id, is_group_callback=True))
        else:
            sub = typer.Typer(
                no_args_is_help=True,
                context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
            )
        return sub

    def _group_for(tokens: tuple[str, ...]) -> typer.Typer:
        if tokens in groups:
            return groups[tokens]
        parent = _group_for(tokens[:-1])
        sub = _make_group(tokens)
        parent.add_typer(sub, name=tokens[-1])
        groups[tokens] = sub
        return sub

    # Ensure every container group exists (parents before children).
    for tokens in sorted(containers, key=len):
        _group_for(tokens)

    # Register every non-container command as a leaf under its parent group.
    # A command_id with a bespoke, fully-typed callback overrides the generic
    # leaf at the same registered name and path; the manifest-driven surface
    # is otherwise unchanged.
    for tokens, command_id in sorted(path_to_command.items()):
        if tokens in containers:
            continue
        record = command_by_id(command_id)
        callback = BESPOKE.get(command_id) or _build_leaf(command_id)
        _group_for(tokens[:-1]).command(
            name=tokens[-1],
            help=_command_help(command_id, record),
            context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
        )(callback)

    return root


def registered_command_paths() -> set[str]:
    """Return every registered command path by walking the built Typer tree.

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
            if sub is None or not group.name:
                continue
            node = (*prefix, group.name)
            if getattr(sub.info, "invoke_without_command", False) and sub.registered_callback:
                paths.add(" ".join(node))
            walk(sub, node)

    walk(build_app(), ())
    return paths


@cache
def _root_click_command() -> Any:
    """Build (once) and cache the fully resolved Click command tree.

    ``typer.main.get_command`` walks and converts every registered Typer
    sub-app into its Click representation; over the full manifest-driven tree
    that is expensive enough that recomputing it per lookup made a full sweep
    over every command (see the contract test) take minutes. Cached because
    the tree is fixed for the process lifetime (:data:`app` is built once at
    import time).
    """
    return typer.main.get_command(app)


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
