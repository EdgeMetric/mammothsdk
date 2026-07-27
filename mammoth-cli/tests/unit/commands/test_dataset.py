"""Unit tests for the ``dataset`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.datasets.DatasetsAPI.list"
_GET = "mammoth.api.datasets.DatasetsAPI.get"
_DATA = "mammoth.api.datasets.DatasetsAPI.get_data"
_FILE_SETTINGS = "mammoth.api.datasets.DatasetsAPI.get_file_settings"
_FILE_SETTINGS_UPDATE = "mammoth.api.datasets.DatasetsAPI.file_settings_update"
_FILE_SETTINGS_UNDO = "mammoth.api.datasets.DatasetsAPI.file_settings_undo"
_CREATE = "mammoth.api.datasets.DatasetsAPI.create"
_CREATE_FROM_PDF = "mammoth.api.datasets.DatasetsAPI.create_from_pdf"
_RENAME = "mammoth.api.datasets.DatasetsAPI.rename"
_TRASH = "mammoth.api.datasets.DatasetsAPI.trash"
_RESTORE = "mammoth.api.datasets.DatasetsAPI.restore"
_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_BULK_DELETE = "mammoth.api.datasets.DatasetsAPI.bulk_delete"
_BULK_UPDATE = "mammoth.api.datasets.DatasetsAPI.bulk_update"
_UPDATE = "mammoth.api.datasets.DatasetsAPI.update"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# -- list -----------------------------------------------------------------


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_list(_inv("dataset.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project_and_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"limit": 10, "sort": "(name:asc)"})
    dataset_cmd.dataset_list(_inv("dataset.list", project=180, input_file=input_file))
    assert fake_service.call_log == [
        (_LIST, {"project_id": 180, "limit": 10, "sort": "(name:asc)"})
    ]


# -- get --------------------------------------------------------------------


def test_get_uses_positional_dataset_id(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"dataset_id": 7, "project_id": 180})]


def test_get_without_dataset_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_get(_inv("dataset.get", project=180))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_dataset_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


# -- data ---------------------------------------------------------------


def test_data_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_data(_inv("dataset.data", project=180))
    assert excinfo.value.code == "missing_argument"


def test_data_forwards_timeout_and_poll_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"timeout": 60, "poll_interval": 1})
    dataset_cmd.dataset_data(
        _inv("dataset.data", project=180, extra_args=["7"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (_DATA, {"dataset_id": 7, "project_id": 180, "timeout": 60, "poll_interval": 1})
    ]


# -- file-settings --------------------------------------------------------


def test_file_settings_passes_dataset_and_project(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_file_settings(
        _inv("dataset.file-settings.get", project=180, extra_args=["7"])
    )
    assert fake_service.call_log == [(_FILE_SETTINGS, {"dataset_id": 7, "project_id": 180})]


def test_file_settings_update_requires_delimiter(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_file_settings_update(
            _inv("dataset.file-settings.update", project=180, extra_args=["7"])
        )
    assert excinfo.value.code == "missing_field"


def test_file_settings_update_forwards_required_and_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path,
        {
            "delimiter": ",",
            "has_header": True,
            "initial_skip_count": 0,
            "quotechar": '"',
            "date_format": "US",
        },
    )
    dataset_cmd.dataset_file_settings_update(
        _inv(
            "dataset.file-settings.update",
            project=180,
            extra_args=["7"],
            input_file=input_file,
        )
    )
    assert fake_service.call_log == [
        (
            _FILE_SETTINGS_UPDATE,
            {
                "dataset_id": 7,
                "delimiter": ",",
                "has_header": True,
                "initial_skip_count": 0,
                "quotechar": '"',
                "project_id": 180,
                "date_format": "US",
            },
        )
    ]


def test_file_settings_undo_blocked_without_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_file_settings_undo(
            _inv("dataset.file-settings.undo", project=180, extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_file_settings_undo_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_file_settings_undo(
        _inv("dataset.file-settings.undo", project=180, extra_args=["7"], yes=True)
    )
    assert fake_service.call_log == [(_FILE_SETTINGS_UNDO, {"dataset_id": 7, "project_id": 180})]


# -- create ---------------------------------------------------------------


def test_create_requires_dataset_spec(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"ds_creation_type": "sketch"})
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_create(_inv("dataset.create", project=180, input_file=input_file))
    assert excinfo.value.code == "missing_field"


def test_create_forwards_folder_resource_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path,
        {
            "dataset_spec": {"foo": "bar"},
            "ds_creation_type": "sketch",
            "folder_resource_id": "r1",
        },
    )
    dataset_cmd.dataset_create(_inv("dataset.create", project=180, input_file=input_file))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "dataset_spec": {"foo": "bar"},
                "ds_creation_type": "sketch",
                "project_id": 180,
                "folder_resource_id": "r1",
            },
        )
    ]


def test_create_waits_and_reports_dataset_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # ``datasets.create`` returns a bare job handle; the handler must block on it
    # and report the finished dataset id, not the job id the caller would poll.
    fake_service.responses[_CREATE] = {"job_id": 14}
    fake_service.job_result = {"ds_id": 303686}
    input_file = _write(
        tmp_path, {"dataset_spec": {"url": "x"}, "ds_creation_type": "weburl"}
    )
    data, _ = dataset_cmd.dataset_create(
        _inv("dataset.create", project=180, input_file=input_file)
    )
    assert "wait_if_job" in fake_service.calls
    assert data == {"status": "ready", "dataset_id": 303686, "job_id": 14}


# -- create-from-pdf --------------------------------------------------------


def test_create_from_pdf_requires_file_name(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_create_from_pdf(
            _inv("dataset.create-from-pdf", project=180, extra_args=["9"], input_file=input_file)
        )
    assert excinfo.value.code == "missing_field"


def test_create_from_pdf_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path,
        {
            "file_name": "tables.pdf",
            "table_list": [0, 1],
            "delete_file_after_extract": True,
        },
    )
    dataset_cmd.dataset_create_from_pdf(
        _inv("dataset.create-from-pdf", project=180, extra_args=["9"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _CREATE_FROM_PDF,
            {
                "file_object_id": 9,
                "file_name": "tables.pdf",
                "project_id": 180,
                "table_list": [0, 1],
                "delete_file_after_extract": True,
            },
        )
    ]


# -- rename -----------------------------------------------------------------


def test_rename_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_rename(_inv("dataset.rename", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_rename_forwards_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"name": "New"})
    dataset_cmd.dataset_rename(
        _inv("dataset.rename", project=180, extra_args=["7"], input_file=input_file)
    )
    assert fake_service.call_log == [(_RENAME, {"dataset_id": 7, "name": "New", "project_id": 180})]


# -- trash / restore --------------------------------------------------------


def test_trash_passes_dataset_and_project(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_trash(_inv("dataset.trash", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_TRASH, {"dataset_id": 7, "project_id": 180})]


def test_restore_passes_dataset_and_project(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_restore(_inv("dataset.restore", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_RESTORE, {"dataset_id": 7, "project_id": 180})]


# -- delete -------------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_delete(
            _inv("dataset.delete", project=180, extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_delete(_inv("dataset.delete", project=180, extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"dataset_id": 7, "project_id": 180})]


# -- bulk-delete --------------------------------------------------------


def test_bulk_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_delete(_inv("dataset.bulk-delete", project=180, output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_bulk_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_bulk_delete(_inv("dataset.bulk-delete", project=180, yes=True))
    assert fake_service.call_log == [(_BULK_DELETE, {"project_id": 180})]


# -- bulk-update --------------------------------------------------------


def test_bulk_update_requires_patch_data(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_update(
            _inv("dataset.bulk-update", project=180, yes=True, confirm="180")
        )
    assert excinfo.value.code == "missing_field"


def test_bulk_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"patch_data": {"op": "noop"}})
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_update(
            _inv("dataset.bulk-update", project=180, input_file=input_file, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_bulk_update_blocked_on_target_mismatch(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"patch_data": {"op": "noop"}})
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_update(
            _inv(
                "dataset.bulk-update",
                project=180,
                input_file=input_file,
                yes=True,
                confirm="999",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_bulk_update_proceeds_with_matching_confirm(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"patch_data": {"op": "noop"}})
    dataset_cmd.dataset_bulk_update(
        _inv(
            "dataset.bulk-update",
            project=180,
            input_file=input_file,
            yes=True,
            confirm="180",
        )
    )
    assert fake_service.call_log == [
        (_BULK_UPDATE, {"patch_data": {"op": "noop"}, "project_id": 180})
    ]


# -- update -------------------------------------------------------------


def test_update_requires_patch_data(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_update(_inv("dataset.update", project=180, yes=True, confirm="180"))
    assert excinfo.value.code == "missing_field"


def test_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path, {"patch_data": [{"op": "rename_dataset", "path": "/1", "value": {}}]}
    )
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_update(
            _inv("dataset.update", project=180, input_file=input_file, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_proceeds_with_matching_confirm(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path, {"patch_data": [{"op": "rename_dataset", "path": "/1", "value": {}}]}
    )
    dataset_cmd.dataset_update(
        _inv(
            "dataset.update",
            project=180,
            input_file=input_file,
            yes=True,
            confirm="180",
        )
    )
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "patch_data": [{"op": "rename_dataset", "path": "/1", "value": {}}],
                "project_id": 180,
            },
        )
    ]
