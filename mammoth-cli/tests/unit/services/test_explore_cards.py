"""The Explore panel the CLI writes is the one the web app reads: ``{height, cards}``.

Pure functions on real column metadata, as ``view get`` returns it; nothing stands in for anything.
The metadata is the shape of the QA view (one numeric id, one text, one date column).
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.explore_cards import card_for_column, resolve_panel

METADATA: list[dict[str, Any]] = [
    {"display_name": "customer_id", "internal_name": "column_1", "type": "NUMERIC"},
    {"display_name": "Region", "internal_name": "column_2", "type": "TEXT"},
    {"display_name": "Order Date", "internal_name": "column_3", "type": "DATE"},
]


def test_columns_all_makes_one_card_per_column_in_the_views_order() -> None:
    panel = resolve_panel({"columns": "all"}, METADATA, {})
    assert [card["colId"] for card in panel["cards"]] == ["column_1", "column_2", "column_3"]


def test_a_text_column_gets_a_list_card_and_the_others_range_buckets() -> None:
    assert card_for_column("column_2", "TEXT")["renderType"] == "list"
    numeric = card_for_column("column_1", "NUMERIC")
    assert numeric["renderType"] == "chart"
    assert numeric["charts"] == [{"queryIndex": 0, "activeValues": [], "level": "AUTO"}]


def test_named_columns_keep_the_saved_cards_and_height_and_skip_a_column_that_has_one() -> None:
    saved = {"height": 372, "cards": [card_for_column("column_2", "TEXT")]}
    panel = resolve_panel({"columns": ["Region", "Order Date"]}, METADATA, saved)
    assert panel["height"] == 372
    assert [card["colId"] for card in panel["cards"]] == ["column_2", "column_3"]


def test_a_panel_with_cards_is_written_as_given() -> None:
    given = {"height": 200, "cards": [card_for_column("column_1", "NUMERIC")]}
    assert resolve_panel(given, METADATA, {}) == given


def test_the_old_open_items_panel_is_refused_because_the_web_app_would_show_no_cards() -> None:
    with pytest.raises(CliError) as refused:
        resolve_panel({"open": True, "items": [{"column": "column_1"}]}, METADATA, {})
    assert "No cards yet" in refused.value.message


def test_an_unknown_column_name_is_refused_by_name() -> None:
    with pytest.raises(CliError) as refused:
        resolve_panel({"columns": ["Regoin"]}, METADATA, {})
    assert "Regoin" in refused.value.message


def test_columns_with_no_readable_metadata_is_refused_not_written_empty() -> None:
    with pytest.raises(CliError):
        resolve_panel({"columns": "all"}, [], {})
