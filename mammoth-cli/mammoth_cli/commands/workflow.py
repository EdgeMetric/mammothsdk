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

import json
from typing import Any

from mammoth.api.workflows import save_is_running, save_run

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_CONFLICT,
    CODE_INVALID_ARGUMENT,
    CODE_INVALID_INPUT,
    CODE_JOB_FAILED,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_API,
    EXIT_CONFLICT,
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
from mammoth_cli.services.mapping import is_missing_route_error


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


def _require_positional_str(invocation: Invocation, name: str, label: str) -> str:
    """Return the named string positional, or raise a usage error."""
    value = invocation.positional(name)
    if value is None or not str(value).strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {label} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {label} as a positional argument.",
        )
    return str(value)


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


_DELETE_PLAN_SYMBOL = "mammoth.api.workflows.WorkflowsAPI.delete_plan"
_JOBS_WAIT_SYMBOL = "mammoth.api.jobs.JobsAPI.wait_for_jobs"
_DELETE_FIELDS = frozenset({"keep_inputs", "trash_inputs", "keep_steps", "trash"})
_STEP_KINDS = frozenset({"steps", "result"})
_FOLLOWER_KINDS = frozenset({"dashboard", "schedule"})
_HAS_STEPS_CODE = "4WKFL310"
#: The plan-key prefix of a trash job's item type, where the two differ.
_PLAN_KEY_PREFIX = {"dataview": "view"}


def _delete_choice(document: dict[str, Any]) -> dict[str, Any]:
    """Validate the ``--input`` of ``workflow delete`` and return it.

    Raises:
        CliError: ``invalid_input`` for an unknown field, a non-boolean flag, a ``trash`` that is
            not a list of keys, or ``trash`` given with another choice.
    """
    # The positional id is folded into the document as ``workflow_id``; it is not a choice.
    document = {k: v for k, v in document.items() if k != "workflow_id"}
    unknown = sorted(set(document) - _DELETE_FIELDS)
    if unknown:
        raise CliError(
            code=CODE_INVALID_INPUT,
            message=f"Unknown field(s) in the input: {', '.join(unknown)}.",
            exit_status=EXIT_USAGE,
            hint="Use keep_inputs, trash_inputs, keep_steps, or trash (a list of plan keys).",
        )
    for name in ("keep_inputs", "trash_inputs", "keep_steps"):
        if name in document and not isinstance(document[name], bool):
            raise CliError(
                code=CODE_INVALID_INPUT,
                message=f"'{name}' must be true or false.",
                exit_status=EXIT_USAGE,
            )
    trash = document.get("trash")
    if "trash" in document and (
        not isinstance(trash, list) or any(not isinstance(k, str) or not k for k in trash)
    ):
        raise CliError(
            code=CODE_INVALID_INPUT,
            message="'trash' must be a list of plan keys such as 'view:12'.",
            exit_status=EXIT_USAGE,
            hint="Read the keys with 'mammoth workflow delete-plan WORKFLOW_ID'.",
        )
    if "trash" in document and len(document) > 1:
        raise CliError(
            code=CODE_INVALID_INPUT,
            message="'trash' names the keys exactly; do not combine it with the other fields.",
            exit_status=EXIT_USAGE,
        )
    if document.get("keep_inputs") and document.get("trash_inputs"):
        raise CliError(
            code=CODE_INVALID_INPUT,
            message="'keep_inputs' and 'trash_inputs' contradict each other.",
            exit_status=EXIT_USAGE,
        )
    return document


