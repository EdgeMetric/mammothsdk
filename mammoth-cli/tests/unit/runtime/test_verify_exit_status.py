"""A write whose read-back says it did not take effect must not read done or exit 0."""

from __future__ import annotations

import json

import pytest
import typer

from mammoth_cli.runtime.executor import run
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.verify import with_verify

_FAILED = {"status": "done", "pipeline_error": {"execution_state": "failed"}}
_PARTIAL = {"status": "done", "partial": True}


def _run(data: dict[str, object], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict]:
    invocation = Invocation(command_id="view.filter-rows", output="json")
    code = 0
    try:
        run("view.filter-rows", "json", lambda: (with_verify(data), {}), invocation=invocation)
    except typer.Exit as exit_:
        code = exit_.exit_code
    out = capsys.readouterr().out
    return code, json.loads(out.strip().splitlines()[-1])


def test_failed_outcome_sets_status_failed_and_exits_1(capsys: pytest.CaptureFixture[str]) -> None:
    code, envelope = _run(_FAILED, capsys)
    assert code == 1
    assert envelope["data"]["status"] == "failed"
    assert envelope["data"]["verify"]["outcome"] == "failed"
    assert envelope["data"]["verify"]["reported_status"] == "done"


def test_partial_outcome_exits_3(capsys: pytest.CaptureFixture[str]) -> None:
    code, envelope = _run(_PARTIAL, capsys)
    assert code == 3
    assert envelope["data"]["status"] == "partial"


def test_settled_write_still_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    code, envelope = _run({"status": "done"}, capsys)
    assert code == 0
    assert envelope["data"]["status"] == "done"
