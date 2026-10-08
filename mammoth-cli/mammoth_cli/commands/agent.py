"""Handlers for the ``agent`` command family (workspace-scoped).

The backing SDK methods never accept a ``project_id`` or ``workspace_id``
keyword argument — a chat scope names its own target (project, dataset, and so
on) and sessions are identified by an opaque ``session_id`` — so handlers here
never forward either explicitly, even though the active project id is still
reported in the envelope metadata. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_RESOURCE_NOT_FOUND,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_USER_CONTROL,
    EXIT_NOT_FOUND,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project, resolved_project
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.protocol import MammothService

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


def _bound_document(invocation: Invocation) -> dict[str, Any]:
    """Return admitted input after the shared S7 contract binding boundary."""
    return bind_command_inputs(invocation.command_id, invocation.load_input() or {})


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The first extra argument, or None when none was given.
    """
    return invocation.extra_args[0] if invocation.extra_args else None


def _require_string_positional(invocation: Invocation, name: str) -> str:
    """Return the first positional argument, raising when absent.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

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
    """Copy every admitted input field into ``kwargs`` unchanged.

    Args:
        document: The parsed ``--input`` document.
        kwargs: The keyword-argument mapping being built for the SDK call.
        fields: The optional field names to forward when present.
    """
    for field, value in document.items():
        if field in kwargs and field not in fields:
            continue
        kwargs[field] = value


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for an agent command.

    Args:
        invocation: The current command's resolved global options.
        workspace_id: The authenticated workspace id.
        project_id: The active project id, or None when not resolved.

    Returns:
        The envelope metadata mapping.
    """
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def agent_chat(invocation: Invocation) -> HandlerResult:
    """Send a chat message to an agent. ``message``/``scope`` are required."""
    document = _bound_document(invocation)
    message = _require_field(document, "message")
    scope = _require_field(document, "scope")
    assert document is not None
    kwargs: dict[str, Any] = {"message": message, "scope": scope}
    _forward_optional(document, kwargs, ("agent_key", "session_id", "client_context", "selection"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_delete(invocation: Invocation) -> HandlerResult:
    """Delete one agent session by id. Prompt or ``--yes`` required."""
    session_id = _require_string_positional(invocation, "session id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete agent session {session_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_list(invocation: Invocation) -> HandlerResult:
    """List agent sessions. All fields are optional and come from ``--input``.

    ``workspace_id`` is never forwarded even if present in the input document:
    the authenticated client already scopes every call to its own workspace.
    """
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("agent_key", "limit", "offset", "include_shared"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_messages(invocation: Invocation) -> HandlerResult:
    """Get the messages of one agent session by id."""
    session_id = _require_string_positional(invocation, "session id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_set_visibility(invocation: Invocation) -> HandlerResult:
    """Set an agent session's visibility. ``visibility`` comes from ``--input``."""
    session_id = _require_string_positional(invocation, "session id")
    document = _bound_document(invocation)
    visibility = _require_field(document, "visibility")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id, visibility=visibility)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def _require_session(invocation: Invocation) -> str:
    """Return the agent chat session id, raising when none was given.

    An embedded call gets the embedding chat's session as ``--session`` from
    :func:`mammoth_cli.embed.invoke`; outside that, the caller passes it.

    Raises:
        CliError: ``missing_argument`` when no session id is set.
    """
    if not invocation.session:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a session id.",
            exit_status=EXIT_USAGE,
            hint="Pass --session SESSION_ID (see 'mammoth agent session list').",
        )
    return invocation.session


def _session_call(invocation: Invocation, **ids: str) -> HandlerResult:
    """Call this command's SDK method on the session plus any extra ids."""
    session_id = _require_session(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id, **ids)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_action_list(invocation: Invocation) -> HandlerResult:
    """List the changes one agent chat session made."""
    return _session_call(invocation)


def agent_action_delete(invocation: Invocation) -> HandlerResult:
    """Delete one object the chat created, by action id. Prompt or ``--yes`` required."""
    action_id = _require_string_positional(invocation, "action id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete what agent action {action_id} made"
    )
    return _session_call(invocation, action_id=action_id)


def agent_run_status(invocation: Invocation) -> HandlerResult:
    """Show the current run of one agent chat session."""
    return _session_call(invocation)


def agent_run_list(invocation: Invocation) -> HandlerResult:
    """List the runs of one agent chat session."""
    return _session_call(invocation)


def _run_control(invocation: Invocation) -> HandlerResult:
    """Pause, resume, stop or extend one run; the SDK method is the manifest's.

    These are the user's run buttons: an agent session (an embedded call) is refused.
    """
    if embedded.active():
        raise CliError(
            code=CODE_USER_CONTROL,
            message="these are the user's run controls; a waiting run resumes by itself",
            exit_status=EXIT_USAGE,
            hint="Carry on without it: a run waiting on a job or a time resumes on its own.",
        )
    return _session_call(invocation, run_id=_require_string_positional(invocation, "run id"))


agent_run_pause = agent_run_resume = agent_run_stop = agent_run_extend = _run_control


def agent_run_units_set(invocation: Invocation) -> HandlerResult:
    """Report the objects one plan step of a run will work on, as queued units."""
    run_id = _require_string_positional(invocation, "run id")
    document = _bound_document(invocation)
    kwargs = {field: _require_field(document, field) for field in ("step", "kind", "units")}
    return _session_call(invocation, run_id=run_id, **kwargs)


def agent_turn_cancel(invocation: Invocation) -> HandlerResult:
    """Stop one turn of an agent chat session (the session's owner only)."""
    return _session_call(invocation, turn_id=_require_string_positional(invocation, "turn id"))


def _definition_call(invocation: Invocation, **kwargs: Any) -> HandlerResult:
    """Call this command's SDK method on the agent key positional plus ``kwargs``."""
    agent_key = _require_string_positional(invocation, "agent key")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), agent_key=agent_key, **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def _field_call(invocation: Invocation, *fields: str) -> HandlerResult:
    """Call this command's SDK method with the required ``--input`` ``fields``."""
    document = _bound_document(invocation)
    return _definition_call(
        invocation, **{field: _require_field(document, field) for field in fields}
    )


def agent_list(invocation: Invocation) -> HandlerResult:
    """List the workspace's agent definitions; ``status`` is optional input."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **_bound_document(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_roles(invocation: Invocation) -> HandlerResult:
    """List the built-in roles an agent definition can take."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_create(invocation: Invocation) -> HandlerResult:
    """Create an agent definition under the KEY positional; ``name`` is required input."""
    _require_string_positional(invocation, "agent key")
    document = _bound_document(invocation)
    _require_field(document, "name")
    # The bound document already carries the KEY positional as ``key``.
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **document)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_get(invocation: Invocation) -> HandlerResult:
    """Get one agent definition."""
    return _definition_call(invocation)


def agent_publish(invocation: Invocation) -> HandlerResult:
    """Publish an agent definition so it can take work."""
    return _definition_call(invocation)


def agent_disable(invocation: Invocation) -> HandlerResult:
    """Disable an agent definition so it stops taking work."""
    return _definition_call(invocation)


def agent_charter_versions(invocation: Invocation) -> HandlerResult:
    """List the saved charter versions of an agent definition."""
    return _definition_call(invocation)


def agent_goldens_list(invocation: Invocation) -> HandlerResult:
    """List the golden cases an agent definition is proven against."""
    return _definition_call(invocation)


def agent_goldens_run(invocation: Invocation) -> HandlerResult:
    """Start a proof run of the agent definition's golden cases."""
    return _definition_call(invocation)


def agent_goldens_status(invocation: Invocation) -> HandlerResult:
    """Show the latest proof run of the agent definition's golden cases."""
    return _definition_call(invocation)


def agent_feedback_list(invocation: Invocation) -> HandlerResult:
    """List the thumbs up/down feedback on the agent definition's answers."""
    return _definition_call(invocation)


def agent_update(invocation: Invocation) -> HandlerResult:
    """Change an agent definition; only the ``--input`` fields given are sent."""
    fields = {k: v for k, v in _bound_document(invocation).items() if k != "agent_key"}
    return _definition_call(invocation, **fields)


def agent_delete(invocation: Invocation) -> HandlerResult:
    """Delete an agent definition. Prompt or ``--yes`` required."""
    agent_key = _require_string_positional(invocation, "agent key")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete agent definition {agent_key}"
    )
    return _definition_call(invocation)


