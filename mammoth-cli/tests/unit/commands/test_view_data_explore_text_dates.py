"""``view data explore`` on a TEXT column of dates, and the rules for which type it reads.

A TEXT column holding dates cannot be bucketed by the backend, so the CLI reads the distinct
stored strings, parses them (the format is stated in the answer) and regroups the counts by
``level`` itself. The expected buckets here are counted from the raw rows below.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.view.explore import (
    _explore_wants_text_dates,
    _require_string_positional_at,
)
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_FIND = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"
_ARGS = ["--project", "180", "--output", "json", "--no-input"]

#: One stored value per order; ISO text is the one text format that cannot be misread.
BOOKED = [
    "2026-01-05",
    "2026-01-05",
    "2026-01-20",
    "2026-02-11",
    "2026-02-11",
    "2026-02-12",
    "2026-04-01",
    "2027-01-03",
]
AMOUNTS = {"2026-01-05": 10.0, "2026-01-20": 5.0, "2026-02-11": 7.0, "2026-04-01": 1.0}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _grouped(call_log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """The backend's grouped answer for ``group_by`` the Booked column: one row per stored value."""
    kwargs = call_log[-1][1]
    assert kwargs["group_by"] == ["column_bk"]
    counts = Counter(BOOKED)
    rows = []
    for value, n in counts.items():
        row: dict[str, Any] = {"group_0": value}
        for index, agg in enumerate(kwargs["aggregations"]):
            if agg["function"] == "COUNT":
                row[f"agg_{index}"] = n
            elif agg["function"] == "SUM":
                row[f"agg_{index}"] = AMOUNTS.get(value, 0.0) * n
        rows.append(row)
    return {"data": rows}


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_GET] = {
        "id": 7,
        "name": "Orders",
        "row_count": len(BOOKED),
        "metadata": [
            {"display_name": "Booked", "internal_name": "column_bk", "type": "TEXT"},
            {"display_name": "Amount", "internal_name": "column_am", "type": "NUMERIC"},
        ],
    }
    fake_service.responses[_FIND] = 9
    fake_service.responses[_AGGREGATE] = _grouped
    return fake_service


def _explore(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    argv = ["view", "data", "explore", "7", "Booked", *_ARGS, "--input", json.dumps(payload)]
    result = make_runner().invoke(argv)
    start = result.output.find("{")
    assert start != -1, result.output
    return result.exit_code, json.loads(result.output[start:])


# ── the regrouped answer ──


def test_text_dates_are_counted_per_month_in_calendar_order(service: FakeMammothService) -> None:
    code, out = _explore({"level": "MONTH"})
    assert code == 0, out
    rows = out["data"]["data"]
    by_month: Counter[str] = Counter(v[:7] + "-01" for v in BOOKED)
    assert [(r["bucket"], r["count"]) for r in rows] == sorted(by_month.items())
    assert [round(r["percentage"], 2) for r in rows] == [
        round(100 * n / len(BOOKED), 2) for _, n in sorted(by_month.items())
    ]


def test_the_format_the_dates_were_read_in_is_stated(service: FakeMammothService) -> None:
    _, out = _explore({"level": "YEAR"})
    (assumed,) = out["data"]["text_dates"]
    assert assumed["column"] == "Booked"
    assert assumed["bucket"].startswith("YEAR")


def test_a_metric_is_summed_into_each_bucket(service: FakeMammothService) -> None:
    _, out = _explore({"level": "MONTH", "metric": {"column": "Amount", "function": "SUM"}})
    rows = out["data"]["data"]
    expected: defaultdict[str, float] = defaultdict(float)
    for value in BOOKED:
        expected[value[:7] + "-01"] += AMOUNTS.get(value, 0.0)
    assert [(r["bucket"], r["SUM_Amount"]) for r in rows] == sorted(expected.items())


def test_a_function_that_cannot_be_recombined_from_the_stored_groups_is_refused(
    service: FakeMammothService,
) -> None:
    code, out = _explore({"level": "MONTH", "metric": {"column": "Amount", "function": "STDDEV"}})
    assert code == 2
    assert out["error"]["message"].startswith(
        "STDDEV cannot be computed per month/year of a TEXT date"
    )


def test_a_level_is_required_to_bucket_a_text_date(service: FakeMammothService) -> None:
    code, out = _explore({"column_type": "DATE"})
    assert code == 2


# ── which type a read honours ──


def test_a_column_type_that_matches_or_is_left_out_changes_nothing() -> None:
    assert _explore_wants_text_dates({"column_type": "numeric"}, "Amount", "NUMERIC") is False
    assert _explore_wants_text_dates({}, "Name", "TEXT") is False
    assert _explore_wants_text_dates({}, "Anything", "") is False


def test_a_level_on_a_text_column_means_its_values_are_dates() -> None:
    assert _explore_wants_text_dates({"level": "MONTH"}, "Booked", "TEXT") is True


def test_date_asked_of_a_text_column_reads_it_as_dates() -> None:
    assert _explore_wants_text_dates({"column_type": "DATE"}, "Booked", "TEXT") is True


@pytest.mark.parametrize(("requested", "stored"), [("NUMERIC", "TEXT"), ("TEXT", "DATE")])
def test_a_read_cannot_retype_a_column(requested: str, stored: str) -> None:
    with pytest.raises(CliError) as excinfo:
        _explore_wants_text_dates({"column_type": requested}, "Booked", stored)
    assert excinfo.value.code == "invalid_arguments"
    assert excinfo.value.exit_status == 2
    assert excinfo.value.message == (
        f"column_type {requested} does not match 'Booked', which is stored as {stored}; "
        "a read cannot re-type a column."
    )
    assert "convert-type" in (excinfo.value.hint or "")


def test_a_level_on_a_boolean_column_is_refused() -> None:
    with pytest.raises(CliError) as excinfo:
        _explore_wants_text_dates({"level": "MONTH"}, "Flag", "BOOLEAN")
    assert excinfo.value.message == (
        "'level' buckets a DATE, NUMERIC or TEXT-date column; 'Flag' is BOOLEAN."
    )


@pytest.mark.parametrize("stored", ["DATE", "NUMERIC"])
def test_a_level_on_a_date_or_number_column_is_the_backends_own_bucketing(stored: str) -> None:
    assert _explore_wants_text_dates({"level": "MONTH"}, "C", stored) is False


# ── positionals ──


def test_the_column_argument_must_be_given_and_not_blank() -> None:
    for extra in ([], ["7"], ["7", "  "]):
        with pytest.raises(CliError) as excinfo:
            _require_string_positional_at(
                Invocation(command_id="view.data.explore", extra_args=extra), 1, "column"
            )
        assert excinfo.value.code == "missing_argument"
        assert excinfo.value.message == "This command requires a column argument."
    got = _require_string_positional_at(
        Invocation(command_id="view.data.explore", extra_args=["7", "Booked"]), 1, "column"
    )
    assert got == "Booked"
