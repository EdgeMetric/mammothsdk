"""What a finished job left behind, for ``job wait`` to report beside the job's result.

Every trace followed ``job wait`` with a ``view get`` or ``view analyze`` to learn
whether the run did anything. The job record names its target (``path``, ``response``),
so ``job wait`` reads that object once and returns its state; a project copy reports
the per-view runs the backend recorded on the job itself, with no read at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mammoth_cli.services.listing import view_summary

#: Jobs that leave a dataview to read: a run, a rebuild, a new or restored view.
VIEW_JOB_OPERATIONS = frozenset(
    {
        "create_dataview",
        "clone_dataview",
        "rerun_dataview",
        "pipeline_rerun",
        "reset_dataview",
        "restore_dataview",
        "optimize_dataview",
        "apply_pipeline_version",
        "apply_pending_changes",
        "reorder_pipeline_rules",
        "post_modification_pipeline_execution",
        "pipeline_modification_handler",
        "apply_ds_data_to_dataviews",
    }
)
COPY_PROJECT_OPERATION = "copy_project"

_PATH_IDS = re.compile(
    r"/projects/(?P<project>\d+)(?:/datasets/(?P<dataset>\d+)(?:/dataviews/(?P<view>\d+))?)?"
)


@dataclass(frozen=True)
class ViewTarget:
    """The dataview a finished job acted on, as far as the job record names it."""

    project_id: int
    dataset_id: int
    view_id: int


def _int_or_none(value: Any) -> int | None:
    return int(value) if isinstance(value, int | str) and str(value).isdigit() else None


def view_target(data: dict[str, Any]) -> ViewTarget | None:
    """The view a ``job wait`` result's job ran on, or ``None`` when it ran on no view.

    Only the operations in :data:`VIEW_JOB_OPERATIONS` count. The ids come from the job's
    ``path``; the view id may instead be the response's ``dataview_id`` (or ``id``,
    for a view the job created).
    """
    if data.get("operation") not in VIEW_JOB_OPERATIONS:
        return None
    match = _PATH_IDS.search(str(data.get("path") or ""))
    result = data.get("result")
    found = result if isinstance(result, dict) else {}
    project = _int_or_none(match.group("project") if match else None)
    dataset = _int_or_none(match.group("dataset") if match else None) or _int_or_none(
        found.get("dataset_id")
    )
    view = _int_or_none(match.group("view") if match else None) or _int_or_none(
        found.get("dataview_id") or found.get("id")
    )
    if project is None or dataset is None or view is None:
        return None
    return ViewTarget(project, dataset, view)


def view_outcome(record: Any, target: ViewTarget) -> dict[str, Any]:
    """The state of the view a job finished on: its rows and columns, and whether it settled."""
    view = record if isinstance(record, dict) else {}
    summary = view_summary(view, None, target.dataset_id)
    keep = ("name", "rows", "cols", "columns", "pipeline_status", "in_sync")
    return {
        "kind": "view",
        "view_id": target.view_id,
        "dataset_id": target.dataset_id,
        "status": view.get("pipeline_status") or view.get("status"),
        **{key: summary[key] for key in keep if key in summary},
        "pipeline_running": bool(view.get("is_pipeline_running")),
    }


def with_derived_datasets(result: Any) -> Any:
    """Add ``derived_datasets`` beside a copy's ``derived``, whose direction misleads.

    The backend records ``derived`` as ``{"5214": [5224]}``: dataset 5214 is derived,
    and view 5224 exports into it. Read as "view 5224 of dataset 5214", it sent an agent
    to the wrong parent. ``derived_datasets`` says the same thing in words:
    ``[{"dataset_id": 5214, "from_view_ids": [5224]}]``. ``derived`` stays as it was.
    """
    derived = result.get("derived") if isinstance(result, dict) else None
    if not isinstance(derived, dict) or not derived:
        return result
    return {
        **result,
        "derived_datasets": [
            {"dataset_id": _int_or_none(dataset) or dataset, "from_view_ids": list(views or [])}
            for dataset, views in sorted(derived.items(), key=lambda item: str(item[0]))
        ],
    }


def copy_outcome(result: Any) -> dict[str, Any] | None:
    """A project copy's outcome: what was copied, what was skipped, and how each run ended.

    ``runs`` is what the backend records on the job as each copied view's run ends
    (``{view_id: {dataview_id, error}}``); a view queued but not yet in it is ``pending``.
    A backend that does not record runs yields no ``runs`` key.
    """
    if not isinstance(result, dict) or "view_map" not in result:
        return None
    outcome: dict[str, Any] = {
        "kind": "project_copy",
        "project_id": result.get("project_id"),
        "datasets": len(result.get("dataset_map") or {}),
        "views": len(result.get("view_map") or {}),
        "skipped": len(result.get("skipped") or []),
    }
    derived = with_derived_datasets(result).get("derived_datasets")
    if derived:
        outcome["derived_datasets"] = derived
    runs = result.get("runs")
    if isinstance(runs, dict):
        outcome["runs"] = _run_summary(runs, result.get("run_views"))
    return outcome


def _run_summary(runs: dict[str, Any], queued: Any) -> dict[str, Any]:
    """Counts of run ends, each failure with its error, and the queued views not yet ended."""
    failed = [
        {"view_id": run.get("dataview_id", view_id), "error": run["error"]}
        for view_id, run in runs.items()
        if isinstance(run, dict) and run.get("error") is not None
    ]
    waiting = [view for view in queued or [] if str(view) not in runs]
    return {"ok": len(runs) - len(failed), "failed": failed, "pending": waiting}
