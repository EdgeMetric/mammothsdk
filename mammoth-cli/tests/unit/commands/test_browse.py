"""Unit tests for the ``browse`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import browse as browse_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_FOLDER = "mammoth.api.browse.BrowseAPI.folder_resources"
_PROJECT = "mammoth.api.projects.ProjectsAPI.browse"
_ROOT = "mammoth.api.browse.BrowseAPI.root"
_WORKSPACE = "mammoth.api.browse.BrowseAPI.workspace_resources"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


# -- browse.folder ---------------------------------------------------------


def test_folder_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_folder(_inv("browse.folder", extra_args=["7"]))
    assert excinfo.value.code == "project_required"


def test_folder_requires_folder_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_folder(_inv("browse.folder", project=180))
    assert excinfo.value.code == "missing_argument"


def test_folder_invalid_folder_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_folder(_inv("browse.folder", project=180, extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


def test_folder_passes_folder_and_project(fake_service: FakeMammothService) -> None:
    browse_cmd.browse_folder(_inv("browse.folder", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_FOLDER, {"folder_id": 7, "project_id": 180})]


def test_folder_forwards_level_and_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"level": 1, "fields": "id,name"}), encoding="utf-8")
    browse_cmd.browse_folder(
        _inv("browse.folder", project=180, extra_args=["7"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_FOLDER, {"folder_id": 7, "project_id": 180, "level": 1, "fields": "id,name"})
    ]


# -- browse.project ---------------------------------------------------------


def test_project_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_project(_inv("browse.project"))
    assert excinfo.value.code == "project_required"


def test_project_passes_project_id(fake_service: FakeMammothService) -> None:
    browse_cmd.browse_project(_inv("browse.project", project=180))
    assert fake_service.call_log == [(_PROJECT, {"project_id": 180})]


def test_project_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "fields": "id,name",
                "name": "Docs",
                "browse_type": "dataset",
                "sort": "name",
                "offset": 10,
                "limit": 20,
            }
        ),
        encoding="utf-8",
    )
    browse_cmd.browse_project(_inv("browse.project", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _PROJECT,
            {
                "project_id": 180,
                "fields": "id,name",
                "name": "Docs",
                "browse_type": "dataset",
                "sort": "name",
                "offset": 10,
                "limit": 20,
            },
        )
    ]


# -- browse.root -------------------------------------------------------------


def test_root_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    browse_cmd.browse_root(_inv("browse.root"))
    assert fake_service.call_log == [(_ROOT, {})]


def test_root_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"name": "Docs", "browse_type": "project", "include_hidden": True}),
        encoding="utf-8",
    )
    browse_cmd.browse_root(_inv("browse.root", input_file=str(doc)))
    assert fake_service.call_log == [
        (_ROOT, {"name": "Docs", "browse_type": "project", "include_hidden": True})
    ]


def test_root_meta_has_no_project_when_unset(fake_service: FakeMammothService) -> None:
    _, meta = browse_cmd.browse_root(_inv("browse.root"))
    assert meta["project_id"] is None


# -- browse.workspace ---------------------------------------------------------


def test_workspace_no_input_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    browse_cmd.browse_workspace(_inv("browse.workspace"))
    assert fake_service.call_log == [(_WORKSPACE, {})]


def test_workspace_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"level": 1, "fields": "id,name", "limit": 50}), encoding="utf-8")
    browse_cmd.browse_workspace(_inv("browse.workspace", input_file=str(doc)))
    assert fake_service.call_log == [(_WORKSPACE, {"level": 1, "fields": "id,name", "limit": 50})]


def test_workspace_meta_has_no_project_when_unset(fake_service: FakeMammothService) -> None:
    _, meta = browse_cmd.browse_workspace(_inv("browse.workspace"))
    assert meta["project_id"] is None