def agent_charter_get(invocation: Invocation) -> HandlerResult:
    """Show the charter text and version of one agent definition."""
    definition, meta = _definition_call(invocation)
    return {key: definition[key] for key in ("key", "charter_version", "charter")}, meta


def agent_charter_set(invocation: Invocation) -> HandlerResult:
    """Replace the charter; the new text becomes a new charter version."""
    return _field_call(invocation, "charter")


def agent_charter_restore(invocation: Invocation) -> HandlerResult:
    """Restore an older charter version as a new version."""
    return _definition_call(invocation, version=invocation.positional("version"))


def agent_access_set(invocation: Invocation) -> HandlerResult:
    """Set the built-in ``role`` and, when given, ``propose``."""
    document = _bound_document(invocation)
    propose = {"propose": document["propose"]} if "propose" in document else {}
    return _definition_call(invocation, role=_require_field(document, "role"), **propose)


def agent_projects_set(invocation: Invocation) -> HandlerResult:
    """Set the projects the agent may work in (replaces the list)."""
    return _field_call(invocation, "project_ids")


def agent_projects_clear(invocation: Invocation) -> HandlerResult:
    """Clear the projects the agent may work in (sets the list to empty)."""
    return _definition_call(invocation, project_ids=[])


def agent_team_set(invocation: Invocation) -> HandlerResult:
    """Replace the team: the agents this agent may ask, and the rounds of asking."""
    return _field_call(invocation, "team")


