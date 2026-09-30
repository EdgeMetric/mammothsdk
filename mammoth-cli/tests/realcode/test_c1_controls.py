"""Offline C1 controls for exact-parent dispatch and HTTP 403 recovery.

These tests exercise the real CLI service, SDK resource resolution, payload
builder, and HTTP adapter.  Only the socket is replaced by ``FakeApi``.  The
expected request paths and task payload are authored here from the public
pipeline contract, independently of the resolver implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.errors.envelope import EXIT_AUTH, CliError

ServiceFactory = Callable[..., Any]

PROJECT_ID = 180
DATASET_ID = 55
VIEW_ID = 1039

VIEW_METADATA = {
    "id": VIEW_ID,
    "name": "C1 view",
    "metadata": [
        {"display_name": "Price", "internal_name": "column_price", "type": "NUMERIC"},
        {"display_name": "Quantity", "internal_name": "column_quantity", "type": "NUMERIC"},
    ],
}


def _view_path() -> str:
    return f"/workspaces/4/projects/{PROJECT_ID}/datasets/{DATASET_ID}/dataviews/{VIEW_ID}"


def _task_path() -> str:
    return f"{_view_path()}/pipeline/tasks"


def _metadata_route(api: Any, *, status: int = 200, body: Any = None) -> None:
    api.on(
        "GET",
        rf"/datasets/{DATASET_ID}/dataviews/{VIEW_ID}$",
        status=status,
        body=VIEW_METADATA if body is None else body,
    )


def _task_requests(api: Any) -> list[Any]:
    return [request for request in api.requests if request.path.endswith("/pipeline/tasks")]


def test_exact_parent_math_uses_only_scoped_metadata_and_task_post(
    real_service: ServiceFactory,
) -> None:
    """A parent supplied by the caller must bind both GET and POST to it."""
    service, api = real_service(project_id=PROJECT_ID)
    _metadata_route(api)
    api.on("POST", r"/pipeline/tasks$", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready", "is_draft": False})

    service.call_view(
        VIEW_ID,
        "math",
        dataset_id=DATASET_ID,
        expression="Price * Quantity",
        new_column="Total",
    )

    paths = [request.path for request in api.requests]
    assert paths
    assert all(f"/datasets/{DATASET_ID}/dataviews/{VIEW_ID}" in path for path in paths)
    assert any(path.endswith(_view_path()) for path in paths)
    assert any(path.endswith(_task_path()) for path in paths)
    task = _task_requests(api)
    assert len(task) == 1
    assert task[0].method == "POST"

    # This is the independently authored wire oracle.  The generated internal
    # destination name is intentionally checked only for shape because it is
    # server-independent and random by design.
    assert task[0].json_body["DATAVIEW_ID"] == VIEW_ID
    assert task[0].json_body["MATH"]["EXPRESSION"] == [
        {"TYPE": "COLUMN", "VALUE": "column_price"},
        {"TYPE": "OPERATOR", "VALUE": "*"},
        {"TYPE": "COLUMN", "VALUE": "column_quantity"},
    ]
    assert task[0].json_body["MATH"]["AS"]["COLUMN"] == "Total"
    assert task[0].json_body["MATH"]["AS"]["TYPE"] == "NUMERIC"
    assert task[0].json_body["MATH"]["AS"]["INTERNAL_NAME"]


def test_exact_parent_task_403_is_typed_and_never_retried(
    real_service: ServiceFactory,
) -> None:
    """A denied exact-parent mutation is authorization-required, not generic API error."""
    service, api = real_service(project_id=PROJECT_ID)
    _metadata_route(api)
    api.on("POST", r"/pipeline/tasks$", status=403, body={"detail": "AddTask denied"})

    with pytest.raises(CliError) as exc_info:
        service.call_view(
            VIEW_ID,
            "math",
            dataset_id=DATASET_ID,
            expression="Price * 2",
            new_column="Double Price",
        )

    error = exc_info.value
    assert error.code == "authorization_required"
    assert error.exit_status == EXIT_AUTH
    assert error.authorization_required is True
    assert error.retryable is False
    assert error.details["status_code"] == 403
    assert error.details["method"] == "POST"
    assert error.details["endpoint"] == _task_path()
    assert error.details["operation_state"] == "failed"
    assert len(_task_requests(api)) == 1


def test_discovery_403_is_typed_and_cannot_reach_task_post(
    real_service: ServiceFactory,
) -> None:
    """A parent-discovery denial must stop before any transform mutation."""
    service, api = real_service(project_id=PROJECT_ID)
    api.on(
        "GET",
        r"/datasets$",
        body={"datasets": [{"id": DATASET_ID, "name": "ds"}], "limit": 100, "offset": 0},
    )
    _metadata_route(api, status=403, body={"detail": "metadata denied"})

    with pytest.raises(CliError) as exc_info:
        service.call_view(
            VIEW_ID,
            "math",
            expression="Price * 2",
            new_column="Double Price",
        )

    error = exc_info.value
    assert error.code == "authorization_required"
    assert error.exit_status == EXIT_AUTH
    assert error.authorization_required is True
    assert error.details["status_code"] == 403
    assert error.details["method"] == "GET"
    assert error.details["endpoint"] == _view_path()
    assert _task_requests(api) == []
