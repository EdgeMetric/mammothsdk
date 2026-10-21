"""Explore card edits, one op at a time, against the web app's own behaviour.

Expected values come from the web app (mm-frontend ``explore-section``): the conditions of
``getConditionFromSelectedValues`` / ``getExcludeConditionFromSelectedValues`` / ``getChartRuns``
(``explore-section.utils.js``), the query-card conditions and the SQL three-valued-logic
check of ``negateCondition`` (``query-cards.utils.js`` and its unit tests), the store actions
``setCardView`` / ``removeExploreCardFilters`` / ``setExploreCardFilters``
(``exploreSection.storePinia.js``) and ``DATE_GRANULARITY_OPTIONS``
(``constants/exploreSection.js``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import explore_card_edit as ece
from mammoth_cli.services.explore_card_edit import Lookups, apply_edits
from mammoth_cli.services.explore_cards import card_for_column

COLUMNS = [
    {"display_name": "Channel", "internal_name": "channel", "type": "TEXT"},
    {"display_name": "Quantity", "internal_name": "quantity", "type": "NUMERIC"},
    {"display_name": "Order date", "internal_name": "order_date", "type": "DATE"},
    {"display_name": "Price", "internal_name": "price", "type": "NUMERIC"},
]
INSENSITIVE = {"CASE": "CASE-INSENSITIVE"}
IS_EMPTY = {"IS_EMPTY": True}


class View:
    """A view's bucket lists and ask answers, for the lookups an edit needs."""

    def __init__(self, **buckets: list[Any]) -> None:
        self.buckets = buckets
        self.asked: list[str] = []
        self.answer: dict[str, Any] | None = None

    def lookups(self) -> Lookups:
        def buckets(column: dict[str, Any], level: Any, only: list[Any] | None) -> list[Any]:
            values = self.buckets[column["internal_name"]]
            return [v for v in values if not only or v in only]

        def ask(question: str) -> dict[str, Any] | None:
            self.asked.append(question)
            return self.answer

        return Lookups(buckets=buckets, ask=ask)


VIEW = View(
    channel=["Amazon", "eBay", "Shop", " "],
    quantity=[10.0, 20.0, 30.0, 40.0, 50.0],
    order_date=[
        "2026-01-01 00:00:00",
        "2026-02-01 00:00:00",
        "2026-12-01 00:00:00",
    ],
    price=[0.0, 100.0],
)


def cards_for(*names: str) -> list[dict[str, Any]]:
    by_name = {c["display_name"]: c for c in COLUMNS}
    return [card_for_column(by_name[n]["internal_name"], by_name[n]["type"]) for n in names]


def run(
    cards: list[dict[str, Any]], *edits: dict[str, Any], view: View = VIEW
) -> list[dict[str, Any]]:
    return apply_edits(cards, list(edits), COLUMNS, view.lookups())


def card(cards: list[dict[str, Any]], col_id: str) -> dict[str, Any]:
    return next(c for c in cards if c["colId"] == col_id)


def refused(cards: list[dict[str, Any]], *edits: dict[str, Any], view: View = VIEW) -> CliError:
    with pytest.raises(CliError) as excinfo:
        run(cards, *edits, view=view)
    assert excinfo.value.code == "invalid_argument"
    assert excinfo.value.exit_status == 2
    return excinfo.value


# ── apply_edits: the envelope around every edit ──


@pytest.mark.parametrize("edits", [None, [], "metric", [1], [{"op": "clear"}, "x"]])
def test_edits_must_be_a_non_empty_list_of_objects(edits: Any) -> None:
    with pytest.raises(CliError) as excinfo:
        apply_edits(cards_for("Channel"), edits, COLUMNS, VIEW.lookups())
    assert excinfo.value.message == '"edits" must be a non-empty list of edit objects.'


def test_no_columns_means_no_card_is_changed() -> None:
    with pytest.raises(CliError) as excinfo:
        apply_edits(cards_for("Channel"), [{"op": "clear"}], [], VIEW.lookups())
    assert excinfo.value.message == "The view's columns could not be read, so no card was changed."


def test_an_unknown_op_lists_the_ops() -> None:
    error = refused(cards_for("Channel"), {"op": "zoom"})
    assert error.message == (
        "'zoom' is not an edit. Choices: metric, sort, view, level, filter, exclude, clear, "
        "remove, search, scatter, ask."
    )


def test_a_key_the_op_does_not_take_is_named_with_what_it_does_take() -> None:
    error = refused(
        cards_for("Channel"), {"op": "metric", "card": "Channel", "agg": "COUNT", "by": "x"}
    )
    assert error.message == ('The "metric" edit does not take by. It takes: agg, card, of, op.')


def test_a_missing_required_key_is_named() -> None:
    assert refused(cards_for("Channel"), {"op": "metric", "card": "Channel"}).message == (
        'The "metric" edit needs "agg".'
    )
    assert refused(cards_for("Channel"), {"op": "remove"}).message == (
        'The "remove" edit needs "card".'
    )


def test_edits_run_in_order_and_the_input_cards_are_never_changed() -> None:
    original = cards_for("Channel", "Quantity")
    before = repr(original)
    out = run(
        original,
        {"op": "sort", "card": "Channel", "by": "value", "direction": "asc"},
        {"op": "metric", "card": "Channel", "agg": "sum", "of": "Quantity"},
    )
    assert repr(original) == before
    assert card(out, "channel")["sortBy"] == [["value", "ASC"]]
    assert card(out, "channel")["aggregation"]["type"] == "SUM"


def test_a_card_that_is_not_open_names_the_open_ones_and_how_to_open_it() -> None:
    error = refused(cards_for("Channel"), {"op": "level", "card": "Quantity", "level": 1})
    assert error.message == "No card is open for 'Quantity'. Open cards: Channel."
    assert error.hint is not None and "view explore-panel set VIEW_ID" in error.hint
    none_open = refused([], {"op": "remove", "card": "Quantity"})
    assert none_open.message == "No card is open for 'Quantity'. Open cards: none."


def test_a_card_name_must_be_a_string_naming_a_column() -> None:
    assert refused(cards_for("Channel"), {"op": "remove", "card": 5}).message == (
        '"card" must be a column display name.'
    )
    error = refused(cards_for("Channel"), {"op": "remove", "card": "Nope"})
    assert error.message == (
        "'Nope' is not a column of this view. Columns: Channel, Quantity, Order date, Price."
    )


# ── metric ──


