"""An Explore card as one dashboard tile: a port of ``explore-to-figure.js`` in the web app.

The web app's "Add to dashboard" turns a card into a figure (an ``AddedFigure`` as the canvas
stores it), an optional banded dimension (a number card's ranges) and a note for everything that
does not carry over exactly. The same mapping is here, so a card added from the CLI is the tile the
web app would add. Pure: the buckets a number card draws arrive as an argument.
"""

from __future__ import annotations

import math
from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.services.explore_card_edit import (
    CHART,
    DATE,
    DATE_LEVELS,
    NUMERIC,
    TEXT,
    number_with_commas,
)

LIST_TOP_N = 10
PARTS_TOP_N = {"donut": 7, "treemap": 24}
MAX_FILLED_BANDS = 60
BLANK_LABEL = "(blank)"

_AGG = {
    "COUNT": "count",
    "DISTINCT_COUNT": "countDistinct",
    "SUM": "sum",
    "AVG": "avg",
    "MIN": "min",
    "MAX": "max",
    "STDDEV": "stddev",
}
_AGG_LABEL = {
    "count": "Count",
    "countDistinct": "Distinct count",
    "sum": "Sum",
    "avg": "Average",
    "min": "Min",
    "max": "Max",
    "stddev": "Std dev",
}
_DATE_UNIT = {"YEAR": "year", "MONTH": "month"}
_UNIT_LABEL = {
    "year": "year",
    "month": "month",
    "DAY": "Day",
    "HOUR": "Hour",
    "MINUTE": "Minute",
    "SECOND": "Second",
}

#: Why a card cannot become a tile, as the web app words it.
UNSUPPORTED = {
    "query_card": "This card filters rows and has no chart to add.",
    "no_column": "This card's column is no longer in the view.",
    "no_target": "This card's value column is no longer in the view.",
    "no_agg": "Dashboards can't show this card's value.",
    "no_buckets": "The card lists no values to draw.",
}

_NOTE = {
    "top_n": "Shows the top {count} values. The card lists all of them.",
    "date_unit": "{from_} buckets become {to}. Dashboards group dates by month, quarter or year.",
    "over_time": "Drawn over time, like the card's columns view.",
    "as_ranges": "Drawn as ranges, like the card's columns view.",
    "ranges_fixed": (
        "The ranges are fixed when you add it. Values that arrive later and fall outside them "
        "land in the first or last bar."
    ),
    "values_fixed": (
        "Shows the same values as the card, {first} to {last}. A value that arrives later "
        "outside them lands in the first or last bar."
    ),
    "sorted_by_name": "Picks the top {count} by value and shows them by name.",
    "drill_left_off": "Shows every value. Drilling in is a filter, so it isn't added.",
    "filters_left_off": (
        "Shows all of the view. {count} explore filter(s) aren't added to dashboards."
    ),
}


def refuse_card(reason: str) -> CliError:
    """The refusal for a card the web app would not add, with the web app's reason."""
    return CliError(
        code=CODE_INVALID_ARGUMENT,
        message=UNSUPPORTED[reason],
        exit_status=EXIT_USAGE,
        details={"reason": reason},
    )


def _note(code: str, **params: Any) -> dict[str, Any]:
    return {
        "code": code,
        "text": _NOTE[code].format(**params),
        **({"params": params} if params else {}),
    }


def _source_name(column: dict[str, Any]) -> str:
    """The name a board knows the column by (the original name, not a display-only rename)."""
    return str(column.get("original_name") or column["display_name"])


def figure_title(agg: str, measure: str | None, by: str) -> str:
    """ "Sum of Amount by Region" / "Count by Region"."""
    if agg == "count":
        return f"Count by {by}"
    return f"{_AGG_LABEL[agg]} of {measure} by {by}"


def _round(value: float) -> float:
    return float(f"{value:.12g}")


def _bucket_starts(buckets: list[Any]) -> list[float]:
    return sorted({float(b) for b in buckets if b is not None and math.isfinite(float(b))})


