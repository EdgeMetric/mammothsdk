"""Unit tests for the ``automation`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import automation as automation_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.automations.AutomationsAPI.list"
_GET = "mammoth.api.automations.AutomationsAPI.get"
_CREATE = "mammoth.api.automations.AutomationsAPI.create"
_UPDATE = "mammoth.api.automations.AutomationsAPI.update"
_DELETE = "mammoth.api.automations.AutomationsAPI.delete"
_RESTORE = "mammoth.api.automations.AutomationsAPI.restore"
_TRASH = "mammoth.api.automations.AutomationsAPI.trash"


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


# --- automation list -----------------------------------------------------


def test_list_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    automation_cmd.automation_list(_inv("automation.list"))
    assert fake_service.call_log == [(_LIST, {})]


# --- automation get -------------------------------------------------------


def test_get_uses_positional_automation_id(fake_service: FakeMammothService) -> None:
    automation_cmd.automation_get(_inv("automation.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"automation_id": 7})]


def test_get_without_id_is_missing_argument(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_get(_inv("automation.get"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_get_with_non_integer_id_is_invalid_argument(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_get(_inv("automation.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


# --- automation trash / restore -------------------------------------------


def test_trash_passes_automation_id(fake_service: FakeMammothService) -> None:
    automation_cmd.automation_trash(_inv("automation.trash", extra_args=["9"]))
    assert fake_service.call_log == [(_TRASH, {"automation_id": 9})]


def test_restore_passes_automation_id(fake_service: FakeMammothService) -> None:
    automation_cmd.automation_restore(_inv("automation.restore", extra_args=["9"]))
    assert fake_service.call_log == [(_RESTORE, {"automation_id": 9})]


# --- automation delete -----------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_delete(_inv("automation.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    automation_cmd.automation_delete(_inv("automation.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"automation_id": 7})]


# --- automation create -----------------------------------------------------


def test_create_requires_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(tmp_path, {"description": "d", "tasks": [{"task_type": "run_data_retrieval"}]})
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_create(_inv("automation.create", input_file=doc, yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_create_requires_description(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(tmp_path, {"name": "Nightly", "tasks": [{"task_type": "run_data_retrieval"}]})
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_create(_inv("automation.create", input_file=doc, yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_requires_tasks(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(tmp_path, {"name": "Nightly", "description": "d"})
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_create(_inv("automation.create", input_file=doc, yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path,
        {
            "name": "Nightly",
            "description": "d",
            "tasks": [{"task_type": "run_data_retrieval"}],
        },
    )
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_create(_inv("automation.create", input_file=doc, output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_create_uses_positional_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(tmp_path, {"description": "d", "tasks": [{"task_type": "run_data_retrieval"}]})
    automation_cmd.automation_create(
        _inv("automation.create", extra_args=["Nightly"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "Nightly",
                "description": "d",
                "tasks": [{"task_type": "run_data_retrieval"}],
            },
        )
    ]


def test_create_forwards_conditions_and_mode(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path,
        {
            "name": "Nightly",
            "description": "d",
            "tasks": [{"task_type": "run_data_retrieval"}],
            "conditions": [{"condition_type": "at_specific_time", "details": {"interval": None}}],
            "condition_mode": "or",
        },
    )
    automation_cmd.automation_create(_inv("automation.create", input_file=doc, yes=True))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "Nightly",
                "description": "d",
                "tasks": [{"task_type": "run_data_retrieval"}],
                "conditions": [
                    {"condition_type": "at_specific_time", "details": {"interval": None}}
                ],
                "condition_mode": "or",
            },
        )
    ]


# --- automation update ------------------------------------------------------


def test_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_update(_inv("automation.update", extra_args=["7"], yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"patch": [{"op": "command", "path": "run", "value": {}}]})
    with pytest.raises(CliError) as excinfo:
        automation_cmd.automation_update(
            _inv("automation.update", extra_args=["7"], input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(tmp_path, {"patch": [{"op": "command", "path": "run", "value": {}}]})
    automation_cmd.automation_update(
        _inv("automation.update", extra_args=["7"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (_UPDATE, {"automation_id": 7, "patch": [{"op": "command", "path": "run", "value": {}}]})
    ]
