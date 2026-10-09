"""Edits to the cards of an Explore panel, in the card config the web app saves and reads.

Each edit is what one control of the web app does to the Explore store
(``exploreSection.storePinia.js`` and the card header menus: the aggregator menu, the view
switcher, the sort menu and the filter actions), so the card a user opens in the web app is
the one written here. The functions are pure:
the two lookups they need from the view (the buckets a card lists, and the condition the suggestions
call reads out of a question) arrive as arguments.
"""

from __future__ import annotations

import copy
import math
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError

TEXT = "TEXT"
NUMERIC = "NUMERIC"
DATE = "DATE"
LIST = "list"
CHART = "chart"
BLANK = None

AGGREGATIONS = ("COUNT", "DISTINCT_COUNT", "SUM", "AVG", "MIN", "MAX", "STDDEV")
SORT_KEYS = {"metric": "unformatted", "value": "value"}
SORT_DIRECTIONS = ("ASC", "DESC")
VIEWS_BY_TYPE = {
    TEXT: ("list", "donut", "treemap"),
    NUMERIC: ("columns", "list"),
    DATE: ("columns", "timeline", "list"),
}
VIEW_RENDER_TYPE = {
    "list": LIST,
    "donut": LIST,
    "treemap": LIST,
    "columns": CHART,
    "timeline": CHART,
}
DATE_LEVELS = ("YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND")
NUMBER_LEVELS = tuple(range(10, -4, -1))
MIN_SEARCH_CHARS = 2

_DATE_GRANULARITY = {
    "YEAR": {"format": "%Y", "listFormat": "yyyy", "graphFormat": "yyyy"},
    "MONTH": {"format": "%b, %Y", "listFormat": "mmm 'yy", "graphFormat": "mmm-yyyy"},
    "DAY": {"format": "%d-%b-%Y", "listFormat": "dd-mmm-yyyy", "graphFormat": "d"},
    "HOUR": {"format": "%d-%b-%Y %H:%M", "listFormat": "dd-mmm-yyyy hh:00", "graphFormat": "h tt"},
    "MINUTE": {
        "format": "%d-%b-%Y %H:%M",
        "listFormat": "dd-mmm-yyyy hh:MM",
        "graphFormat": "h:MM tt",
    },
    "SECOND": {
        "format": "%d-%b-%Y %H:%M:%S",
        "listFormat": "dd-mmm-yyyy hh:MM:ss",
        "graphFormat": "h:MM:ss tt",
    },
}
_DATE_TEXT = "%Y-%m-%d %H:%M:%S"
_SEARCH_ID = "__search__"
_ASK_PREFIX = "__ask_"
_SCATTER_PREFIX = "__scatter_"
_COLUMN_OPS = {
    "metric": {"agg", "of"},
    "sort": {"by", "direction"},
    "view": {"view"},
    "level": {"level"},
    "filter": {"values", "level"},
    "exclude": {"values", "level"},
    "clear": set(),
    "remove": set(),
}
_QUERY_OPS = {
    "search": {"text", "columns", "exclude"},
    "scatter": {"x", "y", "rect", "exclude"},
    "ask": {"question", "exclude"},
}
_ALL_OPS = (*_COLUMN_OPS, *_QUERY_OPS)


@dataclass(frozen=True)
class Lookups:
    """What an edit needs from the view that the card config does not hold.

    ``buckets(column, level, only)`` returns the values the card lists for ``column`` (a metadata
    record) at ``level`` (``None`` for a text column): text as it is, numbers as numbers and
    dates as ``YYYY-MM-DD HH:MM:SS``. ``only`` limits a text column to those values.
    ``ask(question)`` returns the condition the suggestions call reads out of the question, or
    ``None`` when it understood none.
    """

    buckets: Callable[[dict[str, Any], Any, list[Any] | None], list[Any]]
    ask: Callable[[str], dict[str, Any] | None]


def _refuse(message: str, hint: str | None = None) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENT,
        message=message,
        exit_status=EXIT_USAGE,
        hint=hint or f"Each edit is an object with an \"op\", one of: {', '.join(_ALL_OPS)}.",
    )


def _choices(options: Any) -> str:
    return ", ".join(str(option) for option in options)


def _type_of(column: dict[str, Any]) -> str:
    return str(column.get("type") or "").upper()


def _name_of(column: dict[str, Any]) -> str:
    return str(column.get("display_name") or column.get("internal_name"))


def _column_named(columns: list[dict[str, Any]], name: Any, field: str) -> dict[str, Any]:
    if not isinstance(name, str):
        raise _refuse(f'"{field}" must be a column display name.')
    for column in columns:
        if column.get("display_name") == name:
            return column
    raise _refuse(
        f"{name!r} is not a column of this view. Columns: {_choices(map(_name_of, columns))}."
    )


