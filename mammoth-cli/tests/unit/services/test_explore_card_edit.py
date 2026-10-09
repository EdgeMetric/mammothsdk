"""Explore card edits: the card config written is the one the web app saves and reads.

The edits are pure functions of the saved cards, the view's columns and the values the cards
list, so these run them with a small in-test view and assert the cards that come out.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.explore_card_edit import Lookups, apply_edits
from mammoth_cli.services.explore_cards import card_for_column

COLUMNS = [
    {"display_name": "Amount", "internal_name": "column_0", "type": "NUMERIC"},
    {"display_name": "Day", "internal_name": "column_1", "type": "DATE"},
    {"display_name": "Region", "internal_name": "column_2", "type": "TEXT"},
]
REGIONS = ["East", "West", "North"]


def _buckets(column: dict[str, Any], level: Any, only: list[Any] | None) -> list[Any]:
    if column["type"] == "TEXT":
        return [r for r in REGIONS if not only or r in only]
    if column["type"] == "NUMERIC":
        return [0.0, 100.0, 200.0]
    return ["2026-10-02 00:00:00", "2026-10-03 00:00:00"]


def _ask(question: str) -> dict[str, Any] | None:
    if question == "east only":
        return {
            "STRING_PROP": {"CASE": "CASE-INSENSITIVE"},
            "column_2": {"IN_LIST": {"VALUE": ["East"]}},
        }
    return None


LOOKUPS = Lookups(buckets=_buckets, ask=_ask)


def _cards() -> list[dict[str, Any]]:
    return [card_for_column(c["internal_name"], c["type"]) for c in COLUMNS]


def _edit(
    *edits: dict[str, Any], cards: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    return apply_edits(cards or _cards(), list(edits), COLUMNS, LOOKUPS)


def _card(cards: list[dict[str, Any]], col_id: str) -> dict[str, Any]:
    return next(c for c in cards if c["colId"] == col_id)


def test_metric_sums_another_column_and_refuses_a_non_numeric_one() -> None:
    cards = _edit({"op": "metric", "card": "Region", "agg": "SUM", "of": "Amount"})
    assert _card(cards, "column_2")["aggregation"]["type"] == "SUM"
    assert _card(cards, "column_2")["aggregation"]["targetColId"] == "column_0"
    with pytest.raises(CliError) as refused:
        _edit({"op": "metric", "card": "Region", "agg": "SUM", "of": "Day"})
    assert "Numeric columns: Amount" in refused.value.message


def test_sort_writes_the_sort_pair_and_names_the_choices() -> None:
    cards = _edit({"op": "sort", "card": "Region", "by": "value", "direction": "ASC"})
    assert _card(cards, "column_2")["sortBy"] == [["value", "ASC"]]
    with pytest.raises(CliError) as refused:
        _edit({"op": "sort", "card": "Region", "by": "size", "direction": "ASC"})
    assert "metric, value" in refused.value.message


def test_view_switch_follows_the_column_type() -> None:
    cards = _edit({"op": "view", "card": "Region", "view": "donut"})
    assert _card(cards, "column_2")["view"] == "donut"
    with pytest.raises(CliError) as refused:
        _edit({"op": "view", "card": "Day", "view": "donut"})
    assert "columns, timeline, list" in refused.value.message


def test_level_takes_a_date_level_or_a_number_width() -> None:
    cards = _edit(
        {"op": "level", "card": "Day", "level": "month"},
        {"op": "level", "card": "Amount", "level": 1000},
    )
    assert _card(cards, "column_1")["granularity"]["id"] == "MONTH"
    assert _card(cards, "column_0")["granularity"] == {"id": 3, "name": "1,000"}
    with pytest.raises(CliError):
        _edit({"op": "level", "card": "Amount", "level": 7})


def test_filter_and_exclude_write_the_conditions_and_clear_removes_them() -> None:
    kept = _edit({"op": "filter", "card": "Region", "values": ["East"]})
    assert kept[0]["colId"] == "column_2"
    assert kept[0]["condition"] == {"column_2": {"IN_LIST": {"VALUE": ["East"]}}}
    dropped = _edit({"op": "exclude", "card": "Region", "values": ["East"]})
    assert dropped[0]["condition"] == {
        "OR": [
            {"column_2": {"NOT_IN_LIST": {"VALUE": ["East"]}}},
            {"column_2": {"IS_EMPTY": True}},
        ]
    }
    cleared = _edit({"op": "clear", "card": "Region"}, cards=kept)
    assert _card(cleared, "column_2")["condition"] is None


def test_remove_takes_the_card_away() -> None:
    cards = _edit({"op": "remove", "card": "Region"})
    assert [c["colId"] for c in cards] == ["column_0", "column_1"]


def test_unknown_columns_and_values_are_refused_with_the_valid_choices() -> None:
    with pytest.raises(CliError) as no_column:
        _edit({"op": "remove", "card": "Nope"})
    assert "Columns: Amount, Day, Region" in no_column.value.message
    with pytest.raises(CliError) as no_value:
        _edit({"op": "filter", "card": "Region", "values": ["South"]})
    assert "'East', 'West', 'North'" in no_value.value.message


def test_query_cards_get_the_web_apps_shapes() -> None:
    cards = _edit(
        {"op": "search", "text": "eas", "columns": ["Region"]},
        {"op": "scatter", "x": "Amount", "y": "Amount", "rect": {"x": [0, 1], "y": [0, 1]}},
        {"op": "ask", "question": "east only"},
    )
    by_id = {c["colId"]: c for c in cards}
    assert by_id["__search__"]["kind"] == "search"
    assert by_id["__search__"]["condition"]["column_2"] == {"CONTAINS": {"VALUE": ["eas"]}}
    assert by_id["__scatter_1"]["kind"] == "scatter"
    assert by_id["__scatter_1"]["condition"]["AND"][0] == {"column_0": {"GTE": {"VALUE": 0.0}}}
    assert by_id["__ask_1"]["condition"]["column_2"] == {"IN_LIST": {"VALUE": ["East"]}}


def test_scatter_refuses_a_text_axis_and_ask_refuses_an_unread_question() -> None:
    with pytest.raises(CliError) as text_axis:
        _edit({"op": "scatter", "x": "Amount", "y": "Region"})
    assert "Numeric columns: Amount" in text_axis.value.message
    with pytest.raises(CliError):
        _edit({"op": "ask", "question": "gibberish"})


def test_the_saved_cards_are_not_changed_in_place() -> None:
    cards = _cards()
    _edit({"op": "remove", "card": "Region"}, cards=cards)
    assert len(cards) == 3
