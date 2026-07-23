"""Real (unmocked) tests for the ``--local`` install path.

These run the actual installer script against a *stubbed* ``uv`` on an isolated
``PATH``: no network, no real build, no real install. The stub records every
``uv`` invocation so the test can assert the ONLINE contract (R10/R11) — the
SDK and CLI wheels are both built from the source checkout and installed via
``--find-links`` (so mammoth-io/mammoth-cli resolve to those local wheels)
while ``--no-index`` is deliberately absent, so every other runtime dependency
(typer, rich, platformdirs, ...) still resolves from PyPI. A prior version of
this installer used ``--no-index``, but that is unresolvable on a clean
machine: third-party deps are not in the local wheelhouse and are not cached,
so a real offline install could never succeed. This test previously asserted
that always-broken offline contract with an always-pass ``uv`` stub; it now
asserts the online one instead.
"""

from __future__ import annotations

import json
import os
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
_UV = shutil.which("uv")


def _version_key(value: str) -> list[int]:
    return [int(re.sub(r"\D.*$", "", part) or "0") for part in value.split(".")]


def _uv_meets_pinned_minimum() -> bool:
    """True when the on-PATH uv is at least the installer's pinned version.

    The installer only reuses an existing uv when it meets the pinned minimum
    (UV_PINNED_VERSION); an older uv triggers an installer-owned bootstrap
    instead. Tests that drive the installer with the on-PATH uv only hold their
    premise when that uv is new enough, so they skip cleanly otherwise rather
    than exercising (or failing on) the network bootstrap path.
    """
    if _UV is None:
        return False
    match = re.search(r'UV_PINNED_VERSION="([^"]+)"', _INSTALLER_SH.read_text(encoding="utf-8"))
    if not match:
        return False
    try:
        out = subprocess.check_output([_UV, "--version"], text=True)
    except (OSError, subprocess.SubprocessError):
        return False
    parts = out.split()
    if len(parts) < 2:
        return False
    return _version_key(parts[1]) >= _version_key(match.group(1))


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
        # The installer now gates an existing uv on its version; report the
        # pinned version so this stub is accepted and used directly.
        'if [ "$1" = "--version" ]; then printf "uv 0.11.30\\n"; exit 0; fi\n'
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
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="the POSIX .sh --local flow defers to the .ps1 installer on Windows; "
    "Windows install is covered by the PowerShell installer tests",
)
def test_local_source_builds_both_wheels_and_installs_online(tmp_path: Path) -> None:
    """--local builds the SDK + CLI wheels, then installs ONLINE via --find-links.

    ``--no-index`` must NOT be present: third-party runtime deps (typer, rich,
    platformdirs, ...) are not in the local wheelhouse, so a real --no-index
    install can never resolve them on a clean machine. Only mammoth-io and
    mammoth-cli should come from the local wheelhouse; everything else must
    still be resolvable from the default index (PyPI).
    """
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    log_file = tmp_path / "uv.log"
    _write_uv_stub(stub_dir, log_file, home / ".local" / "bin")
    tool_python = home / ".local" / "mammoth-cli" / "bin" / "python"
    tool_python.parent.mkdir(parents=True)
    tool_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tool_python.chmod(tool_python.stat().st_mode | stat.S_IEXEC)

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
    assert any("mammoth_cli-0.6.0-py3-none-any.whl" in line for line in install_lines)
    assert any(
        "--with" in line and "mammoth_io-0.6.0-py3-none-any.whl" in line for line in install_lines
    )
    assert not any(
        "--no-index" in line for line in install_lines
    ), f"install must stay online (no --no-index) so deps resolve from PyPI: {install_lines}"


