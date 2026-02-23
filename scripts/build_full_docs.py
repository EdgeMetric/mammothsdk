#!/usr/bin/env python3
"""Generate single-file documentation from mkdocs nav structure.

Reads mkdocs.yml, concatenates all doc pages in nav order, rewrites
cross-file links to same-document anchors, converts MkDocs admonitions
to blockquotes, and outputs:
  - docs/full-documentation.md  (single markdown with working links)
  - docs/llms-full.txt          (same content, .txt for LLM WebFetch)

Usage:
    python scripts/build_full_docs.py
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
MKDOCS_YML = ROOT / "mkdocs.yml"
OUTPUT_MD = DOCS_DIR / "full-documentation.md"
OUTPUT_TXT = DOCS_DIR / "llms-full.txt"


# ---------------------------------------------------------------------------
# Nav helpers
# ---------------------------------------------------------------------------

def load_nav(mkdocs_path: Path) -> list:
    """Load the nav list from mkdocs.yml."""
    with open(mkdocs_path) as f:
        config = yaml.safe_load(f)
    return config.get("nav", [])


def extract_pages(nav: list) -> list[tuple[str, str]]:
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
                    pages.extend(extract_pages(value))
    return pages


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert heading text to GitHub-compatible anchor slug."""
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
        m = re.match(r"^(#{1,6})\s+(.+?)(?:\s*\{.*\})?\s*$", line)
        if m:
            headings.append((len(m.group(1)), m.group(2).strip()))
    return headings


def first_heading_slug(content: str) -> str | None:
    """Return the anchor slug of the first heading in *content*."""
    headings = extract_headings(content)
    return slugify(headings[0][1]) if headings else None


# ---------------------------------------------------------------------------
# Anchor map: filepath -> first-heading anchor
# ---------------------------------------------------------------------------

def build_anchor_map(pages: list[tuple[str, str]]) -> dict[str, str]:
    """Build mapping of docs-relative filepath -> first-heading anchor slug.

    Example: {"api/client.md": "client-api-reference", "installation.md": "installation"}
    """
    anchor_map: dict[str, str] = {}
    for _title, filepath in pages:
        content = read_doc_file(filepath)
        slug = first_heading_slug(content)
        if slug:
            anchor_map[filepath] = slug
    return anchor_map


# ---------------------------------------------------------------------------
# Build heading anchor inventory (all headings in combined doc)
# ---------------------------------------------------------------------------

def build_all_anchors(sections: list[tuple[str, str, str]]) -> set[str]:
    """Collect every heading anchor that will exist in the combined doc."""
    anchors: set[str] = set()
    for _title, _filepath, content in sections:
        for _level, text in extract_headings(content):
            anchors.add(slugify(text))
    return anchors


# ---------------------------------------------------------------------------
# Link rewriting
# ---------------------------------------------------------------------------

_MD_LINK = re.compile(
    r"""
    (?<!!)\[           # opening [ (not preceded by ! for images)
    ([^\]]+)           # link text
    \]\(               # ](
    ([^)]+)            # href
    \)                 # )
    """,
    re.VERBOSE,
)


def resolve_relative_path(source_file: str, href: str) -> str:
    """Resolve a relative href against the directory of source_file.

    E.g. source="api/views.md", href="../quick-start.md" -> "quick-start.md"
         source="api/views.md", href="client.md"         -> "api/client.md"
    """
    source_dir = PurePosixPath(source_file).parent
    resolved = (source_dir / href).as_posix()
    # Normalize away ".." segments
    parts: list[str] = []
    for part in resolved.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return "/".join(parts)


def rewrite_links(
    content: str,
    source_file: str,
    anchor_map: dict[str, str],
    all_anchors: set[str],
) -> str:
    """Rewrite cross-file .md links to same-document #anchor links."""

    def _replace(m: re.Match) -> str:
        text = m.group(1)
        href = m.group(2).strip()

        # Already an anchor link or external URL — leave as-is
        if href.startswith("#") or href.startswith("http://") or href.startswith("https://"):
            return m.group(0)

        # Split href into file path and optional fragment
        if "#" in href:
            file_part, fragment = href.split("#", 1)
        else:
            file_part, fragment = href, ""

        # Only rewrite .md links
        if not file_part.endswith(".md"):
            return m.group(0)

        # Resolve relative path to docs-relative
        resolved = resolve_relative_path(source_file, file_part)

        # If the link has an explicit fragment, use it (it should exist as
        # a heading anchor in the combined doc)
        if fragment:
            # Verify anchor exists; if not, fall back to file's H1 anchor
            if fragment in all_anchors:
                return f"[{text}](#{fragment})"
            # Try the file's H1 as fallback
            file_anchor = anchor_map.get(resolved, "")
            if file_anchor:
                return f"[{text}](#{file_anchor})"
            return f"[{text}](#{fragment})"

        # No fragment — link to the file's first heading
        file_anchor = anchor_map.get(resolved, "")
        if file_anchor:
            return f"[{text}](#{file_anchor})"

        # Unknown target — leave as-is
        return m.group(0)

    return _MD_LINK.sub(_replace, content)


