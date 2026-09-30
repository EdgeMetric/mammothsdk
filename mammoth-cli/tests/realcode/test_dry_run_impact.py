"""``--dry-run`` of a data-changing transform reports what it would change.

Real-code: argv through the real handler, service and client, with only the
HTTP socket faked. A transform that would change nothing fails the dry run with
``no_op`` (an error envelope, so the in-product agent's confirmation gate sends
it back to the model before any approval card opens).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]

_VIEW = {
    "id": 3062,
    "name": "Fundraising",
    "row_count": 50,
    "metadata": [
        {"display_name": "Donor", "internal_name": "col_a", "type": "TEXT"},
        {"display_name": "Gift", "internal_name": "col_b", "type": "NUMERIC"},
    ],
}


def _dry_run(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    group_counts: list[int],
    input_doc: dict[str, Any] | None = None,
) -> tuple[Any, Any]:
    service, api = real_service(project_id=180)
    monkeypatch.setattr(factory, "build_service", lambda *a, **k: service)
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)
    api.on(
        "POST",
        r"/datasets/55/dataviews/3062/data/query$",
        body={"data": [{"agg_0": n} for n in group_counts]},
    )
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "discard-duplicates",
            "3062",
            "--project",
            "180",
            "--input",
            json.dumps({"dataset_id": 55, **(input_doc or {})}),
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    return result, api


def test_discard_duplicates_dry_run_with_no_duplicates_is_a_no_op_error(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, api = _dry_run(monkeypatch, real_service, [1, 1, 1])
    error = json.loads(result.output)["error"]
    assert error["code"] == "no_op"
    assert "View 3062 has no exact duplicate rows (50 of 50 checked)" in error["message"]
    assert "nothing to change" in error["message"]
    assert not [r for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]


def test_discard_duplicates_dry_run_reports_the_rows_it_would_remove(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, _ = _dry_run(monkeypatch, real_service, [3, 2, 1])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["dry_run"] is True
    assert data["predicted_impact"] == {
        "rows_removed": 3,
        "row_count": 50,
        "rows_after": 47,
        "exact": True,
    }


def test_discard_duplicates_dry_run_honours_ignore_columns(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, api = _dry_run(monkeypatch, real_service, [1], {"ignore_columns": ["Gift"]})
    error = json.loads(result.output)["error"]
    assert error["code"] == "no_op"
    assert "ignoring Gift" in error["message"]
    query = [r for r in api.requests if r.path.endswith("/data/query")][0].json_body
    grouped = [item["COLUMN"] for item in query["param"]["PIVOT"]["GROUP_BY"]]
    assert grouped == ["col_a"]


def test_discard_duplicates_dry_run_says_so_when_the_count_could_not_run(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    service, api = real_service(project_id=180)
    monkeypatch.setattr(factory, "build_service", lambda *a, **k: service)
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)
    api.on("POST", r"/data/query$", status=500, body={"detail": "boom"})
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "discard-duplicates",
            "3062",
            "--project",
            "180",
            "--input",
            '{"dataset_id": 55}',
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code == 0, result.output
    impact = json.loads(result.output)["data"]["predicted_impact"]
    assert impact["checked"] is False and impact["reason"]
