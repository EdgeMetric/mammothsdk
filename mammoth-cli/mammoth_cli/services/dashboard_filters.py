"""Edit a board's filter controls: the canvas's root ``filters[]`` (and ``filter_order``).

A filter control is what lets ONE board answer "per region" or "per month": the
viewer picks the value. It is declared as ``{"field": COLUMN, "control": ...,
"label": ..., "default": [...]}``; the backend validates the column and the
control against the column's type when the canvas is saved.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.services.dashboard_review import _profiles

# Controls per column type (the backend's rule; it only checks at bake, after the save).
# A numeric column may also be a 0/1 flag, which takes the selection lists too.
_SELECTION = ("multi", "dropdown", "chips", "search")
_CONTROLS = {
    "dimension": _SELECTION,
    "measure": (*_SELECTION, "range"),
    "date": ("range", "motion"),
}


def declared(canvas: dict[str, Any]) -> list[dict[str, Any]]:
    """The filter controls the canvas declares, in order."""
    return [f for f in canvas.get("filters") or [] if isinstance(f, dict)]


def with_filter(canvas: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    """A copy of ``canvas`` declaring ``entry``; a filter on the same field is replaced."""
    field = entry["field"]
    kept = [f for f in declared(canvas) if f.get("field") != field]
    edited = {**canvas, "filters": [*kept, entry]}
    order = canvas.get("filter_order")
    if order is not None and field not in order:
        edited["filter_order"] = [*order, field]
    return edited


def without_filter(canvas: dict[str, Any], field: str) -> dict[str, Any]:
    """A copy of ``canvas`` without the filter on ``field``; fails when there is none."""
    current = declared(canvas)
    if field not in {f.get("field") for f in current}:
        names = ", ".join(str(f.get("field")) for f in current) or "none"
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The board has no filter on '{field}'. Declared filters: {names}.",
            exit_status=EXIT_USAGE,
            hint="List them with 'mammoth dashboard filter list DASHBOARD_ID'.",
        )
    edited = {**canvas, "filters": [f for f in current if f.get("field") != field]}
    if canvas.get("filter_order") is not None:
        edited["filter_order"] = [name for name in canvas["filter_order"] if name != field]
    return edited


def check_filter(canvas_doc: dict[str, Any], entry: dict[str, Any]) -> None:
    """Refuse a filter on a column the board lacks, or a control its type cannot take.

    The backend checks this only when it bakes (after the save), so a wrong column or
    control would be stored and the board would show a stale bake. A canvas read without
    a column profile (a blank board) is not checked.
    """
    columns = {p["name"]: p.get("type") for p in _profiles(canvas_doc)}
    if not columns:
        return
    field, control = entry["field"], entry.get("control")
    if field not in columns:
        raise _refuse(f"The board has no column '{field}'. Columns: {', '.join(columns)}.")
    allowed = _CONTROLS.get(str(columns[field]))
    if control is not None and allowed and control not in allowed:
        raise _refuse(
            f"A {columns[field]} column '{field}' cannot take control '{control}'. "
            f"Use one of: {', '.join(allowed)} (or leave control out)."
        )


def _refuse(message: str) -> CliError:
    return CliError(code=CODE_INVALID_ARGUMENT, message=message, exit_status=EXIT_USAGE)
