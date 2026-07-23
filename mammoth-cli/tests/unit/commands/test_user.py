"""Unit tests for the ``user`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import user as user_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_AVATAR_DELETE = "mammoth.api.users.UsersAPI.avatar_delete"
_AVATAR_UPLOAD = "mammoth.api.users.UsersAPI.avatar_upload"
_CHANGE_PASSWORD = "mammoth.api.user_profile.UserProfileAPI.change_password"
_DELETE_ACCOUNT = "mammoth.api.users.UsersAPI.delete_account"
_GET = "mammoth.api.user_profile.UserProfileAPI.get"
_PREFERENCE_GET = "mammoth.api.user_profile.UserProfileAPI.get_preferences"
_PREFERENCE_UPDATE = "mammoth.api.user_profile.UserProfileAPI.update_preferences"
_UPDATE = "mammoth.api.user_profile.UserProfileAPI.update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, data: object) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(data), encoding="utf-8")
    return str(doc)


# --- avatar delete -----------------------------------------------------------


def test_avatar_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_avatar_delete(_inv("user.avatar.delete", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_avatar_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    user_cmd.user_avatar_delete(_inv("user.avatar.delete", yes=True))
    assert fake_service.call_log == [(_AVATAR_DELETE, {})]


# --- avatar upload -----------------------------------------------------------


def test_avatar_upload_requires_file(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_avatar_upload(_inv("user.avatar.upload"))
    assert excinfo.value.code == "missing_argument"


def test_avatar_upload_uses_positional_file(fake_service: FakeMammothService) -> None:
    user_cmd.user_avatar_upload(_inv("user.avatar.upload", extra_args=["avatar.png"]))
    assert fake_service.call_log == [(_AVATAR_UPLOAD, {"file": "avatar.png"})]


def test_avatar_upload_uses_input_field(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"file": "photo.jpg"})
    user_cmd.user_avatar_upload(_inv("user.avatar.upload", input_file=doc))
    assert fake_service.call_log == [(_AVATAR_UPLOAD, {"file": "photo.jpg"})]


# --- change-password -----------------------------------------------------------


def test_change_password_requires_current_password(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_change_password(_inv("user.change-password", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_change_password_requires_new_password(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"current_password": "old"})
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_change_password(
            _inv("user.change-password", input_file=doc, yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_change_password_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"current_password": "old", "new_password": "new"})
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_change_password(_inv("user.change-password", input_file=doc, output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_change_password_requires_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"current_password": "old", "new_password": "new"})
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_change_password(
            _inv("user.change-password", input_file=doc, yes=True, confirm="999")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_change_password_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"current_password": "old", "new_password": "new"})
    user_cmd.user_change_password(
        _inv("user.change-password", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [
        (_CHANGE_PASSWORD, {"current_password": "old", "new_password": "new"})
    ]


# --- delete-account -----------------------------------------------------------


def test_delete_account_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_delete_account(_inv("user.delete-account", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_account_requires_confirm_target(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_delete_account(_inv("user.delete-account", yes=True, confirm="999"))
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_delete_account_proceeds_with_matching_target(fake_service: FakeMammothService) -> None:
    user_cmd.user_delete_account(_inv("user.delete-account", yes=True, confirm="4"))
    assert fake_service.call_log == [(_DELETE_ACCOUNT, {})]


def test_delete_account_forwards_validate_only(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"validate_only": True})
    user_cmd.user_delete_account(_inv("user.delete-account", input_file=doc, yes=True, confirm="4"))
    assert fake_service.call_log == [(_DELETE_ACCOUNT, {"validate_only": True})]


# --- get -----------------------------------------------------------------------


def test_get(fake_service: FakeMammothService) -> None:
    user_cmd.user_get(_inv("user.get"))
    assert fake_service.call_log == [(_GET, {})]


# --- preference get/update -------------------------------------------------------


def test_preference_get(fake_service: FakeMammothService) -> None:
    user_cmd.user_preference_get(_inv("user.preference.get"))
    assert fake_service.call_log == [(_PREFERENCE_GET, {})]


def test_preference_update_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_preference_update(_inv("user.preference.update"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_preference_update_forwards_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"theme": "dark", "locale": "en-US"})
    user_cmd.user_preference_update(_inv("user.preference.update", input_file=doc))
    assert fake_service.call_log == [(_PREFERENCE_UPDATE, {"theme": "dark", "locale": "en-US"})]


# --- update ----------------------------------------------------------------------


def test_update_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_update(_inv("user.update", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "New Name"})
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_update(_inv("user.update", input_file=doc, output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_requires_confirm_target(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"name": "New Name"})
    with pytest.raises(CliError) as excinfo:
        user_cmd.user_update(_inv("user.update", input_file=doc, yes=True, confirm="999"))
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_update_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "New Name", "email": "a@x.com"})
    user_cmd.user_update(_inv("user.update", input_file=doc, yes=True, confirm="4"))
    assert fake_service.call_log == [(_UPDATE, {"name": "New Name", "email": "a@x.com"})]
