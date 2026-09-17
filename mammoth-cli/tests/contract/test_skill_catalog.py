from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mammoth_cli.manifest.loader import load_commands

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts" / "build_skill_catalog.py"
SKILL = ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli"


def test_packaged_skill_catalog_is_manifest_complete_and_current() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"], cwd=ROOT, text=True, capture_output=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    command_files = (SKILL / "references" / "commands").glob("*.md")
    catalog = "\n".join(path.read_text(encoding="utf-8") for path in command_files)
    for command in load_commands():
        assert f"### `{command['command_id']}`" in catalog
