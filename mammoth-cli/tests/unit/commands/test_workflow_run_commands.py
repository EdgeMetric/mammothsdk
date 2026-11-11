"""The Workflows API commands: workflow runnable, run, status, result and verify-callback.

The commands go through the real CLI parser and handler against the in-memory fake service;
the run wait is driven by a fake clock, so no test sleeps.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from mammoth.workflow_callbacks import sign_callback

from mammoth_cli.commands import workflow as wf
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.schema.find import find_schemas
from mammoth_cli.errors.envelope import CODE_RESOURCE_NOT_FOUND, EXIT_NOT_FOUND, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_API = "mammoth.api.workflows.WorkflowsAPI"
_RUN = "3f2b8c1e-6a4d-4e9b-9a51-0c7d2e5f8a10"
_SECRET = "9c1e" * 16


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture(autouse=True)
def _offline(fake_service: FakeMammothService, block_real_network: None) -> FakeMammothService:
    return fake_service


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """The run wait sleeps through ``time.sleep``; record the gaps instead of sleeping."""
    slept: list[float] = []
    monkeypatch.setattr(wf.time, "sleep", slept.append)
    return slept


def _invoke(*argv: str) -> Any:
    return make_runner().invoke([*argv, "--project", "25654", "--output", "json"])


def _status(status: str, **extra: Any) -> dict[str, Any]:
    return {"run_id": _RUN, "workflow_id": 42, "status": status, **extra}


def _statuses(*answers: Any) -> Any:
    """A ``run_status`` responder that answers each read with the next item in turn."""
    queue = list(answers)

    def answer(_log: Any) -> Any:
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        return item

    return answer


# --- wiring ---------------------------------------------------------------------------------

_SDK = {
    "workflow.runnable": f"{_API}.list_runnable",
    "workflow.run": f"{_API}.start_run",
    "workflow.status": f"{_API}.run_status",
    "workflow.result": f"{_API}.run_result",
    "workflow.verify-callback": "mammoth_cli.commands.workflow.verify_callback_file",
}


def test_every_new_command_is_registered_and_backed_by_its_method() -> None:
    assert set(_SDK) <= set(HANDLERS)
    for command_id, symbol in _SDK.items():
        assert command_by_id(command_id)["sdk_symbol"] == symbol  # type: ignore[index]


def test_the_existing_workflow_list_is_unchanged() -> None:
    assert command_by_id("workflow.list")["sdk_symbol"] == f"{_API}.list"  # type: ignore[index]


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        ("run a workflow", "workflow.run"),
        ("workflow run status", "workflow.status"),
        ("verify workflow callback signature", "workflow.verify-callback"),
    ],
)
def test_schema_find_finds_the_run_commands(query: str, command_id: str) -> None:
    found = [m["command_id"] for m in find_schemas(query)["matches"]]
    assert command_id in found[:5], found


# --- workflow runnable / status / result ----------------------------------------------------


def test_runnable_lists_the_project_workflows(fake_service: FakeMammothService) -> None:
    listed = [{"workflow_id": 42, "name": "Weekly", "running": False, "last_run": None}]
    fake_service.responses[f"{_API}.list_runnable"] = listed
    result = _invoke("workflow", "runnable")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"] == listed
    assert fake_service.call_log == [(f"{_API}.list_runnable", {"project_id": 25654})]


@pytest.mark.parametrize(("verb", "method"), [("status", "run_status"), ("result", "run_result")])
def test_status_and_result_pass_the_workflow_and_run_ids(
    fake_service: FakeMammothService, verb: str, method: str
) -> None:
    fake_service.responses[f"{_API}.{method}"] = _status("success", outputs=[])
    result = _invoke("workflow", verb, "42", _RUN)
    assert result.exit_code == 0, result.output
    assert fake_service.call_log == [
        (f"{_API}.{method}", {"workflow_id": 42, "run_id": _RUN, "project_id": 25654})
    ]


def test_status_needs_the_run_id() -> None:
    result = _invoke("workflow", "status", "42")
    assert result.exit_code == 2, result.output


# --- workflow run ---------------------------------------------------------------------------


def test_run_waits_until_the_run_ends_and_returns_its_final_status(
    fake_service: FakeMammothService, _no_real_sleep: list[float]
) -> None:
    fake_service.responses[f"{_API}.start_run"] = {
        "run_id": _RUN,
        "already_running": False,
        "callback_secret": None,
    }
    fake_service.responses[f"{_API}.run_status"] = _statuses(
        _status("running"), _status("running"), _status("success", rows_out=980)
    )
    result = _invoke("workflow", "run", "42")
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["status"] == "success"
    assert data["rows_out"] == 980
    assert data["already_running"] is False
    # Three reads while waiting; the write's read-back may add one more.
    assert [c[0] for c in fake_service.call_log][:4] == [
        f"{_API}.start_run",
        *[f"{_API}.run_status"] * 3,
    ]
    assert fake_service.call_log[0][1] == {"workflow_id": 42, "project_id": 25654}
    assert _no_real_sleep == [2.0, 3.0]


def test_run_no_wait_returns_once_started_and_sends_the_callback_url(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[f"{_API}.start_run"] = {
        "run_id": _RUN,
        "already_running": False,
        "callback_secret": _SECRET,
    }
    result = _invoke(
        *("workflow", "run", "42", "--no-wait"),
        *("--input", '{"callback_url": "https://hooks.example.com/r"}'),
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["run_id"] == _RUN
    assert _SECRET not in result.output, "the callback secret is masked without --reveal"
    # The start, then the declared readback: the run's status.
    assert fake_service.call_log == [
        (
            f"{_API}.start_run",
            {
                "workflow_id": 42,
                "project_id": 25654,
                "callback_url": "https://hooks.example.com/r",
            },
        ),
        (
            f"{_API}.run_status",
            {"workflow_id": 42, "run_id": _RUN, "project_id": 25654},
        ),
    ]


def test_run_reveal_prints_the_callback_secret(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_API}.start_run"] = {
        "run_id": _RUN,
        "already_running": False,
        "callback_secret": _SECRET,
    }
    result = _invoke("workflow", "run", "42", "--no-wait", "--reveal")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["callback_secret"] == _SECRET


def test_a_failed_run_exits_non_zero_and_says_why(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_API}.start_run"] = {"run_id": _RUN, "already_running": True}
    fake_service.responses[f"{_API}.run_status"] = _status(
        "failure", reason="Getting the latest data failed"
    )
    result = _invoke("workflow", "run", "42")
    assert result.exit_code == 1, result.output
    error = json.loads(result.output)["error"]
    assert error["code"] == "job_failed"
    assert "Getting the latest data failed" in error["message"]


def test_run_rejects_an_unknown_option() -> None:
    result = _invoke("workflow", "run", "42", "--no-wiat")
    assert result.exit_code == 2, result.output


# --- the wait loop, on a fake clock ---------------------------------------------------------


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def _not_found() -> CliError:
    return CliError(code=CODE_RESOURCE_NOT_FOUND, message="nope", exit_status=EXIT_NOT_FOUND)


def test_the_gaps_grow_by_half_and_stop_at_the_cap() -> None:
    delays = wf.run_poll_delays()
    assert [next(delays) for _ in range(9)] == [
        2.0,
        3.0,
        4.5,
        6.75,
        10.125,
        15.1875,
        22.78125,
        30.0,
        30.0,
    ]


def test_await_run_returns_the_settled_status() -> None:
    clock = _Clock()
    reads = iter([_status("running"), _status("running"), _status("success")])
    status, finished = wf.await_run(lambda: next(reads), 300, sleep=clock.sleep, clock=clock)
    assert finished is True
    assert status == _status("success")
    assert clock.slept == [2.0, 3.0]


def test_await_run_stops_at_the_budget_with_the_last_status() -> None:
    clock = _Clock()
    status, finished = wf.await_run(lambda: _status("running"), 10, sleep=clock.sleep, clock=clock)
    assert finished is False
    assert status == _status("running")
    assert sum(clock.slept) == 10  # the last gap is cut to the budget
    assert clock.slept == [2.0, 3.0, 4.5, 0.5]


def test_await_run_treats_an_early_404_as_not_started_yet() -> None:
    clock = _Clock()
    reads = iter([_not_found(), _not_found(), _status("success")])

    def read() -> Any:
        item = next(reads)
        if isinstance(item, Exception):
            raise item
        return item

    status, finished = wf.await_run(read, 300, sleep=clock.sleep, clock=clock)
    assert (status, finished) == (_status("success"), True)


def test_await_run_raises_a_404_after_the_grace() -> None:
    clock = _Clock()

    def read() -> Any:
        raise _not_found()

    with pytest.raises(CliError) as caught:
        wf.await_run(read, 300, sleep=clock.sleep, clock=clock, grace=5)
    assert caught.value.code == CODE_RESOURCE_NOT_FOUND
    assert clock.now >= 5


def test_run_times_out_retryably_or_returns_running_with_return_running(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[f"{_API}.start_run"] = {"run_id": _RUN, "already_running": False}
    fake_service.responses[f"{_API}.run_status"] = _status("running")
    # time.sleep is recorded, not slept, so move the monotonic clock with each gap.
    clock = _Clock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(wf.time, "monotonic", clock)
        mp.setattr(wf.time, "sleep", clock.sleep)
        timed_out = _invoke("workflow", "run", "42", "--job-timeout", "20")
        clock.now = 0.0
        running = _invoke("workflow", "run", "42", "--job-timeout", "20", "--return-running")
    assert timed_out.exit_code == 7, timed_out.output
    assert json.loads(timed_out.output)["error"]["code"] == "timeout"
    assert running.exit_code == 0, running.output
    data = json.loads(running.output)["data"]
    assert data["status"] == "running"
    assert data["resume"] == f"mammoth workflow status 42 {_RUN}"


# --- workflow verify-callback ---------------------------------------------------------------


def _callback(tmp_path: Path, *, body: bytes = b'{"run_id":"r1"}') -> tuple[str, str, str]:
    body_file = tmp_path / "body.json"
    body_file.write_bytes(body)
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(_SECRET + "\n", encoding="utf-8")
    secret_file.chmod(0o600)
    import time

    header = sign_callback(_SECRET, int(time.time()), body)
    return header, str(body_file), str(secret_file)


def test_verify_callback_accepts_a_valid_signature(tmp_path: Path) -> None:
    header, body_file, secret_file = _callback(tmp_path)
    document = {"header": header, "body_file": body_file, "secret_file": secret_file}
    result = make_runner().invoke(
        ["workflow", "verify-callback", "--input", json.dumps(document), "--output", "json"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"] == {"valid": True, "reason": None}


def test_verify_callback_refuses_a_changed_body(tmp_path: Path) -> None:
    header, body_file, _ = _callback(tmp_path)
    Path(body_file).write_bytes(b'{"run_id":"r2"}')
    document = {"header": header, "body_file": body_file, "secret": _SECRET}
    result = make_runner().invoke(
        ["workflow", "verify-callback", "--input", json.dumps(document), "--output", "json"]
    )
    assert result.exit_code == 1, result.output
    error = json.loads(result.output)["error"]
    assert error["code"] == "invalid_signature"
    assert "does not match" in error["message"]
    assert _SECRET not in result.output


def test_verify_callback_refuses_a_stale_timestamp_unless_tolerance_is_zero(
    tmp_path: Path,
) -> None:
    body = tmp_path / "body.json"
    body.write_bytes(b"{}")
    header = sign_callback(_SECRET, 1_000, b"{}")
    stale = wf.verify_callback_file(header, str(body), secret=_SECRET)
    assert stale["valid"] is False
    assert "seconds from now" in stale["reason"]
    assert wf.verify_callback_file(header, str(body), secret=_SECRET, tolerance=0)["valid"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"secret": _SECRET, "secret_file": "x"},
        {"secret": _SECRET, "tolerance": -1},
        {"secret": _SECRET, "tolerance": True},
    ],
)
def test_verify_callback_usage_errors(tmp_path: Path, kwargs: dict[str, Any]) -> None:
    body = tmp_path / "body.json"
    body.write_bytes(b"{}")
    with pytest.raises(CliError) as caught:
        wf.verify_callback_file("t=1,v1=00", str(body), **kwargs)
    assert caught.value.exit_status == 2


def test_verify_callback_unreadable_body_is_a_usage_error(tmp_path: Path) -> None:
    with pytest.raises(CliError) as caught:
        wf.verify_callback_file("t=1,v1=00", str(tmp_path / "missing"), secret=_SECRET)
    assert caught.value.exit_status == 2