def delete_selection(
    plan: dict[str, Any], choice: dict[str, Any]
) -> tuple[list[str], list[dict[str, Any]]]:
    """Pick the plan keys to send, and say why each other item stays.

    A default pick is every item the plan ticks that no other workflow uses (a locked key is
    never sent). Inputs stay unless ``trash_inputs``; ``keep_steps`` unticks steps and result
    tables. A schedule or dashboard that follows steps is kept when all of them are kept; a
    dashboard cannot outlive trashed steps, so it goes while any step it follows goes. An
    explicit ``trash`` list is checked against the plan and sent as given.

    Args:
        plan: The delete plan (``items`` with ``key``, ``kind``, ``checked``, ``locked_by``,
            ``follows``).
        choice: The validated ``--input`` document.

    Returns:
        ``(keys, kept)``: the keys to send, and for each other item ``{key, kind, name, reason}``.

    Raises:
        CliError: ``invalid_input`` when an explicit key is not in the plan or is locked.
    """
    items = [i for i in plan.get("items") or [] if isinstance(i, dict) and i.get("key")]
    by_key = {str(i["key"]): i for i in items}
    if "trash" in choice:
        bad = [k for k in choice["trash"] if k not in by_key]
        locked = [k for k in choice["trash"] if k in by_key and by_key[k].get("locked_by")]
        if bad or locked:
            parts = []
            if bad:
                parts.append(f"not in the plan: {', '.join(bad)}")
            if locked:
                names = ", ".join(f"{k} (used by {by_key[k]['locked_by']})" for k in locked)
                parts.append(f"used by another workflow: {names}")
            raise CliError(
                code=CODE_INVALID_INPUT,
                message=f"Cannot trash these keys; {'; '.join(parts)}.",
                exit_status=EXIT_USAGE,
                hint="Read the keys with 'mammoth workflow delete-plan WORKFLOW_ID'.",
            )
        chosen = set(choice["trash"])
    else:
        chosen = set()
        for item in items:
            if item.get("locked_by"):
                continue
            kind = item.get("kind")
            if kind == "input":
                ticked = bool(choice.get("trash_inputs"))
            else:
                ticked = bool(item.get("checked"))
                if kind in _STEP_KINDS and choice.get("keep_steps"):
                    ticked = False
            if ticked:
                chosen.add(str(item["key"]))
        for item in items:
            key, follows = str(item["key"]), [str(f) for f in item.get("follows") or []]
            if item.get("kind") not in _FOLLOWER_KINDS or not follows or item.get("locked_by"):
                continue
            followed_goes = any(f in chosen for f in follows)
            if item["kind"] == "dashboard" and followed_goes:
                chosen.add(key)
            elif not followed_goes:
                chosen.discard(key)
    keys = [str(i["key"]) for i in items if str(i["key"]) in chosen]
    kept: list[dict[str, Any]] = []
    for item in items:
        if str(item["key"]) in chosen:
            continue
        if item.get("locked_by"):
            reason = f"used by workflow {item['locked_by']}"
        elif "trash" in choice:
            reason = "not in the trash list"
        elif item.get("kind") == "input":
            reason = "inputs stay unless trash_inputs is set"
        elif item.get("follows") and item.get("kind") in _FOLLOWER_KINDS:
            reason = "its steps stay"
        else:
            reason = "not ticked" if not item.get("checked") else "kept by the input"
        kept.append(
            {
                "key": item["key"],
                "kind": item.get("kind"),
                "name": item.get("name"),
                "reason": reason,
            }
        )
    return keys, kept


def _has_steps_error(error: CliError, workflow_id: int) -> CliError | None:
    """The actionable error for a 409 ``4WKFL310`` (the workflow still has steps), else None."""
    if error.code != CODE_CONFLICT or _HAS_STEPS_CODE not in json.dumps(
        [error.message, error.details], default=str
    ):
        return None
    return CliError(
        code=CODE_CONFLICT,
        message=f"Workflow {workflow_id} still has steps, so the plain delete was refused.",
        exit_status=EXIT_CONFLICT,
        hint=(
            "Run 'mammoth workflow delete-plan WORKFLOW_ID' to see what goes with it, then "
            "'mammoth workflow delete WORKFLOW_ID --yes' (it sends the ticked items), or add "
            "--input '{\"keep_steps\": true}' to keep the steps."
        ),
        details=error.details,
        request_id=error.request_id,
    )


def _trash_failures(jobs: Any) -> list[dict[str, Any]]:
    """The items a delete job could not trash.

    The server resolves the job as a success and lists them under ``response.failed``.

    Args:
        jobs: The waited jobs, ``{"jobs": [...]}``.

    Returns:
        The ``failed`` entries of every job, in order.
    """
    listed = jobs.get("jobs") if isinstance(jobs, dict) else None
    failures: list[dict[str, Any]] = []
    for job in listed if isinstance(listed, list) else []:
        response = job.get("response") if isinstance(job, dict) else None
        failed = response.get("failed") if isinstance(response, dict) else None
        if isinstance(failed, list):
            failures.extend(entry for entry in failed if isinstance(entry, dict))
    return failures


def _failed_key(entry: dict[str, Any]) -> str:
    """The plan key of an item the delete job could not trash."""
    item_type = str(entry.get("type"))
    return f"{_PLAN_KEY_PREFIX.get(item_type, item_type)}:{entry.get('id')}"


def _trash_failure_warning(entry: dict[str, Any]) -> str:
    """One sentence saying which item was not trashed and why."""
    item = _failed_key(entry)
    if entry.get("name"):
        item += f" ({entry['name']})"
    information = entry.get("information")
    reason = information if isinstance(information, str) and information else None
    reason = reason or entry.get("error_code") or "the server gave no reason"
    return f"{item} was not moved to the Trash: {str(reason).rstrip('.')}."


