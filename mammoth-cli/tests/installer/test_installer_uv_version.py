"""The POSIX installer must version-gate an existing uv.

The installer promises a pinned uv (``UV_PINNED_VERSION``). Before this gate it
reused whatever ``uv`` was on PATH, however old. These tests drive the real
installer against a *stubbed* ``uv`` (and stubbed ``curl``/``wget``) on an
isolated PATH, so they are deterministic and need no network:

* an existing uv at or above the pinned version is used directly, and
* an older existing uv is refused; the installer instead bootstraps its own
  pinned uv (here the download is stubbed to fail, proving the old uv was never
  trusted rather than depending on real network access).
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
    """A ``uv`` stub that reports ``version`` and otherwise records argv, succeeds."""
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
    """A ``curl``/``wget`` stub that always fails, so no real download happens."""
    stub = directory / name
    stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    _make_executable(stub)


def _prepare_tool_python(home: Path) -> None:
    tool_python = home / ".local" / "mammoth-cli" / "bin" / "python"
    tool_python.parent.mkdir(parents=True)
    tool_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    _make_executable(tool_python)


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX installer test")
def test_existing_uv_at_pinned_version_is_used_directly(tmp_path: Path) -> None:
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    log_file = tmp_path / "uv.log"
    _write_uv_stub(stub_dir, log_file, home / ".local" / "bin", _pinned_version())
    _prepare_tool_python(home)

    result = subprocess.run(
        [_SH, str(_INSTALLER_SH), "--local", "--cli-only", "--no-modify-path"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
    )

    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "using existing uv" in result.stderr
    # The compatible uv was used: builds ran, and no pinned-uv bootstrap message.
    log = log_file.read_text(encoding="utf-8")
    assert len([ln for ln in log.splitlines() if ln.startswith("build ")]) == 2
    assert "installing pinned uv" not in result.stderr


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX installer test")
def test_existing_uv_older_than_pinned_is_refused(tmp_path: Path) -> None:
    """An older uv must NOT be trusted: the installer bootstraps the pinned uv.

    Here the download is stubbed to fail, so the installer exits nonzero — the
    point is that it *tried the pinned bootstrap* instead of building with the
    old uv, proving the version gate fired.
    """
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    log_file = tmp_path / "uv.log"
    # An old uv, plus failing curl/wget so the pinned bootstrap cannot succeed.
    _write_uv_stub(stub_dir, log_file, home / ".local" / "bin", "0.9.0")
    _write_failing_downloader(stub_dir, "curl")
    _write_failing_downloader(stub_dir, "wget")

    result = subprocess.run(
        [_SH, str(_INSTALLER_SH), "--local", "--cli-only", "--no-modify-path"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
    )

    assert result.returncode != 0
    assert "older than the pinned" in result.stderr
    assert "installing pinned uv" in result.stderr
    assert "could not download uv" in result.stderr
    # The old uv was never used to build the wheels.
    log = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    assert not [ln for ln in log.splitlines() if ln.startswith("build ")], (
        "installer must not build with an out-of-date uv"
    )
