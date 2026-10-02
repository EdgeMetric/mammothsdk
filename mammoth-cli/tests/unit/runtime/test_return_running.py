"""``--return-running``: a wait that runs out hands back a resumable handle."""

from __future__ import annotations

import pytest
from mammoth.exceptions import MammothJobTimeoutError, MammothPipelineTimeoutError

from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.embed import invoke
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.mapping import map_sdk_exception
from mammoth_cli.services.testing import FakeMammothService

_LIST = "mammoth.api.projects.ProjectsAPI.list"
_WAIT = "mammoth.api.jobs.JobsAPI.wait_for_job"


def _login() -> ExplicitLogin:
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
        api_token="jwt",
        server_prefix="box",
        headers={"Authorization": "Bearer jwt"},
    )


def _run(
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
    outcome: CliError,
    symbol: str = _LIST,
    *,
    return_running: bool,
) -> dict[str, object]:
    fake = FakeMammothService()
    fake.responses[symbol] = outcome
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: fake)
    # A token names its workspace and the CLI learns it from the server; no network here.
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_args: 5)
    return invoke(args, login=_login(), return_running=return_running)


def _job_timeout() -> CliError:
    exc = MammothJobTimeoutError(44, 300, observed_job={"operation": "TRANSFORM", "path": "/x"})
    return map_sdk_exception(exc)


def _pipeline_timeout() -> CliError:
    return map_sdk_exception(MammothPipelineTimeoutError(7, 300, dataset_id=2, project_id=3))


def test_job_timeout_becomes_running_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    envelope = _run(monkeypatch, ["project", "list"], _job_timeout(), return_running=True)

    assert "error" not in envelope
    assert envelope["data"] == {
        "status": "running",
        "job_id": 44,
        "operation": "TRANSFORM",
        "path": "/x",
        "command": "project.list",
        "waited_seconds": 300,
        "resume": "mammoth job wait 44",
    }


def test_pipeline_timeout_becomes_pipeline_running_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = _run(monkeypatch, ["project", "list"], _pipeline_timeout(), return_running=True)

    assert "error" not in envelope
    assert envelope["data"] == {
        "status": "running",
        "dataview_id": 7,
        "command": "project.list",
        "waited_seconds": 300,
        "resume": "mammoth view pipeline wait 7 --project 3",
    }


@pytest.mark.parametrize("make", [_job_timeout, _pipeline_timeout])
def test_without_the_flag_a_timeout_stays_an_error(
    monkeypatch: pytest.MonkeyPatch, make: object
) -> None:
    envelope = _run(monkeypatch, ["project", "list"], make(), return_running=False)  # type: ignore[operator]

    error = envelope["error"]
    assert isinstance(error, dict)
    assert error["code"] == "timeout"
    assert error["details"]["waited_seconds"] == 300
    assert error["details"]["resume"] == error["recovery_commands"][1]


def test_return_running_leaves_other_errors_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    other = CliError(code="authentication_failed", message="expired")
    envelope = _run(monkeypatch, ["project", "list"], other, return_running=True)

    assert envelope["error"]["code"] == "authentication_failed"  # type: ignore[index]


def test_job_wait_running_with_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    envelope = _run(monkeypatch, ["job", "wait", "44"], _job_timeout(), _WAIT, return_running=True)

    data = envelope["data"]
    assert isinstance(data, dict)
    assert (data["status"], data["job_id"], data["command"]) == ("running", 44, "job.wait")
    assert data["resume"] == "mammoth job wait 44"


def test_job_wait_timeout_without_flag_is_the_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = _run(monkeypatch, ["job", "wait", "44"], _job_timeout(), _WAIT, return_running=False)

    assert envelope["error"]["code"] == "timeout"  # type: ignore[index]
