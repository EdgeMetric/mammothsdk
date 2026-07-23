"""The shared release SemVer validator must accept only strict SemVer.

``scripts/validate_semver.sh`` is the single source of truth for the version
check performed by all three tag-triggered release workflows (sdk-release.yml,
cli-release.yml, publish.yml). This test drives the real script over a table of
valid and invalid version strings and asserts its exit code, so the three
workflows cannot silently disagree about what a legal version is.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_CLI_ROOT = Path(__file__).resolve().parents[2]
_VALIDATOR = _CLI_ROOT / "scripts" / "validate_semver.sh"
_BASH = shutil.which("bash")

# Strict SemVer: MAJOR.MINOR.PATCH with optional -prerelease and +build.
_VALID = [
    "1.2.3",
    "1.0.0",
    "0.0.0",
    "10.20.30",
    "1.2.3-rc.1",
    "1.2.3-alpha",
    "1.2.3+build",
    "1.2.3-rc.1+build.5",
    "1.0.0-0",  # numeric prerelease identifier of a single zero is legal
    "1.2.3-0.3.7",  # multiple numeric prerelease identifiers, none zero-padded
    "1.2.3-x.7.z.92",  # mixed alnum prerelease identifiers
    "1.2.3+00A1",  # leading zeros ARE allowed in build metadata
]

_INVALID = [
    "1.2",  # missing PATCH
    "1.2.3.4",  # extra component
    "v1.2.3",  # tag prefix not stripped
    "1.2.3rc1",  # prerelease without the leading dash
    "",  # empty
    ".1.2",  # leading empty component
    "1..2",  # empty middle component
    "1.2.",  # trailing empty component
    "1.2.x",  # non-numeric PATCH
    "01.2.3",  # leading zero in MAJOR
    "1.02.3",  # leading zero in MINOR
    "1.2.03",  # leading zero in PATCH
    "1.2.3-01",  # leading zero in a numeric prerelease identifier
    "1.2.3-alpha..1",  # empty prerelease identifier between dots
    "1.2.3-..",  # empty prerelease identifiers
    "1.2.3-",  # empty prerelease
    "1.2.3+",  # empty build metadata
]


def _run(version: str) -> subprocess.CompletedProcess[str]:
    assert _BASH is not None
    return subprocess.run(
        [_BASH, str(_VALIDATOR), version],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_validator_is_executable() -> None:
    assert _VALIDATOR.is_file(), "validate_semver.sh must exist"


@pytest.mark.skipif(_BASH is None, reason="bash not available")
@pytest.mark.parametrize("version", _VALID)
def test_valid_versions_are_accepted(version: str) -> None:
    result = _run(version)
    assert result.returncode == 0, f"'{version}' rejected: {result.stdout!r} {result.stderr!r}"


@pytest.mark.skipif(_BASH is None, reason="bash not available")
@pytest.mark.parametrize("version", _INVALID)
def test_invalid_versions_are_rejected(version: str) -> None:
    result = _run(version)
    assert result.returncode != 0, f"'{version}' was accepted but should be rejected"
    # The failure must carry a GitHub Actions error annotation.
    assert "::error::" in (result.stdout + result.stderr)


@pytest.mark.skipif(_BASH is None, reason="bash not available")
def test_missing_argument_is_rejected() -> None:
    assert _BASH is not None
    result = subprocess.run(
        [_BASH, str(_VALIDATOR)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "::error::" in (result.stdout + result.stderr)
