"""Unit tests for the ``dataset`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.listing import DATASET_ROW_FIELDS
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.datasets.DatasetsAPI.list"
_LIST_ALL = "mammoth.api.datasets.DatasetsAPI.list_all"
_GET = "mammoth.api.datasets.DatasetsAPI.get"
_SEARCH = "mammoth.api.browse.BrowseAPI.resources_search"
_VIEW_LIST = "mammoth.api.dataviews.DataviewsAPI.list"
_DATA = "mammoth.api.datasets.DatasetsAPI.get_data"
_BATCH_DATA = "mammoth.api.datasets.DatasetsAPI.get_batch_data"
_FILE_SETTINGS = "mammoth.api.datasets.DatasetsAPI.get_file_settings"
_FILE_SETTINGS_UPDATE = "mammoth.api.datasets.DatasetsAPI.file_settings_update"
_FILE_SETTINGS_UNDO = "mammoth.api.datasets.DatasetsAPI.file_settings_undo"
_BROKEN_ROWS = "mammoth.api.datasets.DatasetsAPI.get_unstructured_rows"
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


# -- find -------------------------------------------------------------------


def test_find_requires_name_substring(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_find(_inv("dataset.find"))
    assert excinfo.value.code == "missing_argument"


def test_find_without_project_searches_every_visible_project(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [
        {"id": 1, "name": "P1"},
        {"id": 2, "name": "P2"},
    ]
    fake_service.responses[_LIST_ALL] = {
        "datasets": [{"id": 10, "name": "Sales Q1"}, {"id": 11, "name": "Other"}]
    }
    fake_service.responses[_SEARCH] = {
        "resources": [{"project_id": 1}, {"project_id": 2}],
        "has_more": False,
    }
    result, meta = dataset_cmd.dataset_find(_inv("dataset.find", extra_args=["sales"]))
    assert result["projects_searched"] == 2
    assert result["matches"] == [
        {"project_id": 1, "project_name": "P1", "id": 10, "name": "Sales Q1", "source": "unknown"},
        {"project_id": 2, "project_name": "P2", "id": 10, "name": "Sales Q1", "source": "unknown"},
    ]
    assert "list_all_projects" in fake_service.calls
    assert [symbol for symbol, _ in fake_service.call_log] == [_SEARCH, _LIST_ALL, _LIST_ALL]
    assert fake_service.call_log[1:] == [
        (_LIST_ALL, {"project_id": 1, "fields": DATASET_ROW_FIELDS}),
        (_LIST_ALL, {"project_id": 2, "fields": DATASET_ROW_FIELDS}),
    ]
    assert meta["project_id"] is None


def test_find_matches_are_case_insensitive(fake_service: FakeMammothService) -> None:
    fake_service.projects = [{"id": 1, "name": "P1"}]
    fake_service.responses[_LIST_ALL] = {"datasets": [{"id": 10, "name": "SALES Q1"}]}
    fake_service.responses[_SEARCH] = {"resources": [{"project_id": 1}], "has_more": False}
    result, _meta = dataset_cmd.dataset_find(_inv("dataset.find", extra_args=["sales"]))
    assert [m["id"] for m in result["matches"]] == [10]


def test_find_with_project_restricts_to_one_project(fake_service: FakeMammothService) -> None:
    fake_service.projects = [{"id": 1, "name": "P1"}, {"id": 42, "name": "P42"}]
    fake_service.responses[_LIST_ALL] = {"datasets": [{"id": 10, "name": "Sales Q1"}]}
    result, meta = dataset_cmd.dataset_find(_inv("dataset.find", project=42, extra_args=["sales"]))
    assert result["projects_searched"] == 1
    assert result["matches"] == [
        {
            "project_id": 42,
            "project_name": "P42",
            "id": 10,
            "name": "Sales Q1",
            "source": "unknown",
        }
    ]
    assert fake_service.call_log == [(_LIST_ALL, {"project_id": 42, "fields": DATASET_ROW_FIELDS})]
    assert meta["project_id"] == 42


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
        (
            _LIST,
            {"project_id": 180, "limit": 10, "sort": "(name:asc)", "fields": DATASET_ROW_FIELDS},
        )
    ]


# -- get --------------------------------------------------------------------


def test_get_uses_positional_dataset_id(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["7"]))
    assert fake_service.call_log == [
        (_GET, {"dataset_id": 7, "project_id": 180}),
        (_VIEW_LIST, {"dataset_id": 7, "project_id": 180}),
    ]


def test_get_without_dataset_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_get(_inv("dataset.get", project=180))
    assert excinfo.value.code == "missing_argument"


def test_get_strips_file_ingestion_automation_possible_flag(
    fake_service: FakeMammothService,
) -> None:
    """RCA evidence (T1-R-01/T1-R-07): automation_possible is CSV-ingestion
    metadata (api/api/file/unprocessed.py) about whether the header-parsing
    pipeline can auto-process this upload -- unrelated to whether the
    dataset can be put on a scheduled refresh. An agent reading it next to a
    'no refreshable source' claim misreads it as contradicting that claim.
    It must not appear in dataset get's output.
    """
    fake_service.responses[_GET] = {
        "id": 7,
        "additional_info": {"all_data_backup": {"PARAMS": {"automation_possible": True}}},
    }
    data, _meta = dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["7"]))
    all_data_params = data["additional_info"]["all_data_backup"]["PARAMS"]
    assert "automation_possible" not in all_data_params


def test_get_names_the_export_that_writes_into_this_dataset(
    fake_service: FakeMammothService,
) -> None:
    # T1-O-10: a dataset built by a recurring `view export dataset` carries its
    # source view/export ids in additional_info; name the export and the exact
    # command that stops it instead of leaving that as raw additional_info.
    fake_service.responses[_GET] = {
        "id": 2625,
        "additional_info": {"DATAVIEW_ID": 3229, "TRIGGER_ID": 225},
    }
    result, _meta = dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["2625"]))
    assert "mammoth view export delete 3229 225" in result["hint"]


def test_get_without_additional_info_has_no_hint(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET] = {"id": 7}
    fake_service.responses[_VIEW_LIST] = {"dataviews": [{"id": 1}]}
    result, _meta = dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["7"]))
    assert "hint" not in result
    assert result["view_count"] == 1


def test_get_hints_view_create_when_dataset_has_zero_views(
    fake_service: FakeMammothService,
) -> None:
    # T1-I-13: an agent that only reads dataset-level metadata has no signal
    # nothing is queryable yet; a corrected dataset with zero views is
    # invisible to every downstream Mammoth feature (and to the grader).
    fake_service.responses[_GET] = {"id": 2643}
    fake_service.responses[_VIEW_LIST] = {"dataviews": []}
    result, _meta = dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["2643"]))
    assert result["view_count"] == 0
    assert "mammoth view create 2643" in result["hint"]


def test_batch_data_rejects_invalid_paging_before_service(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    for payload in ({"limit": 101}, {"offset": -1}):
        with pytest.raises(CliError):
            dataset_cmd.dataset_batch_data(
                _inv(
                    "dataset.batch-data",
                    project=180,
                    extra_args=["7", "8"],
                    input_file=_write(tmp_path, payload),
                )
            )
    assert fake_service.call_log == []


def test_batch_data_forwards_ids_and_paging(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    dataset_cmd.dataset_batch_data(
        _inv(
            "dataset.batch-data",
            project=180,
            extra_args=["7", "8"],
            input_file=_write(tmp_path, {"limit": 10, "offset": 2, "columns": "a,b"}),
        )
    )
    assert fake_service.call_log == [
        (
            _BATCH_DATA,
            {
                "dataset_id": 7,
                "batch_id": 8,
                "project_id": 180,
                "limit": 10,
                "offset": 2,
                "columns": "a,b",
            },
        )
    ]


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


def test_file_settings_of_an_upload_say_how_the_next_file_joins(
    fake_service: FakeMammothService,
) -> None:
    """Asked to keep Power BI on the latest data of an uploaded CSV, the agent read
    its file settings, concluded nothing new could ever arrive, and stopped
    without publishing (eval T1-O-08)."""
    fake_service.responses[_FILE_SETTINGS] = {"info": {"delimiter": ",", "has_header": True}}

    data, _ = dataset_cmd.dataset_file_settings(
        _inv("dataset.file-settings.get", project=180, extra_args=["7"])
    )

    (path,) = data["new_data"]
    assert path["dataset_id"] == 7
    assert "append_to_ds_id" in path["how"]


def test_broken_rows_list_reads_the_dataset_s_unparsed_lines(
    fake_service: FakeMammothService,
) -> None:
    dataset_cmd.dataset_broken_rows(_inv("dataset.broken-rows.list", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_BROKEN_ROWS, {"dataset_id": 7, "project_id": 180})]


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
    input_file = _write(tmp_path, {"dataset_spec": {"url": "x"}, "ds_creation_type": "weburl"})
    data, _ = dataset_cmd.dataset_create(_inv("dataset.create", project=180, input_file=input_file))
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
    # The preview read that builds the confirmation message is a read, not a
    # mutation; only the delete call itself must be withheld.
    assert fake_service.call_log == [(_GET, {"dataset_id": 7, "project_id": 180})]


def test_delete_blocked_without_confirmation_names_the_writing_export(
    fake_service: FakeMammothService,
) -> None:
    # T1-O-10: the confirmation preview must name the export writing into this
    # dataset and the command that stops it, not just "delete dataset 2625".
    fake_service.responses[_GET] = {
        "id": 2625,
        "additional_info": {"DATAVIEW_ID": 3229, "TRIGGER_ID": 225},
    }
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_delete(
            _inv("dataset.delete", project=180, extra_args=["2625"], output="json")
        )
    assert "mammoth view export delete 3229 225" in excinfo.value.message


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    dataset_cmd.dataset_delete(_inv("dataset.delete", project=180, extra_args=["7"], yes=True))
    assert fake_service.call_log == [
        (_GET, {"dataset_id": 7, "project_id": 180}),
        (_DELETE, {"dataset_id": 7, "project_id": 180}),
    ]


# -- bulk-delete --------------------------------------------------------


def test_bulk_delete_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"dataset_ids": [7, 8]})
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_delete(
            _inv("dataset.bulk-delete", project=180, output="json", input_file=doc)
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_bulk_delete_requires_explicit_ids(fake_service: FakeMammothService) -> None:
    # The route has no delete-all form; never confirm an implicit whole-project delete.
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_delete(_inv("dataset.bulk-delete", project=180, yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_bulk_delete_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"dataset_ids": [7, 8]})
    dataset_cmd.dataset_bulk_delete(
        _inv("dataset.bulk-delete", project=180, yes=True, input_file=doc)
    )
    assert fake_service.call_log == [(_BULK_DELETE, {"dataset_ids": [7, 8], "project_id": 180})]


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


def test_update_rejects_missing_patch_data_without_dispatch(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_update(_inv("dataset.update", project=180, yes=True, confirm="180"))
    assert excinfo.value.code == "unsupported_contract"
    assert fake_service.call_log == []


def test_update_rejects_raw_patch_even_with_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path, {"patch_data": [{"op": "rename_dataset", "path": "/1", "value": {}}]}
    )
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_update(
            _inv(
                "dataset.update",
                project=180,
                input_file=input_file,
                output="json",
                yes=True,
                confirm="180",
            )
        )
    assert excinfo.value.code == "unsupported_contract"
    assert excinfo.value.details["blocker"] == "B07 DATASET_PATCH_UNTYPED"
    assert excinfo.value.details["typed_alternatives"] == [
        "dataset.rename",
        "dataset.file-settings.update",
    ]
    assert fake_service.call_log == []
