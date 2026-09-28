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
    for family, command_id in (("dataset", "dataset.update"), ("view", "view.update")):
        section = _section(family, command_id)
        assert "mammoth schema get" in section
        assert "Discovery only" in section
        assert "unsupported_contract" in section
        assert "Expected success:" not in section
        assert "Runnable only" not in section


#: An agent's skill-reference reader refuses a file over this many bytes; a
#: shipped reference that exceeds it is unreadable, not just large.
_MAX_REFERENCE_BYTES = 65536


def _section(family: str, command_id: str) -> str:
    """Find one command's entry among a family's file and its split shards."""
    commands_dir = SKILL / "references" / "commands"
    paths = [commands_dir / f"{family}.md"] + sorted(commands_dir.glob(f"{family}-*.md"))
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if f"### `{command_id}`" in text:
            return text.split(f"### `{command_id}`", 1)[1].split("\n### `", 1)[0]
    raise AssertionError(f"{command_id!r} not found under family {family!r}")


def test_every_shipped_reference_file_is_under_the_agent_read_cap() -> None:
    for path in SKILL.rglob("*.md"):
        assert (
            len(path.read_bytes()) < _MAX_REFERENCE_BYTES
        ), f"{path.relative_to(SKILL)} is over the {_MAX_REFERENCE_BYTES}-byte agent read cap"


#: SKILL.md, unlike references/*.md, ships inside the in-product system
#: prompt's own fixed token budget -- it is not read on demand. At mammoth-cli
#: 2.0.49 the prompt measured 11,867 of a 12,000-token cap with everything
#: else already trimmed; SKILL.md was 13,672 bytes. New guidance belongs in
#: references/ or in command hints/schemas (loaded on demand) instead of
#: growing this file, so the cap is enforced at its 2.0.49 size rather than
#: the much looser per-reference-file byte cap above.
_MAX_SKILL_MD_BYTES = 13672


def test_skill_md_does_not_grow_past_its_system_prompt_budget() -> None:
    size = len((SKILL / "SKILL.md").read_bytes())
    assert size <= _MAX_SKILL_MD_BYTES, (
        f"SKILL.md is {size} bytes, over its {_MAX_SKILL_MD_BYTES}-byte budget. It ships "
        "inside the in-product system prompt's fixed token cap, which is already spent "
        "down to fit -- put new guidance in references/ or in command hints/schemas "
        "instead, which load on demand."
    )


#: Measured with ``wc -w`` on the bullet as it read before it was rescoped for
#: shell vs. embedded use (mammoth-cli 2.0.75): "A command whose schema lists
#: `secret_fields` takes `--input FILE` (mode 0600); secrets never go in
#: argv, notes, checkpoints or replies." Rescoping it must not grow it -- it
#: ships inside SKILL.md's own fixed token budget (see the byte-cap test
#: above).
_SECRET_FIELDS_BULLET_WORD_BUDGET = 21


def _bullet_containing(text: str, needle: str) -> str:
    """The single markdown bullet (its wrapped continuation lines included)
    that contains ``needle``, from its leading ``- `` to the next bullet,
    blank line, or heading.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("- ") and needle in line:
            bullet_lines = [line]
            for later in lines[index + 1 :]:
                if later.startswith("  ") and not later.lstrip().startswith("- "):
                    bullet_lines.append(later)
                else:
                    break
            return "\n".join(bullet_lines)
    raise AssertionError(f"no bullet containing {needle!r} found")


def test_secret_fields_bullet_is_scoped_for_shell_and_embedded_without_growing() -> None:
    """A password/token the user gives for their own destination is used in
    the command behind the confirmation card when the CLI runs embedded
    (no shell, no file system) -- the bullet must say so, not just describe
    the shell-only `--input FILE` path, and must not grow past its original
    word count since it ships inside SKILL.md's fixed token budget.
    """
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    bullet = _bullet_containing(text, "secret_fields")
    word_count = len(bullet.split())
    assert word_count <= _SECRET_FIELDS_BULLET_WORD_BUDGET, (
        f"secret_fields bullet is {word_count} words, was "
        f"{_SECRET_FIELDS_BULLET_WORD_BUDGET}: {bullet!r}"
    )
    assert "0600" in bullet
    assert "embedded" in bullet.casefold()
    assert "run log" in bullet.casefold()


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
    unsupported = _section("dashboard", "dashboard.pdf.export")
    assert unsupported.startswith("\n\nRun:") and "Do not run:" in unsupported
    assert "Result:" not in unsupported
