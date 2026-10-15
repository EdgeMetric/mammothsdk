"""Unit tests for the daily update check and the automatic update."""

from __future__ import annotations

import datetime as _dt
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pexpect
import pytest

from mammoth_cli import __version__
from mammoth_cli.commands import upgrade as upgrade_cmd
from mammoth_cli.runtime import executor, updates


@pytest.fixture
def check_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.delenv("MAMMOTH_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("MAMMOTH_AUTO_UPGRADE", raising=False)
    # The hint tests need the notice; a detached refresh must never install anything.
    monkeypatch.setenv("MAMMOTH_NO_AUTO_UPDATE", "1")
    cache = tmp_path / "update-check.json"
    monkeypatch.setenv("MAMMOTH_UPDATE_CACHE", str(cache))
    # A refresh runs in a detached child; it must fail fast instead of reaching PyPI.
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
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
    check_enabled: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    executor.run("project.list", "json", lambda: ({"projects": []}, {}))
    first = json.loads(capsys.readouterr().out)
    assert "update_available" not in first["meta"]  # no cached answer; nulls are omitted
    _write(check_enabled, "99.0.0")
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


def test_auto_upgrade_off_switch_stops_the_upgrade(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(check_enabled, "99.0.0")
    for off in ("0", "false", "No", "OFF"):
        monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", off)
        assert updates.auto_upgrade_enabled() is False
        assert updates.auto_upgrade("99.0.0") is None
    assert "upgraded_to" not in json.loads(check_enabled.read_text())


_DECISION = "from mammoth_cli.runtime import updates; print(updates.auto_upgrade_enabled())"


def _decision_env(tmp_path: Path, **extra: str) -> dict[str, str]:
    drop = {"CI", "MAMMOTH_AUTO_UPGRADE", "MAMMOTH_NO_AUTO_UPDATE", "MAMMOTH_NO_UPDATE_CHECK"}
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env["MAMMOTH_UPDATE_CACHE"] = str(tmp_path / "update-check.json")
    env.update(extra)
    return env


def _decide(env: dict[str, str]) -> str:
    done = subprocess.run(
        [sys.executable, "-c", _DECISION], env=env, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


class _Tty(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    """Set the session shape: ``session(tty=True, **env)``; no CI or override variables."""
    for name in updates._CI_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in (
        "MAMMOTH_AUTO_UPGRADE",
        "MAMMOTH_NO_AUTO_UPDATE",
        "MAMMOTH_NO_UPDATE_CHECK",
        updates.DECIDED_ENV,
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MAMMOTH_UPDATE_CACHE", str(tmp_path / "update-check.json"))

    def _set(tty: bool = True, **env: str) -> None:
        monkeypatch.setattr("sys.stdin", _Tty(tty))
        monkeypatch.setattr("sys.stdout", _Tty(tty))
        for key, value in env.items():
            monkeypatch.setenv(key, value)

    return _set


def test_auto_update_is_on_for_an_interactive_terminal(session: Any) -> None:
    session(tty=True)
    assert updates.auto_upgrade_enabled() is True


@pytest.mark.parametrize(
    "ci_var",
    ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL", "CIRCLECI", "TF_BUILD"],
)
def test_auto_update_is_off_in_ci_even_on_a_terminal(session: Any, ci_var: str) -> None:
    session(tty=True, **{ci_var: "true"})
    assert updates.auto_upgrade_enabled() is False


def test_ci_false_does_not_count_as_ci(session: Any) -> None:
    session(tty=True, CI="false")
    assert updates.auto_upgrade_enabled() is True


def test_auto_update_is_off_without_a_tty(session: Any) -> None:
    session(tty=False)
    assert updates.auto_upgrade_enabled() is False


def test_auto_update_off_when_only_stdout_is_a_pipe(
    session: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    session(tty=True)
    monkeypatch.setattr("sys.stdout", _Tty(False))
    assert updates.auto_upgrade_enabled() is False


def test_auto_upgrade_1_forces_it_on_in_ci_and_without_a_tty(session: Any) -> None:
    session(tty=False, CI="true", MAMMOTH_AUTO_UPGRADE="1")
    assert updates.auto_upgrade_enabled() is True


def test_no_auto_update_forces_it_off_even_when_forced_on(session: Any) -> None:
    session(tty=True, MAMMOTH_AUTO_UPGRADE="1", MAMMOTH_NO_AUTO_UPDATE="1")
    assert updates.auto_upgrade_enabled() is False


def test_the_hint_shows_whenever_auto_install_will_not_happen(session: Any, tmp_path: Path) -> None:
    session(tty=False)
    _write(tmp_path / "update-check.json", "99.0.0")
    update = updates.available_update("project.list")
    assert update is not None and update["latest"] == "99.0.0"
    # An interactive session will install it itself: no hint.
    session(tty=True)
    assert updates.available_update("project.list") is None


def test_the_detached_updater_gets_the_parents_decision(
    session: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []

    def fake_popen(argv: list[str], **kwargs: Any) -> None:
        seen.append(kwargs["env"][updates.DECIDED_ENV])

    monkeypatch.setattr(updates.subprocess, "Popen", fake_popen)
    session(tty=True)
    updates.refresh_in_background("project.list")
    session(tty=False)
    Path(os.environ["MAMMOTH_UPDATE_CACHE"]).unlink()
    updates.refresh_in_background("project.list")
    assert seen == ["1", "0"]
    # In the child (no TTY, decision passed in) the parent's answer wins.
    monkeypatch.setenv(updates.DECIDED_ENV, "1")
    assert updates.auto_upgrade_enabled() is True
    monkeypatch.setenv(updates.DECIDED_ENV, "0")
    session(tty=True)
    assert updates.auto_upgrade_enabled() is False


def test_auto_update_opt_outs(tmp_path: Path) -> None:
    assert _decide(_decision_env(tmp_path, MAMMOTH_NO_AUTO_UPDATE="1")) == "False"
    assert _decide(_decision_env(tmp_path, MAMMOTH_AUTO_UPGRADE="0")) == "False"
    assert _decide(_decision_env(tmp_path, MAMMOTH_NO_UPDATE_CHECK="1")) == "False"


def test_cache_goes_stale_after_a_day(check_enabled: Path) -> None:
    _write(check_enabled, "99.0.0", age=_dt.timedelta(hours=23))
    assert updates.cache_is_fresh(updates.read_cache())
    _write(check_enabled, "99.0.0", age=_dt.timedelta(hours=25))
    assert not updates.cache_is_fresh(updates.read_cache())


def test_notice_is_hidden_while_auto_update_will_install_it(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(check_enabled, "99.0.0")
    monkeypatch.delenv("MAMMOTH_NO_AUTO_UPDATE")
    monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", "1")
    assert updates.available_update("project.list") is None
    # A failed install brings the notice back, so the user can run it by hand.
    updates.write_cache("99.0.0", upgrade_failed="99.0.0")
    assert updates.available_update("project.list") is not None


def test_auto_upgrade_runs_once_per_release(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAMMOTH_NO_AUTO_UPDATE")
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

    record = updates.auto_upgrade("99.0.0", Log())
    assert record is not None and record["ok"] is True
    assert ran and ran[0][-2:] == ["--upgrade", "mammoth-cli"]
    assert written[0]["event"] == "auto_upgrade"
    # The cache records the release it installed: no second attempt from the
    # (still old) process, and none from the next command either.
    assert json.loads(check_enabled.read_text())["upgraded_to"] == "99.0.0"
    assert updates.auto_upgrade("99.0.0", Log()) is None
    assert len(ran) == 1


def test_auto_upgrade_failure_never_breaks_the_command(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAMMOTH_NO_AUTO_UPDATE")
    monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", "1")
    _write(check_enabled, "99.0.0")

    def boom(argv: list[str]) -> subprocess.CompletedProcess[str]:
        raise OSError("no pip here")

    monkeypatch.setattr(upgrade_cmd, "run_upgrade", boom)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: upgrade_cmd.MANAGER_PIP)
    stream = io.StringIO()
    monkeypatch.setattr("sys.stderr", stream)
    record = updates.auto_upgrade("99.0.0")
    assert record is not None and record["ok"] is False
    assert json.loads(check_enabled.read_text())["upgrade_failed"] == "99.0.0"


def test_background_refresh_stamps_the_cache_and_returns(check_enabled: Path) -> None:
    _write(check_enabled, "99.0.0", age=_dt.timedelta(days=3))
    updates.refresh_in_background("project.list")
    document = json.loads(check_enabled.read_text())
    assert updates.cache_is_fresh(document)  # claimed before the child runs
    assert document["latest"] == "99.0.0"  # the earlier answer survives


def test_background_refresh_leaves_a_fresh_cache_alone(check_enabled: Path) -> None:
    _write(check_enabled, "99.0.0")
    before = check_enabled.read_text()
    updates.refresh_in_background("project.list")
    assert check_enabled.read_text() == before


def test_background_refresh_skips_commands_that_check_pypi_themselves(
    check_enabled: Path,
) -> None:
    updates.refresh_in_background("doctor")
    assert not check_enabled.exists()


# --- a pinned install is never auto-updated --------------------------------


def _fake_installs(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    ran: list[list[str]] = []

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        ran.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(upgrade_cmd, "run_upgrade", fake_run)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: upgrade_cmd.MANAGER_PIP)
    monkeypatch.setattr(upgrade_cmd, "installed_version", lambda: None)
    return ran


def _invocation() -> Any:
    from mammoth_cli.runtime.invocation import Invocation

    return Invocation(command_id="upgrade", yes=True, no_input=True)


def test_a_pinned_install_is_not_auto_upgraded(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAMMOTH_NO_AUTO_UPDATE")
    monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", "1")
    _write(check_enabled, "99.0.0")
    ran = _fake_installs(monkeypatch)
    assert updates.write_pin("1.2.3")
    assert updates.auto_upgrade("99.0.0") is None
    assert ran == []
    assert "upgraded_to" not in json.loads(check_enabled.read_text())


def test_the_update_hint_still_shows_for_a_pinned_install(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAMMOTH_NO_AUTO_UPDATE")
    monkeypatch.setenv("MAMMOTH_AUTO_UPGRADE", "1")
    _write(check_enabled, "99.0.0")
    # Auto-update would install it: no hint. Pinned, it will not: the hint shows.
    assert updates.available_update("project.list") is None
    updates.write_pin("1.2.3")
    update = updates.available_update("project.list")
    assert update is not None and update["latest"] == "99.0.0"


def test_upgrade_with_a_version_writes_the_pin(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ran = _fake_installs(monkeypatch)
    upgrade_cmd.perform(_invocation(), check=False, target_version="2.0.5")
    assert ran and ran[0][-1] == "mammoth-cli==2.0.5"
    assert updates.read_pin() == "2.0.5"


def test_a_plain_upgrade_clears_the_pin(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_installs(monkeypatch)
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: "999.0.0")
    updates.write_pin("2.0.5")
    upgrade_cmd.perform(_invocation(), check=False, target_version=None)
    assert updates.read_pin() is None


def test_a_failed_pinned_install_leaves_the_pin_alone(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mammoth_cli.errors.envelope import CliError

    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: upgrade_cmd.MANAGER_PIP)
    monkeypatch.setattr(
        upgrade_cmd,
        "run_upgrade",
        lambda argv: subprocess.CompletedProcess(argv, 1, "", "boom"),
    )
    with pytest.raises(CliError):
        upgrade_cmd.perform(_invocation(), check=False, target_version="2.0.5")
    assert updates.read_pin() is None


def test_the_installer_records_a_pin_without_installing(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ran = _fake_installs(monkeypatch)
    data, _meta = upgrade_cmd.perform(
        _invocation(), check=False, target_version=None, record_pin="2.0.5"
    )
    assert data["action"] == "pinned" and ran == []
    assert updates.read_pin() == "2.0.5"


def test_the_installer_without_a_version_drops_the_pin(
    check_enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_installs(monkeypatch)
    updates.write_pin("2.0.5")
    data, _meta = upgrade_cmd.perform(
        _invocation(), check=False, target_version=None, record_pin="none"
    )
    assert data["action"] == "unpinned"
    assert updates.read_pin() is None


def test_a_malformed_pin_is_refused(check_enabled: Path) -> None:
    from mammoth_cli.errors.envelope import CliError

    with pytest.raises(CliError) as refused:
        upgrade_cmd.perform(_invocation(), check=False, target_version=None, record_pin="x;rm")
    assert refused.value.code == "pin_not_recorded"
    assert updates.read_pin() is None
