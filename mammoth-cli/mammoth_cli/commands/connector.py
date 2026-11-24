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
create``/``update`` and ``ds-config create``/``update`` reach a third-party
service and always require ``--yes`` (``ds-config create`` saves nothing);
``connection delete`` and the ``ds-config`` deletes are destructive and
accept a prompt or ``--yes``.

Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

import re
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
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
from mammoth_cli.runtime.input_loader import refuse_inline_secrets
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    DEFAULT_MUTATION_JOB_TIMEOUT,
    open_service,
    require_project,
    resolved_project,
)
from mammoth_cli.runtime.shell_text import command_with_input

_DS_CONFIG_CREATE_OPTIONAL = ("query", "file_source", "table", "profile", "validate", "data_sample")
_QUERY_OPTIONAL = ("table", "profile")

_SQL_STRING = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|--[^\n]*|/\*.*?\*/", re.DOTALL)
_SQL_READ_START = re.compile(r"^\s*\(*\s*(select|with|show|values)\b", re.IGNORECASE)
_SQL_WRITE_WORD = re.compile(
    r"\b(insert|update|delete|merge|drop|alter|truncate|create|grant|revoke|call|copy|" r"into)\b",
    re.IGNORECASE,
)


_ACTIVE_CONNECTORS_SYMBOL = "mammoth.api.connectors.ConnectorsAPI.active_connectors"
CODE_PROJECT_REQUIRED = "project_required"
_PROJECTS_SYMBOL = "mammoth.api.projects.ProjectsAPI.list_all"
_CONNECTIONS_SYMBOL = "mammoth.api.connectors.ConnectorsAPI.list_connections"
_JOB_WAIT_SYMBOL = "mammoth.api.jobs.JobsAPI.wait_for_job"
#: Fields of a listed connection that can hold the key the caller typed.
_CONNECTION_KEY_FIELDS = ("connection_key", "key", "id", "name")


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
    return (
        _with_plan_availability(data),
        _meta(invocation, auth.workspace_id, resolved_project(invocation)),
    )


#: ``availability`` a connector gets when the server says this workspace's plan
#: does not include it.
_NOT_IN_PLAN = "not_in_plan"


_NOT_IN_PLAN_NOTE = "Not included in this workspace's plan. Mammoth sales can enable it."


def _mark_not_in_plan(item: Any) -> Any:
    """Return ``item`` marked ``not_in_plan`` when the server says it is unavailable."""
    if isinstance(item, dict) and item.get("is_available") is False:
        return {**item, "availability": _NOT_IN_PLAN, "availability_note": _NOT_IN_PLAN_NOTE}
    return item


def _with_plan_availability(data: Any) -> Any:
    """Mark each connector the server reports unavailable to this workspace.

    The server's ``is_available`` is the same plan check that gates creating a
    connection. ``is_premium``/``is_added`` cannot stand in for it: ``is_added``
    only says a legacy integration row exists, so a premium connector the plan
    does include read as "not enabled". A response without ``is_available`` (an
    older server) is left unmarked. ``ConnectorsAPI.list`` returns a list, which
    stays a list; ``ConnectorsAPI.get`` returns one connector dict.
    """
    if isinstance(data, list):
        return [_mark_not_in_plan(item) for item in data]
    return _mark_not_in_plan(data)


