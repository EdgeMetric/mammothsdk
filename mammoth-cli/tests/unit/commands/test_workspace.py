"""Unit tests for the ``workspace`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import workspace as workspace_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_ACCEPT_INVITE = "mammoth.api.workspaces.WorkspacesAPI.accept_invite"
_APP_USAGE = "mammoth.api.workspaces.WorkspacesAPI.app_usage"
_CHECK_EXPRESSION = "mammoth.api.workspaces.WorkspacesAPI.check_expression"
_CREATE = "mammoth.api.workspaces.WorkspacesAPI.create"
_DELETE = "mammoth.api.workspace.WorkspaceAPI.delete"
_GET = "mammoth.api.workspace.WorkspaceAPI.get"
_LIST = "mammoth.api.workspace.WorkspaceAPI.list"
_LLM_TASK = "mammoth.api.workspaces.WorkspacesAPI.llm_task"
_REACTIVATE = "mammoth.api.workspace.WorkspaceAPI.reactivate"
_SEGMENT_LIST = "mammoth.api.workspaces.WorkspacesAPI.segment_list"
_SEGMENT_UPDATE = "mammoth.api.workspaces.WorkspacesAPI.segment_update"
_STORAGE_BREAKDOWN = "mammoth.api.workspaces.WorkspacesAPI.storage_breakdown"
_UPDATE = "mammoth.api.workspace.WorkspaceAPI.update"
_USER_ADD = "mammoth.api.workspaces.WorkspacesAPI.user_add"
_USER_GET = "mammoth.api.workspace.WorkspaceAPI.get_user"
_USER_LIST = "mammoth.api.workspace.WorkspaceAPI.list_users"
_USER_REMOVE = "mammoth.api.workspaces.WorkspacesAPI.user_remove"
_USER_REMOVE_BATCH = "mammoth.api.workspaces.WorkspacesAPI.user_remove_batch"
_USER_UPDATE = "mammoth.api.workspace.WorkspaceAPI.update_user"
_USER_UPDATE_BATCH = "mammoth.api.workspaces.WorkspacesAPI.user_update_batch"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, data: object) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(data), encoding="utf-8")
    return str(doc)


# --- accept-invite -----------------------------------------------------------


def test_accept_invite_requires_token(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_accept_invite(_inv("workspace.accept-invite"))
    assert excinfo.value.code == "missing_field"


def test_accept_invite_forwards_token(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"token": "tok-1"})
    workspace_cmd.workspace_accept_invite(_inv("workspace.accept-invite", input_file=doc))
    assert fake_service.call_log == [(_ACCEPT_INVITE, {"token": "tok-1"})]


# --- app-usage ----------------------------------------------------------------


def test_app_usage_no_fields(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_app_usage(_inv("workspace.app-usage"))
    assert fake_service.call_log == [(_APP_USAGE, {})]


def test_app_usage_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"fields": "id,name"})
    workspace_cmd.workspace_app_usage(_inv("workspace.app-usage", input_file=doc))
    assert fake_service.call_log == [(_APP_USAGE, {"fields": "id,name"})]


# --- check-expression ----------------------------------------------------------


def test_check_expression_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_check_expression(_inv("workspace.check-expression"))
    assert excinfo.value.code == "missing_field"


def test_check_expression_forwards_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"intent": "validate 1+1"}
    doc = _write(tmp_path, {"body": body})
    workspace_cmd.workspace_check_expression(_inv("workspace.check-expression", input_file=doc))
    assert fake_service.call_log == [(_CHECK_EXPRESSION, {"body": body})]


# --- create --------------------------------------------------------------------


def test_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_create(_inv("workspace.create"))
    assert excinfo.value.code == "missing_field"


def test_create_forwards_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"name": "New WS"}})
    workspace_cmd.workspace_create(_inv("workspace.create", input_file=doc))
    assert fake_service.call_log == [(_CREATE, {"body": {"name": "New WS"}})]


# --- delete ----------------------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_delete(_inv("workspace.delete", extra_args=["9"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_requires_confirm_target(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_delete(
            _inv("workspace.delete", extra_args=["9"], yes=True, confirm="999")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_delete_proceeds_with_matching_target(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_delete(
        _inv("workspace.delete", extra_args=["9"], yes=True, confirm="9")
    )
    assert fake_service.call_log == [(_DELETE, {"workspace_id": 9})]


def test_delete_defaults_target_to_auth_workspace(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_delete(_inv("workspace.delete", yes=True, confirm="4"))
    assert fake_service.call_log == [(_DELETE, {})]


# --- get -----------------------------------------------------------------------


def test_get_without_positional_omits_workspace_id(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_get(_inv("workspace.get"))
    assert fake_service.call_log == [(_GET, {})]


def test_get_with_positional_passes_workspace_id(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_get(_inv("workspace.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"workspace_id": 7})]


def test_get_invalid_positional_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_get(_inv("workspace.get", extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


# --- list ------------------------------------------------------------------------


def test_list_default_limit(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_list(_inv("workspace.list"))
    assert fake_service.call_log == [(_LIST, {"limit": 100})]


def test_list_forwards_limit(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"limit": 10})
    workspace_cmd.workspace_list(_inv("workspace.list", input_file=doc))
    assert fake_service.call_log == [(_LIST, {"limit": 10})]


# --- llm-task -----------------------------------------------------------------


def test_llm_task_requires_task_type_and_params(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_llm_task(_inv("workspace.llm-task"))
    assert excinfo.value.code == "missing_field"


def test_llm_task_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"task_type": "generate_summary", "params": {"a": 1}})
    workspace_cmd.workspace_llm_task(_inv("workspace.llm-task", input_file=doc))
    assert fake_service.call_log == [
        (_LLM_TASK, {"task_type": "generate_summary", "params": {"a": 1}})
    ]


# --- reactivate ------------------------------------------------------------------


def test_reactivate_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_reactivate(
            _inv("workspace.reactivate", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_reactivate_proceeds_with_matching_target(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_reactivate(
        _inv("workspace.reactivate", extra_args=["9"], yes=True, confirm="9")
    )
    assert fake_service.call_log == [(_REACTIVATE, {"workspace_id": 9})]


def test_reactivate_defaults_target_to_auth_workspace(
    fake_service: FakeMammothService,
) -> None:
    workspace_cmd.workspace_reactivate(_inv("workspace.reactivate", yes=True, confirm="4"))
    assert fake_service.call_log == [(_REACTIVATE, {})]


# --- segment list/update -----------------------------------------------------------


def test_segment_list(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_segment_list(_inv("workspace.segment.list"))
    assert fake_service.call_log == [(_SEGMENT_LIST, {})]


def test_segment_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_segment_update(_inv("workspace.segment.update"))
    assert excinfo.value.code == "missing_field"


def test_segment_update_forwards_patch(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"patch": [{"op": "add", "path": "segments", "value": "Beta"}]})
    workspace_cmd.workspace_segment_update(_inv("workspace.segment.update", input_file=doc))
    assert fake_service.call_log == [
        (_SEGMENT_UPDATE, {"patch": [{"op": "add", "path": "segments", "value": "Beta"}]})
    ]


# --- storage-breakdown ----------------------------------------------------------


def test_storage_breakdown_no_fields(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_storage_breakdown(_inv("workspace.storage-breakdown"))
    assert fake_service.call_log == [(_STORAGE_BREAKDOWN, {})]


def test_storage_breakdown_forwards_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"limit": 5, "offset": 10})
    workspace_cmd.workspace_storage_breakdown(_inv("workspace.storage-breakdown", input_file=doc))
    assert fake_service.call_log == [(_STORAGE_BREAKDOWN, {"limit": 5, "offset": 10})]


# --- update ----------------------------------------------------------------------


def test_update_requires_patches(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_update(_inv("workspace.update", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_field"


def test_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patches": [{"op": "replace", "path": "name", "value": "X"}]})
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_update(_inv("workspace.update", input_file=doc, output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_proceeds_with_explicit_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patches": [{"op": "replace", "path": "name", "value": "X"}]})
    workspace_cmd.workspace_update(
        _inv("workspace.update", extra_args=["9"], input_file=doc, yes=True, confirm="9")
    )
    assert fake_service.call_log == [
        (_UPDATE, {"patches": [{"op": "replace", "path": "name", "value": "X"}], "workspace_id": 9})
    ]


def test_update_defaults_target_to_auth_workspace(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patches": [{"op": "replace", "path": "name", "value": "X"}]})
    workspace_cmd.workspace_update(_inv("workspace.update", input_file=doc, yes=True, confirm="4"))
    assert fake_service.call_log == [
        (_UPDATE, {"patches": [{"op": "replace", "path": "name", "value": "X"}]})
    ]


# --- user add ------------------------------------------------------------------


def test_user_add_requires_email_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_add(_inv("workspace.user.add"))
    assert excinfo.value.code == "missing_field"


def test_user_add_forwards_projects(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"email_ids": ["a@x.com"], "projects": [{"project_id": 1}]})
    workspace_cmd.workspace_user_add(_inv("workspace.user.add", input_file=doc))
    assert fake_service.call_log == [
        (_USER_ADD, {"email_ids": ["a@x.com"], "projects": [{"project_id": 1}]})
    ]


# --- user get/list ---------------------------------------------------------------


def test_user_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_get(_inv("workspace.user.get"))
    assert excinfo.value.code == "missing_argument"


def test_user_get_uses_positional_never_passes_workspace_id(
    fake_service: FakeMammothService,
) -> None:
    workspace_cmd.workspace_user_get(_inv("workspace.user.get", extra_args=["u1"]))
    assert fake_service.call_log == [(_USER_GET, {"user_id": "u1"})]


def test_user_list_never_passes_workspace_id(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_user_list(_inv("workspace.user.list"))
    assert fake_service.call_log == [(_USER_LIST, {})]


# --- user remove / remove-batch --------------------------------------------------


def test_user_remove_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_remove(_inv("workspace.user.remove"))
    assert excinfo.value.code == "missing_argument"


def test_user_remove_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_remove(
            _inv("workspace.user.remove", extra_args=["3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_remove_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    workspace_cmd.workspace_user_remove(_inv("workspace.user.remove", extra_args=["3"], yes=True))
    assert fake_service.call_log == [(_USER_REMOVE, {"user_id": 3})]


def test_user_remove_batch_requires_ids_or_invite_ids(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_remove_batch(_inv("workspace.user.remove-batch", yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_user_remove_batch_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"ids": "1,2"})
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_remove_batch(
            _inv("workspace.user.remove-batch", input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_remove_batch_proceeds_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"ids": "1,2", "invite_ids": "5"})
    workspace_cmd.workspace_user_remove_batch(
        _inv("workspace.user.remove-batch", input_file=doc, yes=True)
    )
    assert fake_service.call_log == [(_USER_REMOVE_BATCH, {"ids": "1,2", "invite_ids": "5"})]


# --- user update / update-batch -------------------------------------------------


def test_user_update_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_update(_inv("workspace.user.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_user_update_requires_patches(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_update(
            _inv("workspace.user.update", extra_args=["u1"], yes=True, confirm="u1")
        )
    assert excinfo.value.code == "missing_field"


def test_user_update_requires_confirm_target_matching_user_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {"patches": [{"op": "replace", "path": "role", "value": "workspace_member"}]},
    )
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_update(
            _inv(
                "workspace.user.update",
                extra_args=["u1"],
                input_file=doc,
                yes=True,
                confirm="wrong",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_user_update_proceeds_with_matching_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {"patches": [{"op": "replace", "path": "role", "value": "workspace_member"}]},
    )
    workspace_cmd.workspace_user_update(
        _inv(
            "workspace.user.update",
            extra_args=["u1"],
            input_file=doc,
            yes=True,
            confirm="u1",
        )
    )
    assert fake_service.call_log == [
        (
            _USER_UPDATE,
            {
                "user_id": "u1",
                "patches": [{"op": "replace", "path": "role", "value": "workspace_member"}],
            },
        )
    ]


def test_user_update_batch_requires_patches(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_user_update_batch(_inv("workspace.user.update-batch"))
    assert excinfo.value.code == "missing_field"


def test_user_update_batch_forwards_patches(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patches": [{"op": "replace", "path": "role", "value": "x"}]})
    workspace_cmd.workspace_user_update_batch(_inv("workspace.user.update-batch", input_file=doc))
    assert fake_service.call_log == [
        (_USER_UPDATE_BATCH, {"patches": [{"op": "replace", "path": "role", "value": "x"}]})
    ]
