"""Live checks that ``view data explore`` shares and ranks by a metric, reports the exact
range, and writes CSV, each against an independent ``view data aggregate`` answer.

Runs the real CLI in-process against a real tenant (no doubles). The module uploads
its own sales CSV into a scratch project and deletes the project at the end::

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_explore_coverage.py -m live -v
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live

_REGION_BY_REVENUE = {
    "metric": {"column": "Revenue", "function": "SUM", "as_name": "revenue"},
}


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def _explore(cli: LiveCli, data: SalesData, column: str, document: dict[str, Any]) -> Any:
    result, _ = cli.ok(
        "view", "data", "explore", str(data.view), column, *_input(document), project=data.project
    )
    return result


def _aggregate(cli: LiveCli, data: SalesData, document: dict[str, Any]) -> dict[str, Any]:
    result, _ = cli.ok(
        "view", "data", "aggregate", str(data.view), *_input(document), project=data.project
    )
    row: dict[str, Any] = result["data"][0]
    return row


def test_percentage_of_metric_is_each_buckets_share_of_the_metric_total(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """Shares follow Revenue, sum to 100, and the total is the whole-view SUM."""
    result = _explore(
        live_cli, sales_data, "Region", {**_REGION_BY_REVENUE, "percentage_of": "metric"}
    )
    rows = result["data"]
    total = sum(row["revenue"] for row in rows)
    whole = _aggregate(
        live_cli,
        sales_data,
        {"aggregations": [{"function": "SUM", "column": "Revenue", "as_name": "total"}]},
    )["total"]

    assert total == pytest.approx(whole, abs=0.05 * len(rows))
    for row in rows:
        assert row["percentage"] == pytest.approx(row["revenue"] / total * 100, abs=0.05)
    assert sum(row["percentage"] for row in rows) == pytest.approx(100, abs=0.1 * len(rows))


def test_percentage_of_count_stays_the_default_share_of_rows(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """Without percentage_of, a metric does not change what percentage means."""
    rows = _explore(live_cli, sales_data, "Region", _REGION_BY_REVENUE)["data"]
    total = sum(row["count"] for row in rows)
    for row in rows:
        assert row["percentage"] == pytest.approx(row["count"] / total * 100, abs=0.05)


@pytest.mark.parametrize(("order", "descending"), [("metric_desc", True), ("metric_asc", False)])
def test_sort_by_metric_orders_buckets_by_the_metric_with_blanks_last(
    live_cli: LiveCli, sales_data: SalesData, order: str, descending: bool
) -> None:
    rows = _explore(live_cli, sales_data, "Region", {**_REGION_BY_REVENUE, "sort": order})["data"]
    present = [row["revenue"] for row in rows if row["bucket"] is not None]
    blanks = [i for i, row in enumerate(rows) if row["bucket"] is None]

    assert len(present) >= 2
    assert present == sorted(present, reverse=descending)
    assert all(i >= len(present) for i in blanks)


@pytest.mark.parametrize("order", ["metric_desc", "metric_asc"])
def test_sort_by_metric_without_a_metric_is_refused(
    live_cli: LiveCli, sales_data: SalesData, order: str
) -> None:
    error = live_cli.err(
        *("view", "data", "explore", str(sales_data.view), "Region", *_input({"sort": order})),
        project=sales_data.project,
    )
    assert error["code"] == "invalid_arguments", error


def test_range_reports_the_exact_min_and_max_the_aggregate_finds(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    result = _explore(live_cli, sales_data, "Units", {"range": True})
    expected = _aggregate(
        live_cli,
        sales_data,
        {
            "aggregations": [
                {"function": "MIN", "column": "Units", "as_name": "lo"},
                {"function": "MAX", "column": "Units", "as_name": "hi"},
            ]
        },
    )

    assert result["range"]["column"] == "Units"
    assert result["range"]["type"] == "NUMERIC"
    assert (result["range"]["min"], result["range"]["max"]) == (expected["lo"], expected["hi"])


def test_range_honours_the_explore_condition(live_cli: LiveCli, sales_data: SalesData) -> None:
    """Under Units >= 5 the minimum is at least 5, and equals the aggregate's under it."""
    condition = {"column": "Units", "operator": ">=", "value": 5}
    result = _explore(live_cli, sales_data, "Units", {"range": True, "condition": condition})
    expected = _aggregate(
        live_cli,
        sales_data,
        {
            "aggregations": [{"function": "MIN", "column": "Units", "as_name": "lo"}],
            "condition": condition,
        },
    )

    assert result["range"]["min"] >= 5
    assert result["range"]["min"] == expected["lo"]


def test_range_on_a_text_column_is_refused(live_cli: LiveCli, sales_data: SalesData) -> None:
    error = live_cli.err(
        *("view", "data", "explore", str(sales_data.view), "Region", *_input({"range": True})),
        project=sales_data.project,
    )
    assert error["code"] == "invalid_arguments", error


def test_csv_output_is_the_explore_buckets_as_rows(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """`-o csv` prints one line per bucket, the same values `-o json` returns."""
    document = {**_REGION_BY_REVENUE, "sort": "metric_desc"}
    expected = _explore(live_cli, sales_data, "Region", document)["data"]
    argv = ["view", "data", "explore", str(sales_data.view), "Region", *_input(document)]
    argv += ["-o", "csv", "--no-input", "--project", str(sales_data.project)]
    outcome = make_runner().invoke(argv)
    rows = list(csv.DictReader(io.StringIO(outcome.output)))

    assert outcome.exit_code == 0, outcome.output
    assert [row["bucket"] for row in rows] == [str(r["bucket"] or "") for r in expected]
    assert [float(row["revenue"]) for row in rows] == [r["revenue"] for r in expected]


def test_csv_output_of_an_explore_with_no_buckets_fails_loud(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """A condition nothing satisfies leaves no rows: the command exits non-zero, no empty file."""
    nothing = {"condition": {"column": "Units", "operator": ">", "value": 1000000}}
    argv = ["view", "data", "explore", str(sales_data.view), "Region", *_input(nothing)]
    argv += ["-o", "csv", "--no-input", "--project", str(sales_data.project)]
    outcome = make_runner().invoke(argv)

    assert outcome.exit_code != 0, outcome.output
    assert not outcome.output.lstrip().startswith("bucket")
