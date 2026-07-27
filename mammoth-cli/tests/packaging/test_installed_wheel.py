"""PKG-INSTALLED-SMOKE: the built wheel installs and actually runs.

The other PKG-* tests inspect the built artifact's contents. This one proves
the artifact *works*: it builds the CLI wheel and its mammoth-io SDK wheel,
installs them into a throwaway virtual environment (mammoth-io and mammoth-cli
resolve from the freshly built local wheelhouse; their third-party
dependencies resolve normally from the index), and runs the installed
``mammoth`` executable. Running ``schema list`` also exercises the bundled
manifest data and the runtime arg-spec derivation inside the installed package,
catching a wheel that imports but ships incomplete data.

The install step needs the package index for third-party dependencies, so the
test skips when the index is unreachable rather than failing offline.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from mammoth_cli import __version__

pytestmark = pytest.mark.subprocess

CLI_ROOT = Path(__file__).resolve().parents[2]
SDK_ROOT = CLI_ROOT.parent


def _index_reachable() -> bool:
    """Return True if the Python package index host is reachable."""
    try:
        with socket.create_connection(("pypi.org", 443), timeout=5):
            return True
    except OSError:
        return False


def _poetry_build(project_dir: Path, out_dir: Path) -> None:
    """Build ``project_dir`` with an ephemeral Poetry env, failing on error."""
    poetry = shutil.which("poetry")
    assert poetry is not None  # guarded by the fixture skip
    # `poetry build` otherwise chooses Poetry's own interpreter (often an old
    # system Python), even when pytest is running under a supported version.
    # Keep its explicit env selection under the temporary wheelhouse so this
    # test neither reads nor changes the developer's configured Poetry env.
    env = dict(os.environ)
    env["POETRY_VIRTUALENVS_PATH"] = str(out_dir / ".poetry-venvs")
    selected = subprocess.run(
        [poetry, "env", "use", sys.executable],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    if selected.returncode != 0:
        pytest.fail(
            f"could not select pytest interpreter for {project_dir}:\n"
            f"{selected.stdout}\n{selected.stderr}"
        )
    result = subprocess.run(
        [poetry, "build", "--output", str(out_dir)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    if result.returncode != 0:
        pytest.fail(f"build failed for {project_dir}:\n{result.stdout}\n{result.stderr}")


@pytest.fixture(scope="session")
def wheelhouse(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the CLI wheel and its mammoth-io SDK wheel into one wheelhouse."""
    if shutil.which("poetry") is None:
        pytest.skip("poetry is not available on PATH")
    house = tmp_path_factory.mktemp("wheelhouse")
    _poetry_build(SDK_ROOT, house)
    _poetry_build(CLI_ROOT, house)
    assert list(house.glob("mammoth_io-*.whl")), "SDK wheel was not built"
    assert list(house.glob("mammoth_cli-*.whl")), "CLI wheel was not built"
    return house


def _venv_bin(venv: Path, name: str) -> Path:
    """Return the path to an executable inside a venv, cross-platform."""
    subdir = "Scripts" if sys.platform == "win32" else "bin"
    if sys.platform == "win32" and not name.endswith(".exe"):
        name = f"{name}.exe"
    return venv / subdir / name


def _isolated_python_env() -> dict[str, str]:
    """Avoid a checkout on PYTHONPATH masking the installed wheel."""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    return env


@pytest.mark.skipif(shutil.which("poetry") is None, reason="poetry not available")
def test_installed_wheel_runs(wheelhouse: Path, tmp_path: Path) -> None:
    """The installed console script reports its version and lists its schema."""
    if not _index_reachable():
        pytest.skip("package index unreachable; cannot resolve third-party deps")
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=120)
    interpreter = _venv_bin(venv, "python")
    install = subprocess.run(
        [
            str(interpreter),
            "-m",
            "pip",
            "install",
            "--find-links",
            str(wheelhouse),
            "mammoth-cli",
        ],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=tmp_path,
        env=_isolated_python_env(),
    )
    assert install.returncode == 0, f"wheel install failed:\n{install.stdout}\n{install.stderr}"

    mammoth = _venv_bin(venv, "mammoth")
    version = subprocess.run(
        [str(mammoth), "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=tmp_path,
        env=_isolated_python_env(),
    )
    assert version.returncode == 0, version.stderr
    assert __version__ in version.stdout

    # Use the venv's interpreter rather than the test runner's executable.  In
    # particular, Windows console-script suffixes and an editable checkout on
    # sys.path must not hide a wheel that fails when imported in isolation.
    imported = subprocess.run(
        [str(interpreter), "-c", "import mammoth_cli; print(mammoth_cli.__file__)"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=tmp_path,
        env=_isolated_python_env(),
    )
    assert imported.returncode == 0, imported.stderr
    assert Path(imported.stdout.strip()).resolve().is_relative_to(venv.resolve())

    listing = subprocess.run(
        [str(mammoth), "schema", "list", "--output", "json", "--no-input"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=tmp_path,
        env=_isolated_python_env(),
    )
    assert listing.returncode == 0, listing.stderr
    envelope = json.loads(listing.stdout)
    assert envelope["data"], "schema list returned no commands from the installed wheel"
