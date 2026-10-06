"""Read-option truth: order_by/top, unordered flags, TEXT-date bucket plans."""

from __future__ import annotations

import pytest
from mammoth.exceptions import MammothValidationError

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import read_queries
from mammoth_cli.services.testing import FakeMammothService

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


# -- date coverage on reads ---------------------------------------------------

_DATE_RANGE = {"data": [{"agg_0": "2014-01-03", "agg_1": "2017-12-30"}]}


def _reads(response: dict[str, object], column_types: dict[str, str]) -> read_queries.ReadContext:
    service = FakeMammothService()
    service.responses[read_queries.AGGREGATE_SYMBOL] = response
    return read_queries.ReadContext(service, 1, 2, 3, {"Order Date": "column_1"}, column_types)


def test_a_zero_metric_under_a_condition_is_reported_like_no_match() -> None:
    reads = _reads(_DATE_RANGE, {"Order Date": "DATE"})
    for zero in (0, 0.0):
        data = read_queries.with_observed_range(reads, {"data": [{"RESULT": zero}]}, ["Order Date"])
        assert "empty_result" in data
        assert data["observed_range"][0]["max"] == "2017-12-30"


def test_a_nonzero_or_grouped_result_is_not_treated_as_no_match() -> None:
    reads = _reads(_DATE_RANGE, {"Order Date": "DATE"})
    for rows in ([{"RESULT": 5}], [{"group_0": "A", "agg_0": 0}], [{"a": 0}, {"a": 0}]):
        data = read_queries.with_observed_range(reads, {"data": rows}, ["Order Date"])
        assert "empty_result" not in data
    assert reads.service.calls == []


def test_a_zero_metric_without_any_condition_column_is_left_alone() -> None:
    reads = _reads(_DATE_RANGE, {})
    data = {"data": [{"RESULT": 0}]}
    assert read_queries.with_observed_range(reads, data, []) == data


def test_a_non_empty_aggregate_on_a_date_column_carries_coverage_from_one_query() -> None:
    reads = _reads(_DATE_RANGE, {"Order Date": "DATE", "Region": "TEXT"})
    data = read_queries.with_observed_range(
        reads, {"data": [{"RESULT": 5}]}, ["Region", "Order Date"], coverage=True
    )
    assert data["coverage"] == {"column": "Order Date", "min": "2014-01-03", "max": "2017-12-30"}
    assert "empty_result" not in data
    assert len(reads.service.calls) == 1


def test_coverage_is_only_added_when_asked_for() -> None:
    reads = _reads(_DATE_RANGE, {"Order Date": "DATE"})
    data = read_queries.with_observed_range(reads, {"data": [{"RESULT": 5}]}, ["Order Date"])
    assert "coverage" not in data and reads.service.calls == []


def test_a_text_date_column_gets_coverage_from_its_parsed_values() -> None:
    distinct = {"data": [{"group_0": "3/27/2018"}, {"group_0": "1/13/2014"}]}
    reads = _reads(distinct, {"Order Date": "TEXT"})
    reads.column_days("Order Date")  # what a text-date condition or truncate already did
    calls_before = len(reads.service.calls)
    data = read_queries.with_observed_range(
        reads, {"data": [{"RESULT": 5}]}, ["Order Date"], coverage=True
    )
    assert data["coverage"]["column"] == "Order Date"
    assert (data["coverage"]["min"], data["coverage"]["max"]) == ("2014-01-13", "2018-03-27")
    assert len(reads.service.calls) == calls_before


def test_a_plain_text_filter_column_gets_no_coverage_and_costs_no_query() -> None:
    reads = _reads({"data": []}, {"Region": "TEXT"})
    data = read_queries.with_observed_range(
        reads, {"data": [{"RESULT": 5}]}, ["Region"], coverage=True
    )
    assert "coverage" not in data and reads.service.calls == []


# -- explore: percentage_of "metric" and metric_* sorts -----------------------


def _bucketed_rows() -> list[dict[str, object]]:
    """Rows as the backend returns them: a count (agg_0) and a metric (agg_1) per bucket."""
    return [
        {"group_0": "North", "agg_0": 50, "agg_1": 100.0},
        {"group_0": "South", "agg_0": 30, "agg_1": 300.0},
        {"group_0": "East", "agg_0": 20, "agg_1": 600.0},
    ]


def test_explore_percentage_of_metric_shares_by_the_metric_not_the_count() -> None:
    rows = read_queries.apply_explore_order(
        _bucketed_rows(), "value_asc", (None, None), percentage_of="metric"
    )
    assert {row["group_0"]: row["percentage"] for row in rows} == {
        "North": 10.0,
        "South": 30.0,
        "East": 60.0,
    }


def test_explore_percentage_defaults_to_the_count_share() -> None:
    rows = read_queries.apply_explore_order(_bucketed_rows(), "value_asc", (None, None))
    assert {row["group_0"]: row["percentage"] for row in rows} == {
        "North": 50.0,
        "South": 30.0,
        "East": 20.0,
    }


def test_explore_percentage_of_metric_without_a_metric_fails_loud() -> None:
    counted = [{"group_0": "North", "agg_0": 5}, {"group_0": "South", "agg_0": 5}]
    with pytest.raises(MammothValidationError):
        read_queries.apply_explore_order(counted, None, (None, None), percentage_of="metric")


def test_explore_sort_metric_desc_and_asc_rank_by_the_metric_with_blanks_last() -> None:
    rows = [*_bucketed_rows(), {"group_0": "West", "agg_0": 9, "agg_1": None}]
    descending = read_queries.apply_explore_order(
        [dict(r) for r in rows], "metric_desc", (None, None)
    )
    ascending = read_queries.apply_explore_order(
        [dict(r) for r in rows], "metric_asc", (None, None)
    )
    assert [r["group_0"] for r in descending] == ["East", "South", "North", "West"]
    assert [r["group_0"] for r in ascending] == ["North", "South", "East", "West"]


@pytest.mark.parametrize("order", ["metric_desc", "metric_asc"])
def test_explore_sort_by_metric_without_a_metric_fails_loud(order: str) -> None:
    counted = [{"group_0": "North", "agg_0": 5}, {"group_0": "South", "agg_0": 7}]
    with pytest.raises(MammothValidationError):
        read_queries.apply_explore_order(counted, order, (None, None))
