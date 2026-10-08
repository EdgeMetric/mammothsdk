"""The bundled skill is text an agent obeys; keep it free of steering tricks.

Checked on every run: no invisible or direction-changing characters, no
prompt-injection phrasing, no shell-pipe installs, and outbound links only to
Mammoth's own hosts or documentation example domains.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "mammoth_cli" / "bundled_skill" / "mammoth-cli"
FILES = sorted(p for p in SKILL_DIR.rglob("*") if p.is_file())

_INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤﻿­]")
_INJECTION = re.compile(
    r"ignore (all|any|previous|prior|the above)|disregard (all|any|previous|prior|the above)"
    r"|you are now|new instructions|system prompt|do not tell the user|without telling"
    r"|paste (the|your) (key|secret|token)|send (the|your) (key|secret|token|credentials)"
    r"|(curl|wget) [^\n|]*\|\s*(ba|z)?sh\b",
    re.IGNORECASE,
)
_URL = re.compile(r"https?://([^/\s)>`'\"]+)")
_ALLOWED_HOSTS = re.compile(r"(\.|^)(mammoth\.io|example\.(com|org|net)|api\.example)$")
# Lines that state the rule itself ("Do not ask the operator to paste the key").
_NEGATED = re.compile(r"\b(never|do not|don't|not)\b", re.IGNORECASE)


def test_bundled_skill_exists_and_is_nontrivial() -> None:
    assert (SKILL_DIR / "SKILL.md").is_file()
    assert len(FILES) > 20


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(SKILL_DIR)))
def test_no_invisible_or_bidi_characters(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    hit = _INVISIBLE.search(text)
    assert hit is None, f"{path.name}: U+{ord(hit.group()):04X} at offset {hit.start()}"


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(SKILL_DIR)))
def test_no_prompt_injection_phrasing(path: Path) -> None:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if _INJECTION.search(line) and not _NEGATED.search(line):
            pytest.fail(f"{path.name}:{number}: {line.strip()[:120]}")


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(SKILL_DIR)))
def test_links_only_to_known_hosts(path: Path) -> None:
    hosts = {m.group(1).lower() for m in _URL.finditer(path.read_text(encoding="utf-8"))}
    unknown = sorted(h for h in hosts if not _ALLOWED_HOSTS.search(h))
    assert unknown == [], f"{path.name}: {unknown}"


_EXPORT_DATASET_INPUT = re.compile(r"view export dataset[^`']*?--input '(\{[^']*\})'")


def test_new_dataset_examples_do_not_invent_a_dataset_name() -> None:
    """ISS-195: an example that makes a NEW dataset must omit dataset_name (the app's
    default is "Result Dataset"); only an append to an existing dataset names it."""
    offenders = [
        f"{path.relative_to(SKILL_DIR)}: {body}"
        for path in FILES
        if path.suffix == ".md"
        for body in _EXPORT_DATASET_INPUT.findall(path.read_text(encoding="utf-8"))
        if '"dataset_name"' in body and "target_ds_id" not in body
    ]
    assert not offenders, offenders