def agent_goldens_add(invocation: Invocation) -> HandlerResult:
    """Add a golden question and the answer it must reach."""
    return _field_call(invocation, "question", "expected")


def agent_goldens_remove(invocation: Invocation) -> HandlerResult:
    """Remove one golden by id. Prompt or ``--yes`` required."""
    golden_id = invocation.positional("golden_id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"remove golden {golden_id}"
    )
    return _definition_call(invocation, golden_id=golden_id)


def _note_call(invocation: Invocation, kind: str, **kwargs: Any) -> HandlerResult:
    """Call this command's SDK method on a ``kind`` note of the project in scope."""
    return _definition_call(invocation, project_id=require_project(invocation), kind=kind, **kwargs)


def agent_memory_add(invocation: Invocation) -> HandlerResult:
    """Save a learned fact (``name`` and ``content`` from ``--input``) for the project."""
    document = _bound_document(invocation)
    return _note_call(
        invocation,
        "fact",
        name=_require_field(document, "name"),
        content=_require_field(document, "content"),
    )


def agent_memory_list(invocation: Invocation) -> HandlerResult:
    """List the facts the agent learned in the project."""
    return _note_call(invocation, "fact")


def agent_memory_remove(invocation: Invocation) -> HandlerResult:
    """Remove one fact by note id (from ``agent memory list``). Prompt or ``--yes`` required."""
    note_id = invocation.positional("note_id")
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"remove note {note_id}")
    return _definition_call(invocation, note_id=note_id)


def agent_scratch_set(invocation: Invocation) -> HandlerResult:
    """Save a working note NAME (``content`` from ``--input``) for the project."""
    document = _bound_document(invocation)
    return _note_call(
        invocation,
        "scratch",
        name=invocation.positional("name"),
        content=_require_field(document, "content"),
    )


def agent_scratch_list(invocation: Invocation) -> HandlerResult:
    """List the agent's working notes in the project."""
    return _note_call(invocation, "scratch")


def _scratch_note(service: MammothService, invocation: Invocation) -> dict[str, Any]:
    """Return the working note NAME of the project in scope, or raise not found."""
    name = invocation.positional("name")
    listing = service.call(
        _symbol(replace(invocation, command_id="agent.scratch.list")),
        agent_key=_require_string_positional(invocation, "agent key"),
        project_id=require_project(invocation),
        kind="scratch",
    )
    for note in listing["result"]:
        if note["name"] == name:
            return dict(note)
    raise CliError(
        code=CODE_RESOURCE_NOT_FOUND,
        message=f"No working note named '{name}' for this agent in this project.",
        exit_status=EXIT_NOT_FOUND,
        hint="List the names with 'mammoth agent scratch list KEY'.",
    )


def agent_scratch_get(invocation: Invocation) -> HandlerResult:
    """Show the working note NAME."""
    with open_service(invocation) as (service, auth):
        note = _scratch_note(service, invocation)
    return note, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_scratch_clear(invocation: Invocation) -> HandlerResult:
    """Delete the working note NAME. Prompt or ``--yes`` required."""
    name = invocation.positional("name")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"clear working note {name}"
    )
    with open_service(invocation) as (service, auth):
        note = _scratch_note(service, invocation)
        data = service.call(
            _symbol(invocation),
            agent_key=_require_string_positional(invocation, "agent key"),
            note_id=note["id"],
        )
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