def test_count_resets_the_aggregation_and_keeps_its_number_format() -> None:
    cards = cards_for("Channel")
    cards[0]["aggregation"] = {
        "type": "SUM",
        "targetColId": "quantity",
        "format": {"separator": False},
    }
    out = run(cards, {"op": "metric", "card": "Channel", "agg": "count"})
    assert card(out, "channel")["aggregation"] == {
        "type": "COUNT",
        "targetColId": None,
        "headerName": "Count",
        "format": {"separator": False},
    }


def test_count_takes_no_of_column() -> None:
    error = refused(
        cards_for("Channel"), {"op": "metric", "card": "Channel", "agg": "COUNT", "of": "Quantity"}
    )
    assert error.message == 'COUNT counts rows and takes no "of" column.'


def test_a_measure_other_than_count_needs_a_column_to_measure() -> None:
    error = refused(cards_for("Channel"), {"op": "metric", "card": "Channel", "agg": "SUM"})
    assert error.message == 'The "metric" edit needs "of".'


def test_an_unknown_aggregation_lists_the_choices() -> None:
    error = refused(cards_for("Channel"), {"op": "metric", "card": "Channel", "agg": "MEDIAN"})
    assert error.message == (
        "'MEDIAN' is not an aggregation. "
        "Choices: COUNT, DISTINCT_COUNT, SUM, AVG, MIN, MAX, STDDEV."
    )


def test_distinct_count_may_measure_a_text_column_but_a_sum_may_not() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "metric", "card": "Quantity", "agg": "distinct_count", "of": "Channel"},
    )
    assert card(out, "quantity")["aggregation"] == {
        "type": "DISTINCT_COUNT",
        "targetColId": "channel",
        "headerName": "DISTINCT_COUNT (Channel)",
        "format": {"separator": True},
    }
    error = refused(
        cards_for("Quantity"), {"op": "metric", "card": "Quantity", "agg": "AVG", "of": "Channel"}
    )
    assert error.message == (
        "AVG needs a NUMERIC column, and 'Channel' is TEXT. Numeric columns: Quantity, Price."
    )


# ── sort ──


def test_sort_by_metric_writes_the_unformatted_key() -> None:
    out = run(
        cards_for("Channel"), {"op": "sort", "card": "Channel", "by": "Metric", "direction": "desc"}
    )
    assert card(out, "channel")["sortBy"] == [["unformatted", "DESC"]]


def test_a_chart_card_cannot_be_sorted() -> None:
    error = refused(
        cards_for("Quantity"), {"op": "sort", "card": "Quantity", "by": "value", "direction": "ASC"}
    )
    assert error.message == (
        "Only a card in a list, donut or treemap view sorts; a chart view is ordered by value."
    )


def test_sort_needs_a_known_key_and_direction() -> None:
    base = {"op": "sort", "card": "Channel"}
    assert refused(cards_for("Channel"), {**base, "by": "size", "direction": "ASC"}).message == (
        "'size' is not a sort key. Choices: metric, value."
    )
    assert refused(cards_for("Channel"), {**base, "by": "value", "direction": "up"}).message == (
        "'up' is not a direction. Choices: ASC, DESC."
    )
    assert refused(cards_for("Channel"), {**base, "by": "value"}).message == (
        'The "sort" edit needs "direction".'
    )


# ── view (setCardView) ──


def test_a_view_of_the_same_render_type_only_changes_the_view_and_keeps_the_filter() -> None:
    cards = cards_for("Channel")
    cards[0]["condition"] = {"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}}
    out = run(cards, {"op": "view", "card": "Channel", "view": "Donut"})
    assert card(out, "channel")["view"] == "donut"
    assert card(out, "channel")["renderType"] == "list"
    assert card(out, "channel")["condition"] == {"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}}


def test_choosing_the_current_view_changes_nothing() -> None:
    cards = cards_for("Channel")
    assert run(cards, {"op": "view", "card": "Channel", "view": "list"}) == cards


def test_a_view_the_column_type_does_not_offer_is_refused() -> None:
    error = refused(cards_for("Channel"), {"op": "view", "card": "Channel", "view": "columns"})
    assert error.message == "'columns' is not a view of a TEXT card. Views: list, donut, treemap."
    error = refused(cards_for("Quantity"), {"op": "view", "card": "Quantity", "view": "timeline"})
    assert "Views: columns, list" in error.message


def test_crossing_from_chart_to_list_drops_the_filter_and_resets_sort_and_charts() -> None:
    cards = cards_for("Quantity", "Channel")
    cards[0]["granularity"] = {"id": 1, "name": "10"}
    cards[0]["condition"] = {"quantity": {"GTE": {"VALUE": 10}}}
    cards[0]["activeValues"] = [{"value": 10.0, "formatted": "10 to <20"}]
    out = run(cards, {"op": "view", "card": "Quantity", "view": "list"})
    quantity = card(out, "quantity")
    assert (quantity["renderType"], quantity["view"]) == ("list", "list")
    assert quantity["condition"] is None
    assert quantity["activeValues"] == []
    assert quantity["exclude"] is False
    assert quantity["sortBy"] == [["unformatted", "DESC"]]
    assert quantity["granularity"] == {"id": 1, "name": "10"}


def test_crossing_from_list_to_chart_starts_one_chart_at_the_cards_level() -> None:
    cards = cards_for("Quantity")
    out = run(
        cards,
        {"op": "view", "card": "Quantity", "view": "list"},
        {"op": "level", "card": "Quantity", "level": 100},
        {"op": "view", "card": "Quantity", "view": "columns"},
    )
    assert card(out, "quantity")["charts"] == [{"queryIndex": 0, "level": 2, "activeValues": []}]
    assert card(out, "quantity")["renderType"] == "chart"


def test_crossing_with_no_level_set_starts_the_chart_at_auto() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "view", "card": "Quantity", "view": "list"},
        {"op": "view", "card": "Quantity", "view": "columns"},
    )
    assert card(out, "quantity")["charts"] == [
        {"queryIndex": 0, "level": "AUTO", "activeValues": []}
    ]


# ── level ──


def test_a_text_card_has_no_level() -> None:
    assert refused(
        cards_for("Channel"), {"op": "level", "card": "Channel", "level": 1}
    ).message == ("A TEXT card has no level; 'Channel' is TEXT.")


