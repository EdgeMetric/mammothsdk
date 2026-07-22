"""Unit tests for the ``snippet`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import snippet as snippet_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CREATE = "mammoth.api.snippets.SnippetsAPI.create"
_DELETE = "mammoth.api.snippets.SnippetsAPI.delete"
_DEPENDENCIES = "mammoth.api.snippets.SnippetsAPI.dependencies"
_DUPLICATE = "mammoth.api.snippets.SnippetsAPI.duplicate"
_GET = "mammoth.api.snippets.SnippetsAPI.get"
_LIST = "mammoth.api.snippets.SnippetsAPI.list"
_RERUN = "mammoth.api.snippets.SnippetsAPI.rerun"
_UPDATE = "mammoth.api.snippets.SnippetsAPI.update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


# --- create -----------------------------------------------------------------


def test_create_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_create(_inv("snippet.create"))
    assert excinfo.value.code == "project_required"


def test_create_requires_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"code": "1+1", "language": "python"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_create(_inv("snippet.create", project=180, input_file=str(doc)))
    assert excinfo.value.code == "missing_argument"


def test_create_requires_code(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "Snip", "language": "python"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_create(_inv("snippet.create", project=180, input_file=str(doc)))
    assert excinfo.value.code == "missing_field"


def test_create_requires_language(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "Snip", "code": "1+1"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_create(_inv("snippet.create", project=180, input_file=str(doc)))
    assert excinfo.value.code == "missing_field"


def test_create_uses_positional_name(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"code": "1+1", "language": "python"}), encoding="utf-8")
    snippet_cmd.snippet_create(
        _inv("snippet.create", project=180, extra_args=["Snip"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {"name": "Snip", "code": "1+1", "language": "python", "project_id": 180},
        )
    ]


def test_create_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "name": "Snip",
                "code": "1+1",
                "language": "python",
                "description": "desc",
                "group_id": 9,
                "scope": "workspace",
            }
        ),
        encoding="utf-8",
    )
    snippet_cmd.snippet_create(_inv("snippet.create", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "Snip",
                "code": "1+1",
                "language": "python",
                "project_id": 180,
                "description": "desc",
                "group_id": 9,
                "scope": "workspace",
            },
        )
    ]


# --- delete -------------------------------------------------------------------


def test_delete_requires_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_delete(_inv("snippet.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_delete(_inv("snippet.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    snippet_cmd.snippet_delete(_inv("snippet.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"snippet_id": 7})]


# --- dependencies ---------------------------------------------------------


def test_dependencies_requires_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_dependencies(_inv("snippet.dependencies"))
    assert excinfo.value.code == "missing_argument"


def test_dependencies_uses_positional(fake_service: FakeMammothService) -> None:
    snippet_cmd.snippet_dependencies(_inv("snippet.dependencies", extra_args=["7"]))
    assert fake_service.call_log == [(_DEPENDENCIES, {"snippet_id": 7})]


# --- duplicate --------------------------------------------------------------


def test_duplicate_requires_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_duplicate(_inv("snippet.duplicate"))
    assert excinfo.value.code == "missing_argument"


def test_duplicate_uses_positional(fake_service: FakeMammothService) -> None:
    snippet_cmd.snippet_duplicate(_inv("snippet.duplicate", extra_args=["7"]))
    assert fake_service.call_log == [(_DUPLICATE, {"snippet_id": 7})]


# --- get ---------------------------------------------------------------------


def test_get_requires_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_get(_inv("snippet.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_get(_inv("snippet.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"


def test_get_uses_positional(fake_service: FakeMammothService) -> None:
    snippet_cmd.snippet_get(_inv("snippet.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"snippet_id": 7})]


# --- list ----------------------------------------------------------------


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_list(_inv("snippet.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project_and_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"limit": 10, "offset": 5, "search": "q", "group_id": 3, "sort": "name"}),
        encoding="utf-8",
    )
    snippet_cmd.snippet_list(_inv("snippet.list", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _LIST,
            {
                "project_id": 180,
                "limit": 10,
                "offset": 5,
                "search": "q",
                "group_id": 3,
                "sort": "name",
            },
        )
    ]


def test_list_without_optional_fields(fake_service: FakeMammothService) -> None:
    snippet_cmd.snippet_list(_inv("snippet.list", project=180))
    assert fake_service.call_log == [(_LIST, {"project_id": 180})]


# --- rerun -----------------------------------------------------------------


def test_rerun_requires_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_rerun(_inv("snippet.rerun"))
    assert excinfo.value.code == "missing_argument"


def test_rerun_uses_positional(fake_service: FakeMammothService) -> None:
    snippet_cmd.snippet_rerun(_inv("snippet.rerun", extra_args=["7"]))
    assert fake_service.call_log == [(_RERUN, {"snippet_id": 7})]


# --- update ------------------------------------------------------------------


def test_update_requires_snippet_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_update(_inv("snippet.update"))
    assert excinfo.value.code == "missing_argument"


def test_update_requires_at_least_one_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        snippet_cmd.snippet_update(_inv("snippet.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"name": "New", "code": "2+2", "language": "python", "group_id": 4}),
        encoding="utf-8",
    )
    snippet_cmd.snippet_update(_inv("snippet.update", extra_args=["7"], input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "snippet_id": 7,
                "name": "New",
                "code": "2+2",
                "language": "python",
                "group_id": 4,
            },
        )
    ]
