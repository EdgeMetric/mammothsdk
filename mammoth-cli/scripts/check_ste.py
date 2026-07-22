"""Sentence-length checks that Vale cannot classify on its own.

The Mammoth STE house profile caps a *procedural* sentence (a numbered or
bulleted instruction, or one starting with an imperative verb) at 20 words and a
*descriptive* sentence at 25 words. Vale's ``occurrence`` rule enforces one flat
limit; this checker tells the two apart and applies the stricter procedural
limit only to instruction sentences.

Fenced code blocks, inline code spans, URLs, and table rows are excluded, so
command lines and JSON keys never count against a limit. Run over Markdown
files: ``python scripts/check_ste.py docs/*.md`` (``--json`` for machine output).
Exit status is non-zero when any sentence exceeds its limit.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PROCEDURAL_LIMIT = 20
DESCRIPTIVE_LIMIT = 25

_CODE_FENCE = re.compile(r"(?s)```.*?```")
_INLINE_CODE = re.compile(r"`[^`]*`")
_URL = re.compile(r"https?://\S+")
_WORD = re.compile(r"\b[\w'-]+\b")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_IMPERATIVE = re.compile(
    r"^(?:run|pass|use|set|call|read|check|store|log|list|get|create|delete|"
    r"install|update|remove|add|open|close|verify|wait|export|import|copy|move|"
    r"pick|choose|provide|give|do|never|always|avoid|keep|branch|point)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Violation:
    """One over-limit sentence."""

    file: str
    line: int
    words: int
    limit: int
    kind: str
    text: str


def _strip_noise(text: str) -> str:
    text = _CODE_FENCE.sub(" ", text)
    text = _INLINE_CODE.sub(" ", text)
    return _URL.sub(" ", text)


def _is_procedural(raw_line: str, sentence: str) -> bool:
    stripped = raw_line.lstrip()
    if re.match(r"^(?:[-*]|\d+\.)\s", stripped):
        return True
    return bool(_IMPERATIVE.match(sentence.strip()))


def check_text(text: str, filename: str) -> list[Violation]:
    """Return the STE sentence-length violations in ``text``.

    Args:
        text: The Markdown (or plain-text) content to check.
        filename: The name to record on each violation.

    Returns:
        A list of :class:`Violation`, one per over-limit sentence.
    """
    violations: list[Violation] = []
    in_fence = False
    for number, raw_line in enumerate(text.splitlines(), start=1):
        if raw_line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = raw_line.strip()
        if not line or line.startswith(("#", "|", ">")) or line.startswith("---"):
            continue
        clean = _strip_noise(line)
        for sentence in _SENTENCE_SPLIT.split(clean):
            words = len(_WORD.findall(sentence))
            if words == 0:
                continue
            procedural = _is_procedural(raw_line, sentence)
            limit = PROCEDURAL_LIMIT if procedural else DESCRIPTIVE_LIMIT
            if words > limit:
                violations.append(
                    Violation(
                        file=filename,
                        line=number,
                        words=words,
                        limit=limit,
                        kind="procedural" if procedural else "descriptive",
                        text=sentence.strip()[:120],
                    )
                )
    return violations


def check_paths(paths: list[Path]) -> list[Violation]:
    """Check every given file and return all violations."""
    violations: list[Violation] = []
    for path in paths:
        violations.extend(check_text(path.read_text(encoding="utf-8"), str(path)))
    return violations


def main(argv: list[str] | None = None) -> int:
    """Check the given Markdown files; exit non-zero on any violation."""
    args = argv if argv is not None else sys.argv[1:]
    as_json = "--json" in args
    paths = [Path(a) for a in args if not a.startswith("--")]
    violations = check_paths(paths)
    if as_json:
        print(json.dumps([asdict(v) for v in violations], indent=1, sort_keys=True))
    else:
        for v in violations:
            print(f"{v.file}:{v.line}: {v.kind} sentence has {v.words} words "
                  f"(limit {v.limit}): {v.text}")
    return 1 if violations else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
