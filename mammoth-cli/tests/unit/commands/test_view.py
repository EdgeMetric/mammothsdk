"""Unit tests for the sub-client-backed ``view`` command handlers."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_VIEW_LIST = "mammoth.api.dataviews.DataviewsAPI.list"
_DATASETS_LIST_ALL = "mammoth.api.datasets.DatasetsAPI.list_all"
_ACTIVE_USER_LIST = "mammoth.api.dataviews.DataviewsAPI.active_users"
_ACTIVE_USER_MARK = "mammoth.api.dataviews.DataviewsAPI.mark_active"
_BULK_DELETE = "mammoth.api.dataviews.DataviewsAPI.bulk_delete"
_PARAMETER_CONTEXT = "mammoth.api.dataviews.DataviewsAPI.parameter_context"
_PREVIEW = "mammoth.api.dataviews.DataviewsAPI.preview"
_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_RESTORE = "mammoth.api.dataviews.DataviewsAPI.restore"
_TRASH = "mammoth.api.dataviews.DataviewsAPI.trash"
_UPDATE = "mammoth.api.dataviews.DataviewsAPI.update"
_DATA_GET = "mammoth.api.dataviews.DataviewsAPI.get_data"
_DATA_QUERY = "mammoth.api.dataviews.DataviewsAPI.query_data"
_DATA_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"
_EXPORTABLE_GET = "mammoth.api.dataviews.DataviewsAPI.get_exportable_config"
_EXPORTABLE_APPLY = "mammoth.api.dataviews.DataviewsAPI.apply_exportable_config"
_FIND_DATASET = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_CF_CREATE = "mammoth.api.dataviews.DataviewsAPI.conditional_format_create"
_CF_DELETE_ALL = "mammoth.api.dataviews.DataviewsAPI.conditional_format_delete"
_CF_LIST = "mammoth.api.dataviews.DataviewsAPI.conditional_format_list"
_CF_UPDATE = "mammoth.api.dataviews.DataviewsAPI.conditional_format_update"

_CKPT_CREATE = "mammoth.api.checkpoints.CheckpointsAPI.create"
_CKPT_DELETE = "mammoth.api.checkpoints.CheckpointsAPI.delete"
_CKPT_GET = "mammoth.api.checkpoints.CheckpointsAPI.get"
_CKPT_LIST = "mammoth.api.checkpoints.CheckpointsAPI.list"
_CKPT_UPDATE = "mammoth.api.checkpoints.CheckpointsAPI.update"

_DC_CREATE = "mammoth.api.data_checks.DataChecksAPI.create"
_DC_DELETE = "mammoth.api.data_checks.DataChecksAPI.delete"
_DC_GET = "mammoth.api.data_checks.DataChecksAPI.get"
_DC_LIST = "mammoth.api.data_checks.DataChecksAPI.list"
_DC_UPDATE = "mammoth.api.data_checks.DataChecksAPI.update"

_DERIV_CREATE = "mammoth.api.derivatives.DerivativesAPI.create"
_DERIV_DATA = "mammoth.api.derivatives.DerivativesAPI.data"
_DERIV_DELETE = "mammoth.api.derivatives.DerivativesAPI.delete"
_DERIV_LIST = "mammoth.api.derivatives.DerivativesAPI.list"
_DERIV_UPDATE = "mammoth.api.derivatives.DerivativesAPI.update"

_VER_APPLY = "mammoth.api.pipeline_versions.PipelineVersionsAPI.apply"
_VER_DELETE = "mammoth.api.pipeline_versions.PipelineVersionsAPI.delete"
_VER_GET = "mammoth.api.pipeline_versions.PipelineVersionsAPI.get"
_VER_LIST = "mammoth.api.pipeline_versions.PipelineVersionsAPI.list"
_VER_UPDATE = "mammoth.api.pipeline_versions.PipelineVersionsAPI.update"

_AI_GEN_DATA = "mammoth.api.ai.AIAPI.generate_data"
_AI_GEN_INFO = "mammoth.api.ai.AIAPI.get_data_gen_info"
_AI_PROFILE = "mammoth.api.ai.AIAPI.generate_profile"

_DRAFT_COMMAND = "mammoth.api.pipeline.PipelineAPI.command"
_PIPE_EDIT = "mammoth.api.pipeline.PipelineAPI.edit_pipeline"
_PIPE_GET = "mammoth.api.pipeline.PipelineAPI.get_pipeline"
_PIPE_ITEMS = "mammoth.api.pipeline.PipelineAPI.items"
_PIPE_ITEMS_ALL = "mammoth.api.pipeline.PipelineAPI.items_all"
_PIPE_RERUN = "mammoth.api.pipeline.PipelineAPI.rerun"
_PIPE_WAIT = "mammoth.api.pipeline.PipelineAPI.wait_for_pipeline"

_TASK_ADD = "mammoth.api.pipeline.PipelineAPI.add_task"
_TASK_DELETE = "mammoth.api.pipeline.PipelineAPI.delete_task"
_TASK_GET = "mammoth.api.pipeline.PipelineAPI.get_task"
_TASK_LIST = "mammoth.api.pipeline.PipelineAPI.list_tasks"
_TASK_PREVIEW = "mammoth.api.pipeline.PipelineAPI.preview_task"
_TASK_UPDATE = "mammoth.api.pipeline.PipelineAPI.update_task"

_EXPORT_CREATE = "mammoth.api.exports.ExportsAPI.create"
_EXPORT_CSV = "mammoth.api.exports.ExportsAPI.to_csv"
_EXPORT_CSV_URL = "mammoth.api.exports.ExportsAPI.to_csv_url"
_EXPORT_DELETE = "mammoth.api.exports.ExportsAPI.delete"
_EXPORT_GET = "mammoth.api.exports.ExportsAPI.get"
_EXPORT_LIST = "mammoth.api.exports.ExportsAPI.list"
_EXPORT_PUBLISH_DB = "mammoth.api.exports.ExportsAPI.publish_db"
_EXPORT_PUBLISH_DB_UPDATE = "mammoth.api.exports.ExportsAPI.publish_db_update"
_EXPORT_UPDATE = "mammoth.api.exports.ExportsAPI.update"

_VALID_EXPORT_SPEC = {
    "DATAVIEW_ID": 7,
    "handler_type": "csv_file",
    "trigger_type": "none",
    "target_properties": {},
    "additional_properties": {},
    "run_immediately": True,
}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# ── view.list / view.bulk-delete ───────────────────────────────────────────


def test_view_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_list(_inv("view.list", extra_args=["9"]))
    assert excinfo.value.code == "project_required"


def test_view_list_without_dataset_id_walks_every_dataset_in_the_project(
    fake_service: FakeMammothService,
) -> None:
    """Item G: an agent's first move is often `view list` before it has any
    dataset id yet. It must not fail outright; it lists across the project."""
    fake_service.responses[_DATASETS_LIST_ALL] = {
        "datasets": [{"id": 9, "name": "a"}, {"id": 10, "name": "b"}]
    }
    fake_service.responses[_VIEW_LIST] = {"dataviews": [{"id": 501, "name": "v"}]}
    data, _ = view_cmd.view_list(_inv("view.list", project=180))
    assert data["dataviews"] == [
        {"id": 501, "name": "v", "dataset_id": 9},
        {"id": 501, "name": "v", "dataset_id": 10},
    ]
    assert data["datasets_visited"] == 2
    assert "next_dataset_offset" not in data
    dataset_calls = [c for c in fake_service.call_log if c[0] == _VIEW_LIST]
    assert [c[1]["dataset_id"] for c in dataset_calls] == [9, 10]


def test_view_list_without_dataset_id_pages_past_the_view_floor(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Once enough views have been collected, later datasets are deferred to
    a resumable `dataset_offset`, never silently dropped."""
    fake_service.responses[_DATASETS_LIST_ALL] = {"datasets": [{"id": 9}, {"id": 10}, {"id": 11}]}
    fake_service.responses[_VIEW_LIST] = {
        "dataviews": [{"id": i} for i in range(view_cmd._VIEW_LIST_ALL_DATASETS_MIN_VIEWS)]
    }
    data, _ = view_cmd.view_list(_inv("view.list", project=180))
    assert data["datasets_visited"] == 1
    assert data["next_dataset_offset"] == 1

    doc = _doc(tmp_path, {"dataset_offset": 1})
    data, _ = view_cmd.view_list(_inv("view.list", project=180, input_file=doc))
    assert data["datasets_visited"] == 1
    assert data["next_dataset_offset"] == 2
    resumed_calls = [c for c in fake_service.call_log if c[0] == _VIEW_LIST]
    assert [c[1]["dataset_id"] for c in resumed_calls] == [9, 10]


