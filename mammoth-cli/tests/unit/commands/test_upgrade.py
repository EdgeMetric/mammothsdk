"""Unit tests for the local ``upgrade`` command. No network, no subprocess.

Every test mocks the three side-effecting seams -- install-manager detection,
the PyPI latest-version lookup, and the subprocess runner -- so no real network
request or process launch ever happens.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from mammoth_cli import __version__
from mammoth_cli.app import command_option_names
from mammoth_cli.commands import upgrade as upgrade_cmd
from mammoth_cli.errors.envelope import EXIT_RETRYABLE, CliError
from mammoth_cli.runtime.invocation import Invocation


def _inv(**overrides: object) -> Invocation:
    return Invocation(command_id="upgrade", **overrides)  # type: ignore[arg-type]


def _completed(command: list[str], *, returncode: int = 0, stderr: str = "") -> object:
    return subprocess.CompletedProcess(
        args=command, returncode=returncode, stdout="", stderr=stderr
    )


def _no_subprocess(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Fail loudly if any test path reaches the real subprocess runner."""
    calls: list[list[str]] = []

    def _boom(command: list[str]) -> object:
        raise AssertionError(f"unexpected upgrade subprocess: {command}")

    monkeypatch.setattr(upgrade_cmd, "_run_upgrade", _boom)
    return calls


# --- build_upgrade_command (pure) -----------------------------------------


def test_build_command_uv_latest() -> None:
    assert upgrade_cmd.build_upgrade_command("uv", None) == [
        "uv",
        "tool",
        "upgrade",
        "mammoth-cli",
    ]


def test_build_command_uv_pinned() -> None:
    assert upgrade_cmd.build_upgrade_command("uv", "1.2.3") == [
        "uv",
        "tool",
        "install",
        "--force",
        "mammoth-cli==1.2.3",
    ]


def test_build_command_pipx_latest_and_pinned() -> None:
    assert upgrade_cmd.build_upgrade_command("pipx", None) == ["pipx", "upgrade", "mammoth-cli"]
    assert upgrade_cmd.build_upgrade_command("pipx", "9.9.9") == [
        "pipx",
        "install",
        "--force",
        "mammoth-cli==9.9.9",
    ]


def test_build_command_pip_latest_and_pinned() -> None:
    assert upgrade_cmd.build_upgrade_command("pip", None) == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "mammoth-cli",
    ]
    assert upgrade_cmd.build_upgrade_command("pip", "0.6.0") == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "mammoth-cli==0.6.0",
    ]


# --- --check (read-only) ---------------------------------------------------


def test_check_reports_would_upgrade_without_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "uv")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: "999.0.0")

    data, meta = upgrade_cmd.perform(_inv(output="json"), check=True, target_version=None)

    assert data["action"] == "would_upgrade"
    assert data["manager"] == "uv"
    assert data["current_version"] == __version__
    assert data["latest_version"] == "999.0.0"
    assert data["command"] is None
    assert meta == {}


def test_check_reports_already_current(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "pipx")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: __version__)

    data, _meta = upgrade_cmd.perform(_inv(output="json"), check=True, target_version=None)

    assert data["action"] == "already_current"
    assert data["command"] is None


def test_check_never_prompts_even_without_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "pip")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: "999.0.0")

    # no_input + no --yes would block a mutation, but --check is class read.
    data, _meta = upgrade_cmd.perform(
        _inv(output="json", no_input=True, yes=False), check=True, target_version=None
    )
    assert data["action"] == "would_upgrade"


# --- upgrade path ----------------------------------------------------------


def test_upgrade_already_current_makes_no_change(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "uv")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: __version__)

    data, _meta = upgrade_cmd.perform(
        _inv(output="json", no_input=True, yes=True), check=False, target_version=None
    )
    assert data["action"] == "already_current"
    assert data["command"] is None


def test_upgrade_to_latest_runs_built_command_with_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    ran: list[list[str]] = []

    def _fake_run(command: list[str]) -> object:
        ran.append(command)
        return _completed(command)

    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "uv")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: "999.0.0")
    monkeypatch.setattr(upgrade_cmd, "_run_upgrade", _fake_run)

    data, _meta = upgrade_cmd.perform(
        _inv(output="json", no_input=True, yes=True), check=False, target_version=None
    )
    assert data["action"] == "upgraded"
    assert ran == [["uv", "tool", "upgrade", "mammoth-cli"]]
    assert data["command"] == ["uv", "tool", "upgrade", "mammoth-cli"]


