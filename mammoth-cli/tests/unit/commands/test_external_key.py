"""Unit tests for the ``external-key`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import external_key as external_key_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.external_keys.ExternalKeysAPI.list"
_GET = "mammoth.api.external_keys.ExternalKeysAPI.get"
_CREATE = "mammoth.api.external_keys.ExternalKeysAPI.create"
_DELETE = "mammoth.api.external_keys.ExternalKeysAPI.delete"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_list_calls_with_no_kwargs(fake_service: FakeMammothService) -> None:
    external_key_cmd.external_key_list(_inv("external-key.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_get_uses_positional_key_id(fake_service: FakeMammothService) -> None:
    external_key_cmd.external_key_get(_inv("external-key.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"key_id": 7})]


def test_get_without_key_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_get(_inv("external-key.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_key_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_get(_inv("external-key.get", extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


def test_create_requires_key_type(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"key_name": "n", "secure_key": "sk-123"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_create(
            _inv("external-key.create", input_file=str(doc), yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_requires_key_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"key_type": "anthropic", "secure_key": "sk-123"}), encoding="utf-8"
    )
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_create(
            _inv("external-key.create", input_file=str(doc), yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"


def test_create_requires_secure_key(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"key_type": "anthropic", "key_name": "n"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_create(
            _inv("external-key.create", input_file=str(doc), yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"


def test_create_ignores_positional_for_secret(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A positional never substitutes for required create fields."""
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"key_name": "n", "secure_key": "sk-123"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_create(
            _inv(
                "external-key.create",
                extra_args=["anthropic"],
                input_file=str(doc),
                yes=True,
                confirm="4",
            )
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"key_type": "anthropic", "key_name": "n", "secure_key": "sk-123"}),
        encoding="utf-8",
    )
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_create(
            _inv("external-key.create", input_file=str(doc), output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_create_requires_matching_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"key_type": "anthropic", "key_name": "n", "secure_key": "sk-123"}),
        encoding="utf-8",
    )
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_create(
            _inv("external-key.create", input_file=str(doc), yes=True, confirm="999")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_create_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"key_type": "anthropic", "key_name": "n", "secure_key": "sk-123"}),
        encoding="utf-8",
    )
    external_key_cmd.external_key_create(
        _inv("external-key.create", input_file=str(doc), yes=True, confirm="4")
    )
    assert fake_service.call_log == [
        (_CREATE, {"key_type": "anthropic", "key_name": "n", "secure_key": "sk-123"})
    ]


def test_create_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "key_type": "anthropic",
                "key_name": "n",
                "secure_key": "sk-123",
                "description": "prod key",
                "model_id": "claude-x",
                "model_settings": {"thinking_budget": 100},
            }
        ),
        encoding="utf-8",
    )
    external_key_cmd.external_key_create(
        _inv("external-key.create", input_file=str(doc), yes=True, confirm="4")
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "key_type": "anthropic",
                "key_name": "n",
                "secure_key": "sk-123",
                "description": "prod key",
                "model_id": "claude-x",
                "model_settings": {"thinking_budget": 100},
            },
        )
    ]


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_delete(
            _inv("external-key.delete", extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    external_key_cmd.external_key_delete(
        _inv("external-key.delete", extra_args=["7"], yes=True)
    )
    assert fake_service.call_log == [(_DELETE, {"key_id": 7})]


def test_delete_without_key_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        external_key_cmd.external_key_delete(_inv("external-key.delete", yes=True))
    assert excinfo.value.code == "missing_argument"
