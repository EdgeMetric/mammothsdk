"""Handlers for the ``connector`` command family.

``connector get``, ``connector list``, and ``connector active`` describe
connector types and active connections at the workspace level and take no
project scope. Every other command operates inside a resolved project: the
project id comes from ``--project`` or the active project (mirroring
``folder.py``), and the connector/connection/data-source-config keys that
address a specific resource come from positional arguments, in the order they
appear in the command path (``connector_key``, then ``connection_key``, then
``ds_config_key``).

Connection secrets always come from the strict ``--input`` document, never a
positional argument: ``config`` on ``connection create``, ``credentials`` on
``connection update``, and the AI-chat ``body`` payloads. ``connection
create``/``update`` and ``ds-config create``/``update`` cause an external
side effect against a third-party service and always require ``--yes``;
``connection delete`` and the ``ds-config`` deletes are destructive and
accept a prompt or ``--yes``.

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
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]

_DS_CONFIG_CREATE_OPTIONAL = ("query", "file_source", "table", "profile", "validate", "data_sample")


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


def _string_positional_at(invocation: Invocation, index: int, name: str) -> str | None:
    """Return the positional argument at ``index``, or None if absent."""
    if len(invocation.extra_args) <= index:
        return None
    return invocation.extra_args[index]


def _require_string_positional_at(invocation: Invocation, index: int, name: str) -> str:
    """Return the required positional argument at ``index``, or raise usage."""
    value = _string_positional_at(invocation, index, name)
    if not value:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` parsed as an int."""
    raw = _string_positional_at(invocation, index, name)
    if raw is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
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
    """Copy each present field from ``document`` into ``kwargs`` unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a connector command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def connector_active(invocation: Invocation) -> HandlerResult:
    """List active connectors with established connections (workspace-scoped)."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def connector_get(invocation: Invocation) -> HandlerResult:
    """Get one connector's details by key (workspace-scoped, no project)."""
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), connector_key=connector_key)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def connector_list(invocation: Invocation) -> HandlerResult:
    """List all available connectors (workspace-scoped, no project)."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def connector_ai_chat(invocation: Invocation) -> HandlerResult:
    """Send a message to the connector AI chat assistant. ``body`` is required input."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ai_history(invocation: Invocation) -> HandlerResult:
    """Get chat history for a connection. The connection key is positional."""
    project_id = require_project(invocation)
    connection_key = _require_string_positional_at(invocation, 0, "connection key")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), connection_key=connection_key, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ai_session_list(invocation: Invocation) -> HandlerResult:
    """List connector chat sessions in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ai_session_messages(invocation: Invocation) -> HandlerResult:
    """Get messages for a connector chat session. The session id is positional."""
    project_id = require_project(invocation)
    session_id = _require_int_positional_at(invocation, 0, "session id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ai_submit_column_selection(invocation: Invocation) -> HandlerResult:
    """Submit a column selection to the connector chat flow. ``body`` is required input."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ai_submit_credentials(invocation: Invocation) -> HandlerResult:
    """Submit connector credentials to the connector chat flow.

    ``body`` (the credentials payload) is a required ``--input`` field; it is
    never accepted as a positional argument.
    """
    project_id = require_project(invocation)
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_connection_create(invocation: Invocation) -> HandlerResult:
    """Create a connection for a connector. ``--yes`` is always required.

    ``config`` (the connection credentials) is a required ``--input`` field;
    it is never accepted as a positional argument.
    """
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    document = invocation.load_input()
    config = _require_field(document, "config")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"create a {connector_key} connection",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), connector_key=connector_key, config=config, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_connection_delete(invocation: Invocation) -> HandlerResult:
    """Delete a connection. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete connection {connection_key} of connector {connector_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_connection_get(invocation: Invocation) -> HandlerResult:
    """Get one connection's details. Connector and connection keys are positional."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_connection_list(invocation: Invocation) -> HandlerResult:
    """List connections for a connector type. The connector key is positional."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), connector_key=connector_key, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_connection_update(invocation: Invocation) -> HandlerResult:
    """Update a connection's credentials. ``--yes`` is always required.

    ``credentials`` is a required ``--input`` field; it is never accepted as
    a positional argument.
    """
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input()
    credentials = _require_field(document, "credentials")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update credentials for connection {connection_key} of connector {connector_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            credentials=credentials,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ds_config_create(invocation: Invocation) -> HandlerResult:
    """Create a data source configuration. ``--yes`` is always required."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "connector_key": connector_key,
        "connection_key": connection_key,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, _DS_CONFIG_CREATE_OPTIONAL)
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"create a data source config for connection {connection_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ds_config_delete(invocation: Invocation) -> HandlerResult:
    """Delete a data source configuration. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    ds_config_key = _require_string_positional_at(invocation, 2, "ds config key")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete data source config {ds_config_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            ds_config_key=ds_config_key,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ds_config_delete_all(invocation: Invocation) -> HandlerResult:
    """Bulk-delete data source configurations for a connection. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input()
    config_ids = _require_field(document, "config_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete data source configs for connection {connection_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            config_ids=config_ids,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ds_config_get(invocation: Invocation) -> HandlerResult:
    """Get one data source configuration by key."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    ds_config_key = _require_string_positional_at(invocation, 2, "ds config key")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            ds_config_key=ds_config_key,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ds_config_list(invocation: Invocation) -> HandlerResult:
    """List data source configurations for a connection."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_ds_config_update(invocation: Invocation) -> HandlerResult:
    """Update a data source configuration via JSON-patch ops. ``--yes`` is always required."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    ds_config_key = _require_string_positional_at(invocation, 2, "ds config key")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update data source config {ds_config_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            ds_config_key=ds_config_key,
            patch=patch,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_query_generate(invocation: Invocation) -> HandlerResult:
    """Generate a query for a connector using AI. ``prompt`` is required input."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input()
    prompt = _require_field(document, "prompt")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            prompt=prompt,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def connector_query_status(invocation: Invocation) -> HandlerResult:
    """Get the status of an AI chat session for a connector connection."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)
