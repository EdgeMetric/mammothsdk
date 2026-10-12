"""Handlers for the ``workflow`` command family (project-scoped).

Every workflow operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and workflow/block ids come from a
positional argument or the strict ``--input`` document. Block-scoped commands
take the workflow id as the first positional and the block id as the second,
mirroring ``batch.py``'s dataset/batch pair. Handlers dispatch through the
generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

import time
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_JOB_FAILED,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_API,
    EXIT_RETRYABLE,
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
from mammoth_cli.runtime.session import (
    DEFAULT_MUTATION_JOB_TIMEOUT,
    open_service,
    require_project,
)

HandlerResult = tuple[Any, dict[str, Any]]


def _graph_projection(raw: Any) -> dict[str, Any]:
    """Project a backend graph into validated nodes, edges, and neighbors.

    Unknown shapes are explicitly incomplete; this reader never invents an id
    or follows additional resources to fill a hidden region.
    """
    if (
        not isinstance(raw, dict)
        or not isinstance(raw.get("nodes"), list)
        or not isinstance(raw.get("edges"), list)
    ):
        return {"nodes": [], "edges": [], "complete": False, "hidden_regions": ["unknown_shape"]}
    nodes: dict[str, dict[str, Any]] = {}
    for node in raw["nodes"]:
        if not isinstance(node, dict) or node.get("id") is None:
            return {"nodes": [], "edges": [], "complete": False, "hidden_regions": ["invalid_node"]}
        node_id = str(node["id"])
        if node_id in nodes:
            return {
                "nodes": [],
                "edges": [],
                "complete": False,
                "hidden_regions": ["duplicate_node"],
            }
        nodes[node_id] = {"id": node_id, "upstream": [], "downstream": []}
    edges: list[dict[str, str]] = []
    hidden: list[str] = []
    for edge in raw["edges"]:
        if not isinstance(edge, dict) or edge.get("source") is None or edge.get("target") is None:
            hidden.append("invalid_edge")
            continue
        source, target = str(edge["source"]), str(edge["target"])
        if source not in nodes or target not in nodes:
            hidden.append("unresolved_edge_endpoint")
            continue
        nodes[source]["downstream"].append(target)
        nodes[target]["upstream"].append(source)
        edges.append({"source": source, "target": target})
    for node in nodes.values():
        node["upstream"].sort()
        node["downstream"].sort()
    return {
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": edges,
        "complete": not hidden,
        "hidden_regions": sorted(set(hidden)),
    }


_CREATE_OPTIONAL = ("shape", "purpose", "seed_datasource_id")
_UPDATE_OPTIONAL = ("name", "purpose", "pipeline_summary", "notes")
_BLOCK_ADD_OPTIONAL = ("display_name", "connection_type", "position_hint")


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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _int_positional_at(invocation: Invocation, index: int, name: str) -> int | None:
    """Parse the positional argument at ``index`` as an int, or return None."""
    if len(invocation.extra_args) <= index:
        return None
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` as an int, or raise."""
    value = _int_positional_at(invocation, index, name)
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
    """Copy each of ``fields`` from ``document`` into ``kwargs`` when present."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a workflow command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def workflow_list(invocation: Invocation) -> HandlerResult:
    """List workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_get(invocation: Invocation) -> HandlerResult:
    """Get one workflow by id in the active project."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workflow_id=workflow_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_graph(invocation: Invocation) -> HandlerResult:
    """Get the active project's workflow graph."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        raw = service.call(_symbol(invocation), project_id=project_id)
    # Keep every backend field intact. The typed projection is additive because
    # the backend graph shape is not yet a versioned public SDK model.
    if isinstance(raw, dict):
        data = dict(raw)
        navigation_key = "cli_navigation"
        suffix = 1
        while navigation_key in data:
            navigation_key = f"cli_navigation_v{suffix}"
            suffix += 1
        data[navigation_key] = _graph_projection(raw)
    else:
        data = {"backend_graph": raw, "cli_navigation": _graph_projection(raw)}
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_cleanup(invocation: Invocation) -> HandlerResult:
    """Clean up ghost (orphaned skeleton) workflows in the active project."""
    project_id = require_project(invocation)
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete the ghost workflows of project {project_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_workspace_datasets(invocation: Invocation) -> HandlerResult:
    """List workspace datasets available to workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_workspace_exports(invocation: Invocation) -> HandlerResult:
    """List workspace exports available to workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_workspace_sources(invocation: Invocation) -> HandlerResult:
    """List workspace sources available to workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_create(invocation: Invocation) -> HandlerResult:
    """Create a workflow. Name comes from a positional or the ``name`` field."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    name = _string_positional(invocation) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A workflow name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    kwargs: dict[str, Any] = {"name": name, "project_id": project_id}
    _forward_optional(document, kwargs, _CREATE_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_update(invocation: Invocation) -> HandlerResult:
    """Update a workflow's metadata. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"workflow_id": workflow_id, "project_id": project_id}
    _forward_optional(document, kwargs, _UPDATE_OPTIONAL)
    if len(kwargs) == 2:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=(
                "Provide at least one of 'name', 'purpose', 'pipeline_summary', "
                "or 'notes' to update."
            ),
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_delete(invocation: Invocation) -> HandlerResult:
    """Delete one workflow by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete workflow {workflow_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workflow_id=workflow_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_from_template(invocation: Invocation) -> HandlerResult:
    """Instantiate a workflow from a workspace template.

    ``template_id`` is positional; the new workflow name is an input field.
    """
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    workflow_name = document.get("workflow_name")
    if not workflow_name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A workflow name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass 'workflow_name' via --input.",
        )
    template_id = invocation.positional("template_id")
    if template_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A template id is required.", exit_status=EXIT_USAGE
        )
    template_id = int(template_id)
    kwargs: dict[str, Any] = {
        "template_id": template_id,
        "workflow_name": workflow_name,
        "project_id": project_id,
    }
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_canvas(invocation: Invocation) -> HandlerResult:
    """Update a workflow's canvas state. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input()
    canvas_state = _require_field(document, "canvas_state")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            canvas_state=canvas_state,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_add(invocation: Invocation) -> HandlerResult:
    """Add a skeleton block to a workflow. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input()
    block_type = _require_field(document, "block_type")
    kwargs: dict[str, Any] = {
        "workflow_id": workflow_id,
        "block_type": block_type,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, _BLOCK_ADD_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_auth(invocation: Invocation) -> HandlerResult:
    """Patch a workflow block's auth credentials.

    The workflow id is the first positional and the block id is the second.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    block_id = _require_int_positional_at(invocation, 1, "block id")
    document = invocation.load_input()
    auth_data = _require_field(document, "auth_data")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"replace the credentials of block {block_id} in workflow {workflow_id}",
        target=str(block_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            block_id=block_id,
            auth_data=auth_data,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_config(invocation: Invocation) -> HandlerResult:
    """Promote a configured skeleton block to a real resource.

    The workflow id is the first positional and the block id is the second.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    block_id = _require_int_positional_at(invocation, 1, "block id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), workflow_id=workflow_id, block_id=block_id, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_type(invocation: Invocation) -> HandlerResult:
    """Patch a workflow block's connector/handler type.

    The workflow id is the first positional and the block id is the second.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    block_id = _require_int_positional_at(invocation, 1, "block id")
    document = invocation.load_input()
    connection_type = _require_field(document, "connection_type")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            block_id=block_id,
            connection_type=connection_type,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


_GET_SYMBOL = "mammoth.api.workflows.WorkflowsAPI.get"
_SAVE_POLL_SECONDS = 2.0


def _save_run(workflow: Any) -> dict[str, Any] | None:
    """The Save the workflow's record holds, or None when the response carries none."""
    state = workflow.get("canvas_state") if isinstance(workflow, dict) else None
    run = state.get("save_run") if isinstance(state, dict) else None
    return run if isinstance(run, dict) else None


def _save_is_running(workflow: Any) -> bool:
    run = _save_run(workflow)
    return run is not None and run.get("status") == "running"


def _save_failure(workflow: Any) -> CliError | None:
    """The error for a Save that ended without building every change, else None.

    The route answers 202 and builds in the background, so a finished run is the
    only proof the changes were saved: ``done`` means all of them were, anything
    else (``partial``) left some unbuilt, each with the reason it gives.
    """
    run = _save_run(workflow)
    if run is None or run.get("status") in ("running", "done"):
        return None
    reasons = [
        f"{step.get('label') or step.get('kind')}: {step['error']}"
        for step in run.get("steps") or []
        if isinstance(step, dict) and step.get("error")
    ]
    reasons += [str(why) for why in (run.get("needs_setup") or {}).values()]
    message = f"The workflow save did not build every change (status: {run.get('status')})."
    if reasons:
        message += " " + "; ".join(reasons)
    return CliError(
        code=CODE_JOB_FAILED,
        message=message,
        exit_status=EXIT_API,
        hint="Fix what the message names, then run 'workflow save' again.",
        details={"save_run": run},
    )


def workflow_save(invocation: Invocation) -> HandlerResult:
    """Save a workflow's unsaved canvas changes and wait for the run. Workflow id is positional.

    Fails, naming the reasons, when the save does not build every change.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"workflow_id": workflow_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("keys", "expected_version"))
    budget = invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        deadline = time.monotonic() + budget
        while _save_is_running(data):
            if time.monotonic() >= deadline:
                raise CliError(
                    code="timeout",
                    message=f"The workflow save was still running after {budget:.0f} seconds.",
                    exit_status=EXIT_RETRYABLE,
                    hint=f"Check it with 'mammoth workflow get {workflow_id}'.",
                    retryable=True,
                )
            time.sleep(_SAVE_POLL_SECONDS)
            data = service.call(_GET_SYMBOL, workflow_id=workflow_id, project_id=project_id)
    if (failure := _save_failure(data)) is not None:
        raise failure
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_archive(invocation: Invocation) -> HandlerResult:
    """Archive a workflow, or bring it back. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "workflow_id": workflow_id,
        "archived": _require_field(document, "archived"),
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("dataset_ids",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_attach_dataset(invocation: Invocation) -> HandlerResult:
    """Attach a dataset to a workflow. Workflow id and dataset id are positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            datasource_id=invocation.positional("datasource_id"),
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_resolve_held(invocation: Invocation) -> HandlerResult:
    """Settle a change that a workflow Save held back. Workflow id and change key are positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "workflow_id": workflow_id,
        "key": invocation.positional("key"),
        "built": _require_field(document, "built"),
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("expected_version",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)
