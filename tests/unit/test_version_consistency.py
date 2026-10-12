"""The version a built wheel reports must be the version pyproject.toml publishes."""

import tomllib
from pathlib import Path

import mammoth


def test_dunder_version_matches_pyproject() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert mammoth.__version__ == declared
