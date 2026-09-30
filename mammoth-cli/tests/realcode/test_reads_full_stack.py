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
    service, api = real_service(project_id=180)
    monkeypatch.setattr(factory, "build_service", lambda *a, **k: service)
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
    assert "(+5 more)" in default["dataviews"][0]["columns"]
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
