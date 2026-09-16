"""Unit tests for the read-only ``project`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import project as project_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST_SYMBOL = "mammoth.api.projects.ProjectsAPI.list"
_GET_SYMBOL = "mammoth.api.projects.ProjectsAPI.get"
_DEPS_SYMBOL = "mammoth.api.projects.ProjectsAPI.resource_dependencies"
_DEPS_UPDATE_SYMBOL = "mammoth.api.projects.ProjectsAPI.resource_dependencies_update"
_PUBCRED_SYMBOL = "mammoth.api.projects.ProjectsAPI.publish_credentials"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _invocation(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_project_list_passes_default_limit(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST_SYMBOL] = {"projects": [{"id": 1}]}
    data, meta = project_cmd.project_list(_invocation("project.list"))
    assert data == {"projects": [{"id": 1}]}
    assert fake_service.call_log == [(_LIST_SYMBOL, {"limit": 100})]
    assert meta["workspace_id"] == 4
    assert "close" in fake_service.calls


def test_project_list_reads_limit_from_input(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 5}), encoding="utf-8")
    project_cmd.project_list(_invocation("project.list", input_file=str(doc)))
    assert fake_service.call_log[0] == (_LIST_SYMBOL, {"limit": 5})


def test_project_get_uses_positional_id(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET_SYMBOL] = {"id": 180}
    data, meta = project_cmd.project_get(_invocation("project.get", extra_args=["180"]))
    assert data == {"id": 180}
    assert fake_service.call_log == [(_GET_SYMBOL, {"project": 180})]
    assert meta["project_id"] == 180


def test_project_get_uses_project_flag_when_no_positional(
    fake_service: FakeMammothService,
) -> None:
    project_cmd.project_get(_invocation("project.get", project=42))
    assert fake_service.call_log == [(_GET_SYMBOL, {"project": 42})]


def test_project_get_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_get(_invocation("project.get"))
    assert excinfo.value.code == "project_required"


def test_project_get_non_integer_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_get(_invocation("project.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"


def test_resource_dependencies_requires_resource_ids(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_resource_dependencies(
            _invocation("project.resource-dependencies", project=1)
        )
    assert excinfo.value.code == "missing_field"


def test_resource_dependencies_forwards_optional_recursive(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"resource_ids": ["a", "b"], "is_recursive": True}), encoding="utf-8")
    project_cmd.project_resource_dependencies(
        _invocation("project.resource-dependencies", project=7, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_DEPS_SYMBOL, {"project_id": 7, "resource_ids": ["a", "b"], "is_recursive": True})
    ]


def test_resource_dependencies_update_requires_project_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "patches": [
                    {
                        "op": "replace",
                        "path": "data_sync",
                        "value": {"context_type": "dataview", "context_id": 42},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_resource_dependencies_update(
            _invocation("project.resource-dependencies.update", project=7, input_file=str(doc))
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_resource_dependencies_update_forwards_patch_and_waits(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    patches = [
        {
            "op": "replace",
            "path": "data_sync",
            "value": {"context_type": "task", "context_id": 9, "data_pass_through": None},
        }
    ]
    doc.write_text(json.dumps({"patches": patches}), encoding="utf-8")
    fake_service.responses[_DEPS_UPDATE_SYMBOL] = {"job_id": 801}
    fake_service.job_result = {"status": "completed"}
    data, meta = project_cmd.project_resource_dependencies_update(
        _invocation(
            "project.resource-dependencies.update",
            project=7,
            input_file=str(doc),
            yes=True,
            confirm="7",
            no_input=True,
            output="json",
        )
    )
    assert data == {"job_id": 801, "status": "completed"}
    assert fake_service.call_log[0] == (_DEPS_UPDATE_SYMBOL, {"project_id": 7, "patches": patches})
    assert fake_service.wait_log == [{"job_id": 801}]
    assert meta["project_id"] == 7


def test_resource_dependencies_update_rejects_duplicate_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    patch = {
        "op": "replace",
        "path": "data_sync",
        "value": {"context_type": "action", "context_id": 3},
    }
    doc.write_text(json.dumps({"patches": [patch, patch]}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_resource_dependencies_update(
            _invocation(
                "project.resource-dependencies.update",
                project=7,
                input_file=str(doc),
                yes=True,
                confirm="7",
                no_input=True,
                output="json",
            )
        )
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_publish_credentials_requires_odbc_type(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        project_cmd.project_publish_credentials(
            _invocation("project.publish-credentials", project=1)
        )
    assert excinfo.value.code == "missing_field"


def test_publish_credentials_forwards_odbc_type(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"odbc_type": "postgres"}), encoding="utf-8")
    project_cmd.project_publish_credentials(
        _invocation("project.publish-credentials", project=9, input_file=str(doc))
    )
    assert fake_service.call_log == [(_PUBCRED_SYMBOL, {"project_id": 9, "odbc_type": "postgres"})]
