"""Unit tests for the sub-client-backed ``view`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_VIEW_LIST = "mammoth.api.dataviews.DataviewsAPI.list"
_ACTIVE_USER_LIST = "mammoth.api.dataviews.DataviewsAPI.active_users"
_ACTIVE_USER_MARK = "mammoth.api.dataviews.DataviewsAPI.mark_active"
_BULK_DELETE = "mammoth.api.dataviews.DataviewsAPI.bulk_delete"
_PARAMETER_CONTEXT = "mammoth.api.dataviews.DataviewsAPI.parameter_context"
_PREVIEW = "mammoth.api.dataviews.DataviewsAPI.preview"
_RESTORE = "mammoth.api.dataviews.DataviewsAPI.restore"
_TRASH = "mammoth.api.dataviews.DataviewsAPI.trash"
_UPDATE = "mammoth.api.dataviews.DataviewsAPI.update"
_DATA_GET = "mammoth.api.dataviews.DataviewsAPI.get_data"
_DATA_QUERY = "mammoth.api.dataviews.DataviewsAPI.query_data"
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
_EXPORT_DELETE = "mammoth.api.exports.ExportsAPI.delete"
_EXPORT_GET = "mammoth.api.exports.ExportsAPI.get"
_EXPORT_LIST = "mammoth.api.exports.ExportsAPI.list"
_EXPORT_PUBLISH_DB = "mammoth.api.exports.ExportsAPI.publish_db"
_EXPORT_PUBLISH_DB_UPDATE = "mammoth.api.exports.ExportsAPI.publish_db_update"
_EXPORT_UPDATE = "mammoth.api.exports.ExportsAPI.update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


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


def test_view_list_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_list(_inv("view.list", project=180))
    assert excinfo.value.code == "missing_argument"


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
        _inv("view.active-user.list", project=180, extra_args=["9", "7"])
    )
    assert fake_service.call_log == [
        (_ACTIVE_USER_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_active_user_list_requires_dataview_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_active_user_list(_inv("view.active-user.list", project=180, extra_args=["9"]))
    assert excinfo.value.code == "missing_argument"


def test_active_user_mark_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_active_user_mark(
        _inv("view.active-user.mark", project=180, extra_args=["9", "7"])
    )
    assert fake_service.call_log == [
        (_ACTIVE_USER_MARK, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_parameter_context_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_parameter_context(
        _inv("view.parameter-context", project=180, extra_args=["9", "7"])
    )
    assert fake_service.call_log == [
        (_PARAMETER_CONTEXT, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_preview_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_PREVIEW, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_preview_forwards_rows_cols(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"rows": 5, "cols": 3})
    view_cmd.view_preview(_inv("view.preview", project=180, extra_args=["9", "7"], input_file=doc))
    assert fake_service.call_log == [
        (_PREVIEW, {"dataset_id": 9, "dataview_id": 7, "project_id": 180, "rows": 5, "cols": 3})
    ]


def test_restore_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_restore(_inv("view.restore", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_RESTORE, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_trash_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_trash(_inv("view.trash", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_TRASH, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_update_requires_patch_data(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_update(_inv("view.update", project=180, extra_args=["9", "7"]))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_patch_data(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"patch_data": [{"op": "replace", "path": "/name", "value": "x"}]})
    view_cmd.view_update(_inv("view.update", project=180, extra_args=["9", "7"], input_file=doc))
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "patch_data": [{"op": "replace", "path": "/name", "value": "x"}],
                "project_id": 180,
            },
        )
    ]


def test_data_get_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_get(_inv("view.data.get", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_DATA_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_data_get_forwards_timeout_poll_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"timeout": 30, "poll_interval": 1})
    view_cmd.view_data_get(
        _inv("view.data.get", project=180, extra_args=["9", "7"], input_file=doc)
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


def test_data_query_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_query(_inv("view.data.query", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_DATA_QUERY, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_data_query_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(
        tmp_path,
        {
            "sequence": 1,
            "offset": 10,
            "limit": 100,
            "columns": ["a", "b"],
            "condition": {"op": "eq"},
            "sort": "(a:asc)",
        },
    )
    view_cmd.view_data_query(
        _inv("view.data.query", project=180, extra_args=["9", "7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DATA_QUERY,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "project_id": 180,
                "sequence": 1,
                "offset": 10,
                "limit": 100,
                "columns": ["a", "b"],
                "condition": {"op": "eq"},
                "sort": "(a:asc)",
            },
        )
    ]


def test_conditional_format_create_requires_rule(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_create(
            _inv("view.conditional-format.create", project=180, extra_args=["9", "7"])
        )
    assert excinfo.value.code == "missing_field"


def test_conditional_format_create_forwards_rule(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"rule": {"color": "red"}})
    view_cmd.view_conditional_format_create(
        _inv("view.conditional-format.create", project=180, extra_args=["9", "7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CF_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "rule": {"color": "red"}, "project_id": 180},
        )
    ]


def test_conditional_format_delete_all_blocked_without_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_delete_all(
            _inv(
                "view.conditional-format.delete-all",
                project=180,
                extra_args=["9", "7"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_conditional_format_delete_all_proceeds_with_yes(
    fake_service: FakeMammothService,
) -> None:
    view_cmd.view_conditional_format_delete_all(
        _inv("view.conditional-format.delete-all", project=180, extra_args=["9", "7"], yes=True)
    )
    assert fake_service.call_log == [
        (_CF_DELETE_ALL, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_conditional_format_list_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_conditional_format_list(
        _inv("view.conditional-format.list", project=180, extra_args=["9", "7"])
    )
    assert fake_service.call_log == [
        (_CF_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_conditional_format_update_requires_rule(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_conditional_format_update(
            _inv("view.conditional-format.update", project=180, extra_args=["9", "7"])
        )
    assert excinfo.value.code == "missing_field"


def test_conditional_format_update_forwards_rule(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"rule": {"color": "blue"}})
    view_cmd.view_conditional_format_update(
        _inv("view.conditional-format.update", project=180, extra_args=["9", "7"], input_file=doc)
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
            _inv("view.checkpoint.create", project=180, extra_args=["9", "7"])
        )
    assert excinfo.value.code == "missing_field"


def test_checkpoint_create_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"name": "cp1"}})
    view_cmd.view_checkpoint_create(
        _inv("view.checkpoint.create", project=180, extra_args=["9", "7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CKPT_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "body": {"name": "cp1"}, "project_id": 180},
        )
    ]


def test_checkpoint_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_checkpoint_delete(
            _inv("view.checkpoint.delete", project=180, extra_args=["9", "7", "3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_checkpoint_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_checkpoint_delete(
        _inv("view.checkpoint.delete", project=180, extra_args=["9", "7", "3"], yes=True)
    )
    assert fake_service.call_log == [
        (_CKPT_DELETE, {"dataset_id": 9, "dataview_id": 7, "checkpoint_id": 3, "project_id": 180})
    ]


def test_checkpoint_delete_requires_checkpoint_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_checkpoint_delete(
            _inv("view.checkpoint.delete", project=180, extra_args=["9", "7"], yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_checkpoint_get_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_checkpoint_get(
        _inv("view.checkpoint.get", project=180, extra_args=["9", "7", "3"])
    )
    assert fake_service.call_log == [
        (_CKPT_GET, {"dataset_id": 9, "dataview_id": 7, "checkpoint_id": 3, "project_id": 180})
    ]


def test_checkpoint_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id,name"})
    view_cmd.view_checkpoint_get(
        _inv("view.checkpoint.get", project=180, extra_args=["9", "7", "3"], input_file=doc)
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
        _inv("view.checkpoint.list", project=180, extra_args=["9", "7"], input_file=doc)
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
            _inv("view.checkpoint.update", project=180, extra_args=["9", "7", "3"])
        )
    assert excinfo.value.code == "missing_field"


def test_checkpoint_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"name": "cp2"}})
    view_cmd.view_checkpoint_update(
        _inv("view.checkpoint.update", project=180, extra_args=["9", "7", "3"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _CKPT_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "checkpoint_id": 3,
                "body": {"name": "cp2"},
                "project_id": 180,
            },
        )
    ]


# ── data checks ──────────────────────────────────────────────────────────────


def test_data_check_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_check_create(
            _inv("view.data-check.create", project=180, extra_args=["9", "7"])
        )
    assert excinfo.value.code == "missing_field"


def test_data_check_create_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"rule": "not_null"}})
    view_cmd.view_data_check_create(
        _inv("view.data-check.create", project=180, extra_args=["9", "7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DC_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "body": {"rule": "not_null"}, "project_id": 180},
        )
    ]


def test_data_check_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_check_delete(
            _inv("view.data-check.delete", project=180, extra_args=["9", "7", "3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_data_check_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_data_check_delete(
        _inv("view.data-check.delete", project=180, extra_args=["9", "7", "3"], yes=True)
    )
    assert fake_service.call_log == [
        (_DC_DELETE, {"dataset_id": 9, "dataview_id": 7, "data_check_id": 3, "project_id": 180})
    ]


def test_data_check_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id"})
    view_cmd.view_data_check_get(
        _inv("view.data-check.get", project=180, extra_args=["9", "7", "3"], input_file=doc)
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
    view_cmd.view_data_check_list(_inv("view.data-check.list", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_DC_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_data_check_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_data_check_update(
            _inv("view.data-check.update", project=180, extra_args=["9", "7", "3"])
        )
    assert excinfo.value.code == "missing_field"


def test_data_check_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"rule": "unique"}})
    view_cmd.view_data_check_update(
        _inv("view.data-check.update", project=180, extra_args=["9", "7", "3"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DC_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "data_check_id": 3,
                "body": {"rule": "unique"},
                "project_id": 180,
            },
        )
    ]


# ── derivatives ───────────────────────────────────────────────────────────


def test_derivative_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_create(
            _inv("view.derivative.create", project=180, extra_args=["9", "7"])
        )
    assert excinfo.value.code == "missing_field"


def test_derivative_create_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"kind": "chart"}})
    view_cmd.view_derivative_create(
        _inv("view.derivative.create", project=180, extra_args=["9", "7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DERIV_CREATE,
            {"dataset_id": 9, "dataview_id": 7, "body": {"kind": "chart"}, "project_id": 180},
        )
    ]


def test_derivative_data_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_data(
            _inv("view.derivative.data", project=180, extra_args=["9", "7", "3"])
        )
    assert excinfo.value.code == "missing_field"


def test_derivative_data_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"filter": "x"}})
    view_cmd.view_derivative_data(
        _inv("view.derivative.data", project=180, extra_args=["9", "7", "3"], input_file=doc)
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
            _inv("view.derivative.delete", project=180, extra_args=["9", "7", "3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_derivative_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_derivative_delete(
        _inv("view.derivative.delete", project=180, extra_args=["9", "7", "3"], yes=True)
    )
    assert fake_service.call_log == [
        (_DERIV_DELETE, {"dataset_id": 9, "dataview_id": 7, "derivative_id": 3, "project_id": 180})
    ]


def test_derivative_list_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_derivative_list(_inv("view.derivative.list", project=180, extra_args=["9", "7"]))
    assert fake_service.call_log == [
        (_DERIV_LIST, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]


def test_derivative_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_derivative_update(
            _inv("view.derivative.update", project=180, extra_args=["9", "7", "3"])
        )
    assert excinfo.value.code == "missing_field"


def test_derivative_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"kind": "table"}})
    view_cmd.view_derivative_update(
        _inv("view.derivative.update", project=180, extra_args=["9", "7", "3"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _DERIV_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "derivative_id": 3,
                "body": {"kind": "table"},
                "project_id": 180,
            },
        )
    ]


# ── pipeline versions ────────────────────────────────────────────────────


def test_version_apply_passes_ids(fake_service: FakeMammothService) -> None:
    view_cmd.view_version_apply(_inv("view.version.apply", project=180, extra_args=["9", "7", "3"]))
    assert fake_service.call_log == [
        (_VER_APPLY, {"dataset_id": 9, "dataview_id": 7, "version_id": 3, "project_id": 180})
    ]


def test_version_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_version_delete(
            _inv("view.version.delete", project=180, extra_args=["9", "7", "3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_version_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_cmd.view_version_delete(
        _inv("view.version.delete", project=180, extra_args=["9", "7", "3"], yes=True)
    )
    assert fake_service.call_log == [
        (_VER_DELETE, {"dataset_id": 9, "dataview_id": 7, "version_id": 3, "project_id": 180})
    ]


def test_version_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"fields": "id"})
    view_cmd.view_version_get(
        _inv("view.version.get", project=180, extra_args=["9", "7", "3"], input_file=doc)
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
        _inv("view.version.list", project=180, extra_args=["9", "7"], input_file=doc)
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
            _inv("view.version.update", project=180, extra_args=["9", "7", "3"])
        )
    assert excinfo.value.code == "missing_field"


def test_version_update_passes_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"body": {"name": "v2"}})
    view_cmd.view_version_update(
        _inv("view.version.update", project=180, extra_args=["9", "7", "3"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _VER_UPDATE,
            {
                "dataset_id": 9,
                "dataview_id": 7,
                "version_id": 3,
                "body": {"name": "v2"},
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


# ── draft.command ───────────────────────────────────────────────────────────


def test_draft_command_requires_command(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_draft_command(_inv("view.draft.command", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_draft_command_passes_command(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"command": "undo"})
    view_cmd.view_draft_command(_inv("view.draft.command", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_DRAFT_COMMAND, {"dataview_id": 7, "command": "undo"})]


def test_draft_command_forwards_dataset_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _doc(tmp_path, {"command": "undo", "dataset_id": 9})
    view_cmd.view_draft_command(_inv("view.draft.command", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_DRAFT_COMMAND, {"dataview_id": 7, "command": "undo", "dataset_id": 9})
    ]


# ── pipeline.* (no project scope) ───────────────────────────────────────────


def test_pipeline_edit_requires_patches(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_pipeline_edit(_inv("view.pipeline.edit", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_pipeline_edit_passes_patches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"patches": [{"op": "remove", "path": "/x"}]})
    view_cmd.view_pipeline_edit(_inv("view.pipeline.edit", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_PIPE_EDIT, {"dataview_id": 7, "patches": [{"op": "remove", "path": "/x"}]})
    ]


def test_pipeline_get_passes_dataview_id(fake_service: FakeMammothService) -> None:
    view_cmd.view_pipeline_get(_inv("view.pipeline.get", extra_args=["7"]))
    assert fake_service.call_log == [(_PIPE_GET, {"dataview_id": 7})]


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
        (_TASK_ADD, {"dataview_id": 7, "task_spec": {"kind": "filter"}})
    ]


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
    doc = _doc(tmp_path, {"export_spec": {"type": "csv"}})
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
    doc = _doc(tmp_path, {"export_spec": {"type": "csv"}, "dataset_id": 9})
    view_cmd.view_export_create(
        _inv("view.export.create", project=180, extra_args=["7"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (
            _EXPORT_CREATE,
            {
                "dataview_id": 7,
                "export_spec": {"type": "csv"},
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


def test_export_list_forwards_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _doc(tmp_path, {"limit": 10, "offset": 0, "status": "done"})
    view_cmd.view_export_list(_inv("view.export.list", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [
        (_EXPORT_LIST, {"dataview_id": 7, "limit": 10, "offset": 0, "status": "done"})
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