def test_upgrade_pinned_version_forces_install_without_pypi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ran: list[list[str]] = []

    def _fake_run(command: list[str]) -> object:
        ran.append(command)
        return _completed(command)

    def _no_pypi() -> str | None:
        raise AssertionError("pinned upgrade must not query PyPI")

    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "pipx")
    monkeypatch.setattr(upgrade_cmd, "latest_version", _no_pypi)
    monkeypatch.setattr(upgrade_cmd, "_run_upgrade", _fake_run)

    data, _meta = upgrade_cmd.perform(
        _inv(output="json", no_input=True, yes=True), check=False, target_version="1.2.3"
    )
    assert data["action"] == "upgraded"
    assert data["target_version"] == "1.2.3"
    assert ran == [["pipx", "install", "--force", "mammoth-cli==1.2.3"]]


def test_upgrade_no_yes_in_no_input_mode_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "uv")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: "999.0.0")

    with pytest.raises(CliError) as excinfo:
        upgrade_cmd.perform(
            _inv(output="json", no_input=True, yes=False), check=False, target_version=None
        )
    assert excinfo.value.code == "confirmation_required"


def test_upgrade_failure_surfaces_upgrade_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(upgrade_cmd, "detect_manager", lambda: "uv")
    monkeypatch.setattr(upgrade_cmd, "latest_version", lambda: "999.0.0")
    monkeypatch.setattr(
        upgrade_cmd,
        "_run_upgrade",
        lambda command: _completed(command, returncode=1, stderr="boom"),
    )

    with pytest.raises(CliError) as excinfo:
        upgrade_cmd.perform(
            _inv(output="json", no_input=True, yes=True), check=False, target_version="1.2.3"
        )
    assert excinfo.value.code == "upgrade_failed"


# --- network + response failures ------------------------------------------


def test_pypi_unreachable_is_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.error

    def _raise(*_args: object, **_kwargs: object) -> object:
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(upgrade_cmd.urllib.request, "urlopen", _raise)

    with pytest.raises(CliError) as excinfo:
        upgrade_cmd.latest_version()
    assert excinfo.value.code == "pypi_unreachable"
    assert excinfo.value.retryable is True
    assert excinfo.value.exit_status == EXIT_RETRYABLE


def test_pypi_bad_payload_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_exc: object) -> bool:
            return False

        def read(self) -> bytes:
            return b"{ not json"

    monkeypatch.setattr(upgrade_cmd.urllib.request, "urlopen", lambda *_a, **_k: _Resp())

    with pytest.raises(CliError) as excinfo:
        upgrade_cmd.latest_version()
    assert excinfo.value.code == "pypi_response_invalid"


def test_latest_version_reads_info_version(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_exc: object) -> bool:
            return False

        def read(self) -> bytes:
            return b'{"info": {"version": "7.7.7"}}'

    monkeypatch.setattr(upgrade_cmd.urllib.request, "urlopen", lambda *_a, **_k: _Resp())
    assert upgrade_cmd.latest_version() == "7.7.7"


# --- manager detection -----------------------------------------------------


def test_detect_manager_uv_from_path(monkeypatch: pytest.MonkeyPatch) -> None:
    exe = "/home/u/.local/share/uv/tools/mammoth-cli/bin/python"
    monkeypatch.setattr(upgrade_cmd.sys, "executable", exe)
    assert upgrade_cmd.detect_manager() == "uv"


def test_detect_manager_pipx_from_path(monkeypatch: pytest.MonkeyPatch) -> None:
    exe = "/home/u/.local/pipx/venvs/mammoth-cli/bin/python"
    monkeypatch.setattr(upgrade_cmd.sys, "executable", exe)
    assert upgrade_cmd.detect_manager() == "pipx"


def test_detect_manager_pip_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(upgrade_cmd.sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(upgrade_cmd, "_uv_tool_lists_package", lambda: False)
    assert upgrade_cmd.detect_manager() == "pip"


# --- option surface --------------------------------------------------------


def test_upgrade_declares_check_version_and_confirmation_options() -> None:
    opts = command_option_names("upgrade")
    assert {"--check", "--version", "--yes", "--output", "--no-input"} <= opts
