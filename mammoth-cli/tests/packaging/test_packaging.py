"""PKG-* packaging acceptance tests for the built distribution.

These assert the normative packaging contract from
``docs/plans/add-cli-for-mammoth/07-packaging-install-skill.md``: a universal
pure-Python wheel that installs on Python 3.12 through 3.14, a source
distribution that carries the README, license, and bundled skill, stable
console and module entry points, the skill shipped as package data, and no
repository-local dependency URL.
"""

from __future__ import annotations

import configparser
import shutil
import subprocess
import tarfile
import zipfile
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

CLI_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class BuiltDist:
    """Locations of the freshly built wheel and source distribution."""

    directory: Path
    wheel: Path
    sdist: Path


@pytest.fixture(scope="session")
def built_dist(tmp_path_factory: pytest.TempPathFactory) -> BuiltDist:
    """Build the wheel and source distribution into an isolated directory.

    The build runs into a temporary directory so the tests never touch the
    repository ``dist/`` folder. Tests skip when Poetry is not on PATH.
    """
    poetry = shutil.which("poetry")
    if poetry is None:
        pytest.skip("poetry is not available on PATH")
    out = tmp_path_factory.mktemp("dist")
    result = subprocess.run(
        [poetry, "build", "--output", str(out)],
        cwd=CLI_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        pytest.fail(f"poetry build failed:\n{result.stdout}\n{result.stderr}")
    wheels = sorted(out.glob("*.whl"))
    sdists = sorted(out.glob("*.tar.gz"))
    assert len(wheels) == 1, f"expected one wheel, found {wheels}"
    assert len(sdists) == 1, f"expected one sdist, found {sdists}"
    return BuiltDist(directory=out, wheel=wheels[0], sdist=sdists[0])


def _wheel_metadata(wheel: Path) -> dict[str, list[str]]:
    """Return the wheel METADATA fields keyed by lowercase field name."""
    with zipfile.ZipFile(wheel) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".dist-info/METADATA"))
        raw = zf.read(name).decode("utf-8")
    message = Parser().parsestr(raw)
    fields: dict[str, list[str]] = {}
    for key, value in message.items():
        fields.setdefault(key.lower(), []).append(value)
    return fields


def _wheel_names(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as zf:
        return zf.namelist()


def _sdist_names(sdist: Path) -> list[str]:
    with tarfile.open(sdist, "r:gz") as tf:
        return tf.getnames()


@pytest.mark.parametrize("python_minor", ["3.12", "3.13", "3.14"])
def test_pkg_wheel_py31x(built_dist: BuiltDist, python_minor: str) -> None:
    """PKG-WHEEL-PY312/313/314: a universal wheel that admits each minor."""
    assert built_dist.wheel.name.endswith("-py3-none-any.whl")
    requires = _wheel_metadata(built_dist.wheel).get("requires-python", [])
    assert requires, "wheel METADATA is missing Requires-Python"
    assert ">=3.12" in requires[0]
    assert "<3.15" in requires[0]
    # The declared range must admit the parametrized minor.
    major, minor = (int(part) for part in python_minor.split("."))
    assert (major, minor) >= (3, 12)
    assert (major, minor) < (3, 15)


def test_pkg_sdist_contents(built_dist: BuiltDist) -> None:
    """PKG-SDIST-CONTENTS: README, license, and skill ride in the sdist."""
    names = _sdist_names(built_dist.sdist)
    joined = "\n".join(names)
    assert any(n.endswith("/README.md") for n in names), joined
    assert any(n.endswith("/LICENSE") for n in names), joined
    assert any(n.endswith("/pyproject.toml") for n in names), joined
    assert any(
        n.endswith("/mammoth_cli/bundled_skill/mammoth-cli/SKILL.md") for n in names
    ), joined


def test_pkg_entrypoints(built_dist: BuiltDist) -> None:
    """PKG-ENTRYPOINTS: console script and module entry point both resolve."""
    with zipfile.ZipFile(built_dist.wheel) as zf:
        entry_name = next(n for n in zf.namelist() if n.endswith(".dist-info/entry_points.txt"))
        entry_text = zf.read(entry_name).decode("utf-8")
    parser = configparser.ConfigParser()
    parser.read_string(entry_text)
    assert parser.has_section("console_scripts")
    assert parser["console_scripts"]["mammoth"] == "mammoth_cli.__main__:main"
    # The module entry point (`python -m mammoth_cli`) requires __main__.py.
    assert "mammoth_cli/__main__.py" in _wheel_names(built_dist.wheel)


def test_pkg_skill_data(built_dist: BuiltDist) -> None:
    """PKG-SKILL-DATA: the canonical skill ships as wheel package data."""
    names = _wheel_names(built_dist.wheel)
    assert "mammoth_cli/bundled_skill/mammoth-cli/SKILL.md" in names
    references = [n for n in names if "/bundled_skill/mammoth-cli/references/" in n]
    assert references, "bundled skill references are missing from the wheel"


def test_pkg_no_local_url(built_dist: BuiltDist) -> None:
    """PKG-NO-LOCAL-URL: no dependency resolves to a repository-local path."""
    requires_dist = _wheel_metadata(built_dist.wheel).get("requires-dist", [])
    assert any("mammoth-io" in dep for dep in requires_dist), requires_dist
    forbidden = ("file://", "@ file", " @ .", "path=", "../", "./")
    for dep in requires_dist:
        for token in forbidden:
            assert token not in dep, f"local dependency URL in {dep!r}"
