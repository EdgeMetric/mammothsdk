"""The committed capability matrix must match the server spec, manifests and SDK."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = CLI_ROOT / "scripts" / "generate_release_capability_matrix.py"


def test_release_capability_matrix_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
