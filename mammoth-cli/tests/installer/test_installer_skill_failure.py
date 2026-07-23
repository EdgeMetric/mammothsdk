"""Real (unmocked) tests that a failed skill install fails the installer.

These run the actual installer scripts against a *stubbed* ``mammoth`` binary
placed on an isolated ``PATH``. No network, no admin, no real CLI: the stub is
a tiny script that exits nonzero for ``skill install``. The contract under test
is simple and load-bearing: if ``mammoth skill install`` fails, the installer
must exit NONZERO (it previously downgraded this to a warning and exited 0).

They deliberately use ``--skills-only`` so no uv acquisition or ``uv tool
install`` is attempted; only the skill-install path executes.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_HERE = Path(__file__).resolve()
_INSTALLER_SH = _HERE.parents[2] / "installers" / "mammoth-install.sh"
_INSTALLER_PS1 = _HERE.parents[2] / "installers" / "mammoth-install.ps1"
_SH = shutil.which("sh")
_PWSH = shutil.which("pwsh")


def _write_stub(directory: Path, *, exit_code_on_skill: int) -> None:
    """Write an executable ``mammoth`` stub into ``directory``.

    The stub exits ``exit_code_on_skill`` for a ``skill`` invocation and 0
    otherwise, so tests can drive both the failure and success paths.
    """
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "mammoth"
    stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "skill" ]; then\n'
        f"    exit {exit_code_on_skill}\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_sh(tmp_path: Path, *, skill_exit: int) -> subprocess.CompletedProcess[str]:
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    _write_stub(stub_dir, exit_code_on_skill=skill_exit)
    # Isolated PATH: the stub first, then the system minimum. uv is absent, so
    # the installer falls back to $HOME/.local/bin for BIN_DIR and resolves the
    # `mammoth` executable via PATH -> our stub.
    return subprocess.run(
        [_SH, str(_INSTALLER_SH), "--skills-only"],
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
    )


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
def test_sh_skill_install_failure_exits_nonzero(tmp_path: Path) -> None:
    result = _run_sh(tmp_path, skill_exit=3)
    assert result.returncode != 0, (
        "installer must fail when 'mammoth skill install' fails; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "skill install did not complete" in result.stderr


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
def test_sh_skill_install_success_exits_zero(tmp_path: Path) -> None:
    result = _run_sh(tmp_path, skill_exit=0)
    assert result.returncode == 0, (
        "clean skill install must still succeed; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "installed the agent skill" in result.stderr


def _write_windows_stub(directory: Path, *, exit_code_on_skill: int) -> None:
    """Write a ``mammoth.cmd`` stub so pwsh's ``& mammoth`` resolves via PATHEXT.

    On Windows an extensionless ``#!/bin/sh`` file is not executable, so the
    PowerShell test needs a ``.cmd`` shim instead.
    """
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "mammoth.cmd"
    stub.write_text(
        "@echo off\r\n"
        f'if "%1"=="skill" exit /b {exit_code_on_skill}\r\n'
        "exit /b 0\r\n",
        encoding="utf-8",
    )


@pytest.mark.skipif(_PWSH is None, reason="pwsh not available")
def test_ps1_skill_install_failure_exits_nonzero(tmp_path: Path) -> None:
    assert _PWSH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        _write_windows_stub(stub_dir, exit_code_on_skill=3)
    else:
        _write_stub(stub_dir, exit_code_on_skill=3)
    env = dict(os.environ)
    # Stub first on PATH so `& mammoth` resolves to it. USERPROFILE is set so
    # the -SkillsOnly fallback for BIN_DIR (uv is absent) does not choke on a
    # null path when this runs on non-Windows pwsh.
    env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"
    env["USERPROFILE"] = str(home)
    result = subprocess.run(
        [
            _PWSH,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(_INSTALLER_PS1),
            "-SkillsOnly",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode != 0, (
        "PowerShell installer must fail when 'mammoth skill install' fails; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "skill install did not complete" in (result.stdout + result.stderr)
