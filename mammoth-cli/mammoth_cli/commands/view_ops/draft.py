"""Handlers for ``view draft *``: enter, status, submit, discard and auto-run."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mammoth_cli.commands.view._common import (
    _DATAVIEW_GET_SYMBOL,
)
from mammoth_cli.commands.view.settle import (
    UNFINISHED_STATE,
    wait_for_refreshed_view,
)
from mammoth_cli.commands.view_ops import (
    _DRAFT_STATUS_SYMBOL,
    _PIPELINE_ITEMS_ALL_SYMBOL,
    _PIPELINE_ITEMS_FULL,
    _PIPELINE_ITEMS_SYMBOL,
    _compact_reference_error,
    _dispatch_view,
    _meta,
    _parse_created_at,
    _profile_name,
    _require_field,
    _resolve_exact_dataset_id,
    _symbol,
    _tasks,
    _view_id,
)
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

HandlerResult = tuple[Any, dict[str, Any]]


def view_draft_enter(invocation: Invocation) -> HandlerResult:
    """Enter draft mode on a view's pipeline."""
    view_id = _view_id(invocation)
    return _dispatch_view(invocation, view_id, "enter_draft_mode")


def view_draft_status(invocation: Invocation) -> HandlerResult:
    """Report whether a view's pipeline is currently in draft mode.

    Draft state is read from the server (``PipelineAPI.get_draft_status``) so it
    is correct across processes, rather than from a process-local flag that a
    freshly resolved view would always report as ``False``.
    """
    view_id = _view_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataview_id=view_id)
        dataset_id = _resolve_exact_dataset_id(
            invocation, view_id, invocation.load_input() or {}, required=False, allow_missing=True
        ) or parents.lookup(_profile_name(invocation), auth.workspace_id, view_id)
        if isinstance(data, dict):
            data = {**data, "step_errors": pipeline_step_errors(service, view_id, dataset_id)}
    return data, _meta(invocation, auth.workspace_id)


def pipeline_step_errors(service: Any, view_id: int, dataset_id: Any) -> list[dict[str, Any]]:
    """Every pipeline step (task or export) whose reference is in error, and why.

    The web app disables Apply while any step is in reference error (a column
    that is gone or changed type under an export); the draft status alone
    only says the pipeline is dirty, so the reasons are read from the items.
    """
    kwargs: dict[str, Any] = {"dataview_id": view_id}
    if dataset_id is not None:
        kwargs["dataset_id"] = int(dataset_id)
    listing = (
        service.call(_PIPELINE_ITEMS_ALL_SYMBOL, fields=_PIPELINE_ITEMS_FULL, **kwargs)
        if "dataset_id" in kwargs
        else service.call(_PIPELINE_ITEMS_SYMBOL, fields=_PIPELINE_ITEMS_FULL, limit=100, **kwargs)
    )
    items = listing.get("items") if isinstance(listing, dict) else None
    errors: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        reference_errors = (item.get("reference_errors") or {}).get("reference_errors") or []
        if not reference_errors and item.get("has_refferror") is not True:
            continue
        errors.append(
            {
                "item_type": item.get("item_type"),
                "id": item.get("id"),
                "sequence": item.get("sequence"),
                "handler_type": item.get("handler_type"),
                "reference_errors": [_compact_reference_error(e) for e in reference_errors],
                "error_info": item.get("error_info"),
            }
        )
    return errors


