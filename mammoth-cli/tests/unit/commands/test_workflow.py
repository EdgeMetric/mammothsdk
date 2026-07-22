"""Unit tests for the ``workflow`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import workflow as workflow_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.workflows.WorkflowsAPI.list"
_GET = "mammoth.api.workflows.WorkflowsAPI.get"
_GRAPH = "mammoth.api.workflows.WorkflowsAPI.graph"
_CLEANUP = "mammoth.api.workflows.WorkflowsAPI.cleanup"
_WS_DATASETS = "mammoth.api.workflows.WorkflowsAPI.workspace_datasets"
_WS_EXPORTS = "mammoth.api.workflows.WorkflowsAPI.workspace_exports"
_WS_SOURCES = "mammoth.api.workflows.WorkflowsAPI.workspace_sources"
_CREATE = "mammoth.api.workflows.WorkflowsAPI.create"
_UPDATE = "mammoth.api.workflows.WorkflowsAPI.update"
_DELETE = "mammoth.api.workflows.WorkflowsAPI.delete"
_FROM_TEMPLATE = "mammoth.api.workflows.WorkflowsAPI.from_template"
_CANVAS = "mammoth.api.workflows.WorkflowsAPI.canvas"
_BLOCK_ADD = "mammoth.api.workflows.WorkflowsAPI.block_add"
_BLOCK_AUTH = "mammoth.api.workflows.WorkflowsAPI.block_auth"
_BLOCK_CONFIG = "mammoth.api.workflows.WorkflowsAPI.block_config"
_BLOCK_TYPE = "mammoth.api.workflows.WorkflowsAPI.block_type"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# -- list / read-only project-scoped commands --------------------------------


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_list(_inv("workflow.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_list(_inv("workflow.list", project=180))
    assert fake_service.call_log == [(_LIST, {"project_id": 180})]


def test_get_uses_positional_workflow_id(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_get(_inv("workflow.get", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"workflow_id": 7, "project_id": 180})]


def test_get_without_workflow_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_get(_inv("workflow.get", project=180))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_workflow_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_get(_inv("workflow.get", project=180, extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


def test_graph_passes_project(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_graph(_inv("workflow.graph", project=180))
    assert fake_service.call_log == [(_GRAPH, {"project_id": 180})]


def test_cleanup_passes_project(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_cleanup(_inv("workflow.cleanup", project=180))
    assert fake_service.call_log == [(_CLEANUP, {"project_id": 180})]


def test_workspace_datasets_passes_project(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_workspace_datasets(_inv("workflow.workspace-datasets", project=180))
    assert fake_service.call_log == [(_WS_DATASETS, {"project_id": 180})]


def test_workspace_exports_passes_project(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_workspace_exports(_inv("workflow.workspace-exports", project=180))
    assert fake_service.call_log == [(_WS_EXPORTS, {"project_id": 180})]


def test_workspace_sources_passes_project(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_workspace_sources(_inv("workflow.workspace-sources", project=180))
    assert fake_service.call_log == [(_WS_SOURCES, {"project_id": 180})]


# -- create --------------------------------------------------------------


def test_create_uses_positional_name(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_create(_inv("workflow.create", project=180, extra_args=["Pipeline"]))
    assert fake_service.call_log == [(_CREATE, {"name": "Pipeline", "project_id": 180})]


def test_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_create(_inv("workflow.create", project=180))
    assert excinfo.value.code == "missing_argument"


def test_create_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(
        tmp_path,
        {"name": "Pipeline", "shape": "full", "purpose": "ETL", "seed_datasource_id": 9},
    )
    workflow_cmd.workflow_create(_inv("workflow.create", project=180, input_file=input_file))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "Pipeline",
                "project_id": 180,
                "shape": "full",
                "purpose": "ETL",
                "seed_datasource_id": 9,
            },
        )
    ]


# -- update --------------------------------------------------------------


def test_update_requires_a_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_update(_inv("workflow.update", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"name": "New", "notes": "n"})
    workflow_cmd.workflow_update(
        _inv("workflow.update", project=180, extra_args=["7"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (_UPDATE, {"workflow_id": 7, "project_id": 180, "name": "New", "notes": "n"})
    ]


def test_update_without_workflow_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_update(_inv("workflow.update", project=180))
    assert excinfo.value.code == "missing_argument"


# -- delete ----------------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_delete(
            _inv("workflow.delete", project=180, extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_delete(_inv("workflow.delete", project=180, extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"workflow_id": 7, "project_id": 180})]


# -- from-template -----------------------------------------------------------


def test_from_template_requires_workflow_name(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"template_id": 3})
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_from_template(
            _inv("workflow.from-template", project=180, input_file=input_file)
        )
    assert excinfo.value.code == "missing_argument"


def test_from_template_requires_template_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_from_template(
            _inv("workflow.from-template", project=180, extra_args=["Copy"])
        )
    assert excinfo.value.code == "missing_field"


def test_from_template_uses_positional_name_and_input_template_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"template_id": 3})
    workflow_cmd.workflow_from_template(
        _inv("workflow.from-template", project=180, extra_args=["Copy"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (_FROM_TEMPLATE, {"template_id": 3, "workflow_name": "Copy", "project_id": 180})
    ]


def test_from_template_name_from_input_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"template_id": 3, "workflow_name": "Copy"})
    workflow_cmd.workflow_from_template(
        _inv("workflow.from-template", project=180, input_file=input_file)
    )
    assert fake_service.call_log == [
        (_FROM_TEMPLATE, {"template_id": 3, "workflow_name": "Copy", "project_id": 180})
    ]


# -- canvas ------------------------------------------------------------------


def test_canvas_requires_canvas_state(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_canvas(_inv("workflow.canvas", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_canvas_forwards_state(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"canvas_state": {"nodes": []}})
    workflow_cmd.workflow_canvas(
        _inv("workflow.canvas", project=180, extra_args=["7"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (_CANVAS, {"workflow_id": 7, "canvas_state": {"nodes": []}, "project_id": 180})
    ]


# -- block.add -----------------------------------------------------------


def test_block_add_requires_block_type(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_block_add(_inv("workflow.block.add", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_block_add_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path,
        {
            "block_type": "source",
            "display_name": "Source A",
            "connection_type": "s3",
            "position_hint": {"x": 1, "y": 2},
        },
    )
    workflow_cmd.workflow_block_add(
        _inv("workflow.block.add", project=180, extra_args=["7"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _BLOCK_ADD,
            {
                "workflow_id": 7,
                "block_type": "source",
                "project_id": 180,
                "display_name": "Source A",
                "connection_type": "s3",
                "position_hint": {"x": 1, "y": 2},
            },
        )
    ]


# -- block.auth ------------------------------------------------------------


def test_block_auth_uses_two_positionals(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"auth_data": {"token": "t"}})
    workflow_cmd.workflow_block_auth(
        _inv("workflow.block.auth", project=180, extra_args=["7", "3"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _BLOCK_AUTH,
            {
                "workflow_id": 7,
                "block_id": 3,
                "auth_data": {"token": "t"},
                "project_id": 180,
            },
        )
    ]


def test_block_auth_requires_block_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_block_auth(_inv("workflow.block.auth", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_argument"


def test_block_auth_requires_auth_data(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_block_auth(
            _inv("workflow.block.auth", project=180, extra_args=["7", "3"])
        )
    assert excinfo.value.code == "missing_field"


# -- block.config ----------------------------------------------------------


def test_block_config_uses_two_positionals(fake_service: FakeMammothService) -> None:
    workflow_cmd.workflow_block_config(
        _inv("workflow.block.config", project=180, extra_args=["7", "3"])
    )
    assert fake_service.call_log == [
        (_BLOCK_CONFIG, {"workflow_id": 7, "block_id": 3, "project_id": 180})
    ]


def test_block_config_requires_block_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_block_config(
            _inv("workflow.block.config", project=180, extra_args=["7"])
        )
    assert excinfo.value.code == "missing_argument"


# -- block.type ------------------------------------------------------------


def test_block_type_uses_two_positionals_and_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"connection_type": "gcs"})
    workflow_cmd.workflow_block_type(
        _inv("workflow.block.type", project=180, extra_args=["7", "3"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _BLOCK_TYPE,
            {"workflow_id": 7, "block_id": 3, "connection_type": "gcs", "project_id": 180},
        )
    ]


def test_block_type_requires_connection_type(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_block_type(
            _inv("workflow.block.type", project=180, extra_args=["7", "3"])
        )
    assert excinfo.value.code == "missing_field"