def test_wheel_discovery_is_posix_portable_not_gnu_find() -> None:
    """Wheel discovery must not depend on ``find ... -maxdepth`` (GNU/BSD-only).

    ``-maxdepth`` is not part of POSIX ``find`` (it is a GNU/BSD extension), so
    a strictly POSIX ``sh``/``find`` combination could break on it. The
    installer discovers the just-built wheels with a POSIX shell glob instead.
    This is a portability lint: before the fix the script contained
    ``find "$wheelhouse" -maxdepth 1 ... -name 'mammoth_*.whl'`` and this
    assertion fails; after the fix the glob loop replaces it and it passes.
    """
    text = _INSTALLER_SH.read_text(encoding="utf-8")
    assert "-maxdepth" not in text, "installer must not use non-POSIX `find -maxdepth`"
    # The portable replacement globs the wheelhouse for each distribution.
    assert '"$wheelhouse"/mammoth_cli-*.whl' in text
    assert '"$wheelhouse"/mammoth_io-*.whl' in text


@pytest.mark.skipif(_SH is None, reason="POSIX sh not available")
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="the POSIX .sh --local flow defers to the .ps1 installer on Windows",
)
def test_local_source_selects_wheels_via_portable_glob(tmp_path: Path) -> None:
    """The --local path still selects the built wheels correctly without GNU find.

    Runs the real installer against the stubbed ``uv`` (same harness as above)
    and asserts the exact CLI and SDK wheels the stub dropped into the
    wheelhouse are the ones passed to ``uv tool install`` — proving the glob
    discovery picks the right artifacts, not just that ``-maxdepth`` is gone.
    """
    assert _SH is not None
    stub_dir = tmp_path / "bin"
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    log_file = tmp_path / "uv.log"
    _write_uv_stub(stub_dir, log_file, home / ".local" / "bin")
    tool_python = home / ".local" / "mammoth-cli" / "bin" / "python"
    tool_python.parent.mkdir(parents=True)
    tool_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tool_python.chmod(tool_python.stat().st_mode | stat.S_IEXEC)

    result = subprocess.run(
        [_SH, str(_INSTALLER_SH), "--local", "--cli-only"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(home)},
    )

    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    install_lines = [
        line
        for line in log_file.read_text(encoding="utf-8").splitlines()
        if line.startswith("tool install")
    ]
    assert install_lines, "expected a 'uv tool install' call"
    # The stub writes mammoth_cli-0.6.0-...whl and mammoth_io-0.6.0-...whl into
    # the wheelhouse; the glob must have selected exactly those basenames.
    assert any("mammoth_cli-0.6.0-py3-none-any.whl" in line for line in install_lines)
    assert any(
        "--with" in line and "mammoth_io-0.6.0-py3-none-any.whl" in line for line in install_lines
    )


@pytest.mark.skipif(_SH is None or _UV is None, reason="real sh and uv are required")
@pytest.mark.skipif(
    not _uv_meets_pinned_minimum(),
    reason="on-PATH uv is older than the installer's pinned minimum; the installer "
    "bootstraps its own uv rather than reusing this one",
)
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX installer test")
def test_local_source_installs_exact_local_distributions(tmp_path: Path) -> None:
    """Use real uv and inspect the isolated tool environment, including wheel origins."""
    home = tmp_path / "home"
    tool_dir = tmp_path / "tools"
    bin_dir = tmp_path / "bin"
    home.mkdir()
    env = {
        **dict(os.environ),
        "HOME": str(home),
        "UV_TOOL_DIR": str(tool_dir),
        "UV_TOOL_BIN_DIR": str(bin_dir),
        "PATH": f"{Path(_UV).parent}:/usr/bin:/bin",
    }
    result = subprocess.run(
        [_SH, str(_INSTALLER_SH), "--local", "--cli-only", "--no-modify-path"],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    python = tool_dir / "mammoth-cli" / "bin" / "python"
    code = """import importlib.metadata as m, json
for name in ('mammoth-cli', 'mammoth-io'):
 d=m.distribution(name)
 print(json.dumps([name,d.version,json.loads(d.read_text('direct_url.json'))['url']]))
"""
    records = [
        json.loads(line)
        for line in subprocess.check_output([python, "-c", code], text=True).splitlines()
    ]
    assert {record[0] for record in records} == {"mammoth-cli", "mammoth-io"}
    assert all(record[2].startswith("file://") and record[2].endswith(".whl") for record in records)
