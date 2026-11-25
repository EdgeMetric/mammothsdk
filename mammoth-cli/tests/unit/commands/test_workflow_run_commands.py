"""The Workflows API commands: workflow runnable, run start/status/result and verify-callback.

The commands go through the real CLI parser and handler against the in-memory fake service.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from mammoth.workflow_callbacks import sign_callback

from mammoth_cli.commands import workflow_callback as wf
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.schema.find import find_schemas
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_API = "mammoth.api.workflows.WorkflowsAPI"
_TRIGGERS = "mammoth.api.workflow_triggers.WorkflowTriggersAPI"
_RUN = "3f2b8c1e-6a4d-4e9b-9a51-0c7d2e5f8a10"
_SECRET = "9c1e" * 16


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture(autouse=True)
def _offline(fake_service: FakeMammothService, block_real_network: None) -> FakeMammothService:
    return fake_service


def _invoke(*argv: str) -> Any:
    return make_runner().invoke([*argv, "--project", "25654", "--output", "json"])


def _status(status: str, **extra: Any) -> dict[str, Any]:
    return {"run_id": _RUN, "workflow_id": 42, "status": status, **extra}


# --- wiring ---------------------------------------------------------------------------------

_SDK = {
    "workflow.runnable": f"{_API}.list_runnable",
    "workflow.run.start": f"{_TRIGGERS}.run",
    "workflow.run.status": f"{_API}.run_status",
    "workflow.run.result": f"{_API}.run_result",
    "workflow.verify-callback": "mammoth_cli.commands.workflow_callback.verify_callback_file",
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
        ("run a workflow", "workflow.run.start"),
        ("workflow run status", "workflow.run.status"),
        ("verify workflow callback signature", "workflow.verify-callback"),
    ],
)
def test_schema_find_finds_the_run_commands(query: str, command_id: str) -> None:
    found = [m["command_id"] for m in find_schemas(query)["matches"]]
    assert command_id in found[:5], found


# --- workflow runnable / run status / result ----------------------------------------------------


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
    result = _invoke("workflow", "run", verb, "42", _RUN)
    assert result.exit_code == 0, result.output
    assert fake_service.call_log == [
        (f"{_API}.{method}", {"workflow_id": 42, "run_id": _RUN, "project_id": 25654})
    ]


def test_status_needs_the_run_id() -> None:
    result = _invoke("workflow", "run", "status", "42")
    assert result.exit_code == 2, result.output


# --- workflow run start with a callback -----------------------------------------------------

_CALLBACK = '{"callback_url": "https://hooks.example.com/r"}'


def _started(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_TRIGGERS}.run"] = {
        "run_id": _RUN,
        "already_running": False,
        "callback_secret": _SECRET,
    }


@pytest.mark.parametrize("extra", [[], ["--dry-run"]])
def test_run_start_with_a_callback_needs_reveal_and_starts_nothing(
    fake_service: FakeMammothService, extra: list[str]
) -> None:
    result = _invoke("workflow", "run", "start", "42", "--input", _CALLBACK, *extra)
    assert result.exit_code == 2, result.output
    assert "--reveal" in json.loads(result.output)["error"]["message"]
    assert fake_service.call_log == []


def test_run_start_without_a_callback_needs_no_reveal(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_TRIGGERS}.run"] = {"run_id": _RUN, "already_running": False}
    result = _invoke("workflow", "run", "start", "42")
    assert result.exit_code == 0, result.output


def test_run_start_reveal_prints_the_callback_secret(fake_service: FakeMammothService) -> None:
    _started(fake_service)
    result = _invoke("workflow", "run", "start", "42", "--input", _CALLBACK, "--reveal")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["callback_secret"] == _SECRET
    sent = [kwargs for symbol, kwargs in fake_service.call_log if symbol == f"{_TRIGGERS}.run"]
    assert sent == [
        {"workflow_id": 42, "project_id": 25654, "callback_url": "https://hooks.example.com/r"}
    ]


def test_run_start_dry_run_refuses_an_empty_callback_url(
    fake_service: FakeMammothService,
) -> None:
    result = _invoke(
        "workflow", "run", "start", "42", "--dry-run", "--input", '{"callback_url": " "}'
    )
    assert result.exit_code == 2, result.output
    assert fake_service.call_log == []


# --- workflow verify-callback ---------------------------------------------------------------


def _callback(tmp_path: Path, *, body: bytes = b'{"run_id":"r1"}') -> tuple[str, str, str]:
    body_file = tmp_path / "body.json"
    body_file.write_bytes(body)
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(_SECRET + "\n", encoding="utf-8")
    secret_file.chmod(0o600)
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
