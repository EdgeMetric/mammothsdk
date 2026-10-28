"""Public NDJSON lifecycle framing contract."""

from __future__ import annotations

import io
import json

import pytest
import typer

from mammoth_cli.app.usage import _output_mode_from_argv
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.output.emit import emit_error
from mammoth_cli.output.render import NDJSON_STREAM_VERSION, render
from mammoth_cli.runtime import executor


class _FailsAfterFirstWrite(io.StringIO):
    """A stdout sink that accepts ``start`` then fails before an item/end."""

    writes = 0

    def write(self, text: str) -> int:
        if self.writes >= 1:
            raise OSError("simulated stdout loss")
        self.writes += 1
        return super().write(text)


def _frames(envelope: dict[str, object]) -> list[dict[str, object]]:
    stream = io.StringIO()
    render(envelope, output="ndjson", stream=stream)
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_ndjson_success_has_versioned_terminal_lifecycle_and_pagination() -> None:
    meta = {"pagination": {"next_cursor": "opaque", "has_more": True}}
    frames = _frames({"schema_version": 1, "data": [{"id": 1}], "meta": meta})

    assert [frame["event"] for frame in frames] == ["start", "item", "end"]
    assert all(frame["stream_version"] == NDJSON_STREAM_VERSION for frame in frames)
    assert frames[0]["meta"] == meta
    assert frames[-1] == {
        "complete": True,
        "count": 1,
        "event": "end",
        "meta": meta,
        "schema_version": 1,
        "stream_version": NDJSON_STREAM_VERSION,
    }


def test_ndjson_distinguishes_empty_list_from_scalar_null() -> None:
    empty = _frames({"schema_version": 1, "data": [], "meta": {}})
    null = _frames({"schema_version": 1, "data": None, "meta": {}})

    assert [frame["event"] for frame in empty] == ["start", "end"]
    assert empty[-1]["count"] == 0
    assert [frame["event"] for frame in null] == ["start", "item", "end"]
    assert null[1]["data"] is None
    assert null[-1]["count"] == 1


def test_ndjson_error_is_one_incomplete_terminal_frame() -> None:
    frames = _frames({"schema_version": 1, "error": {"code": "interrupted"}})

    assert frames == [
        {
            "complete": False,
            "error": {"code": "interrupted"},
            "event": "error",
            "meta": None,
            "schema_version": 1,
            "stream_version": NDJSON_STREAM_VERSION,
        }
    ]


def test_ndjson_write_failure_leaves_no_false_end_and_reports_to_working_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = _FailsAfterFirstWrite()
    stderr = io.StringIO()
    monkeypatch.setattr(executor.sys, "stdout", stdout)
    monkeypatch.setattr(executor.sys, "stderr", stderr)

    with pytest.raises(typer.Exit):
        executor.run("test", "ndjson", lambda: ([{"id": 1}], {}))

    stdout_frames = [json.loads(line) for line in stdout.getvalue().splitlines()]
    stderr_frames = [json.loads(line) for line in stderr.getvalue().splitlines()]
    assert [frame["event"] for frame in stdout_frames] == ["start"]
    assert all(frame["event"] != "end" for frame in stdout_frames)
    assert stderr_frames[-1]["event"] == "error"
    assert stderr_frames[-1]["complete"] is False


@pytest.mark.parametrize("output", ["json", "ndjson", "yaml"])
def test_machine_error_is_the_one_document_on_stdout(
    output: str, capsys: pytest.CaptureFixture[str]
) -> None:
    emit_error(CliError(code="resource_not_found", message="gone"), machine=True, output=output)

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "resource_not_found" in captured.out


def test_human_error_stays_on_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    emit_error(CliError(code="resource_not_found", message="gone"), machine=False, output="table")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error [resource_not_found]: gone" in captured.err


def test_machine_error_falls_back_to_stderr_when_stdout_is_unwritable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Closed(io.StringIO):
        def write(self, text: str) -> int:
            raise OSError("closed pipe")

    stderr = io.StringIO()
    monkeypatch.setattr("sys.stdout", _Closed())
    monkeypatch.setattr("sys.stderr", stderr)

    emit_error(CliError(code="resource_not_found", message="gone"), machine=True, output="json")

    assert json.loads(stderr.getvalue())["error"]["code"] == "resource_not_found"


def test_output_mode_from_argv_honours_the_session_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAMMOTH_OUTPUT", "json")

    assert _output_mode_from_argv(["project", "lst"]) == "json"
    assert _output_mode_from_argv(["project", "lst", "-o", "yaml"]) == "yaml"