def _report_what_stayed(result: dict[str, Any]) -> None:
    """Add what a settled delete left behind to its result, in place.

    Items the job could not trash go under ``failed``, leave ``trashed`` and make the result
    partial (exit 3). Kept steps get a warning that they show as their own workflow.

    Args:
        result: The delete result, with the waited ``jobs`` when there were any.
    """
    warnings: list[str] = []
    failures = _trash_failures(result.get("jobs"))
    if failures:
        result["partial"] = True
        result["failed"] = failures
        gone_wrong = {_failed_key(entry) for entry in failures}
        if isinstance(result.get("trashed"), list):
            result["trashed"] = [key for key in result["trashed"] if key not in gone_wrong]
        warnings.extend(_trash_failure_warning(entry) for entry in failures)
        warnings.append(
            "The workflow itself was deleted; steps that were not trashed may show as their own "
            "workflow."
        )
    kept_steps = result.get("kept_steps")
    if isinstance(kept_steps, list) and kept_steps:
        names = ", ".join(str(name) for name in kept_steps)
        warnings.append(f"Kept steps show as their own workflow after the delete: {names}.")
    if warnings:
        result["warnings"] = warnings


def workflow_delete(invocation: Invocation) -> HandlerResult:
    """Delete a workflow with the items of its delete plan. Prompt or ``--yes`` required.

    Reads the delete plan, sends the ticked items no other workflow uses, waits for the job and
    reports what was trashed and kept. An older server with no delete plan gets the plain delete.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    choice = _delete_choice(invocation.load_input() or {})
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete workflow {workflow_id}"
    )
    symbol = _symbol(invocation)
    with open_service(invocation) as (service, auth):
        try:
            plan = service.call(_DELETE_PLAN_SYMBOL, workflow_id=workflow_id, project_id=project_id)
        except CliError as error:
            if not is_missing_route_error(error):
                raise
            # An older server: no plan, so the plain delete is all there is.
            try:
                data = service.call(symbol, workflow_id=workflow_id, project_id=project_id)
            except CliError as plain:
                raise _has_steps_error(plain, workflow_id) or plain from plain
            result = dict(data) if isinstance(data, dict) else {"result": data}
            result["delete_plan"] = "unavailable"
            result["note"] = (
                "This server has no delete plan: only the workflow record was deleted. "
                "Its steps were not touched."
            )
            return result, _meta(invocation, auth.workspace_id, project_id)
        blocked = plan.get("blocked") if isinstance(plan, dict) else None
        if blocked:
            raise CliError(
                code=CODE_CONFLICT,
                message=str(blocked.get("message") or "The workflow cannot be deleted now."),
                exit_status=EXIT_CONFLICT,
                details={"blocked": blocked},
            )
        keys, kept = delete_selection(plan if isinstance(plan, dict) else {}, choice)
        try:
            data = service.call(symbol, workflow_id=workflow_id, project_id=project_id, trash=keys)
        except CliError as error:
            raise _has_steps_error(error, workflow_id) or error from error
        result = dict(data) if isinstance(data, dict) else {"result": data}
        job_ids = [j for j in result.get("job_ids") or [] if isinstance(j, int)]
        if job_ids:
            result["jobs"] = service.call(
                _JOBS_WAIT_SYMBOL,
                job_ids=job_ids,
                timeout=invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT,
            )
    _report_what_stayed(result)
    result["sent"] = keys
    result["kept"] = kept
    return result, _meta(invocation, auth.workspace_id, project_id)


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
    kwargs: dict[str, Any] = {
        "workflow_id": workflow_id,
        "canvas_state": canvas_state,
        "project_id": project_id,
    }
    _forward_optional(document or {}, kwargs, ("expected_version",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
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


_WAIT_SAVE_SYMBOL = "mammoth.api.workflows.WorkflowsAPI.wait_for_save"


def _save_failure(workflow: Any, what: str = "save") -> CliError | None:
    """The error for a Save that ended without building every change, else None.

    The route answers 202 and builds in the background, so a finished run is the
    only proof the changes were saved: ``done`` means all of them were, anything
    else (``partial``) left some unbuilt, each with the reason it gives. ``what`` names
    the run in the message: ``save``, or ``undo`` for the run an undo starts.
    """
    run = save_run(workflow)
    if run is None or run.get("status") in ("running", "done"):
        return None
    reasons = [
        f"{step.get('label') or step.get('kind')}: {step['error']}"
        for step in run.get("steps") or []
        if isinstance(step, dict) and step.get("error")
    ]
    reasons += [str(why) for why in (run.get("needs_setup") or {}).values()]
    outcome = "build every change" if what == "save" else "put back every change"
    message = f"The workflow {what} did not {outcome} (status: {run.get('status')})."
    if reasons:
        message += " " + "; ".join(reasons)
    return CliError(
        code=CODE_JOB_FAILED,
        message=message,
        exit_status=EXIT_API,
        hint=(
            "Fix what the message names, then run 'workflow save' again."
            if what == "save"
            else "Fix what the message names, then read the workflow with 'workflow get'."
        ),
        details={"save_run": run},
    )


def _await_save_run(
    service: Any, data: Any, workflow_id: int, project_id: int, budget: float, what: str
) -> Any:
    """Wait (in the SDK) until the workflow's Save run is no longer running; return it."""
    if not save_is_running(data):
        return data
    data = service.call(
        _WAIT_SAVE_SYMBOL,
        workflow_id=workflow_id,
        workflow=data if isinstance(data, dict) else None,
        timeout=budget,
        project_id=project_id,
    )
    if save_is_running(data):
        raise CliError(
            code="timeout",
            message=f"The workflow {what} was still running after {budget:.0f} seconds.",
            exit_status=EXIT_RETRYABLE,
            hint=f"Check it with 'mammoth workflow get {workflow_id}'.",
            retryable=True,
        )
    return data


