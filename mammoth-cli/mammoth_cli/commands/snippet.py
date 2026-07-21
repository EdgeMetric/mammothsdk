"""Handlers for the ``snippet`` command family.

Most snippet operations act on a single snippet by id with no project scope
(``get``, ``delete``, ``duplicate``, ``dependencies``, ``rerun``, ``update``);
``create`` and ``list`` are project-scoped, taking the project id from
``--project`` or the active project. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project

HandlerResult = tuple[Any, dict[str, Any]]

_UPDATE_OPTIONAL = ("name", "code", "language", "description", "group_id")
_LIST_OPTIONAL = ("limit", "offset", "search", "group_id", "sort")
_CREATE_OPTIONAL = ("description", "group_id", "scope")


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code="sdk_symbol_unresolved",
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
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Parse the first positional argument as an int, or raise a usage error."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code="missing_field",
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a snippet command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def snippet_create(invocation: Invocation) -> HandlerResult:
    """Create a snippet. Name comes from a positional or the ``name`` field."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    name = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("name")
    if not name:
        raise CliError(
            code="missing_argument",
            message="A snippet name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    code = _require_field(document, "code")
    language = _require_field(document, "language")
    kwargs: dict[str, Any] = {
        "name": name,
        "code": code,
        "language": language,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, _CREATE_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def snippet_delete(invocation: Invocation) -> HandlerResult:
    """Delete one snippet by id. Prompt or ``--yes`` required."""
    snippet_id = _require_int_positional(invocation, "snippet id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete snippet {snippet_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), snippet_id=snippet_id)
    return data, _meta(invocation, auth.workspace_id, None)


def snippet_dependencies(invocation: Invocation) -> HandlerResult:
    """Report dependencies for one snippet by id."""
    snippet_id = _require_int_positional(invocation, "snippet id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), snippet_id=snippet_id)
    return data, _meta(invocation, auth.workspace_id, None)


def snippet_duplicate(invocation: Invocation) -> HandlerResult:
    """Duplicate one snippet by id."""
    snippet_id = _require_int_positional(invocation, "snippet id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), snippet_id=snippet_id)
    return data, _meta(invocation, auth.workspace_id, None)


def snippet_get(invocation: Invocation) -> HandlerResult:
    """Get one snippet by id."""
    snippet_id = _require_int_positional(invocation, "snippet id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), snippet_id=snippet_id)
    return data, _meta(invocation, auth.workspace_id, None)


def snippet_list(invocation: Invocation) -> HandlerResult:
    """List snippets in the active project."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, _LIST_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def snippet_rerun(invocation: Invocation) -> HandlerResult:
    """Rerun one snippet by id."""
    snippet_id = _require_int_positional(invocation, "snippet id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), snippet_id=snippet_id)
    return data, _meta(invocation, auth.workspace_id, None)


def snippet_update(invocation: Invocation) -> HandlerResult:
    """Update a snippet's fields. Snippet id is positional; fields come from ``--input``."""
    snippet_id = _require_int_positional(invocation, "snippet id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"snippet_id": snippet_id}
    _forward_optional(document, kwargs, _UPDATE_OPTIONAL)
    if len(kwargs) == 1:
        raise CliError(
            code="missing_field",
            message="Provide at least one field to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)