def band_edges(buckets: list[Any], level: int) -> list[tuple[float, float]]:
    """The ``[start, end)`` edges of a number card's buckets, empty ones between put back."""
    width = 10.0 ** int(level)
    seen = _bucket_starts(buckets)
    starts = seen
    if len(seen) > 1:
        span = round((seen[-1] - seen[0]) / width) + 1
        if span <= MAX_FILLED_BANDS:
            grid = [_round(seen[0] + k * width) for k in range(span)]
            if all(v in set(grid) for v in seen):
                starts = grid
    return [
        (start, starts[i + 1] if i < len(starts) - 1 else _round(start + width))
        for i, start in enumerate(starts)
    ]


def _compact(value: float) -> str:
    if abs(value) < 10000:
        return number_with_commas(value)
    for limit, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= limit:
            return f"{round(value / limit, 2):g}{suffix}"
    return number_with_commas(value)


def _is_single_value(edges: list[tuple[float, float]]) -> bool:
    return all(float(s).is_integer() and _round(e - s) == 1 for s, e in edges)


def bands_from_buckets(buckets: list[Any], level: int) -> list[dict[str, Any]]:
    """Named half-open bands, open below at the first and above at the last."""
    edges = band_edges(buckets, level)
    single = _is_single_value(edges)
    return [
        {
            "label": str(int(s)) if single else f"{_compact(s)}–{_compact(e)}",
            "lo": None if i == 0 else s,
            "hi": None if i == len(edges) - 1 else e,
        }
        for i, (s, e) in enumerate(edges)
    ]


def _value_of(
    card: dict[str, Any], columns: list[dict[str, Any]]
) -> tuple[str, str | None, str | None]:
    """The card's descriptor aggregation, the column it reads and that column's display name."""
    kind = (card.get("aggregation") or {}).get("type") or "COUNT"
    agg = _AGG.get(kind)
    if not agg:
        raise refuse_card("no_agg")
    if agg == "count":
        return agg, None, None
    target = next(
        (c for c in columns if c["internal_name"] == card["aggregation"].get("targetColId")), None
    )
    if target is None:
        raise refuse_card("no_target")
    return agg, _source_name(target), str(target["display_name"])


def _sort_of(card: dict[str, Any]) -> tuple[str, bool]:
    key, direction = (card.get("sortBy") or [["unformatted", "DESC"]])[0]
    if key == "value":
        return ("alpha" if direction == "ASC" else "alpha_desc"), True
    return ("asc" if direction == "ASC" else "desc"), False


def card_level(card: dict[str, Any]) -> Any:
    """The level a card draws with: its granularity, else its first chart's level."""
    granularity = card.get("granularity")
    if isinstance(granularity, dict) and granularity.get("id") is not None:
        return granularity["id"]
    charts = card.get("charts") or [{}]
    return charts[0].get("level")


def card_view(card: dict[str, Any], column_type: str) -> str:
    """The view a card draws (``getCardView``)."""
    allowed = {
        TEXT: ("list", "donut", "treemap"),
        NUMERIC: ("columns", "list"),
        DATE: ("columns", "timeline", "list"),
    }.get(column_type, ())
    chart = {"columns", "timeline"}
    view = card.get("view")
    if view in allowed and ((view in chart) == (card.get("renderType") == CHART)):
        return str(view)
    return "columns" if card.get("renderType") == CHART else "list"


