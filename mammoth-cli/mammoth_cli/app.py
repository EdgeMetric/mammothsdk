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

from collections.abc import Callable
from typing import Any

import typer

from mammoth_cli import __version__
from mammoth_cli.commands import BESPOKE
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import not_implemented_error
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.output.policy import VALID_OUTPUTS
from mammoth_cli.runtime import executor
from mammoth_cli.runtime.invocation import Invocation

OUTPUT_MODES = VALID_OUTPUTS
COLOR_MODES = ("auto", "always", "never")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit(0)


def _build_leaf(command_id: str, *, is_group_callback: bool = False) -> Callable[..., None]:
    """Return a Typer callback bound to one manifest command id.

    Each callback shares the same global-option signature so ``--help`` for any
    command advertises the machine-output and agent-mode contract. When
    ``is_group_callback`` is set the command sits at a node that also has
    subcommands; the callback then only runs when no subcommand is invoked.
    """

    def leaf(
        ctx: typer.Context,
        output: str = typer.Option(
            "table", "--output", "-o", help="Output format.", metavar="|".join(OUTPUT_MODES)
        ),
        profile: str | None = typer.Option(None, "--profile", help="Credential profile name."),
        project: int | None = typer.Option(None, "--project", help="Active project id override."),
        base_url: str | None = typer.Option(
            None, "--base-url", help="Expert runtime API base-url override."
        ),
        timeout: float | None = typer.Option(
            None, "--timeout", help="Per-request timeout seconds."
        ),
        job_timeout: float | None = typer.Option(
            None, "--job-timeout", help="Job wait timeout seconds."
        ),
        pipeline_timeout: float | None = typer.Option(
            None, "--pipeline-timeout", help="Pipeline wait timeout seconds."
        ),
        color: str = typer.Option(
            "auto", "--color", help="Color policy.", metavar="|".join(COLOR_MODES)
        ),
        no_input: bool = typer.Option(False, "--no-input", help="Never prompt; fail instead."),
        no_progress: bool = typer.Option(False, "--no-progress", help="Never render progress."),
        debug: bool = typer.Option(False, "--debug", help="Emit diagnostic detail to stderr."),
        yes: bool = typer.Option(
            False, "--yes", "-y", help="Confirm a mutation without prompting."
        ),
        confirm: str | None = typer.Option(
            None, "--confirm", help="Exact target name required for high-impact actions."
        ),
        input_file: str | None = typer.Option(
            None, "--input", help="Strict JSON/YAML request document, or '-' for stdin."
        ),
        input_format: str | None = typer.Option(
            None, "--input-format", help="Required for stdin: json or yaml."
        ),
    ) -> None:
        if is_group_callback and ctx.invoked_subcommand is not None:
            return
        invocation = Invocation(
            command_id=command_id,
            output=output,
            profile=profile,
            project=project,
            base_url=base_url,
            timeout=timeout,
            job_timeout=job_timeout,
            pipeline_timeout=pipeline_timeout,
            color=color,
            no_input=no_input,
            no_progress=no_progress,
            debug=debug,
            yes=yes,
            confirm=confirm,
            input_file=input_file,
            input_format=input_format,
            extra_args=list(ctx.args),
        )
        _execute(invocation)

    leaf.__name__ = "cmd_" + command_id.replace(".", "_").replace("-", "_")
    return leaf


def _execute(invocation: Invocation) -> None:
    """Run one command: dispatch to its handler and render the envelope."""

    def producer() -> tuple[Any, dict[str, Any]]:
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


app = build_app()


def main() -> Any:
    """Console-script entry point."""
    return app()


if __name__ == "__main__":  # pragma: no cover
    main()
