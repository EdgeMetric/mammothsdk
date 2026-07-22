"""Unit tests for the project sub-group handlers (checkpoint, data-check, user)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import project as project_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CHECKPOINTS = "mammoth.api.projects.ProjectsAPI.checkpoint_list"
_DATA_CHECKS = "mammoth.api.projects.ProjectsAPI.data_check_list"
_ADD_USERS = "mammoth.api.projects.ProjectsAPI.add_users"
_REMOVE_USERS = "mammoth.api.projects.ProjectsAPI.remove_users"
_USER_UPDATE = "mammoth.api.projects.ProjectsAPI.user_update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_checkpoint_list_passes_project(fake_service: FakeMammothService) -> None:
    project_cmd.project_checkpoint_list(_inv("project.checkpoint.list", extra_args=["180"]))
    assert fake_service.call_log == [(_CHECKPOINTS, {"project_id": 180})]


def test_data_check_list_forwards_filters(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"status": "failed", "dataview_id": 3}), encoding="utf-8")
    project_cmd.project_data_check_list(
        _inv("project.data-check.list", project=180, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_DATA_CHECKS, {"project_id": 180, "dataview_id": 3, "status": "failed"})
    ]


def test_user_add_requires_user_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_user_add(_inv("project.user.add", project=180, yes=True, confirm="180"))
    assert excinfo.value.code == "missing_field"


def test_user_add_blocked_without_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"user_ids": ["u1"]}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_user_add(
            _inv("project.user.add", project=180, input_file=str(doc), yes=True, confirm="179")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_user_add_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"user_ids": ["u1"], "role": "project_admin"}), encoding="utf-8")
    project_cmd.project_user_add(
        _inv("project.user.add", project=180, input_file=str(doc), yes=True, confirm="180")
    )
    assert fake_service.call_log == [
        (_ADD_USERS, {"project_id": 180, "user_ids": ["u1"], "role": "project_admin"})
    ]


def test_user_remove_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"user_ids": ["u1", "u2"]}), encoding="utf-8")
    project_cmd.project_user_remove(
        _inv("project.user.remove", project=180, input_file=str(doc), yes=True, confirm="180")
    )
    assert fake_service.call_log == [
        (_REMOVE_USERS, {"project_id": 180, "user_ids": ["u1", "u2"]})
    ]


def test_user_update_requires_role(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_user_update(_inv("project.user.update", project=180))
    assert excinfo.value.code == "missing_field"


def test_user_update_forwards_role_and_user_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"role": "project_analyst", "user_id": 9}), encoding="utf-8")
    project_cmd.project_user_update(
        _inv("project.user.update", project=180, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_USER_UPDATE, {"project_id": 180, "role": "project_analyst", "user_id": 9})
    ]
