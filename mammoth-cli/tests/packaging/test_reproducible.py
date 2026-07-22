"""PKG reproducibility: two pinned builds produce identical content.

The build is reproducible when two runs with the same ``SOURCE_DATE_EPOCH``
yield distributions whose members carry identical content. This normalizes away
the archive container's own timestamp fields (the gzip header mtime in a
``.tar.gz`` differs regardless), which are not part of the shipped content.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

CLI_ROOT = Path(__file__).resolve().parents[2]
_EPOCH = "1700000000"


def _build(out: Path) -> tuple[Path, Path]:
    poetry = shutil.which("poetry")
    if poetry is None:
        pytest.skip("poetry is not available on PATH")
    env = {**os.environ, "SOURCE_DATE_EPOCH": _EPOCH}
    result = subprocess.run(
        [poetry, "build", "--output", str(out)],
        cwd=CLI_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    if result.returncode != 0:
        pytest.fail(f"poetry build failed:\n{result.stdout}\n{result.stderr}")
    return next(out.glob("*.whl")), next(out.glob("*.tar.gz"))


def _wheel_content_hashes(wheel: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    with zipfile.ZipFile(wheel) as zf:
        for name in sorted(zf.namelist()):
            # The RECORD file embeds the other members' hashes, so it is a
            # derived artifact; comparing the members themselves is sufficient.
            if name.endswith(".dist-info/RECORD"):
                continue
            digests[name] = hashlib.sha256(zf.read(name)).hexdigest()
    return digests


def _sdist_content_hashes(sdist: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    with tarfile.open(sdist, "r:gz") as tf:
        for member in sorted(tf.getmembers(), key=lambda m: m.name):
            if not member.isfile():
                continue
            handle = tf.extractfile(member)
            assert handle is not None
            digests[member.name] = hashlib.sha256(handle.read()).hexdigest()
    return digests


def test_pkg_reproducible_content(tmp_path: Path) -> None:
    """Two SOURCE_DATE_EPOCH-pinned builds ship byte-identical members."""
    first_wheel, first_sdist = _build(tmp_path / "a")
    second_wheel, second_sdist = _build(tmp_path / "b")
    assert _wheel_content_hashes(first_wheel) == _wheel_content_hashes(second_wheel)
    assert _sdist_content_hashes(first_sdist) == _sdist_content_hashes(second_sdist)