@pytest.mark.parametrize(
    ("width", "granularity"),
    [
        (10, {"id": 1, "name": "10"}),
        (1000, {"id": 3, "name": "1,000"}),
        (0.1, {"id": -1, "name": "0.1"}),
        (0.001, {"id": -3, "name": "0.001"}),
        (1, {"id": 0, "name": "1"}),
        (1e10, {"id": 10, "name": "10,000,000,000"}),
    ],
)
def test_a_number_level_is_a_power_of_ten_width(width: float, granularity: dict[str, Any]) -> None:
    out = run(cards_for("Quantity"), {"op": "level", "card": "Quantity", "level": width})
    assert card(out, "quantity")["granularity"] == granularity
    assert card(out, "quantity")["charts"][0]["level"] == granularity["id"]


@pytest.mark.parametrize("width", [5, 0, -10, True, "10", 1e11, 0.0001, 12.5])
def test_other_number_levels_are_refused_with_the_widths_the_menu_offers(width: Any) -> None:
    error = refused(cards_for("Quantity"), {"op": "level", "card": "Quantity", "level": width})
    assert "10,000,000,000, 1,000,000,000, 100,000,000" in error.message
    assert error.message.endswith("1, 0.1, 0.01, 0.001.")


def test_a_date_level_stores_the_web_apps_granularity_options() -> None:
    out = run(cards_for("Order date"), {"op": "level", "card": "Order date", "level": "month"})
    assert card(out, "order_date")["granularity"] == {
        "id": "MONTH",
        "format": "%b, %Y",
        "listFormat": "mmm 'yy",
        "graphFormat": "mmm-yyyy",
    }


def test_an_unknown_date_level_lists_the_levels() -> None:
    error = refused(cards_for("Order date"), {"op": "level", "card": "Order date", "level": "week"})
    assert (
        error.message
        == "'week' is not a date level. Levels: YEAR, MONTH, DAY, HOUR, MINUTE, SECOND."
    )


# ── filter / exclude on a TEXT list card (getListCondition / exclude conditions) ──


def test_filtering_text_keeps_the_listed_values() -> None:
    out = run(
        cards_for("Channel"),
        {"op": "filter", "card": "Channel", "values": ["Amazon", "eBay"]},
    )
    channel = card(out, "channel")
    assert channel["condition"] == {"channel": {"IN_LIST": {"VALUE": ["Amazon", "eBay"]}}}
    assert channel["activeValues"] == [
        {"value": "Amazon", "formatted": "Amazon"},
        {"value": "eBay", "formatted": "eBay"},
    ]
    assert channel["exclude"] is False


def test_the_blank_value_is_null_and_adds_an_is_empty_branch() -> None:
    out = run(cards_for("Channel"), {"op": "filter", "card": "Channel", "values": [None, "Shop"]})
    channel = card(out, "channel")
    assert channel["condition"] == {
        "OR": [{"channel": IS_EMPTY}, {"channel": {"IN_LIST": {"VALUE": ["Shop"]}}}]
    }
    assert channel["activeValues"][0] == {"value": None, "formatted": "(blank)"}


def test_only_the_blank_value_is_a_bare_is_empty() -> None:
    out = run(cards_for("Channel"), {"op": "filter", "card": "Channel", "values": [None]})
    assert card(out, "channel")["condition"] == {"channel": IS_EMPTY}


def test_a_whitespace_value_is_labelled_spaces() -> None:
    out = run(cards_for("Channel"), {"op": "filter", "card": "Channel", "values": [" "]})
    assert card(out, "channel")["activeValues"] == [{"value": " ", "formatted": "(spaces)"}]


def test_excluding_text_puts_blanks_back_because_sql_negation_drops_nulls() -> None:
    out = run(
        cards_for("Channel"), {"op": "exclude", "card": "Channel", "values": ["Amazon", "eBay"]}
    )
    channel = card(out, "channel")
    assert channel["condition"] == {
        "OR": [{"channel": {"NOT_IN_LIST": {"VALUE": ["Amazon", "eBay"]}}}, {"channel": IS_EMPTY}]
    }
    assert channel["exclude"] is True


def test_excluding_the_blank_value_itself_requires_a_non_empty_cell() -> None:
    out = run(
        cards_for("Channel"), {"op": "exclude", "card": "Channel", "values": [None, "Amazon"]}
    )
    assert card(out, "channel")["condition"] == {
        "AND": [
            {"channel": {"NOT_IN_LIST": {"VALUE": ["Amazon"]}}},
            {"channel": {"IS_NOT_EMPTY": True}},
        ]
    }
    only_blank = run(cards_for("Channel"), {"op": "exclude", "card": "Channel", "values": [None]})
    assert card(only_blank, "channel")["condition"] == {"channel": {"IS_NOT_EMPTY": True}}


def test_duplicate_values_are_selected_once() -> None:
    out = run(cards_for("Channel"), {"op": "filter", "card": "Channel", "values": ["Shop", "Shop"]})
    assert card(out, "channel")["condition"] == {"channel": {"IN_LIST": {"VALUE": ["Shop"]}}}


@pytest.mark.parametrize("values", [None, [], "Amazon"])
def test_values_must_be_a_non_empty_list(values: Any) -> None:
    edit: dict[str, Any] = {"op": "filter", "card": "Channel"}
    if values is not None:
        edit["values"] = values
    error = refused(cards_for("Channel"), edit)
    assert error.message in (
        '"values" must be a non-empty list; null stands for the blank value.',
        'The "filter" edit needs "values".',
    )


def test_a_text_value_that_is_not_text_is_refused() -> None:
    assert refused(
        cards_for("Channel"), {"op": "filter", "card": "Channel", "values": [5]}
    ).message == ("5 is not text; this card lists TEXT values.")


def test_a_value_the_card_does_not_list_is_refused_with_what_it_lists() -> None:
    error = refused(
        cards_for("Channel"), {"op": "filter", "card": "Channel", "values": ["Nope", "Shop"]}
    )
    assert error.message == (
        "Not values of the 'Channel' card: 'Nope'. It lists: 'Amazon', 'eBay', 'Shop', ' '."
    )


def test_a_long_value_list_is_cut_after_ten() -> None:
    many = View(channel=[f"v{i}" for i in range(12)])
    error = refused(
        cards_for("Channel"), {"op": "filter", "card": "Channel", "values": ["zzz"]}, view=many
    )
    assert error.message.endswith("'v9'.".replace("'v9'.", "'v9', ...."))


def test_a_number_card_in_its_list_view_cannot_be_filtered_here() -> None:
    cards = run(cards_for("Quantity"), {"op": "view", "card": "Quantity", "view": "list"})
    error = refused(cards, {"op": "filter", "card": "Quantity", "values": [10]})
    assert 'first {"op": "view", "view": "columns"}' in error.message


