"""Reads that return what the agent fetched next: view list links, view analyze, job wait.

Real CLI argv through the real handlers, service and SDK client; only the HTTP
socket is faked (the suite's established boundary).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]
_VIEWS = r"/projects/180/datasets/9/dataviews$"
_METADATA = [
    {"internal_name": "column_1", "display_name": "order_id", "type": "NUMERIC"},
    {"internal_name": "column_2", "display_name": "region", "type": "TEXT"},
]


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


def _run(args: list[str], tmp_path: Path, payload: dict[str, Any] | None = None) -> Any:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload or {}), encoding="utf-8")
    return make_runner().invoke(
        [*args, "--project", "180", "--input", str(doc), "--output", "json", "--no-input"]
    )


def _data(args: list[str], tmp_path: Path, payload: dict[str, Any] | None = None) -> Any:
    result = _run(args, tmp_path, payload)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"]


def _paths(api: Any) -> list[str]:
    return [urlparse(r.url).path.removeprefix("/api/v2") for r in api.requests]


def test_view_list_names_what_a_view_is_built_from_and_what_reads_it(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    record = {
        "id": 501,
        "name": "Joined",
        "metadata": _METADATA,
        "status": "running",
        "is_dataview_data_in_sync": False,
        "dependencies_info": {
            "dependees": {"501": {}, "7": {}, "6": {}},
            "dependents": {"501": {}, "800": {}},
        },
    }
    api.on("GET", _VIEWS, body={"dataviews": [record]})
    api.on("GET", r"/projects/180/datasets/9$", body={"dataset": {"id": 9, "name": "Sales"}})

    view = _data(["view", "list", "9"], tmp_path)["dataviews"][0]

    assert view["built_from"] == [6, 7]
    assert view["feeds"] == [800]
    assert view["pipeline_status"] == "running"
    assert view["in_sync"] is False


def test_view_list_leaves_out_links_a_plain_view_does_not_have(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    record = {"id": 501, "name": "V", "metadata": _METADATA, "status": "ready"}
    api.on("GET", _VIEWS, body={"dataviews": [record]})
    api.on("GET", r"/projects/180/datasets/9$", body={"dataset": {"id": 9, "name": "Sales"}})

    view = _data(["view", "list", "9"], tmp_path)["dataviews"][0]

    assert not {"built_from", "feeds", "pipeline_status", "in_sync"} & set(view)


def _analysis_routes(api: Any, view_id: int, steps: int) -> None:
    """A view with ``steps`` pipeline tasks and one export, and one finding."""
    base = rf"/projects/180/datasets/9/dataviews/{view_id}"
    api.on("GET", base + "/analysis$", body={"findings": [{"rule": "drop_suspended", "seqs": [2]}]})
    api.on(
        "GET",
        base + "$",
        body={
            "id": view_id,
            "name": f"View {view_id}",
            "row_count": 120,
            "column_count": 2,
            "metadata": _METADATA,
            "pipeline_status": "ready",
        },
    )
    tasks = [{"item_type": "task", "sequence": n + 1} for n in range(steps)]
    api.on("GET", base + "/pipeline/items$", body={"items": [*tasks, {"item_type": "export"}]})


def test_view_analyze_returns_the_view_and_its_step_count_with_the_findings(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    _analysis_routes(api, 7, steps=3)
    api.on("GET", r"/projects/180/datasets/9$", body={"dataset": {"id": 9, "name": "Sales"}})

    data = _data(["view", "analyze", "7", "9"], tmp_path)

    assert data["findings"] == [{"rule": "drop_suspended", "seqs": [2]}]
    assert data["steps"] == 3
    assert data["view"]["name"] == "View 7"
    assert data["view"]["rows"] == 120
    assert data["view"]["dataset_name"] == "Sales"
    assert data["view"]["columns"] == "order_id:numeric, region:text"


def test_view_analyze_takes_several_ids_and_reports_each_failure_beside_the_rest(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    _analysis_routes(api, 7, steps=2)
    _analysis_routes(api, 8, steps=5)
    api.on("GET", r"/dataviews/99/analysis$", status=404, body={"message": "no such view"})
    api.on("GET", r"/projects/180/datasets/9$", body={"dataset": {"id": 9, "name": "Sales"}})

    data = _data(["view", "analyze", "7,99,8", "9"], tmp_path)

    assert data["requested"] == 3
    assert [(a["view_id"], a["steps"]) for a in data["analyses"]] == [(7, 2), (8, 5)]
    assert [e["view_id"] for e in data["errors"]] == [99]
    assert data["errors"][0]["code"]


def test_view_analyze_reads_a_shared_dataset_once(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    _analysis_routes(api, 7, steps=1)
    _analysis_routes(api, 8, steps=1)
    api.on("GET", r"/projects/180/datasets/9$", body={"dataset": {"id": 9, "name": "Sales"}})

    _data(["view", "analyze", "7,8", "9"], tmp_path)

    assert _paths(api).count("/workspaces/4/projects/180/datasets/9") == 1


def test_view_analyze_of_one_missing_view_still_fails_the_command(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    api.on("GET", r"/dataviews/99/analysis$", status=404, body={"message": "no such view"})

    result = _run(["view", "analyze", "99", "9"], tmp_path)

    assert result.exit_code != 0


def test_view_analyze_refuses_a_pasted_list_and_a_non_id(tmp_path: Path) -> None:
    too_many = _run(["view", "analyze", ",".join(str(n) for n in range(1, 14)), "9"], tmp_path)
    not_an_id = _run(["view", "analyze", "7,abc", "9"], tmp_path)

    assert json.loads(too_many.output)["error"]["code"] == "too_many_ids"
    assert json.loads(not_an_id.output)["error"]["code"] == "invalid_argument"
