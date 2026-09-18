"""The always-on JSONL run log: location, redaction, retention, and reading."""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import pytest

from mammoth_cli.runtime import runlog


def _records(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_log_dir_prefers_the_environment_override(
    isolated_run_log: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert runlog.log_dir() == isolated_run_log
    monkeypatch.delenv("MAMMOTH_LOG_DIR")
    assert runlog.log_dir().name == "logs"
    assert runlog.log_dir() != isolated_run_log


def test_redact_argv_removes_the_input_document_only() -> None:
    argv = [
        "view",
        "export",
        "postgres",
        "12",
        "--input",
        '{"password": "x"}',
        '--input={"password": "y"}',
        "--yes",
        "--confirm",
        "12",
    ]
    assert runlog.redact_argv(argv) == [
        "view",
        "export",
        "postgres",
        "12",
        "--input",
        "<redacted --input>",
        "--input=<redacted --input>",
        "--yes",
        "--confirm",
        "12",
    ]


def test_start_and_finish_write_a_run_scoped_record_pair(isolated_run_log: Path) -> None:
    run = runlog.RunLog.start(
        "project.list", argv=["project", "list", "--input", "{}"], profile="p", project_id=3
    )
    run.finish(0)

    assert run.path is not None and run.path.parent == isolated_run_log
    records = _records(run.path)
    assert [r["event"] for r in records] == ["command.start", "command.end"]
    start, end = records
    assert start["run_id"] == end["run_id"] == run.run_id
    assert start["command_id"] == "project.list"
    assert start["argv"] == ["project", "list", "--input", "<redacted --input>"]
    assert start["profile"] == "p" and start["project_id"] == 3
    assert end["exit_status"] == 0 and end["error_code"] is None
    assert isinstance(end["duration_ms"], int)
    assert run.ref == {"file": str(run.path), "run_id": run.run_id}
    if run.path.stat().st_mode & 0o777 != 0o600:  # pragma: no cover - non-posix
        pytest.skip("permission bits are posix-only")


def test_sdk_logger_records_are_captured_and_redacted(isolated_run_log: Path) -> None:
    run = runlog.RunLog.start("view.get", argv=[])
    logging.getLogger("mammoth.http").info(
        "http",
        extra={
            "mammoth": {
                "event": "http",
                "method": "GET",
                "path": "/x",
                "status": 401,
                "api_secret": "should-not-appear",
            }
        },
    )
    logging.getLogger("mammoth.jobs").debug("job.poll", extra={"mammoth": {"job_id": 7}})
    run.finish(1, error_code="not_authenticated")

    assert run.path is not None
    events = _records(run.path)
    http = next(r for r in events if r["event"] == "http")
    assert http["status"] == 401 and http["logger"] == "mammoth.http"
    assert http["api_secret"] == "***REDACTED***"
    # INFO is the default level; DEBUG job polls need --debug.
    assert not any(r["event"] == "mammoth.jobs" for r in events)
    assert events[-1]["error_code"] == "not_authenticated"
    # Handlers are detached on finish: nothing further is written.
    logging.getLogger("mammoth.http").info("late", extra={"mammoth": {"event": "http"}})
    assert len(_records(run.path)) == len(events)


def test_debug_lowers_the_level_and_mirrors_to_stderr(
    isolated_run_log: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = runlog.RunLog.start("job.get", argv=[], debug=True)
    logging.getLogger("mammoth.jobs").debug(
        "job.poll", extra={"mammoth": {"event": "job.poll", "job_id": 7, "status": "processing"}}
    )
    run.finish(0)
    assert run.path is not None
    assert any(r["event"] == "job.poll" for r in _records(run.path))
    assert "[mammoth job.poll] job_id=7 status=processing" in capsys.readouterr().err


def test_a_failing_log_directory_never_fails_the_command(
    isolated_run_log: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated_run_log.write_text("not a directory", encoding="utf-8")
    run = runlog.RunLog.start("version", argv=[])
    logging.getLogger("mammoth.http").info("x", extra={"mammoth": {"event": "http"}})
    run.finish(0)
    assert run.ref is None


def test_rotation_ages_out_old_days_and_caps_the_current_file(
    isolated_run_log: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated_run_log.mkdir()
    today = dt.date.today()
    old = isolated_run_log / f"{today - dt.timedelta(days=runlog.RETENTION_DAYS + 1)}.jsonl"
    recent = isolated_run_log / f"{today - dt.timedelta(days=1)}.jsonl"
    stray = isolated_run_log / "notes.jsonl"
    for path in (old, recent, stray):
        path.write_text("{}\n", encoding="utf-8")
    current = runlog.log_file_for(today)
    current.write_text("x" * 10, encoding="utf-8")
    monkeypatch.setattr(runlog, "MAX_FILE_BYTES", 5)

    run = runlog.RunLog.start("version", argv=[])
    run.finish(0)

    assert not old.exists()
    assert recent.exists() and stray.exists()
    rotated = current.with_name(f"{current.stem}.1.jsonl")
    assert rotated.read_text(encoding="utf-8") == "x" * 10
    assert _records(current)[0]["event"] == "command.start"


def test_read_records_filters_by_error_command_and_run(isolated_run_log: Path) -> None:
    ok = runlog.RunLog.start("project.list", argv=[])
    ok.finish(0)
    bad = runlog.RunLog.start("view.get", argv=[])
    logging.getLogger("mammoth.http").info(
        "http", extra={"mammoth": {"event": "http", "status": 404}}
    )
    bad.finish(5, error_code="resource_not_found")

    everything = runlog.read_records(limit=0)
    assert [r["event"] for r in everything] == [
        "command.start",
        "command.end",
        "command.start",
        "http",
        "command.end",
    ]
    errors = runlog.read_records(errors_only=True)
    assert [(r["event"], r["run_id"]) for r in errors] == [
        ("http", bad.run_id),
        ("command.end", bad.run_id),
    ]
    assert {r["run_id"] for r in runlog.read_records(command_id="project.list")} == {ok.run_id}
    assert len(runlog.read_records(run_id=bad.run_id)) == 3
    assert len(runlog.read_records(limit=2)) == 2
    assert runlog.read_records(days=0) == []


def test_log_path_reports_directory_and_files(isolated_run_log: Path) -> None:
    run = runlog.RunLog.start("version", argv=[])
    run.finish(0)
    info = runlog.log_path()
    assert info["directory"] == str(isolated_run_log)
    assert info["files"] == [runlog.log_file_for(dt.date.today()).name]
    assert info["retention_days"] == runlog.RETENTION_DAYS
