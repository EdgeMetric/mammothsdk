#!/usr/bin/env python3
"""Report the documented status of public SDK client-facing methods.

This is deliberately an inventory, not a completeness assertion.  It scans
the public client classes declared in ``mammoth/client.py`` and ``mammoth/api``
and records an owning MkDocs source page or a concrete ``no_owner_page`` gap.
It does not claim that any per-method rendered anchor exists or is visible.
The stable JSON output is suitable for CI diffs.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def _public_classes(path: Path) -> list[tuple[str, str, list[str]]]:
    """Return declared public client/API classes and their declared methods."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module = _module_name(path)
    classes: list[tuple[str, str, list[str]]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
            continue
        if path.name != "client.py" and not node.name.endswith("API"):
            continue
        methods = sorted(
            child.name
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not child.name.startswith("_")
        )
        classes.append((module, node.name, methods))
    return classes


def _owner_pages() -> dict[str, str]:
    pages: dict[str, str] = {}
    for page in sorted((DOCS / "api").glob("*.md")):
        for line in page.read_text(encoding="utf-8").splitlines():
            if line.startswith("::: mammoth."):
                symbol = line.removeprefix("::: ").strip()
                pages[symbol] = page.relative_to(DOCS).as_posix()
    return pages


def inventory() -> dict[str, Any]:
    """Build one deterministic, gap-preserving documentation inventory."""
    sources = [ROOT / "mammoth" / "client.py", *sorted((ROOT / "mammoth" / "api").glob("*.py"))]
    owner_pages = _owner_pages()
    entries: list[dict[str, str | bool | None]] = []
    for source in sources:
        for module, class_name, methods in _public_classes(source):
            class_symbol = f"{module}.{class_name}"
            owner_page = owner_pages.get(class_symbol)
            for method in methods:
                entries.append(
                    {
                        "symbol": f"{class_symbol}.{method}",
                        "owner_page": owner_page,
                        "owner_page_mapped": owner_page is not None,
                        # Mkdocstrings can filter members and change rendered
                        # ids. This source scan deliberately does not pretend
                        # it has checked individual rendered method anchors.
                        "rendered_method_anchor_verified": False,
                        "gap": "no_owner_page" if owner_page is None else None,
                    }
                )
    entries.sort(key=lambda entry: str(entry["symbol"]))
    owner_page_mapped = sum(entry["owner_page_mapped"] is True for entry in entries)
    return {
        "inventory_version": 1,
        "denominator": len(entries),
        "owner_page_mapped": owner_page_mapped,
        "owner_page_gaps": len(entries) - owner_page_mapped,
        "rendered_method_anchor_verified": 0,
        "rendered_method_anchor_unassessed": len(entries),
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout.")
    args = parser.parse_args()
    rendered = json.dumps(inventory(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
