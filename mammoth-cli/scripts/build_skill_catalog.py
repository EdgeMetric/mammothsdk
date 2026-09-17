#!/usr/bin/env python3
"""Generate the packaged, sharded Mammoth CLI skill command catalog.

The command manifest is authoritative for *published CLI command* coverage.
It intentionally does not claim coverage of every backend/OpenAPI operation:
those are separately represented by capability/schema discovery at runtime.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mammoth_cli.manifest.loader import load_commands  # noqa: E402

SKILL = ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli"
REFS = SKILL / "references" / "commands"
INDEX = SKILL / "references" / "command-index.md"


def body(record: dict[str, object]) -> str:
    command_id = str(record["command_id"])
    path = str(record["command_path"])
    result = str(record.get("result_model") or "JSON result envelope")
    example = str(record.get("agent_example") or f"mammoth {path} --output json --no-input")
    mutation = str(record.get("mutation_class") or "unknown")
    wait = str(record.get("wait_policy") or "not_async")
    confirmation = str(record.get("confirmation") or "none")
    if confirmation == "confirm_target":
        example_note = (
            "Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target."
        )
    elif confirmation in {"prompt_or_yes", "yes_always"}:
        example_note = "Illustrative only: append `--yes` after observing an owned target."
    else:
        example_note = (
            "Runnable only after resolving schema-required IDs and input from observed reads."
        )
    return (
        f"### `{command_id}`\n\n"
        f"Run: `mammoth {path}`. Exact input fields: `mammoth schema get {command_id} "
        "--output json --no-input`.\n\n"
        f"Example: `{example}`. {example_note}\n\n"
        f"Expected success: `{result}` in the standard JSON envelope; mutation `{mutation}`, "
        f"confirmation `{confirmation}`, wait policy `{wait}`. On nonzero exit, inspect the "
        "JSON error envelope and its `recovery_commands`; do not guess request fields. "
        "See [representative envelopes](../machine-output.md) for concrete "
        "success/error shapes.\n\n"
    )


def render() -> dict[Path, str]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in load_commands():
        groups[str(record["command_id"]).split(".", 1)[0]].append(record)
    output: dict[Path, str] = {}
    links: list[str] = []
    for group, records in sorted(groups.items()):
        path = REFS / f"{group}.md"
        output[path] = f"# `{group}` commands\n\n" + "".join(body(record) for record in records)
        links.append(f"- [{group}](commands/{group}.md) — {len(records)} published commands")
    output[INDEX] = (
        "# Published CLI command catalog\n\n"
        "This generated catalog covers every command in the published CLI manifest, currently "
        f"{sum(len(items) for items in groups.values())}. It is a command-contract index, not an "
        "assertion that every backend/OpenAPI operation has a CLI binding. For an exact local "
        "CLI contract, run `mammoth schema get COMMAND_ID --output json --no-input`; "
        "`mammoth capability list` is an API-binding inventory and can omit typed/local CLI "
        "routes. For focused workflows, read the "
        "[recipes index](recipes/index.md).\n\n"
        "Load only the applicable domain file:\n\n" + "\n".join(links) + "\n"
    )
    return {path: text.rstrip() + "\n" for path, text in output.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    stale = [
        path
        for path, text in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    if args.check:
        if stale:
            print("stale skill catalog:\n" + "\n".join(str(path) for path in stale))
            return 1
        return 0
    for path, text in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
