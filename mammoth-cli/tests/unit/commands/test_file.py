"""Unit tests for the ``file`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import file as file_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.files.FilesAPI.list"
_GET = "mammoth.api.files.FilesAPI.get"
_UPDATE = "mammoth.api.files.FilesAPI.update"
_SET_PASSWORD = "mammoth.api.files.FilesAPI.set_password"
_EXTRACT_SHEETS = "mammoth.api.files.FilesAPI.extract_sheets"
_DELETE = "mammoth.api.files.FilesAPI.delete"
_BULK_DELETE = "mammoth.api.files.FilesAPI.bulk_delete"
_UPLOAD = "mammoth.api.files.FilesAPI.upload"
_UPLOAD_FOLDER = "mammoth.api.files.FilesAPI.upload_folder"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_list_with_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    file_cmd.file_list(_inv("file.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"limit": 10, "offset": 5, "names": ["a.csv"], "statuses": ["ready"]}),
        encoding="utf-8",
    )
    file_cmd.file_list(_inv("file.list", input_file=str(doc)))
    assert fake_service.call_log == [
        (_LIST, {"limit": 10, "offset": 5, "names": ["a.csv"], "statuses": ["ready"]})
    ]


def test_get_uses_positional_file_id(fake_service: FakeMammothService) -> None:
    file_cmd.file_get(_inv("file.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"file_id": 7})]


def test_get_without_file_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_get(_inv("file.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_file_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_get(_inv("file.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"


def test_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"fields": "id,name"}), encoding="utf-8")
    file_cmd.file_get(_inv("file.get", extra_args=["7"], input_file=str(doc)))
    assert fake_service.call_log == [(_GET, {"file_id": 7, "fields": "id,name"})]


def test_update_requires_patch_request(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_update(_inv("file.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_patch_request(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    patch_request = {"patch": [{"op": "replace", "path": "password", "value": "secret"}]}
    doc.write_text(json.dumps({"patch_request": patch_request}), encoding="utf-8")
    file_cmd.file_update(_inv("file.update", extra_args=["7"], input_file=str(doc)))
    assert fake_service.call_log == [(_UPDATE, {"file_id": 7, "patch_request": patch_request})]


def test_set_password_requires_password(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_set_password(
            _inv("file.set-password", extra_args=["7"], yes=True, confirm="7")
        )
    assert excinfo.value.code == "missing_field"


def test_set_password_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"password": "s3cret"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_set_password(
            _inv("file.set-password", extra_args=["7"], input_file=str(doc), output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_set_password_target_mismatch(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"password": "s3cret"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_set_password(
            _inv(
                "file.set-password",
                extra_args=["7"],
                input_file=str(doc),
                yes=True,
                confirm="8",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_set_password_proceeds_with_matching_confirm(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"password": "s3cret"}), encoding="utf-8")
    file_cmd.file_set_password(
        _inv("file.set-password", extra_args=["7"], input_file=str(doc), yes=True, confirm="7")
    )
    assert fake_service.call_log == [(_SET_PASSWORD, {"file_id": 7, "password": "s3cret"})]


def test_extract_sheets_requires_sheets(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_extract_sheets(_inv("file.extract-sheets", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_extract_sheets_forwards_optional_flags(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "sheets": ["Sheet1", "Sheet2"],
                "delete_file_after_extract": False,
                "combine_after_extract": True,
            }
        ),
        encoding="utf-8",
    )
    file_cmd.file_extract_sheets(_inv("file.extract-sheets", extra_args=["7"], input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _EXTRACT_SHEETS,
            {
                "file_id": 7,
                "sheets": ["Sheet1", "Sheet2"],
                "delete_file_after_extract": False,
                "combine_after_extract": True,
            },
        )
    ]


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_delete(_inv("file.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    file_cmd.file_delete(_inv("file.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"file_id": 7})]


def test_bulk_delete_requires_file_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_bulk_delete(_inv("file.bulk-delete", yes=True))
    assert excinfo.value.code == "missing_field"


def test_bulk_delete_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"file_ids": [1, 2]}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_bulk_delete(_inv("file.bulk-delete", input_file=str(doc), output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_bulk_delete_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"file_ids": [1, 2]}), encoding="utf-8")
    file_cmd.file_bulk_delete(_inv("file.bulk-delete", input_file=str(doc), yes=True))
    assert fake_service.call_log == [(_BULK_DELETE, {"file_ids": [1, 2]})]


def test_upload_uses_positional_paths(fake_service: FakeMammothService) -> None:
    file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv", "b.csv"]))
    assert fake_service.call_log == [(_UPLOAD, {"files": ["a.csv", "b.csv"]})]


def test_upload_uses_files_input_field_when_no_positional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "files": ["a.csv"],
                "folder_resource_id": "r1",
                "append_to_ds_id": 9,
                "override_target_schema": True,
                "wait_for_completion": False,
                "timeout": 30,
            }
        ),
        encoding="utf-8",
    )
    file_cmd.file_upload(_inv("file.upload", input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _UPLOAD,
            {
                "files": ["a.csv"],
                "folder_resource_id": "r1",
                "append_to_ds_id": 9,
                "override_target_schema": True,
                "wait_for_completion": False,
                "timeout": 30,
            },
        )
    ]


def test_upload_with_no_files_omits_files_kwarg(fake_service: FakeMammothService) -> None:
    file_cmd.file_upload(_inv("file.upload"))
    assert fake_service.call_log == [(_UPLOAD, {})]


def test_upload_reports_ready_dataset(fake_service: FakeMammothService) -> None:
    # The SDK waits and returns the new dataset id as a bare int; the handler
    # labels it so the output reads as a finished dataset, not a raw number.
    fake_service.responses[_UPLOAD] = 303694
    data, _ = file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv"]))
    assert data == {"status": "ready", "dataset_ids": [303694], "dataset_id": 303694}


def test_upload_reports_multiple_dataset_ids(fake_service: FakeMammothService) -> None:
    fake_service.responses[_UPLOAD] = [11, 22]
    data, _ = file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv", "b.csv"]))
    assert data == {"status": "ready", "dataset_ids": [11, 22]}


def test_upload_without_wait_returns_raw_handle(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # With wait_for_completion=false the SDK returns a bare job id; the handler
    # passes it through unchanged rather than claiming a ready dataset.
    fake_service.responses[_UPLOAD] = 99
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"files": ["a.csv"], "wait_for_completion": False}), encoding="utf-8"
    )
    data, _ = file_cmd.file_upload(_inv("file.upload", input_file=str(doc)))
    assert data == 99


def test_upload_folder_requires_folder_path(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_upload_folder(_inv("file.upload-folder"))
    assert excinfo.value.code == "missing_argument"


def test_upload_folder_uses_positional_path(fake_service: FakeMammothService) -> None:
    file_cmd.file_upload_folder(_inv("file.upload-folder", extra_args=["/data/in"]))
    assert fake_service.call_log == [(_UPLOAD_FOLDER, {"folder_path": "/data/in"})]


def test_upload_folder_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"folder_path": "/data/in", "folder_resource_id": "r1", "timeout": 60}),
        encoding="utf-8",
    )
    file_cmd.file_upload_folder(_inv("file.upload-folder", input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _UPLOAD_FOLDER,
            {"folder_path": "/data/in", "folder_resource_id": "r1", "timeout": 60},
        )
    ]
