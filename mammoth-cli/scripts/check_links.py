"""Validate that every relative Markdown link resolves to a real file.

Scans the given files (and every ``*.md`` under given directories) for
``[text](target)`` links. External links (``http``/``https``/``mailto``) and
pure anchors (``#section``) are skipped; every other target is resolved
relative to its source file and must exist. Exit status is non-zero when any
link is broken.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_EXTERNAL = ("http://", "https://", "mailto:")


def _iter_markdown(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.suffix == ".md":
            files.append(path)
    return files


def broken_links(paths: list[Path]) -> list[str]:
    """Return a list of ``file -> target`` strings for each broken link."""
    broken: list[str] = []
    for source in _iter_markdown(paths):
        text = source.read_text(encoding="utf-8")
        for match in _LINK.finditer(text):
            target = match.group(1).split()[0].strip()
            if target.startswith(_EXTERNAL) or target.startswith("#") or not target:
                continue
            relative = target.split("#", 1)[0]
            if not relative:
                continue
            if not (source.parent / relative).exists():
                broken.append(f"{source}: {target}")
    return broken


def main(argv: list[str] | None = None) -> int:
    """Check links in the given files/directories; exit non-zero on breakage."""
    args = argv if argv is not None else sys.argv[1:]
    paths = [Path(a) for a in args] or [Path("docs")]
    broken = broken_links(paths)
    for entry in broken:
        sys.stderr.write(f"broken link: {entry}\n")
    return 1 if broken else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