# ── filter / exclude on a chart card (getChartCondition / getChartRuns) ──


def _bucket(col: str, lower: Any, upper: Any) -> dict[str, Any]:
    return {"AND": [{col: {"GTE": {"VALUE": lower}}}, {col: {"LT": {"VALUE": upper}}}]}


def _outside(col: str, lower: Any, upper: Any) -> dict[str, Any]:
    return {"OR": [{col: {"LT": {"VALUE": lower}}}, {col: {"GTE": {"VALUE": upper}}}]}


def test_adjacent_number_buckets_merge_into_one_range_and_a_gap_splits_it() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "filter", "card": "Quantity", "level": 10, "values": [30, 10, 20, 50]},
    )
    quantity = card(out, "quantity")
    assert quantity["condition"] == {
        "OR": [_bucket("quantity", 10.0, 40), _bucket("quantity", 50.0, 60)]
    }
    assert [v["formatted"] for v in quantity["activeValues"]] == [
        "30 to <40",
        "10 to <20",
        "20 to <30",
        "50 to <60",
    ]
    assert quantity["granularity"] == {"id": 1, "name": "10"}
    # four buckets selected: no drill-down level is added
    assert [c["queryIndex"] for c in quantity["charts"]] == [0]
    assert quantity["charts"][0]["condition"] == quantity["condition"]


def test_selecting_one_bucket_drills_into_the_next_level() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "filter", "card": "Quantity", "level": 10, "values": [20]},
    )
    charts = card(out, "quantity")["charts"]
    assert [c["queryIndex"] for c in charts] == [0, 1]
    assert charts[0]["condition"] == _bucket("quantity", 20.0, 30)
    assert charts[1] == {"queryIndex": 1, "activeValues": [], "level": 0}
    # the card's own condition is the selection on the level it was made at
    assert card(out, "quantity")["condition"] == _bucket("quantity", 20.0, 30)


def test_selecting_the_blank_bucket_alone_does_not_drill() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "filter", "card": "Quantity", "level": 10, "values": [None]},
    )
    assert card(out, "quantity")["condition"] == {"quantity": IS_EMPTY}
    assert len(card(out, "quantity")["charts"]) == 1


def test_a_bucket_selection_with_blank_adds_an_is_empty_branch() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "filter", "card": "Quantity", "level": 10, "values": [10, None]},
    )
    assert card(out, "quantity")["condition"] == {
        "OR": [_bucket("quantity", 10.0, 20), {"quantity": IS_EMPTY}]
    }


def test_excluding_one_run_keeps_blanks_and_does_not_drill() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "exclude", "card": "Quantity", "level": 10, "values": [10, 20]},
    )
    quantity = card(out, "quantity")
    assert quantity["condition"] == {"OR": [_outside("quantity", 10.0, 30), {"quantity": IS_EMPTY}]}
    assert quantity["exclude"] is True
    assert len(quantity["charts"]) == 1


def test_excluding_a_gapped_selection_excludes_each_span() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "exclude", "card": "Quantity", "level": 10, "values": [10, 40]},
    )
    assert card(out, "quantity")["condition"] == {
        "OR": [
            {"AND": [_outside("quantity", 10.0, 20), _outside("quantity", 40.0, 50)]},
            {"quantity": IS_EMPTY},
        ]
    }


def test_excluding_a_bucket_and_the_blank_requires_a_non_empty_cell() -> None:
    out = run(
        cards_for("Quantity"),
        {"op": "exclude", "card": "Quantity", "level": 10, "values": [10, None]},
    )
    assert card(out, "quantity")["condition"] == {
        "AND": [_outside("quantity", 10.0, 20), {"quantity": {"IS_NOT_EMPTY": True}}]
    }


def test_excluding_inside_a_drilled_level_stays_inside_the_parent_bucket() -> None:
    drilled = run(
        cards_for("Quantity"),
        {"op": "filter", "card": "Quantity", "level": 10, "values": [20]},
    )
    out = run(
        drilled, {"op": "exclude", "card": "Quantity", "values": [24]}, view=View(quantity=[24.0])
    )
    quantity = card(out, "quantity")
    assert quantity["condition"] == {
        "AND": [
            _bucket("quantity", 20.0, 30),
            {"OR": [_outside("quantity", 24.0, 25), {"quantity": IS_EMPTY}]},
        ]
    }


def test_a_chart_at_auto_level_needs_a_level_to_have_bucket_bounds() -> None:
    error = refused(cards_for("Quantity"), {"op": "filter", "card": "Quantity", "values": [10]})
    assert error.message == (
        "The 'Quantity' card has no fixed level yet (it is AUTO), so a bucket has no bounds to "
        'filter on. Give "level" in this edit, as the level menu lists it.'
    )


def test_a_number_value_must_be_a_number_and_may_carry_thousands_commas() -> None:
    big = View(quantity=[1000.0, 2000.0])
    out = run(
        cards_for("Quantity"),
        {"op": "filter", "card": "Quantity", "level": 1000, "values": ["1,000"]},
        view=big,
    )
    assert card(out, "quantity")["condition"] == _bucket("quantity", 1000.0, 2000)
    assert card(out, "quantity")["activeValues"][0]["formatted"] == "1,000 to <2,000"
    for bad in ("abc", True, [1], {"a": 1}):
        error = refused(
            cards_for("Quantity"),
            {"op": "filter", "card": "Quantity", "level": 1000, "values": [bad]},
            view=big,
        )
        assert error.message == f"{bad!r} is not a number."


def test_fractional_levels_round_the_upper_bound_to_the_bucket_width() -> None:
    out = run(
        cards_for("Price"),
        {"op": "filter", "card": "Price", "level": 0.1, "values": [0.3]},
        view=View(price=[0.3]),
    )
    assert card(out, "price")["condition"] == _bucket("price", 0.3, 0.4)
    assert card(out, "price")["activeValues"][0]["formatted"] == "0.3 to <0.4"


def test_date_buckets_merge_across_a_year_boundary_and_a_gap_splits() -> None:
    dates = View(
        order_date=[
            "2026-11-01 00:00:00",
            "2026-12-01 00:00:00",
            "2027-01-01 00:00:00",
            "2027-03-01 00:00:00",
        ]
    )
    out = run(
        cards_for("Order date"),
        {
            "op": "filter",
            "card": "Order date",
            "level": "month",
            "values": ["2027-01-01", "2026-11-01", "2026-12-01 00:00", "2027-03-01T00:00:00Z"],
        },
        view=dates,
    )
    order = card(out, "order_date")
    assert order["condition"] == {
        "OR": [
            _bucket("order_date", "2026-11-01 00:00:00", "2027-02-01 00:00:00"),
            _bucket("order_date", "2027-03-01 00:00:00", "2027-04-01 00:00:00"),
        ]
    }
    assert [v["formatted"] for v in order["activeValues"]] == [
        "Jan '27",
        "Nov '26",
        "Dec '26",
        "Mar '27",
    ]
    assert order["charts"][0]["level"] == "MONTH"


