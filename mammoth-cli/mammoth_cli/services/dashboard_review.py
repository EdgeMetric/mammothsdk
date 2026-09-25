"""Check a dashboard against what its data holds, after each authoring step.

The skill tells an agent to put the money on the board and to decide on
blanks, but an agent that authors the canvas directly never reads that part
(cold-agent eval, CLI 2.0.40: counts only, blanks undecided). The check runs
where the agent already looks: the result of ``create-blank``, ``canvas
save`` and ``pages add``. It uses the column profile the dashboard backend
computes for the canvas (``plan.hints._profiles``), so it costs one read.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from typing import Any

CANVAS_GET = "mammoth.api.dashboards.DashboardsAPI.canvas_get"

#: A dashboard reads the view as it was when the dashboard was made; a column
#: added later is not a measure there (release, CLI 2.0.41: pages add refused
#: ``revenue`` on a dashboard made before it, and ``swap-data`` did not always
#: pick it up). A dashboard made after the column sees it.
NEW_COLUMN_NOTE = (
    "A dashboard sees only the columns the view had when the dashboard was made. "
    "Run each fix first, then make a new dashboard (dashboard create-blank) and build "
    "on that one; delete this one if you made it for this task."
)
#: The same fact, for the upload result, where no dashboard exists yet.
UPLOAD_NOTE = (
    "Run these before you make a dashboard: a dashboard sees only the columns "
    "the view had when the dashboard was made."
)

_MONEY = re.compile(
    r"price|amount|revenue|sales|cost|spend|fee|income|profit|margin|total|value|gmv|arr|mrr",
    re.IGNORECASE,
)
_UNIT = re.compile(r"price|rate|unit|per[_ ]", re.IGNORECASE)
_QUANTITY = re.compile(r"^(qty|quantity|units?|count|volume|pieces|items?)\b", re.IGNORECASE)
_MEASURE_KEYS = ("measure", "measure2", "measure_x", "measure_y", "measure_size")
_LIST_MEASURE_KEYS = ("measures", "extra_measures")


def _profiles(canvas_doc: Mapping[str, Any]) -> list[dict[str, Any]]:
    plan = canvas_doc.get("plan")
    hints = plan.get("hints") if isinstance(plan, Mapping) else None
    profiles = hints.get("_profiles") if isinstance(hints, Mapping) else None
    return [p for p in profiles or [] if isinstance(p, dict) and isinstance(p.get("name"), str)]


def _charts(canvas: Mapping[str, Any]) -> Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Yield ``(container, figure)`` for every authored figure and focus."""
    containers = [canvas, *[p for p in canvas.get("pages") or [] if isinstance(p, Mapping)]]
    for container in containers:
        focus = container.get("focus")
        if isinstance(focus, Mapping):
            yield container, focus
        for figure in container.get("added") or []:
            if isinstance(figure, Mapping):
                yield container, figure


def _used(canvas: Mapping[str, Any]) -> tuple[set[str], set[str], list[tuple[str, str]]]:
    """Measures and dimensions the board uses, and ``(measure, agg)`` pairs."""
    derived = {
        str(d.get("id")): [d.get("numerator"), d.get("denominator")]
        for d in canvas.get("derived") or []
        if isinstance(d, Mapping)
    }
    measures: set[str] = set()
    dims: set[str] = set()
    aggs: list[tuple[str, str]] = []

    def add(name: Any, agg: Any) -> None:
        if not isinstance(name, str):
            return
        for part in derived.get(name, [name]):
            if isinstance(part, str):
                measures.add(part)
                aggs.append((part, str(agg or "sum").lower()))

    for _, figure in _charts(canvas):
        agg = figure.get("agg")
        for key in _MEASURE_KEYS:
            add(figure.get(key), agg)
        for key in _LIST_MEASURE_KEYS:
            for name in figure.get(key) or []:
                add(name.get("field") if isinstance(name, Mapping) else name, agg)
        for kpi in figure.get("kpis") or []:
            if isinstance(kpi, Mapping):
                add(kpi.get("field"), kpi.get("agg"))
        for key in ("dim", "col_dim", "row_dim", "series", "date_field"):
            if isinstance(figure.get(key), str):
                dims.add(figure[key])
    return measures, dims, aggs


