"""Unit tests for the mutating ``project`` command handlers and guards."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import project as project_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CREATE = "mammoth.api.projects.ProjectsAPI.create"
_UPDATE = "mammoth.api.projects.ProjectsAPI.update"
_DELETE = "mammoth.api.projects.ProjectsAPI.delete"
_BULK_DELETE = "mammoth.api.projects.ProjectsAPI.bulk_delete"
_BULK_UPDATE = "mammoth.api.projects.ProjectsAPI.bulk_update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_create_uses_positional_name(fake_service: FakeMammothService) -> None:
    project_cmd.project_create(_inv("project.create", extra_args=["Sales"]))
    assert fake_service.call_log == [(_CREATE, {"name": "Sales"})]


def test_create_uses_input_name_and_options(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "X", "color": "#fff"}), encoding="utf-8")
    project_cmd.project_create(_inv("project.create", input_file=str(doc)))
    assert fake_service.call_log == [(_CREATE, {"name": "X", "color": "#fff"})]


def test_create_without_name_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_create(_inv("project.create"))
    assert excinfo.value.code == "missing_argument"


def test_update_requires_a_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_update(_inv("project.update", project=1))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "New"}), encoding="utf-8")
    project_cmd.project_update(_inv("project.update", project=3, input_file=str(doc)))
    assert fake_service.call_log == [(_UPDATE, {"project_id": 3, "name": "New"})]


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_delete(_inv("project.delete", extra_args=["5"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    project_cmd.project_delete(_inv("project.delete", extra_args=["5"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"project_id": 5})]


def test_bulk_delete_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"project_ids": [1, 2]}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_bulk_delete(
            _inv("project.bulk-delete", input_file=str(doc), output="json")
        )
    assert excinfo.value.code == "confirmation_required"


def test_bulk_update_requires_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"patch_data": {"color": "#000"}}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_bulk_update(
            _inv("project.bulk-update", input_file=str(doc), yes=True, confirm="999")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"


def test_bulk_update_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"patch_data": {"color": "#000"}}), encoding="utf-8")
    project_cmd.project_bulk_update(
        _inv("project.bulk-update", input_file=str(doc), yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_BULK_UPDATE, {"patch_data": {"color": "#000"}})]