def test_a_date_drill_goes_to_the_next_finer_level_and_stops_after_the_finest() -> None:
    out = run(
        cards_for("Order date"),
        {"op": "filter", "card": "Order date", "level": "year", "values": ["2026-01-01"]},
        view=View(order_date=["2026-01-01 00:00:00"]),
    )
    charts = card(out, "order_date")["charts"]
    assert charts[1] == {"queryIndex": 1, "activeValues": [], "level": "MONTH"}
    seconds = run(
        cards_for("Order date"),
        {"op": "filter", "card": "Order date", "level": "second", "values": ["2026-01-01"]},
        view=View(order_date=["2026-01-01 00:00:00"]),
    )
    assert len(card(seconds, "order_date")["charts"]) == 1


@pytest.mark.parametrize(
    ("level", "end"),
    [
        ("YEAR", "2027-01-01 00:00:00"),
        ("MONTH", "2026-02-01 00:00:00"),
        ("DAY", "2026-01-02 00:00:00"),
        ("HOUR", "2026-01-01 01:00:00"),
        ("MINUTE", "2026-01-01 00:01:00"),
        ("SECOND", "2026-01-01 00:00:01"),
    ],
)
def test_a_date_bucket_ends_one_unit_after_it_starts(level: str, end: str) -> None:
    assert ece._upper_bound("DATE", "2026-01-01 00:00:00", level) == end


def test_a_date_that_is_not_a_date_is_refused() -> None:
    error = refused(
        cards_for("Order date"),
        {"op": "filter", "card": "Order date", "level": "day", "values": ["soon"]},
    )
    assert error.message == "'soon' is not a date. Write it as YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."


def test_a_filter_voids_the_filters_of_the_cards_after_it_and_moves_filtered_cards_first() -> None:
    cards = cards_for("Channel", "Quantity")
    cards[1]["condition"] = {"quantity": {"GTE": {"VALUE": 10}}}
    cards[1]["activeValues"] = [{"value": 10.0, "formatted": "10"}]
    cards[1]["exclude"] = True
    cards[1]["charts"][0]["condition"] = cards[1]["condition"]
    cards[1]["charts"].append({"queryIndex": 1, "level": 0, "activeValues": []})
    out = run(cards, {"op": "filter", "card": "Channel", "values": ["Shop"]})
    assert [c["colId"] for c in out] == ["channel", "quantity"]
    quantity = card(out, "quantity")
    assert quantity["condition"] is None
    assert quantity["activeValues"] == []
    assert quantity["exclude"] is False
    assert quantity["charts"] == [
        {"queryIndex": 0, "level": "AUTO", "activeValues": [], "condition": None, "exclude": False}
    ]


def test_filtered_cards_sort_in_front_of_unfiltered_ones_keeping_their_order() -> None:
    cards = cards_for("Quantity", "Price", "Channel")
    out = run(cards, {"op": "filter", "card": "Channel", "values": ["Shop"]})
    assert [c["colId"] for c in out] == ["channel", "quantity", "price"]


# ── clear / remove ──


def test_clearing_one_chart_card_resets_its_filter_and_first_level_but_keeps_other_cards() -> None:
    cards = cards_for("Channel", "Quantity")
    filtered = run(
        cards,
        {"op": "filter", "card": "Channel", "values": ["Shop"]},
        {"op": "filter", "card": "Quantity", "level": 10, "values": [20]},
    )
    out = run(filtered, {"op": "clear", "card": "Quantity"})
    quantity = card(out, "quantity")
    assert quantity["condition"] is None
    assert quantity["charts"] == [{"queryIndex": 0, "activeValues": [], "level": "AUTO"}]
    assert card(out, "channel")["condition"] is not None


def test_clearing_without_a_card_clears_every_card_including_query_cards() -> None:
    filtered = run(
        cards_for("Channel", "Quantity"),
        {"op": "filter", "card": "Channel", "values": ["Shop"]},
        {"op": "search", "text": "leather"},
        {"op": "scatter", "x": "Quantity", "y": "Price", "rect": {"x": [1, 2], "y": [3, 4]}},
    )
    out = run(filtered, {"op": "clear"})
    assert all(c["condition"] is None for c in out)
    assert card(out, "__search__")["query"] == ""
    assert card(out, "__scatter_1")["rect"] is None
    assert card(out, "channel")["activeValues"] == []
    assert all(c.get("exclude") is False for c in out)


def test_clearing_a_query_card_by_its_id() -> None:
    filtered = run(cards_for("Channel"), {"op": "search", "text": "leather"})
    out = run(filtered, {"op": "clear", "card": "__search__"})
    assert card(out, "__search__") | {} == {
        "colId": "__search__",
        "kind": "search",
        "query": "",
        "columns": None,
        "condition": None,
        "exclude": False,
    }


def test_remove_takes_a_column_card_or_a_query_card_by_id_away() -> None:
    cards = run(cards_for("Channel", "Quantity"), {"op": "search", "text": "leather"})
    out = run(cards, {"op": "remove", "card": "__search__"}, {"op": "remove", "card": "Quantity"})
    assert [c["colId"] for c in out] == ["channel"]


# ── search ──


def test_a_search_for_a_word_matches_text_columns_case_insensitively() -> None:
    out = run(cards_for("Channel"), {"op": "search", "text": " Leather "})
    search = card(out, "__search__")
    assert out[0] is search  # a query card opens at the front
    assert search["condition"] == {
        "channel": {"CONTAINS": {"VALUE": ["Leather"]}},
        "STRING_PROP": INSENSITIVE,
    }
    assert search["query"] == "Leather"


def test_a_numeric_term_also_matches_number_columns_and_a_date_term_date_columns() -> None:
    cond = ece.search_condition("30", COLUMNS[:2], False)
    assert cond == {
        "OR": [
            {"channel": {"CONTAINS": {"VALUE": ["30"]}}},
            {"quantity": {"IN_LIST": {"VALUE": [30.0]}}},
        ],
        "STRING_PROP": INSENSITIVE,
    }
    month = ece.search_condition("2024-08", COLUMNS, False)
    assert month is not None
    assert month["OR"][-1] == {
        "order_date": {"EQ": {"VALUE": {"TRUNCATE": "MONTH", "VALUE": "2024-08-01 00:00:00"}}}
    }


