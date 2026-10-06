"""Handlers for the ``job`` command family (workspace-scoped, no project).

Jobs are workspace-scoped background tasks tracked by an integer id. ``job get``
and ``job wait`` take a single job id from the first positional argument;
``job get-many`` and ``job wait-many`` take a list of job ids from the strict
``--input`` document. The ``wait`` commands additionally forward optional
``timeout``/``poll_interval`` fields from that document when present. Every
handler dispatches through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
    interrupted_error,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services import job_outcome
from mammoth_cli.services.board_values import board_values, dashboard_link

HandlerResult = tuple[Any, dict[str, Any]]

_WAIT_OPTIONAL = ("timeout", "poll_interval")
_DASHBOARD_WAIT_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.wait_for_job_by_url"


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as an int, or raise usage."""
    if not invocation.extra_args:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each of ``fields`` from ``document`` into ``kwargs`` when present."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a job command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def _profile_scoped_recovery(error: CliError, profile: str | None) -> CliError:
    """Keep Ctrl-C recovery pinned to the profile that owns the observed job."""
    if profile:
        # The CLI validates profile names to shell-portable identifier syntax.
        option = f" --profile {profile}"
        error.recovery_commands = [
            f"{command}{option}" if " --profile " not in command else command
            for command in error.recovery_commands
        ]
    return error


def job_get(invocation: Invocation) -> HandlerResult:
    """Get one job's status by id."""
    job_id = _require_int_positional(invocation, "job id")
    # Load even though this immediate read has no request fields.  This keeps
    # strict validation authoritative when a caller supplies ``--input`` (for
    # example, a misleading timeout that only wait commands implement).
    invocation.load_input()
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), job_id=job_id)
    return data, _meta(invocation, auth.workspace_id)


def job_get_many(invocation: Invocation) -> HandlerResult:
    """Get status for several jobs by id, from the ``--input`` document."""
    document = invocation.load_input()
    job_ids = _require_field(document, "job_ids")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), job_ids=job_ids)
    return data, _meta(invocation, auth.workspace_id)


def _wait_call(
    invocation: Invocation, document: dict[str, Any], kwargs: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """The SDK symbol and arguments for one job wait.

    A ``dashboard_url`` field switches to the URL-scoped wait: jobs dispatched
    by published-dashboard routes are unreadable through ``GET /jobs/{id}``.
    """
    if "dashboard_url" not in document:
        return _symbol(invocation), kwargs
    return _DASHBOARD_WAIT_SYMBOL, {**kwargs, "url": document["dashboard_url"]}


def _wait_result(job_id: int, job: Any) -> dict[str, Any]:
    """The ``job wait`` success payload: the job's response, plus what the job was."""
    data: dict[str, Any] = {"status": "success", "job_id": job_id}
    if isinstance(job, dict):
        data.update({key: job[key] for key in ("operation", "path") if job.get(key) is not None})
        data["result"] = job.get("response", job)
    else:
        data["result"] = job
    return data


def job_wait(invocation: Invocation) -> HandlerResult:
    """Wait for one job and report success, failure, or still running (15 min default).

    The job id is a positional argument; optional ``timeout``, ``poll_interval``
    and ``dashboard_url`` (a published dashboard's URL slug) fields are read from
    the ``--input`` document. Success returns ``{status, job_id, result}``; a
    failed job is a ``job_failed`` error with its reason; a wait that runs out is
    a ``timeout`` error, or with ``--return-running`` ``{status: running, job_id,
    resume}``.
    """
    job_id = _require_int_positional(invocation, "job id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"job_id": job_id}
    _forward_optional(document, kwargs, _WAIT_OPTIONAL)
    symbol, kwargs = _wait_call(invocation, document, kwargs)
    try:
        with open_service(invocation) as (service, auth):
            data = _with_board(service, auth, _wait_result(job_id, service.call(symbol, **kwargs)))
            data = _with_outcome(service, data)
    except KeyboardInterrupt as exc:
        # Keep the explicit handle even when the polling implementation raises
        # a bare SIGINT.  A caller can inspect/resume it without replaying the
        # operation that produced the job.
        raise _profile_scoped_recovery(
            interrupted_error(
                job_id=job_id,
                operation_state="running",
                phase="polling",
                details={"interrupted": True},
            ),
            invocation.profile,
        ) from exc
    return data, _meta(invocation, auth.workspace_id)


_DATAVIEW_GET_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.get"


def _with_outcome(service: Any, data: dict[str, Any]) -> dict[str, Any]:
    """Add ``outcome``: the state of what the finished job acted on.

    A job on a view gets that view's rows, columns and state (one read); a project copy
    gets its copied counts and per-view runs (no read). The job succeeded either way, so
    a view that cannot be read is an ``outcome_error``, never a failed wait.
    """
    result = job_outcome.with_derived_datasets(data.get("result"))
    data = {**data, "result": result} if result is not data.get("result") else data
    copied = job_outcome.copy_outcome(result)
    if copied is not None and data.get("operation") == job_outcome.COPY_PROJECT_OPERATION:
        return {**data, "outcome": copied}
    target = job_outcome.view_target(data)
    if target is None:
        return data
    try:
        record = service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=target.dataset_id,
            dataview_id=target.view_id,
            project_id=target.project_id,
        )
    except CliError as error:
        return {**data, "outcome_error": f"{error.code}: {error.message}"}
    return {**data, "outcome": job_outcome.view_outcome(record, target)}


#: Jobs that build a board. A build that outlived its own wait hands back a running
#: job; waiting on it here must report what the build would have: the board's link
#: and its evaluated numbers (UQA-RT2-05).
_BOARD_BUILD_OPERATIONS = frozenset({"generate_dashboard_v3"})


def _with_board(service: Any, auth: Any, data: dict[str, Any]) -> dict[str, Any]:
    """Add ``dashboard_link`` and the board's evaluated numbers to a finished board build."""
    result = data.get("result")
    board = result.get("id") if isinstance(result, dict) else None
    if data.get("operation") not in _BOARD_BUILD_OPERATIONS or not isinstance(board, int):
        return data
    return {
        **data,
        "dashboard_link": dashboard_link(auth.base_url, auth.workspace_id, board),
        "values": board_values(service, board),
    }


def job_wait_many(invocation: Invocation) -> HandlerResult:
    """Block until several jobs complete, or raise on failure/timeout.

    The job ids come from the required ``job_ids`` field of the ``--input``
    document; optional ``timeout`` and ``poll_interval`` fields are forwarded
    from the same document when present.
    """
    document = invocation.load_input()
    job_ids = _require_field(document, "job_ids")
    kwargs: dict[str, Any] = {"job_ids": job_ids}
    assert document is not None
    _forward_optional(document, kwargs, _WAIT_OPTIONAL)
    try:
        with open_service(invocation) as (service, auth):
            data = service.call(_symbol(invocation), **kwargs)
    except KeyboardInterrupt as exc:
        job_ids_for_recovery = job_ids if isinstance(job_ids, list) else str(job_ids)
        raise _profile_scoped_recovery(
            interrupted_error(
                job_id=job_ids_for_recovery,
                operation_state="running",
                phase="polling",
                details={"interrupted": True, "job_ids": job_ids_for_recovery},
            ),
            invocation.profile,
        ) from exc
    return data, _meta(invocation, auth.workspace_id)
