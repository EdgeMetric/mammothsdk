"""Handlers for the ``schedule`` command family (project-scoped).

Every schedule operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and schedule ids come from a
positional argument. The structured ``spec`` (schedule creation) and ``patch``
(schedule update) fields come from the strict ``--input`` document and are
forwarded unchanged — this layer never constructs or imports the SDK's
``ScheduleCreateSpec``/``SchedulePatchItem`` types directly. Handlers dispatch
through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the public SDK method named by the command's reviewed manifest
``sdk_symbol``.
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
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The dotted SDK symbol recorded in the reviewed manifest.

    Raises:
        CliError: ``sdk_symbol_unresolved`` when no symbol is recorded.
    """
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument, parsed as a required int.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The parsed integer id.

    Raises:
        CliError: ``missing_argument`` when no positional was given;
            ``invalid_argument`` when it is not an integer.
    """
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
    """Return a required field from the ``--input`` document, or raise usage.

    Args:
        document: The parsed ``--input`` document, or None when absent.
        field: The required field name.

    Returns:
        The field's value.

    Raises:
        CliError: ``missing_field`` when the document is absent or lacks
            ``field``.
    """
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
    """Copy each of ``fields`` present in ``document`` into ``kwargs``, unchanged.

    Args:
        document: The parsed ``--input`` document.
        kwargs: The keyword-argument mapping being built for the SDK call.
        fields: The optional field names to forward when present.
    """
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a schedule command.

    Args:
        invocation: The current command's resolved global options.
        workspace_id: The authenticated workspace id.
        project_id: The active project id.

    Returns:
        The envelope metadata mapping.
    """
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def schedule_list(invocation: Invocation) -> HandlerResult:
    """List schedules in the active project. ``limit``/``offset`` are optional."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "offset"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def schedule_get(invocation: Invocation) -> HandlerResult:
    """Get one schedule by id in the active project."""
    project_id = require_project(invocation)
    schedule_id = _require_int_positional(invocation, "schedule id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), schedule_id=schedule_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def schedule_create(invocation: Invocation) -> HandlerResult:
    """Create a schedule. The required ``spec`` field comes from ``--input``.

    Always requires ``--yes``.
    """
    project_id = require_project(invocation)
    document = invocation.load_input()
    spec = _require_field(document, "spec")
    enforce_confirmation(invocation, policy=POLICY_YES_ALWAYS, action="create a schedule")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), spec=spec, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def schedule_update(invocation: Invocation) -> HandlerResult:
    """Apply JSON-patch operations to one schedule. Always requires ``--yes``.

    Schedule id is positional; the non-empty ``patch`` list comes from the
    ``--input`` document.
    """
    project_id = require_project(invocation)
    schedule_id = _require_int_positional(invocation, "schedule id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update schedule {schedule_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), schedule_id=schedule_id, patch=patch, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def schedule_delete(invocation: Invocation) -> HandlerResult:
    """Delete one schedule by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    schedule_id = _require_int_positional(invocation, "schedule id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete schedule {schedule_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), schedule_id=schedule_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)
