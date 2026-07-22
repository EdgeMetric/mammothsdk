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
from collections.abc import Callable
from functools import cache
from typing import Annotated, Any

import typer

from mammoth_cli import __version__
from mammoth_cli.commands import BESPOKE
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import not_implemented_error
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.output.policy import COLOR_MODES, VALID_OUTPUTS
from mammoth_cli.runtime import executor, validate
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_extra_args
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals

OUTPUT_MODES = VALID_OUTPUTS


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
            "table",
            Annotated[
                str,
                typer.Option(
                    "--output", "-o", help="Output format.", metavar="|".join(OUTPUT_MODES)
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
            "base_url",
            None,
            Annotated[
                str | None,
                typer.Option("--base-url", help="Expert runtime API base-url override."),
            ],
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

    The argument is declared optional at the Typer layer (default ``None``)
    regardless of ``spec.required`` so a missing or malformed value flows to the
    handler, which raises the stable ``CliError`` envelope. This preserves the
    machine error contract (a missing required positional still returns the JSON
    error envelope with the same code and exit status) while surfacing the
    argument in ``--help`` and routing the parsed value into ``Invocation``.
    """
    return inspect.Parameter(
        spec.name,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=None,
        annotation=Annotated[str | None, typer.Argument(help=spec.help, metavar=spec.metavar)],
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


def build_app() -> typer.Typer:
    """Construct the full Typer command tree from the command manifests."""
    root = typer.Typer(
        name="mammoth",
        help="Command-line interface for the Mammoth Analytics platform.",
        no_args_is_help=True,
        add_completion=True,
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
            help=(record or {}).get("known_restrictions") or None,
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
