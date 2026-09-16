"""Keep the CLI runtime and distribution versions in lockstep."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from mammoth_cli import __version__

_ROOT = Path(__file__).resolve().parents[2]
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def test_cli_runtime_version_matches_distribution_metadata() -> None:
    """The wheel metadata and imported package must advertise one version."""
    project = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = project["tool"]["poetry"]["version"]
    assert declared == __version__
    assert _SEMVER.fullmatch(declared)