def connector_list(invocation: Invocation) -> HandlerResult:
    """List all available connectors (workspace-scoped, no project)."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return (
        _with_plan_availability(data),
        _meta(invocation, auth.workspace_id, resolved_project(invocation)),
    )


def connector_ai_chat(invocation: Invocation) -> HandlerResult:
    """Send a message to the older connector chat, not the AI connector builder.

    ``body`` is required input. This chat cannot save an AI connector version; build one
    with ``connector draft create`` and follow its agent chat.
    """
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
    """Get one connection's details. Connector and connection keys are positional.

    Without a project (``--project`` or the active one), the project is looked up: the one
    project whose connections hold the key. A key found in none or in several is refused
    with the projects named. A read that starts a platform job is waited for, so the answer
    is the job's result and not its id.
    """
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    project_id = resolved_project(invocation)
    with open_service(invocation) as (service, auth):
        if project_id is None:
            project_id = _project_of_connection(service, connector_key, connection_key)
        data = service.call(
            _symbol(invocation),
            connector_key=connector_key,
            connection_key=connection_key,
            project_id=project_id,
        )
        data = _settled_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _project_of_connection(service: Any, connector_key: str, connection_key: str) -> int:
    """The one project whose ``connector_key`` connections include ``connection_key``.

    Args:
        service: The open service.
        connector_key: The connector the connection belongs to.
        connection_key: The connection to find.

    Returns:
        The project id.

    Raises:
        CliError: ``project_required`` when the key is in none of the projects, in more than
            one, or when a project could not be read (the candidates and the unreadable
            projects are named).
    """
    holders: list[int] = []
    unreadable: list[int] = []
    for project in service.call(_PROJECTS_SYMBOL):
        project_id = project.get("id") if isinstance(project, dict) else None
        if not isinstance(project_id, int):
            continue
        try:
            listed = service.call(
                _CONNECTIONS_SYMBOL, connector_key=connector_key, project_id=project_id
            )
        except CliError:
            # One call per project; a project that cannot be read may be the holder, so
            # the answer below is not a guess when it is named here.
            unreadable.append(project_id)
            continue
        if any(_names_connection(item, connection_key) for item in listed or []):
            holders.append(project_id)
    if len(holders) == 1 and not unreadable:
        return holders[0]
    where = f"projects {holders}" if holders else "none of the projects that could be read"
    skipped = (
        f" Projects {unreadable} could not be read, so the connection may be in one of them."
        if unreadable
        else ""
    )
    raise CliError(
        code=CODE_PROJECT_REQUIRED,
        message=(
            f"Connection '{connection_key}' of connector '{connector_key}' is in {where}."
            f"{skipped} Pass --project to say which."
        ),
        exit_status=EXIT_USAGE,
        hint="Set an active project or pass --project.",
        recovery_commands=[
            f"mammoth connector connection get {connector_key} {connection_key} --project {pid}"
            for pid in holders
        ]
        or ["mammoth project list"],
    )


def _names_connection(item: Any, connection_key: str) -> bool:
    """Whether the listed connection ``item`` is the one called ``connection_key``."""
    return isinstance(item, dict) and any(
        str(item.get(field)) == connection_key for field in _CONNECTION_KEY_FIELDS
    )


def _settled_job(service: Any, invocation: Invocation, data: Any) -> Any:
    """The job's result when ``data`` is nothing but a job id, else ``data`` as it is."""
    job_id = data.get("job_id") if isinstance(data, dict) and set(data) == {"job_id"} else None
    if not isinstance(job_id, int):
        return data
    return service.call(
        _JOB_WAIT_SYMBOL,
        job_id=job_id,
        timeout=invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT,
    )


def connector_connection_list(invocation: Invocation) -> HandlerResult:
    """List connections for one connector type, or for every connector with a saved one."""
    project_id = require_project(invocation)
    connector_key = _string_positional_at(invocation, 0, "connector key")
    with open_service(invocation) as (service, auth):
        if connector_key:
            data = service.call(
                _symbol(invocation), connector_key=connector_key, project_id=project_id
            )
        else:
            data = _connections_of_every_connector(service, invocation, project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _connections_of_every_connector(
    service: Any, invocation: Invocation, project_id: int
) -> list[dict[str, Any]]:
    """Each active connector's connections, every row carrying its ``connector_key``."""
    rows: list[dict[str, Any]] = []
    for key in service.call(_ACTIVE_CONNECTORS_SYMBOL):
        listed = service.call(_symbol(invocation), connector_key=key, project_id=project_id)
        rows.extend({"connector_key": key, **connection} for connection in listed)
    return rows


def connector_connection_update(invocation: Invocation) -> HandlerResult:
    """Update a connection's credentials, optionally renaming it. ``--yes`` is always required.

    ``credentials`` is a required ``--input`` field, never a positional argument. An
    optional ``name`` rides along in the same patch value (mammothsdk#413): the server
    validates the whole value against the connector's model, so a rename needs the full
    credentials. The server saves the change in a job, which this waits for.
    """
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input() or {}
    name = document.get("name")
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'name' must be a non-empty string.",
            exit_status=EXIT_USAGE,
        )
    kwargs: dict[str, Any] = {
        "connector_key": connector_key,
        "connection_key": connection_key,
        "project_id": project_id,
    }
    kwargs["credentials"] = _require_field(document, "credentials")
    if name:
        kwargs["name"] = name.strip()
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update connection {connection_key} of connector {connector_key}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        data = service.wait_if_job(data)
    return data, _meta(invocation, auth.workspace_id, project_id)


