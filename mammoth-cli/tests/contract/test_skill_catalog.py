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


def test_fail_closed_patch_commands_are_discoverable_but_not_presented_as_runnable() -> None:
    catalog = (SKILL / "references" / "commands" / "dataset.md").read_text(encoding="utf-8")
    catalog += (SKILL / "references" / "commands" / "view.md").read_text(encoding="utf-8")
    for command_id in ("dataset.update", "view.update"):
        section = catalog.split(f"### `{command_id}`", 1)[1].split("\n### `", 1)[0]
        assert "mammoth schema get" in section
        assert "Discovery only" in section
        assert "unsupported_contract" in section
        assert "Expected success:" not in section
        assert "Runnable only" not in section


def _section(family: str, command_id: str) -> str:
    catalog = (SKILL / "references" / "commands" / f"{family}.md").read_text(encoding="utf-8")
    return catalog.split(f"### `{command_id}`", 1)[1].split("\n### `", 1)[0]


def test_every_entry_carries_a_release_status_joined_from_the_matrix() -> None:
    catalog = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SKILL / "references" / "commands").glob("*.md")
    )
    entries = catalog.count("\n### `")
    assert entries == sum(1 for _ in load_commands())
    # Fail-closed patch routes explain themselves instead; every other entry
    # says ran once / untried / not supported.
    fail_closed = catalog.count("Discovery only")
    assert (
        catalog.count("Status on release:") + catalog.count("Do not run:") == entries - fail_closed
    )

    assert "ran once on CLI" in _section("view", "view.data.get")
    assert "untried" in _section("view", "view.transform.unnest")
    assert "through `view.task.add`" in _section("view", "view.transform.filter")
    unsupported = _section("dashboard", "dashboard.create")
    assert unsupported.startswith("\n\nRun:") and "Do not run:" in unsupported
    assert "Result:" not in unsupported