def _math_fix(view_id: Any, dataset_id: Any, quantity: str, price: str) -> str:
    spec = json.dumps(
        {
            "dataset_id": dataset_id if dataset_id is not None else "DATASET_ID",
            "expression": f"{quantity} * {price}",
            "new_column": "revenue",
        }
    )
    return f"mammoth view transform math {view_id} --input '{spec}'"


def profiles_from_view(
    metadata: Iterable[Mapping[str, Any]], rows: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """A stand-in for ``plan.hints._profiles`` from view metadata and a data page.

    A blank canvas has no profile until its first bake, so ``create-blank``
    builds one: NUMERIC columns are measures, and ``nullRate`` is the share of
    blank values in the rows given (display-name keyed).
    """
    materialised = [row for row in rows if isinstance(row, Mapping)]
    profiles: list[dict[str, Any]] = []
    for column in metadata:
        name = column.get("display_name")
        if not isinstance(name, str):
            continue
        kind = str(column.get("type") or "").upper()
        profile: dict[str, Any] = {
            "name": name,
            "type": "measure" if kind == "NUMERIC" else "date" if kind == "DATE" else "dimension",
        }
        # Only rows that carry the column count; a column the page left out
        # is unknown, not blank.
        values = [row[name] for row in materialised if name in row]
        blank = sum(1 for v in values if v is None or (isinstance(v, str) and not v.strip()))
        if blank:
            profile["nullRate"] = blank / len(values)
        profiles.append(profile)
    return profiles


def review(
    canvas_doc: Any,
    dataset_id: int | None = None,
    fallback_profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return warnings about money and blanks for a canvas read.

    Args:
        canvas_doc: A ``dashboard canvas get`` payload (``canvas``, ``plan``).
        dataset_id: The view's parent dataset, for the suggested command.

    Returns:
        ``money_not_shown``, ``unit_price_summed`` and ``blank_values``
        records (``issue``, ``detail``, optional ``fix``); empty when none.
    """
    if not isinstance(canvas_doc, Mapping):
        return []
    canvas = canvas_doc.get("canvas")
    if not isinstance(canvas, Mapping):
        return []
    profiles = _profiles(canvas_doc) or list(fallback_profiles or [])
    if not profiles:
        return []
    source = canvas.get("dataset")
    view_id = source.get("dataview_id") if isinstance(source, Mapping) else None
    view_ref = view_id if view_id is not None else "VIEW_ID"
    measures, dims, aggs = _used(canvas)
    numeric = [p for p in profiles if p.get("type") == "measure"]
    unit_prices = [
        p["name"]
        for p in numeric
        if p.get("perUnit") is True or (_UNIT.search(p["name"]) and _MONEY.search(p["name"]))
    ]
    money = [
        p["name"] for p in numeric if _MONEY.search(p["name"]) and p["name"] not in unit_prices
    ]
    quantities = [
        p["name"] for p in numeric if p.get("semantic") == "count" or _QUANTITY.search(p["name"])
    ]
    warnings: list[dict[str, Any]] = []
    shows_money = any(name in measures for name in money + unit_prices)
    if (money or unit_prices) and not shows_money:
        if money:
            detail = (
                f"The view has money ({', '.join(money)}) but no chart or KPI shows it. "
                f"Add a KPI and a chart with the sum of {money[0]}."
            )
            warnings.append({"issue": "money_not_shown", "detail": detail})
        else:
            record: dict[str, Any] = {
                "issue": "money_not_shown",
                "detail": (
                    f"The view has a unit price ({', '.join(unit_prices)}) but no chart shows "
                    "money. A unit price is not revenue: "
                    + (
                        f"add revenue = {quantities[0]} * {unit_prices[0]}, then chart its sum."
                        if quantities
                        else "chart revenue, not the sum of the price."
                    )
                ),
            }
            if quantities:
                record["fix"] = _math_fix(view_ref, dataset_id, quantities[0], unit_prices[0])
            warnings.append(record)
    summed = sorted({name for name, agg in aggs if name in unit_prices and agg == "sum"})
    if summed:
        record = {
            "issue": "unit_price_summed",
            "detail": (
                f"A chart sums the unit price {summed[0]}; that total means nothing. "
                + (
                    f"Chart the sum of revenue = {quantities[0]} * {summed[0]} instead."
                    if quantities
                    else "Use avg, or chart revenue instead."
                )
            ),
        }
        if quantities:
            record["fix"] = _math_fix(view_ref, dataset_id, quantities[0], summed[0])
        warnings.append(record)
    shown = measures | dims
    for profile in profiles:
        name = profile["name"]
        rate = profile.get("nullRate") or profile.get("emptyRate") or 0
        if not isinstance(rate, (int, float)) or rate <= 0:
            continue
        if shown and name not in shown:
            continue
        warnings.append(
            {
                "issue": "blank_values",
                "column": name,
                "detail": (
                    f"{round(rate * 100)}% of {name} is blank. Say in your report what you "
                    "did: filled, filtered, or kept (and how the board shows them)."
                ),
            }
        )
    return warnings


def upload_hints(
    view_id: Any,
    metadata: Iterable[Mapping[str, Any]],
    rows: Iterable[Mapping[str, Any]],
    dataset_id: Any = None,
    text_numbers: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """The money warnings for a new view, before any dashboard exists.

    The fix is cheapest here: a column added before ``create-blank`` is on
    the dashboard, one added after is not (``NEW_COLUMN_NOTE``).
    ``text_numbers`` are the columns ``column_warnings`` found to be numbers
    stored as text; they count as numbers here, and the warning says to
    convert them first.
    """
    pending = set(text_numbers)
    profiles = [
        {**profile, "type": "measure"} if profile["name"] in pending else profile
        for profile in profiles_from_view(metadata, rows)
    ]
    canvas_doc = {"canvas": {"dataset": {"dataview_id": view_id}}}
    warnings = []
    # Blanks are already in the upload's column_warnings.
    for warning in review(canvas_doc, dataset_id, profiles):
        if warning["issue"] == "blank_values":
            continue
        # No board exists yet: drop the "no chart shows it" clause.
        detail = (
            str(warning["detail"])
            .replace(" but no chart shows money", "")
            .replace(" but no chart or KPI shows it", "")
        )
        convert = sorted(name for name in pending if name in detail)
        if convert:
            detail = (
                f"Convert {', '.join(convert)} to NUMERIC first (see column_warnings). " + detail
            )
        warnings.append({**warning, "detail": detail})
    return warnings


def columns_not_on_dashboard(
    canvas_doc: Any, view_columns: Iterable[Mapping[str, Any]] | None
) -> list[dict[str, Any]]:
    """Warn about view columns that the dashboard's profile does not have.

    A dashboard sees the view as it was when the dashboard was made
    (``NEW_COLUMN_NOTE``), so a column added later cannot be charted there.
    ``view_columns`` is the view's own profile (``profiles_from_view``).
    """
    known = {p["name"] for p in _profiles(canvas_doc)} if isinstance(canvas_doc, Mapping) else set()
    if not known or not view_columns:
        return []
    missing = [
        str(c["name"])
        for c in view_columns
        if isinstance(c.get("name"), str) and c["name"] not in known
    ]
    if not missing:
        return []
    canvas = canvas_doc.get("canvas")
    source = canvas.get("dataset") if isinstance(canvas, Mapping) else None
    view_id = source.get("dataview_id") if isinstance(source, Mapping) else None
    spec = json.dumps({"params": {"dataview_id": view_id if view_id is not None else "VIEW_ID"}})
    return [
        {
            "issue": "columns_not_on_dashboard",
            "columns": missing,
            "detail": (
                f"The view has {', '.join(missing)}, but this dashboard was made before "
                f"and cannot chart {'it' if len(missing) == 1 else 'them'}. Make a new "
                "dashboard on the view and build there."
            ),
            "fix": f"mammoth dashboard create-blank --input '{spec}' --yes",
        }
    ]


def has_profiles(canvas_doc: Any) -> bool:
    """Whether a canvas read carries the backend's column profile."""
    return isinstance(canvas_doc, Mapping) and bool(_profiles(canvas_doc))