_DRAFT_GET_SYMBOL = "mammoth.api.connector_drafts.ConnectorDraftsAPI.get"
_SESSION_MESSAGES_SYMBOL = "mammoth.api.agents.AgentsAPI.session_messages"
#: The widget kind of a chat's credential card ("Test and connect").
_CREDENTIAL_CARD_KIND = "CONNECTOR_CREDENTIAL"


def open_credential_card(messages: Any) -> str | None:
    """The id of the newest unanswered credential card in a chat's messages, or None.

    Args:
        messages: The session-messages read (``{"messages": [...]}`` or the list).

    Returns:
        The card's ``widget.id``, or None when the chat shows no open card.
    """
    items = messages.get("messages") if isinstance(messages, dict) else messages
    for message in reversed(items if isinstance(items, list) else []):
        widget = message.get("widget") if isinstance(message, dict) else None
        if (
            isinstance(widget, dict)
            and widget.get("kind") == _CREDENTIAL_CARD_KIND
            and not widget.get("resolved")
            and not message.get("resolved")
            and widget.get("id")
        ):
            return str(widget["id"])
    return None


def connector_draft_credentials(invocation: Invocation) -> HandlerResult:
    """Answer a connector draft's open key card: test the key and connect.

    The card is the chat's "Test and connect" form (mammothsdk#319). The draft names
    its chat; the newest open credential card in it is answered unless the input gives
    ``widget_id``. Credentials are read from an ``--input`` file or stdin only.

    Args:
        invocation: The parsed command; positional 0 is the draft id.

    Returns:
        The check's outcome with the draft, chat and card ids, and the command metadata.

    Raises:
        CliError: On inline credentials, a missing field, a draft with no chat, or a
            chat with no open card.
    """
    draft_id = _require_string_positional_at(invocation, 0, "draft id")
    if not draft_id.isdigit():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"Draft id must be a number, got {draft_id!r}.",
            exit_status=EXIT_USAGE,
        )
    refuse_inline_secrets(invocation.input_file)
    document = invocation.load_input() or {}
    credentials = _require_field(document, "credentials")
    if not isinstance(credentials, dict) or not credentials:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'credentials' must be a non-empty object of the card's fields.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"test and connect the key card of connector draft {draft_id}",
    )
    with open_service(invocation) as (service, auth):
        draft = service.call(_DRAFT_GET_SYMBOL, draft_id=int(draft_id))
        session_id = draft.get("session_id") if isinstance(draft, dict) else None
        if not session_id:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"Connector draft {draft_id} has no agent chat, so it has no key card.",
                exit_status=EXIT_USAGE,
                hint=f"Open its chat first: mammoth connector draft get {draft_id}.",
            )
        widget_id = document.get("widget_id") or open_credential_card(
            service.call(_SESSION_MESSAGES_SYMBOL, session_id=session_id)
        )
        if not widget_id:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"The chat of connector draft {draft_id} shows no open key card.",
                exit_status=EXIT_USAGE,
                hint=f"Read the chat with mammoth agent session messages {session_id}; "
                "ask the agent to connect the source to get a card.",
            )
        outcome = service.call(
            _symbol(invocation),
            session_id=session_id,
            widget_id=widget_id,
            credentials=credentials,
        )
    data = {"draft_id": int(draft_id), "session_id": session_id, "widget_id": widget_id}
    data["outcome"] = outcome
    return data, _meta(invocation, auth.workspace_id, None)


