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
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

from typer._click.core import Command, Context

from mammoth_cli import __version__
from mammoth_cli.app import _ABORT_ERRORS, _USAGE_ERRORS, _root_click_command
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.errors.envelope import EXIT_API, EXIT_INTERRUPT, EXIT_USAGE, CliError
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime import embedded


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
    call = embedded.EmbeddedCall(login=login)
    token = embedded.enter(call)
    try:
        _run(argv)
    finally:
        embedded.leave(token)
    if call.envelopes:
        return call.envelopes[-1]
    return _error("no_output", "This command printed text only (help or version).", EXIT_USAGE)


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
    meta = Meta(command=" ".join(_resolve(root, command_tokens)[1]) or "mammoth")
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


def _error(code: str, message: str, exit_status: int) -> dict[str, Any]:
    return CliError(code=code, message=message, exit_status=exit_status).to_envelope()
