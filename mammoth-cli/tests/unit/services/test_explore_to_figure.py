"""A card as a dashboard tile: the mapping and the refusals of the web app's explore-to-figure."""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.explore_cards import card_for_column
from mammoth_cli.services.explore_to_figure import card_to_figure

COLUMNS = [
    {"display_name": "Amount", "internal_name": "column_0", "type": "NUMERIC"},
    {"display_name": "Day", "internal_name": "column_1", "type": "DATE"},
    {"display_name": "Region", "internal_name": "column_2", "type": "TEXT"},
]


def _tile(index: int, **card_changes: object) -> dict[str, object]:
    column = COLUMNS[index]
    card = {**card_for_column(column["internal_name"], column["type"]), **card_changes}
    return card_to_figure(card, column, COLUMNS, buckets=[0.0, 100.0, 200.0], value_count=25)


def test_a_text_list_becomes_a_top_ten_bar_titled_by_the_column() -> None:
    tile = _tile(2)
    assert tile["figure"] == {
        "kind": "hbar",
        "agg": "count",
        "dim": "Region",
        "top_n": 10,
        "sort": "desc",
        "title": "Count by Region",
    }
    assert [n["code"] for n in tile["notes"]] == ["top_n"]


def test_donut_and_treemap_keep_their_own_top_n() -> None:
    assert _tile(2, view="donut")["figure"]["top_n"] == 7
    assert _tile(2, view="treemap")["figure"]["top_n"] == 24


def test_a_date_card_becomes_a_bar_by_month_and_a_timeline_a_line() -> None:
    bar = _tile(1)["figure"]
    assert bar["kind"] == "bar"
    assert bar["date_bucket"] == {"field": "Day", "unit": "month"}
    assert bar["title"] == "Count by Day (month)"
    assert _tile(1, view="timeline")["figure"]["kind"] == "line"


def test_a_sum_card_is_titled_with_its_measure() -> None:
    aggregation = {"type": "SUM", "targetColId": "column_0", "format": {}}
    figure = _tile(2, aggregation=aggregation)["figure"]
    assert figure["measure"] == "Amount"
    assert figure["title"] == "Sum of Amount by Region"


def test_a_number_card_becomes_a_bar_over_fixed_ranges() -> None:
    tile = _tile(0, granularity={"id": 2})
    assert tile["figure"]["kind"] == "bar"
    assert [b["label"] for b in tile["banded"]["bands"]] == ["0–100", "100–200", "200–300"]


def test_a_filter_card_is_refused_with_the_web_apps_reason() -> None:
    column = COLUMNS[2]
    with pytest.raises(CliError) as refused:
        card_to_figure({"kind": "search", "colId": "__search__"}, column, COLUMNS)
    assert refused.value.message == "This card filters rows and has no chart to add."


def test_a_card_whose_value_column_is_gone_is_refused() -> None:
    aggregation = {"type": "SUM", "targetColId": "column_9", "format": {}}
    with pytest.raises(CliError) as refused:
        _tile(2, aggregation=aggregation)
    assert refused.value.message == "This card's value column is no longer in the view."
