"""Full-stack reads: view list all_columns and date coverage on aggregates.

Real CLI argv through the real handlers, service and SDK client; only the HTTP
socket is faked (the suite's established boundary).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]
_VIEWS = r"/projects/180/datasets/9/dataviews$"
_VIEW = r"/projects/180/datasets/9/dataviews/7$"
_QUERY = r"/projects/180/datasets/9/dataviews/7/data/query$"


def _bind(monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory) -> Any:
    """Every build gets a fresh service, as in production (a command closes its own)."""
    first, api = real_service(project_id=180)
    unused = iter([first])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    return api


def _invoke(args: list[str], payload: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    result = make_runner().invoke(
        [*args, "--project", "180", "--input", str(doc), "--output", "json", "--no-input"]
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"]


def test_view_list_all_columns_lists_every_column_with_its_type(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [
        {"internal_name": f"column_{i}", "display_name": f"Col {i}", "type": "NUMERIC"}
        for i in range(9)
    ]
    api.on("GET", _VIEWS, body={"dataviews": [{"id": 501, "name": "V", "metadata": metadata}]})
    api.on("GET", r"/projects/180/datasets/9$", body={"dataset": {"id": 9, "name": "Sales"}})

    default = _invoke(["view", "list", "9"], {}, tmp_path)
    # One dataset's views list every column: it saves a `view get` before a read.
    assert "more)" not in default["dataviews"][0]["columns"]
    full = _invoke(["view", "list", "9"], {"all_columns": True}, tmp_path)
    columns = full["dataviews"][0]["columns"]
    assert "more)" not in columns
    assert columns.startswith("Col 0:numeric") and columns.endswith("Col 8:numeric")


def test_aggregate_over_a_date_column_states_the_dates_the_view_covers(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [{"internal_name": "column_3", "display_name": "inspection_date", "type": "DATE"}]
    api.on("GET", _VIEW, body={"id": 7, "metadata": metadata})

    def answer(request: Any) -> tuple[int, Any]:
        if "GROUP_BY" in request.json_body["param"]["PIVOT"]:
            return 200, {"data": [{"group_0": "2024-01-01", "agg_0": 1500}]}
        return 200, {"data": [{"agg_0": "2019-02-03", "agg_1": "2024-11-30"}]}

    api.on("POST", _QUERY, handler=answer)
    data = _invoke(
        ["view", "data", "aggregate", "7", "9"],
        {
            "group_by": [{"column": "inspection_date", "truncate": "MONTH"}],
            "aggregations": [{"function": "COUNT", "as_name": "inspections"}],
        },
        tmp_path,
    )
    assert data["coverage"] == {
        "column": "inspection_date",
        "min": "2019-02-03",
        "max": "2024-11-30",
    }
    assert len([r for r in api.requests if r.method == "POST"]) == 2


def test_a_zero_metric_under_a_date_condition_reports_the_observed_range(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [
        {"internal_name": "column_3", "display_name": "inspection_date", "type": "DATE"},
        {"internal_name": "column_4", "display_name": "Spend", "type": "NUMERIC"},
    ]
    api.on("GET", _VIEW, body={"id": 7, "metadata": metadata})

    def answer(request: Any) -> tuple[int, Any]:
        if "METRIC" in request.json_body["param"]:
            return 200, {"data": [{"metric": 0}]}
        return 200, {"data": [{"agg_0": "2019-02-03", "agg_1": "2024-11-30"}]}

    api.on("POST", _QUERY, handler=answer)
    data = _invoke(
        ["view", "data", "aggregate", "7", "9"],
        {
            "metric": {"column": "Spend", "function": "SUM"},
            "condition": {"column": "inspection_date", "operator": "GTE", "value": "2030-01-01"},
        },
        tmp_path,
    )
    assert "may mean no rows matched" in data["empty_result"]
    assert data["observed_range"][0]["max"] == "2024-11-30"


_WEEKDAY_INPUT: dict[str, Any] = {
    "group_by": [{"column": "Order Date", "part": "weekday"}],
    "aggregations": [{"column": "Sales", "function": "SUM", "as_name": "Total"}],
}


def _invoke_failing(args: list[str], payload: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    result = make_runner().invoke(
        [*args, "--project", "180", "--input", str(doc), "--output", "json", "--no-input"]
    )
    assert result.exit_code != 0, result.output
    return json.loads(result.output)["error"]


def test_aggregate_by_weekday_of_a_date_column_names_and_orders_the_days(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    isolated_cli_config: Path,
    tmp_path: Path,
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [
        {"internal_name": "column_3", "display_name": "Order Date", "type": "DATE"},
        {"internal_name": "column_4", "display_name": "Sales", "type": "NUMERIC"},
    ]
    api.on("GET", _VIEW, body={"id": 7, "metadata": metadata})
    days = [  # two Saturdays, a Tuesday, a Wednesday
        {"group_0": "2024-01-13", "agg_0": 300.5},
        {"group_0": "2024-01-06", "agg_0": 200.25},
        {"group_0": "2024-01-09", "agg_0": 400.0},
        {"group_0": "2024-01-10", "agg_0": 50.0},
    ]
    api.on("POST", _QUERY, body={"data": days})

    data = _invoke(["view", "data", "aggregate", "7", "9"], _WEEKDAY_INPUT, tmp_path)

    assert data["data"] == [
        {"Order Date": "Tuesday", "Total": 400.0},
        {"Order Date": "Wednesday", "Total": 50.0},
        {"Order Date": "Saturday", "Total": 500.75},
    ]
    pivots = [r.json_body["param"]["PIVOT"] for r in api.requests if r.method == "POST"]
    grouped = next(p for p in pivots if "GROUP_BY" in p)
    assert json.dumps(grouped["GROUP_BY"]).count("DAY") == 1  # the backend groups by day only


def test_aggregate_by_weekday_ranks_the_named_days_with_order_by_and_top(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    isolated_cli_config: Path,
    tmp_path: Path,
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [
        {"internal_name": "column_3", "display_name": "Order Date", "type": "DATE"},
        {"internal_name": "column_4", "display_name": "Sales", "type": "NUMERIC"},
    ]
    api.on("GET", _VIEW, body={"id": 7, "metadata": metadata})
    api.on(
        "POST",
        _QUERY,
        body={
            "data": [
                {"group_0": "2024-01-13", "agg_0": 300.5},
                {"group_0": "2024-01-09", "agg_0": 400.0},
                {"group_0": "2024-01-06", "agg_0": 200.25},
            ]
        },
    )

    data = _invoke(
        ["view", "data", "aggregate", "7", "9"],
        {**_WEEKDAY_INPUT, "order_by": ["Total desc"], "top": 1},
        tmp_path,
    )

    assert data["data"] == [{"Order Date": "Saturday", "Total": 500.75}]


def test_aggregate_by_month_of_a_text_date_column_states_the_assumed_format(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    isolated_cli_config: Path,
    tmp_path: Path,
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [
        {"internal_name": "column_3", "display_name": "Order Date", "type": "TEXT"},
        {"internal_name": "column_4", "display_name": "Sales", "type": "NUMERIC"},
    ]
    api.on("GET", _VIEW, body={"id": 7, "metadata": metadata})

    rows = [
        {"group_0": "13/03/2024", "agg_0": 10.0},
        {"group_0": "20/03/2024", "agg_0": 5.0},
        {"group_0": "02/01/2023", "agg_0": 7.0},
    ]
    api.on("POST", _QUERY, body={"data": rows})
    payload = {**_WEEKDAY_INPUT, "group_by": [{"column": "Order Date", "part": "month"}]}

    data = _invoke(["view", "data", "aggregate", "7", "9"], payload, tmp_path)

    assert data["data"] == [
        {"Order Date": "January", "Total": 7.0},
        {"Order Date": "March", "Total": 15.0},
    ]
    assumed = data["text_dates"][0]
    assert assumed["column"] == "Order Date" and assumed["assumed_format"] == "D/M/YYYY"


def test_a_date_part_on_a_numeric_column_is_refused_with_the_reason(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    isolated_cli_config: Path,
    tmp_path: Path,
) -> None:
    api = _bind(monkeypatch, real_service)
    metadata = [{"internal_name": "column_4", "display_name": "Sales", "type": "NUMERIC"}]
    api.on("GET", _VIEW, body={"id": 7, "metadata": metadata})
    payload = {**_WEEKDAY_INPUT, "group_by": [{"column": "Sales", "part": "weekday"}]}

    error = _invoke_failing(["view", "data", "aggregate", "7", "9"], payload, tmp_path)

    assert "'Sales' is NUMERIC" in error["message"]
    assert not [r for r in api.requests if r.method == "POST"]
