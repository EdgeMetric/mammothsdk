"""Generate the deterministic CLI documentation corpus from the manifests.

Produces three files under ``mammoth-cli/docs/``:

* ``reference/commands.md`` — the complete command reference, grouped by family.
* ``llms.txt`` — a compact index of the guides, command families, and skill.
* ``llms-full.txt`` — the full agent-readable reference (every command with its
  mutation class, confirmation policy, backing SDK symbol, and examples).

Output is fully deterministic (sorted, no timestamps) so a regeneration diff can
fail CI. Run from the ``mammoth-cli`` directory: ``python scripts/gen_docs.py``.
A ``--check`` flag regenerates into memory and exits non-zero on any drift.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mammoth_cli import __version__  # noqa: E402
from mammoth_cli.manifest.loader import load_commands  # noqa: E402

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
REPO_URL = "https://github.com/EdgeMetric/mm-pysdk"

GUIDES = [
    ("installation.md", "Install the CLI and the agent skill."),
    ("quickstart.md", "Authenticate and run your first commands in five minutes."),
    ("authentication.md", "Credentials, profiles, server prefixes, and project context."),
    ("agents.md", "Deterministic output, promptless mode, and CI patterns for agents."),
    ("safety.md", "Confirmation policies and safe mutation."),
    ("troubleshooting.md", "Exit codes, error envelopes, and recovery."),
    ("upgrade.md", "Update the CLI and skill."),
    ("uninstall.md", "Remove the CLI, skill, and configuration."),
]


def _families() -> dict[str, list[dict[str, object]]]:
    families: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        families[record["command_path"].split()[0]].append(record)
    for records in families.values():
        records.sort(key=lambda r: str(r["command_path"]))
    return dict(sorted(families.items()))


def _command_block(record: dict[str, object]) -> list[str]:
    return [
        f"### `mammoth {record['command_path']}`",
        "",
        f"- Mutation class: `{record['mutation_class']}`",
        f"- Confirmation: `{record['confirmation']}`",
        f"- Backing SDK: `{record['sdk_symbol']}`",
        f"- Agent example: `{record['agent_example']}`",
        "",
    ]


def render_commands_md(families: dict[str, list[dict[str, object]]]) -> str:
    lines = [
        "# Command reference",
        "",
        f"Generated from the reviewed command manifests for mammoth-cli {__version__}.",
        "Do not edit by hand; run `python scripts/gen_docs.py`.",
        "",
        f"Total commands: {sum(len(v) for v in families.values())}.",
        "",
    ]
    for family, records in families.items():
        lines.append(f"## {family}")
        lines.append("")
        for record in records:
            lines.extend(_command_block(record))
    return "\n".join(lines).rstrip() + "\n"


def render_llms_txt(families: dict[str, list[dict[str, object]]]) -> str:
    lines = [
        "# mammoth-cli",
        "",
        "> Command-line interface for the Mammoth Analytics platform, built for "
        "autonomous agents: deterministic JSON output, promptless mode, and stable "
        "error envelopes.",
        "",
        "## Guides",
        "",
    ]
    for name, summary in GUIDES:
        lines.append(f"- [{name}](docs/{name}): {summary}")
    lines.append("- [command reference](docs/reference/commands.md): every command.")
    lines.append("- [agent skill](mammoth_cli/bundled_skill/mammoth-cli/SKILL.md): the "
                 "installable skill.")
    lines.append("")
    lines.append("## Command families")
    lines.append("")
    for family, records in families.items():
        lines.append(f"- `{family}` ({len(records)} commands)")
    lines.append("")
    lines.append(f"## Source\n\n- {REPO_URL}")
    return "\n".join(lines).rstrip() + "\n"


def render_llms_full_txt(families: dict[str, list[dict[str, object]]]) -> str:
    lines = [
        "# mammoth-cli — full reference",
        "",
        "Every non-alias command with its mutation class, confirmation policy, "
        "backing public SDK symbol, and agent example. Generated deterministically "
        "from the command manifests.",
        "",
    ]
    for family, records in families.items():
        lines.append(f"## {family}")
        lines.append("")
        for record in records:
            lines.append(
                f"- `mammoth {record['command_path']}` "
                f"[{record['mutation_class']}/{record['confirmation']}] "
                f"-> {record['sdk_symbol']}"
            )
            lines.append(f"  example: {record['agent_example']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build() -> dict[Path, str]:
    """Return the mapping of output path to rendered content."""
    families = _families()
    return {
        DOCS_DIR / "reference" / "commands.md": render_commands_md(families),
        DOCS_DIR / "llms.txt": render_llms_txt(families),
        DOCS_DIR / "llms-full.txt": render_llms_full_txt(families),
    }


def main(argv: list[str] | None = None) -> int:
    """Write the docs, or check them for drift with ``--check``."""
    args = argv if argv is not None else sys.argv[1:]
    check = "--check" in args
    drift: list[str] = []
    for path, content in build().items():
        if check:
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != content:
                drift.append(str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if check and drift:
        sys.stderr.write("Docs are stale; run scripts/gen_docs.py:\n")
        sys.stderr.write("\n".join(f"  {p}" for p in drift) + "\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
