"""Unit tests for the ``client-app`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import client_app as client_app_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.clientapps.ClientAppsAPI.list"
_GET = "mammoth.api.clientapps.ClientAppsAPI.get"
_CREATE = "mammoth.api.clientapps.ClientAppsAPI.create"
_UPDATE = "mammoth.api.clientapps.ClientAppsAPI.update"
_DELETE = "mammoth.api.clientapps.ClientAppsAPI.delete"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_with_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    client_app_cmd.client_app_list(_inv("client-app.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"limit": 5, "offset": 10, "fields": "id,app_name", "sort": "app_name"}),
        encoding="utf-8",
    )
    client_app_cmd.client_app_list(_inv("client-app.list", input_file=str(doc)))
    assert fake_service.call_log == [
        (_LIST, {"limit": 5, "offset": 10, "fields": "id,app_name", "sort": "app_name"})
    ]


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_uses_positional_client_key(fake_service: FakeMammothService) -> None:
    client_app_cmd.client_app_get(_inv("client-app.get", extra_args=["ck_1"]))
    assert fake_service.call_log == [(_GET, {"client_key": "ck_1"})]


def test_get_without_client_key_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_get(_inv("client-app.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"fields": "id,app_name"}), encoding="utf-8")
    client_app_cmd.client_app_get(
        _inv("client-app.get", extra_args=["ck_1"], input_file=str(doc))
    )
    assert fake_service.call_log == [(_GET, {"client_key": "ck_1", "fields": "id,app_name"})]


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create_requires_app_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_create(_inv("client-app.create", yes=True, confirm="My App"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_create_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_create(
            _inv("client-app.create", extra_args=["My App"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_create_blocked_on_confirm_mismatch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_create(
            _inv("client-app.create", extra_args=["My App"], yes=True, confirm="Other")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_create_uses_positional_name_with_matching_confirm(
    fake_service: FakeMammothService,
) -> None:
    client_app_cmd.client_app_create(
        _inv("client-app.create", extra_args=["My App"], yes=True, confirm="My App")
    )
    assert fake_service.call_log == [(_CREATE, {"app_name": "My App"})]


def test_create_uses_input_name_and_forwards_description(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"app_name": "My App", "description": "A test app"}), encoding="utf-8"
    )
    client_app_cmd.client_app_create(
        _inv("client-app.create", input_file=str(doc), yes=True, confirm="My App")
    )
    assert fake_service.call_log == [
        (_CREATE, {"app_name": "My App", "description": "A test app"})
    ]


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_requires_patch_request(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_update(
            _inv("client-app.update", extra_args=["ck_1"], yes=True, confirm="ck_1")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"patch_request": {"patch": []}}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_update(
            _inv("client-app.update", extra_args=["ck_1"], input_file=str(doc), output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_forwards_patch_request(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"patch_request": {"patch": [{"op": "replace", "path": "/description"}]}}),
        encoding="utf-8",
    )
    client_app_cmd.client_app_update(
        _inv(
            "client-app.update",
            extra_args=["ck_1"],
            input_file=str(doc),
            yes=True,
            confirm="ck_1",
        )
    )
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "client_key": "ck_1",
                "patch_request": {"patch": [{"op": "replace", "path": "/description"}]},
            },
        )
    ]


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_without_client_key_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_delete(_inv("client-app.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        client_app_cmd.client_app_delete(
            _inv("client-app.delete", extra_args=["ck_1"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    client_app_cmd.client_app_delete(
        _inv("client-app.delete", extra_args=["ck_1"], yes=True)
    )
    assert fake_service.call_log == [(_DELETE, {"client_key": "ck_1"})]
