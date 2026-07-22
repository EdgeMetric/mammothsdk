"""Structural tests for the POSIX installer (no network paths exercised).

These cover the INS-* option-handling contract that runs before any download:
help, mutually exclusive selection, and unknown options. Network-dependent
paths (uv acquisition, ``uv tool install``) are validated against a local
release fixture in CI, not here.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_INSTALLER = Path(__file__).resolve().parents[2] / "installers" / "mammoth-install.sh"
_SH = shutil.which("sh")


def _write_uname_stub(directory: Path, *, kernel: str) -> None:
    """Write a ``uname`` stub reporting ``kernel`` for ``-s`` (real arch for ``-m``)."""
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "uname"
    stub.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        f'  -s) echo "{kernel}" ;;\n'
        '  -m) echo "x86_64" ;;\n'
        '  *) echo "unknown" ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    assert _SH is not None
    return subprocess.run(
        [_SH, str(_INSTALLER), *args],
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"},
    )


def test_installer_exists_and_has_shebang() -> None:
    text = _INSTALLER.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh")
    assert "uv tool install" in text
    assert "0.11.30" in text  # pinned uv version


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
def test_help_exits_zero() -> None:
    result = _run("--help")
    assert result.returncode == 0
    assert "mammoth-install" in (result.stdout + result.stderr).lower()


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
def test_cli_only_and_skills_only_are_mutually_exclusive() -> None:
    result = _run("--cli-only", "--skills-only")
    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
def test_unknown_option_is_rejected() -> None:
    result = _run("--bogus")
    assert result.returncode != 0
    assert "unknown option" in result.stderr


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.parametrize(
    "kernel", ["MINGW64_NT-10.0-22631", "MSYS_NT-10.0-22631", "CYGWIN_NT-10.0"]
)
def test_mingw_msys_cygwin_defers_to_powershell_installer(kernel: str) -> None:
    """R10: git-bash/MSYS/Cygwin on Windows must defer to the .ps1 installer.

    Previously this hit the catch-all ``*) die "unsupported OS ..."`` branch and
    exited nonzero. That is the wrong entry point, not an unsupported platform,
    so it must print a clear message and exit 0 (not fail the caller/CI job).
    """
    assert _SH is not None
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        stub_dir = tmp / "bin"
        home = tmp / "home"
        home.mkdir(parents=True, exist_ok=True)
        _write_uname_stub(stub_dir, kernel=kernel)
        result = subprocess.run(
            [_SH, str(_INSTALLER), "--cli-only"],
            capture_output=True,
            text=True,
            timeout=30,
            env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
        )
        assert result.returncode == 0, (
            f"must not fail the job on {kernel}; stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "mammoth-install.ps1" in result.stderr


def test_powershell_installer_declares_contract() -> None:
    ps1 = _INSTALLER.with_name("mammoth-install.ps1").read_text(encoding="utf-8")
    tokens = (
        "$CliOnly",
        "$SkillsOnly",
        "$NoModifyPath",
        "$Version",
        "0.11.30",
        "uv tool install",
    )
    for token in tokens:
        assert token in ps1