def test_view_list_passes_dataset_and_project(fake_service: FakeMammothService) -> None:
    view_cmd.view_list(_inv("view.list", project=180, extra_args=["9"]))
    assert fake_service.call_log == [(_VIEW_LIST, {"dataset_id": 9, "project_id": 180})]


def test_view_list_forwards_limit_sort(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"limit": 10, "sort": "(name:asc)"})
    view_cmd.view_list(_inv("view.list", project=180, extra_args=["9"], input_file=doc))
    assert fake_service.call_log == [
        (_VIEW_LIST, {"dataset_id": 9, "project_id": 180, "limit": 10, "sort": "(name:asc)"})
    ]


def test_bulk_delete_requires_dataview_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_bulk_delete(_inv("view.bulk-delete", project=180, extra_args=["9"], yes=True))
    assert excinfo.value.code == "missing_field"


def test_bulk_delete_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"dataview_ids": [1, 2]})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_bulk_delete(
            _inv("view.bulk-delete", project=180, extra_args=["9"], input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_bulk_delete_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"dataview_ids": [1, 2]})
    view_cmd.view_bulk_delete(
        _inv("view.bulk-delete", project=180, extra_args=["9"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (_BULK_DELETE, {"dataset_id": 9, "dataview_ids": [1, 2], "project_id": 180})
    ]


# ── dataset_id + dataview_id (project-scoped) ──────────────────────────────


def test_active_user_list_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_active_user_list(
        _inv("view.active-user.list", project=180, extra_args=["7", "9"])
    )
    assert fake_service.call_log == [
        (_ACTIVE_USER_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_active_user_list_requires_view_id(fake_service: FakeMammothService) -> None:
    # The view id is the only required positional now; the dataset is optional
    # and resolved from the view when omitted.
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_active_user_list(_inv("view.active-user.list", project=180, extra_args=[]))
    assert excinfo.value.code == "missing_argument"


def test_active_user_mark_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_active_user_mark(
        _inv("view.active-user.mark", project=180, extra_args=["7", "9"])
    )
    assert fake_service.call_log == [
        (_ACTIVE_USER_MARK, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_parameter_context_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_parameter_context(
        _inv("view.parameter-context", project=180, extra_args=["7", "9"])
    )
    assert fake_service.call_log == [
        (_PARAMETER_CONTEXT, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_preview_passes_ids_with_default_rows(fake_service: FakeMammothService) -> None:
    # Preview fetches the display-name map first (drives relabel and the
    # show-every-column default), then previews with the default 50 rows. With
    # the fake returning no metadata, the column count is unknown so no cols cap
    # is sent (the endpoint keeps its own default).
    view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (_PREVIEW, {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "rows": 50}),
    ]


def test_preview_forwards_rows_cols(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"rows": 5, "cols": 3})
    view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7", "9"], input_file=doc))
    assert fake_service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (_PREVIEW, {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "rows": 5, "cols": 3}),
    ]


def test_preview_trims_unheaded_system_value_from_positional_rows(
    fake_service: FakeMammothService,
) -> None:
    """Keep array rows aligned when the backend appends its identity value."""
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "name"},
            {"internal_name": "column_2", "display_name": "amount"},
        ]
    }
    fake_service.responses[_PREVIEW] = {
        "columns": ["column_1", "column_2"],
        "data": [["A", "10", 987654321]],
    }
    data, _ = view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7", "9"]))
    assert data == {"columns": ["name", "amount"], "data": [["A", "10"]]}


def test_preview_trims_unheaded_system_value_from_real_rows_shape(
    fake_service: FakeMammothService,
) -> None:
    """Handle the live preview envelope's ``columns`` plus ``rows`` keys."""
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "name"},
            {"internal_name": "column_2", "display_name": "amount"},
        ]
    }
    fake_service.responses[_PREVIEW] = {
        "columns": ["column_1", "column_2"],
        "rows": [["A", "10", 987654321]],
    }
    data, _ = view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7", "9"]))
    assert data == {"columns": ["name", "amount"], "rows": [["A", "10"]]}


def test_preview_preserves_unknown_multiple_extra_values(
    fake_service: FakeMammothService,
) -> None:
    """Do not silently discard more than the one known identity value."""
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "name"},
            {"internal_name": "column_2", "display_name": "amount"},
        ]
    }
    fake_service.responses[_PREVIEW] = {
        "columns": ["column_1", "column_2"],
        "data": [["A", "10", 987654321, "unexpected"]],
    }
    data, _ = view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7", "9"]))
    assert data == {
        "columns": ["name", "amount"],
        "data": [["A", "10", 987654321, "unexpected"]],
    }


def test_preview_defaults_cols_to_column_count(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # When metadata is available, the preview requests exactly the real column
    # count so every column shows (system columns like ``hash`` are excluded).
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "a"},
            {"internal_name": "column_2", "display_name": "b"},
            {"internal_name": "column_3", "display_name": "revenue"},
        ]
    }
    view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log[-1] == (
        _PREVIEW,
        {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "rows": 50, "cols": 3},
    )


def test_restore_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_restore(_inv("view.restore", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_RESTORE, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_trash_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_trash(_inv("view.trash", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_TRASH, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_update_rejects_missing_patch_data_without_dispatch(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_update(_inv("view.update", project=180, extra_args=["7", "9"]))
    assert excinfo.value.code == "unsupported_contract"
    assert excinfo.value.details["blocker"] == "B09 DATAVIEW_INPUT_UNTYPED"
    assert fake_service.call_log == []


def test_update_rejects_raw_patch_without_dispatch(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"patch_data": [{"op": "replace", "path": "/name", "value": "x"}]})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_update(
            _inv("view.update", project=180, extra_args=["7", "9"], input_file=doc)
        )
    assert excinfo.value.code == "unsupported_contract"
    assert excinfo.value.details["typed_alternatives"] == []
    assert fake_service.call_log == []


def test_data_get_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_DATA_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_data_get_forwards_timeout_poll_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"timeout": 30, "poll_interval": 1})
    view_cmd.view_data_get(
        _inv("view.data.get", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DATA_GET,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "timeout": 30,
                "poll_interval": 1,
            },
        )
    ]


def test_data_get_relabels_and_drops_system_columns(
    fake_service: FakeMammothService,
) -> None:
    # Data rows come back keyed by internal ids plus the system ``hash`` column;
    # the handler relabels to display names and drops ``hash``.
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "store"},
            {"internal_name": "column_2", "display_name": "revenue"},
        ]
    }
    fake_service.responses[_DATA_GET] = {
        "data": [{"column_1": "A", "column_2": "10", "hash": "deadbeef"}]
    }
    data, _ = view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["7", "9"]))
    assert data == {
        "data": [{"store": "A", "revenue": "10"}],
        "rows_returned": 1,
        "rows_total_in_page": 1,
        "truncated": False,
    }


