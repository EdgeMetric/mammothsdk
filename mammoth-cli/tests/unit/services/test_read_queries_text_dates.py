"""Read helpers that look inside a view's values: date ranges on TEXT columns, spelling hints,
leader shares and empty-result coverage.

Expected values are worked out by hand from the stored values listed in each test (which stored
string is on which side of a date bound, which count is what share of a total), following each
function's docstring in ``mammoth_cli/services/read_queries.py``.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import data_profile, text_dates
from mammoth_cli.services import read_queries as rq
from mammoth_cli.services.testing import FakeMammothService


def _ctx(
    answer: Any,
    types: dict[str, str],
    internal: dict[str, str] | None = None,
) -> rq.ReadContext:
    service = FakeMammothService()
    service.responses[rq.AGGREGATE_SYMBOL] = answer
    return rq.ReadContext(
        service,
        dataset_id=9,
        view_id=7,
        project_id=180,
        display_to_internal=internal or {name: f"column_{name.lower()}" for name in types},
        column_types=types,
    )


def _queries(ctx: rq.ReadContext) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in ctx.service.call_log if name == rq.AGGREGATE_SYMBOL]


#: Distinct stored values of the TEXT date column "Day", as the backend returns them grouped.
_DAYS = ["2026-01-10", "2026-02-10", "2026-03-10", "2026-04-10", None]


def _day_ctx() -> rq.ReadContext:
    rows = {"data": [{"group_0": v, "agg_0": 1} for v in _DAYS]}
    return _ctx(rows, {"Day": "TEXT", "Qty": "NUMERIC"})


# ── a range on a TEXT date column becomes the stored values inside it ──


@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        ("GT", "2026-02-10", ["2026-03-10", "2026-04-10"]),
        ("GTE", "2026-02-10", ["2026-02-10", "2026-03-10", "2026-04-10"]),
        ("LT", "2026-02-10", ["2026-01-10"]),
        ("LTE", "2026-02-10", ["2026-01-10", "2026-02-10"]),
        ("IN_RANGE", ["2026-02-01", "2026-03-31"], ["2026-02-10", "2026-03-10"]),
        ("GT", "2030-01-01", [rq.NO_MATCH]),
    ],
)
def test_a_date_range_on_a_text_column_is_the_list_of_stored_values_inside_it(
    operator: str, value: Any, expected: list[str]
) -> None:
    out = rq.resolve_text_date_conditions(
        _day_ctx(), {"column": "Day", "operator": operator, "value": value}
    )
    assert out == {"column": "Day", "operator": "IN_LIST", "value": expected}


def test_a_blank_stored_value_is_never_inside_a_range() -> None:
    out = rq.resolve_text_date_conditions(
        _day_ctx(), {"column": "Day", "operator": "LT", "value": "2100-01-01"}
    )
    assert len(out["value"]) == 4


def test_the_distinct_values_are_read_once_for_all_the_leaves_of_a_condition() -> None:
    ctx = _day_ctx()
    spec = {
        "and": [
            {"column": "Day", "operator": "GTE", "value": "2026-02-01"},
            {"not": {"column": "Day", "operator": "GT", "value": "2026-03-31"}},
        ]
    }
    out = rq.resolve_text_date_conditions(ctx, spec)
    assert out == {
        "and": [
            {"column": "Day", "operator": "IN_LIST", "value": _DAYS[1:4]},
            {"not": {"column": "Day", "operator": "IN_LIST", "value": [_DAYS[3]]}},
        ]
    }
    assert len(_queries(ctx)) == 1
    assert _queries(ctx)[0]["group_by"] == ["column_day"]


def test_an_or_condition_is_rewritten_leaf_by_leaf() -> None:
    out = rq.resolve_text_date_conditions(
        _day_ctx(),
        {
            "or": [
                {"column": "Day", "operator": "LT", "value": "2026-02-01"},
                {"column": "Qty", "operator": "GT", "value": 5},
            ]
        },
    )
    assert out == {
        "or": [
            {"column": "Day", "operator": "IN_LIST", "value": ["2026-01-10"]},
            {"column": "Qty", "operator": "GT", "value": 5},
        ]
    }


@pytest.mark.parametrize(
    "leaf",
    [
        {"column": "Qty", "operator": "GT", "value": "2026-01-01"},  # not a TEXT column
        {"column": "Day", "operator": "EQ", "value": "2026-01-10"},  # not a range operator
        {"column": "Day", "operator": "GT", "value": "2026-01-01", "value_is_column": True},
        {"column": "Day", "operator": "GT", "value": "Jan 2026"},  # not an ISO bound
        {"column": "Day", "operator": "IN_RANGE", "value": ["2026-01-01"]},  # not a pair
        {"column": "Day", "operator": "IN_RANGE", "value": "2026-01-01"},
    ],
)
def test_a_leaf_that_is_not_an_iso_range_on_a_text_column_passes_through(
    leaf: dict[str, Any],
) -> None:
    ctx = _day_ctx()
    assert rq.resolve_text_date_conditions(ctx, leaf) == leaf
    assert _queries(ctx) == []


def test_a_condition_that_is_not_a_mapping_passes_through() -> None:
    assert rq.resolve_text_date_conditions(_day_ctx(), None) is None
    assert rq.resolve_text_date_conditions(_day_ctx(), {"and": "x"}) == {"and": "x"}


def test_an_iso_looking_bound_that_is_not_a_calendar_date_is_refused_by_column() -> None:
    with pytest.raises(CliError) as excinfo:
        rq.resolve_text_date_conditions(
            _day_ctx(), {"column": "Day", "operator": "GT", "value": "2026-02-30"}
        )
    assert excinfo.value.message == "'2026-02-30' is not a real calendar date (column 'Day')."


def test_a_text_column_with_more_distinct_values_than_the_cap_is_too_many_to_read_as_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(text_dates, "MAX_DISTINCT_VALUES", 2)
    ctx = _ctx({"data": [{"group_0": f"2026-01-{n:02d}"} for n in (1, 2, 3)]}, {"Day": "TEXT"})
    with pytest.raises(CliError) as excinfo:
        ctx.column_days("Day")
    assert excinfo.value.message == (
        "Column 'Day' has more than 2 distinct values, too many to read as dates."
    )
    assert _queries(ctx)[0]["limit"] == 3  # one more than the cap, to tell "more" from "exactly"


# ── group_by entries with a truncate / part ──


def test_part_needs_a_date_or_text_column_and_not_a_truncate_beside_it() -> None:
    with pytest.raises(CliError) as excinfo:
        rq.text_date_group_levels([{"column": "Qty", "part": "MONTH"}], {"Qty": "NUMERIC"})
    assert excinfo.value.message == (
        "'part' groups a DATE column, or a TEXT column of dates; 'Qty' is NUMERIC."
    )
    with pytest.raises(CliError) as both:
        rq.text_date_group_levels(
            [{"column": "Day", "part": "MONTH", "truncate": "YEAR"}], {"Day": "TEXT"}
        )
    assert both.value.message == "Give 'part' or 'truncate' for 'Day', not both."


def test_a_part_on_a_text_or_date_column_is_bucketed_by_the_cli() -> None:
    levels = rq.text_date_group_levels(
        [{"column": "Day", "part": "MONTH"}, "plain", {"column": "Day", "truncate": "YEAR"}],
        {"Day": "TEXT"},
    )
    assert set(levels) == {0, 2}
    assert levels[0] == "part:month"  # a named calendar part, not a period start
    assert levels[2] == "YEAR"
    assert rq.text_date_group_levels("not a list", {}) == {}


# ── explore range ──


def test_range_of_a_number_column_asks_for_its_min_and_max_under_the_condition() -> None:
    ctx = _ctx({"data": [{"agg_0": 3, "agg_1": 90}]}, {"Qty": "NUMERIC"})
    condition = {"column_qty": {"GT": {"VALUE": 1}}}
    assert rq.explore_range(ctx, "Qty", condition, False) == {
        "column": "Qty",
        "type": "NUMERIC",
        "min": 3,
        "max": 90,
    }
    (query,) = _queries(ctx)
    assert query["condition"] == condition
    assert [(a["function"], a["column"]) for a in query["aggregations"]] == [
        ("MIN", "column_qty"),
        ("MAX", "column_qty"),
    ]


def test_range_of_an_empty_column_says_so_with_nulls() -> None:
    ctx = _ctx({"data": []}, {"When": "DATE"})
    assert rq.explore_range(ctx, "When", None, False) == {
        "column": "When",
        "type": "DATE",
        "min": None,
        "max": None,
    }


def test_range_of_a_text_date_column_is_its_parsed_first_and_last_day() -> None:
    out = rq.explore_range(_day_ctx(), "Day", None, True)
    assert out["min"] == "2026-01-10"
    assert out["max"] == "2026-04-10"
    assert out["column"] == "Day"
    assert out["type"].startswith("TEXT date (")


def test_range_of_a_text_date_column_cannot_honour_a_condition() -> None:
    with pytest.raises(CliError) as excinfo:
        rq.explore_range(_day_ctx(), "Day", {"column_day": {}}, True)
    assert excinfo.value.message == (
        "'range' of the text-date column 'Day' cannot honour a condition."
    )


@pytest.mark.parametrize(("types", "kind"), [({"Name": "TEXT"}, "TEXT"), ({}, "unknown")])
def test_range_needs_a_date_or_number_column(types: dict[str, str], kind: str) -> None:
    with pytest.raises(CliError) as excinfo:
        rq.explore_range(_ctx({}, types), "Name", None, False)
    assert excinfo.value.message == (
        f"'range' needs a DATE, NUMERIC or text-date column; 'Name' is {kind}."
    )


# ── spelling variants hint ──


def _names(counts: dict[Any, int]) -> rq.ReadContext:
    return _ctx({"data": [{"group_0": k, "agg_0": n} for k, n in counts.items()]}, {"Name": "TEXT"})


def test_a_text_read_says_how_many_spelling_groups_its_values_hold() -> None:
    ctx = _names({"Acme Ltd": 3, "ACME Limited": 2, "Zed": 1, None: 4})
    out = rq.with_variant_hint(ctx, {"data": []}, "Name")
    found = out["spelling_variants"]
    assert found["checked"] is True
    assert found["groups"] + found["likely_groups"] >= 1
    assert sorted(found["examples"][0]) == ["ACME Limited", "Acme Ltd"]
    assert found["next"].startswith("mammoth view data profile 7 lists every group")


def test_a_clean_text_column_reports_no_groups_and_no_examples() -> None:
    out = rq.with_variant_hint(_names({"Acme": 3, "Zed": 1}), {"data": []}, "Name")
    assert out["spelling_variants"] == {"checked": True, "groups": 0, "likely_groups": 0}


def test_a_text_column_with_too_many_values_is_not_checked_and_says_why() -> None:
    limit = data_profile.MAX_LISTED_DISTINCT
    ctx = _ctx(
        {"data": [{"group_0": f"v{n}", "agg_0": 1} for n in range(limit + 2)]}, {"N": "TEXT"}
    )
    out = rq.with_variant_hint(ctx, {"data": []}, "N")
    assert out["spelling_variants"] == {
        "checked": False,
        "reason": f"more than {limit} distinct values",
    }
    assert _queries(ctx)[0]["limit"] == limit + 2


def test_a_read_of_another_type_or_a_non_mapping_is_left_alone() -> None:
    ctx = _ctx({}, {"Qty": "NUMERIC"})
    assert rq.with_variant_hint(ctx, {"data": []}, "Qty") == {"data": []}
    assert rq.with_variant_hint(_names({}), ["x"], "Name") == ["x"]
    assert _queries(ctx) == []


# ── leader share ──


def _share(rows: list[dict[str, Any]], total: Any) -> Any:
    ctx = _ctx({"data": [{"agg_0": total}]}, {"Qty": "NUMERIC"})
    fields = {
        "aggregations": [
            {"function": "AVG", "column": "c", "as_name": "avg"},
            {"function": "SUM", "column": "c", "as_name": "total"},
        ],
        "group_by": ["g"],
    }
    out = rq.with_leader_share(ctx, {"data": rows}, fields, {"cond": 1}, 2)
    return out, ctx


def test_the_leaders_share_of_the_filtered_total_uses_the_first_summable_aggregate() -> None:
    rows = [{"agg_0": 5, "agg_1": 40.0}, {"agg_0": 6, "agg_1": 10.0}]
    out, ctx = _share(rows, 100.0)
    assert out["share_of_total"] == {
        "aggregation": "total",
        "total": 100.0,
        "first_row": 0.4,
        "returned_rows": 0.5,
    }
    (query,) = _queries(ctx)
    assert query == {
        "dataset_id": 9,
        "dataview_id": 7,
        "project_id": 180,
        "aggregations": [{"function": "SUM", "column": "c", "as_name": "total"}],
        "condition": {"cond": 1},
    }


@pytest.mark.parametrize("total", [0, None, "n/a"])
def test_a_total_that_is_zero_or_not_a_number_gives_no_share(total: Any) -> None:
    out, _ = _share([{"agg_1": 4.0}], total)
    assert "share_of_total" not in out


def test_a_row_without_a_number_gives_no_share() -> None:
    out, _ = _share([{"agg_1": 4.0}, {"agg_1": None}], 100.0)
    assert "share_of_total" not in out


def test_no_share_is_asked_for_an_ungrouped_or_unlimited_read() -> None:
    ctx = _ctx({"data": [{"agg_0": 9}]}, {"Qty": "NUMERIC"})
    fields = {"aggregations": [{"function": "COUNT"}], "group_by": ["g"]}
    assert rq.with_leader_share(ctx, {"data": [{"agg_0": 1}]}, fields, None, None) == {
        "data": [{"agg_0": 1}]
    }
    assert rq.with_leader_share(ctx, {"data": [{"agg_0": 1}]}, {"aggregations": []}, None, 5) == {
        "data": [{"agg_0": 1}]
    }
    assert _queries(ctx) == []


# ── empty results say what the data covers ──


def test_an_empty_result_lists_the_observed_range_of_each_filtered_column() -> None:
    ctx = _ctx({"data": [{"agg_0": "2020-01-01", "agg_1": "2024-12-31"}]}, {"When": "DATE"})
    out = rq.with_observed_range(ctx, {"data": []}, ["When"])
    assert out["empty_result"] == ("No rows matched. The data covers, per filtered/date column:")
    assert out["observed_range"] == [
        {"column": "When", "type": "DATE", "min": "2020-01-01", "max": "2024-12-31"}
    ]


def test_at_most_three_columns_are_ranged() -> None:
    types = {name: "DATE" for name in "ABCDE"}
    ctx = _ctx({"data": [{"agg_0": 1, "agg_1": 2}]}, types)
    out = rq.with_observed_range(ctx, {"data": []}, list(types))
    assert [r["column"] for r in out["observed_range"]] == ["A", "B", "C"]
    assert len(_queries(ctx)) == 3


def test_no_range_is_added_when_no_column_has_one() -> None:
    ctx = _ctx({"data": []}, {"When": "DATE", "Name": "BOOLEAN"})
    assert rq.with_observed_range(ctx, {"data": []}, ["When", "Name"]) == {"data": []}
    assert rq.with_observed_range(ctx, {"data": []}, []) == {"data": []}
    assert rq.with_observed_range(ctx, ["x"], ["When"]) == ["x"]


def test_a_text_date_column_in_an_empty_result_is_ranged_from_its_parsed_days() -> None:
    out = rq.with_observed_range(_day_ctx(), {"data": []}, ["Day"])
    (found,) = out["observed_range"]
    assert (found["min"], found["max"]) == ("2026-01-10", "2026-04-10")


def test_a_text_column_that_is_not_dates_has_no_range() -> None:
    ctx = _ctx({"data": [{"group_0": "red"}, {"group_0": "blue"}]}, {"Colour": "TEXT"})
    assert rq.with_observed_range(ctx, {"data": []}, ["Colour"]) == {"data": []}


def test_the_assumptions_a_read_made_are_attached_as_text_dates() -> None:
    ctx = _day_ctx()
    assert rq.with_assumptions(ctx, {"data": []}) == {"data": []}
    ctx.column_days("Day")
    out = rq.with_assumptions(ctx, {"data": []})
    (assumed,) = out["text_dates"]
    assert assumed["column"] == "Day"
    assert assumed["assumed_format"] == ctx.column_days("Day")[0].label
    assert rq.with_assumptions(ctx, ["x"]) == ["x"]


def test_a_text_date_can_be_grouped_by_the_day_of_the_month() -> None:
    # Recorded: group_by [{"column": "Order Date", "part": "day"}] was refused: weekday, month, ...
    levels = rq.text_date_group_levels(
        [{"column": "Order Date", "part": "day"}], {"Order Date": "TEXT"}
    )
    assert levels == {0: "part:day"}

    rows = [
        {"g": "2026-01-10", "n": 2},
        {"g": "2026-02-10", "n": 3},
        {"g": "2026-02-03", "n": 4},
    ]
    days = {row["g"]: date.fromisoformat(row["g"]) for row in rows}
    out = text_dates.rebucket(
        rows, date_key="g", other_keys=[], functions={"n": "SUM"}, days=days, level=levels[0]
    )
    assert out == [{"g": 3, "n": 4}, {"g": 10, "n": 5}]


# ── bucketing a TEXT date in a pivot ──


def test_a_pivot_on_two_text_date_levels_is_refused() -> None:
    with pytest.raises(CliError) as excinfo:
        rq.pivot_with_text_dates(
            _day_ctx(),
            aggregations=[{"function": "COUNT"}],
            group_by=["column_day", "column_qty"],
            levels={0: "MONTH", 1: "YEAR"},
            condition=None,
        )
    assert excinfo.value.message == "Bucket at most one TEXT date column per query."


def test_a_date_column_grouped_by_day_is_regrouped_from_the_backends_iso_values() -> None:
    ctx = _ctx(
        {
            "data": [
                {"group_0": "2026-01-10T00:00:00", "agg_0": 2},
                {"group_0": "2026-01-25T00:00:00", "agg_0": 3},
                {"group_0": "2026-02-02T00:00:00", "agg_0": 4},
            ]
        },
        {"When": "DATE"},
    )
    out = rq.pivot_with_text_dates(
        ctx,
        aggregations=[{"function": "COUNT", "as_name": "n"}],
        group_by=["column_when"],
        levels={0: "MONTH"},
        condition=None,
    )
    assert [(r["group_0"], r["agg_0"]) for r in out["data"]] == [
        ("2026-01-01", 5),
        ("2026-02-01", 4),
    ]
    assert out["row_count"] == 2


def test_a_backend_value_that_is_not_a_date_is_reported() -> None:
    ctx = _ctx({"data": [{"group_0": "soon", "agg_0": 1}]}, {"When": "DATE"})
    with pytest.raises(CliError) as excinfo:
        rq.pivot_with_text_dates(
            ctx,
            aggregations=[{"function": "COUNT"}],
            group_by=["column_when"],
            levels={0: "MONTH"},
            condition=None,
        )
    assert excinfo.value.message == "The backend returned 'soon', which is not a date."


def test_a_grouped_result_at_the_backend_row_cap_is_refused() -> None:
    ctx = _ctx({"data": [{"group_0": "2026-01-01", "agg_0": 1}] * 40000}, {"When": "DATE"})
    with pytest.raises(CliError) as excinfo:
        rq.pivot_with_text_dates(
            ctx,
            aggregations=[{"function": "COUNT"}],
            group_by=["column_when"],
            levels={0: "DAY"},
            condition=None,
        )
    assert excinfo.value.message.startswith("The grouped result hit the 40000-row backend cap")


def test_an_average_per_month_is_the_total_over_the_count_of_its_stored_groups() -> None:
    def answer(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        functions = [a["function"] for a in log[-1][1]["aggregations"]]
        assert functions == ["SUM", "COUNT"]  # AVG is planned as SUM and COUNT
        return {
            "data": [
                {"group_0": "2026-01-10T00:00:00", "agg_0": 30.0, "agg_1": 3},
                {"group_0": "2026-01-20T00:00:00", "agg_0": 10.0, "agg_1": 1},
            ]
        }

    ctx = _ctx(answer, {"When": "DATE", "Qty": "NUMERIC"})
    out = rq.pivot_with_text_dates(
        ctx,
        aggregations=[{"function": "AVG", "column": "column_qty", "as_name": "avg"}],
        group_by=["column_when"],
        levels={0: "MONTH"},
        condition={"c": 1},
    )
    assert out["data"] == [{"group_0": "2026-01-01", "agg_0": 10.0}]  # (30+10)/(3+1)
    assert _queries(ctx)[0]["condition"] == {"c": 1}


def test_a_column_named_twice_in_a_condition_is_listed_once_in_first_seen_order() -> None:
    spec = {
        "and": [
            {"column": "Booked", "operator": ">=", "value": "2026-01-01"},
            {"or": [{"column": "Region", "operator": "=", "value": "N"}]},
            {"not": {"column": "Booked", "operator": "<", "value": "2027-01-01"}},
        ]
    }
    assert rq.condition_columns(spec) == ["Booked", "Region"]
    assert rq.condition_columns("not a spec") == []
