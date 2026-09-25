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
        api_key=None, api_secret=None, workspace_id=7, api_token="...",
        server_prefix="app", headers={"Cookie": "..."},
    )
    envelope = invoke(["project", "list"], login=login)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mammoth_cli.app import _ABORT_ERRORS, _USAGE_ERRORS, _root_click_command
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.errors.envelope import EXIT_API, EXIT_INTERRUPT, EXIT_USAGE, CliError
from mammoth_cli.runtime import embedded


def invoke(
    args: Sequence[str],
    *,
    login: ExplicitLogin,
    project_id: int | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Run ``mammoth <args>`` as ``login`` and return its envelope.

    Args:
        args: The command line after ``mammoth``, for example
            ``["view", "data", "get", "12"]``.
        login: The credentials, endpoint and extra headers for this call.
        project_id: The active project, sent as ``--project`` unless ``args``
            already names one.
        timeout: Per-request timeout in seconds, sent as ``--timeout`` unless
            ``args`` already sets one.

    Returns:
        The success envelope (``data`` + ``meta``) or the error envelope
        (``error``). A CLI error is returned, never raised.
    """
    argv = _argv(args, project_id=project_id, timeout=timeout)
    call = embedded.EmbeddedCall(login=login)
    token = embedded.enter(call)
    try:
        _run(argv)
    finally:
        embedded.leave(token)
    if call.envelopes:
        return call.envelopes[-1]
    return _error("no_output", "This command printed text only (help or version).", EXIT_USAGE)


def _argv(args: Sequence[str], *, project_id: int | None, timeout: float | None) -> list[str]:
    """``args`` plus the options an embedded call always runs with."""
    argv = list(args)
    if project_id is not None and not _has_option(argv, "--project"):
        argv += ["--project", str(project_id)]
    if timeout is not None and not _has_option(argv, "--timeout"):
        argv += ["--timeout", str(timeout)]
    # Last, so they win over any output or input option in ``args``.
    return [*argv, "--output", "json", "--no-input"]


def _has_option(argv: Sequence[str], name: str) -> bool:
    return any(token == name or token.startswith(f"{name}=") for token in argv)


def _run(argv: list[str]) -> None:
    """Run the command; every outcome ends as a captured envelope."""
    root = _root_click_command()
    try:
        root.main(args=argv, prog_name="mammoth", standalone_mode=False)
    except _USAGE_ERRORS as error:
        root.render_usage_error(error, argv)
    except _ABORT_ERRORS:
        embedded.capture(_error("aborted", "The command was aborted.", EXIT_INTERRUPT))
    except SystemExit:
        return
    except Exception as exc:  # noqa: BLE001 -- the host gets an envelope, never a traceback
        embedded.capture(_error("internal_error", f"{type(exc).__name__}: {exc}", EXIT_API))


def _error(code: str, message: str, exit_status: int) -> dict[str, Any]:
    return CliError(code=code, message=message, exit_status=exit_status).to_envelope()