def test_excluding_a_search_keeps_rows_no_column_matches_blanks_included() -> None:
    assert ece.search_condition("30", COLUMNS[:2], True) == {
        "AND": [
            {"channel": {"NOT_CONTAINS": {"VALUE": ["30"]}}},
            {
                "OR": [
                    {"quantity": {"NOT_IN_LIST": {"VALUE": [30.0]}}},
                    {"quantity": IS_EMPTY},
                ]
            },
        ],
        "STRING_PROP": INSENSITIVE,
    }
    date = ece.search_condition("2024", [COLUMNS[2]], True)
    assert date == {
        "OR": [
            {"order_date": {"NE": {"VALUE": {"TRUNCATE": "YEAR", "VALUE": "2024-01-01 00:00:00"}}}},
            {"order_date": IS_EMPTY},
        ],
        "STRING_PROP": INSENSITIVE,
    }


def test_commas_are_only_thousands_separators_in_a_search_number() -> None:
    quantity = [COLUMNS[1]]
    assert ece.search_condition("1,200", quantity, False) == {
        "quantity": {"IN_LIST": {"VALUE": [1200.0]}},
        "STRING_PROP": INSENSITIVE,
    }
    negative = ece.search_condition("-1,234,567.5", quantity, False)
    assert negative is not None and negative["quantity"] == {"IN_LIST": {"VALUE": [-1234567.5]}}
    assert ece.search_condition("1,2", COLUMNS[:2], False) == {
        "channel": {"CONTAINS": {"VALUE": ["1,2"]}},
        "STRING_PROP": INSENSITIVE,
    }
    # "12,34" is not a number, and a number column holds nothing else: matches no row
    assert ece.search_condition("12,34", quantity, False) == {
        "AND": [{"quantity": IS_EMPTY}, {"quantity": {"IS_NOT_EMPTY": True}}]
    }


def test_a_term_no_searched_column_can_hold_matches_nothing_and_excluding_it_removes_nothing() -> (
    None
):
    numbers = [COLUMNS[1]]
    assert ece.search_condition("leather", numbers, False) == {
        "AND": [{"quantity": IS_EMPTY}, {"quantity": {"IS_NOT_EMPTY": True}}]
    }
    assert ece.search_condition("leather", numbers, True) is None
    assert ece.search_condition("   ", COLUMNS, False) is None
    assert ece.search_condition("leather", [], False) is None


@pytest.mark.parametrize(
    ("term", "unit", "value"),
    [
        ("2024-08-15", "DAY", "2024-08-15 00:00:00"),
        ("2024/08/15", "DAY", "2024-08-15 00:00:00"),
        ("15 Aug 2024", "DAY", "2024-08-15 00:00:00"),
        ("Aug 15 2024", "DAY", "2024-08-15 00:00:00"),
        ("August 15, 2024", "DAY", "2024-08-15 00:00:00"),
        ("2024-08", "MONTH", "2024-08-01 00:00:00"),
        ("aug 2024", "MONTH", "2024-08-01 00:00:00"),
        ("August 2024", "MONTH", "2024-08-01 00:00:00"),
        ("2024", "YEAR", "2024-01-01 00:00:00"),
    ],
)
def test_the_date_formats_a_search_term_may_take(term: str, unit: str, value: str) -> None:
    assert ece._search_date(term) == {"unit": unit, "value": value}


def test_a_date_like_term_that_is_not_a_real_date_is_not_a_date() -> None:
    assert ece._search_date("2024-13-01") is None
    assert ece._search_date("2024-02-30") is None
    assert ece._search_date("leather") is None


def test_a_search_needs_two_characters_and_reuses_its_single_card() -> None:
    assert refused(cards_for("Channel"), {"op": "search", "text": " a "}).message == (
        "A search needs at least 2 characters."
    )
    out = run(
        cards_for("Channel"), {"op": "search", "text": "leather"}, {"op": "search", "text": "shoe"}
    )
    assert [c["colId"] for c in out].count("__search__") == 1
    assert card(out, "__search__")["query"] == "shoe"


def test_a_search_can_be_limited_to_columns_and_remembers_them() -> None:
    out = run(
        cards_for("Channel"),
        {"op": "search", "text": "30", "columns": ["Channel", "Quantity"]},
        {"op": "search", "text": "40"},
    )
    search = card(out, "__search__")
    assert search["columns"] == ["channel", "quantity"]
    # the second search keeps the narrowed columns: nothing is searched in Order date or Price
    assert set(search["condition"]) == {"OR", "STRING_PROP"}
    assert len(search["condition"]["OR"]) == 2


def test_searching_every_column_stores_no_column_list() -> None:
    out = run(
        cards_for("Channel"),
        {"op": "search", "text": "x1", "columns": [c["display_name"] for c in COLUMNS]},
    )
    assert card(out, "__search__")["columns"] is None


def test_search_columns_must_be_a_non_empty_list_of_known_names() -> None:
    assert refused(cards_for("Channel"), {"op": "search", "text": "xy", "columns": []}).message == (
        '"columns" must be a non-empty list of column display names.'
    )
    assert refused(
        cards_for("Channel"), {"op": "search", "text": "xy", "columns": ["Nope"]}
    ).message.startswith("'Nope' is not a column of this view.")


def test_an_excluding_search_is_stored_as_excluding() -> None:
    out = run(cards_for("Channel"), {"op": "search", "text": "leather", "exclude": True})
    search = card(out, "__search__")
    assert search["exclude"] is True
    assert search["condition"]["STRING_PROP"] == INSENSITIVE
    assert "NOT_CONTAINS" in str(search["condition"])


def test_a_named_search_card_must_be_a_search_card() -> None:
    error = refused(cards_for("Channel"), {"op": "search", "text": "xy", "card": "channel"})
    assert error.message == "'channel' is not a search card. Search cards: none."


# ── scatter ──


def test_a_new_scatter_card_needs_both_axes_and_opens_with_the_web_apps_defaults() -> None:
    assert refused(cards_for("Channel"), {"op": "scatter", "x": "Quantity"}).message == (
        'The "scatter" edit needs "y".'
    )
    out = run(cards_for("Channel"), {"op": "scatter", "x": "Quantity", "y": "Price"})
    assert out[0] == {
        "colId": "__scatter_1",
        "kind": "scatter",
        "x": "quantity",
        "y": "price",
        "colorBy": None,
        "sizeBy": "rows",
        "rect": None,
        "condition": None,
        "exclude": False,
        "width": 480,
    }


