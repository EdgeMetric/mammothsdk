"""Unit tests for the STE sentence-length checker."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_STE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_ste.py"
_spec = importlib.util.spec_from_file_location("mammoth_cli_check_ste", _STE_PATH)
assert _spec is not None and _spec.loader is not None
check_ste = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = check_ste
_spec.loader.exec_module(check_ste)


def test_short_descriptive_sentence_passes() -> None:
    assert check_ste.check_text("The CLI returns a stable envelope.", "x.md") == []


def test_long_descriptive_sentence_flagged() -> None:
    text = "The command " + " ".join(["word"] * 30) + " ends here."
    violations = check_ste.check_text(text, "x.md")
    assert len(violations) == 1
    assert violations[0].kind == "descriptive"
    assert violations[0].limit == 25


def test_procedural_step_uses_stricter_limit() -> None:
    # 22 words: within the 25 descriptive limit but over the 20 procedural one.
    step = "- Run the command with " + " ".join(["flag"] * 18) + " now."
    violations = check_ste.check_text(step, "x.md")
    assert len(violations) == 1
    assert violations[0].kind == "procedural"
    assert violations[0].limit == 20


def test_imperative_sentence_is_procedural() -> None:
    sentence = "Pass the option and " + " ".join(["value"] * 18) + " here."
    violations = check_ste.check_text(sentence, "x.md")
    assert violations and violations[0].kind == "procedural"


def test_code_fence_is_ignored() -> None:
    text = "```\n" + " ".join(["token"] * 40) + "\n```\n"
    assert check_ste.check_text(text, "x.md") == []


def test_inline_code_and_urls_do_not_count() -> None:
    text = "Run `mammoth a b c d e f g h i j k l m n o p q r s t` to see https://example.com/very/long/path/here."
    assert check_ste.check_text(text, "x.md") == []


def test_headings_and_table_rows_skipped() -> None:
    text = "# " + " ".join(["h"] * 40) + "\n| " + " ".join(["c"] * 40) + " |\n"
    assert check_ste.check_text(text, "x.md") == []


def test_committed_docs_pass() -> None:
    docs = sorted((Path(__file__).resolve().parents[2] / "docs").glob("*.md"))
    assert docs, "expected guide docs to exist"
    assert check_ste.check_paths(docs) == []