def card_to_figure(
    card: dict[str, Any],
    column: dict[str, Any],
    columns: list[dict[str, Any]],
    buckets: list[Any] | None = None,
    value_count: int | None = None,
    filters_left_off: int = 0,
) -> dict[str, Any]:
    """The tile for ``card``: ``{figure, banded, notes}``; raises the web app's refusal otherwise.

    ``buckets`` are the values a NUMERIC card lists at its (fixed) level; ``value_count`` is how
    many values a TEXT card lists, when known.
    """
    if card.get("kind"):
        raise refuse_card("query_card")
    agg, measure, measure_label = _value_of(card, columns)
    column_type = str(column.get("type") or "").upper()
    view = card_view(card, column_type)
    notes: list[dict[str, Any]] = []
    banded: dict[str, Any] | None = None
    if column_type == DATE:
        figure, by = _date_figure(card, column, agg, view, notes)
    elif column_type == NUMERIC:
        figure, banded = _number_figure(card, column, agg, view, buckets or [], notes)
        by = str(column["display_name"])
    else:
        figure = _text_figure(card, column, agg, view, value_count, notes)
        by = str(column["display_name"])
    if measure:
        figure["measure"] = measure
    figure["title"] = figure_title(agg, measure_label, by)
    if len(card.get("charts") or []) > 1 and card.get("renderType") == CHART:
        notes.append(_note("drill_left_off"))
    if filters_left_off > 0:
        notes.append(_note("filters_left_off", count=filters_left_off))
    return {"figure": figure, "banded": banded, "notes": notes}


def _date_figure(
    card: dict[str, Any], column: dict[str, Any], agg: str, view: str, notes: list[dict[str, Any]]
) -> tuple[dict[str, Any], str]:
    level = card_level(card)
    from_ = level if isinstance(level, str) and level != "AUTO" else "MONTH"
    unit = _DATE_UNIT.get(from_, "month")
    if from_ not in _DATE_UNIT:
        notes.append(_note("date_unit", from_=_UNIT_LABEL[from_], to=_UNIT_LABEL[unit]))
    if view == "list":
        notes.append(_note("over_time"))
    kind = "line" if view == "timeline" else "bar"
    figure = {
        "kind": kind,
        "agg": agg,
        "date_bucket": {"field": _source_name(column), "unit": unit},
    }
    return figure, f"{column['display_name']} ({_UNIT_LABEL[unit]})"


def _number_figure(
    card: dict[str, Any],
    column: dict[str, Any],
    agg: str,
    view: str,
    buckets: list[Any],
    notes: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    level = card_level(card)
    bands = bands_from_buckets(buckets, level) if isinstance(level, int) else []
    if not bands:
        raise refuse_card("no_buckets")
    if view == "list":
        notes.append(_note("as_ranges"))
    if _is_single_value(band_edges(buckets, level)):
        notes.append(_note("values_fixed", first=bands[0]["label"], last=bands[-1]["label"]))
    else:
        notes.append(_note("ranges_fixed"))
    banded = {
        "label": f"{column['display_name']} ranges",
        "source": _source_name(column),
        "bands": bands,
        "other_label": BLANK_LABEL,
    }
    return {"kind": "bar", "agg": agg, "sort": "alpha"}, banded


def _text_figure(
    card: dict[str, Any],
    column: dict[str, Any],
    agg: str,
    view: str,
    value_count: int | None,
    notes: list[dict[str, Any]],
) -> dict[str, Any]:
    kind = view if view in ("donut", "treemap") else "hbar"
    top_n = PARTS_TOP_N.get(kind, LIST_TOP_N)
    figure: dict[str, Any] = {
        "kind": kind,
        "agg": agg,
        "dim": _source_name(column),
        "top_n": top_n,
        "blank_label": BLANK_LABEL,
    }
    if kind != "hbar":
        figure["sort"] = "desc"
        return figure
    sort, by_name = _sort_of(card)
    figure["sort"] = sort
    if value_count is None or value_count > top_n:
        notes.append(_note("top_n", count=top_n))
    if by_name:
        notes.append(_note("sorted_by_name", count=top_n))
    return figure


def count_filters(cards: list[dict[str, Any]]) -> int:
    """How many cards carry a filter; none of them travel to the dashboard."""
    return sum(1 for card in cards if card.get("condition"))


__all__ = [
    "DATE_LEVELS",
    "UNSUPPORTED",
    "band_edges",
    "bands_from_buckets",
    "card_level",
    "card_to_figure",
    "count_filters",
    "figure_title",
    "refuse_card",
]
