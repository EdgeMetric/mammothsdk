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
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

HandlerResult = tuple[Any, dict[str, Any]]

_WAIT_OPTIONAL = ("timeout", "poll_interval")


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


def job_wait(invocation: Invocation) -> HandlerResult:
    """Block until one job completes, or raise on failure/timeout.

    The job id is a positional argument; optional ``timeout`` and
    ``poll_interval`` fields are forwarded from the ``--input`` document when
    present.
    """
    job_id = _require_int_positional(invocation, "job id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"job_id": job_id}
    _forward_optional(document, kwargs, _WAIT_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


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
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)
