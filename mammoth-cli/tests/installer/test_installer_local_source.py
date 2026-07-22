"""Real (unmocked) tests for the ``--local`` no-index install path.

These run the actual installer script against a *stubbed* ``uv`` on an isolated
``PATH``: no network, no real build, no real install. The stub records every
``uv`` invocation so the test can assert the offline contract — the SDK and CLI
wheels are both built from the source checkout and installed from the local
wheelhouse with ``--no-index`` — which is what lets a user install and use the
CLI with no package index configured.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_HERE = Path(__file__).resolve()
_INSTALLER_SH = _HERE.parents[2] / "installers" / "mammoth-install.sh"
_SH = shutil.which("sh")


def _write_uv_stub(directory: Path, log_file: Path, bin_dir: Path) -> None:
    """Write an executable ``uv`` stub that logs its argv and succeeds.

    ``uv tool dir --bin`` prints ``bin_dir``; every other subcommand simply
    records its arguments and exits 0, so the installer's flow runs end to end
    without a real build or install.
    """
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "uv"
    stub.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log_file}"\n'
        'if [ "$1" = "tool" ] && [ "$2" = "dir" ]; then\n'
        f'    printf "%s\\n" "{bin_dir}"\n'
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
def test_local_source_builds_both_wheels_and_installs_offline(tmp_path: Path) -> None:
    """--local builds the SDK + CLI wheels and installs them with --no-index."""
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    log_file = tmp_path / "uv.log"
    _write_uv_stub(stub_dir, log_file, home / ".local" / "bin")

    result = subprocess.run(
        [_SH, str(_INSTALLER_SH), "--local", "--cli-only"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
    )

    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    log = log_file.read_text(encoding="utf-8")
    build_lines = [line for line in log.splitlines() if line.startswith("build ")]
    # Two builds: the mammoth-io SDK wheel and the mammoth-cli wheel.
    assert len(build_lines) == 2, f"expected 2 uv build calls, got: {build_lines}"
    install_lines = [line for line in log.splitlines() if line.startswith("tool install")]
    assert install_lines, "expected a 'uv tool install' call"
    assert any(
        "--no-index" in line and "--find-links" in line for line in install_lines
    ), f"install must be offline via wheelhouse: {install_lines}"
