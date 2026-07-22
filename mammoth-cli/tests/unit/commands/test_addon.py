"""Unit tests for the ``addon`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import addon as addon_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CONNECTOR_ADD = "mammoth.api.addons.AddonsAPI.add_connector"
_CONNECTOR_REMOVE = "mammoth.api.addons.AddonsAPI.remove_connector"
_LIST = "mammoth.api.addons.AddonsAPI.list"
_STORAGE_ADD = "mammoth.api.addons.AddonsAPI.add_storage"
_STORAGE_REMOVE = "mammoth.api.addons.AddonsAPI.remove_storage"
_USER_ADD = "mammoth.api.addons.AddonsAPI.add_users"
_USER_REMOVE = "mammoth.api.addons.AddonsAPI.remove_users"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- connector add ---------------------------------------------------------------


def test_connector_add_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_connector_add(_inv("addon.connector.add", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_add_requires_confirm_target(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_connector_add(_inv("addon.connector.add", yes=True, confirm="999"))
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_connector_add_forwards_single_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"connector_id": 42})
    addon_cmd.addon_connector_add(
        _inv("addon.connector.add", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_CONNECTOR_ADD, {"connector_id": 42})]


def test_connector_add_forwards_bulk_ids(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"connector_ids": [1, 2]})
    addon_cmd.addon_connector_add(
        _inv("addon.connector.add", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_CONNECTOR_ADD, {"connector_ids": [1, 2]})]


# --- connector remove ------------------------------------------------------------


def test_connector_remove_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_connector_remove(_inv("addon.connector.remove", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_remove_forwards_single_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"connector_id": 7})
    addon_cmd.addon_connector_remove(
        _inv("addon.connector.remove", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_CONNECTOR_REMOVE, {"connector_id": 7})]


# --- list --------------------------------------------------------------------------


def test_list_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST] = {"addons": []}
    result, meta = addon_cmd.addon_list(_inv("addon.list"))
    assert fake_service.call_log == [(_LIST, {})]
    assert result == {"addons": []}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": None}


# --- storage add ---------------------------------------------------------------


def test_storage_add_requires_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_storage_add(_inv("addon.storage.add", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_storage_add_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"additional_storage_gb": 50})
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_storage_add(
            _inv("addon.storage.add", input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_storage_add_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"additional_storage_gb": 50})
    addon_cmd.addon_storage_add(
        _inv("addon.storage.add", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STORAGE_ADD, {"additional_storage_gb": 50})]


def test_storage_add_target_mismatch(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"additional_storage_gb": 50})
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_storage_add(
            _inv("addon.storage.add", input_file=doc, yes=True, confirm="999")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


# --- storage remove --------------------------------------------------------------


def test_storage_remove_requires_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_storage_remove(_inv("addon.storage.remove", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_storage_remove_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"removal_storage_gb": 10})
    addon_cmd.addon_storage_remove(
        _inv("addon.storage.remove", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STORAGE_REMOVE, {"removal_storage_gb": 10})]


# --- user add ----------------------------------------------------------------------


def test_user_add_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_user_add(_inv("addon.user.add", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_add_forwards_user_count(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"user_count": 5})
    addon_cmd.addon_user_add(_inv("addon.user.add", input_file=doc, yes=True, confirm="4"))
    assert fake_service.call_log == [(_USER_ADD, {"user_count": 5})]


def test_user_add_without_input_omits_user_count(fake_service: FakeMammothService) -> None:
    addon_cmd.addon_user_add(_inv("addon.user.add", yes=True, confirm="4"))
    assert fake_service.call_log == [(_USER_ADD, {})]


def test_user_add_target_mismatch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_user_add(_inv("addon.user.add", yes=True, confirm="999"))
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


# --- user remove ---------------------------------------------------------------


def test_user_remove_requires_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_user_remove(_inv("addon.user.remove", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_user_remove_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"user_count": 2})
    with pytest.raises(CliError) as excinfo:
        addon_cmd.addon_user_remove(
            _inv("addon.user.remove", input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_remove_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"user_count": 2})
    addon_cmd.addon_user_remove(
        _inv("addon.user.remove", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_USER_REMOVE, {"user_count": 2})]
