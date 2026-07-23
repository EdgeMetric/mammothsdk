"""A prerelease/suffixed uv must NOT satisfy the pin.

The installer promises a pinned FINAL uv (``UV_PINNED_VERSION``). A build whose
version string carries any prerelease or build suffix — ``0.11.30rc1``,
``0.11.30-alpha``, ``0.11.30+build`` — is not that pinned release and may behave
differently, so it must be refused even though its numeric fields match. When it
is refused, the installer leaves the user's uv untouched and bootstraps its own
pinned uv.

These tests drive the real installer against a *stubbed* ``uv`` (and stubbed,
always-failing ``curl``/``wget``) on an isolated PATH, so they are deterministic
and need no network. They mirror test_installer_uv_version.py's harness.
"""

from __future__ import annotations

import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_HERE = Path(__file__).resolve()
_INSTALLER_SH = _HERE.parents[2] / "installers" / "mammoth-install.sh"
_SH = shutil.which("sh")


def _pinned_version() -> str:
    match = re.search(r'UV_PINNED_VERSION="([^"]+)"', _INSTALLER_SH.read_text(encoding="utf-8"))
    assert match, "installer must declare UV_PINNED_VERSION"
    return match.group(1)


def _make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _write_uv_stub(directory: Path, log_file: Path, bin_dir: Path, version: str) -> None:
    """A ``uv`` stub reporting ``version`` that otherwise records argv and succeeds."""
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "uv"
    stub.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log_file}"\n'
        f'if [ "$1" = "--version" ]; then printf "uv {version}\\n"; exit 0; fi\n'
        'if [ "$1" = "build" ]; then\n'
        '    project="${5##*/}"\n'
        '    if [ "$project" = "mammoth-cli" ]; then\n'
        '        touch "$4/mammoth_cli-0.6.0-py3-none-any.whl"\n'
        '    else touch "$4/mammoth_io-0.6.0-py3-none-any.whl"; fi\n'
        "fi\n"
        'if [ "$1" = "tool" ] && [ "$2" = "dir" ] && [ "$3" = "--bin" ]; then\n'
        f'    printf "%s\\n" "{bin_dir}"\n'
        'elif [ "$1" = "tool" ] && [ "$2" = "dir" ]; then\n'
        f'    printf "%s\\n" "{bin_dir.parent}"\n'
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    _make_executable(stub)


def _write_failing_downloader(directory: Path, name: str) -> None:
    stub = directory / name
    stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    _make_executable(stub)


def _prepare_tool_python(home: Path) -> None:
    tool_python = home / ".local" / "mammoth-cli" / "bin" / "python"
    tool_python.parent.mkdir(parents=True)
    tool_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    _make_executable(tool_python)


def _run_local(
    tmp_path: Path, uv_version: str
) -> tuple[subprocess.CompletedProcess[str], Path]:
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    log_file = tmp_path / "uv.log"
    _write_uv_stub(stub_dir, log_file, home / ".local" / "bin", uv_version)
    # Failing downloaders so a refused uv cannot silently succeed via a real
    # network bootstrap; a refusal must surface as a nonzero exit.
    _write_failing_downloader(stub_dir, "curl")
    _write_failing_downloader(stub_dir, "wget")
    _prepare_tool_python(home)
    result = subprocess.run(
        [_SH, str(_INSTALLER_SH), "--local", "--cli-only", "--no-modify-path"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
    )
    return result, log_file


def _build_lines(log_file: Path) -> list[str]:
    if not log_file.exists():
        return []
    return [
        ln for ln in log_file.read_text(encoding="utf-8").splitlines() if ln.startswith("build ")
    ]


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX installer test")
def test_prerelease_uv_is_rejected(tmp_path: Path) -> None:
    """A prerelease uv (e.g. 0.11.30rc1) does not satisfy the pinned 0.11.30."""
    pinned = _pinned_version()
    result, log_file = _run_local(tmp_path, f"{pinned}rc1")
    # Refused: the installer tried to bootstrap the pinned uv (download stubbed
    # to fail), rather than trusting the prerelease and building with it.
    assert result.returncode != 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "installing pinned uv" in result.stderr
    assert "could not download uv" in result.stderr
    assert not _build_lines(log_file), "installer must not build with a prerelease uv"


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX installer test")
@pytest.mark.parametrize("clean_version", ["0.11.30", "0.12.0"])
def test_clean_uv_at_or_above_pin_is_accepted(tmp_path: Path, clean_version: str) -> None:
    """A clean final uv at or above the pin is trusted and used directly."""
    result, log_file = _run_local(tmp_path, clean_version)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "using existing uv" in result.stderr
    assert "installing pinned uv" not in result.stderr
    # The trusted uv actually built both wheels.
    assert len(_build_lines(log_file)) == 2
