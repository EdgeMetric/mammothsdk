"""A write in draft mode is staged without a settle wait; draft status lists step errors.

Real-code: the real CLI, service and SDK client, with only the HTTP socket faked.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]
DATASET, VIEW = 55, 3062
_VIEW_BODY = {
    "id": VIEW,
    "name": "Fundraising",
    "row_count": 50,
    "metadata": [{"display_name": "Gift", "internal_name": "col_b", "type": "NUMERIC"}],
}


def _run(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    argv: list[str],
    routes: Callable[[Any], None],
) -> tuple[dict[str, Any], Any]:
    service, api = real_service(project_id=180)
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", body=_VIEW_BODY)
    api.on("PATCH", rf"/datasets/{DATASET}/dataviews/{VIEW}$", body=_VIEW_BODY)
    api.on(
        "GET",
        rf"/resources/dataview/{VIEW}$",
        body={"resource": {"object_id": VIEW, "dataset": {"id": DATASET, "name": "ds"}}},
    )
    routes(api)
    result = make_runner().invoke([*argv, "--project", "180", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"], api


def _sort(monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, pipeline: dict[str, Any]):
    return _run(
        monkeypatch,
        real_service,
        [
            "view",
            "transform",
            "sort",
            str(VIEW),
            "--input",
            json.dumps({"dataset_id": DATASET, "order_by": [["Gift", "DESC"]]}),
            "--yes",
        ],
        lambda api: (
            api.on("GET", r"/pipeline$", body=pipeline),
            api.on("GET", r"/data$", body={"data": []}),
        ),
    )


def test_a_sort_in_draft_mode_is_staged_and_waits_for_nothing(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data, _api = _sort(
        monkeypatch, real_service, {"state": "ready", "in_draft_mode": True, "draft": "dirty"}
    )

    assert data["status"] == "staged"
    assert data["sort"] == [["Gift", "DESC"]]
    assert "row_check" not in data


def test_a_sort_outside_draft_mode_is_not_staged(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data, _api = _sort(monkeypatch, real_service, {"state": "ready", "execution_state": "ready"})

    assert data.get("status") != "staged"
    assert data["row_check"]["rows_after"] == 50


def test_draft_status_lists_the_steps_whose_reference_is_in_error(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    broken_export = {
        "item_type": "export",
        "id": 12,
        "sequence": 4,
        "handler_type": "csv_file",
        "has_refferror": True,
        "error_info": {"error_code": 7003, "reason": "type_mismatch"},
    }
    broken_task = {
        "item_type": "task",
        "id": 7,
        "sequence": 2,
        "reference_errors": {
            "reference_errors": [
                {
                    "column": {"display_name": "customer_id", "type": "NUMERIC"},
                    "reason": "type_mismatch",
                    "error_code": 7003,
                }
            ]
        },
    }
    healthy = {"item_type": "task", "id": 6, "sequence": 1, "reference_errors": None}

    def routes(api: Any) -> None:
        api.on("GET", r"/pipeline$", body={"state": "ref_error", "in_draft_mode": True})
        api.on(
            "GET",
            r"/pipeline/items",
            body={"items": [healthy, broken_task, broken_export], "total": 3},
        )

    data, _api = _run(
        monkeypatch,
        real_service,
        [
            "view",
            "draft",
            "status",
            str(VIEW),
            "--input",
            json.dumps({"dataset_id": DATASET}),
        ],
        routes,
    )

    errors = {(e["item_type"], e["id"]): e for e in data["step_errors"]}
    assert set(errors) == {("task", 7), ("export", 12)}
    assert errors[("task", 7)]["reference_errors"][0]["reason"] == "type_mismatch"
    assert errors[("task", 7)]["reference_errors"][0]["error_code"] == 7003
    assert errors[("export", 12)]["error_info"]["error_code"] == 7003


def test_draft_status_with_no_broken_step_lists_none(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    def routes(api: Any) -> None:
        api.on("GET", r"/pipeline$", body={"state": "ready", "in_draft_mode": True})
        api.on("GET", r"/pipeline/items", body={"items": [{"item_type": "task", "id": 6}]})

    data, _api = _run(
        monkeypatch,
        real_service,
        ["view", "draft", "status", str(VIEW), "--input", json.dumps({"dataset_id": DATASET})],
        routes,
    )

    assert data["step_errors"] == []
