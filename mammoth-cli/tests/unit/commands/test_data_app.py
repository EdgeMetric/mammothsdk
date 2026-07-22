"""Unit tests for the ``data-app`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import data_app as data_app_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.data_apps.DataAppsAPI.list"
_GET = "mammoth.api.data_apps.DataAppsAPI.get"
_CREATE = "mammoth.api.data_apps.DataAppsAPI.create"
_UPDATE = "mammoth.api.data_apps.DataAppsAPI.update"
_DELETE = "mammoth.api.data_apps.DataAppsAPI.delete"
_ACTIVE_JOB = "mammoth.api.data_apps.DataAppsAPI.active_job"
_JOB = "mammoth.api.data_apps.DataAppsAPI.job"
_PIPELINE_CHANGES = "mammoth.api.data_apps.DataAppsAPI.pipeline_changes"
_SHARE = "mammoth.api.data_apps.DataAppsAPI.share"
_UPLOAD = "mammoth.api.data_apps.DataAppsAPI.upload"
_USER_LIST = "mammoth.api.data_apps.DataAppsAPI.user_list"
_USER_REMOVE = "mammoth.api.data_apps.DataAppsAPI.user_remove"


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


# --- data-app list -----------------------------------------------------


def test_list_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_list(_inv("data-app.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_meta_reports_workspace(fake_service: FakeMammothService) -> None:
    _, meta = data_app_cmd.data_app_list(_inv("data-app.list"))
    assert meta["workspace_id"] == 4
    assert meta["project_id"] is None


# --- data-app get --------------------------------------------------------


def test_get_uses_positional_data_app_id(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_get(_inv("data-app.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"data_app_id": 7})]


def test_get_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_get(_inv("data-app.get"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_get_with_non_integer_id_is_invalid_argument(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_get(_inv("data-app.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_get_returns_programmed_response(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET] = {"id": 7, "name": "App"}
    data, _ = data_app_cmd.data_app_get(_inv("data-app.get", extra_args=["7"]))
    assert data == {"id": 7, "name": "App"}


# --- data-app create -----------------------------------------------------


def test_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_create(_inv("data-app.create"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_forwards_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"name": "My App"}})
    data_app_cmd.data_app_create(_inv("data-app.create", input_file=doc))
    assert fake_service.call_log == [(_CREATE, {"body": {"name": "My App"}})]


# --- data-app update -----------------------------------------------------


def test_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_update(_inv("data-app.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_update(_inv("data-app.update"))
    assert excinfo.value.code == "missing_argument"


def test_update_forwards_id_and_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"name": "New name"}})
    data_app_cmd.data_app_update(_inv("data-app.update", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_UPDATE, {"data_app_id": 7, "body": {"name": "New name"}})
    ]


# --- data-app delete -------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_delete(
            _inv("data-app.delete", extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_delete(_inv("data-app.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"data_app_id": 7})]


def test_delete_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_delete(_inv("data-app.delete", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# --- data-app active-job --------------------------------------------------


def test_active_job_uses_positional_id(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_active_job(_inv("data-app.active-job", extra_args=["7"]))
    assert fake_service.call_log == [(_ACTIVE_JOB, {"data_app_id": 7})]


def test_active_job_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_active_job(_inv("data-app.active-job"))
    assert excinfo.value.code == "missing_argument"


# --- data-app job ----------------------------------------------------------


def test_job_uses_both_positionals(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_job(_inv("data-app.job", extra_args=["7", "42"]))
    assert fake_service.call_log == [(_JOB, {"data_app_id": 7, "job_id": 42})]


def test_job_without_job_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_job(_inv("data-app.job", extra_args=["7"]))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_job_without_any_positional_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_job(_inv("data-app.job"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_job_with_non_integer_job_id_is_invalid_argument(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_job(_inv("data-app.job", extra_args=["7", "abc"]))
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


# --- data-app pipeline-changes ----------------------------------------------


def test_pipeline_changes_uses_positional_id(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_pipeline_changes(
        _inv("data-app.pipeline-changes", extra_args=["7"])
    )
    assert fake_service.call_log == [(_PIPELINE_CHANGES, {"data_app_id": 7})]


def test_pipeline_changes_without_id_is_usage_error(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_pipeline_changes(_inv("data-app.pipeline-changes"))
    assert excinfo.value.code == "missing_argument"


# --- data-app share ----------------------------------------------------------


def test_share_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_share(_inv("data-app.share", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_share_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_share(_inv("data-app.share"))
    assert excinfo.value.code == "missing_argument"


def test_share_forwards_id_and_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"email": "a@b.com", "role": "viewer"}})
    data_app_cmd.data_app_share(_inv("data-app.share", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_SHARE, {"data_app_id": 7, "body": {"email": "a@b.com", "role": "viewer"}})
    ]


# --- data-app upload ---------------------------------------------------------


def test_upload_requires_file(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_upload(_inv("data-app.upload", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_upload_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_upload(_inv("data-app.upload"))
    assert excinfo.value.code == "missing_argument"


def test_upload_forwards_file_only(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"file": "/tmp/data.csv"})
    data_app_cmd.data_app_upload(_inv("data-app.upload", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_UPLOAD, {"data_app_id": 7, "file": "/tmp/data.csv"})]


def test_upload_forwards_append_to_ds_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"file": "/tmp/data.csv", "append_to_ds_id": 9})
    data_app_cmd.data_app_upload(_inv("data-app.upload", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_UPLOAD, {"data_app_id": 7, "file": "/tmp/data.csv", "append_to_ds_id": 9})
    ]


# --- data-app user list --------------------------------------------------


def test_user_list_uses_positional_id(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_user_list(_inv("data-app.user.list", extra_args=["7"]))
    assert fake_service.call_log == [(_USER_LIST, {"data_app_id": 7})]


def test_user_list_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_user_list(_inv("data-app.user.list"))
    assert excinfo.value.code == "missing_argument"


# --- data-app user remove ---------------------------------------------------


def test_user_remove_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_user_remove(
            _inv(
                "data-app.user.remove",
                extra_args=["7", "a@b.com"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_remove_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    data_app_cmd.data_app_user_remove(
        _inv("data-app.user.remove", extra_args=["7", "a@b.com"], yes=True)
    )
    assert fake_service.call_log == [
        (_USER_REMOVE, {"data_app_id": 7, "email": "a@b.com"})
    ]


def test_user_remove_without_email_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_user_remove(
            _inv("data-app.user.remove", extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_user_remove_without_any_positional_is_usage_error(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        data_app_cmd.data_app_user_remove(_inv("data-app.user.remove", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []
