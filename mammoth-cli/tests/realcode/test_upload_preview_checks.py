"""The upload preview says it was checked, or says why it could not be built.

Only the HTTP socket is faked; the preview, the data-quality checks and the
SDK calls are the real code.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.commands.view import upload_preview
from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

DATASET_ID = 55
VIEW_ID = 1039

ServiceFactory = Callable[..., Any]


def _views(api: Any, views: list[dict[str, Any]]) -> None:
    api.on("GET", rf"/datasets/{DATASET_ID}/dataviews$", body={"dataviews": views})


def _view(rows: list[dict[str, Any]], api: Any) -> dict[str, Any]:
    api.on("GET", rf"/dataviews/{VIEW_ID}/data", body={"data": rows})
    return {
        "id": VIEW_ID,
        "name": "V",
        "row_count": len(rows),
        "metadata": [{"display_name": "tip", "internal_name": "column_1", "type": "NUMERIC"}],
    }


def test_clean_preview_carries_checks_and_an_empty_warning_list(
    real_service: ServiceFactory,
) -> None:
    service, api = real_service(project_id=180)
    _views(api, [_view([{"column_1": 1}, {"column_1": 2}, {"column_1": 3}], api)])
    preview = upload_preview(service, DATASET_ID, 180)
    assert "preview_error" not in preview
    assert preview["column_warnings"] == []
    assert preview["column_checks"]["rows_checked"] == 3
    assert preview["column_checks"]["found"] == 0
    assert "error" not in preview["column_checks"]


def test_a_dataset_without_views_is_an_explicit_preview_error(
    real_service: ServiceFactory,
) -> None:
    service, api = real_service(project_id=180)
    _views(api, [])
    preview = upload_preview(service, DATASET_ID, 180)
    assert preview == {"preview_error": f"dataset {DATASET_ID} has no view to preview"}


def test_a_failed_read_is_an_explicit_preview_error(real_service: ServiceFactory) -> None:
    service, api = real_service(project_id=180)
    api.on("GET", rf"/datasets/{DATASET_ID}/dataviews$", status=500, body={"message": "boom"})
    preview = upload_preview(service, DATASET_ID, 180)
    assert set(preview) == {"preview_error"}


def test_project_check_lists_checked_and_skipped_datasets(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    view = _view([{"column_1": 1}, {"column_1": 2}], api)
    _views(api, [view])
    api.on("GET", r"/datasets/91/dataviews$", body={"dataviews": []})

    ok = make_runner().invoke(["project", "check", "180", "55", "--output", "json"])
    assert ok.exit_code == 0, ok.output
    data = json.loads(ok.output)["data"]
    assert data["checked"] == [
        {"dataset_id": 55, "view_id": VIEW_ID, "view_name": "V", "rows_checked": 2}
    ]
    assert data["skipped"] == []

    empty = make_runner().invoke(["project", "check", "180", "91", "--output", "json"])
    data = json.loads(empty.output)["data"]
    assert data["checked"] == []
    assert data["skipped"] == [{"dataset_id": 91, "reason": "dataset 91 has no view to preview"}]