def _require(edit: dict[str, Any], key: str) -> Any:
    if edit.get(key) is None:
        raise _refuse(f'The "{edit["op"]}" edit needs "{key}".')
    return edit[key]


def _only_keys(edit: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(edit) - allowed - {"op", "card"})
    if unknown:
        raise _refuse(
            f'The "{edit["op"]}" edit does not take {_choices(unknown)}. '
            f"It takes: {_choices(sorted({'op', 'card'} | allowed))}."
        )


def _is_query(card: dict[str, Any]) -> bool:
    return bool(card.get("kind"))


def _find(cards: list[dict[str, Any]], col_id: str) -> dict[str, Any] | None:
    return next((card for card in cards if card.get("colId") == col_id), None)


def open_card(
    cards: list[dict[str, Any]], columns: list[dict[str, Any]], name: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The saved card and column a column-card edit names."""
    column = _column_named(columns, name, "card")
    card = _find(cards, str(column["internal_name"]))
    if card is None:
        open_names = [
            _name_of(c)
            for card_ in cards
            if not _is_query(card_)
            for c in columns
            if c["internal_name"] == card_.get("colId")
        ]
        raise _refuse(
            f"No card is open for {name!r}. Open cards: {_choices(open_names) or 'none'}.",
            hint=(
                "Open it first: view explore-panel set VIEW_ID "
                '--input \'{"panel": {"columns": ["NAME"]}}\'.'
            ),
        )
    return card, column


def _sort_cards(cards: list[dict[str, Any]]) -> None:
    """Cards with a filter first, in their order; the web app does this after a filter change."""
    cards.sort(key=lambda card: 0 if card.get("condition") else 1)


# -- granularity ---------------------------------------------------------------------------------


def _number_level(value: Any) -> int:
    """The exponent of a bucket width the level menu offers (``1000`` is level 3)."""
    widths = [10.0**level for level in NUMBER_LEVELS]
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise _refuse(
            f'"level" must be a bucket width: {_choices(_width_text(w) for w in widths)}.'
        )
    level = round(math.log10(value))
    if level not in NUMBER_LEVELS or not math.isclose(10.0**level, value, rel_tol=1e-9):
        raise _refuse(
            f"{value} is not a bucket width the level menu offers. "
            f"Widths: {_choices(_width_text(w) for w in widths)}."
        )
    return level


def _width_text(width: float) -> str:
    return f"{int(width):,}" if width >= 1 else f"{width:g}"


def _granularity(column_type: str, level: Any) -> dict[str, Any]:
    """The granularity object the aggregator menu stores for a level."""
    if column_type == NUMERIC:
        exponent = _number_level(level)
        return {"id": exponent, "name": _width_text(10.0**exponent)}
    name = str(level).upper()
    if name not in DATE_LEVELS:
        raise _refuse(f"{level!r} is not a date level. Levels: {_choices(DATE_LEVELS)}.")
    return {"id": name, **_DATE_GRANULARITY[name]}


def _chart_template(index: int, column_type: str, level: Any = "AUTO") -> dict[str, Any] | None:
    next_level: Any = "AUTO"
    if level != "AUTO":
        if column_type == NUMERIC:
            next_level = level - 1
        else:
            position = DATE_LEVELS.index(level)
            next_level = DATE_LEVELS[position + 1] if position < len(DATE_LEVELS) - 1 else "AUTO"
        if next_level == "AUTO":
            return None
    return {"queryIndex": index, "activeValues": [], "level": next_level}


# -- metric, sort, view, level ---------------------------------------------------------------------


def _edit_metric(
    card: dict[str, Any],
    column: dict[str, Any],
    edit: dict[str, Any],
    columns: list[dict[str, Any]],
) -> None:
    agg = str(_require(edit, "agg")).upper()
    if agg not in AGGREGATIONS:
        raise _refuse(f"{edit['agg']!r} is not an aggregation. Choices: {_choices(AGGREGATIONS)}.")
    format_ = (card.get("aggregation") or {}).get("format") or {"separator": True}
    if agg == "COUNT":
        if edit.get("of") is not None:
            raise _refuse('COUNT counts rows and takes no "of" column.')
        card["aggregation"] = {
            "type": agg,
            "targetColId": None,
            "headerName": "Count",
            "format": format_,
        }
        return
    target = _column_named(columns, _require(edit, "of"), "of")
    if agg != "DISTINCT_COUNT" and _type_of(target) != NUMERIC:
        numeric = [_name_of(c) for c in columns if _type_of(c) == NUMERIC]
        raise _refuse(
            f"{agg} needs a NUMERIC column, and {_name_of(target)!r} is {_type_of(target)}. "
            f"Numeric columns: {_choices(numeric) or 'none'}."
        )
    card["aggregation"] = {
        "type": agg,
        "targetColId": target["internal_name"],
        "headerName": f"{agg} ({_name_of(target)})",
        "format": format_,
    }


def _edit_sort(card: dict[str, Any], edit: dict[str, Any]) -> None:
    if card.get("renderType") != LIST:
        raise _refuse(
            "Only a card in a list, donut or treemap view sorts; a chart view is ordered by value."
        )
    by = str(_require(edit, "by")).lower()
    if by not in SORT_KEYS:
        raise _refuse(f"{edit['by']!r} is not a sort key. Choices: {_choices(SORT_KEYS)}.")
    direction = str(_require(edit, "direction")).upper()
    if direction not in SORT_DIRECTIONS:
        raise _refuse(
            f"{edit['direction']!r} is not a direction. Choices: {_choices(SORT_DIRECTIONS)}."
        )
    card["sortBy"] = [[SORT_KEYS[by], direction]]


def _clear_card_filter(card: dict[str, Any], column_type: str) -> None:
    """``removeExploreCardFilters``: the card's own filter off, a chart back to its first level."""
    card.update({"condition": None, "activeValues": [], "exclude": False})
    if card.get("renderType") == CHART:
        card["charts"] = [_chart_template(0, column_type)]


def _edit_view(card: dict[str, Any], column: dict[str, Any], edit: dict[str, Any]) -> None:
    """``setCardView``: list and chart fetch different data, so crossing drops the filter."""
    view = str(_require(edit, "view")).lower()
    allowed = VIEWS_BY_TYPE.get(_type_of(column), ())
    if view not in allowed:
        raise _refuse(
            f"{edit['view']!r} is not a view of a {_type_of(column)} card. "
            f"Views: {_choices(allowed)}."
        )
    if card.get("view") == view:
        return
    render_type = VIEW_RENDER_TYPE[view]
    if render_type == card.get("renderType"):
        card["view"] = view
        return
    if card.get("condition"):
        _clear_card_filter(card, _type_of(column))
    granularity = card.get("granularity")
    card.update(
        {
            "activeValues": [],
            "renderType": render_type,
            "view": view,
            "granularity": granularity,
            "exclude": False,
            "sortBy": [["unformatted", "DESC"]],
        }
    )
    if render_type == CHART:
        level = granularity["id"] if isinstance(granularity, dict) else "AUTO"
        card["charts"] = [{"queryIndex": 0, "level": level, "activeValues": []}]


def _edit_level(card: dict[str, Any], column: dict[str, Any], edit: dict[str, Any]) -> None:
    if _type_of(column) not in (NUMERIC, DATE):
        raise _refuse(f"A TEXT card has no level; {_name_of(column)!r} is TEXT.")
    granularity = _granularity(_type_of(column), _require(edit, "level"))
    card["granularity"] = granularity
    if card.get("renderType") == CHART:
        first = (card.get("charts") or [{"queryIndex": 0, "activeValues": []}])[0]
        card["charts"] = [{**first, "level": granularity["id"]}]


# -- filter and exclude ---------------------------------------------------------------------------


def date_text(value: Any) -> str:
    """A date as the chart rows spell it, ``YYYY-MM-DD HH:MM:SS``."""
    text = str(value).strip().replace("T", " ")
    text = re.sub(r"(Z|[+-]\d\d:\d\d)+$", "", text)
    for pattern in (_DATE_TEXT, "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).strftime(_DATE_TEXT)
        except ValueError:
            continue
    raise _refuse(f"{value!r} is not a date. Write it as YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.")


def number_with_commas(value: float) -> str:
    """``Number.toLocaleString()``: grouped, at most three decimals."""
    text = f"{float(value):,.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _upper_bound(column_type: str, value: Any, level: Any) -> Any:
    if column_type == NUMERIC:
        step = 10.0**level
        total = float(value) + step
        if level < 0:
            return float(f"{round(total / step) * step:.{-level}f}")
        return round(total)
    start = datetime.strptime(value, _DATE_TEXT)
    if level == "YEAR":
        end = start.replace(year=start.year + 1)
    elif level == "MONTH":
        end = start.replace(year=start.year + start.month // 12, month=start.month % 12 + 1)
    else:
        end = start + timedelta(**{f"{level.lower()}s": 1})
    return end.strftime(_DATE_TEXT)


def _comparable(column_type: str, value: Any) -> float:
    if column_type == NUMERIC:
        return float(value)
    return datetime.strptime(value, _DATE_TEXT).timestamp()


def _chart_runs(values: list[Any], column_type: str, level: Any) -> list[dict[str, Any]]:
    """Each unbroken run of adjacent buckets as one ``[lower, upper)`` range (``getChartRuns``)."""
    runs: list[dict[str, Any]] = []
    for value in sorted(values, key=lambda v: _comparable(column_type, v)):
        upper = _upper_bound(column_type, value, level)
        last = runs[-1] if runs else None
        if last and _comparable(column_type, last["upper"]) >= _comparable(column_type, value):
            last["upper"] = upper
        else:
            runs.append(
                {"lower": float(value) if column_type == NUMERIC else value, "upper": upper}
            )
    return runs


def _range_clause(col: str, run: dict[str, Any]) -> dict[str, Any]:
    return {
        "AND": [{col: {"GTE": {"VALUE": run["lower"]}}}, {col: {"LT": {"VALUE": run["upper"]}}}]
    }


def _outside(col: str, run: dict[str, Any]) -> dict[str, Any]:
    return {"OR": [{col: {"LT": {"VALUE": run["lower"]}}}, {col: {"GTE": {"VALUE": run["upper"]}}}]}


def _exclude_blanks(
    col: str, condition: dict[str, Any] | None, blank_listed: bool
) -> dict[str, Any]:
    """SQL negation drops blanks, so they are put back unless the blank value itself is excluded."""
    if blank_listed:
        not_empty = {col: {"IS_NOT_EMPTY": True}}
        return {"AND": [condition, not_empty]} if condition else not_empty
    return {"OR": [condition, {col: {"IS_EMPTY": True}}]}


def _text_condition(col: str, values: list[Any], exclude: bool) -> dict[str, Any] | None:
    blank = BLANK in values
    present = [v for v in values if v is not BLANK]
    if exclude:
        clause = {col: {"NOT_IN_LIST": {"VALUE": present}}} if present else None
        return _exclude_blanks(col, clause, blank)
    parts: list[dict[str, Any]] = [{col: {"IS_EMPTY": True}}] if blank else []
    if present:
        parts.append({col: {"IN_LIST": {"VALUE": present}}})
    return {"OR": parts} if len(parts) > 1 else parts[0]


def _chart_condition(
    col: str, column_type: str, values: list[Any], level: Any, exclude: bool
) -> dict[str, Any] | None:
    blank = BLANK in values
    runs = _chart_runs([v for v in values if v is not BLANK], column_type, level)
    if exclude:
        clauses = [_outside(col, run) for run in runs]
        condition = ({"AND": clauses} if len(clauses) > 1 else clauses[0]) if clauses else None
        return _exclude_blanks(col, condition, blank)
    parts = [_range_clause(col, run) for run in runs]
    if blank:
        parts.append({col: {"IS_EMPTY": True}})
    return {"OR": parts} if len(parts) > 1 else parts[0]


def _label(column_type: str, value: Any, level: Any, depth: int) -> str:
    if value is BLANK:
        return "(blank)"
    if column_type == NUMERIC:
        upper = number_with_commas(_upper_bound(NUMERIC, value, level))
        return f"{number_with_commas(value)} to <{upper}"
    if column_type == DATE:
        option = _DATE_GRANULARITY[level]
        return date_format(
            datetime.strptime(value, _DATE_TEXT),
            option["listFormat" if depth == 0 else "graphFormat"],
        )
    if str(value).strip() == "":
        return "(spaces)"
    return str(value)


def date_format(moment: datetime, mask: str) -> str:
    """The ``dateformat`` package's masks the granularity options use."""
    hour12 = moment.hour % 12 or 12
    tokens = {
        "yyyy": f"{moment.year:04d}",
        "yy": f"{moment.year % 100:02d}",
        "mmm": moment.strftime("%b"),
        "dd": f"{moment.day:02d}",
        "d": str(moment.day),
        "hh": f"{hour12:02d}",
        "h": str(hour12),
        "MM": f"{moment.minute:02d}",
        "ss": f"{moment.second:02d}",
        "tt": "am" if moment.hour < 12 else "pm",
    }
    return re.sub("yyyy|yy|mmm|dd|d|hh|h|MM|ss|tt", lambda m: tokens[m.group(0)], mask)


def _selected_values(
    column: dict[str, Any], values: Any, level: Any, lookups: Lookups
) -> list[Any]:
    """The values to select, checked against the values the card lists."""
    if not isinstance(values, list) or not values:
        raise _refuse('"values" must be a non-empty list; null stands for the blank value.')
    column_type = _type_of(column)
    wanted: list[Any] = []
    for value in values:
        if value is BLANK:
            wanted.append(BLANK)
        elif column_type == NUMERIC:
            if isinstance(value, bool) or not isinstance(value, int | float | str):
                raise _refuse(f"{value!r} is not a number.")
            try:
                wanted.append(float(str(value).replace(",", "")))
            except ValueError:
                raise _refuse(f"{value!r} is not a number.") from None
        elif column_type == DATE:
            wanted.append(date_text(value))
        elif isinstance(value, str):
            wanted.append(value)
        else:
            raise _refuse(f"{value!r} is not text; this card lists TEXT values.")
    wanted = list(dict.fromkeys(wanted))
    listed = lookups.buckets(
        column, level, [v for v in wanted if v is not BLANK] if column_type == TEXT else None
    )
    missing = [v for v in wanted if v is not BLANK and v not in listed]
    if missing:
        if column_type == TEXT:
            listed = lookups.buckets(column, level, None)
        sample = _choices(repr(v) for v in listed[:10])
        raise _refuse(
            f"Not values of the {_name_of(column)!r} card: {_choices(repr(v) for v in missing)}. "
            f"It lists: {sample or 'nothing'}{', ...' if len(listed) > 10 else ''}."
        )
    return wanted


def _edit_filter(
    cards: list[dict[str, Any]],
    card: dict[str, Any],
    column: dict[str, Any],
    edit: dict[str, Any],
    lookups: Lookups,
) -> None:
    """``setExploreCardFilters``: select values to keep them or, with ``exclude``, drop them."""
    exclude = edit["op"] == "exclude"
    column_type = _type_of(column)
    col = str(column["internal_name"])
    is_chart = card.get("renderType") == CHART
    if column_type != TEXT and not is_chart:
        raise _refuse(
            f"{_name_of(column)!r} is in its list view, which lists values at a level this command "
            'cannot read. Filter it in its chart view: first {"op": "view", "view": "columns"}.'
        )
    if is_chart and edit.get("level") is not None:
        _edit_level(card, column, {"level": edit["level"]})
    charts = card.get("charts") or [_chart_template(0, column_type)]
    index = len(charts) - 1
    level = charts[index].get("level")
    if is_chart and (level is None or level == "AUTO"):
        raise _refuse(
            f"The {_name_of(column)!r} card has no fixed level yet (it is AUTO), "
            "so a bucket has no "
            'bounds to filter on. Give "level" in this edit, as the level menu lists it.'
        )
    values = _selected_values(column, edit.get("values"), level if is_chart else None, lookups)
    items = [{"value": v, "formatted": _label(column_type, v, level, index)} for v in values]
    condition = (
        _chart_condition(col, column_type, values, level, exclude)
        if is_chart
        else _text_condition(col, values, exclude)
    )
    if is_chart:
        card["charts"] = _filter_charts(card, charts, index, items, condition, exclude, column_type)
        parent = charts[index - 1].get("condition") if index else None
        if exclude and parent and condition:
            condition = {"AND": [parent, condition]}
    card.update({"condition": condition, "activeValues": items, "exclude": exclude})
    position = cards.index(card)
    for later in cards[position + 1 :]:
        _drop_downstream_filter(later)
    _sort_cards(cards)


def _filter_charts(
    card: dict[str, Any],
    charts: list[dict[str, Any]],
    index: int,
    items: list[dict[str, Any]],
    condition: dict[str, Any] | None,
    exclude: bool,
    column_type: str,
) -> list[dict[str, Any]]:
    """The charts after selecting on level ``index``: filtering to one bucket drills into it."""
    charts = [dict(chart) for chart in charts]
    charts[index].update({"condition": condition, "activeValues": items, "exclude": exclude})
    keep = index
    if not exclude and len(items) == 1 and items[0]["value"] is not BLANK:
        drilled = _chart_template(index + 1, column_type, charts[index]["level"])
        if drilled:
            charts.append(drilled)
            keep = index + 1
    return charts[: keep + 1]


def _drop_downstream_filter(card: dict[str, Any]) -> None:
    """A filter upstream voids the filters of the cards after it, as the web app does."""
    if _is_query(card):
        return
    card.update({"condition": None, "activeValues": [], "exclude": False})
    charts = card.get("charts")
    if charts:
        del charts[1:]
        charts[0].update({"condition": None, "activeValues": [], "exclude": False})


def _edit_clear(
    cards: list[dict[str, Any]], columns: list[dict[str, Any]], edit: dict[str, Any]
) -> None:
    if edit.get("card") is None:
        for card in cards:
            if _is_query(card):
                card.update(_cleared_query(card))
                continue
            card.update({"condition": None, "activeValues": [], "exclude": False})
            if card.get("renderType") == CHART:
                charts = card.get("charts") or [{"queryIndex": 0, "level": "AUTO"}]
                card["charts"] = [
                    {**charts[0], "condition": None, "activeValues": [], "exclude": False}
                ]
        return
    card, column = _card_for(cards, columns, edit["card"])
    if _is_query(card):
        card.update(_cleared_query(card))
    else:
        _clear_card_filter(card, _type_of(column))
        _sort_cards(cards)


def _cleared_query(card: dict[str, Any]) -> dict[str, Any]:
    if card["kind"] == "search":
        return {"query": "", "condition": None, "exclude": False}
    if card["kind"] == "scatter":
        return {"rect": None, "condition": None, "exclude": False}
    return {"condition": None, "exclude": False}


def _card_for(
    cards: list[dict[str, Any]], columns: list[dict[str, Any]], name: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    """A column card by its column's display name, or a query card by its id (``__search__``)."""
    query = _find(cards, name) if isinstance(name, str) else None
    if query is not None and _is_query(query):
        return query, {}
    return open_card(cards, columns, name)


# -- query cards ----------------------------------------------------------------------------------


def _new_id(cards: list[dict[str, Any]], prefix: str) -> str:
    taken = {card.get("colId") for card in cards}
    n = 1
    while f"{prefix}{n}" in taken:
        n += 1
    return f"{prefix}{n}"


def _query_card(
    cards: list[dict[str, Any]], edit: dict[str, Any], kind: str, fresh: dict[str, Any]
) -> dict[str, Any]:
    """The query card an edit names, or a new one at the front, as the web app opens them."""
    if edit.get("card") is not None:
        card = _find(cards, edit["card"])
        if card is None or card.get("kind") != kind:
            ids = [c["colId"] for c in cards if c.get("kind") == kind]
            raise _refuse(
                f"{edit['card']!r} is not a {kind} card. "
                f"{kind.title()} cards: {_choices(ids) or 'none'}."
            )
        return card
    if kind == "search":
        existing = next((c for c in cards if c.get("kind") == "search"), None)
        if existing:
            return existing
    cards.insert(0, fresh)
    return fresh


def _edit_search(
    cards: list[dict[str, Any]], columns: list[dict[str, Any]], edit: dict[str, Any]
) -> None:
    text = str(_require(edit, "text")).strip()
    if len(text) < MIN_SEARCH_CHARS:
        raise _refuse(f"A search needs at least {MIN_SEARCH_CHARS} characters.")
    fresh = {
        "colId": _SEARCH_ID,
        "kind": "search",
        "query": "",
        "columns": None,
        "condition": None,
        "exclude": False,
    }
    card = _query_card(cards, {**edit, "card": edit.get("card")}, "search", fresh)
    searched = columns
    if edit.get("columns") is not None:
        names = edit["columns"]
        if not isinstance(names, list) or not names:
            raise _refuse('"columns" must be a non-empty list of column display names.')
        picked = [_column_named(columns, name, "columns") for name in names]
        searched = picked
        card["columns"] = (
            [c["internal_name"] for c in picked] if len(picked) < len(columns) else None
        )
    elif card.get("columns"):
        searched = [c for c in columns if c["internal_name"] in card["columns"]]
    exclude = bool(edit.get("exclude", False))
    card.update(
        {"query": text, "exclude": exclude, "condition": search_condition(text, searched, exclude)}
    )


def _edit_scatter(
    cards: list[dict[str, Any]], columns: list[dict[str, Any]], edit: dict[str, Any]
) -> None:
    numeric = [c for c in columns if _type_of(c) == NUMERIC]
    creating = edit.get("card") is None
    if creating:
        _require(edit, "x")
        _require(edit, "y")
    fresh = {
        "colId": _new_id(cards, _SCATTER_PREFIX),
        "kind": "scatter",
        "x": None,
        "y": None,
        "colorBy": None,
        "sizeBy": "rows",
        "rect": None,
        "condition": None,
        "exclude": False,
        "width": 480,
    }
    card = _query_card(cards, edit, "scatter", fresh)
    for axis in ("x", "y"):
        if edit.get(axis) is None:
            continue
        column = _column_named(columns, edit[axis], axis)
        if _type_of(column) != NUMERIC:
            raise _refuse(
                f'A scatter plots numbers, and "{axis}" {_name_of(column)!r} '
                f"is {_type_of(column)}. "
                f"Numeric columns: {_choices(map(_name_of, numeric)) or 'none'}."
            )
        card.update(
            {axis: column["internal_name"], "rect": None, "condition": None, "exclude": False}
        )
    if edit.get("rect") is not None:
        rect = _rect(edit["rect"])
        exclude = bool(edit.get("exclude", False))
        card.update(
            {
                "rect": rect,
                "exclude": exclude,
                "condition": scatter_condition(rect, card["x"], card["y"], exclude),
            }
        )


def _rect(value: Any) -> dict[str, list[float]]:
    ok = isinstance(value, dict) and set(value) == {"x", "y"}
    pairs = [value[axis] for axis in ("x", "y")] if ok else []
    if not ok or not all(
        isinstance(p, list)
        and len(p) == 2
        and all(isinstance(n, int | float) and not isinstance(n, bool) for n in p)
        and p[0] <= p[1]
        for p in pairs
    ):
        raise _refuse('"rect" must be {"x": [low, high], "y": [low, high]} with low <= high.')
    return {axis: [float(n) for n in value[axis]] for axis in ("x", "y")}


def scatter_condition(
    rect: dict[str, list[float]], x: str, y: str, exclude: bool
) -> dict[str, Any]:
    """A box on the scatter: ``getScatterCondition``."""
    (x0, x1), (y0, y1) = rect["x"], rect["y"]
    if exclude:
        return {
            "OR": [
                {x: {"LT": {"VALUE": x0}}},
                {x: {"GT": {"VALUE": x1}}},
                {y: {"LT": {"VALUE": y0}}},
                {y: {"GT": {"VALUE": y1}}},
                {x: {"IS_EMPTY": True}},
                {y: {"IS_EMPTY": True}},
            ]
        }
    return {
        "AND": [
            {x: {"GTE": {"VALUE": x0}}},
            {x: {"LTE": {"VALUE": x1}}},
            {y: {"GTE": {"VALUE": y0}}},
            {y: {"LTE": {"VALUE": y1}}},
        ]
    }


_MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def _search_number(term: str) -> float | None:
    cleaned = re.sub(r"[$£€\s]", "", term)
    if re.fullmatch(r"-?\d+(\.\d+)?", cleaned):
        return float(cleaned)
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", cleaned):
        return float(cleaned.replace(",", ""))
    return None


def _search_date(term: str) -> dict[str, str] | None:
    """A term that reads as a day, month or year matches that bucket of a date column."""
    month = (
        "|".join(_MONTHS)
        + "|january|february|march|april|june|july|august|september|october|november|december"
    )
    patterns: list[tuple[str, str, Callable[[tuple[str, ...]], tuple[str, str, str]]]] = [
        (r"(\d{4})-(\d{2})-(\d{2})", "DAY", lambda g: (g[0], g[1], g[2])),
        (r"(\d{4})/(\d{2})/(\d{2})", "DAY", lambda g: (g[0], g[1], g[2])),
        (rf"(\d{{1,2}}) ({month}) (\d{{4}})", "DAY", lambda g: (g[2], g[1], g[0])),
        (rf"({month}) (\d{{1,2}}),? (\d{{4}})", "DAY", lambda g: (g[2], g[0], g[1])),
        (r"(\d{4})-(\d{2})", "MONTH", lambda g: (g[0], g[1], "1")),
        (rf"({month}) (\d{{4}})", "MONTH", lambda g: (g[1], g[0], "1")),
        (r"(\d{4})", "YEAR", lambda g: (g[0], "1", "1")),
    ]
    for pattern, unit, parts in patterns:
        found = re.fullmatch(pattern, term, re.IGNORECASE)
        if not found:
            continue
        year, mon, day = parts(found.groups())
        number = int(mon) if mon.isdigit() else _MONTHS.index(mon[:3].lower()) + 1
        try:
            return {
                "unit": unit,
                "value": datetime(int(year), number, int(day)).strftime(_DATE_TEXT),
            }
        except ValueError:
            continue
    return None


def search_condition(
    term: str, columns: list[dict[str, Any]], exclude: bool
) -> dict[str, Any] | None:
    """The search card's condition: a row matches when any searched column does."""
    query = term.strip()
    if not query:
        return None
    number = _search_number(query)
    date = _search_date(query)
    parts: list[dict[str, Any]] = []
    for column in columns:
        col = column["internal_name"]
        kind = _type_of(column)
        if kind == TEXT:
            parts.append({col: {"NOT_CONTAINS" if exclude else "CONTAINS": {"VALUE": [query]}}})
        elif kind == NUMERIC and number is not None:
            parts.append(
                {"OR": [{col: {"NOT_IN_LIST": {"VALUE": [number]}}}, {col: {"IS_EMPTY": True}}]}
                if exclude
                else {col: {"IN_LIST": {"VALUE": [number]}}}
            )
        elif kind == DATE and date:
            bucket = {"VALUE": {"TRUNCATE": date["unit"], "VALUE": date["value"]}}
            parts.append(
                {"OR": [{col: {"NE": bucket}}, {col: {"IS_EMPTY": True}}]}
                if exclude
                else {col: {"EQ": bucket}}
            )
    if not parts:
        if exclude or not columns:
            return None
        col = columns[0]["internal_name"]
        return {"AND": [{col: {"IS_EMPTY": True}}, {col: {"IS_NOT_EMPTY": True}}]}
    joined = parts[0] if len(parts) == 1 else {"AND" if exclude else "OR": parts}
    return {**joined, "STRING_PROP": {"CASE": "CASE-INSENSITIVE"}}


_FLIPPED = {"IS_EMPTY": "IS_NOT_EMPTY", "IS_NOT_EMPTY": "IS_EMPTY"}
_PROPERTIES = ("STRING_PROP", "FILTER_TYPE", "PROMPT")


def negate_condition(condition: dict[str, Any] | None) -> dict[str, Any] | None:
    """Every row the condition does not keep, blanks included (``negateCondition``)."""
    return _not_true(condition, True) if condition else None


def _not_true(node: dict[str, Any], is_not_true: bool) -> dict[str, Any]:
    properties = {k: v for k, v in node.items() if k in _PROPERTIES}
    parts: list[dict[str, Any]] = []
    for key, value in node.items():
        if key in _PROPERTIES:
            continue
        if key in ("AND", "OR"):
            group = ({"AND": "OR", "OR": "AND"}[key]) if is_not_true else key
            parts.append({group: [_not_true(child, is_not_true) for child in value]})
        elif key == "NOT":
            parts.append(_not_true(value, not is_not_true))
        else:
            operator = next(iter(value))
            if operator in _FLIPPED:
                parts.append(
                    {key: {_FLIPPED[operator]: value[operator]}} if is_not_true else {key: value}
                )
            else:
                clause = {key: value}
                parts.append(
                    {"OR": [{"NOT": clause} if is_not_true else clause, {key: {"IS_EMPTY": True}}]}
                )
    rewritten = parts[0] if len(parts) == 1 else {("OR" if is_not_true else "AND"): parts}
    return {**rewritten, **properties}


def normalize_ask_condition(condition: Any) -> dict[str, Any] | None:
    """The model's condition without its authoring keys (``normalizeAskCondition``)."""
    if not isinstance(condition, dict):
        return None
    rest = {k: v for k, v in condition.items() if k not in ("FILTER_TYPE", "PROMPT")}
    return rest if any(k not in _PROPERTIES for k in rest) else None


def _edit_ask(cards: list[dict[str, Any]], edit: dict[str, Any], lookups: Lookups) -> None:
    question = str(_require(edit, "question")).strip()
    if len(question) <= 2:
        raise _refuse('"question" must say what to keep, in more than two characters.')
    understood = lookups.ask(question)
    if not understood:
        raise _refuse(
            f"The question could not be read as a condition: {question!r}. Say it another way."
        )
    fresh = {
        "colId": _new_id(cards, _ASK_PREFIX),
        "kind": "ask",
        "prompt": "",
        "understood": None,
        "condition": None,
        "exclude": False,
    }
    card = _query_card(cards, edit, "ask", fresh)
    exclude = bool(edit.get("exclude", False))
    card.update(
        {
            "prompt": question,
            "understood": understood,
            "exclude": exclude,
            "condition": negate_condition(understood) if exclude else understood,
        }
    )


# -- entry point ----------------------------------------------------------------------------------


def _apply_one(
    cards: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    edit: dict[str, Any],
    lookups: Lookups,
) -> None:
    op = edit.get("op")
    if op not in _ALL_OPS:
        raise _refuse(f"{op!r} is not an edit. Choices: {_choices(_ALL_OPS)}.")
    _only_keys(edit, _COLUMN_OPS.get(op) or _QUERY_OPS.get(op) or set())
    if op == "search":
        _edit_search(cards, columns, edit)
    elif op == "scatter":
        _edit_scatter(cards, columns, edit)
    elif op == "ask":
        _edit_ask(cards, edit, lookups)
    elif op == "clear":
        _edit_clear(cards, columns, edit)
    elif op == "remove":
        card, _ = _card_for(cards, columns, _require(edit, "card"))
        cards.remove(card)
    else:
        card, column = open_card(cards, columns, _require(edit, "card"))
        if op == "metric":
            _edit_metric(card, column, edit, columns)
        elif op == "sort":
            _edit_sort(card, edit)
        elif op == "view":
            _edit_view(card, column, edit)
            _sort_cards(cards)
        elif op == "level":
            _edit_level(card, column, edit)
        else:
            _edit_filter(cards, card, column, edit, lookups)


def apply_edits(
    cards: list[dict[str, Any]], edits: Any, columns: list[dict[str, Any]], lookups: Lookups
) -> list[dict[str, Any]]:
    """The panel's cards after ``edits`` run in order; ``cards`` itself is left as it was."""
    if not isinstance(edits, list) or not edits or not all(isinstance(e, dict) for e in edits):
        raise _refuse('"edits" must be a non-empty list of edit objects.')
    if not columns:
        raise _refuse("The view's columns could not be read, so no card was changed.")
    result = copy.deepcopy(cards)
    for edit in edits:
        _apply_one(result, columns, edit, lookups)
    return result


def guess_number_level(values: list[float]) -> int | None:
    """The bucket width exponent the list of bucket starts implies."""
    if len(values) < 2:
        return None
    levels: Counter[int] = Counter()
    for first, second in zip(values, values[1:], strict=False):
        diff = round(abs(second - first), 4)
        if diff == 0:
            levels[0] += 1
            continue
        level = math.floor(math.log10(diff))
        while level >= 0 and float(first / 10**level) != int(first / 10**level):
            level -= 1
        levels[level] += 1
        if sum(levels.values()) >= 10:
            break
    return levels.most_common(1)[0][0]
