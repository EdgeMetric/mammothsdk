"""An Explore card as the engine figure spec the SVG route renders.

The web app's Explore card is a chart or a list of grouped rows. A chart card becomes a bar spec
(one bar per group, its value the card's metric); a list card becomes a table spec (one row per
group). The title and the value's name come from the card's own description (``figure_title`` in
:mod:`mammoth_cli.services.explore_to_figure`). Pure: the grouped rows arrive as an argument, read
the way ``view data explore`` reads them (``group_0`` the group, ``agg_0`` the count, ``agg_1`` the
metric).
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.explore_card_edit import CHART, DATE, date_text
from mammoth_cli.services.explore_to_figure import (
    _AGG_LABEL,
    BLANK_LABEL,
    _value_of,
    figure_title,
)

BAR_WIDTH = 620
BAR_HEIGHT = 360


def _label(group: Any, column_type: str) -> str:
    """The group as an axis label; a date bucket reads as its day, or day and time."""
    if group is None:
        return BLANK_LABEL
    if column_type != DATE:
        return str(group)
    return date_text(group).removesuffix(" 00:00:00").removesuffix(":00")


def card_to_render_spec(
    card: dict[str, Any],
    column: dict[str, Any],
    columns: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """The bar or table spec for ``card``, drawn from its grouped ``rows``."""
    agg, _, measure_label = _value_of(card, columns)
    by = str(column["display_name"])
    title = figure_title(agg, measure_label, by)
    value_key = "agg_0" if agg == "count" else "agg_1"
    column_type = str(column.get("type") or "").upper()
    points = [(_label(row.get("group_0"), column_type), row.get(value_key)) for row in rows]
    if card.get("renderType") == CHART:
        return {
            "chart": "bar",
            "title": title,
            "width": BAR_WIDTH,
            "height": BAR_HEIGHT,
            "data": [{"label": label, "value": value} for label, value in points],
        }
    value_label = "Count" if agg == "count" else f"{_AGG_LABEL[agg]} of {measure_label}"
    return {
        "chart": "table",
        "title": title,
        "columns": [{"label": by}, {"label": value_label, "num": True}],
        "rows": [{"cells": [label, value]} for label, value in points],
    }
