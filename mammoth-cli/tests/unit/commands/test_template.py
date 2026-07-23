"""Unit tests for the ``template`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import template as template_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_CREATE = "mammoth.api.templates.TemplatesAPI.create"
_DELETE = "mammoth.api.templates.TemplatesAPI.delete"
_GET = "mammoth.api.templates.TemplatesAPI.get"
_LIST = "mammoth.api.templates.TemplatesAPI.list"
_UPDATE = "mammoth.api.templates.TemplatesAPI.update"


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


# --- create ----------------------------------------------------------------


def test_create_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_create(_inv("template.create"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_forwards_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"name": "Weekly report"}})
    template_cmd.template_create(_inv("template.create", input_file=doc))
    assert fake_service.call_log == [(_CREATE, {"body": {"name": "Weekly report"}})]


# --- delete ------------------------------------------------------------------


def test_delete_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_delete(_inv("template.delete", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_delete_invalid_positional_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_delete(_inv("template.delete", extra_args=["nope"], yes=True))
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_delete(_inv("template.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    template_cmd.template_delete(_inv("template.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"template_id": 7})]


# --- get -----------------------------------------------------------------------


def test_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_get(_inv("template.get"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_get_uses_positional_template_id(fake_service: FakeMammothService) -> None:
    template_cmd.template_get(_inv("template.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"template_id": 7})]


# --- list ------------------------------------------------------------------------


def test_list_no_args(fake_service: FakeMammothService) -> None:
    template_cmd.template_list(_inv("template.list"))
    assert fake_service.call_log == [(_LIST, {})]


# --- update ----------------------------------------------------------------------


def test_update_requires_positional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"name": "New name"}})
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_update(_inv("template.update", input_file=doc))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_update_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        template_cmd.template_update(_inv("template.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_forwards_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"name": "New name"}})
    template_cmd.template_update(_inv("template.update", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_UPDATE, {"template_id": 7, "body": {"name": "New name"}})]
