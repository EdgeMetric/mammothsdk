"""Handlers for the ``client-app`` command family.

Client apps are workspace-level API credentials: none of the reviewed manifest
signatures in this family take a ``project_id`` argument, so no handler here
requires an active project. The (optional) active project is still reported
in the envelope metadata for context, mirroring the read handlers in
:mod:`mammoth_cli.commands.file`. The family's resource id is ``client_key``,
a string identifier — never a secret — read from the first CLI positional.
No command in this family accepts application secret material as input at
all: ``create`` only takes a name and description, and ``update`` forwards an
opaque ``patch_request`` document from ``--input``, never a positional.
Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The dotted SDK symbol recorded in the command's manifest entry.

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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The first extra argument, or None when there is none.
    """
    return invocation.extra_args[0] if invocation.extra_args else None


def _require_string_positional(invocation: Invocation, name: str) -> str:
    """Return the required first positional argument, or raise usage.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error text.

    Returns:
        The first extra argument.

    Raises:
        CliError: ``missing_argument`` when no positional was given.
    """
    value = _string_positional(invocation)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage.

    Args:
        document: The parsed ``--input`` request document, or None.
        field: The required field name.

    Returns:
        The field's value.

    Raises:
        CliError: ``missing_field`` when the document or field is absent.
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
        document: The parsed ``--input`` request document.
        kwargs: The keyword arguments accumulator to update in place.
        fields: The optional field names to forward when present.
    """
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a client-app command.

    Args:
        invocation: The current command's resolved global options.
        workspace_id: The authenticated client's resolved workspace id.
        project_id: The active project id, or None when unset.

    Returns:
        The envelope metadata mapping.
    """
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def client_app_list(invocation: Invocation) -> HandlerResult:
    """List client apps in the active workspace (requires an admin role)."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("limit", "offset", "fields", "sort"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def client_app_get(invocation: Invocation) -> HandlerResult:
    """Get one client app by its client key."""
    client_key = _require_string_positional(invocation, "client key")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"client_key": client_key}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def client_app_create(invocation: Invocation) -> HandlerResult:
    """Create a client app. Name comes from a positional or the ``app_name`` field.

    High-impact: this mints a new set of API credentials in the workspace, so
    it requires ``--yes --confirm APP_NAME``. No secret material is ever
    accepted as input here; any tokens are returned by the API, not supplied.
    """
    document = invocation.load_input() or {}
    app_name = _string_positional(invocation) or document.get("app_name")
    if not app_name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A client app name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or an 'app_name' input field.",
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"create client app '{app_name}'",
        target=str(app_name),
    )
    kwargs: dict[str, Any] = {"app_name": app_name}
    _forward_optional(document, kwargs, ("description",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def client_app_update(invocation: Invocation) -> HandlerResult:
    """Apply a patch request to one client app. Client key is positional.

    High-impact: requires ``--yes --confirm CLIENT_KEY``. The patch document
    is a required ``--input`` field (``patch_request``); no secret material
    is ever taken from a positional argument.
    """
    client_key = _require_string_positional(invocation, "client key")
    document = invocation.load_input()
    patch_request = _require_field(document, "patch_request")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"update client app {client_key}",
        target=str(client_key),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), client_key=client_key, patch_request=patch_request)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def client_app_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one client app by its client key. Prompt or ``--yes`` required."""
    client_key = _require_string_positional(invocation, "client key")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete client app {client_key}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), client_key=client_key)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
