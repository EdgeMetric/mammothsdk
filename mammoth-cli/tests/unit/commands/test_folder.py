"""Unit tests for the ``folder`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import folder as folder_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.folders.FoldersAPI.list"
_GET = "mammoth.api.folders.FoldersAPI.get"
_ROOT = "mammoth.api.folders.FoldersAPI.get_project_root"
_CREATE = "mammoth.api.folders.FoldersAPI.create"
_UPDATE = "mammoth.api.folders.FoldersAPI.update"
_MOVE = "mammoth.api.folders.FoldersAPI.move"
_TRASH = "mammoth.api.folders.FoldersAPI.trash"
_DELETE = "mammoth.api.folders.FoldersAPI.delete"
_BULK_DELETE = "mammoth.api.folders.FoldersAPI.bulk_delete"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        folder_cmd.folder_list(_inv("folder.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project_and_optional_limit(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 10}), encoding="utf-8")
    folder_cmd.folder_list(_inv("folder.list", project=180, input_file=str(doc)))
    assert fake_service.call_log == [(_LIST, {"project_id": 180, "limit": 10})]


def test_get_uses_positional_folder_id(fake_service: FakeMammothService) -> None:
    folder_cmd.folder_get(_inv("folder.get", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"folder_id": 7, "project_id": 180})]


def test_get_without_folder_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        folder_cmd.folder_get(_inv("folder.get", project=180))
    assert excinfo.value.code == "missing_argument"


def test_root_passes_project(fake_service: FakeMammothService) -> None:
    folder_cmd.folder_root(_inv("folder.root", project=180))
    assert fake_service.call_log == [(_ROOT, {"project_id": 180})]


def test_create_uses_positional_name(fake_service: FakeMammothService) -> None:
    folder_cmd.folder_create(_inv("folder.create", project=180, extra_args=["Docs"]))
    assert fake_service.call_log == [(_CREATE, {"name": "Docs", "project_id": 180})]


def test_create_forwards_parent(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "Docs", "parent_resource_id": "r1"}), encoding="utf-8")
    folder_cmd.folder_create(_inv("folder.create", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (_CREATE, {"name": "Docs", "project_id": 180, "parent_resource_id": "r1"})
    ]


def test_update_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        folder_cmd.folder_update(_inv("folder.update", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "New"}), encoding="utf-8")
    folder_cmd.folder_update(
        _inv("folder.update", project=180, extra_args=["7"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_UPDATE, {"folder_id": 7, "name": "New", "project_id": 180})
    ]


def test_move_requires_resource_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        folder_cmd.folder_move(_inv("folder.move", project=180))
    assert excinfo.value.code == "missing_field"


def test_move_forwards_targets(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"resource_ids": ["a"], "target_folder_resource_id": "t"}), encoding="utf-8"
    )
    folder_cmd.folder_move(_inv("folder.move", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (_MOVE, {"resource_ids": ["a"], "project_id": 180, "target_folder_resource_id": "t"})
    ]


def test_trash_passes_folder_and_project(fake_service: FakeMammothService) -> None:
    folder_cmd.folder_trash(_inv("folder.trash", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_TRASH, {"folder_id": 7, "project_id": 180})]


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        folder_cmd.folder_delete(
            _inv("folder.delete", project=180, extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    folder_cmd.folder_delete(_inv("folder.delete", project=180, extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"folder_ids": [7], "project_id": 180})]


def test_bulk_delete_requires_folder_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        folder_cmd.folder_bulk_delete(_inv("folder.bulk-delete", project=180, yes=True))
    assert excinfo.value.code == "missing_field"


def test_bulk_delete_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"folder_ids": [1, 2]}), encoding="utf-8")
    folder_cmd.folder_bulk_delete(
        _inv("folder.bulk-delete", project=180, input_file=str(doc), yes=True)
    )
    assert fake_service.call_log == [(_BULK_DELETE, {"folder_ids": [1, 2], "project_id": 180})]