def test_scatter_ids_do_not_reuse_a_taken_number() -> None:
    out = run(
        cards_for("Channel"),
        {"op": "scatter", "x": "Quantity", "y": "Price"},
        {"op": "scatter", "x": "Price", "y": "Quantity"},
    )
    assert [c["colId"] for c in out if c.get("kind") == "scatter"] == ["__scatter_2", "__scatter_1"]


def test_a_scatter_box_keeps_rows_inside_it() -> None:
    out = run(
        cards_for("Channel"),
        {"op": "scatter", "x": "Quantity", "y": "Price", "rect": {"x": [1, 2], "y": [10, 20]}},
    )
    assert out[0]["condition"] == {
        "AND": [
            {"quantity": {"GTE": {"VALUE": 1.0}}},
            {"quantity": {"LTE": {"VALUE": 2.0}}},
            {"price": {"GTE": {"VALUE": 10.0}}},
            {"price": {"LTE": {"VALUE": 20.0}}},
        ]
    }
    assert out[0]["rect"] == {"x": [1.0, 2.0], "y": [10.0, 20.0]}


def test_excluding_a_scatter_box_keeps_every_row_outside_it_blanks_on_either_axis_included() -> (
    None
):
    out = run(
        cards_for("Channel"),
        {
            "op": "scatter",
            "x": "Quantity",
            "y": "Price",
            "rect": {"x": [1, 2], "y": [10, 20]},
            "exclude": True,
        },
    )
    assert out[0]["condition"] == {
        "OR": [
            {"quantity": {"LT": {"VALUE": 1.0}}},
            {"quantity": {"GT": {"VALUE": 2.0}}},
            {"price": {"LT": {"VALUE": 10.0}}},
            {"price": {"GT": {"VALUE": 20.0}}},
            {"quantity": IS_EMPTY},
            {"price": IS_EMPTY},
        ]
    }


def test_changing_an_axis_drops_the_box_and_its_filter() -> None:
    boxed = run(
        cards_for("Channel"),
        {"op": "scatter", "x": "Quantity", "y": "Price", "rect": {"x": [1, 2], "y": [3, 4]}},
    )
    out = run(boxed, {"op": "scatter", "card": "__scatter_1", "x": "Price"})
    assert out[0]["x"] == "price"
    assert (out[0]["rect"], out[0]["condition"], out[0]["exclude"]) == (None, None, False)


def test_a_scatter_axis_must_be_numeric() -> None:
    error = refused(cards_for("Channel"), {"op": "scatter", "x": "Channel", "y": "Price"})
    assert error.message == (
        "A scatter plots numbers, and \"x\" 'Channel' is TEXT. Numeric columns: Quantity, Price."
    )


@pytest.mark.parametrize(
    "rect",
    [
        [1, 2],
        {"x": [1, 2]},
        {"x": [1, 2], "y": [3, 4], "z": [0, 1]},
        {"x": [2, 1], "y": [3, 4]},
        {"x": [1], "y": [3, 4]},
        {"x": [1, True], "y": [3, 4]},
        {"x": ["a", "b"], "y": [3, 4]},
    ],
)
def test_a_scatter_box_must_be_low_high_pairs_on_both_axes(rect: Any) -> None:
    error = refused(
        cards_for("Channel"), {"op": "scatter", "x": "Quantity", "y": "Price", "rect": rect}
    )
    assert error.message == '"rect" must be {"x": [low, high], "y": [low, high]} with low <= high.'


def test_a_named_scatter_card_must_exist() -> None:
    error = refused(cards_for("Channel"), {"op": "scatter", "card": "__scatter_9", "x": "Price"})
    assert error.message == "'__scatter_9' is not a scatter card. Scatter cards: none."


# ── ask ──


