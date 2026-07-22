"""Handlers for the ``parameter`` command family (workspace-scoped, project-optional).

Parameters and parameter groups belong to the authenticated workspace but may
optionally be scoped to a project via ``--project`` or the active project;
most SDK signatures in this family accept an optional ``project_id`` and fall
back to a workspace-level default when it is absent. The one exception is
``parameter rerun-all-stale``, whose SDK signature requires a project id.
Handlers dispatch through the generic
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
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


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


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Parse the first positional argument as an int, or raise ``missing_argument``."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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
    """Copy each present field from ``document`` into ``kwargs``, unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _add_scoped_project(invocation: Invocation, kwargs: dict[str, Any]) -> None:
    """Add ``project_id`` to ``kwargs`` when a project is resolved, else omit it."""
    project_id = resolved_project(invocation)
    if project_id is not None:
        kwargs["project_id"] = project_id


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a parameter command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": resolved_project(invocation),
    }


def parameter_create(invocation: Invocation) -> HandlerResult:
    """Create a parameter. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
    name = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A parameter name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    param_type = _require_field(document, "param_type")
    value = _require_field(document, "value")
    kwargs: dict[str, Any] = {"name": name, "param_type": param_type, "value": value}
    _forward_optional(document, kwargs, ("description", "group_id", "scope"))
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one parameter by id. Prompt or ``--yes`` required."""
    parameter_id = _require_int_positional(invocation, "parameter id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete parameter {parameter_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), parameter_id=parameter_id)
    return data, _meta(invocation, auth.workspace_id)


def parameter_dependencies(invocation: Invocation) -> HandlerResult:
    """Report what depends on one parameter by id."""
    parameter_id = _require_int_positional(invocation, "parameter id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), parameter_id=parameter_id)
    return data, _meta(invocation, auth.workspace_id)


def parameter_duplicate(invocation: Invocation) -> HandlerResult:
    """Duplicate one parameter by id."""
    parameter_id = _require_int_positional(invocation, "parameter id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), parameter_id=parameter_id)
    return data, _meta(invocation, auth.workspace_id)


def parameter_get(invocation: Invocation) -> HandlerResult:
    """Get one parameter by id."""
    parameter_id = _require_int_positional(invocation, "parameter id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), parameter_id=parameter_id)
    return data, _meta(invocation, auth.workspace_id)


def parameter_list(invocation: Invocation) -> HandlerResult:
    """List parameters, optionally filtered and scoped to a project."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("limit", "offset", "search", "group_id", "sort"))
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_rerun(invocation: Invocation) -> HandlerResult:
    """Rerun one parameter's computation by id."""
    parameter_id = _require_int_positional(invocation, "parameter id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), parameter_id=parameter_id)
    return data, _meta(invocation, auth.workspace_id)


def parameter_rerun_all_stale(invocation: Invocation) -> HandlerResult:
    """Rerun every stale parameter in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id)


def parameter_update(invocation: Invocation) -> HandlerResult:
    """Update a parameter. Parameter id is positional; fields come from ``--input``."""
    parameter_id = _require_int_positional(invocation, "parameter id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"parameter_id": parameter_id}
    _forward_optional(document, kwargs, ("name", "value", "param_type", "description", "group_id"))
    if len(kwargs) == 1:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=(
                "Provide at least one of 'name', 'value', 'param_type', 'description', "
                "or 'group_id' to update."
            ),
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_group_create(invocation: Invocation) -> HandlerResult:
    """Create a parameter group. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
    name = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A parameter group name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    kwargs: dict[str, Any] = {"name": name}
    _forward_optional(document, kwargs, ("color",))
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_group_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one parameter group by id. Prompt or ``--yes`` required."""
    group_id = _require_int_positional(invocation, "group id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete parameter group {group_id}"
    )
    kwargs: dict[str, Any] = {"group_id": group_id}
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_group_list(invocation: Invocation) -> HandlerResult:
    """List parameter groups, optionally scoped to a project."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("limit", "offset", "sort"))
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_group_reorder(invocation: Invocation) -> HandlerResult:
    """Reorder parameter groups. ``order`` (a list of group ids) is required."""
    document = invocation.load_input()
    order = _require_field(document, "order")
    kwargs: dict[str, Any] = {"order": order}
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def parameter_group_update(invocation: Invocation) -> HandlerResult:
    """Update a parameter group. Group id is positional; fields come from ``--input``."""
    group_id = _require_int_positional(invocation, "group id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"group_id": group_id}
    _forward_optional(document, kwargs, ("name", "color"))
    if len(kwargs) == 1:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="Provide at least one of 'name' or 'color' to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    _add_scoped_project(invocation, kwargs)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)
