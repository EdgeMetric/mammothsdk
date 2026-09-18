"""End-to-end tests that runtime validation (R5, R6, R8) is wired into the app.

These drive the real Typer app in-process (:func:`mammoth_cli.testing.make_runner`)
with no mocked service: every case here is invalid before a handler would ever
open a service or touch the network, so no credentials are required — the
point of each test is that ``app._execute`` rejects the bad input first.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.executor import _profile_scope_recovery, run
from mammoth_cli.testing import make_runner

_JSON_NO_INPUT = ["--output", "json", "--no-input"]


def test_profile_scoped_recovery_handles_commands_without_output_option() -> None:
    error = CliError(
        code="interrupted", message="interrupted", recovery_commands=["mammoth auth login"]
    )

    scoped = _profile_scope_recovery(error, "staging")

    assert scoped.recovery_commands == ["mammoth auth login --profile staging"]


def test_ndjson_error_is_one_terminal_frame_on_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    def _failure() -> tuple[object, dict[str, object]]:
        raise CliError(code="interrupted", message="stopped", exit_status=130)

    with pytest.raises(typer.Exit) as raised:
        run("test", "ndjson", _failure)

    captured = capsys.readouterr()
    assert raised.value.exit_code == 130
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "complete": False,
        "error": {
            "authorization_required": False,
            "code": "interrupted",
            "details": {},
            "hint": None,
            "message": "stopped",
            "recovery_commands": [],
            "request_id": None,
            "retryable": False,
        },
        "event": "error",
        "meta": None,
        "schema_version": 1,
        "stream_version": 2,
    }


# --- R5: a surplus positional is refused, not silently dropped ------------


def test_surplus_positional_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    """'project delete 1 2' must not silently act only on '1'."""
    result = make_runner().invoke(["project", "delete", "1", "2", "--yes", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "unexpected_argument" in result.output


def test_single_positional_for_project_delete_reaches_past_arg_validation(
    isolated_cli_config: Path,
) -> None:
    """A single id is accepted by argument validation (fails later, on auth)."""
    result = make_runner().invoke(
        ["project", "delete", "1", "--yes", "--confirm", "1", *_JSON_NO_INPUT]
    )
    # No credentials configured: this must fail on auth/profile resolution, not
    # on argument validation.
    assert "unexpected_argument" not in result.output


# --- R6: an --input field that fails its annotated type is rejected -------


def test_input_field_type_mismatch_is_rejected_through_the_app(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": "abc"}), encoding="utf-8")
    result = make_runner().invoke(["project", "list", "--input", str(doc), *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_input_field_type" in result.output


def test_non_positive_structured_ids_are_rejected_before_auth(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = tmp_path / "ids.json"
    doc.write_text(json.dumps({"project_ids": [-1, 0]}), encoding="utf-8")
    result = make_runner().invoke(["project", "bulk-delete", "--input", str(doc), *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_input_field_type" in result.output
    assert "project_ids[0]" in result.output


def test_handler_owned_field_is_rejected_before_auth(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = tmp_path / "job.json"
    doc.write_text(json.dumps({"timeout": 1}), encoding="utf-8")
    result = make_runner().invoke(["job", "get", "123", "--input", str(doc), *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "unknown_input_field" in result.output


# --- R8: global options and positional ids are validated -------------------


def test_zero_project_option_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["project", "list", "--project", "0", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


def test_unrecognized_color_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["project", "list", "--color", "pink", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


def test_negative_timeout_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["project", "list", "--timeout", "-1", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


def test_zero_view_id_positional_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["view", "get", "0", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


# --- run log: every invocation is recorded; errors point at it -------------


def test_error_envelope_carries_log_ref_and_the_run_is_recorded(
    isolated_run_log: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from mammoth_cli.runtime import runlog
    from mammoth_cli.runtime.invocation import Invocation

    invocation = Invocation(command_id="project.list", output="json", no_input=True, profile="p")

    def _failure() -> tuple[object, dict[str, object]]:
        raise CliError(code="resource_not_found", message="gone", exit_status=5)

    with pytest.raises(typer.Exit):
        run("project.list", "json", _failure, invocation=invocation)

    envelope = json.loads(capsys.readouterr().err)
    ref = envelope["error"]["log_ref"]
    assert Path(ref["file"]).parent == isolated_run_log
    records = runlog.read_records(run_id=ref["run_id"])
    assert [r["event"] for r in records] == ["command.start", "command.end"]
    assert records[0]["profile"] == "p"
    assert (records[-1]["exit_status"], records[-1]["error_code"]) == (5, "resource_not_found")


def test_success_is_recorded_without_touching_the_envelope(
    isolated_run_log: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from mammoth_cli.runtime import runlog
    from mammoth_cli.runtime.invocation import Invocation

    invocation = Invocation(command_id="version", output="json", no_input=True)
    run("version", "json", lambda: ({"ok": True}, {}), invocation=invocation)

    envelope = json.loads(capsys.readouterr().out)
    assert envelope["data"] == {"ok": True} and "log_ref" not in envelope
    assert runlog.read_records(command_id="version")[-1]["exit_status"] == 0


def test_the_cli_process_logs_and_log_tail_reads_it_back(isolated_run_log: Path) -> None:
    runner = make_runner()
    assert runner.invoke(["version", *_JSON_NO_INPUT]).exit_code == 0
    result = runner.invoke(["log", "tail", "--input", '{"command_id": "version"}', *_JSON_NO_INPUT])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["count"] >= 2
    assert {r["event"] for r in data["records"]} == {"command.start", "command.end"}
    path = json.loads(runner.invoke(["log", "path", *_JSON_NO_INPUT]).output)["data"]
    assert path["directory"] == str(isolated_run_log)