def test_an_ask_card_stores_the_understood_condition_and_the_question() -> None:
    view = View()
    view.answer = {"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}, "STRING_PROP": INSENSITIVE}
    out = run(cards_for("Channel"), {"op": "ask", "question": " amazon only "}, view=view)
    assert view.asked == ["amazon only"]
    assert out[0] == {
        "colId": "__ask_1",
        "kind": "ask",
        "prompt": "amazon only",
        "understood": view.answer,
        "condition": view.answer,
        "exclude": False,
    }


def test_an_excluding_ask_stores_the_negated_condition_and_keeps_the_reading() -> None:
    view = View()
    view.answer = {"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}, "STRING_PROP": INSENSITIVE}
    out = run(
        cards_for("Channel"), {"op": "ask", "question": "amazon only", "exclude": True}, view=view
    )
    assert out[0]["understood"] == view.answer
    assert out[0]["exclude"] is True
    assert out[0]["condition"] == {
        "OR": [{"NOT": {"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}}}, {"channel": IS_EMPTY}],
        "STRING_PROP": INSENSITIVE,
    }


def test_an_ask_that_reads_as_no_condition_is_refused_and_a_short_one_is_not_sent() -> None:
    view = View()
    error = refused(cards_for("Channel"), {"op": "ask", "question": "gibberish"}, view=view)
    assert error.message == (
        "The question could not be read as a condition: 'gibberish'. Say it another way."
    )
    short = refused(cards_for("Channel"), {"op": "ask", "question": "ab"}, view=view)
    assert short.message == '"question" must say what to keep, in more than two characters.'
    assert view.asked == ["gibberish"]


def test_ask_ids_number_up_from_the_taken_ones() -> None:
    view = View()
    view.answer = {"channel": IS_EMPTY}
    out = run(
        cards_for("Channel"),
        {"op": "ask", "question": "missing channel"},
        {"op": "ask", "question": "missing channel again"},
        view=view,
    )
    assert [c["colId"] for c in out if c.get("kind") == "ask"] == ["__ask_2", "__ask_1"]


def test_a_named_ask_card_is_updated_in_place() -> None:
    view = View()
    view.answer = {"channel": IS_EMPTY}
    first = run(cards_for("Channel"), {"op": "ask", "question": "missing channel"}, view=view)
    view.answer = {"channel": {"IS_NOT_EMPTY": True}}
    out = run(first, {"op": "ask", "card": "__ask_1", "question": "has a channel"}, view=view)
    assert [c["colId"] for c in out] == ["__ask_1", "channel"]
    assert out[0]["prompt"] == "has a channel"


def test_the_asked_condition_loses_its_authoring_keys() -> None:
    understood = {
        "AND": [{"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}}],
        "STRING_PROP": INSENSITIVE,
        "FILTER_TYPE": "CONDITION",
        "PROMPT": "amazon",
    }
    assert ece.normalize_ask_condition(understood) == {
        "AND": understood["AND"],
        "STRING_PROP": INSENSITIVE,
    }
    assert ece.normalize_ask_condition({"FILTER_TYPE": "X"}) is None
    assert ece.normalize_ask_condition({"STRING_PROP": INSENSITIVE}) is None
    assert ece.normalize_ask_condition(None) is None
    assert ece.normalize_ask_condition([1]) is None


# ── negate_condition: the web app's three-valued-logic check ──

_PROPS = {"STRING_PROP", "FILTER_TYPE", "PROMPT"}


def _evaluate(node: dict[str, Any], row: dict[str, Any]) -> bool | None:
    """SQL's three-valued logic in miniature (query-cards.utils.test.js): a clause on a blank
    cell is unknown, and a WHERE keeps only rows that are true."""
    results: list[bool | None] = []
    for key, value in node.items():
        if key in _PROPS:
            continue
        if key in ("AND", "OR"):
            kids = [_evaluate(child, row) for child in value]
            if key == "AND":
                results.append(False if False in kids else None if None in kids else True)
            else:
                results.append(True if True in kids else None if None in kids else False)
        elif key == "NOT":
            inner = _evaluate(value, row)
            results.append(None if inner is None else not inner)
        else:
            cell = row.get(key)
            (operator,) = value
            if operator == "IS_EMPTY":
                results.append(cell is None)
            elif operator == "IS_NOT_EMPTY":
                results.append(cell is not None)
            elif cell is None:
                results.append(None)
            elif operator == "IN_LIST":
                results.append(cell in value["IN_LIST"]["VALUE"])
            elif operator == "GTE":
                results.append(cell >= value["GTE"]["VALUE"])
            else:
                raise AssertionError(operator)
    return False if False in results else None if None in results else True


_ROWS = [
    {"channel": "Amazon", "quantity": 5},
    {"channel": "Amazon", "quantity": 1},
    {"channel": "eBay", "quantity": None},
    {"channel": None, "quantity": 9},
    {"channel": None, "quantity": None},
    {"channel": "Shop", "quantity": 7},
]
_UNDERSTOOD = {
    "AND": [
        {"channel": {"IN_LIST": {"VALUE": ["Amazon", "eBay"]}}},
        {"quantity": {"GTE": {"VALUE": 2}}},
    ],
    "STRING_PROP": INSENSITIVE,
}


@pytest.mark.parametrize(
    "condition",
    [
        _UNDERSTOOD,
        {
            "OR": [
                {"channel": {"IN_LIST": {"VALUE": ["eBay"]}}},
                {"quantity": {"GTE": {"VALUE": 6}}},
            ]
        },
        {"channel": IS_EMPTY},
        {"quantity": {"IS_NOT_EMPTY": True}},
        {"NOT": {"channel": {"IN_LIST": {"VALUE": ["Amazon"]}}}},
        {"OR": [{"channel": {"IN_LIST": {"VALUE": ["Shop"]}}}, {"NOT": {"quantity": IS_EMPTY}}]},
    ],
    ids=["and", "or", "is-missing", "is-not-missing", "not", "not-of-emptiness-in-or"],
)
def test_exclude_keeps_exactly_the_rows_the_reading_does_not_keep_blanks_included(
    condition: dict[str, Any],
) -> None:
    negated = ece.negate_condition(condition)
    assert negated is not None
    kept = [r for r in _ROWS if _evaluate(negated, r) is True]
    not_kept = [r for r in _ROWS if _evaluate(condition, r) is not True]
    assert kept == not_kept


def test_negation_keeps_the_case_setting_and_has_nothing_to_negate_without_a_reading() -> None:
    negated = ece.negate_condition(_UNDERSTOOD)
    assert negated is not None and negated["STRING_PROP"] == INSENSITIVE
    assert ece.negate_condition(None) is None


# ── small helpers ──


def test_guess_number_level_reads_the_bucket_width_from_neighbouring_starts() -> None:
    assert ece.guess_number_level([0.0, 10.0, 20.0, 30.0]) == 1
    assert ece.guess_number_level([0.0, 100.0, 200.0]) == 2
    assert ece.guess_number_level([1.0, 2.0, 3.0]) == 0
    assert ece.guess_number_level([0.5, 0.6, 0.7]) == -1
    assert ece.guess_number_level([5.0]) is None
    assert ece.guess_number_level([]) is None


def test_guess_number_level_takes_the_most_common_width_among_the_first_ten_gaps() -> None:
    values = [float(i * 10) for i in range(11)] + [1000.0, 1001.0, 1002.0]
    assert ece.guess_number_level(values) == 1


@pytest.mark.parametrize(
    ("raw", "text"),
    [
        ("2026-03-04", "2026-03-04 00:00:00"),
        ("2026-03-04 05:06", "2026-03-04 05:06:00"),
        ("2026-03-04T05:06:07", "2026-03-04 05:06:07"),
        ("2026-03-04T05:06:07Z", "2026-03-04 05:06:07"),
        ("2026-03-04T05:06:07+05:30", "2026-03-04 05:06:07"),
    ],
)
def test_date_text_normalises_the_spellings_the_rows_use(raw: str, text: str) -> None:
    assert ece.date_text(raw) == text


@pytest.mark.parametrize(
    ("value", "text"),
    [(1234567.8912, "1,234,567.891"), (10.0, "10"), (0.5, "0.5"), (-0.0, "0"), (1000, "1,000")],
)
def test_numbers_are_grouped_with_at_most_three_decimals(value: float, text: str) -> None:
    assert ece.number_with_commas(value) == text


def test_date_masks_follow_the_dateformat_package() -> None:
    moment = datetime(2026, 3, 4, 15, 6, 7)
    assert ece.date_format(moment, "yyyy") == "2026"
    assert ece.date_format(moment, "mmm 'yy") == "Mar '26"
    assert ece.date_format(moment, "dd-mmm-yyyy hh:MM:ss") == "04-Mar-2026 03:06:07"
    assert ece.date_format(moment, "h:MM tt") == "3:06 pm"
    assert ece.date_format(datetime(2026, 3, 4, 0, 5), "h tt") == "12 am"
    assert ece.date_format(moment, "d") == "4"
