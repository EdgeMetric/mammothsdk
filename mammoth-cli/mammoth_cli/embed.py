"""Run one CLI command in-process and return its envelope.

For a host (for example a server-side agent) that runs commands for its own
signed-in users. Each call carries its own login, is forced to machine output
and no prompts, writes nothing to stdout or stderr, and returns the success or
error envelope as a dict. Calls are safe to run concurrently in threads: the
login and the captured envelope live in a context variable
(:mod:`mammoth_cli.runtime.embedded`), and the update check, the run log and
saved profiles are not used.

Example::

    from mammoth_cli.context.resolver import ExplicitLogin
    from mammoth_cli.embed import invoke

    login = ExplicitLogin(
        api_key=None, api_secret=None, api_token="...",
        server_prefix="app", headers={"Cookie": "..."},
    )
    envelope = invoke(["project", "list"], login=login)

    # Several commands as one user, over one connection, stopping at the first failure:
    envelopes = invoke_many([["project", "list"], ["view", "list"]], login=login)
"""

from __future__ import annotations

import copy
import time
from collections.abc import Sequence
from typing import Any

from typer._click.core import Command, Context

from mammoth_cli import __version__
from mammoth_cli.app import _ABORT_ERRORS, _USAGE_ERRORS, _root_click_command
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.errors.envelope import (
    CODE_SKIPPED,
    EXIT_API,
    EXIT_INTERRUPT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.shared import forget_reads, shared_services


def invoke(
    args: Sequence[str],
    *,
    login: ExplicitLogin,
    project_id: int | None = None,
    session_id: str | None = None,
    timeout: float | None = None,
    pipeline_timeout: float | None = None,
    job_timeout: float | None = None,
    return_running: bool = False,
    hide_pending: bool = False,
) -> dict[str, Any]:
    """Run ``mammoth <args>`` as ``login`` and return its envelope.

    Args:
        args: The command line after ``mammoth``, for example
            ``["view", "data", "get", "12"]``.
        login: The credentials, endpoint and extra headers for this call.
        project_id: The active project, sent as ``--project`` unless ``args``
            already names one.
        session_id: The embedding chat's session, sent as ``--session`` unless
            ``args`` already names one; ``agent action`` and ``agent run``
            commands act on it, so the model never has to know its id.
        timeout: Per-request timeout in seconds, sent as ``--timeout`` unless
            ``args`` already sets one.
        pipeline_timeout: Pipeline wait timeout in seconds, sent as
            ``--pipeline-timeout`` unless ``args`` already sets one.
        job_timeout: Job wait timeout in seconds, sent as ``--job-timeout``
            unless ``args`` already sets one.
        return_running: Send ``--return-running`` so a wait that runs out
            returns a ``status: running`` handle instead of a timeout error.
        hide_pending: Refuse the commands the production server does not serve
            yet (``server_status: pending`` in ``schema``) with
            ``pending_server_release``, and leave them out of ``schema list`` and
            ``schema find``. Off by default: a terminal user may target a newer server.

    Returns:
        The success envelope (``data`` + ``meta``) or the error envelope
        (``error``). A CLI error is returned, never raised.
    """
    argv = _argv(
        args,
        project_id=project_id,
        session_id=session_id,
        timeout=timeout,
        pipeline_timeout=pipeline_timeout,
        job_timeout=job_timeout,
        return_running=return_running,
    )
    return _invoke_one(argv, login, hide_pending=hide_pending)


def invoke_many(
    commands: Sequence[Sequence[str]],
    *,
    login: ExplicitLogin,
    project_id: int | None = None,
    session_id: str | None = None,
    timeout: float | None = None,
    pipeline_timeout: float | None = None,
    job_timeout: float | None = None,
    return_running: bool = False,
    hide_pending: bool = False,
    stop_on_error: bool = True,
) -> list[dict[str, Any]]:
    """Run several commands as ``login``, in order, and return one envelope each.

    Each command runs exactly as :func:`invoke` would run it, with the same
    options added, but all of them share one scope: a command opens the
    service (client and connection) the earlier ones already opened for the
    same login and project, the way the lines of a ``mammoth run`` do, instead
    of starting a new connection each. The services close when the batch ends.

    Args:
        commands: The command lines after ``mammoth``, run in this order.
        login: The credentials, endpoint and extra headers for every command.
        project_id: See :func:`invoke`; applied to each command.
        session_id: See :func:`invoke`; applied to each command.
        timeout: See :func:`invoke`; applied to each command.
        pipeline_timeout: See :func:`invoke`; applied to each command.
        job_timeout: See :func:`invoke`; applied to each command.
        return_running: See :func:`invoke`; applied to each command.
        hide_pending: See :func:`invoke`; applied to each command.
        stop_on_error: Stop at the first command that fails (an ``error``
            envelope, or a non-zero ``meta.exit``); each command after it gets
            a ``skipped`` error envelope naming its index and the failed one.
            False runs every command whatever the others return.

    Returns:
        One envelope per command, in the order of ``commands``. A CLI error is
        returned in its command's slot, never raised.
    """
    envelopes: list[dict[str, Any]] = []
    failed: int | None = None
    with shared_services():
        for index, args in enumerate(commands):
            if failed is not None:
                envelopes.append(_timed(_skipped(index, failed), 0))
                continue
            argv = _argv(
                args,
                project_id=project_id,
                session_id=session_id,
                timeout=timeout,
                pipeline_timeout=pipeline_timeout,
                job_timeout=job_timeout,
                return_running=return_running,
            )
            envelope = _invoke_one(argv, login, hide_pending=hide_pending)
            forget_reads()
            envelopes.append(envelope)
            if stop_on_error and _failed(envelope):
                failed = index
    return envelopes


def _invoke_one(
    argv: list[str], login: ExplicitLogin, *, hide_pending: bool = False
) -> dict[str, Any]:
    """Run ``argv`` as ``login`` in its own embedded call; its envelope, with its wall time."""
    started = time.perf_counter()
    call = embedded.EmbeddedCall(login=login, hide_pending=hide_pending)
    embedded.install_stream_guards()
    token = embedded.enter(call)
    try:
        _run(argv)
    finally:
        embedded.leave(token)
    return _timed(_outcome(call), round((time.perf_counter() - started) * 1000))


def _timed(envelope: dict[str, Any], elapsed_ms: int) -> dict[str, Any]:
    """``envelope`` with ``elapsed_ms`` on its ``meta`` (success) or its ``error``."""
    body = envelope.get("error", envelope.get("meta"))
    if isinstance(body, dict):
        body["elapsed_ms"] = elapsed_ms
    return envelope


def _outcome(call: embedded.EmbeddedCall) -> dict[str, Any]:
    """The one envelope a finished call stands for; anything else is an error to fix.

    Text on stdout, or a second envelope, means a command broke the one-envelope
    contract. Returning the one envelope and dropping the rest would hide that, so
    the call fails and says what it saw. Text on stderr (a library's log line, a
    warning) is not a contract break: it never reaches the host's stderr, and rides
    on the envelope as ``meta.stderr`` or ``error.details.stderr`` instead.
    """
    out = "".join(call.stray["stdout"]).strip()[:_STRAY_CHARS]
    err = "".join(call.stray["stderr"]).strip()[:_STRAY_CHARS]
    if out:
        details: dict[str, Any] = {"stdout": out, "envelopes": len(call.envelopes)}
        if err:
            details["stderr"] = err
        return _error(
            "stray_output", "The command wrote text outside its envelope.", EXIT_API, details
        )
    if len(call.envelopes) > 1:
        details = {"envelopes": [_describe(item) for item in call.envelopes]}
        if err:
            details["stderr"] = err
        return _error(
            "multiple_envelopes",
            f"The command produced {len(call.envelopes)} envelopes; it should produce one.",
            EXIT_API,
            details,
        )
    if not call.envelopes:
        return _error("no_output", "This command printed text only (help or version).", EXIT_USAGE)
    envelope = call.envelopes[0]
    if err:
        if isinstance(envelope.get("error"), dict):
            envelope["error"].setdefault("details", {})["stderr"] = err
        elif isinstance(envelope.get("meta"), dict):
            envelope["meta"]["stderr"] = err
    return envelope


#: Stray text kept in the error, as ``mammoth run`` keeps it.
_STRAY_CHARS = 500


def _describe(envelope: dict[str, Any]) -> str:
    """One short label for an envelope: its error code, or ``data``."""
    error = envelope.get("error")
    return str(error.get("code")) if isinstance(error, dict) else "data"


def _failed(envelope: dict[str, Any]) -> bool:
    """An error envelope, or a success whose ``meta.exit`` says it did not take effect."""
    if "error" in envelope:
        return True
    meta = envelope.get("meta")
    return isinstance(meta, dict) and bool(meta.get("exit"))


def _skipped(index: int, failed: int) -> dict[str, Any]:
    return CliError(
        code=CODE_SKIPPED,
        message=f"Command {index} was not run because command {failed} failed.",
        exit_status=EXIT_USAGE,
        details={"index": index, "reason": "earlier_command_failed", "failed_index": failed},
    ).to_envelope()


def _argv(
    args: Sequence[str],
    *,
    project_id: int | None,
    timeout: float | None,
    pipeline_timeout: float | None,
    job_timeout: float | None,
    return_running: bool,
    session_id: str | None = None,
) -> list[str]:
    """``args`` plus the options an embedded call always runs with."""
    argv = list(args)
    if project_id is not None and not _has_option(argv, "--project"):
        argv += ["--project", str(project_id)]
    if session_id is not None and not _has_option(argv, "--session"):
        argv += ["--session", session_id]
    if timeout is not None and not _has_option(argv, "--timeout"):
        argv += ["--timeout", str(timeout)]
    if pipeline_timeout is not None and not _has_option(argv, "--pipeline-timeout"):
        argv += ["--pipeline-timeout", str(pipeline_timeout)]
    if job_timeout is not None and not _has_option(argv, "--job-timeout"):
        argv += ["--job-timeout", str(job_timeout)]
    if return_running and not _has_option(argv, "--return-running"):
        argv.append("--return-running")
    # Last, so they win over any output or input option in ``args``.
    return [*argv, "--output", "json", "--no-input"]


def _has_option(argv: Sequence[str], name: str) -> bool:
    return any(token == name or token.startswith(f"{name}=") for token in argv)


def _run(argv: list[str]) -> None:
    """Run the command; every outcome ends as a captured envelope."""
    root = _root_click_command()
    if _capture_help(root, argv):
        return
    try:
        root.main(args=argv, prog_name="mammoth", standalone_mode=False)
    except _USAGE_ERRORS as error:
        root.render_usage_error(error, argv)
    except _ABORT_ERRORS:
        embedded.capture(_error("aborted", "The command was aborted.", EXIT_INTERRUPT))
    except SystemExit:
        pass
    except Exception as exc:  # noqa: BLE001 -- the host gets an envelope, never a traceback
        embedded.capture(_error("internal_error", f"{type(exc).__name__}: {exc}", EXIT_API))


def _capture_help(root: Command, argv: list[str]) -> bool:
    """Answer ``--help``, ``--version`` and a bare group as an envelope; True when it did.

    Click and Typer print these to standard output, a process-wide stream the
    host shares with every other thread, so they are rendered into a string
    here instead and never printed.
    """
    command_tokens = [token for token in argv if not token.startswith("-")]
    if argv[:1] == ["--version"]:
        text = __version__
    elif "--help" in argv or _is_bare_group(root, command_tokens):
        text = _help_text(root, command_tokens)
    else:
        return False
    meta = Meta(command=" ".join(_resolve(root, command_tokens)[1]) or "mammoth", exit=0)
    embedded.capture(Result(data={"help": text}, meta=meta).to_envelope())
    return True


def _resolve(root: Command, tokens: list[str]) -> tuple[Command, list[str]]:
    """The deepest command ``tokens`` name, and the path of names that reached it."""
    command, path = root, []
    for token in tokens:
        children = getattr(command, "commands", {})
        if token in children:
            command = children[token]
            path.append(token)
    return command, path


def _is_bare_group(root: Command, tokens: list[str]) -> bool:
    """A group named with nothing after it, which Typer answers with its help page."""
    command, path = _resolve(root, tokens)
    return (
        hasattr(command, "commands")
        and bool(getattr(command, "no_args_is_help", False))
        and len(path) == len(tokens)
    )


def _help_text(root: Command, tokens: list[str]) -> str:
    """The plain (no rich markup) help page of the command ``tokens`` name."""
    command, path = _resolve(root, tokens)
    context = Context(root, info_name="mammoth")
    walk: Command = root
    for name in path:
        walk = walk.commands[name]  # type: ignore[attr-defined]
        context = Context(walk, info_name=name, parent=context)
    # A copy, so the shared command tree keeps its rich help for the terminal CLI.
    plain = copy.copy(command)
    plain.rich_markup_mode = None  # type: ignore[attr-defined]
    return plain.get_help(context)


def _error(
    code: str, message: str, exit_status: int, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return CliError(
        code=code, message=message, exit_status=exit_status, details=details or {}
    ).to_envelope()
