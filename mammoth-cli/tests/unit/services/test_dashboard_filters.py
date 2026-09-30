"""A board filter control is a canvas ``filters[]`` entry; these are its edits."""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.dashboard_filters import (
    check_filter,
    declared,
    with_filter,
    without_filter,
)


def test_adding_a_filter_declares_it_on_the_canvas_without_touching_the_rest() -> None:
    canvas = {"filters": [{"field": "Month", "control": "range"}], "pages": [{"id": "p1"}]}

    edited = with_filter(canvas, {"field": "Region", "control": "dropdown"})

    assert [f["field"] for f in edited["filters"]] == ["Month", "Region"]
    assert edited["pages"] == [{"id": "p1"}]
    assert canvas["filters"] == [{"field": "Month", "control": "range"}]  # input untouched


def test_adding_the_same_field_again_replaces_it_instead_of_duplicating() -> None:
    canvas = {"filters": [{"field": "Region", "control": "multi"}]}

    edited = with_filter(canvas, {"field": "Region", "control": "chips", "label": "Area"})

    assert edited["filters"] == [{"field": "Region", "control": "chips", "label": "Area"}]


def test_a_filter_is_appended_to_an_explicit_filter_order_only_when_one_exists() -> None:
    ordered = with_filter({"filters": [], "filter_order": ["Month"]}, {"field": "Region"})
    unordered = with_filter({"filters": []}, {"field": "Region"})

    assert ordered["filter_order"] == ["Month", "Region"]
    assert "filter_order" not in unordered


def test_a_canvas_without_filters_gets_the_list_created() -> None:
    assert with_filter({}, {"field": "Region"})["filters"] == [{"field": "Region"}]


def test_removing_a_filter_drops_it_from_filters_and_filter_order() -> None:
    canvas = {
        "filters": [{"field": "Month"}, {"field": "Region"}],
        "filter_order": ["Month", "Region"],
    }

    edited = without_filter(canvas, "Region")

    assert edited["filters"] == [{"field": "Month"}]
    assert edited["filter_order"] == ["Month"]


def test_removing_a_filter_that_is_not_declared_fails_and_names_what_is() -> None:
    with pytest.raises(CliError) as caught:
        without_filter({"filters": [{"field": "Month"}]}, "Region")

    assert "Region" in caught.value.message and "Month" in caught.value.message


def test_declared_lists_the_filters_and_tolerates_a_canvas_with_none() -> None:
    assert declared({"filters": [{"field": "Month"}]}) == [{"field": "Month"}]
    assert declared({}) == []


_DOC = {
    "plan": {
        "hints": {
            "_profiles": [
                {"name": "Region", "type": "dimension"},
                {"name": "Revenue", "type": "measure"},
                {"name": "Order Date", "type": "date"},
            ]
        }
    }
}


def test_a_filter_on_a_column_the_board_does_not_have_names_the_columns_it_does() -> None:
    with pytest.raises(CliError) as caught:
        check_filter(_DOC, {"field": "Regoin"})

    assert "Regoin" in caught.value.message
    assert "Region" in caught.value.message and "Order Date" in caught.value.message


def test_a_control_the_column_type_cannot_take_is_refused_with_the_ones_it_can() -> None:
    with pytest.raises(CliError) as caught:
        check_filter(_DOC, {"field": "Region", "control": "range"})

    assert "dropdown" in caught.value.message


@pytest.mark.parametrize(
    "entry",
    [
        {"field": "Region"},
        {"field": "Region", "control": "chips"},
        {"field": "Order Date", "control": "range"},
        {"field": "Revenue", "control": "range"},
    ],
)
def test_a_filter_the_column_type_takes_passes(entry: dict[str, str]) -> None:
    check_filter(_DOC, entry)


def test_a_canvas_read_without_a_column_profile_is_not_second_guessed() -> None:
    check_filter({"canvas": {}}, {"field": "Anything", "control": "range"})
