"""Read-option truth: order_by/top, unordered flags, TEXT-date bucket plans."""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import read_queries

_AS_MAP = {"group_0": "Region", "agg_0": "Total Sales"}


def test_order_by_a_label_becomes_a_backend_sort_on_the_internal_name() -> None:
    sort, top = read_queries.parse_order(
        {"order_by": [{"column": "Total Sales", "direction": "desc"}], "top": 5}, _AS_MAP
    )
    assert sort == [["agg_0", "DESC"]]
    assert top == 5


def test_order_by_accepts_the_short_string_form_and_defaults_to_descending() -> None:
    assert read_queries.parse_order({"order_by": ["Region asc"]}, _AS_MAP)[0] == [
        ["group_0", "ASC"]
    ]
    assert read_queries.parse_order({"order_by": ["Total Sales"]}, _AS_MAP)[0] == [
        ["agg_0", "DESC"]
    ]


def test_order_by_a_column_the_result_does_not_have_fails_loud_with_the_choices() -> None:
    with pytest.raises(CliError) as caught:
        read_queries.parse_order({"order_by": ["Profit"]}, _AS_MAP)
    assert "Total Sales" in (caught.value.hint or "")


def test_top_without_an_order_fails_loud() -> None:
    with pytest.raises(CliError) as caught:
        read_queries.parse_order({"top": 3}, _AS_MAP)
    assert "order_by" in caught.value.message


def test_top_and_limit_together_are_ambiguous() -> None:
    with pytest.raises(CliError):
        read_queries.parse_order({"order_by": ["Region"], "top": 3, "limit": 9}, _AS_MAP)


def test_more_than_three_sort_keys_fail_loud() -> None:
    with pytest.raises(CliError):
        read_queries.parse_order({"order_by": ["Region"] * 4}, _AS_MAP)


def test_a_limit_without_order_by_is_flagged_unordered() -> None:
    flagged = read_queries.mark_unordered({"limit": 10}, {"data": []})
    assert flagged["ordered"] is False
    assert "arbitrary" in flagged["note"]


def test_a_ranked_or_unlimited_result_is_not_flagged() -> None:
    result = {"data": []}
    assert read_queries.mark_unordered({"limit": 10, "order_by": ["Region"]}, result) == result
    assert read_queries.mark_unordered({}, result) == result


def test_sort_locally_orders_by_the_keys_with_blanks_last() -> None:
    rows = [{"agg_0": 1}, {"agg_0": None}, {"agg_0": 9}, {"agg_0": 5}]
    ordered = read_queries.sort_locally(rows, [["agg_0", "DESC"]])
    assert [r["agg_0"] for r in ordered] == [9, 5, 1, None]


def test_truncate_on_a_numeric_column_is_refused_not_ignored() -> None:
    with pytest.raises(CliError) as caught:
        read_queries.text_date_group_levels(
            [{"column": "Sales", "truncate": "MONTH"}], {"Sales": "NUMERIC"}
        )
    assert "DATE column" in caught.value.message


def test_truncate_on_a_text_column_is_planned_for_text_date_bucketing() -> None:
    levels = read_queries.text_date_group_levels(
        ["Region", {"column": "Order Date", "truncate": "month"}],
        {"Region": "TEXT", "Order Date": "TEXT"},
    )
    assert levels == {1: "MONTH"}


def test_truncate_on_a_real_date_column_is_left_to_the_backend() -> None:
    assert (
        read_queries.text_date_group_levels(
            [{"column": "Day", "truncate": "MONTH"}], {"Day": "DATE"}
        )
        == {}
    )


def test_resolution_on_a_non_numeric_column_is_refused() -> None:
    with pytest.raises(CliError):
        read_queries.text_date_group_levels(
            [{"column": "Region", "resolution": 10}], {"Region": "TEXT"}
        )


def test_avg_is_planned_as_sum_and_count_so_buckets_can_be_recombined() -> None:
    plan = read_queries._plan_aggregations(
        [{"function": "AVG", "column": "column_3", "as_name": "Avg"}]
    )
    assert [a["function"] for a in plan.aggregations] == ["SUM", "COUNT"]
    assert plan.averages == {"agg_0": "agg_1"}


def test_a_function_that_cannot_be_recombined_fails_loud() -> None:
    with pytest.raises(CliError) as caught:
        read_queries._plan_aggregations(
            [{"function": "DISTINCT_COUNT", "column": "column_3", "as_name": "d"}]
        )
    assert "recombined" in caught.value.message


def test_averages_are_finished_from_the_bucketed_sum_and_count() -> None:
    rows = [{"agg_0": 30, "agg_1": 3}, {"agg_0": 5, "agg_1": 0}]
    read_queries._finish_averages(rows, {"agg_0": "agg_1"})
    assert rows == [{"agg_0": 10}, {"agg_0": None}]


def test_condition_columns_walks_and_or_not() -> None:
    spec = {
        "and": [
            {"column": "Order Date", "operator": "GTE", "value": "2018-01-01"},
            {"or": [{"column": "Region", "operator": "EQ", "value": "West"}]},
            {"not": {"column": "Order Date", "operator": "LT", "value": "2019-01-01"}},
        ]
    }
    assert read_queries.condition_columns(spec) == ["Order Date", "Region"]
