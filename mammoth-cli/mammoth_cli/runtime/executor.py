"""Shared success/error envelope emission for every command path.

Both the generic manifest leaf (``app.py``) and every bespoke command
callback call :func:`run` so there is exactly one code path from a handler's
``(data, meta_extra)`` result (or a raised :class:`CliError`) to rendered
stdout/stderr and the process exit status. Keeping this in one module means a
bespoke command and a not-yet-implemented generic command always behave
identically for machine output, error shape, and exit code.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

import typer

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.output.policy import MACHINE_OUTPUTS
from mammoth_cli.output.render import render

Producer = Callable[[], tuple[Any, dict[str, Any]]]


def emit_success(
    command_id: str,
    data: Any,
    output: str,
    *,
    profile: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
    pagination: dict[str, Any] | None = None,
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
    """
    meta = Meta(
        command=command_id.replace(".", " "),
        profile=profile,
        workspace_id=workspace_id,
        project_id=project_id,
        pagination=pagination,
    )
    envelope = Result(data=data, meta=meta).to_envelope()
    render(envelope, output=output)


def emit_error(error: CliError, *, machine: bool) -> None:
    """Render one error envelope to stderr.

    Args:
        error: The classified error to render.
        machine: Whether the current output mode is machine-readable (``json``
            or ``ndjson``). Machine mode renders the versioned JSON error
            envelope; human mode renders a short readable message with any
            recovery commands.
    """
    if machine:
        render(error.to_envelope(), output="json", stream=sys.stderr)
        return
    message = error.message
    if error.hint:
        message = f"{message}\n{error.hint}"
    typer.echo(f"error [{error.code}]: {message}", err=True)
    for command in error.recovery_commands:
        typer.echo(f"  try: {command}", err=True)


def run(command_id: str, output: str, producer: Producer) -> None:
    """Run one command's producer and emit its envelope.

    Args:
        command_id: The manifest command id driving this invocation.
        output: The resolved ``--output`` mode.
        producer: A zero-argument callable returning ``(data, meta_extra)``.
            ``meta_extra`` is forwarded as keyword arguments to
            :func:`emit_success` (``profile``, ``workspace_id``,
            ``project_id``, ``pagination``).

    Raises:
        typer.Exit: Always, when ``producer`` raises a :class:`CliError`, with
            the error's mapped exit status. On success the function returns
            normally after rendering the success envelope.
    """
    try:
        data, meta_extra = producer()
        emit_success(command_id, data, output, **meta_extra)
    except CliError as error:
        emit_error(error, machine=output in MACHINE_OUTPUTS)
        raise typer.Exit(error.exit_status) from None
