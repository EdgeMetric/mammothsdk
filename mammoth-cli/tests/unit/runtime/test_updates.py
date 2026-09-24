"""Unit tests for the daily update check and the opt-in automatic upgrade."""

from __future__ import annotations

import datetime as _dt
import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli import __version__
from mammoth_cli.commands import upgrade as upgrade_cmd
from mammoth_cli.runtime import executor, updates


@pytest.fixture
def check_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.delenv("MAMMOTH_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("MAMMOTH_AUTO_UPGRADE", raising=False)
    cache = tmp_path / "update-check.json"
    monkeypatch.setenv("MAMMOTH_UPDATE_CACHE", str(cache))
    return cache


def _write(cache: Path, latest: str | None, *, age: _dt.timedelta = _dt.timedelta()) -> None:
    checked = _dt.datetime.now(_dt.UTC) - age
    cache.write_text(
        json.dumps({"checked_at": checked.isoformat(timespec="seconds"), "latest": latest})
    )


def test_version_ordering_is_numeric() -> None:
    assert updates.is_newer("2.0.19", "2.0.18")
    assert updates.is_newer("2.1.0", "2.0.18")
    assert updates.is_newer("10.0.0", "9.9.9")
    assert not updates.is_newer("2.0.18", "2.0.18")
    assert not updates.is_newer("2.0.17", "2.0.18")
    assert not updates.is_newer(None, "2.0.18")
    # A pre-release of the same number never counts as newer.
    assert not updates.is_newer("2.0.18rc1", "2.0.18")


def test_disabled_by_env_reads_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cache = tmp_path / "c.json"
    monkeypatch.setenv("MAMMOTH_UPDATE_CACHE", str(cache))
    monkeypatch.setenv("MAMMOTH_NO_UPDATE_CHECK", "1")
    _write(cache, "99.0.0")
    assert updates.available_update("project.list") is None
    updates.refresh_if_stale("project.list")
    assert json.loads(cache.read_text())["latest"] == "99.0.0"  # untouched


def test_available_update_comes_from_the_cache_only(check_enabled: Path) -> None:
    assert updates.available_update("project.list") is None  # no cache, no network
    _write(check_enabled, "99.0.0")
    update = updates.available_update("project.list")
    assert update == {
        "current": __version__,
        "latest": "99.0.0",
        "command": "mammoth upgrade --yes",
    }
    _write(check_enabled, __version__)
    assert updates.available_update("project.list") is None


def test_self_managing_commands_get_no_notice(check_enabled: Path) -> None:
    _write(check_enabled, "99.0.0")
    assert updates.available_update("upgrade") is None
    # doctor carries the notice: agents act on meta.update_available.
    assert updates.available_update("doctor") is not None


def test_refresh_only_when_stale(check_enabled: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_fetch() -> str:
        calls.append(1)
        return "99.0.0"

    monkeypatch.setattr(updates, "_fetch_latest", fake_fetch)
    updates.refresh_if_stale("project.list")
    assert calls == [1]
    assert json.loads(check_enabled.read_text())["latest"] == "99.0.0"
    updates.refresh_if_stale("project.list")
    assert calls == [1]  # fresh: no second fetch
    _write(check_enabled, "99.0.0", age=_dt.timedelta(hours=25))
    updates.refresh_if_stale("project.list")
    assert calls == [1, 1]


def test_refresh_survives_a_failed_fetch(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(updates, "_fetch_latest", lambda: None)
    updates.refresh_if_stale("project.list")
    document = json.loads(check_enabled.read_text())
    assert document["latest"] is None
    assert updates.available_update("project.list") is None


def test_hint_goes_to_stderr_in_human_modes_only(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(check_enabled, "99.0.0")
    update = updates.available_update("project.list")
    assert update is not None
    for mode in ("json", "ndjson", "yaml"):
        stream = io.StringIO()
        monkeypatch.setattr("sys.stderr", stream)
        updates.emit_hint(update, output=mode)
        assert stream.getvalue() == ""
    stream = io.StringIO()
    monkeypatch.setattr("sys.stderr", stream)
    updates.emit_hint(update, output="table")
    assert "99.0.0" in stream.getvalue() and "mammoth upgrade --yes" in stream.getvalue()


def test_success_envelope_carries_update_available(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(updates, "_fetch_latest", lambda: "99.0.0")
    executor.run("project.list", "json", lambda: ({"projects": []}, {}))
    first = json.loads(capsys.readouterr().out)
    assert "update_available" not in first["meta"]  # cache was empty at start; nulls are omitted
    executor.run("project.list", "json", lambda: ({"projects": []}, {}))
    second = json.loads(capsys.readouterr().out)
    assert second["meta"]["update_available"]["latest"] == "99.0.0"


def test_envelope_carries_what_the_command_itself_learned(
    check_enabled: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """doctor asks PyPI and refreshes the cache; its own envelope must say so.

    Seen after a release: the daily cache still said the installed version was
    newest, doctor reported the newer one in its checks, and meta did not.
    """
    _write(check_enabled, __version__)

    def _doctor_like() -> tuple[dict[str, Any], dict[str, Any]]:
        updates.write_cache("99.0.0")
        return {"ok": True}, {}

    executor.run("doctor", "json", _doctor_like)
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["meta"]["update_available"]["latest"] == "99.0.0"


def test_auto_upgrade_is_opt_in(check_enabled: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(check_enabled, "99.0.0")
    ran: list[list[str]] = []
    monkeypatch.setattr(upgrade_cmd, "run_upgrade", lambda argv: ran.append(argv))
    assert updates.auto_upgrade("project.list") is None
    assert ran == []


def test_auto_upgrade_runs_once_per_release(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", "1")
    _write(check_enabled, "99.0.0")
    ran: list[list[str]] = []

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        ran.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(upgrade_cmd, "run_upgrade", fake_run)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: upgrade_cmd.MANAGER_PIP)
    monkeypatch.setattr("sys.stderr", io.StringIO())
    written: list[dict[str, Any]] = []

    class Log:
        def write(self, body: dict[str, Any]) -> None:
            written.append(body)

    record = updates.auto_upgrade("project.list", Log())
    assert record is not None and record["ok"] is True
    assert ran and ran[0][-2:] == ["--upgrade", "mammoth-cli"]
    assert written[0]["event"] == "auto_upgrade"
    # The cache records the release it installed: no second attempt from the
    # (still old) process, and none from the next command either.
    assert json.loads(check_enabled.read_text())["upgraded_to"] == "99.0.0"
    assert updates.auto_upgrade("project.list", Log()) is None
    assert len(ran) == 1


def test_auto_upgrade_failure_never_breaks_the_command(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", "1")
    _write(check_enabled, "99.0.0")

    def boom(argv: list[str]) -> subprocess.CompletedProcess[str]:
        raise OSError("no pip here")

    monkeypatch.setattr(upgrade_cmd, "run_upgrade", boom)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: upgrade_cmd.MANAGER_PIP)
    stream = io.StringIO()
    monkeypatch.setattr("sys.stderr", stream)
    record = updates.auto_upgrade("project.list")
    assert record is not None and record["ok"] is False
    assert "failed" in stream.getvalue()