def test_data_get_uses_renamed_column_names(fake_service: FakeMammothService) -> None:
    # A rename lives in display_properties.COLUMN_NAMES; metadata keeps the
    # pipeline's name. Rows must carry the name the user sees.
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "store"},
            {"internal_name": "column_2", "display_name": "rev"},
        ],
        "display_properties": {"COLUMN_NAMES": {"column_2": "Revenue"}},
    }
    fake_service.responses[_DATA_GET] = {"data": [{"column_1": "A", "column_2": "10"}]}
    data, _ = view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["7", "9"]))
    assert data["data"] == [{"store": "A", "Revenue": "10"}]


def test_data_get_offset_reads_a_later_page_through_the_query_route(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {
        "metadata": [{"internal_name": "column_1", "display_name": "n", "type": "NUMERIC"}]
    }
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.query_data"] = {
        "data": [{"column_1": 36}, {"column_1": 37}]
    }
    doc = tmp_path / "in.json"
    doc.write_text('{"offset": 36, "limit": 2}', encoding="utf-8")
    data, _ = view_cmd.view_data_get(
        _inv("view.data.get", project=180, extra_args=["7", "9"], input_file=str(doc))
    )
    query = [c for c in fake_service.call_log if c[0].endswith("query_data")]
    assert query == [
        (
            "mammoth.api.dataviews.DataviewsAPI.query_data",
            {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "offset": 36, "limit": 2},
        )
    ]
    assert data["data"] == [{"n": 36}, {"n": 37}]


def test_data_get_adds_column_warnings(fake_service: FakeMammothService) -> None:
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {
        "metadata": [{"internal_name": "column_1", "display_name": "price", "type": "TEXT"}]
    }
    fake_service.responses[_DATA_GET] = {
        "data": [{"column_1": v} for v in ("1.5", "2", "3", "4", "N/A")]
    }
    data, _ = view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["7", "9"]))
    assert [w["issue"] for w in data["column_warnings"]] == ["numbers_stored_as_text"]
    assert "convert-type 7" in data["column_warnings"][0]["fix"]


def test_join_check_reports_match_rate_and_unmatched_keys() -> None:
    before = {"row_count": 40, "columns": {"column_1": "cust_ref"}, "rows": []}
    after = {
        "row_count": 40,
        "columns": {"column_1": "cust_ref", "column_9": "name"},
        "rows": [{"cust_ref": "C1", "name": "Acme"}, {"cust_ref": "C99", "name": None}],
    }
    doc = {"on": [{"left": "cust_ref", "right": "id"}]}
    check = view_cmd.with_join_check({"status": "done"}, before, after, doc)["join_check"]
    assert check["columns_added"] == ["name"]
    assert (check["unmatched_rows"], check["match_rate"]) == (1, 0.5)
    assert check["unmatched_keys"] == ["C99"]
    assert any("found no match" in n for n in check["notes"])
    assert any("first 2 rows of 40" in n for n in check["notes"])


def test_join_check_flags_repeated_and_dropped_rows() -> None:
    cols = {"column_1": "k"}
    grew = view_cmd.with_join_check(
        {}, {"row_count": 10, "columns": cols}, {"row_count": 14, "columns": cols}, {}
    )["join_check"]
    assert any("added 4 rows" in n for n in grew["notes"])
    shrank = view_cmd.with_join_check(
        {}, {"row_count": 10, "columns": cols}, {"row_count": 7, "columns": cols}, {}
    )["join_check"]
    assert any("3 rows had no match and were dropped" in n for n in shrank["notes"])


def test_data_get_trims_rows_to_the_limit(fake_service: FakeMammothService, tmp_path: Path) -> None:
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {
        "metadata": [{"internal_name": "column_1", "display_name": "n"}]
    }
    fake_service.responses[_DATA_GET] = {"data": [{"column_1": i} for i in range(120)]}
    data, _ = view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["7", "9"]))
    assert (data["rows_returned"], data["rows_total_in_page"], data["truncated"]) == (50, 120, True)
    assert len(data["data"]) == 50

    doc = _doc(tmp_path, {"limit": 0, "sequence": 3})
    data, _ = view_cmd.view_data_get(
        _inv("view.data.get", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert len(data["data"]) == 120 and data["truncated"] is False
    data_calls = [kwargs for symbol, kwargs in fake_service.call_log if symbol == _DATA_GET]
    assert data_calls[-1]["sequence"] == 3


def test_data_query_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_query(_inv("view.data.query", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_DATA_QUERY, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_exportable_config_get_passes_view_and_explicit_dataset(
    fake_service: FakeMammothService,
) -> None:
    view_cmd.view_exportable_config_get(
        _inv("view.exportable-config.get", project=180, extra_args=["7", "9"])
    )
    assert fake_service.call_log == [
        (_EXPORTABLE_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_exportable_config_rejects_nonpositive_ids_before_service(
    fake_service: FakeMammothService,
) -> None:
    for args in (["0"], ["7", "0"], ["7", "-1"]):
        with pytest.raises(CliError):
            view_cmd.view_exportable_config_get(
                _inv("view.exportable-config.get", project=180, extra_args=args)
            )
    assert fake_service.call_log == []


def test_exportable_config_apply_requires_exact_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"config": {"tasks": []}})
    for confirm in (None, "8"):
        with pytest.raises(CliError):
            view_cmd.view_exportable_config_apply(
                _inv(
                    "view.exportable-config.apply",
                    project=180,
                    extra_args=["7", "9"],
                    input_file=doc,
                    no_input=True,
                    yes=True,
                    confirm=confirm,
                )
            )
    assert fake_service.call_log == []


def test_exportable_config_apply_passes_exact_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"config": {"tasks": []}, "is_paste_mode": True})
    view_cmd.view_exportable_config_apply(
        _inv(
            "view.exportable-config.apply",
            project=180,
            extra_args=["7", "9"],
            input_file=doc,
            no_input=True,
            yes=True,
            confirm="7",
        )
    )
    assert fake_service.call_log == [
        (
            _EXPORTABLE_APPLY,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "items": None,
                "config": {"tasks": []},
                "project_id": 180,
                "is_paste_mode": True,
            },
        )
    ]


def test_data_query_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    # The data route takes the backend condition shape with internal column
    # names (forwarding the CLI spec verbatim fails the job with "A clause can
    # only have one key"); display names in ``columns`` are mapped the same way.
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "a", "type": "TEXT"},
            {"internal_name": "column_2", "display_name": "b", "type": "NUMERIC"},
        ]
    }
    doc = _doc(
        tmp_path,
        {
            "sequence": 1,
            "offset": 10,
            "limit": 100,
            "columns": ["a", "b"],
            "condition": {"column": "b", "operator": ">", "value": 3},
            "sort": "(a:asc)",
        },
    )
    view_cmd.view_data_query(
        _inv("view.data.query", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (
            _DATA_QUERY,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "sequence": 1,
                "offset": 10,
                "limit": 100,
                "columns": ["column_1", "column_2"],
                "condition": {"column_2": {"GT": {"VALUE": 3}}},
                "sort": "(a:asc)",
            },
        ),
    ]


def test_data_query_rejects_an_unknown_operator(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"condition": {"column": "a", "operator": "GREATER", "value": 1}})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_query(
            _inv("view.data.query", project=180, extra_args=["7", "9"], input_file=doc)
        )
    assert excinfo.value.code == "invalid_condition"
    assert fake_service.call_log[-1][0] != _DATA_QUERY


