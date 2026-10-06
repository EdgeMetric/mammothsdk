"""``job wait`` returns the state of what the job acted on, so no read follows it.

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


def _data(args: list[str], tmp_path: Path) -> Any:
    doc = tmp_path / "in.json"
    doc.write_text("{}", encoding="utf-8")
    result = make_runner().invoke(
        [*args, "--project", "180", "--input", str(doc), "--output", "json", "--no-input"]
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"]


def _job(api: Any, operation: str, path: str, response: dict[str, Any]) -> None:
    body = {"id": 5, "status": "success", "operation": operation, "path": path}
    api.on("GET", r"/jobs/5$", body={**body, "response": response})


def test_job_wait_after_a_view_run_returns_the_views_rows_and_state(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    path = "/workspaces/4/projects/180/datasets/9/dataviews/7/pipeline/rerun"
    _job(api, "pipeline_rerun", path, {"dataview_id": 7})
    api.on(
        "GET",
        r"/projects/180/datasets/9/dataviews/7$",
        body={
            "id": 7,
            "name": "Joined",
            "row_count": 147,
            "column_count": 2,
            "metadata": _METADATA,
            "pipeline_status": "ready",
            "is_pipeline_running": False,
        },
    )

    data = _data(["job", "wait", "5"], tmp_path)

    assert data["status"] == "success"
    assert data["outcome"] == {
        "kind": "view",
        "view_id": 7,
        "dataset_id": 9,
        "status": "ready",
        "name": "Joined",
        "rows": 147,
        "cols": 2,
        "columns": "order_id:numeric, region:text",
        "pipeline_running": False,
    }


def test_job_wait_after_a_view_create_finds_the_new_view_from_the_response(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    _job(api, "create_dataview", "/workspaces/4/projects/180/datasets/9/dataviews", {"id": 31})
    api.on(
        "GET",
        r"/projects/180/datasets/9/dataviews/31$",
        body={"id": 31, "name": "New", "row_count": 4, "status": "ready"},
    )

    data = _data(["job", "wait", "5"], tmp_path)

    assert (data["outcome"]["view_id"], data["outcome"]["rows"]) == (31, 4)


def test_job_wait_after_a_project_copy_returns_the_per_view_runs_without_reading(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    response = {
        "project_id": 55,
        "dataset_map": {"9": 90, "10": 100},
        "view_map": {"7": 70, "8": 80, "9": 90},
        "skipped": [{"kind": "reference"}],
        "run_views": [70, 80, 90],
        "runs": {
            "70": {"dataview_id": 70, "error": None},
            "80": {"dataview_id": 80, "error": "join column missing"},
        },
    }
    _job(api, "copy_project", "/workspaces/4/projects/180/copy", response)

    data = _data(["job", "wait", "5"], tmp_path)

    assert data["outcome"] == {
        "kind": "project_copy",
        "project_id": 55,
        "datasets": 2,
        "views": 3,
        "skipped": 1,
        "runs": {
            "ok": 1,
            "failed": [{"view_id": 80, "error": "join column missing"}],
            "pending": [90],
        },
    }
    assert len(api.requests) == 1


def test_job_wait_succeeds_when_the_view_it_ran_on_cannot_be_read(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    path = "/workspaces/4/projects/180/datasets/9/dataviews/7/optimize"
    _job(api, "rerun_dataview", path, {"dataview_id": 7})
    api.on("GET", r"/projects/180/datasets/9/dataviews/7$", status=403, body={"message": "no"})

    data = _data(["job", "wait", "5"], tmp_path)

    assert data["status"] == "success"
    assert "outcome" not in data
    assert data["outcome_error"]


def test_job_wait_after_a_job_with_no_object_adds_no_outcome(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind(monkeypatch, real_service)
    _job(api, "get_dataview_data", "/workspaces/4/projects/180/datasets/9/dataviews/7/data", {})

    data = _data(["job", "wait", "5"], tmp_path)

    assert "outcome" not in data
    assert len(api.requests) == 1
