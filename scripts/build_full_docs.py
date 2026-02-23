#!/usr/bin/env python3
"""Generate single-file documentation from mkdocs nav structure.

Reads mkdocs.yml, concatenates all doc pages in nav order, and outputs:
  - docs/full-documentation.md  (single markdown for custom site)
  - docs/llms-full.txt          (same content, .txt for LLM WebFetch)

Usage:
    python scripts/build_full_docs.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
MKDOCS_YML = ROOT / "mkdocs.yml"
OUTPUT_MD = DOCS_DIR / "full-documentation.md"
OUTPUT_TXT = DOCS_DIR / "llms-full.txt"


def load_nav(mkdocs_path: Path) -> list:
    """Load the nav list from mkdocs.yml."""
    with open(mkdocs_path) as f:
        config = yaml.safe_load(f)
    return config.get("nav", [])


def extract_pages(nav: list, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively extract (title, filepath) pairs from nav structure."""
    pages: list[tuple[str, str]] = []
    for item in nav:
        if isinstance(item, str):
            pages.append(("", item))
        elif isinstance(item, dict):
            for title, value in item.items():
                if isinstance(value, str):
                    pages.append((title, value))
                elif isinstance(value, list):
                    pages.extend(extract_pages(value, prefix=title + " > "))
    return pages


def slugify(text: str) -> str:
    """Convert heading text to anchor slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def read_doc_file(filepath: str) -> str:
    """Read a doc file and return its content."""
    full_path = DOCS_DIR / filepath
    if not full_path.exists():
        return f"<!-- File not found: {filepath} -->\n"
    return full_path.read_text(encoding="utf-8")


def extract_headings(content: str) -> list[tuple[int, str]]:
    """Extract (level, text) pairs from markdown headings."""
    headings: list[tuple[int, str]] = []
    for line in content.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)(?:\s*\{.*\})?\s*$", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((level, text))
    return headings


def build_toc(sections: list[tuple[str, str]]) -> str:
    """Build a table of contents from section titles and their headings."""
    toc_lines = ["# Table of Contents\n"]
    for section_title, content in sections:
        if not section_title:
            continue
        slug = slugify(section_title)
        toc_lines.append(f"- [{section_title}](#{slug})")
        # Add H2 and H3 subheadings
        for level, text in extract_headings(content):
            if level in (2, 3):
                indent = "  " * (level - 1)
                heading_slug = slugify(text)
                toc_lines.append(f"{indent}- [{text}](#{heading_slug})")
    return "\n".join(toc_lines) + "\n"


def strip_mkdocstrings_blocks(content: str) -> str:
    """Remove ::: mkdocstrings directives (not renderable outside MkDocs)."""
    lines = content.splitlines()
    result: list[str] = []
    skip = False
    for line in lines:
        if line.strip().startswith("::: "):
            skip = True
            result.append(f"*See API reference for `{line.strip()[4:]}`*\n")
            continue
        if skip and (line.strip() == "" or line.startswith("    ")):
            continue
        skip = False
        result.append(line)
    return "\n".join(result)


def build_full_docs() -> str:
    """Build the complete documentation markdown."""
    nav = load_nav(MKDOCS_YML)
    pages = extract_pages(nav)

    # Collect sections
    sections: list[tuple[str, str]] = []
    for title, filepath in pages:
        content = read_doc_file(filepath)
        content = strip_mkdocstrings_blocks(content)
        sections.append((title, content))

    # Build header
    header = (
        "# Mammoth Analytics Python SDK — Complete Documentation\n\n"
        "> Official Python SDK for the Mammoth Analytics platform. "
        "Build data pipelines, apply transformations, and export results from Python.\n\n"
        "> This file is auto-generated from the MkDocs source. "
        "Run `python scripts/build_full_docs.py` to regenerate.\n\n"
    )

    # Build TOC
    toc = build_toc(sections)

    # Combine all sections
    parts = [header, toc, "---\n"]
    for title, content in sections:
        if title:
            parts.append(f"\n---\n\n")
        parts.append(content.rstrip() + "\n")

    return "\n".join(parts)


def main() -> None:
    full_docs = build_full_docs()

    OUTPUT_MD.write_text(full_docs, encoding="utf-8")
    print(f"Generated {OUTPUT_MD} ({len(full_docs):,} bytes)")

    OUTPUT_TXT.write_text(full_docs, encoding="utf-8")
    print(f"Generated {OUTPUT_TXT} ({len(full_docs):,} bytes)")


if __name__ == "__main__":
    main()