def test_data_get_resolves_dataset_from_view_when_omitted(
    fake_service: FakeMammothService,
) -> None:
    # Only the view id is given: the dataset is resolved from the view via the
    # public pipeline resolver, then forwarded to the SDK call.
    fake_service.responses[_FIND_DATASET] = 9
    view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["7"]))
    assert fake_service.call_log == [
        (_FIND_DATASET, {"dataview_id": 7}),
        (_DATA_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
    ]


def test_preview_resolves_dataset_from_view_when_omitted(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_FIND_DATASET] = 9
    view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["7"]))
    assert fake_service.call_log == [
        (_FIND_DATASET, {"dataview_id": 7}),
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (_PREVIEW, {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "rows": 50}),
    ]


def test_data_query_dataset_from_input_field_skips_resolution(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # A ``dataset_id`` --input field is honored and skips the browse lookup.
    doc = _doc(tmp_path, {"dataset_id": 9, "limit": 5})
    view_cmd.view_data_query(_inv("view.data.query", project=180, extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_DATA_QUERY, {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "limit": 5}),
    ]


# ── view.data.aggregate ─────────────────────────────────────────────────────


def test_data_aggregate_pivot_group_by_and_sum(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "Channel", "type": "TEXT"},
            {"internal_name": "column_2", "display_name": "Spend", "type": "NUMERIC"},
        ]
    }
    fake_service.responses[_DATA_AGGREGATE] = {
        "data": [{"group_0": "Email", "agg_0": 120}, {"group_0": "Search", "agg_0": 80}]
    }
    doc = _doc(
        tmp_path,
        {
            "group_by": ["Channel"],
            "aggregations": [{"column": "Spend", "function": "SUM", "as_name": "Total Spend"}],
        },
    )
    data = view_cmd.view_data_aggregate(
        _inv("view.data.aggregate", project=180, extra_args=["7", "9"], input_file=doc)
    )[0]
    assert fake_service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (
            _DATA_AGGREGATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "aggregations": [
                    {"function": "SUM", "as_name": "Total Spend", "column": "column_2"}
                ],
                "group_by": ["column_1"],
            },
        ),
    ]
    assert data["data"] == [
        {"Channel": "Email", "Total Spend": 120},
        {"Channel": "Search", "Total Spend": 80},
    ]


def test_data_aggregate_pivot_count_no_group_by(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"aggregations": [{"function": "COUNT"}]})
    view_cmd.view_data_aggregate(
        _inv("view.data.aggregate", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (
            _DATA_AGGREGATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "aggregations": [{"function": "COUNT", "as_name": "COUNT"}],
            },
        ),
    ]


def test_data_aggregate_metric(fake_service: FakeMammothService, tmp_path: Path) -> None:
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [{"internal_name": "column_2", "display_name": "Spend", "type": "NUMERIC"}]
    }
    doc = _doc(tmp_path, {"metric": {"column": "Spend", "function": "SUM", "as_name": "Total"}})
    view_cmd.view_data_aggregate(
        _inv("view.data.aggregate", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
        (
            _DATA_AGGREGATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "metric": {"function": "SUM", "as_name": "Total", "column": "column_2"},
            },
        ),
    ]


