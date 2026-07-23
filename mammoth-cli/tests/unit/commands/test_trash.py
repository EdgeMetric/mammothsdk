"""Unit tests for the ``trash`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import trash as trash_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_ADD = "mammoth.api.trash.TrashAPI.add"
_LIST = "mammoth.api.trash.TrashAPI.list"
_RESTORE = "mammoth.api.trash.TrashAPI.restore"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_add_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        trash_cmd.trash_add(_inv("trash.add"))
    assert excinfo.value.code == "project_required"
    assert fake_service.call_log == []


def test_add_requires_items(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        trash_cmd.trash_add(_inv("trash.add", project=180))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_add_forwards_items(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"items": [{"id": 1, "type": "dataview"}]}), encoding="utf-8")
    trash_cmd.trash_add(_inv("trash.add", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (_ADD, {"items": [{"id": 1, "type": "dataview"}], "project_id": 180})
    ]


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        trash_cmd.trash_list(_inv("trash.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project_only(fake_service: FakeMammothService) -> None:
    trash_cmd.trash_list(_inv("trash.list", project=180))
    assert fake_service.call_log == [(_LIST, {"project_id": 180})]


def test_list_forwards_optional_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "type": "dataset",
                "sort": "trashed_at",
                "order": "desc",
                "limit": 10,
                "offset": 5,
                "q": "sales",
                "trashed_by": 3,
                "trashed_after": "2024-01-01",
                "trashed_before": "2024-06-01",
                "expiring_within_days": 7,
                "folder_path": "/Reports",
                "folder_root": "workspace",
            }
        ),
        encoding="utf-8",
    )
    trash_cmd.trash_list(_inv("trash.list", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _LIST,
            {
                "project_id": 180,
                "type": "dataset",
                "sort": "trashed_at",
                "order": "desc",
                "limit": 10,
                "offset": 5,
                "q": "sales",
                "trashed_by": 3,
                "trashed_after": "2024-01-01",
                "trashed_before": "2024-06-01",
                "expiring_within_days": 7,
                "folder_path": "/Reports",
                "folder_root": "workspace",
            },
        )
    ]


def test_restore_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        trash_cmd.trash_restore(_inv("trash.restore"))
    assert excinfo.value.code == "project_required"
    assert fake_service.call_log == []


def test_restore_requires_items(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        trash_cmd.trash_restore(_inv("trash.restore", project=180))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_restore_forwards_items(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"items": [{"id": 9, "type": "dashboard"}]}), encoding="utf-8")
    trash_cmd.trash_restore(_inv("trash.restore", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (_RESTORE, {"items": [{"id": 9, "type": "dashboard"}], "project_id": 180})
    ]
