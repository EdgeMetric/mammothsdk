"""``view analyze``: the findings, plus what a caller reads next.

The backend route returns only ``findings``. Every agent trace followed it with a
``view get`` (rows, columns, state), a dataset read (its name and source) and a
pipeline read (how many steps the findings' ``seqs`` point into). This module shapes
one result per view from those same reads, and splits ``VIEW_ID,VIEW_ID`` into ids.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.services.listing import view_summary

#: Enough for every view a dashboard build traces in one call (mammothsdk#381 item 9: 16 views
#: took two calls at 12); the reads per view run concurrently.
MAX_VIEW_IDS = 50


def view_ids(raw: str) -> list[int]:
    """The view ids of ``5000`` or ``5000,5001`` (``;`` also separates), without repeats."""
    parts = [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    try:
        ids = list(dict.fromkeys(int(part) for part in parts))
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The view id argument '{raw}' is not an integer or a comma-separated list.",
            exit_status=EXIT_USAGE,
            hint="Pass one id (view analyze 5000) or several joined by commas (5000,5001).",
        ) from exc
    if not ids:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="No view id was given.",
            exit_status=EXIT_USAGE,
            hint="view analyze VIEW_ID[,VIEW_ID...]",
        )
    if len(ids) > MAX_VIEW_IDS:
        raise CliError(
            code="too_many_ids",
            message=f"view analyze accepts at most {MAX_VIEW_IDS} ids per call; got {len(ids)}.",
            exit_status=EXIT_USAGE,
            hint="Split the ids across more than one 'view analyze' call.",
        )
    return ids


def step_count(items: Any) -> int | None:
    """Pipeline steps in a pipeline-items read (its exports are not steps), or ``None``."""
    listed = items.get("items") if isinstance(items, dict) else None
    if not isinstance(listed, list):
        return None
    return sum(1 for item in listed if isinstance(item, dict) and item.get("item_type") == "task")


def lineage(tasks_read: Any) -> dict[str, Any] | None:
    """The other views a view's steps read, from a task-list read; ``None`` when unreadable.

    A join or lookup step names its other view as ``params.<OP>.DATAVIEW_ID`` (the step's own
    view is the top-level ``DATAVIEW_ID``). ``reads`` lists each such step in pipeline order;
    ``views_read`` the distinct views; ``text`` says it in one line, e.g. "joins view 107990
    (step 1, LEFT)". ILG friction 11-03 (#1): mapping 16 views' sources took one call per view.
    """
    tasks = tasks_read.get("tasks") if isinstance(tasks_read, dict) else None
    if not isinstance(tasks, list):
        return None
    ordered = sorted((task for task in tasks if isinstance(task, dict)), key=_sequence)
    reads: list[dict[str, Any]] = []
    for task in ordered:
        params = task.get("params")
        for op, spec in (params.items() if isinstance(params, dict) else ()):
            if not isinstance(spec, dict) or not isinstance(spec.get("DATAVIEW_ID"), int):
                continue
            read: dict[str, Any] = {
                "step": task.get("sequence"),
                "op": str(op).lower(),
                "view_id": spec["DATAVIEW_ID"],
            }
            if isinstance(spec.get("TYPE"), str):
                read["join_type"] = spec["TYPE"]
            reads.append(read)
    result: dict[str, Any] = {
        "views_read": sorted({read["view_id"] for read in reads}),
        "reads": reads,
        "text": "; ".join(_read_text(read) for read in reads) or "reads no other view",
    }
    if tasks_read.get("next"):
        result["partial"] = True
    return result


def _sequence(task: dict[str, Any]) -> int:
    """A task's pipeline position; 0 when the read left it out."""
    sequence = task.get("sequence")
    return sequence if isinstance(sequence, int) else 0


def _read_text(read: dict[str, Any]) -> str:
    """One cross-view step in words: "joins view 7 (step 2, LEFT)", "looks up view 9 (step 4)"."""
    verb = {"join": "joins", "lookup": "looks up"}.get(read["op"], f"{read['op']} reads")
    detail = f"step {read['step']}" + (f", {read['join_type']}" if "join_type" in read else "")
    return f"{verb} view {read['view_id']} ({detail})"


def analysis_entry(
    analysis: Any,
    view: dict[str, Any],
    dataset: dict[str, Any],
    steps: int | None,
    view_lineage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One view's result: its ``findings`` and, beside them, the view, its step count and
    the other views its steps read (``lineage``, when the task list was readable)."""
    findings = analysis.get("findings") if isinstance(analysis, dict) else None
    entry: dict[str, Any] = {
        "findings": findings if isinstance(findings, list) else [],
        "view": view_summary(view, dataset, dataset.get("id"), all_columns=True),
    }
    if steps is not None:
        entry["steps"] = steps
    if view_lineage is not None:
        entry["lineage"] = view_lineage
    return entry


def error_entry(view_id: int, error: CliError) -> dict[str, Any]:
    """One id's failure, as a list entry instead of a failed call."""
    return {"view_id": view_id, "code": error.code, "message": error.message}


def many_result(ids: list[int], outcomes: dict[int, dict[str, Any] | CliError]) -> dict[str, Any]:
    """``{"requested", "analyses", "errors"}``: one entry per id, in the order asked."""
    analyses = [
        {"view_id": view_id, **outcome}
        for view_id in ids
        if isinstance(outcome := outcomes[view_id], dict)
    ]
    errors = [
        error_entry(view_id, outcome)
        for view_id in ids
        if isinstance(outcome := outcomes[view_id], CliError)
    ]
    return {"requested": len(ids), "analyses": analyses, "errors": errors}
