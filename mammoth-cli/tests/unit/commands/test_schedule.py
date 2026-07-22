"""Unit tests for the ``schedule`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import schedule as schedule_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.schedules.SchedulesAPI.list"
_GET = "mammoth.api.schedules.SchedulesAPI.get"
_CREATE = "mammoth.api.schedules.SchedulesAPI.create"
_UPDATE = "mammoth.api.schedules.SchedulesAPI.update"
_DELETE = "mammoth.api.schedules.SchedulesAPI.delete"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# -- list ---------------------------------------------------------------


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_list(_inv("schedule.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project_only(fake_service: FakeMammothService) -> None:
    schedule_cmd.schedule_list(_inv("schedule.list", project=180))
    assert fake_service.call_log == [(_LIST, {"project_id": 180})]


def test_list_forwards_limit_and_offset(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"limit": 10, "offset": 5})
    schedule_cmd.schedule_list(_inv("schedule.list", project=180, input_file=input_file))
    assert fake_service.call_log == [
        (_LIST, {"project_id": 180, "limit": 10, "offset": 5})
    ]


# -- get ------------------------------------------------------------------


def test_get_uses_positional_schedule_id(fake_service: FakeMammothService) -> None:
    schedule_cmd.schedule_get(_inv("schedule.get", project=180, extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"schedule_id": 7, "project_id": 180})]


def test_get_without_schedule_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_get(_inv("schedule.get", project=180))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_schedule_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_get(_inv("schedule.get", project=180, extra_args=["nope"]))
    assert excinfo.value.code == "invalid_argument"


def test_get_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_get(_inv("schedule.get", extra_args=["7"]))
    assert excinfo.value.code == "project_required"


# -- create -----------------------------------------------------------------


def test_create_requires_spec(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_create(_inv("schedule.create", project=180, yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"spec": {"rrule": {"frequency": "daily"}}})
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_create(
            _inv("schedule.create", project=180, input_file=input_file, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_create_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    spec = {"rrule": {"frequency": "daily"}}
    input_file = _write(tmp_path, {"spec": spec})
    schedule_cmd.schedule_create(
        _inv("schedule.create", project=180, input_file=input_file, yes=True)
    )
    assert fake_service.call_log == [(_CREATE, {"spec": spec, "project_id": 180})]


# -- update -----------------------------------------------------------------


def test_update_requires_schedule_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_update(_inv("schedule.update", project=180, yes=True))
    assert excinfo.value.code == "missing_argument"


def test_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_update(
            _inv("schedule.update", project=180, extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path, {"patch": [{"op": "replace", "path": "status", "value": "pause"}]}
    )
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_update(
            _inv(
                "schedule.update",
                project=180,
                extra_args=["7"],
                input_file=input_file,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_proceeds_with_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    patch = [{"op": "replace", "path": "status", "value": "pause"}]
    input_file = _write(tmp_path, {"patch": patch})
    schedule_cmd.schedule_update(
        _inv(
            "schedule.update",
            project=180,
            extra_args=["7"],
            input_file=input_file,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (_UPDATE, {"schedule_id": 7, "patch": patch, "project_id": 180})
    ]


# -- delete -------------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_delete(
            _inv("schedule.delete", project=180, extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    schedule_cmd.schedule_delete(_inv("schedule.delete", project=180, extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"schedule_id": 7, "project_id": 180})]


def test_delete_requires_schedule_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        schedule_cmd.schedule_delete(_inv("schedule.delete", project=180, yes=True))
    assert excinfo.value.code == "missing_argument"
