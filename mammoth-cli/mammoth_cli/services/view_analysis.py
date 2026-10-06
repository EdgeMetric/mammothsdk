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

#: More ids than this in one call is a pasted list, not a lookup (same ceiling as ``schema get``).
MAX_VIEW_IDS = 12


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


def analysis_entry(
    analysis: Any, view: dict[str, Any], dataset: dict[str, Any], steps: int | None
) -> dict[str, Any]:
    """One view's result: its ``findings`` and, beside them, the view and its step count."""
    findings = analysis.get("findings") if isinstance(analysis, dict) else None
    entry: dict[str, Any] = {
        "findings": findings if isinstance(findings, list) else [],
        "view": view_summary(view, dataset, dataset.get("id"), all_columns=True),
    }
    if steps is not None:
        entry["steps"] = steps
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