#: Commands whose answer is ``{"workflow": ...}`` with the Save that builds it still running.
SAVE_AWAITED = frozenset({"workflow.template.build", "workflow.describe.build"})


def await_built_workflow(invocation: Invocation, service: Any, data: Any) -> Any:
    """Wait for the Save a build started, and fail when it did not build every step.

    Args:
        invocation: The build command's invocation (its project and ``--job-timeout``).
        service: The open Mammoth service.
        data: The build's answer, ``{"workflow": {...}}`` with ``canvas_state.save_run``.

    Returns:
        The answer with ``workflow`` replaced by the workflow once its Save ended.

    Raises:
        CliError: ``timeout`` when the Save outlives the budget, ``job_failed`` when it
            ended without building every step.
    """
    workflow = data.get("workflow") if isinstance(data, dict) else None
    if not isinstance(workflow, dict) or not isinstance(workflow.get("id"), int):
        return data
    project_id = require_project(invocation)
    budget = invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT
    workflow = _await_save_run(service, workflow, workflow["id"], project_id, budget, "save")
    if (failure := _save_failure(workflow)) is not None:
        raise failure
    return {**data, "workflow": workflow}


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
        data = _await_save_run(service, data, workflow_id, project_id, budget, "save")
    if (failure := _save_failure(data)) is not None:
        raise failure
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_save_undo(invocation: Invocation) -> HandlerResult:
    """Undo a workflow's latest finished Save and wait for the undo run. Prompt or ``--yes``.

    The workflow id and the Save's run id are positional. The undo removes what that Save
    built (datasets, views, steps), so it confirms first.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    run_id = _require_positional_str(invocation, "run_id", "Save run id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"undo save {run_id} of workflow {workflow_id}",
    )
    budget = invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), workflow_id=workflow_id, run_id=run_id, project_id=project_id
        )
        data = _await_save_run(service, data, workflow_id, project_id, budget, "undo")
    if (failure := _save_failure(data, "undo")) is not None:
        raise failure
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_save_cancel_step(invocation: Invocation) -> HandlerResult:
    """Cancel one step of a workflow's running Save. Workflow id, run id and step are positional.

    The step ends cancelled and the steps that need it are skipped. Best effort: a job the
    step already started may still finish. The Save keeps running its other steps; read
    ``workflow get`` for the outcome.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    run_id = _require_positional_str(invocation, "run_id", "Save run id")
    step = _require_int_positional_at(invocation, 2, "step")
    if step is None or step < 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The step argument must be 0 or more, got {step}.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            run_id=run_id,
            step=step,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_duplicate(invocation: Invocation) -> HandlerResult:
    """Duplicate a workflow into a new workflow of the same project and wait for the copies.

    The new ``name`` and the ``dataset_ids`` to copy come from ``--input``; the source
    workflow id is an optional positional. The copies hold the datasets' rows, views and
    steps; automations and outside exports are not copied.
    """
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "name": _require_field(document, "name"),
        "dataset_ids": _require_field(document, "dataset_ids"),
        "project_id": project_id,
        "wait": True,
        "timeout": invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT,
    }
    source = _int_positional_at(invocation, 0, "workflow id")
    if source is None:
        source = document.get("source_workflow_id")
    if source is not None:
        kwargs["source_workflow_id"] = source
    with open_service(invocation) as (service, auth):
        job = service.call(_symbol(invocation), **kwargs)
    response = job.get("response") if isinstance(job, dict) else None
    data = dict(job) if isinstance(job, dict) else {"job": job}
    if isinstance(response, dict) and response.get("workflow_id") is not None:
        data["workflow_id"] = response["workflow_id"]
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
