"""Unit tests for the ``notification`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import notification as notification_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.notifications.NotificationsAPI.list"
_UPDATE = "mammoth.api.notifications.NotificationsAPI.update"
_UPDATE_BATCH = "mammoth.api.notifications.NotificationsAPI.update_batch"
_DELETE = "mammoth.api.notifications.NotificationsAPI.delete"
_DELETE_BATCH = "mammoth.api.notifications.NotificationsAPI.delete_batch"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write_doc(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- notification list -------------------------------------------------


def test_list_with_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    notification_cmd.notification_list(_inv("notification.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_forwards_optional_filters(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path,
        {
            "fields": "id,status",
            "project_id": 180,
            "status": "unread",
            "is_read": False,
            "notification_scope": "workspace",
            "limit": 10,
            "offset": 5,
            "sort": "-created_at",
        },
    )
    notification_cmd.notification_list(_inv("notification.list", input_file=doc))
    assert fake_service.call_log == [
        (
            _LIST,
            {
                "fields": "id,status",
                "project_id": 180,
                "status": "unread",
                "is_read": False,
                "notification_scope": "workspace",
                "limit": 10,
                "offset": 5,
                "sort": "-created_at",
            },
        )
    ]


def test_list_never_forwards_workspace_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"workspace_id": 999, "status": "read"})
    notification_cmd.notification_list(_inv("notification.list", input_file=doc))
    assert fake_service.call_log == [(_LIST, {"status": "read"})]


# --- notification update ------------------------------------------------


def test_update_uses_positional_id_and_requires_patch(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_update(_inv("notification.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_update(_inv("notification.update"))
    assert excinfo.value.code == "missing_argument"


def test_update_forwards_notification_id_and_patch(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"patch": [{"op": "replace", "path": "/is_read", "value": True}]})
    notification_cmd.notification_update(
        _inv("notification.update", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "notification_id": 7,
                "patch": [{"op": "replace", "path": "/is_read", "value": True}],
            },
        )
    ]


# --- notification update-batch ------------------------------------------


def test_update_batch_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_update_batch(_inv("notification.update-batch"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_batch_forwards_patch_only(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path,
        {"patch": [{"op": "replace", "path": "/is_read", "value": True}], "workspace_id": 4},
    )
    notification_cmd.notification_update_batch(
        _inv("notification.update-batch", input_file=doc)
    )
    assert fake_service.call_log == [
        (_UPDATE_BATCH, {"patch": [{"op": "replace", "path": "/is_read", "value": True}]})
    ]


# --- notification delete -------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_delete(
            _inv("notification.delete", extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    notification_cmd.notification_delete(
        _inv("notification.delete", extra_args=["7"], yes=True)
    )
    assert fake_service.call_log == [(_DELETE, {"notification_id": 7})]


def test_delete_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_delete(_inv("notification.delete", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# --- notification delete-batch -------------------------------------------


def test_delete_batch_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"ids": [1, 2]})
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_delete_batch(
            _inv("notification.delete-batch", input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_batch_proceeds_with_yes_and_forwards_ids(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"ids": [1, 2]})
    notification_cmd.notification_delete_batch(
        _inv("notification.delete-batch", input_file=doc, yes=True)
    )
    assert fake_service.call_log == [(_DELETE_BATCH, {"ids": [1, 2]})]


def test_delete_batch_proceeds_with_filter_only_and_no_workspace_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path, {"last_updated_at__lt": "2026-01-01", "is_read": True, "workspace_id": 4}
    )
    notification_cmd.notification_delete_batch(
        _inv("notification.delete-batch", input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (_DELETE_BATCH, {"last_updated_at__lt": "2026-01-01", "is_read": True})
    ]


def test_delete_batch_with_no_input_still_requires_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        notification_cmd.notification_delete_batch(_inv("notification.delete-batch"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []
