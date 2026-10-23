"""The terminal's adapter: render a command's outcome and exit with its status.

Both the generic manifest leaf (``app.py``) and every bespoke command callback call
:func:`run`. It hands the call to :func:`mammoth_cli.runtime.dispatch.dispatch`, which
runs it and returns an :class:`~mammoth_cli.runtime.dispatch.Outcome`, then renders
that outcome to stdout/stderr and raises ``typer.Exit`` with its status. The run log,
update notices and skill refresh live here too: they belong to the terminal, not to
the command. One path from handler to exit status means a bespoke command and a
generic one behave identically for machine output, error shape, and exit code.
"""

from __future__ import annotations

import sys
import traceback

import typer

from mammoth_cli.output.emit import emit_error, emit_success
from mammoth_cli.output.policy import MACHINE_OUTPUTS, VALID_OUTPUTS
from mammoth_cli.runtime import embedded, linecapture, trace, updates
from mammoth_cli.runtime.dispatch import (
    INTERCEPTORS,
    Interceptor,
    Outcome,
    Producer,
    Request,
    dispatch,
    failure,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.journal import journal_writes
from mammoth_cli.runtime.runlog import RunLog

#: The steps around every terminal command: the use case's own, then the journal, inside
#: the shared services so its read before a pipeline edit reuses the command's login.
TERMINAL_INTERCEPTORS: tuple[Interceptor, ...] = (*INTERCEPTORS, journal_writes())


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

    Every API request the command makes names it and carries one invocation id
    (:mod:`mammoth_cli.runtime.trace`), so the server's request log can tell
    commands apart. When ``invocation`` is given a run log is opened for the command
    (:mod:`mammoth_cli.runtime.runlog`): SDK request and job records are
    captured while ``producer`` runs, the outcome is recorded, and an error
    envelope carries ``log_ref`` so the failure can be traced.

    Args:
        command_id: The manifest command id driving this invocation.
        output: The requested or resolved ``--output`` mode.
        producer: A zero-argument callable returning ``(data, meta_extra)``.
            ``meta_extra`` is forwarded as keyword arguments to
            :func:`emit_success` (``profile``, ``workspace_id``,
            ``project_id``, ``pagination``, ``dataset``, ``view``).
        agent_mode: Whether the invocation explicitly disabled interaction
            (``--no-input``). This is used only when an invalid output mode
            needs an error renderer before a concrete machine mode exists.

    Raises:
        typer.Exit: Always, when ``producer`` raises a :class:`CliError`, with
            the error's mapped exit status. On success the function returns
            normally after rendering the success envelope.
    """
    with trace.begin(command_id):
        _run(
            command_id,
            output,
            producer,
            agent_mode=agent_mode,
            profile=profile,
            invocation=invocation,
        )


def _run(
    command_id: str,
    output: str,
    producer: Producer,
    *,
    agent_mode: bool = False,
    profile: str | None = None,
    invocation: Invocation | None = None,
) -> None:
    """:func:`run` inside the invocation's trace."""
    # An invalid mode cannot itself identify a renderer. In redirected/non-TTY
    # execution, or when the caller explicitly selected agent mode, keep the
    # error contract machine-readable. A human TTY still receives the concise
    # diagnostic intended for interactive troubleshooting.
    machine_error = (
        output in MACHINE_OUTPUTS
        or output == "yaml"
        or (output not in VALID_OUTPUTS and (agent_mode or not sys.stdout.isatty()))
    )
    run_log = _open_run_log(command_id, invocation)
    request = Request(command_id, output, producer, invocation=invocation, profile=profile)
    outcome = dispatch(request, TERMINAL_INTERCEPTORS)
    # A ``mammoth run`` line leaves the update notice and the skill refresh to the run itself.
    in_line = linecapture.active()
    if outcome.error is None:
        try:
            _emit_outcome(command_id, output, outcome, in_line=in_line)
        except (Exception, KeyboardInterrupt) as exc:
            outcome = failure(request, exc)
    if outcome.error is not None:
        error = outcome.error
        if run_log is not None:
            error.log_ref = run_log.ref
            run_log.finish(error.exit_status, error_code=error.code, exception=outcome.cause)
        cause = outcome.cause
        if cause is not None and invocation is not None and invocation.debug:
            sys.stderr.write(
                "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
            )
        emit_error(error, machine=machine_error, output=output)
        raise typer.Exit(error.exit_status)
    if run_log is not None:
        run_log.finish(outcome.exit_status)
    if not in_line:
        updates.refresh_in_background(command_id)
        _sync_skill_installs(command_id, output)
    if outcome.exit_status:
        raise typer.Exit(outcome.exit_status)


def _emit_outcome(command_id: str, output: str, outcome: Outcome, *, in_line: bool) -> None:
    """Render a successful outcome, with the cached newer-release notice when there is one."""
    if outcome.running:
        emit_success(command_id, outcome.data, output, **outcome.meta)
        return
    # Read after the command: one that asked PyPI itself (doctor) refreshed the cache,
    # and its envelope must not carry the older answer. No network either way.
    update = None if in_line else updates.available_update(command_id)
    if not outcome.streamed:
        emit_success(
            command_id,
            outcome.data,
            output,
            update_available=update,
            exit_status=outcome.exit_status,
            **outcome.meta,
        )
    updates.emit_hint(update, output=output)


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
    if invocation is None or embedded.active():
        return None
    try:
        traced = trace.current()
        return RunLog.start(
            command_id,
            profile=invocation.profile,
            project_id=invocation.project,
            debug=invocation.debug,
            run_id=traced.invocation_id if traced is not None else None,
        )
    except Exception:
        return None
