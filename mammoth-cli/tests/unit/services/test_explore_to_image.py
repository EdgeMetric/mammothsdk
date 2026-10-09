"""An Explore card as the engine spec the SVG route renders: a chart is a bar, a list a table."""

from __future__ import annotations

from mammoth_cli.services.explore_cards import card_for_column
from mammoth_cli.services.explore_to_image import card_to_render_spec

COLUMNS = [
    {"display_name": "Region", "internal_name": "column_0", "type": "TEXT"},
    {"display_name": "Amount", "internal_name": "column_1", "type": "NUMERIC"},
]
REGION = COLUMNS[0]
ROWS = [{"group_0": "East", "agg_0": 12}, {"group_0": None, "agg_0": 3}]


def _card(**changes: object) -> dict[str, object]:
    return {**card_for_column(REGION["internal_name"], REGION["type"]), **changes}


def test_a_chart_card_becomes_a_bar_spec_of_its_counts() -> None:
    card = _card(renderType="chart", view="columns")
    spec = card_to_render_spec(card, REGION, COLUMNS, ROWS)
    assert spec == {
        "chart": "bar",
        "title": "Count by Region",
        "width": 620,
        "height": 360,
        "data": [{"label": "East", "value": 12}, {"label": "(blank)", "value": 3}],
    }


def test_a_list_card_becomes_a_table_of_its_rows_with_the_metric_as_a_number() -> None:
    card = _card(
        aggregation={"type": "SUM", "targetColId": "column_1", "format": {"separator": True}}
    )
    rows = [{"group_0": "East", "agg_0": 12, "agg_1": 4150.5}]
    spec = card_to_render_spec(card, REGION, COLUMNS, rows)
    assert spec == {
        "chart": "table",
        "title": "Sum of Amount by Region",
        "columns": [{"label": "Region"}, {"label": "Sum of Amount", "num": True}],
        "rows": [{"cells": ["East", 4150.5]}],
    }
