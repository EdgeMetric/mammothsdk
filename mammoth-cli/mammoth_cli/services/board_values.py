"""The evaluated numbers of a board a write just built or changed.

``dashboard v3 generate`` and ``dashboard chat edit`` return card and tile
*definitions*; the numbers are only produced when the board's baked
descriptors are evaluated. Without them an agent cannot tell a KPI that reads
21.9% from one that reads 14.9%, and reports what it has not seen.

The bake binds every KPI card (``<page>:kpi:<n>``) and every added tile
(``<page>:add:<key>``) to descriptor ids (``canvas get`` ``meta.figures``).
:func:`board_values` reads that binding and evaluates the ids in ONE
``dashboard descriptor-data`` call -- the backend's own evaluation of the
already-baked descriptors, not a recomputation here.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CANVAS_GET = "mammoth.api.dashboards.DashboardsAPI.canvas_get"
DESCRIPTOR_DATA = "mammoth.api.dashboards.DashboardsAPI.descriptor_data"

#: Rows of a grouped tile kept per series; ``row_count`` says how many there are.
TILE_ROW_CAP = 10
_KINDS = {"kpi": "kpi", "add": "tile"}
_API_SUFFIX = "/api/v2"


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def dashboard_link(base_url: str, workspace_id: int, dashboard_id: int) -> str:
    """The web app address of a v3 board, from the API base url."""
    origin = base_url.rstrip("/")
    origin = origin[: -len(_API_SUFFIX)] if origin.endswith(_API_SUFFIX) else origin
    return f"{origin}/workspaces/{workspace_id}/publish/{dashboard_id}"


def figure_bindings(canvas_doc: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every KPI card and tile with the descriptor ids that carry its number.

    Returns ``{"figure", "kind", "label", "descriptors": {series: id}}`` in
    figure order. Detail tables and filter controls are not numbers and are
    left out.
    """
    meta = canvas_doc.get("meta")
    figures = meta.get("figures") if isinstance(meta, Mapping) else None
    if not isinstance(figures, Mapping):
        return []
    labels = _labels(canvas_doc)
    bindings: list[dict[str, Any]] = []
    for figure, entry in figures.items():
        parts = str(figure).split(":")
        kind = _KINDS.get(parts[1]) if len(parts) == 3 else None
        descriptors = entry.get("descriptors") if isinstance(entry, Mapping) else None
        if kind is None or not isinstance(descriptors, Mapping) or not descriptors:
            continue
        bindings.append(
            {
                "figure": str(figure),
                "kind": kind,
                "label": labels.get(str(figure)),
                "descriptors": {str(name): str(did) for name, did in descriptors.items()},
            }
        )
    return bindings


def _labels(canvas_doc: Mapping[str, Any]) -> dict[str, str]:
    """``figure id -> title`` for the cards and tiles the canvas names, best effort."""
    canvas = canvas_doc.get("canvas")
    if not isinstance(canvas, Mapping):
        return {}
    pages = [("p1", canvas)]
    for page in canvas.get("pages") or []:
        if isinstance(page, Mapping) and isinstance(page.get("id"), str):
            pages.append((page["id"], page))
    labels: dict[str, str] = {}
    for page_id, page in pages:
        focus = page.get("focus")
        kpis = focus.get("kpis") if isinstance(focus, Mapping) else None
        for index, card in enumerate(kpis or []):
            _put_label(labels, f"{page_id}:kpi:{index}", card, ("label", "title"))
        for index, tile in enumerate(page.get("added") or []):
            key = tile.get("id") if isinstance(tile, Mapping) and tile.get("id") else index
            _put_label(labels, f"{page_id}:add:{key}", tile, ("title", "label"))
    return labels


def _put_label(labels: dict[str, str], figure: str, item: Any, fields: tuple[str, ...]) -> None:
    if not isinstance(item, Mapping):
        return
    for field in fields:
        if isinstance(item.get(field), str) and item[field]:
            labels[figure] = item[field]
            return


def results_of(evaluated: Any) -> Mapping[str, Any] | None:
    """The ``{descriptor_id: {status, value|data}}`` map of a descriptor-data result."""
    evaluated = _dump(evaluated)
    for candidate in (evaluated, _get(evaluated, "response"), _get(evaluated, "result")):
        results = _get(candidate, "results")
        if isinstance(results, Mapping):
            return results
    return None


def _get(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, Mapping) else None


def _entry_values(entry: Any) -> dict[str, Any]:
    """One evaluated descriptor as ``{value}`` or ``{rows, row_count}``, or its error."""
    if not isinstance(entry, Mapping):
        return {"error": "no result"}
    if entry.get("status") not in (None, "success"):
        return {"status": entry.get("status"), "error": entry.get("error")}
    if "value" in entry:
        return {"value": entry["value"]}
    rows = entry.get("data")
    if isinstance(rows, list):
        return {"rows": rows[:TILE_ROW_CAP], "row_count": len(rows)}
    return {"error": "no value or rows in the result"}


def attach_values(
    bindings: list[dict[str, Any]], results: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Fill each figure with the evaluated numbers of its descriptors."""
    values: list[dict[str, Any]] = []
    for binding in bindings:
        series = {
            name: _entry_values(results.get(did)) for name, did in binding["descriptors"].items()
        }
        item = {key: binding[key] for key in ("figure", "kind", "label") if binding[key]}
        if binding["kind"] == "kpi" and set(series) == {"value"}:
            item.update(series["value"])
        else:
            item["series"] = series
        values.append(item)
    return values


def board_values(service: Any, dashboard_id: int) -> dict[str, Any]:
    """The evaluated KPI and tile numbers of ``dashboard_id`` (one descriptor-data call).

    Never raises for a board that will not evaluate: the write already
    happened, so a failed read comes back as ``{"unavailable": reason}``
    instead of hiding it or failing the write.
    """
    try:
        canvas_doc = _dump(service.call(CANVAS_GET, dashboard_id=dashboard_id))
        bindings = figure_bindings(canvas_doc if isinstance(canvas_doc, Mapping) else {})
        if not bindings:
            return {"unavailable": "the canvas has no KPI or tile bound to a descriptor"}
        ids = sorted({did for binding in bindings for did in binding["descriptors"].values()})
        body = {"params": {"descriptor_ids": ids}}
        evaluated = service.wait_if_job(
            _dump(service.call(DESCRIPTOR_DATA, dashboard_id=dashboard_id, body=body))
        )
        results = results_of(evaluated)
        if results is None:
            return {"unavailable": "descriptor-data returned no results"}
        return {"values": attach_values(bindings, results)}
    except Exception as exc:  # noqa: BLE001 -- the write already succeeded
        return {"unavailable": getattr(exc, "message", None) or str(exc)}
