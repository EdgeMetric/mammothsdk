"""Unit tests for the ``parameter`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import parameter as parameter_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CREATE = "mammoth.api.parameters.ParametersAPI.create"
_DELETE = "mammoth.api.parameters.ParametersAPI.delete"
_DEPENDENCIES = "mammoth.api.parameters.ParametersAPI.dependencies"
_DUPLICATE = "mammoth.api.parameters.ParametersAPI.duplicate"
_GET = "mammoth.api.parameters.ParametersAPI.get"
_GROUP_CREATE = "mammoth.api.parameters.ParametersAPI.group_create"
_GROUP_DELETE = "mammoth.api.parameters.ParametersAPI.group_delete"
_GROUP_LIST = "mammoth.api.parameters.ParametersAPI.group_list"
_GROUP_REORDER = "mammoth.api.parameters.ParametersAPI.group_reorder"
_GROUP_UPDATE = "mammoth.api.parameters.ParametersAPI.group_update"
_LIST = "mammoth.api.parameters.ParametersAPI.list"
_RERUN = "mammoth.api.parameters.ParametersAPI.rerun"
_RERUN_ALL_STALE = "mammoth.api.parameters.ParametersAPI.rerun_all_stale"
_UPDATE = "mammoth.api.parameters.ParametersAPI.update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


# -- parameter.create --------------------------------------------------------


def test_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_create(_inv("parameter.create"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_create_requires_param_type(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_create(_inv("parameter.create", extra_args=["Rate"]))
    assert excinfo.value.code == "missing_field"


def test_create_uses_positional_name_and_input_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"param_type": "number", "value": 5}), encoding="utf-8")
    parameter_cmd.parameter_create(
        _inv("parameter.create", extra_args=["Rate"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_CREATE, {"name": "Rate", "param_type": "number", "value": 5})
    ]


def test_create_forwards_optional_and_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "name": "Rate",
                "param_type": "number",
                "value": 5,
                "description": "desc",
                "group_id": 3,
                "scope": "workspace",
            }
        ),
        encoding="utf-8",
    )
    parameter_cmd.parameter_create(_inv("parameter.create", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "Rate",
                "param_type": "number",
                "value": 5,
                "description": "desc",
                "group_id": 3,
                "scope": "workspace",
                "project_id": 180,
            },
        )
    ]


def test_create_without_project_omits_project_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"param_type": "number", "value": 5}), encoding="utf-8")
    parameter_cmd.parameter_create(
        _inv("parameter.create", extra_args=["Rate"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_CREATE, {"name": "Rate", "param_type": "number", "value": 5})
    ]


# -- parameter.delete ---------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_delete(_inv("parameter.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_delete(_inv("parameter.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"parameter_id": 7})]


def test_delete_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_delete(_inv("parameter.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


# -- parameter.dependencies / duplicate / get / rerun -------------------------


def test_dependencies_uses_positional_id(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_dependencies(_inv("parameter.dependencies", extra_args=["9"]))
    assert fake_service.call_log == [(_DEPENDENCIES, {"parameter_id": 9})]


def test_dependencies_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_dependencies(_inv("parameter.dependencies"))
    assert excinfo.value.code == "missing_argument"


def test_duplicate_uses_positional_id(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_duplicate(_inv("parameter.duplicate", extra_args=["9"]))
    assert fake_service.call_log == [(_DUPLICATE, {"parameter_id": 9})]


def test_get_uses_positional_id(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_get(_inv("parameter.get", extra_args=["9"]))
    assert fake_service.call_log == [(_GET, {"parameter_id": 9})]


def test_get_invalid_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_get(_inv("parameter.get", extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


def test_rerun_uses_positional_id(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_rerun(_inv("parameter.rerun", extra_args=["9"]))
    assert fake_service.call_log == [(_RERUN, {"parameter_id": 9})]


# -- parameter.rerun-all-stale -------------------------------------------------


def test_rerun_all_stale_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_rerun_all_stale(_inv("parameter.rerun-all-stale"))
    assert excinfo.value.code == "project_required"
    assert fake_service.call_log == []


def test_rerun_all_stale_passes_project(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_rerun_all_stale(_inv("parameter.rerun-all-stale", project=180))
    assert fake_service.call_log == [(_RERUN_ALL_STALE, {"project_id": 180})]


# -- parameter.list -------------------------------------------------------------


def test_list_forwards_optional_fields_and_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"limit": 10, "offset": 5, "search": "rate", "group_id": 2, "sort": "name"}),
        encoding="utf-8",
    )
    parameter_cmd.parameter_list(_inv("parameter.list", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _LIST,
            {
                "limit": 10,
                "offset": 5,
                "search": "rate",
                "group_id": 2,
                "sort": "name",
                "project_id": 180,
            },
        )
    ]


def test_list_without_project_omits_project_id(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_list(_inv("parameter.list"))
    assert fake_service.call_log == [(_LIST, {})]


# -- parameter.update -----------------------------------------------------------


def test_update_requires_at_least_one_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_update(_inv("parameter.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "New", "value": 10}), encoding="utf-8")
    parameter_cmd.parameter_update(
        _inv("parameter.update", extra_args=["7"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_UPDATE, {"parameter_id": 7, "name": "New", "value": 10})
    ]


# -- parameter.group.create ------------------------------------------------------


def test_group_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_group_create(_inv("parameter.group.create"))
    assert excinfo.value.code == "missing_argument"


def test_group_create_uses_positional_name(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_group_create(
        _inv("parameter.group.create", extra_args=["Rates"])
    )
    assert fake_service.call_log == [(_GROUP_CREATE, {"name": "Rates"})]


def test_group_create_forwards_color_and_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "Rates", "color": "#FF0000"}), encoding="utf-8")
    parameter_cmd.parameter_group_create(
        _inv("parameter.group.create", project=180, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_GROUP_CREATE, {"name": "Rates", "color": "#FF0000", "project_id": 180})
    ]


# -- parameter.group.delete -------------------------------------------------------


def test_group_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_group_delete(
            _inv("parameter.group.delete", extra_args=["3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_group_delete_proceeds_with_yes_and_project(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_group_delete(
        _inv("parameter.group.delete", extra_args=["3"], project=180, yes=True)
    )
    assert fake_service.call_log == [(_GROUP_DELETE, {"group_id": 3, "project_id": 180})]


# -- parameter.group.list ----------------------------------------------------------


def test_group_list_forwards_optional_fields_and_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 10, "offset": 5, "sort": "name"}), encoding="utf-8")
    parameter_cmd.parameter_group_list(
        _inv("parameter.group.list", project=180, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_GROUP_LIST, {"limit": 10, "offset": 5, "sort": "name", "project_id": 180})
    ]


def test_group_list_without_project_omits_project_id(fake_service: FakeMammothService) -> None:
    parameter_cmd.parameter_group_list(_inv("parameter.group.list"))
    assert fake_service.call_log == [(_GROUP_LIST, {})]


# -- parameter.group.reorder --------------------------------------------------------


def test_group_reorder_requires_order(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_group_reorder(_inv("parameter.group.reorder"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_group_reorder_forwards_order_and_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"order": [3, 1, 2]}), encoding="utf-8")
    parameter_cmd.parameter_group_reorder(
        _inv("parameter.group.reorder", project=180, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_GROUP_REORDER, {"order": [3, 1, 2], "project_id": 180})
    ]


# -- parameter.group.update ---------------------------------------------------------


def test_group_update_requires_at_least_one_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        parameter_cmd.parameter_group_update(_inv("parameter.group.update", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_group_update_forwards_fields_and_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"name": "New", "color": "#00FF00"}), encoding="utf-8")
    parameter_cmd.parameter_group_update(
        _inv("parameter.group.update", extra_args=["3"], project=180, input_file=str(doc))
    )
    assert fake_service.call_log == [
        (
            _GROUP_UPDATE,
            {"group_id": 3, "name": "New", "color": "#00FF00", "project_id": 180},
        )
    ]
