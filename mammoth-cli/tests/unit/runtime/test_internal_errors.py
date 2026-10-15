"""An unexpected fault in the CLI is reported as one, with its cause kept for the bug report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer

from mammoth_cli.runtime.executor import run
from mammoth_cli.runtime.invocation import Invocation


def _boom() -> tuple[object, dict[str, object]]:
    raise TypeError("cannot serialise <widget>")


def _run_failing(
    capsys: pytest.CaptureFixture[str], *, debug: bool
) -> tuple[dict[str, object], str]:
    invocation = Invocation(command_id="project.list", output="json", debug=debug)
    with pytest.raises(typer.Exit):
        run("project.list", "json", _boom, invocation=invocation)
    stderr = capsys.readouterr().err
    # The error envelope is the last line of stderr; a --debug traceback comes before it.
    return json.loads(stderr.strip().splitlines()[-1]), stderr


def test_an_unexpected_exception_is_internal_error_not_api_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    envelope, _ = _run_failing(capsys, debug=False)
    error = envelope["error"]
    assert error["code"] == "internal_error"
    assert "TypeError" in error["message"]
    assert error["details"]["exception_type"] == "TypeError"
    assert "--debug" in error["hint"]


def test_a_failure_while_rendering_the_result_is_internal_error(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from mammoth_cli.runtime import executor

    def broken_render(*_args: object, **_kwargs: object) -> None:
        raise ValueError("cannot render")

    monkeypatch.setattr(executor, "emit_success", broken_render)
    with pytest.raises(typer.Exit):
        run("project.list", "json", lambda: ({"ok": 1}, {}))
    envelope = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert envelope["error"]["code"] == "internal_error"


def test_debug_prints_the_traceback_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    _, stderr = _run_failing(capsys, debug=True)
    assert "Traceback (most recent call last)" in stderr
    assert "TypeError: cannot serialise <widget>" in stderr


def test_without_debug_stderr_has_no_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    _, stderr = _run_failing(capsys, debug=False)
    assert "Traceback" not in stderr


def test_the_run_log_records_the_exception_type_and_message(
    capsys: pytest.CaptureFixture[str], isolated_run_log: Path
) -> None:
    envelope, _ = _run_failing(capsys, debug=False)
    log_file = Path(envelope["error"]["log_ref"]["file"])
    records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    exception = next(r for r in records if r["event"] == "command.exception")
    assert exception["exception_type"] == "TypeError"
    assert exception["exception_message"] == "cannot serialise <widget>"
    assert "Traceback" in exception["traceback"]
    end = next(r for r in records if r["event"] == "command.end")
    assert end["error_code"] == "internal_error"