def test_data_aggregate_forwards_condition_sequence_and_limit(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {
        "metadata": [{"internal_name": "column_2", "display_name": "Spend", "type": "NUMERIC"}]
    }
    doc = _doc(
        tmp_path,
        {
            "metric": {"column": "Spend", "function": "SUM"},
            "condition": {"column": "Spend", "operator": ">", "value": 0},
            "sequence": 3,
            "limit": 10,
        },
    )
    view_cmd.view_data_aggregate(
        _inv("view.data.aggregate", project=180, extra_args=["7", "9"], input_file=doc)
    )
    call = fake_service.call_log[-1][1]
    assert call["condition"] == {"column_2": {"GT": {"VALUE": 0}}}
    assert call["sequence"] == 3
    assert call["limit"] == 10


def test_data_aggregate_requires_exactly_one_of_aggregations_or_metric(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    for payload in ({}, {"group_by": ["Channel"], "metric": {"function": "COUNT"}}):
        doc = _doc(tmp_path, payload)
        with pytest.raises(CliError) as excinfo:
            view_cmd.view_data_aggregate(
                _inv("view.data.aggregate", project=180, extra_args=["7", "9"], input_file=doc)
            )
        assert excinfo.value.code == "invalid_arguments"
    assert fake_service.call_log == []


def test_data_aggregate_resolves_dataset_from_view_when_omitted(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_FIND_DATASET] = 9
    doc = _doc(tmp_path, {"metric": {"function": "COUNT"}})
    view_cmd.view_data_aggregate(
        _inv("view.data.aggregate", project=180, extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log[0] == (_FIND_DATASET, {"dataview_id": 7})


def test_active_user_list_resolves_dataset_from_view_when_omitted(
    fake_service: FakeMammothService,
) -> None:
    # Sub-resource commands are view-first too: with only the view id, the
    # dataset is resolved from the view before the SDK call.
    fake_service.responses[_FIND_DATASET] = 9
    view_cmd.view_active_user_list(_inv("view.active-user.list", project=180, extra_args=["7"]))
    assert fake_service.call_log == [
        (_FIND_DATASET, {"dataview_id": 7}),
        (_ACTIVE_USER_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
    ]


def test_checkpoint_get_resolves_dataset_from_view_when_omitted(
    fake_service: FakeMammothService,
) -> None:
    # A three-id command (view, sub id, optional dataset): with the dataset
    # omitted, it is resolved from the view and the checkpoint id stays second.
    fake_service.responses[_FIND_DATASET] = 9
    view_cmd.view_checkpoint_get(_inv("view.checkpoint.get", project=180, extra_args=["7", "3"]))
    assert fake_service.call_log == [
        (_FIND_DATASET, {"dataview_id": 7}),
        (_CKPT_GET, {"dataset_id": 9, "dataview_id": 7, "checkpoint_id": 3, "project_id": 180}),
    ]


@pytest.mark.parametrize(
    ("handler", "command_id", "extra_args"),
    [
        (view_cmd.view_trash, "view.trash", ["7"]),
        (view_cmd.view_derivative_delete, "view.derivative.delete", ["7", "3"]),
        (view_cmd.view_active_user_mark, "view.active-user.mark", ["7"]),
    ],
)
def test_non_read_commands_refuse_parent_discovery(
    fake_service: FakeMammothService, handler, command_id: str, extra_args: list[str]
) -> None:
    # Only reads may fall back to the project-wide browse-and-probe resolver.
    # A mutation, export, or delete without the exact parent fails closed
    # before the resolver or the SDK is called, and names the read to run.
    fake_service.responses[_FIND_DATASET] = 9
    with pytest.raises(CliError) as excinfo:
        handler(_inv(command_id, project=180, extra_args=extra_args, yes=True))
    error = excinfo.value
    assert error.code == "missing_argument"
    assert error.exit_status == 2
    assert error.recovery_commands == ["mammoth view get 7 --project 180"]
    assert fake_service.call_log == []


def test_non_read_command_with_exact_parent_skips_discovery(
    fake_service: FakeMammothService,
) -> None:
    view_cmd.view_trash(_inv("view.trash", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_TRASH, {"dataset_id": 9, "dataview_id": 7, "project_id": 180}),
    ]


def test_conditional_format_create_requires_rule(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_create(
            _inv("view.conditional-format.create", project=180, extra_args=["7", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_conditional_format_create_forwards_rule(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"rule": {"color": "red"}})
    view_cmd.view_conditional_format_create(
        _inv("view.conditional-format.create", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CF_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "rule": {"color": "red"}, "project_id": 180},
        )
    ]


def test_conditional_format_delete_all_requires_rule_id(
    fake_service: FakeMammothService,
) -> None:
    # The release route deletes one rule per call and needs rule_id.
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_delete_all(
            _inv("view.conditional-format.delete-all", project=180, extra_args=["9", "7"], yes=True)
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_conditional_format_delete_all_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"rule_id": "rule-1"})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_delete_all(
            _inv(
                "view.conditional-format.delete-all",
                project=180,
                extra_args=["9", "7"],
                output="json",
                input_file=doc,
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_conditional_format_delete_all_proceeds_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"rule_id": "rule-1"})
    view_cmd.view_conditional_format_delete_all(
        _inv(
            "view.conditional-format.delete-all",
            project=180,
            extra_args=["7", "9"],
            yes=True,
            input_file=doc,
        )
    )
    assert fake_service.call_log == [
        (
            _CF_DELETE_ALL,
            {"dataset_id": 9, "dataview_id": 7, "rule_id": "rule-1", "project_id": 180},
        )
    ]


def test_conditional_format_list_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_conditional_format_list(
        _inv("view.conditional-format.list", project=180, extra_args=["7", "9"])
    )
    assert fake_service.call_log == [
        (_CF_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_conditional_format_update_requires_rule(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_update(
            _inv("view.conditional-format.update", project=180, extra_args=["7", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_conditional_format_update_forwards_rule(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"rule": {"color": "blue"}})
    view_cmd.view_conditional_format_update(
        _inv("view.conditional-format.update", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CF_UPDATE,
            {"dataset_id": 9, "dataview_id": 7, "rule": {"color": "blue"}, "project_id": 180},
        )
    ]


# ── checkpoints ─────────────────────────────────────────────────────────────


def test_checkpoint_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_checkpoint_create(
            _inv("view.checkpoint.create", project=180, extra_args=["7", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_checkpoint_create_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"checkpoint_name": "cp1", "checkpoint_type": "alert"}
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_checkpoint_create(
        _inv("view.checkpoint.create", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CKPT_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "body": body, "project_id": 180},
        )
    ]


def test_checkpoint_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_checkpoint_delete(
            _inv("view.checkpoint.delete", project=180, extra_args=["7", "3", "9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_checkpoint_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_checkpoint_delete(
        _inv("view.checkpoint.delete", project=180, extra_args=["7", "3", "9"], yes=True)
    )
    assert fake_service.call_log == [
        (_CKPT_DELETE, {"dataset_id": 9, "dataview_id": 7, "checkpoint_id": 3, "project_id": 180})
    ]


def test_checkpoint_delete_requires_checkpoint_id(fake_service: FakeMammothService) -> None:
    # With only the view id present, the required checkpoint id (second
    # positional) is missing.
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_checkpoint_delete(
            _inv("view.checkpoint.delete", project=180, extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_checkpoint_get_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_checkpoint_get(
        _inv("view.checkpoint.get", project=180, extra_args=["7", "3", "9"])
    )
    assert fake_service.call_log == [
        (_CKPT_GET, {"dataset_id": 9, "dataview_id": 7, "checkpoint_id": 3, "project_id": 180})
    ]


def test_checkpoint_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id,name"})
    view_cmd.view_checkpoint_get(
        _inv("view.checkpoint.get", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CKPT_GET,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "checkpoint_id": 3,
                "project_id": 180,
                "fields": "id,name",
            },
        )
    ]


def test_checkpoint_list_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id", "sort": "(id:asc)", "sequence": "1", "status": "ok"})
    view_cmd.view_checkpoint_list(
        _inv("view.checkpoint.list", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CKPT_LIST,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "fields": "id",
                "sort": "(id:asc)",
                "sequence": "1",
                "status": "ok",
            },
        )
    ]


def test_checkpoint_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_checkpoint_update(
            _inv("view.checkpoint.update", project=180, extra_args=["7", "3", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_checkpoint_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"patches": [{"op": "replace", "path": "approve"}]}
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_checkpoint_update(
        _inv("view.checkpoint.update", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CKPT_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "checkpoint_id": 3,
                "body": body,
                "project_id": 180,
            },
        )
    ]


# ── data checks ──────────────────────────────────────────────────────────────


def test_data_check_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_check_create(
            _inv("view.data-check.create", project=180, extra_args=["7", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_data_check_create_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {
        "name": "not null",
        "checks": [{"check_type": "null_percentage", "config": {"column": "a", "condition": "lt"}}],
    }
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_data_check_create(
        _inv("view.data-check.create", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DC_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "body": body, "project_id": 180},
        )
    ]


def test_data_check_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_check_delete(
            _inv("view.data-check.delete", project=180, extra_args=["7", "3", "9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_data_check_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_check_delete(
        _inv("view.data-check.delete", project=180, extra_args=["7", "3", "9"], yes=True)
    )
    assert fake_service.call_log == [
        (_DC_DELETE, {"dataset_id": 9, "dataview_id": 7, "data_check_id": 3, "project_id": 180})
    ]


def test_data_check_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id"})
    view_cmd.view_data_check_get(
        _inv("view.data-check.get", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DC_GET,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "data_check_id": 3,
                "project_id": 180,
                "fields": "id",
            },
        )
    ]


def test_data_check_list_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_check_list(_inv("view.data-check.list", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_DC_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_data_check_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_check_update(
            _inv("view.data-check.update", project=180, extra_args=["7", "3", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_data_check_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"patches": [{"op": "replace", "path": "enable"}]}
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_data_check_update(
        _inv("view.data-check.update", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DC_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "data_check_id": 3,
                "body": body,
                "project_id": 180,
            },
        )
    ]


# ── derivatives ───────────────────────────────────────────────────────────


def test_derivative_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_create(
            _inv("view.derivative.create", project=180, extra_args=["7", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_derivative_create_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {
        "param": {
            "METRIC": {
                "AS": "Total",
                "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "a", "FUNCTION": "SUM"}}],
            }
        }
    }
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_derivative_create(
        _inv("view.derivative.create", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DERIV_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "body": body, "project_id": 180},
        )
    ]


def test_derivative_data_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_data(
            _inv("view.derivative.data", project=180, extra_args=["7", "3", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_derivative_data_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"filter": "x"}})
    view_cmd.view_derivative_data(
        _inv("view.derivative.data", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DERIV_DATA,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "derivative_id": 3,
                "body": {"filter": "x"},
                "project_id": 180,
            },
        )
    ]


def test_derivative_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_delete(
            _inv("view.derivative.delete", project=180, extra_args=["7", "3", "9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_derivative_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_derivative_delete(
        _inv("view.derivative.delete", project=180, extra_args=["7", "3", "9"], yes=True)
    )
    assert fake_service.call_log == [
        (_DERIV_DELETE, {"dataset_id": 9, "dataview_id": 7, "derivative_id": 3, "project_id": 180})
    ]


def test_derivative_list_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_derivative_list(_inv("view.derivative.list", project=180, extra_args=["7", "9"]))
    assert fake_service.call_log == [
        (_DERIV_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_derivative_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_update(
            _inv("view.derivative.update", project=180, extra_args=["7", "3", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_derivative_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {
        "patches": [
            {
                "op": "replace",
                "path": "param",
                "value": {
                    "METRIC": {
                        "AS": "Total",
                        "EXPRESSION": [
                            {"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "a", "FUNCTION": "SUM"}}
                        ],
                    }
                },
            }
        ]
    }
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_derivative_update(
        _inv("view.derivative.update", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DERIV_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "derivative_id": 3,
                "body": body,
                "project_id": 180,
            },
        )
    ]


# ── pipeline versions ────────────────────────────────────────────────────


def test_version_apply_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_version_apply(_inv("view.version.apply", project=180, extra_args=["7", "3", "9"]))
    assert fake_service.call_log == [
        (_VER_APPLY, {"dataset_id": 9, "dataview_id": 7, "version_id": 3, "project_id": 180})
    ]


def test_version_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_version_delete(
            _inv("view.version.delete", project=180, extra_args=["7", "3", "9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_version_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_version_delete(
        _inv("view.version.delete", project=180, extra_args=["7", "3", "9"], yes=True)
    )
    assert fake_service.call_log == [
        (_VER_DELETE, {"dataset_id": 9, "dataview_id": 7, "version_id": 3, "project_id": 180})
    ]


def test_version_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id"})
    view_cmd.view_version_get(
        _inv("view.version.get", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _VER_GET,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "version_id": 3,
                "project_id": 180,
                "fields": "id",
            },
        )
    ]


def test_version_list_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(
        tmp_path, {"fields": "id", "sort": "(id:asc)", "limit": 10, "offset": 0, "name": "v1"}
    )
    view_cmd.view_version_list(
        _inv("view.version.list", project=180, extra_args=["7", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _VER_LIST,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "fields": "id",
                "sort": "(id:asc)",
                "limit": 10,
                "offset": 0,
                "name": "v1",
            },
        )
    ]


def test_version_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_version_update(
            _inv("view.version.update", project=180, extra_args=["7", "3", "9"])
        )
    assert excinfo.value.code == "missing_field"


def test_version_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"patches": [{"op": "replace", "path": "name"}]}
    doc = _doc(tmp_path, {"body": body})
    view_cmd.view_version_update(
        _inv("view.version.update", project=180, extra_args=["7", "3", "9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _VER_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "version_id": 3,
                "body": body,
                "project_id": 180,
            },
        )
    ]


# ── ai (no project scope) ──────────────────────────────────────────────────


def test_ai_generate_data_requires_prompt(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_ai_generate_data(_inv("view.ai.generate-data", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_ai_generate_data_passes_prompt_no_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"prompt": "make data"})
    view_cmd.view_ai_generate_data(_inv("view.ai.generate-data", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_AI_GEN_DATA, {"dataview_id": 7, "prompt": "make data"})]


def test_ai_generate_data_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(
        tmp_path,
        {"prompt": "make data", "no_of_rows": 20, "columns": ["a"], "dataset_id": 9},
    )
    view_cmd.view_ai_generate_data(_inv("view.ai.generate-data", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (
            _AI_GEN_DATA,
            {
                "dataview_id": 7,
                "prompt": "make data",
                "no_of_rows": 20,
                "columns": ["a"],
                "dataset_id": 9,
            },
        )
    ]


def test_ai_generation_info_passes_dataview_id(fake_service: FakeMammothService) -> None:
    view_cmd.view_ai_generation_info(_inv("view.ai.generation-info", extra_args=["7"]))
    assert fake_service.call_log == [(_AI_GEN_INFO, {"dataview_id": 7})]


def test_ai_generation_info_forwards_dataset_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"dataset_id": 9})
    view_cmd.view_ai_generation_info(
        _inv("view.ai.generation-info", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [(_AI_GEN_INFO, {"dataview_id": 7, "dataset_id": 9})]


def test_ai_profile_passes_dataview_id(fake_service: FakeMammothService) -> None:
    view_cmd.view_ai_profile(_inv("view.ai.profile", extra_args=["7"]))
    assert fake_service.call_log == [(_AI_PROFILE, {"dataview_id": 7})]


def test_ai_profile_forwards_action(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"dataset_id": 9, "action": "data_quality"})
    view_cmd.view_ai_profile(_inv("view.ai.profile", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_AI_PROFILE, {"dataview_id": 7, "dataset_id": 9, "action": "data_quality"})
    ]


# ── draft.command ───────────────────────────────────────────────────────────


def test_draft_command_requires_command(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_draft_command(_inv("view.draft.command", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_draft_command_passes_command(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"command": "enter"})
    view_cmd.view_draft_command(_inv("view.draft.command", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_DRAFT_COMMAND, {"dataview_id": 7, "command": "enter"})]


def test_draft_command_forwards_dataset_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"command": "enter", "dataset_id": 9})
    view_cmd.view_draft_command(_inv("view.draft.command", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_DRAFT_COMMAND, {"dataview_id": 7, "command": "enter", "dataset_id": 9})
    ]


# ── pipeline.* (no project scope) ───────────────────────────────────────────


def test_pipeline_edit_requires_patches(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_pipeline_edit(_inv("view.pipeline.edit", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_pipeline_edit_passes_patches_then_waits(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # After applying patches, the handler blocks on the pipeline until it settles
    # (run/reset patches are async) and returns that terminal state.
    doc = _doc(tmp_path, {"patches": [{"op": "remove", "path": "/x"}]})
    view_cmd.view_pipeline_edit(_inv("view.pipeline.edit", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_PIPE_EDIT, {"dataview_id": 7, "patches": [{"op": "remove", "path": "/x"}]}),
        (_PIPE_WAIT, {"dataview_id": 7}),
    ]


def test_pipeline_edit_forwards_dataset_id_to_wait(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"patches": [{"op": "run"}], "dataset_id": 9})
    view_cmd.view_pipeline_edit(_inv("view.pipeline.edit", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_PIPE_EDIT, {"dataview_id": 7, "patches": [{"op": "run"}], "dataset_id": 9}),
        (_PIPE_WAIT, {"dataview_id": 7, "dataset_id": 9}),
    ]


def test_pipeline_get_passes_dataview_id(fake_service: FakeMammothService) -> None:
    view_cmd.view_pipeline_get(_inv("view.pipeline.get", extra_args=["7"]))
    assert fake_service.call_log == [(_PIPE_GET, {"dataview_id": 7})]


def test_pipeline_get_hints_the_exact_command_when_draft_is_dirty(
    fake_service: FakeMammothService,
) -> None:
    # WPP/T3 evidence: an agent that only reads 'view pipeline get' had no
    # way to notice an unsubmitted draft was holding back pending changes.
    fake_service.responses[_PIPE_GET] = {"draft_mode": "dirty", "auto_run": True}
    data, _ = view_cmd.view_pipeline_get(_inv("view.pipeline.get", extra_args=["7"]))
    assert data["hint"] == (
        "This view has an unsubmitted draft with pending changes; run "
        "'mammoth view draft submit 7' to apply them."
    )


def test_pipeline_get_hints_the_exact_command_when_auto_run_is_off(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_PIPE_GET] = {"draft_mode": "off", "auto_run": False}
    data, _ = view_cmd.view_pipeline_get(_inv("view.pipeline.get", extra_args=["7"]))
    assert data["hint"] == (
        "Auto-run is off for this pipeline; new tasks will not compute "
        "automatically. Run 'mammoth view pipeline rerun 7' to compute pending "
        "tasks now."
    )


def test_pipeline_get_has_no_hint_when_clean_and_auto_run(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_PIPE_GET] = {"draft_mode": "off", "auto_run": True}
    data, _ = view_cmd.view_pipeline_get(_inv("view.pipeline.get", extra_args=["7"]))
    assert "hint" not in data


def test_pipeline_items_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(
        tmp_path,
        {
            "fields": "id",
            "limit": 10,
            "offset": 0,
            "sort": "(id:asc)",
            "sequence": 1,
            "status": "ok",
        },
    )
    view_cmd.view_pipeline_items(_inv("view.pipeline.items", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (
            _PIPE_ITEMS,
            {
                "dataview_id": 7,
                "fields": "id",
                "limit": 10,
                "offset": 0,
                "sort": "(id:asc)",
                "sequence": 1,
                "status": "ok",
            },
        )
    ]


def test_pipeline_items_all_requires_parent_and_forwards_bounds(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"dataset_id": 9, "limit": 2, "max_pages": 3, "status": "success"})
    view_cmd.view_pipeline_items_all(
        _inv("view.pipeline.items-all", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _PIPE_ITEMS_ALL,
            {"dataview_id": 7, "dataset_id": 9, "limit": 2, "max_pages": 3, "status": "success"},
        )
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dataset_id", 0),
        ("dataset_id", -1),
        ("dataset_id", True),
        ("limit", 0),
        ("max_pages", 0),
        ("max_pages", 1001),
    ],
)
def test_pipeline_items_all_rejects_invalid_bounds_before_request(
    fake_service: FakeMammothService, tmp_path: Path, field: str, value: object
) -> None:
    payload: dict[str, object] = {"dataset_id": 9, field: value}
    doc = _doc(tmp_path, payload)
    expected = "dataset_id" if field == "dataset_id" else field
    with pytest.raises(CliError, match=expected):
        view_cmd.view_pipeline_items_all(
            _inv("view.pipeline.items-all", extra_args=["7"], input_file=doc)
        )
    assert fake_service.call_log == []


def test_pipeline_rerun_passes_dataview_id(fake_service: FakeMammothService) -> None:
    view_cmd.view_pipeline_rerun(_inv("view.pipeline.rerun", extra_args=["7"]))
    assert fake_service.call_log == [(_PIPE_RERUN, {"dataview_id": 7})]


def test_pipeline_rerun_forwards_from_sequence(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"from_sequence": 2, "dataset_id": 9})
    view_cmd.view_pipeline_rerun(_inv("view.pipeline.rerun", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_PIPE_RERUN, {"dataview_id": 7, "from_sequence": 2, "dataset_id": 9})
    ]


def test_pipeline_wait_forwards_timeout(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"timeout": 60, "poll_interval": 5})
    view_cmd.view_pipeline_wait(_inv("view.pipeline.wait", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_PIPE_WAIT, {"dataview_id": 7, "timeout": 60, "poll_interval": 5})
    ]


# ── task.* (no project scope) ───────────────────────────────────────────────


def test_task_add_requires_task_spec(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_task_add(_inv("view.task.add", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_task_add_passes_task_spec(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"task_spec": {"kind": "filter"}})
    view_cmd.view_task_add(_inv("view.task.add", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_TASK_ADD, {"dataview_id": 7, "task_spec": {"kind": "filter"}}),
        (_TASK_LIST, {"dataview_id": 7}),
    ]


def test_task_add_rejects_a_task_that_failed_at_run_time(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A GEN_AI step can fail after the backend accepts and binds the task --
    a workspace AI quota outage, for example -- leaving the column blank
    while ``has_error`` stays false and ``pipeline_state`` reads ready. Only
    the task's own ``transform_status`` (``__full`` fields) shows it.
    """
    long_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    just_now = datetime.now(UTC).isoformat()
    fake_service.responses[_TASK_LIST] = {
        "tasks": [
            {"id": 3, "sequence": 1, "created_at": long_ago, "transform_status": "DONE"},
            {"id": 9, "sequence": 2, "created_at": just_now, "transform_status": "ERROR"},
        ]
    }
    doc = _doc(tmp_path, {"task_spec": {"kind": "gen_ai"}})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_task_add(_inv("view.task.add", extra_args=["7"], input_file=doc))
    assert excinfo.value.code == "task_runtime_error"
    assert excinfo.value.details["task_id"] == 9
    assert excinfo.value.details["transform_status"] == "ERROR"
    assert "mammoth view task get 7 9" in excinfo.value.recovery_commands
    # The API does not expose the failure reason -- do not claim it does.
    assert excinfo.value.hint is not None
    assert "does not expose" in excinfo.value.hint
    assert "AI quota" in excinfo.value.hint


def test_task_add_does_not_reject_a_pipeline_with_a_pre_existing_error_on_a_later_step(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A step already in ERROR before this call (the pipeline's last step,
    by sequence) must not fail every later add just because it sorts last.
    """
    long_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    just_now = datetime.now(UTC).isoformat()
    fake_service.responses[_TASK_LIST] = {
        "tasks": [
            {"id": 9, "sequence": 3, "created_at": just_now, "transform_status": "DONE"},
            {"id": 2, "sequence": 5, "created_at": long_ago, "transform_status": "ERROR"},
        ]
    }
    doc = _doc(tmp_path, {"task_spec": {"kind": "filter"}})
    view_cmd.view_task_add(_inv("view.task.add", extra_args=["7"], input_file=doc))


def test_task_add_checks_the_task_this_call_created_not_the_last_step(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A task inserted mid-pipeline is not the highest-sequence task."""
    long_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    just_now = datetime.now(UTC).isoformat()
    fake_service.responses[_TASK_LIST] = {
        "tasks": [
            {"id": 9, "sequence": 1, "created_at": just_now, "transform_status": "ERROR"},
            {"id": 3, "sequence": 2, "created_at": long_ago, "transform_status": "DONE"},
        ]
    }
    doc = _doc(tmp_path, {"task_spec": {"kind": "gen_ai"}})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_task_add(_inv("view.task.add", extra_args=["7"], input_file=doc))
    assert excinfo.value.details["task_id"] == 9


def test_task_add_accepts_a_task_that_finished_cleanly(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_TASK_LIST] = {
        "tasks": [
            {
                "id": 3,
                "sequence": 1,
                "created_at": datetime.now(UTC).isoformat(),
                "transform_status": "DONE",
            }
        ]
    }
    doc = _doc(tmp_path, {"task_spec": {"kind": "filter"}})
    view_cmd.view_task_add(_inv("view.task.add", extra_args=["7"], input_file=doc))


def test_task_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_task_delete(_inv("view.task.delete", extra_args=["7", "3"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_task_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_task_delete(_inv("view.task.delete", extra_args=["7", "3"], yes=True))
    assert fake_service.call_log == [(_TASK_DELETE, {"dataview_id": 7, "task_id": 3})]


def test_task_get_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_task_get(_inv("view.task.get", extra_args=["7", "3"]))
    assert fake_service.call_log == [(_TASK_GET, {"dataview_id": 7, "task_id": 3})]


def test_task_list_passes_dataview_id(fake_service: FakeMammothService) -> None:
    view_cmd.view_task_list(_inv("view.task.list", extra_args=["7"]))
    assert fake_service.call_log == [(_TASK_LIST, {"dataview_id": 7})]


def test_task_preview_requires_task_spec(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_task_preview(_inv("view.task.preview", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_task_preview_passes_task_spec(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"task_spec": {"kind": "math"}})
    view_cmd.view_task_preview(_inv("view.task.preview", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_TASK_PREVIEW, {"dataview_id": 7, "task_spec": {"kind": "math"}})
    ]


def test_task_update_requires_task_spec(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_task_update(_inv("view.task.update", extra_args=["7", "3"]))
    assert excinfo.value.code == "missing_field"


def test_task_update_passes_task_spec(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"task_spec": {"kind": "sort"}})
    view_cmd.view_task_update(_inv("view.task.update", extra_args=["7", "3"], input_file=doc))
    assert fake_service.call_log == [
        (_TASK_UPDATE, {"dataview_id": 7, "task_id": 3, "task_spec": {"kind": "sort"}})
    ]


# ── export.* ────────────────────────────────────────────────────────────────


def test_export_create_requires_export_spec(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_create(
            _inv("view.export.create", project=180, extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_field"


def test_export_create_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"export_spec": _VALID_EXPORT_SPEC})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_create(
            _inv(
                "view.export.create",
                project=180,
                extra_args=["7"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_export_create_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"export_spec": _VALID_EXPORT_SPEC, "dataset_id": 9})
    view_cmd.view_export_create(
        _inv("view.export.create", project=180, extra_args=["7"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (
            _EXPORT_CREATE,
            {
                "dataview_id": 7,
                "export_spec": _VALID_EXPORT_SPEC,
                "project_id": 180,
                "dataset_id": 9,
            },
        )
    ]


def test_export_csv_passes_dataview_id_no_project(fake_service: FakeMammothService) -> None:
    view_cmd.view_export_csv(_inv("view.export.csv", extra_args=["7"]))
    assert fake_service.call_log == [(_EXPORT_CSV, {"dataview_id": 7})]


def test_export_csv_forwards_output_path(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"output_path": "/tmp/out.csv", "timeout": 60})
    view_cmd.view_export_csv(_inv("view.export.csv", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_EXPORT_CSV, {"dataview_id": 7, "output_path": "/tmp/out.csv", "timeout": 60})
    ]


def _enter_embedded_call() -> object:
    """Make an embedded call current; returns the token for ``embedded.leave``."""
    login = ExplicitLogin(
        api_key=None,
        api_secret=None,
        workspace_id=1,
        api_token="jwt-user",
        server_prefix="app",
        headers={},
    )
    return embedded.enter(embedded.EmbeddedCall(login=login))


def test_export_csv_embedded_returns_download_url_and_writes_no_file(
    fake_service: FakeMammothService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Embedded, the CSV export must never touch the host process's disk --
    it hands back the signed URL instead (see mammoth_cli/embed.py)."""
    cwd = tmp_path / "server-cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    fake_service.responses[_EXPORT_CSV_URL] = {
        "url": "https://signed.example/file.csv",
        "trigger_id": None,
        "job_id": 9001,
    }
    token = _enter_embedded_call()
    try:
        data, _ = view_cmd.view_export_csv(_inv("view.export.csv", extra_args=["7"]))
    finally:
        embedded.leave(token)

    assert data == {"download_url": "https://signed.example/file.csv"}
    assert fake_service.call_log == [(_EXPORT_CSV_URL, {"dataview_id": 7})]
    assert list(cwd.iterdir()) == []


def test_export_csv_embedded_rejects_output_path(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"output_path": str(tmp_path / "out.csv")})
    token = _enter_embedded_call()
    try:
        with pytest.raises(CliError) as excinfo:
            view_cmd.view_export_csv(_inv("view.export.csv", extra_args=["7"], input_file=doc))
    finally:
        embedded.leave(token)

    assert excinfo.value.code == "unsupported_contract"
    assert fake_service.call_log == []
    assert not (tmp_path / "out.csv").exists()


def test_export_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_delete(
            _inv("view.export.delete", project=180, extra_args=["7", "3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_export_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_export_delete(
        _inv("view.export.delete", project=180, extra_args=["7", "3"], yes=True)
    )
    assert fake_service.call_log == [
        (_EXPORT_DELETE, {"dataview_id": 7, "export_id": 3, "project_id": 180})
    ]


def test_export_get_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_export_get(_inv("view.export.get", project=180, extra_args=["7", "3"]))
    assert fake_service.call_log == [
        (_EXPORT_GET, {"dataview_id": 7, "export_id": 3, "project_id": 180})
    ]


def test_export_list_passes_dataview_id_no_project(fake_service: FakeMammothService) -> None:
    view_cmd.view_export_list(_inv("view.export.list", extra_args=["7"]))
    assert fake_service.call_log == [(_EXPORT_LIST, {"dataview_id": 7})]


def test_export_list_passes_explicit_dataset_without_discovery(
    fake_service: FakeMammothService,
) -> None:
    view_cmd.view_export_list(_inv("view.export.list", extra_args=["7", "9"]))
    assert fake_service.call_log == [(_EXPORT_LIST, {"dataview_id": 7, "dataset_id": 9})]


def test_export_list_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"limit": 10, "offset": 0, "status": "executed"})
    view_cmd.view_export_list(_inv("view.export.list", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_EXPORT_LIST, {"dataview_id": 7, "limit": 10, "offset": 0, "status": "executed"})
    ]


def test_export_publish_db_requires_odbc_type(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"target_properties": {"host": "x"}})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_publish_db(
            _inv(
                "view.export.publish-db",
                project=180,
                extra_args=["7"],
                input_file=doc,
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_export_publish_db_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"odbc_type": "postgres", "target_properties": {"host": "x"}})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_publish_db(
            _inv(
                "view.export.publish-db",
                project=180,
                extra_args=["7"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_export_publish_db_proceeds_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"odbc_type": "postgres", "target_properties": {"host": "x"}})
    view_cmd.view_export_publish_db(
        _inv("view.export.publish-db", project=180, extra_args=["7"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (
            _EXPORT_PUBLISH_DB,
            {
                "dataview_id": 7,
                "odbc_type": "postgres",
                "target_properties": {"host": "x"},
                "project_id": 180,
            },
        )
    ]


def test_export_publish_db_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_publish_db_update(
            _inv("view.export.publish-db-update", project=180, extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_field"


def test_export_publish_db_update_proceeds_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"patch": [{"op": "replace", "path": "/host", "value": "y"}]})
    view_cmd.view_export_publish_db_update(
        _inv(
            "view.export.publish-db-update",
            project=180,
            extra_args=["7"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _EXPORT_PUBLISH_DB_UPDATE,
            {
                "dataview_id": 7,
                "patch": [{"op": "replace", "path": "/host", "value": "y"}],
                "project_id": 180,
            },
        )
    ]


def test_export_update_requires_patches(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_update(
            _inv("view.export.update", project=180, extra_args=["7", "3"], yes=True)
        )
    assert excinfo.value.code == "missing_field"


def test_export_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"patches": [{"op": "remove", "path": "/x"}]})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_update(
            _inv(
                "view.export.update",
                project=180,
                extra_args=["7", "3"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_export_update_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"patches": [{"op": "remove", "path": "/x"}], "skip_validation": True})
    view_cmd.view_export_update(
        _inv(
            "view.export.update",
            project=180,
            extra_args=["7", "3"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _EXPORT_UPDATE,
            {
                "dataview_id": 7,
                "export_id": 3,
                "patches": [{"op": "remove", "path": "/x"}],
                "project_id": 180,
                "skip_validation": True,
            },
        )
    ]


def test_pipeline_items_all_accepts_trailing_parent_positional(
    fake_service: FakeMammothService,
) -> None:
    # The schema advertises DATAVIEW_ID [DATASET_ID]; the trailing positional
    # used to be ignored and the command then demanded the input field.
    view_cmd.view_pipeline_items_all(_inv("view.pipeline.items-all", extra_args=["7", "9"]))
    assert fake_service.call_log == [(_PIPE_ITEMS_ALL, {"dataview_id": 7, "dataset_id": 9})]


def test_pipeline_items_all_rejects_conflicting_parents(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"dataset_id": 10})
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_pipeline_items_all(
            _inv("view.pipeline.items-all", extra_args=["7", "9"], input_file=doc)
        )
    assert excinfo.value.code == "ambiguous_resource_identity"
    assert fake_service.call_log == []


def test_view_list_trims_records_unless_full(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    record = {
        "id": 45,
        "ds_id": 9,
        "name": "v",
        "status": "ready",
        "row_count": 6,
        "dependencies_info": {"dependees": {"45": {}}},
        "display_properties": {},
    }
    fake_service.responses[_VIEW_LIST] = {"dataviews": [record], "next": None}
    data, _ = view_cmd.view_list(_inv("view.list", project=180, extra_args=["9"]))
    assert data["dataviews"] == [
        {"id": 45, "ds_id": 9, "name": "v", "status": "ready", "row_count": 6}
    ]
    assert data["next"] is None
    doc = _doc(tmp_path, {"full": True})
    data, _ = view_cmd.view_list(_inv("view.list", project=180, extra_args=["9"], input_file=doc))
    assert data["dataviews"] == [record]
    assert "full" not in fake_service.call_log[-1][1]
