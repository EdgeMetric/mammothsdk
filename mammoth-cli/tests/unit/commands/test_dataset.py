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
_BULK_UPDATE = "mammoth.api.datasets.DatasetsAPI.bulk_update"
_UPDATE = "mammoth.api.datasets.DatasetsAPI.update"
_TRASH_LIST = "mammoth.api.trash.TrashAPI.list"
_COLUMN_STATS = "mammoth.api.datasets.DatasetsAPI.column_stats"
_DEFINITION_LIST = "mammoth.api.datasets.DatasetsAPI.list_definitions"
_DEFINITION_ADD = "mammoth.api.datasets.DatasetsAPI.add_definition"
_DEFINITION_REMOVE = "mammoth.api.datasets.DatasetsAPI.remove_definition"


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


def _hit(project_id: int, object_id: int, name: str) -> dict[str, object]:
    return {"project_id": project_id, "object_id": object_id, "name": name}


def test_find_without_project_searches_every_visible_project(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [
        {"id": 1, "name": "P1"},
        {"id": 2, "name": "P2"},
    ]
    fake_service.responses[_SEARCH] = {
        "resources": [_hit(1, 10, "Sales Q1"), _hit(2, 10, "Sales Q1"), _hit(2, 11, "Other")],
        "has_more": False,
    }
    result, meta = dataset_cmd.dataset_find(_inv("dataset.find", extra_args=["sales"]))
    assert result["projects_searched"] == 2
    assert result["matches"] == [
        {"project_id": 1, "project_name": "P1", "id": 10, "name": "Sales Q1", "source": "unknown"},
        {"project_id": 2, "project_name": "P2", "id": 10, "name": "Sales Q1", "source": "unknown"},
    ]
    assert "list_all_projects" in fake_service.calls
    assert [symbol for symbol, _ in fake_service.call_log] == [_SEARCH]
    assert meta["project_id"] is None


def test_find_matches_are_case_insensitive(fake_service: FakeMammothService) -> None:
    fake_service.projects = [{"id": 1, "name": "P1"}]
    fake_service.responses[_SEARCH] = {
        "resources": [_hit(1, 10, "SALES Q1")],
        "has_more": False,
    }
    result, _meta = dataset_cmd.dataset_find(_inv("dataset.find", extra_args=["sales"]))
    assert [m["id"] for m in result["matches"]] == [10]


def test_find_with_project_puts_its_own_matches_first_and_marks_them(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [{"id": 1, "name": "P1"}, {"id": 42, "name": "P42"}]
    fake_service.responses[_SEARCH] = {
        "resources": [_hit(1, 9, "Sales 2023"), _hit(42, 10, "Sales Q1")],
        "has_more": False,
    }
    result, meta = dataset_cmd.dataset_find(_inv("dataset.find", project=42, extra_args=["sales"]))
    assert result["projects_searched"] == 2
    assert result["matches"] == [
        {
            "project_id": 42,
            "project_name": "P42",
            "id": 10,
            "name": "Sales Q1",
            "source": "unknown",
            "in_project": True,
        },
        {
            "project_id": 1,
            "project_name": "P1",
            "id": 9,
            "name": "Sales 2023",
            "source": "unknown",
            "in_project": False,
        },
    ]
    assert [symbol for symbol, _ in fake_service.call_log] == [_SEARCH]
    assert meta["project_id"] == 42


def _trashed(object_id: int, name: str) -> dict[str, object]:
    return {
        "id": object_id,
        "type": "dataset",
        "name": name,
        "project_id": 42,
        "trashed_at": "2026-10-02T14:37:18",
        "trashed_by": {"id": 13, "name": "Gaurav"},
        "days_until_purge": 22,
    }


def test_find_with_no_live_match_reads_the_trash_and_offers_restore(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [{"id": 42, "name": "P42"}]
    fake_service.responses[_SEARCH] = {"resources": [], "has_more": False}
    fake_service.responses[_TRASH_LIST] = {"items": [_trashed(451, "Late delivery log")]}

    result, _meta = dataset_cmd.dataset_find(
        _inv("dataset.find", project=42, extra_args=["Late delivery log"])
    )

    assert result["matches"] == []
    assert result["trashed_matches"] == [
        {
            "id": 451,
            "name": "Late delivery log",
            "trashed_at": "2026-10-02T14:37:18",
            "trashed_by": "Gaurav",
            "days_until_purge": 22,
        }
    ]
    assert "in this project's trash" in result["note"]
    assert "mammoth dataset restore 451" in result["note"]
    trash_calls = [kw for symbol, kw in fake_service.call_log if symbol == _TRASH_LIST]
    assert trash_calls == [
        {"project_id": 42, "type": "dataset", "q": "late delivery log", "limit": 5}
    ]


def test_a_trashed_name_that_does_not_match_is_left_out(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [{"id": 42, "name": "P42"}]
    fake_service.responses[_SEARCH] = {"resources": [], "has_more": False}
    fake_service.responses[_TRASH_LIST] = {"items": [_trashed(9, "Delivery log late")]}

    result, _meta = dataset_cmd.dataset_find(
        _inv("dataset.find", project=42, extra_args=["late delivery"])
    )

    assert "trashed_matches" not in result


def test_find_without_a_project_never_reads_the_trash(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [{"id": 1, "name": "P1"}]
    fake_service.responses[_SEARCH] = {"resources": [], "has_more": False}

    result, _meta = dataset_cmd.dataset_find(_inv("dataset.find", extra_args=["gone"]))

    assert "trashed_matches" not in result
    assert [symbol for symbol, _ in fake_service.call_log] == [_SEARCH]


# -- column-stats -----------------------------------------------------------


def _col(name: str, blank_count: int, blank_pct: float) -> dict[str, object]:
    return {
        "name": name,
        "type": "TEXT",
        "blank_count": blank_count,
        "blank_pct": blank_pct,
        "distinct": 3,
    }


def test_column_stats_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_column_stats(_inv("dataset.column-stats"))
    assert excinfo.value.code == "project_required"
    assert fake_service.call_log == []


def test_column_stats_reads_the_project_in_one_call(fake_service: FakeMammothService) -> None:
    fake_service.responses[_COLUMN_STATS] = {
        "datasets": [
            {"id": 7, "name": "Orders", "rows": 100, "columns": [_col("Region", 0, 0.0)]},
            {
                "id": 5,
                "name": "Customers",
                "rows": 40,
                "columns": [_col("Email", 4, 10.0), _col("Phone", 20, 50.0), _col("Id", 0, 0.0)],
            },
        ]
    }
    result, meta = dataset_cmd.dataset_column_stats(_inv("dataset.column-stats", project=180))

    assert fake_service.call_log == [(_COLUMN_STATS, {"project_id": 180})]
    assert meta["project_id"] == 180
    # The dataset with the worst column comes first; its blank columns worst first.
    assert result["datasets"] == [
        {
            "id": 5,
            "name": "Customers",
            "rows": 40,
            "columns": [_col("Phone", 20, 50.0), _col("Email", 4, 10.0)],
            "complete_columns": 1,
        },
        {"id": 7, "name": "Orders", "rows": 100, "columns": [], "complete_columns": 1},
    ]
    assert result["dataset_count"] == 2
    assert "omitted" not in result
    note = result["note"]
    assert "blank_pct" in note and "last load or pipeline run" in note


def test_column_stats_cuts_a_wide_project_to_the_output_cap(
    fake_service: FakeMammothService,
) -> None:
    columns = [_col(f"Column {i}", i + 1, float(i + 1)) for i in range(20)]
    fake_service.responses[_COLUMN_STATS] = {
        "datasets": [
            {"id": i, "name": f"Source {i}", "rows": 10, "columns": columns} for i in range(17)
        ]
    }
    result, _ = dataset_cmd.dataset_column_stats(_inv("dataset.column-stats", project=180))

    first = result["datasets"][0]
    assert first["columns"][0]["name"] == "Column 19"
    assert len(first["columns"]) == 8 and first["more_columns_with_blanks"] == 12
    assert result["dataset_count"] == 17
    assert result["omitted"] == 17 - len(result["datasets"])
    assert len(json.dumps(result)) < 4000


# -- definitions ------------------------------------------------------------


def _definition(def_id: str, term: str, definition: str) -> dict[str, object]:
    return {
        "id": def_id,
        "term": term,
        "definition": definition,
        "created_by": 3,
        "created_at": "2026-10-11T09:00:00+00:00",
    }


_LATE = _definition("a1b2c3d4", "late", "delivered more than 5 days after shipped_date")
_CHURNED = _definition("e5f6a7b8", "churned", "no order in the last 90 days")


def test_definition_list_reads_the_dataset(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DEFINITION_LIST] = {"dataset_id": 7, "definitions": [_LATE, _CHURNED]}

    result, meta = dataset_cmd.dataset_definition_list(
        _inv("dataset.definition.list", project=180, extra_args=["7"])
    )

    assert fake_service.call_log == [(_DEFINITION_LIST, {"dataset_id": 7, "project_id": 180})]
    assert meta["project_id"] == 180
    assert result == {
        "dataset_id": 7,
        "definitions": [
            {
                "id": "a1b2c3d4",
                "term": "late",
                "definition": "delivered more than 5 days after shipped_date",
            },
            {"id": "e5f6a7b8", "term": "churned", "definition": "no order in the last 90 days"},
        ],
    }


def test_definition_add_saves_the_term_after_the_target_is_confirmed(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DEFINITION_ADD] = {"dataset_id": 7, "definitions": [_CHURNED, _LATE]}
    doc = _write(
        tmp_path,
        {"term": " late ", "definition": "delivered more than 5 days after shipped_date"},
    )

    result, _ = dataset_cmd.dataset_definition_add(
        _inv(
            "dataset.definition.add",
            project=180,
            extra_args=["7"],
            input_file=doc,
            yes=True,
            confirm="7",
        )
    )

    assert fake_service.call_log == [
        (
            _DEFINITION_ADD,
            {
                "dataset_id": 7,
                "term": "late",
                "definition": "delivered more than 5 days after shipped_date",
                "project_id": 180,
            },
        )
    ]
    assert [d["term"] for d in result["definitions"]] == ["churned", "late"]
    assert set(result["definitions"][1]) == {"id", "term", "definition"}


def test_definition_add_asks_before_saving_a_shared_definition(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"term": "late", "definition": "delivered after 5 days"})

    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_definition_add(
            _inv("dataset.definition.add", project=180, extra_args=["7"], input_file=doc)
        )

    assert excinfo.value.code == "confirmation_required"
    # The agent backend reads the target to pass back from this hint.
    assert "--yes --confirm 7" in (excinfo.value.hint or "")
    assert fake_service.call_log == []


@pytest.mark.parametrize(
    "document",
    [
        {"definition": "delivered after 5 days"},
        {"term": "  ", "definition": "delivered after 5 days"},
        {"term": "late", "definition": "x" * 301},
        {"term": "t" * 61, "definition": "delivered after 5 days"},
    ],
)
def test_definition_add_refuses_a_missing_or_oversized_field(
    fake_service: FakeMammothService, tmp_path: Path, document: dict[str, object]
) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_definition_add(
            _inv(
                "dataset.definition.add",
                project=180,
                extra_args=["7"],
                input_file=_write(tmp_path, document),
                yes=True,
                confirm="7",
            )
        )
    assert excinfo.value.code in {"missing_field", "invalid_argument"}
    assert fake_service.call_log == []


def test_definition_remove_deletes_by_id(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DEFINITION_REMOVE] = {"dataset_id": 7, "definitions": [_CHURNED]}

    result, _ = dataset_cmd.dataset_definition_remove(
        _inv("dataset.definition.remove", project=180, extra_args=["7", "a1b2c3d4"], yes=True)
    )

    assert fake_service.call_log == [
        (_DEFINITION_REMOVE, {"dataset_id": 7, "definition_id": "a1b2c3d4", "project_id": 180})
    ]
    assert [d["id"] for d in result["definitions"]] == ["e5f6a7b8"]


def test_definition_remove_needs_yes_without_a_terminal(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_definition_remove(
            _inv(
                "dataset.definition.remove",
                project=180,
                extra_args=["7", "a1b2c3d4"],
                no_input=True,
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_definition_remove_passes_an_unknown_id_error_through(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_DEFINITION_REMOVE] = CliError(
        code="api_error",
        message="Definition not found on this dataset.",
        details={"backend_code": "4DSET077"},
    )

    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_definition_remove(
            _inv("dataset.definition.remove", project=180, extra_args=["7", "zzzz0000"], yes=True)
        )

    assert excinfo.value.details["backend_code"] == "4DSET077"
    assert fake_service.call_log == [
        (_DEFINITION_REMOVE, {"dataset_id": 7, "definition_id": "zzzz0000", "project_id": 180})
    ]


def test_definition_remove_requires_the_definition_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_definition_remove(
            _inv("dataset.definition.remove", project=180, extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# -- refresh ----------------------------------------------------------------


_REFRESH = "mammoth.api.datasets.DatasetsAPI.refresh_from_url"


def test_refresh_sends_the_dataset_and_waits_for_the_job(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_REFRESH] = {"job_id": 88}
    fake_service.job_result = {"status": "completed"}

    result, meta = dataset_cmd.dataset_refresh(
        _inv("dataset.refresh", project=180, extra_args=["7"], yes=True)
    )

    assert fake_service.call_log == [(_REFRESH, {"dataset_id": 7, "project_id": 180})]
    assert "wait_if_job" in fake_service.calls
    assert result == {"dataset_id": 7, "refreshed": True}
    assert meta["project_id"] == 180


def test_refresh_shows_the_servers_reason_for_a_dataset_not_made_from_a_url(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_REFRESH] = CliError(
        code="api_error", message="This dataset cannot be refreshed from this source."
    )

    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_refresh(
            _inv("dataset.refresh", project=180, extra_args=["7"], yes=True)
        )

    assert "cannot be refreshed" in excinfo.value.message
    assert "wait_if_job" not in fake_service.calls


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


def test_get_need_action_with_zero_views_points_at_file_settings_not_view_create(
    fake_service: FakeMammothService,
) -> None:
    # A need_action dataset has no views because it is waiting for a decision;
    # `view create` is not the next step.
    fake_service.responses[_GET] = {"id": 2644, "status": "need_action"}
    fake_service.responses[_VIEW_LIST] = {"dataviews": []}
    result, _meta = dataset_cmd.dataset_get(_inv("dataset.get", project=180, extra_args=["2644"]))
    assert "view create" not in result["hint"]
    assert "mammoth dataset file-settings get 2644" in result["hint"]


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
    # Column names resolve to the ids the route wants through the dataset's schema.
    fake_service.responses[_GET] = {
        "data_schema": [{"c_name": "a", "c_id": "column_a"}, {"c_name": "b", "c_id": "column_b"}]
    }
    dataset_cmd.dataset_batch_data(
        _inv(
            "dataset.batch-data",
            project=180,
            extra_args=["7", "8"],
            input_file=_write(tmp_path, {"limit": 10, "offset": 2, "columns": "a,b"}),
        )
    )
    assert fake_service.call_log == [
        (_GET, {"dataset_id": 7, "project_id": 180}),
        (
            _BATCH_DATA,
            {
                "dataset_id": 7,
                "batch_id": 8,
                "project_id": 180,
                "limit": 10,
                "offset": 2,
                "columns": "column_a,column_b",
            },
        ),
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
    assert fake_service.call_log[:1] == [
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
    assert fake_service.call_log == [
        (_RENAME, {"dataset_id": 7, "name": "New", "project_id": 180, "unique": True})
    ]


def test_rename_to_the_name_it_already_has_is_a_no_op_success(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_RENAME] = CliError(
        code="api_error",
        message="Dataset name is the same as the current name [4DSET008]",
        exit_status=1,
    )
    fake_service.responses[_GET] = {"dataset": {"id": 7, "name": "Same"}}
    input_file = _write(tmp_path, {"name": "Same"})
    data, _ = dataset_cmd.dataset_rename(
        _inv("dataset.rename", project=180, extra_args=["7"], input_file=input_file)
    )
    assert data["name"] == "Same"
    assert data["changed"] is False


def test_rename_error_that_is_not_the_same_name_still_raises(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_RENAME] = CliError(
        code="api_error",
        message="Dataset name is the same as the current name [4DSET008]",
        exit_status=1,
    )
    fake_service.responses[_GET] = {"dataset": {"id": 7, "name": "Other"}}
    input_file = _write(tmp_path, {"name": "Same"})
    with pytest.raises(CliError):
        dataset_cmd.dataset_rename(
            _inv("dataset.rename", project=180, extra_args=["7"], input_file=input_file)
        )


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
    # Preview read, the delete, then the read that confirms the dataset is gone.
    assert fake_service.call_log == [
        (_GET, {"dataset_id": 7, "project_id": 180}),
        (_DELETE, {"dataset_id": 7, "project_id": 180}),
        (_GET, {"dataset_id": 7, "project_id": 180}),
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


def _gone(code: str = "api_error") -> CliError:
    return CliError(
        code=code,
        message="Invalid dataset id",
        exit_status=1,
        details={"backend_code": "4DSET001"},
    )


def _bulk_delete_fake(
    fake_service: FakeMammothService, *, exists: set[int], kept: set[int]
) -> None:
    """Program the get/delete reads: ``exists`` are present before, ``kept`` survive the delete."""
    fake_service.responses[_GET] = lambda log: _bulk_get(log, exists, kept)


def _bulk_get(log: list[tuple[str, dict[str, object]]], exists: set[int], kept: set[int]) -> object:
    dataset_id = log[-1][1]["dataset_id"]
    deleted = any(symbol.endswith("bulk_delete") for symbol, _ in log)
    present = dataset_id in (kept if deleted else exists)
    if not present:
        raise _gone()
    return {"id": dataset_id}


def test_bulk_delete_reports_each_id_as_deleted(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _bulk_delete_fake(fake_service, exists={7, 8}, kept=set())
    doc = _write(tmp_path, {"dataset_ids": [7, 8]})
    data, _ = dataset_cmd.dataset_bulk_delete(
        _inv("dataset.bulk-delete", project=180, yes=True, input_file=doc)
    )
    assert data["results"] == [
        {"dataset_id": 7, "status": "deleted"},
        {"dataset_id": 8, "status": "deleted"},
    ]
    assert data["deleted"] == [7, 8]
    assert not data.get("partial")


def test_bulk_delete_of_a_missing_id_is_not_found_and_partial(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _bulk_delete_fake(fake_service, exists={7}, kept=set())
    doc = _write(tmp_path, {"dataset_ids": [7, 99999]})
    data, _ = dataset_cmd.dataset_bulk_delete(
        _inv("dataset.bulk-delete", project=180, yes=True, input_file=doc)
    )
    assert data["results"] == [
        {"dataset_id": 7, "status": "deleted"},
        {"dataset_id": 99999, "status": "not_found"},
    ]
    assert data["partial"] is True
    sent = [kw for symbol, kw in fake_service.call_log if symbol.endswith("bulk_delete")]
    assert sent[0]["dataset_ids"] == [7]


def test_bulk_delete_of_only_missing_ids_is_resource_not_found(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _bulk_delete_fake(fake_service, exists=set(), kept=set())
    doc = _write(tmp_path, {"dataset_ids": [99999]})
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_bulk_delete(
            _inv("dataset.bulk-delete", project=180, yes=True, input_file=doc)
        )
    assert excinfo.value.code == "resource_not_found"
    assert excinfo.value.exit_status == 5
    assert not [1 for symbol, _ in fake_service.call_log if symbol.endswith("bulk_delete")]


def test_bulk_delete_with_a_survivor_is_partial_with_per_id_status(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _bulk_delete_fake(fake_service, exists={7, 8}, kept={8})
    doc = _write(tmp_path, {"dataset_ids": [7, 8]})
    data, _ = dataset_cmd.dataset_bulk_delete(
        _inv("dataset.bulk-delete", project=180, yes=True, input_file=doc)
    )
    assert [r["status"] for r in data["results"]] == ["deleted", "failed"]
    assert data["partial"] is True
    assert "dataset get 8" in data["results"][1]["detail"]


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


# -- what a create job settles with -----------------------------------------


@pytest.mark.parametrize(
    ("settled", "expected"),
    [
        ({"ds_id": 5}, {"status": "ready", "dataset_id": 5, "job_id": 9}),
        ({"dataset_id": 5}, {"status": "ready", "dataset_id": 5, "job_id": 9}),
        ({"datasource_id": 5}, {"status": "ready", "dataset_id": 5, "job_id": 9}),
        (
            {"datasource_config_id": 7},
            {"status": "scheduled", "datasource_config_id": 7, "job_id": 9},
        ),
        (
            {"files_found": 2, "created": ["a", "b"], "failed": []},
            {"files_found": 2, "created": ["a", "b"], "failed": []},
        ),
    ],
)
def test_created_dataset_reads_every_settled_shape(
    settled: dict[str, object], expected: dict[str, object]
) -> None:
    assert dataset_cmd._created_dataset({"job_id": 9}, settled) == expected


def test_created_dataset_raises_when_the_job_made_nothing() -> None:
    with pytest.raises(CliError) as excinfo:
        dataset_cmd._created_dataset({"job_id": 9}, {"message": "No such file"})
    assert excinfo.value.code == "job_failed"
    assert "No such file" in excinfo.value.message


def test_created_dataset_passes_a_sketch_through() -> None:
    sketch = {"id": 12, "name": "n", "status": "ready"}
    assert dataset_cmd._created_dataset(sketch, sketch) == sketch


# -- delete that the server accepts but does not carry out ----------------------


def test_delete_blocked_by_a_dependent_view_is_not_a_success(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The server acknowledges the delete with a dependency map keyed by the dataset id
    # (view -> column -> tasks) and the dataset is still readable afterwards.
    monkeypatch.setattr("mammoth_cli.services.delete_check.time.sleep", lambda _s: None)
    fake_service.responses[_GET] = {"id": 313432, "name": "orders"}
    fake_service.responses[_DELETE] = {
        "job_id": 9,
        "313432": {"311853": {"column_1": [{"task_id": 5}]}},
    }
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_delete(
            _inv("dataset.delete", project=180, extra_args=["313432"], yes=True)
        )
    error = excinfo.value
    assert error.code == "has_dependents"
    assert error.details["deleted"] is False
    assert "311853" in error.details["dependents"]
    assert error.recovery_commands == ["mammoth view task list 311853"]
    assert "311853" in error.message


def test_delete_that_leaves_the_dataset_without_a_reason_is_not_applied(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("mammoth_cli.services.delete_check.time.sleep", lambda _s: None)
    fake_service.responses[_GET] = {"id": 7}
    with pytest.raises(CliError) as excinfo:
        dataset_cmd.dataset_delete(_inv("dataset.delete", project=180, extra_args=["7"], yes=True))
    assert excinfo.value.code == "delete_not_applied"


def test_delete_succeeds_when_the_dataset_is_gone_afterwards(
    fake_service: FakeMammothService,
) -> None:
    from mammoth_cli.errors.envelope import CODE_RESOURCE_NOT_FOUND, EXIT_NOT_FOUND

    def get(log: list[tuple[str, dict[str, object]]]) -> dict[str, object]:
        if any(symbol == _DELETE for symbol, _ in log):
            raise CliError(code=CODE_RESOURCE_NOT_FOUND, message="gone", exit_status=EXIT_NOT_FOUND)
        return {"id": 7}

    fake_service.responses[_GET] = get  # type: ignore[assignment]
    data, _meta = dataset_cmd.dataset_delete(
        _inv("dataset.delete", project=180, extra_args=["7"], yes=True)
    )
    assert isinstance(data, dict)


def test_delete_succeeds_when_the_get_answers_4dset001_afterwards(
    fake_service: FakeMammothService,
) -> None:
    # Live (2.2.82): the dataset get route answers 400 4DSET001, not 404, for a
    # deleted dataset; the delete is done and must not be reported as api_error.
    def get(log: list[tuple[str, dict[str, object]]]) -> dict[str, object]:
        if any(symbol == _DELETE for symbol, _ in log):
            raise CliError(
                code="api_error",
                message="Invalid dataset id",
                exit_status=1,
                details={"backend_code": "4DSET001"},
            )
        return {"id": 7}

    fake_service.responses[_GET] = get  # type: ignore[assignment]
    data, _meta = dataset_cmd.dataset_delete(
        _inv("dataset.delete", project=180, extra_args=["7"], yes=True)
    )
    assert isinstance(data, dict)


def test_file_settings_update_waits_for_the_reprocess_job_and_names_the_dataset(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_FILE_SETTINGS_UPDATE] = {"job_id": 55}
    fake_service.job_result = {"ds_id": 7, "status": "ready"}
    fake_service.responses["mammoth.api.datasets.DatasetsAPI.get"] = {"id": 7, "name": "wb.csv"}
    doc = tmp_path / "in.json"
    doc.write_text(
        '{"delimiter": ",", "has_header": true, "initial_skip_count": 0, "quotechar": "\\""}',
        encoding="utf-8",
    )
    data, _ = dataset_cmd.dataset_file_settings_update(
        _inv("dataset.file-settings.update", project=180, extra_args=["7"], input_file=str(doc))
    )
    assert fake_service.wait_log == [{"job_id": 55}]
    assert data["status"] == "ready"
    assert data["dataset_name"] == "wb.csv"


def test_delete_names_the_deleted_id_and_lists_nothing(fake_service: FakeMammothService) -> None:
    data, _ = dataset_cmd.dataset_delete(
        _inv("dataset.delete", project=180, extra_args=["7"], yes=True)
    )
    assert data["deleted"] == [7]
    assert all(symbol != "mammoth.api.datasets.DatasetsAPI.list" for symbol in fake_service.calls)


def test_list_total_counts_whole_project_when_page_is_cut(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    rows = [{"id": i, "name": f"d{i}"} for i in range(150)]
    fake_service.responses[_LIST] = {"datasets": rows[:100]}
    fake_service.responses[_LIST_ALL] = {"datasets": rows}
    input_file = _write(tmp_path, {"limit": 100})
    result, _ = dataset_cmd.dataset_list(_inv("dataset.list", project=180, input_file=input_file))
    assert result["more"] is True
    assert result["total"] == 150


def test_list_total_is_free_on_last_page(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST] = {"datasets": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}
    result, _ = dataset_cmd.dataset_list(_inv("dataset.list", project=180))
    assert result["total"] == 2
    assert all(symbol != _LIST_ALL for symbol, _ in fake_service.call_log)


def test_list_names_returns_every_name_in_one_call(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    rows = [{"id": i, "name": f"file_{i}.csv"} for i in range(450)]
    fake_service.responses[_LIST_ALL] = {"datasets": rows}
    input_file = _write(tmp_path, {"names": True})
    result, _ = dataset_cmd.dataset_list(_inv("dataset.list", project=180, input_file=input_file))
    assert result["shown"] == result["total"] == 450
    assert result["datasets"][0] == {"id": 0, "name": "file_0.csv"}
    assert "more" not in result
    assert len(json.dumps(result)) < 50_000


def test_list_names_caps_at_500_and_says_more(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    rows = [{"id": i, "name": f"d{i}"} for i in range(600)]
    fake_service.responses[_LIST_ALL] = {"datasets": rows}
    input_file = _write(tmp_path, {"names": True})
    result, _ = dataset_cmd.dataset_list(_inv("dataset.list", project=180, input_file=input_file))
    assert result["shown"] == 500
    assert result["total"] == 600
    assert result["more"] is True


def test_cut_list_page_points_to_names_true(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    rows = [{"id": i, "name": f"d{i}"} for i in range(150)]
    fake_service.responses[_LIST] = {"datasets": rows[:100]}
    fake_service.responses[_LIST_ALL] = {"datasets": rows}
    input_file = _write(tmp_path, {"limit": 100})
    result, _ = dataset_cmd.dataset_list(_inv("dataset.list", project=180, input_file=input_file))
    assert '"names": true' in result["note"]


def test_last_list_page_does_not_point_to_names_true(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST] = {"datasets": [{"id": 1, "name": "a"}]}
    result, _ = dataset_cmd.dataset_list(_inv("dataset.list", project=180))
    assert "names" not in result["note"]
