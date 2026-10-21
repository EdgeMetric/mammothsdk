"""The impact a ``--dry-run`` transform predicts, counted by read-only aggregates.

The documented contract (module docstring): a count of zero means the step is a no-op;
counts that are only an upper bound say so (``exact: False``, ``rows_matching``,
``blank_cells``); filters measure the *removed* rows (REMOVE removes the matches, SHOW keeps
them); every read goes out as an aggregate against the view on internal column names.
The service answers from a table we hold here, so counts come out of the logic under test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import write_impact as wi
from mammoth_cli.services.read_queries import AGGREGATE_SYMBOL
from mammoth_cli.services.testing import FakeMammothService

_META = [
    {"display_name": "Region", "internal_name": "column_r", "type": "TEXT"},
    {"display_name": "Amount", "internal_name": "column_a", "type": "NUMERIC"},
    {"display_name": "Company", "internal_name": "column_c", "type": "TEXT"},
]


def _read(
    answers: Any,
    *,
    row_count: int = 10,
    document: dict[str, Any] | None = None,
    dry_run: bool = False,
    metadata: list[dict[str, Any]] | None = None,
) -> tuple[wi.ImpactRead, FakeMammothService]:
    service = FakeMammothService()
    service.responses[AGGREGATE_SYMBOL] = (
        answers if callable(answers) or isinstance(answers, Exception) else lambda _log: answers
    )
    info = {"row_count": row_count, "metadata": _META if metadata is None else metadata}
    read = wi.ImpactRead(service, 9, 7, 180, info, document or {}, dry_run)
    return read, service


def _sent(service: FakeMammothService) -> list[dict[str, Any]]:
    return [kwargs for symbol, kwargs in service.call_log if symbol == AGGREGATE_SYMBOL]


def _groups(**counts: int) -> dict[str, Any]:
    return {"STATUS": "READY", "data": [{"agg_0": n, "group_0": v} for v, n in counts.items()]}


# ── the error shapes ──


def test_no_op_error_is_a_usage_error_naming_the_view_and_the_standing_option() -> None:
    error = wi.no_op_error("nothing to do", view_id=7)
    assert (error.code, error.exit_status, error.details) == ("no_op", 2, {"view_id": 7})
    assert error.hint is not None and error.hint.endswith(wi.STANDING_HINT)
    assert "--standing" in wi.STANDING_HINT


def test_empties_view_error_points_to_allow_empty_only_after_asking_the_user() -> None:
    error = wi.empties_view_error("would empty", view_id=7)
    assert (error.code, error.exit_status, error.details) == ("empties_view", 2, {"view_id": 7})
    assert error.hint is not None and "--allow-empty" in error.hint


# ── ImpactRead.count ──


def test_count_without_a_condition_aggregates_the_whole_view() -> None:
    read, service = _read({"data": [{"agg_0": 4}]})
    assert read.count() == 4
    (sent,) = _sent(service)
    assert sent["aggregations"] == [{"function": "COUNT", "as_name": "rows"}]
    assert sent["condition"] is None
    assert (sent["dataset_id"], sent["dataview_id"], sent["project_id"]) == (9, 7, 180)


def test_count_with_a_condition_builds_it_on_internal_column_names() -> None:
    from mammoth_cli.services.conditions import compile_condition

    read, service = _read({"data": [{"agg_0": 2}]})
    read.count(compile_condition({"column": "Amount", "operator": ">", "value": 5}))
    (sent,) = _sent(service)
    assert sent["condition"] == {"column_a": {"GT": {"VALUE": 5}}}


def test_an_answered_count_with_no_row_is_zero_only_when_the_job_is_ready() -> None:
    read, _ = _read({"STATUS": "READY", "data": []})
    assert read.count() == 0

    unfinished, _ = _read({"STATUS": "PENDING", "data": []})
    with pytest.raises(CliError) as excinfo:
        unfinished.count()
    assert excinfo.value.code == "invalid_arguments"
    assert excinfo.value.message == "Could not count the impact: the count query returned no row."
    assert excinfo.value.exit_status == 2


def test_a_non_mapping_aggregate_answer_is_treated_as_no_row() -> None:
    read, _ = _read(["not", "a", "mapping"])
    with pytest.raises(CliError):
        read.count()


# ── discard-duplicates ──


def test_duplicates_removed_is_the_surplus_of_every_group_over_one() -> None:
    read, service = _read(_groups(a=3, b=2, c=1), row_count=6)
    measured = wi.measure_duplicates(read, {})
    assert measured.changes == 3  # (3-1) + (2-1) + 0
    assert measured.report == {
        "rows_removed": 3,
        "row_count": 6,
        "rows_after": 3,
        "exact": True,
    }
    (sent,) = _sent(service)
    assert sent["group_by"] == ["column_r", "column_a", "column_c"]
    assert sent["sort"] == [["agg_0", "DESC"]]
    assert sent["limit"] == wi.MAX_DUPLICATE_GROUPS


def test_ignored_columns_are_left_out_of_the_comparison_and_named_in_the_no_op() -> None:
    read, service = _read(_groups(a=1, b=1), row_count=2)
    measured = wi.measure_duplicates(read, {"ignore_columns": ["Amount"]})
    assert _sent(service)[0]["group_by"] == ["column_r", "column_c"]
    assert measured.changes == 0
    assert measured.no_op_message == (
        "View 7 has no exact duplicate rows (2 of 2 checked, ignoring Amount); nothing to change."
    )


def test_a_full_page_of_duplicate_groups_makes_the_count_a_floor() -> None:
    rows = [{"agg_0": 2, "group_0": str(i)} for i in range(wi.MAX_DUPLICATE_GROUPS)]
    read, _ = _read({"data": rows}, row_count=5000)
    measured = wi.measure_duplicates(read, {})
    assert measured.changes == wi.MAX_DUPLICATE_GROUPS
    assert measured.report["exact"] is False


def test_a_full_page_that_ends_in_singletons_is_still_exact() -> None:
    rows = [{"agg_0": 2, "group_0": "x"}] + [
        {"agg_0": 1, "group_0": str(i)} for i in range(wi.MAX_DUPLICATE_GROUPS - 1)
    ]
    read, _ = _read({"data": rows}, row_count=5000)
    assert wi.measure_duplicates(read, {}).report["exact"] is True


def test_duplicates_refuse_to_guess_when_the_view_has_no_columns() -> None:
    read, service = _read({"data": []}, metadata=[])
    with pytest.raises(CliError) as excinfo:
        wi.measure_duplicates(read, {})
    assert excinfo.value.message == (
        "Could not count the impact: the view has no columns to compare."
    )
    assert _sent(service) == []


def test_duplicates_refuse_when_a_view_with_rows_returns_no_groups() -> None:
    read, _ = _read({"data": []}, row_count=3)
    with pytest.raises(CliError) as excinfo:
        wi.measure_duplicates(read, {})
    assert "no groups for a view with rows" in excinfo.value.message


def test_duplicates_of_an_empty_view_are_zero() -> None:
    read, _ = _read({"data": []}, row_count=0)
    assert wi.measure_duplicates(read, {}).changes == 0


# ── filter ──

_REGION_COUNTS = {"North": 3, "South": 2}


def _filter_service(matching: int) -> Any:
    """A table of 10 rows: a count query gets ``matching``; the value table gets the groups."""

    def answer(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        kwargs = log[-1][1]
        if kwargs.get("group_by"):
            return _groups(**_REGION_COUNTS)
        return {"STATUS": "READY", "data": [{"agg_0": matching}] if matching else []}

    return answer


def test_a_show_filter_removes_the_rows_that_do_not_match() -> None:
    read, _ = _read(
        _filter_service(4),
        document={"condition": {"column": "Amount", "operator": ">", "value": 5}},
    )
    measured = wi.measure_filter(read, {})
    assert measured.changes == 6
    assert measured.report == {"rows_removed": 6, "row_count": 10, "rows_after": 4, "exact": True}
    assert measured.empties_message is None


def test_a_remove_filter_removes_the_rows_that_match() -> None:
    read, _ = _read(
        _filter_service(4),
        document={
            "filter_type": "remove",
            "condition": {"column": "Amount", "operator": ">", "value": 5},
        },
    )
    measured = wi.measure_filter(read, {})
    assert measured.changes == 4
    assert measured.report["rows_after"] == 6


def test_a_show_filter_matching_every_row_is_a_no_op() -> None:
    read, _ = _read(
        _filter_service(10),
        document={"condition": {"column": "Amount", "operator": ">", "value": 0}},
    )
    measured = wi.measure_filter(read, {})
    assert measured.changes == 0
    assert measured.no_op_message == (
        "Every row of view 7 matches the condition (10 of 10), so the filter keeps all of them; "
        "nothing to change."
    )


def test_a_keep_filter_matching_nothing_would_empty_the_view_and_names_the_values_held() -> None:
    read, service = _read(
        _filter_service(0),
        document={"condition": {"column": "Region", "operator": "=", "value": "East"}},
    )
    measured = wi.measure_filter(read, {})
    assert measured.changes == 10  # every row would go
    assert measured.report["no_row_matches"] == {
        "column": "Region",
        "values": {"North": 3, "South": 2},
    }
    assert measured.empties_message == (
        "No row of view 7 matches the condition (0 of 10), so keeping only matching rows would "
        "leave the view empty. Region holds: North (3), South (2)."
    )
    held_query = _sent(service)[-1]
    assert held_query["group_by"] == ["column_r"]
    assert held_query["limit"] == 20


def test_a_remove_filter_matching_nothing_is_a_no_op_that_lists_the_values_held() -> None:
    read, _ = _read(
        _filter_service(0),
        document={
            "filter_type": "REMOVE",
            "condition": {"column": "Region", "operator": "=", "value": "East"},
        },
    )
    measured = wi.measure_filter(read, {})
    assert measured.changes == 0
    assert measured.empties_message is None
    assert measured.no_op_message == (
        "No row of view 7 matches the condition (0 of 10), so removing matching rows changes "
        "nothing; nothing to change. Region holds: North (3), South (2)."
    )


def test_a_multi_column_condition_that_matches_nothing_lists_no_values() -> None:
    read, _ = _read(
        _filter_service(0),
        document={
            "condition": {
                "and": [
                    {"column": "Region", "operator": "=", "value": "East"},
                    {"column": "Amount", "operator": ">", "value": 1},
                ]
            }
        },
    )
    measured = wi.measure_filter(read, {})
    assert "no_row_matches" not in measured.report
    assert measured.empties_message is not None
    assert measured.empties_message.endswith("leave the view empty.")


def test_a_keep_filter_on_an_empty_view_does_not_claim_to_empty_it() -> None:
    read, _ = _read(
        _filter_service(0),
        row_count=0,
        document={"condition": {"column": "Amount", "operator": ">", "value": 1}},
    )
    assert wi.measure_filter(read, {}).empties_message is None


# ── fill-missing ──


def test_fill_missing_counts_blank_cells_of_the_column_as_an_upper_bound() -> None:
    read, service = _read({"data": [{"agg_0": 3}]}, row_count=10)
    measured = wi.measure_fill_missing(read, {"column": "Amount"})
    assert measured.changes == 3
    assert measured.report == {"blank_cells": 3, "row_count": 10, "exact": False}
    assert _sent(service)[0]["condition"] == {"column_a": {"IS_EMPTY": True}}


def test_fill_missing_with_no_blanks_is_a_no_op_naming_the_column() -> None:
    read, _ = _read({"STATUS": "READY", "data": []})
    measured = wi.measure_fill_missing(read, {"column": "Amount"})
    assert measured.changes == 0
    assert measured.no_op_message == (
        "Column Amount of view 7 has no blank values (0 of 10 rows); nothing to fill, "
        "nothing to change."
    )


# ── replace / bulk replace ──


def test_replace_counts_rows_containing_the_text_case_insensitively_by_default() -> None:
    read, service = _read({"data": [{"agg_0": 4}]})
    measured = wi.measure_replace(read, {"columns": ["Region", "Company"], "find": "n/a"})
    assert measured.changes == 4
    assert measured.report == {"rows_matching": 4, "row_count": 10, "exact": False}
    assert _sent(service)[0]["condition"] == {
        "OR": [
            {"column_r": {"ICONTAINS": {"VALUE": "n/a"}}},
            {"column_c": {"ICONTAINS": {"VALUE": "n/a"}}},
        ]
    }


def test_match_case_makes_the_search_case_sensitive() -> None:
    read, service = _read({"data": [{"agg_0": 1}]})
    wi.measure_replace(read, {"columns": ["Region"], "find": "N/A", "match_case": True})
    # One search value collapses the OR; the case-sensitive operator takes a list of values.
    assert _sent(service)[0]["condition"] == {"column_r": {"CONTAINS": {"VALUE": ["N/A"]}}}


def test_a_replace_that_finds_nothing_is_a_no_op_that_quotes_the_search() -> None:
    read, _ = _read({"STATUS": "READY", "data": []})
    measured = wi.measure_replace(read, {"columns": ["Region"], "find": "zzz"})
    assert measured.changes == 0
    assert measured.no_op_message == (
        "No row of view 7 holds 'zzz' in Region (0 of 10 rows); nothing to replace, "
        "nothing to change."
    )


def test_a_scope_condition_narrows_the_count() -> None:
    read, service = _read({"data": [{"agg_0": 1}]})
    wi.measure_replace(
        read,
        {
            "columns": ["Region"],
            "find": "x",
            "condition": {"column": "Amount", "operator": ">", "value": 1},
        },
    )
    assert _sent(service)[0]["condition"] == {
        "AND": [
            {"column_r": {"ICONTAINS": {"VALUE": "x"}}},
            {"column_a": {"GT": {"VALUE": 1}}},
        ]
    }


_COMPANY_VALUES = {"Acme Inc": 4, "ACME INC": 2, "acme inc": 1, "Beta Co": 3, "BETA CO": 1}


def _variant_service(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    if log[-1][1].get("group_by"):
        return _groups(**_COMPANY_VALUES)
    return {"data": [{"agg_0": 3}]}


def test_a_dry_run_replace_reports_the_spelling_variants_it_leaves_behind() -> None:
    """Rewriting ``ACME INC`` -> ``Acme Inc`` (any case) merges the Acme spellings; Beta stays."""
    read, _ = _read(_variant_service, dry_run=True)
    measured = wi.measure_replace(
        read, {"columns": ["Company"], "find": "ACME INC", "replace": "Acme Inc"}
    )
    assert measured.report["variants_left"] == {
        "Company": {
            "groups_left": 1,
            "likely_groups_left": 0,
            "examples": [["Beta Co", "BETA CO"]],
        }
    }


def test_variants_left_is_only_read_on_a_dry_run_and_never_for_a_scoped_replace() -> None:
    document = {"columns": ["Company"], "find": "ACME INC", "replace": "Acme Inc"}
    live, live_service = _read(_variant_service, dry_run=False)
    assert "variants_left" not in wi.measure_replace(live, document).report
    assert all(not kwargs.get("group_by") for kwargs in _sent(live_service))

    scoped, _ = _read(_variant_service, dry_run=True)
    scoped_report = wi.measure_replace(
        scoped, {**document, "condition": {"column": "Amount", "operator": ">", "value": 1}}
    ).report
    assert "variants_left" not in scoped_report


def test_a_replace_that_merges_every_variant_says_none_remain() -> None:
    values = {"Acme Inc": 4, "ACME INC": 2}

    def answer(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        return _groups(**values) if log[-1][1].get("group_by") else {"data": [{"agg_0": 2}]}

    read, _ = _read(answer, dry_run=True)
    report = wi.measure_replace(
        read, {"columns": ["Company"], "find": "ACME INC", "replace": "Acme Inc"}
    ).report
    assert report["variants_left"] == "none: no spelling-variant group remains in these columns"


def test_variants_are_only_compared_for_text_columns_and_a_failed_read_is_reported_not_raised() -> (
    None
):
    def answer(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        if log[-1][1].get("group_by"):
            raise CliError(code="api_error", message="backend down " + "x" * 200, exit_status=1)
        return {"data": [{"agg_0": 2}]}

    read, _ = _read(answer, dry_run=True)
    report = wi.measure_replace(
        read, {"columns": ["Amount", "Company"], "find": "1", "replace": "2"}
    ).report
    # Amount is NUMERIC: never read. Company's failed read is named, truncated to 120 chars.
    assert list(report["variants_left"]) == ["Company"]
    assert report["variants_left"]["Company"]["checked"] is False
    assert len(report["variants_left"]["Company"]["reason"]) == 120


def test_too_many_distinct_values_are_not_compared() -> None:
    from mammoth_cli.services import data_profile

    too_many = [
        {"agg_0": 1, "group_0": f"v{i}"} for i in range(data_profile.MAX_LISTED_DISTINCT + 2)
    ]

    def answer(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        return {"data": too_many} if log[-1][1].get("group_by") else {"data": [{"agg_0": 1}]}

    read, _ = _read(answer, dry_run=True)
    report = wi.measure_replace(read, {"columns": ["Company"], "find": "a", "replace": "b"}).report
    assert report["variants_left"] == {
        "Company": {"checked": False, "reason": "too many distinct values to compare"}
    }


def test_a_replacement_is_applied_per_pair_in_order_and_only_to_whole_cells_when_asked() -> None:
    rewrite = wi._rewriter([("a.b", "X"), ("X", "Y")], match_case=True, whole=False)
    assert rewrite("a.b-a.b") == "Y-Y"  # the dot is literal, not a wildcard
    assert rewrite("aXb") == "aYb"
    assert wi._rewriter([("n/a", "")], False, True)("N/A") == ""
    assert wi._rewriter([("n/a", "")], False, True)("N/A!") == "N/A!"
    assert wi._rewriter([("n/a", "")], True, False)("N/A") == "N/A"


def test_bulk_replace_counts_rows_holding_any_search_value() -> None:
    read, service = _read({"data": [{"agg_0": 5}]})
    measured = wi.measure_bulk_replace(
        read,
        {
            "columns": ["Region"],
            "mapping": [{"search": ["n", "s"], "replace": "x"}, {"search": ["e"], "replace": "y"}],
        },
    )
    assert measured.changes == 5
    # bulk replace defaults to case-sensitive, unlike replace
    assert _sent(service)[0]["condition"] == {
        "OR": [
            {"column_r": {"CONTAINS": {"VALUE": ["n"]}}},
            {"column_r": {"CONTAINS": {"VALUE": ["s"]}}},
            {"column_r": {"CONTAINS": {"VALUE": ["e"]}}},
        ]
    }


def test_bulk_replace_accepts_sdk_style_entries_and_match_case_false() -> None:
    @dataclass
    class Entry:
        search: list[str]
        replace: str

    read, service = _read({"data": [{"agg_0": 1}]})
    wi.measure_bulk_replace(
        read, {"columns": ["Region"], "mapping": [Entry(["n"], "x")], "match_case": False}
    )
    assert _sent(service)[0]["condition"] == {"column_r": {"ICONTAINS": {"VALUE": "n"}}}


def test_bulk_replace_variant_check_honours_match_words() -> None:
    values = {"Bar Co": 3, "BAR Co": 1}

    def answer(log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        return _groups(**values) if log[-1][1].get("group_by") else {"data": [{"agg_0": 1}]}

    read, _ = _read(answer, dry_run=True)
    document = {
        "columns": ["Company"],
        "mapping": [{"search": ["bar"], "replace": "Bar"}],
        "match_case": False,
    }
    # Whole-cell matching: "bar" is not a whole cell, so the two spellings stay a group.
    whole = wi.measure_bulk_replace(read, {**document, "match_words": True}).report
    assert whole["variants_left"]["Company"]["groups_left"] == 1
    assert whole["variants_left"]["Company"]["examples"] == [["Bar Co", "BAR Co"]]
    # Substring matching rewrites both to "Bar Co": the group is gone.
    part = wi.measure_bulk_replace(read, document).report
    assert part["variants_left"] == "none: no spelling-variant group remains in these columns"
