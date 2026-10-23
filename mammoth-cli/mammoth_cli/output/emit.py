"""Render one success or error envelope: the terminal's output port.

A machine-readable envelope goes to stdout (success) or stderr (error) in the selected
mode. Inside ``mammoth run`` or an embedded call the envelope is handed to that surface's
capture instead of being printed.
"""

from __future__ import annotations

import sys
from typing import Any

import typer

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.output.normalize import normalize
from mammoth_cli.output.render import render
from mammoth_cli.runtime import embedded, linecapture

#: Output modes a person reads; they get the ``Next:`` line on stderr.
_HUMAN_OUTPUTS = frozenset({"table", "plain", "csv"})


def emit_success(
    command_id: str,
    data: Any,
    output: str,
    *,
    profile: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
    pagination: dict[str, Any] | None = None,
    update_available: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    view: dict[str, Any] | None = None,
    opens: list[dict[str, Any]] | None = None,
    next_commands: list[str] | None = None,
    exit_status: int = 0,
) -> None:
    """Render one success envelope to stdout.

    Args:
        command_id: The manifest command id (dotted form); rendered as the
            space-separated command path in the envelope metadata.
        data: The result payload. Normalized recursively before rendering.
        output: The resolved ``--output`` mode.
        profile: The active profile name, if any.
        workspace_id: The resolved workspace id, if any.
        project_id: The resolved project id, if any.
        pagination: Pagination metadata, if any.
        update_available: The cached newer-release notice, if any.
        dataset: ``{"id", "name"}`` of the dataset a data read came from, if any.
        view: ``{"id", "name"}`` of the view a data read came from, if any.
        opens: ``{"kind", "id", "url", "created"}`` of each object a write made or
            changed, if any.
        next_commands: Ready-to-run commands that usually come next, if any.
            Human output (table, plain, csv) also prints them as one ``Next:``
            line on stderr.
        exit_status: The exit status the command ends with, carried as ``meta.exit``.
    """
    meta = Meta(
        command=command_id.replace(".", " "),
        profile=None if embedded.active() else profile,
        workspace_id=workspace_id,
        project_id=project_id,
        pagination=pagination,
        update_available=update_available,
        dataset=dataset,
        view=view,
        opens=opens,
        next_commands=next_commands or None,
        exit=exit_status,
    )
    envelope = Result(data=data, meta=meta).to_envelope()
    if embedded.capture(normalize(envelope)) or linecapture.capture(normalize(envelope)):
        return
    render(envelope, output=output)
    if next_commands and output in _HUMAN_OUTPUTS:
        sys.stderr.write(f"Next: {'; '.join(next_commands)}\n")


def emit_error(error: CliError, *, machine: bool, output: str = "json") -> None:
    """Render one error envelope to stderr.

    Args:
        error: The classified error to render.
        machine: Whether the current output mode is machine-readable (``json``
            or ``ndjson``). Machine mode renders the versioned JSON error
            envelope; human mode renders a short readable message with any
            recovery commands.
        output: The selected machine mode. Only ``ndjson`` selects lifecycle
            framing; all other machine errors retain the JSON envelope.
    """
    if embedded.capture(normalize(error.to_envelope())) or linecapture.capture(
        normalize(error.to_envelope())
    ):
        return
    if machine:
        render(
            error.to_envelope(),
            output=output if output in ("ndjson", "yaml") else "json",
            stream=sys.stderr,
        )
        return
    message = error.message
    if error.hint:
        message = f"{message}\n{error.hint}"
    typer.echo(f"error [{error.code}]: {message}", err=True)
    for command in error.recovery_commands:
        typer.echo(f"  try: {command}", err=True)