def _require_read_only_sql(query: Any) -> str:
    """Return ``query`` when it is one SELECT-style statement, or raise usage.

    A first line of defence only: Mammoth runs the SQL as the connection's
    database user, so that user's grants are what finally stop a write.
    """
    if not isinstance(query, str) or not query.strip():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'query' input field must be a non-empty SQL string.",
            exit_status=EXIT_USAGE,
        )
    bare = _SQL_STRING.sub(" ", query).strip().rstrip(";").strip()
    if ";" in bare or not _SQL_READ_START.match(bare) or _SQL_WRITE_WORD.search(bare):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="connector connection query runs one read-only SELECT statement.",
            exit_status=EXIT_USAGE,
            hint=(
                "Send a single SELECT (or WITH ... SELECT) without INSERT, UPDATE, DELETE or "
                "DDL. To import rows as a dataset use 'dataset create'."
            ),
        )
    return query


def connector_connection_query(invocation: Invocation) -> HandlerResult:
    """Run one SELECT on a connection and return sample rows; saves nothing, no ``--yes``."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input()
    kwargs: dict[str, Any] = {
        "connector_key": connector_key,
        "connection_key": connection_key,
        "query": _require_read_only_sql(_require_field(document, "query")),
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, _QUERY_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _no_tables_reason(data: dict[str, Any]) -> str | None:
    """Why a table list is not usable, or ``None`` when it is."""
    if data.get("needs_sign_in"):
        return "its sign-in was refused: sign the connection in again"
    if data.get("failed"):
        return "the tables could not be read; try again"
    if data.get("shape") == "other":
        return "this connection lists no tables (pick its files or data in the web app)"
    return None


def connector_connection_tables(invocation: Invocation) -> HandlerResult:
    """List the tables of a saved connection. Connection key is positional."""
    project_id = require_project(invocation)
    connection_key = _require_string_positional_at(invocation, 0, "connection key")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), connection_key=connection_key)
    if isinstance(data, dict):
        reason = _no_tables_reason(data)
        if reason is not None:
            data = {**data, "warning": f"No usable table list: {reason}."}
    return data, _meta(invocation, auth.workspace_id, project_id)


def _ds_config_next(
    connector_key: str, connection_key: str, document: dict[str, Any]
) -> dict[str, Any]:
    """The result fields naming the import of the query ``ds-config create`` just checked.

    Args:
        connector_key: The connector type.
        connection_key: The saved connection.
        document: The checked ``--input`` document.

    Returns:
        The fields (``next``, and ``next_input`` on Windows), with placeholders for what the check
        did not name; empty for a file check, whose import takes other fields.
    """
    if document.get("file_source"):
        return {}
    spec = {
        "ds_creation_type": "cloud",
        "dataset_spec": {
            "connector_key": connector_key,
            "connection_key": connection_key,
            "query_properties": {
                "ds_name": "NAME",
                "table_name": document.get("table") or "TABLE",
                "query": document.get("query") or "QUERY",
            },
        },
    }
    return command_with_input(["mammoth", "dataset", "create"], spec)


def connector_ds_config_create(invocation: Invocation) -> HandlerResult:
    """Check or sample a query on a connection; saves nothing. ``--yes`` always needed.

    A REST ``query`` is a JSON string. The server only validates the config or returns sample
    rows: no data source config and no dataset is made. ``dataset create`` imports the rows.
    """
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
        action=f"check a data source config on connection {connection_key} (saves nothing)",
    )
    with open_service(invocation) as (service, auth):
        # The route answers with a job; the result to mark is the job's.
        data = service.wait_if_job(service.call(_symbol(invocation), **kwargs))
    if isinstance(data, dict):
        fields = _ds_config_next(connector_key, connection_key, document)
        data = {**data, "saved": False, **fields}
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
    """Generate a query for a connector using AI. ``query`` (the intent) is required input."""
    project_id = require_project(invocation)
    connector_key = _require_string_positional_at(invocation, 0, "connector key")
    connection_key = _require_string_positional_at(invocation, 1, "connection key")
    document = invocation.load_input()
    query = _require_field(document, "query")
    kwargs: dict[str, Any] = {
        "connector_key": connector_key,
        "connection_key": connection_key,
        "query": query,
        "project_id": project_id,
    }
    if document is not None and document.get("profile") is not None:
        kwargs["profile"] = document["profile"]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
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
