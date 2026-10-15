"""Check authored dashboard figures against the board's own columns.

The backend accepts a figure over a column that is not on the board, or a
``sum`` over a text column, and only fails later in the bake (``bake_error`` in
``canvas get``) or bakes every value as null. These checks run locally against
the column profile the backend computes for the canvas
(``plan.hints._profiles``: ``name`` and ``type`` of ``measure``, ``date`` or
``dimension``), so a bad figure is named before or right after it is saved.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Iterable, Mapping
from typing import Any

from mammoth_cli.services.dashboard_review import _profiles

#: Aggregations that need a numeric measure; count and count_distinct do not.
NUMERIC_AGGS = frozenset({"sum", "avg", "mean", "average", "min", "max", "median"})

_MEASURE_KEYS = ("measure", "measure2", "measure_x", "measure_y", "measure_size")
_DIM_KEYS = ("dim", "col_dim", "row_dim", "series", "date_field")


def _figure_refs(figure: Mapping[str, Any]) -> list[tuple[str, str, str | None]]:
    """``(role, column, agg)`` for each column a figure names."""
    agg = str(figure["agg"]).lower() if isinstance(figure.get("agg"), str) else None
    refs: list[tuple[str, str, str | None]] = []
    for key in _MEASURE_KEYS:
        if isinstance(figure.get(key), str):
            refs.append(("measure", figure[key], agg))
    for key in ("measures", "extra_measures"):
        for item in figure.get(key) or []:
            name = item.get("field") if isinstance(item, Mapping) else item
            if isinstance(name, str):
                refs.append(("measure", name, agg))
    for kpi in figure.get("kpis") or []:
        if isinstance(kpi, Mapping) and isinstance(kpi.get("field"), str):
            kpi_agg = kpi.get("agg")
            refs.append(("measure", kpi["field"], str(kpi_agg).lower() if kpi_agg else None))
    for key in _DIM_KEYS:
        if isinstance(figure.get(key), str):
            refs.append(("dimension", figure[key], None))
    return refs


def _type_label(profile_type: Any) -> str:
    return {"measure": "NUMERIC", "date": "DATE"}.get(str(profile_type), "TEXT")


def figure_problems(
    figure: Mapping[str, Any],
    profiles: list[dict[str, Any]],
    *,
    derived: Iterable[str] = (),
    view_id: Any = None,
    where: str | None = None,
) -> list[dict[str, Any]]:
    """Structured problems for one figure: unknown columns, text measures under a numeric agg."""
    if not profiles:
        return []
    by_name = {str(p["name"]): p for p in profiles}
    folded = {name.casefold(): name for name in by_name}
    allowed = set(derived)
    problems: list[dict[str, Any]] = []
    for role, column, agg in _figure_refs(figure):
        if column in allowed:
            continue
        profile = by_name.get(column)
        if profile is None:
            near = folded.get(column.casefold())
            problems.append(
                {
                    "issue": "unknown_column",
                    "column": column,
                    "role": role,
                    "where": where,
                    "detail": (
                        f"unknown column '{column}': the dashboard has no such column"
                        + (f"; did you mean '{near}'?" if near else ".")
                    ),
                    "columns": sorted(by_name),
                }
            )
            continue
        if role == "measure" and agg in NUMERIC_AGGS and profile.get("type") != "measure":
            kind = _type_label(profile.get("type"))
            problem: dict[str, Any] = {
                "issue": "non_numeric_measure",
                "column": column,
                "column_type": kind,
                "agg": agg,
                "where": where,
                "detail": (
                    f"'{agg}' needs a NUMERIC measure but '{column}' is {kind}, so every value "
                    "would be null. Use agg count or count_distinct, or convert the column "
                    "to NUMERIC first."
                ),
            }
            if view_id is not None:
                spec = json.dumps({"conversions": [{"column": column, "to": "NUMERIC"}]})
                problem["fix"] = (
                    f"mammoth view transform convert-type {view_id} --input {shlex.quote(spec)}"
                )
            problems.append(problem)
    return problems


def canvas_figure_problems(canvas_doc: Any) -> list[dict[str, Any]]:
    """Problems for every authored figure and focus of a ``canvas get`` payload."""
    if not isinstance(canvas_doc, Mapping):
        return []
    canvas = canvas_doc.get("canvas")
    profiles = _profiles(canvas_doc)
    if not isinstance(canvas, Mapping) or not profiles:
        return []
    derived = [str(d.get("id")) for d in canvas.get("derived") or [] if isinstance(d, Mapping)]
    source = canvas.get("dataset")
    view_id = source.get("dataview_id") if isinstance(source, Mapping) else None
    problems: list[dict[str, Any]] = []
    containers = [canvas, *[p for p in canvas.get("pages") or [] if isinstance(p, Mapping)]]
    for container in containers:
        label = container.get("title") or container.get("id")
        figures = [*(container.get("added") or [])]
        if isinstance(container.get("focus"), Mapping):
            figures.append(container["focus"])
        for figure in figures:
            if isinstance(figure, Mapping):
                title = figure.get("title") or figure.get("kind")
                where = f"page '{label}', figure '{title}'" if label else f"figure '{title}'"
                problems += figure_problems(
                    figure, profiles, derived=derived, view_id=view_id, where=where
                )
    return problems


def bake_error_problem(canvas_doc: Any) -> dict[str, Any] | None:
    """The backend's own ``meta.bake_error`` as a structured problem, when set."""
    meta = canvas_doc.get("meta") if isinstance(canvas_doc, Mapping) else None
    error = meta.get("bake_error") if isinstance(meta, Mapping) else None
    if not error:
        return None
    text = error if isinstance(error, str) else json.dumps(error, default=str)
    return {"issue": "bake_error", "detail": f"the dashboard did not bake: {text}"}
