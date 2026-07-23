"""Unit tests for the ``webhook`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import webhook as webhook_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.webhooks.WebhooksAPI.list"
_GET = "mammoth.api.webhooks.WebhooksAPI.get"
_CREATE = "mammoth.api.webhooks.WebhooksAPI.create"
_UPDATE = "mammoth.api.webhooks.WebhooksAPI.update"
_DELETE = "mammoth.api.webhooks.WebhooksAPI.delete"
_SEND = "mammoth.api.webhooks.WebhooksAPI.send_data"
_SEND_GET = "mammoth.api.webhooks.WebhooksAPI.send_data_get"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_list_passes_no_kwargs_by_default(fake_service: FakeMammothService) -> None:
    webhook_cmd.webhook_list(_inv("webhook.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_forwards_limit_and_offset(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 10, "offset": 5}), encoding="utf-8")
    webhook_cmd.webhook_list(_inv("webhook.list", input_file=str(doc)))
    assert fake_service.call_log == [(_LIST, {"limit": 10, "offset": 5})]


def test_get_uses_positional_webhook_id(fake_service: FakeMammothService) -> None:
    webhook_cmd.webhook_get(_inv("webhook.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"webhook_id": 7})]


def test_get_without_webhook_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_get(_inv("webhook.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_webhook_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_get(_inv("webhook.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"


def test_create_with_no_args_passes_empty_kwargs(fake_service: FakeMammothService) -> None:
    webhook_cmd.webhook_create(_inv("webhook.create"))
    assert fake_service.call_log == [(_CREATE, {})]


def test_create_uses_positional_name(fake_service: FakeMammothService) -> None:
    webhook_cmd.webhook_create(_inv("webhook.create", extra_args=["My Hook"]))
    assert fake_service.call_log == [(_CREATE, {"name": "My Hook"})]


def test_create_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "name": "Docs Hook",
                "mode": "combine",
                "folder_resource_id": "r1",
                "origins": "https://example.com",
                "is_secure": True,
            }
        ),
        encoding="utf-8",
    )
    webhook_cmd.webhook_create(_inv("webhook.create", input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "Docs Hook",
                "mode": "combine",
                "folder_resource_id": "r1",
                "origins": "https://example.com",
                "is_secure": True,
            },
        )
    ]


def test_update_requires_webhook_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_update(_inv("webhook.update"))
    assert excinfo.value.code == "missing_argument"


def test_update_passes_only_webhook_id_when_no_fields(
    fake_service: FakeMammothService,
) -> None:
    webhook_cmd.webhook_update(_inv("webhook.update", extra_args=["7"]))
    assert fake_service.call_log == [(_UPDATE, {"webhook_id": 7})]


def test_update_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"mode": "replace", "origins": "*", "is_secure": False}), encoding="utf-8"
    )
    webhook_cmd.webhook_update(_inv("webhook.update", extra_args=["7"], input_file=str(doc)))
    assert fake_service.call_log == [
        (_UPDATE, {"webhook_id": 7, "mode": "replace", "origins": "*", "is_secure": False})
    ]


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_delete(_inv("webhook.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    webhook_cmd.webhook_delete(_inv("webhook.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"webhook_id": 7})]


def test_send_requires_webhook_uri(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_send(_inv("webhook.send"))
    assert excinfo.value.code == "missing_field"


def test_send_requires_data(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"webhook_uri": "abc123"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_send(_inv("webhook.send", input_file=str(doc)))
    assert excinfo.value.code == "missing_field"


def test_send_passes_uri_and_data(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"webhook_uri": "abc123", "data": {"col1": "val1"}}), encoding="utf-8"
    )
    webhook_cmd.webhook_send(_inv("webhook.send", input_file=str(doc)))
    assert fake_service.call_log == [(_SEND, {"webhook_uri": "abc123", "data": {"col1": "val1"}})]


def test_send_get_requires_webhook_uri(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        webhook_cmd.webhook_send_get(_inv("webhook.send-get"))
    assert excinfo.value.code == "missing_field"


def test_send_get_passes_uri_without_params(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"webhook_uri": "abc123"}), encoding="utf-8")
    webhook_cmd.webhook_send_get(_inv("webhook.send-get", input_file=str(doc)))
    assert fake_service.call_log == [(_SEND_GET, {"webhook_uri": "abc123"})]


def test_send_get_forwards_params(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"webhook_uri": "abc123", "params": {"col1": "val1"}}), encoding="utf-8"
    )
    webhook_cmd.webhook_send_get(_inv("webhook.send-get", input_file=str(doc)))
    assert fake_service.call_log == [
        (_SEND_GET, {"webhook_uri": "abc123", "params": {"col1": "val1"}})
    ]