def view_draft_submit(invocation: Invocation) -> HandlerResult:
    """Submit a view's draft pipeline changes.

    ``--dry-run`` lists the pending draft steps the submit would apply (``pending_draft_steps``).
    """
    view_id = _view_id(invocation)
    project_id = invocation.project
    pending_steps: list[dict[str, Any]] = []

    def before(service: Any, dataset_id: int) -> dict[str, Any]:
        state = _draft_before_submit(service, dataset_id, view_id, project_id)
        if invocation.dry_run and state["pending"]:
            pending_steps.extend(_pending_draft_steps(service, dataset_id, view_id, invocation))
        return state

    def after(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        return _draft_submit_row_check(service, dataset_id, view_id, project_id, state, data)

    try:
        return _dispatch_view(invocation, view_id, "submit_draft", before=before, after=after)
    except DryRunStop as stop:
        stop.record["pending_draft_steps"] = pending_steps
        raise


#: Task statuses of a draft change not yet applied: a step added, edited, removed or
#: suspended in the draft.
_PENDING_STEP_STATUSES = frozenset({"added", "edited", "deleted", "suspending"})
_ACTION_LIST_SYMBOL = "mammoth.api.agents.AgentsAPI.action_list"
_VIEW_KIND = "view"


def _pending_draft_steps(
    service: Any, dataset_id: int, view_id: int, invocation: Invocation
) -> list[dict[str, Any]]:
    """The draft steps a submit would apply, in pipeline order, one task listing.

    With the embedding chat's session (``--session``) each step also says whether another
    session staged it: a step last touched before this session's first write on the view.
    """
    first_write = _first_write_on_view(service, invocation.session, view_id)
    steps = []
    for task in _tasks(service, dataset_id, view_id):
        if task.get("status") not in _PENDING_STEP_STATUSES:
            continue
        touched = _parse_created_at(task.get("updated_at")) or _parse_created_at(
            task.get("created_at")
        )
        step: dict[str, Any] = {
            "id": task.get("id"),
            "sequence": task.get("sequence"),
            "status": task.get("status"),
            "name": _step_name(task.get("params")),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }
        if invocation.session:
            step["staged_by_other"] = first_write is None or (
                touched is not None and touched < first_write
            )
        steps.append(step)
    return sorted(steps, key=lambda step: step["sequence"] or 0)


def _first_write_on_view(service: Any, session_id: str | None, view_id: int) -> datetime | None:
    """When this session first wrote to the view, from its change record; ``None`` if never."""
    if not session_id:
        return None
    record = service.call(_ACTION_LIST_SYMBOL, session_id=session_id)
    actions = record.get("actions") if isinstance(record, dict) else None
    times = [
        written
        for action in actions or []
        if isinstance(action, dict)
        and action.get("kind") == _VIEW_KIND
        and action.get("object_id") == view_id
        and (written := _parse_created_at(action.get("created_at"))) is not None
    ]
    return min(times, default=None)


def _step_name(params: Any) -> str | None:
    """``Replace`` for a step whose params start with ``REPLACE``; ``None`` when unknown."""
    if not isinstance(params, dict) or not params:
        return None
    return str(next(iter(params))).replace("_", " ").title()


def _draft_before_submit(
    service: Any, dataset_id: int, view_id: int, project_id: int | None
) -> dict[str, Any]:
    """The view's row count and data timestamp, and whether its draft has changes to run."""
    info = service.call(
        _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
    )
    draft = service.call(_DRAFT_STATUS_SYMBOL, dataview_id=view_id)
    return {
        "row_count": info.get("row_count"),
        "stamp": info.get("data_updated_at"),
        "pending": bool(draft.get("has_pending_changes")),
    }


def _draft_submit_row_check(
    service: Any,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
    before: dict[str, Any],
    data: Any,
) -> Any:
    """``data`` with the row count read once the submitted steps' data is in.

    The submit returns with the pipeline ``idle`` while its steps still run, so a
    count read at once is the old one (FB-22). A draft with nothing to run is
    read at once; data that never refreshes is reported as unfinished.
    """
    if not isinstance(data, dict):
        return data
    if before["pending"]:
        info = wait_for_refreshed_view(service, dataset_id, view_id, project_id, before["stamp"])
    else:
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
    rows_after = info.get("row_count") if info is not None else None
    out = {**data, "row_check": {"rows_before": before["row_count"], "rows_after": rows_after}}
    if info is None:
        out["pipeline_error"] = {
            "execution_state": UNFINISHED_STATE,
            "wait_error": "the view's data was not refreshed after the submit; read it again",
        }
    return out


def view_draft_discard(invocation: Invocation) -> HandlerResult:
    """Discard a view's draft pipeline changes. Prompt or ``--yes`` required."""
    view_id = _view_id(invocation)
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"discard the draft for view {view_id}"
    )
    return _dispatch_view(invocation, view_id, "discard_draft")


def view_draft_auto_run(invocation: Invocation) -> HandlerResult:
    """Set whether a view's draft pipeline auto-runs. ``enabled`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    enabled = _require_field(document, "enabled")
    return _dispatch_view(invocation, view_id, "set_auto_run", enabled=enabled)
