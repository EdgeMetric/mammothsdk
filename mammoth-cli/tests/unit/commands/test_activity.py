"""Unit tests for the ``activity`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import activity as activity_cmd
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.activity_logs.ActivityLogsAPI.list"
_EXPORT = "mammoth.api.activity_logs.ActivityLogsAPI.export"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write_doc(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- activity list -------------------------------------------------------


def test_list_with_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    activity_cmd.activity_list(_inv("activity.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_forwards_optional_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(
        tmp_path,
        {
            "limit": 10,
            "offset": 5,
            "sort": "-created_at",
            "project_id": 180,
            "categories": ["Project", "Dataview"],
            "activities": ["create_project"],
            "resource_id": "resource_123",
            "result": "success",
            "start_time": "2021-01-01 00:00:00",
            "end_time": "2021-01-31 23:59:59",
            "origin": "user",
            "user_ids": [14, 27],
            "parent_id": 3,
            "search_text": "create",
        },
    )
    activity_cmd.activity_list(_inv("activity.list", input_file=doc))
    assert fake_service.call_log == [
        (
            _LIST,
            {
                "limit": 10,
                "offset": 5,
                "sort": "-created_at",
                "project_id": 180,
                "categories": ["Project", "Dataview"],
                "activities": ["create_project"],
                "resource_id": "resource_123",
                "result": "success",
                "start_time": "2021-01-01 00:00:00",
                "end_time": "2021-01-31 23:59:59",
                "origin": "user",
                "user_ids": [14, 27],
                "parent_id": 3,
                "search_text": "create",
            },
        )
    ]


def test_list_never_forwards_unknown_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"workspace_id": 999, "limit": 5})
    activity_cmd.activity_list(_inv("activity.list", input_file=doc))
    assert fake_service.call_log == [(_LIST, {"limit": 5})]


def test_list_returns_response_and_meta(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = {"activity_logs": [], "limit": 50, "offset": 0}
    data, meta = activity_cmd.activity_list(_inv("activity.list", project=180))
    assert data == {"activity_logs": [], "limit": 50, "offset": 0}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": 180}


# --- activity export ------------------------------------------------------


def test_export_with_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    activity_cmd.activity_export(_inv("activity.export"))
    assert fake_service.call_log == [(_EXPORT, {})]


def test_export_forwards_optional_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(
        tmp_path,
        {
            "format": "xlsx",
            "start_time": "2021-01-01 00:00:00",
            "end_time": "2021-01-31 23:59:59",
            "categories": ["Project", "View"],
            "activities": ["create_project", "create_view"],
            "user_ids": [14, 27],
        },
    )
    activity_cmd.activity_export(_inv("activity.export", input_file=doc))
    assert fake_service.call_log == [
        (
            _EXPORT,
            {
                "format": "xlsx",
                "start_time": "2021-01-01 00:00:00",
                "end_time": "2021-01-31 23:59:59",
                "categories": ["Project", "View"],
                "activities": ["create_project", "create_view"],
                "user_ids": [14, 27],
            },
        )
    ]


def test_export_never_forwards_unknown_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"workspace_id": 999, "format": "csv"})
    activity_cmd.activity_export(_inv("activity.export", input_file=doc))
    assert fake_service.call_log == [(_EXPORT, {"format": "csv"})]


def test_export_returns_response_and_meta(fake_service: FakeMammothService) -> None:
    fake_service.responses[_EXPORT] = {"job_id": "job_1"}
    data, meta = activity_cmd.activity_export(_inv("activity.export"))
    assert data == {"job_id": "job_1"}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": None}
