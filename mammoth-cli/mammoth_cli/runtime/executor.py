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

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.output.policy import MACHINE_OUTPUTS, VALID_OUTPUTS
from mammoth_cli.output.render import render
from mammoth_cli.runtime import updates
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.runlog import RunLog
from mammoth_cli.services.mapping import map_sdk_exception

Producer = Callable[[], tuple[Any, dict[str, Any]]]


def _profile_scope_recovery(error: CliError, profile: str | None) -> CliError:
    """Add the selected profile to concrete recovery commands exactly once."""
    if not profile:
        return error
    # Profile names are admitted as ``[A-Za-z0-9][A-Za-z0-9._-]{0,63}``, so
    # this argv fragment is portable across POSIX shells and PowerShell.
    profile_option = f" --profile {profile}"
    error.recovery_commands = [
        f"{command}{profile_option}" if " --profile " not in command else command
        for command in error.recovery_commands
    ]
    return error


def _validate_output(output: str) -> None:
    """Reject an unsupported ``--output`` mode before any work is done.

    Validating up front means an invalid mode fails with a clean usage error
    instead of running the producer (and its network calls) and then crashing
    in the renderer.

    Args:
        output: The requested output mode.

    Raises:
        CliError: ``invalid_output_mode`` with :data:`EXIT_USAGE` when the mode
            is not one the renderer supports.
    """
    if output not in VALID_OUTPUTS:
        raise CliError(
            code="invalid_output_mode",
            message=f"Unsupported output mode '{output}'.",
            exit_status=EXIT_USAGE,
            hint=f"Use one of: {', '.join(VALID_OUTPUTS)}.",
        )


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
    """
    meta = Meta(
        command=command_id.replace(".", " "),
        profile=profile,
        workspace_id=workspace_id,
        project_id=project_id,
        pagination=pagination,
        update_available=update_available,
    )
    envelope = Result(data=data, meta=meta).to_envelope()
    render(envelope, output=output)


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
    if machine:
        render(
            error.to_envelope(),
            output="ndjson" if output == "ndjson" else "json",
            stream=sys.stderr,
        )
        return
    message = error.message
    if error.hint:
        message = f"{message}\n{error.hint}"
    typer.echo(f"error [{error.code}]: {message}", err=True)
    for command in error.recovery_commands:
        typer.echo(f"  try: {command}", err=True)


def run(
    command_id: str,
    output: str,
    producer: Producer,
    *,
    agent_mode: bool = False,
    profile: str | None = None,
    invocation: Invocation | None = None,
) -> None:
    """Run one command's producer and emit its envelope.

    When ``invocation`` is given a run log is opened for the command
    (:mod:`mammoth_cli.runtime.runlog`): SDK request and job records are
    captured while ``producer`` runs, the outcome is recorded, and an error
    envelope carries ``log_ref`` so the failure can be traced.

    Args:
        command_id: The manifest command id driving this invocation.
        output: The requested or resolved ``--output`` mode.
        producer: A zero-argument callable returning ``(data, meta_extra)``.
            ``meta_extra`` is forwarded as keyword arguments to
            :func:`emit_success` (``profile``, ``workspace_id``,
            ``project_id``, ``pagination``).
        agent_mode: Whether the invocation explicitly disabled interaction
            (``--no-input``). This is used only when an invalid output mode
            needs an error renderer before a concrete machine mode exists.

    Raises:
        typer.Exit: Always, when ``producer`` raises a :class:`CliError`, with
            the error's mapped exit status. On success the function returns
            normally after rendering the success envelope.
    """
    # An invalid mode cannot itself identify a renderer. In redirected/non-TTY
    # execution, or when the caller explicitly selected agent mode, keep the
    # error contract machine-readable. A human TTY still receives the concise
    # diagnostic intended for interactive troubleshooting.
    machine_error = output in MACHINE_OUTPUTS or (
        output not in VALID_OUTPUTS and (agent_mode or not sys.stdout.isatty())
    )
    run_log = _open_run_log(command_id, invocation)

    def fail(error: CliError) -> None:
        if run_log is not None:
            error.log_ref = run_log.ref
            run_log.finish(error.exit_status, error_code=error.code)
        emit_error(error, machine=machine_error, output=output)

    # The update notice is read from the daily cache (no network); the cache
    # itself is refreshed only after the command has produced its output.
    update = updates.available_update(command_id)
    try:
        _validate_output(output)
        updates.auto_upgrade(command_id, run_log)
        data, meta_extra = producer()
        emit_success(command_id, data, output, update_available=update, **meta_extra)
        updates.emit_hint(update, output=output)
    except CliError as error:
        fail(error)
        raise typer.Exit(error.exit_status) from None
    except KeyboardInterrupt as exc:
        # Polling can be interrupted after a job handle was observed.  Keep
        # that handle when an SDK exception exposes one; never turn Ctrl-C
        # into a successful/empty result or a Python traceback.
        mapped_error = _profile_scope_recovery(map_sdk_exception(exc), profile)
        fail(mapped_error)
        raise typer.Exit(mapped_error.exit_status) from None
    except Exception as exc:
        # Bespoke handlers should normally cross the SDK service seam, but a
        # malformed response or filesystem fault must still obey the same
        # machine envelope rather than leaking an implementation traceback.
        mapped_error = _profile_scope_recovery(map_sdk_exception(exc), profile)
        fail(mapped_error)
        raise typer.Exit(mapped_error.exit_status) from None
    if run_log is not None:
        run_log.finish(0)
    updates.refresh_if_stale(command_id)
    _sync_skill_installs(command_id, output)


def _sync_skill_installs(command_id: str, output: str) -> None:
    """Refresh installed skill copies once after a CLI upgrade; never fail a command.

    Part of the update machinery, so ``MAMMOTH_NO_UPDATE_CHECK`` turns it off too.
    """
    if not updates.enabled() or command_id.split(".")[0] == "skill":
        return
    try:
        from mammoth_cli import __version__
        from mammoth_cli.skills import installer

        refreshed = installer.sync_owned_installs(__version__)
    except Exception:  # noqa: BLE001 -- a skill refresh must not break the command
        return
    if refreshed and output not in {"json", "ndjson", "yaml"}:
        try:
            sys.stderr.write(
                f"Updated the mammoth-cli skill to match CLI {__version__} in: "
                + ", ".join(refreshed)
                + "\n"
            )
        except OSError:
            return


def _open_run_log(command_id: str, invocation: Invocation | None) -> RunLog | None:
    """Open the run log for ``invocation``; never let logging break a command."""
    if invocation is None:
        return None
    try:
        return RunLog.start(
            command_id,
            profile=invocation.profile,
            project_id=invocation.project,
            debug=invocation.debug,
        )
    except Exception:
        return None
