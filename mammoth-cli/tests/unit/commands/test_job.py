"""Unit tests for the ``job`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import job as job_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_GET = "mammoth.api.jobs.JobsAPI.get_job"
_GET_MANY = "mammoth.api.jobs.JobsAPI.get_jobs"
_WAIT = "mammoth.api.jobs.JobsAPI.wait_for_job"
_WAIT_MANY = "mammoth.api.jobs.JobsAPI.wait_for_jobs"


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


# --- job get -----------------------------------------------------------


def test_get_uses_positional_job_id(fake_service: FakeMammothService) -> None:
    job_cmd.job_get(_inv("job.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"job_id": 7})]


def test_get_without_job_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        job_cmd.job_get(_inv("job.get"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_get_with_non_integer_job_id_is_invalid_argument(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        job_cmd.job_get(_inv("job.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_get_meta_has_no_project(fake_service: FakeMammothService) -> None:
    _, meta = job_cmd.job_get(_inv("job.get", extra_args=["7"]))
    assert meta["project_id"] is None
    assert meta["workspace_id"] == 4


def test_get_returns_programmed_response(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET] = {"job": {"id": 7, "status": "success"}}
    data, _ = job_cmd.job_get(_inv("job.get", extra_args=["7"]))
    assert data == {"job": {"id": 7, "status": "success"}}


# --- job get-many --------------------------------------------------------


def test_get_many_requires_job_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        job_cmd.job_get_many(_inv("job.get-many"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_get_many_forwards_job_ids(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"job_ids": [1, 2, 3]})
    job_cmd.job_get_many(_inv("job.get-many", input_file=input_file))
    assert fake_service.call_log == [(_GET_MANY, {"job_ids": [1, 2, 3]})]


# --- job wait ------------------------------------------------------------


def test_wait_uses_positional_job_id(fake_service: FakeMammothService) -> None:
    job_cmd.job_wait(_inv("job.wait", extra_args=["9"]))
    assert fake_service.call_log == [(_WAIT, {"job_id": 9})]


def test_wait_without_job_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        job_cmd.job_wait(_inv("job.wait"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_wait_forwards_timeout_and_poll_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"timeout": 30, "poll_interval": 5})
    job_cmd.job_wait(_inv("job.wait", extra_args=["9"], input_file=input_file))
    assert fake_service.call_log == [(_WAIT, {"job_id": 9, "timeout": 30, "poll_interval": 5})]


def test_wait_without_input_omits_optional_fields(fake_service: FakeMammothService) -> None:
    job_cmd.job_wait(_inv("job.wait", extra_args=["9"]))
    assert fake_service.call_log == [(_WAIT, {"job_id": 9})]


# --- job wait-many ---------------------------------------------------------


def test_wait_many_requires_job_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        job_cmd.job_wait_many(_inv("job.wait-many"))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_wait_many_forwards_job_ids_only(fake_service: FakeMammothService, tmp_path: Path) -> None:
    input_file = _write(tmp_path, {"job_ids": [1, 2]})
    job_cmd.job_wait_many(_inv("job.wait-many", input_file=input_file))
    assert fake_service.call_log == [(_WAIT_MANY, {"job_ids": [1, 2]})]


def test_wait_many_forwards_timeout_and_poll_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path, {"job_ids": [1, 2], "timeout": 60, "poll_interval": 3})
    job_cmd.job_wait_many(_inv("job.wait-many", input_file=input_file))
    assert fake_service.call_log == [
        (_WAIT_MANY, {"job_ids": [1, 2], "timeout": 60, "poll_interval": 3})
    ]