# ---------------------------------------------------------------------------
# MkDocs extensions → portable markdown
# ---------------------------------------------------------------------------

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


_ADMONITION_RE = re.compile(r"^(!{3})\s+(\w+)\s*(?:\"([^\"]*)\")?\s*$")


def convert_admonitions(content: str) -> str:
    """Convert MkDocs admonitions (``!!! type "title"``) to blockquotes.

    Input::

        !!! note "Title"
            First line.
            Second line.

    Output::

        > **Note:** Title
        >
        > First line.
        > Second line.
    """
    lines = content.splitlines()
    result: list[str] = []
    i = 0
    while i < len(lines):
        m = _ADMONITION_RE.match(lines[i])
        if m:
            kind = m.group(2).capitalize()  # note -> Note, tip -> Tip
            title = m.group(3) or ""
            if title:
                result.append(f"> **{kind}:** {title}")
            else:
                result.append(f"> **{kind}**")
            result.append(">")
            i += 1
            # Collect indented body lines (4 spaces)
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
                body = lines[i]
                if body.strip() == "":
                    result.append(">")
                else:
                    result.append(f"> {body[4:]}")  # strip 4-space indent
                i += 1
            result.append("")  # blank line after blockquote
        else:
            result.append(lines[i])
            i += 1
    return "\n".join(result)


# ---------------------------------------------------------------------------
# TOC builder
# ---------------------------------------------------------------------------

def build_toc(sections: list[tuple[str, str, str]]) -> str:
    """Build a table of contents from section titles and their headings."""
    toc_lines = ["# Table of Contents\n"]
    for section_title, _filepath, content in sections:
        if not section_title:
            continue
        slug = slugify(section_title)
        toc_lines.append(f"- [{section_title}](#{slug})")
        for level, text in extract_headings(content):
            if level in (2, 3):
                indent = "  " * (level - 1)
                toc_lines.append(f"{indent}- [{text}](#{slugify(text)})")
    return "\n".join(toc_lines) + "\n"


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_full_docs() -> str:
    """Build the complete documentation markdown."""
    nav = load_nav(MKDOCS_YML)
    pages = extract_pages(nav)

    # Phase 1: read all files, build anchor map
    anchor_map = build_anchor_map(pages)

    # Phase 2: read + pre-process all sections
    sections: list[tuple[str, str, str]] = []  # (title, filepath, content)
    for title, filepath in pages:
        content = read_doc_file(filepath)
        content = strip_mkdocstrings_blocks(content)
        content = convert_admonitions(content)
        sections.append((title, filepath, content))

    # Phase 3: collect every heading anchor in the combined doc
    all_anchors = build_all_anchors(sections)

    # Phase 4: rewrite links now that we know all anchors
    processed: list[tuple[str, str]] = []
    for title, filepath, content in sections:
        content = rewrite_links(content, filepath, anchor_map, all_anchors)
        processed.append((title, content))

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
    for title, content in processed:
        if title:
            parts.append("\n---\n\n")
        parts.append(content.rstrip() + "\n")

    return "\n".join(parts)


def main() -> None:
    full_docs = build_full_docs()

    OUTPUT_MD.write_text(full_docs, encoding="utf-8")
    print(f"Generated {OUTPUT_MD} ({len(full_docs):,} bytes)")

    OUTPUT_TXT.write_text(full_docs, encoding="utf-8")
    print(f"Generated {OUTPUT_TXT} ({len(full_docs):,} bytes)")

    # Print link rewriting stats
    nav = load_nav(MKDOCS_YML)
    pages = extract_pages(nav)
    anchor_map = build_anchor_map(pages)
    print(f"Anchor map: {len(anchor_map)} files mapped to anchors")

    # Count rewritten links in output
    anchor_links = len(re.findall(r"\]\(#[^)]+\)", full_docs))
    remaining_md = len(re.findall(r"\]\([^)#]*\.md[^)]*\)", full_docs))
    print(f"Anchor links in output: {anchor_links}")
    if remaining_md:
        print(f"WARNING: {remaining_md} .md file links were NOT rewritten:")
        for m in re.finditer(r"\[([^\]]+)\]\(([^)#]*\.md[^)]*)\)", full_docs):
            print(f"  [{m.group(1)}]({m.group(2)})")


if __name__ == "__main__":
    main()
