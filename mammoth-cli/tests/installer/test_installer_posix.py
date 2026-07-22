"""Structural tests for the POSIX installer (no network paths exercised).

These cover the INS-* option-handling contract that runs before any download:
help, mutually exclusive selection, and unknown options. Network-dependent
paths (uv acquisition, ``uv tool install``) are validated against a local
release fixture in CI, not here.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_INSTALLER = Path(__file__).resolve().parents[2] / "installers" / "mammoth-install.sh"
_SH = shutil.which("sh")


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
