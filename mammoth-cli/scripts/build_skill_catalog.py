#!/usr/bin/env python3
"""Generate the packaged, sharded Mammoth CLI skill command catalog.

The command manifest is authoritative for *published CLI command* coverage.
It intentionally does not claim coverage of every backend/OpenAPI operation:
those are separately represented by capability/schema discovery at runtime.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from build_skill_capabilities import _CLI_VERSION, _VERIFIED, _blocker  # noqa: E402

from mammoth_cli.manifest.loader import load_commands  # noqa: E402

MATRIX = ROOT / "docs" / "release-capability-matrix.json"

SKILL = ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli"
REFS = SKILL / "references" / "commands"
INDEX = SKILL / "references" / "command-index.md"
_FAIL_CLOSED_PATCH_RESTRICTIONS = (
    "BLOCKED[B07",
    "BLOCKED[B09",
    "BLOCKED[B17",
    "BLOCKED[B19",
    "BLOCKED[B21",
)


def _load_matrix() -> dict[str, dict[str, object]]:
    """Map each canonical command to its matrix row (first row wins)."""
    rows: dict[str, dict[str, object]] = {}
    for row in json.loads(MATRIX.read_text(encoding="utf-8"))["rows"]:
        command = row.get("canonical_command")
        if command and command not in rows:
            rows[str(command)] = row
    return rows


_REMARK_PREFIXES = (
    "Partial bounded evidence only;",
    "Partial bounded evidence only:",
    "Not supported on release:",
    "Not supported from the CLI on release:",
)


def _remark(text: str, limit: int = 260) -> str:
    text = " ".join(text.split())
    for prefix in _REMARK_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _release(version: object) -> str:
    match = _CLI_VERSION.search(str(version or ""))
    return match.group(0) if match else "an earlier release"


def release_status(command_id: str, matrix: dict[str, dict[str, object]]) -> tuple[str, bool]:
    """Return the per-command release status line and whether the route is refused.

    Typed ``view.transform.*`` commands all submit through ``view.task.add``, so
    they inherit that row; everything without a row is untried.
    """
    via = ""
    row = matrix.get(command_id)
    if row is None and command_id.startswith("view.transform."):
        task_row = matrix.get("view.task.add") or {}
        evidence = task_row.get("evidence") or {}
        proven: set[str] = set()
        if isinstance(evidence, dict):
            proven = set(evidence.get("proven_transforms") or [])
        name = command_id.rsplit(".", 1)[1]
        version = _release(task_row.get("evidence_version"))
        if name in proven:
            return (
                f"Status on release: ran once on CLI {version} through `view.task.add` and was "
                "read back with `view data get`; other inputs for this transform are untried.",
                False,
            )
        return (
            "Status on release: untried; it submits through `view.task.add`, but this "
            "transform was not among those run.",
            False,
        )
    if row is None:
        return "Status on release: untried; no live run recorded.", False
    status = str(row.get("status") or "Unassessed")
    remarks = str(row.get("remarks") or "")
    version = _release(row.get("evidence_version"))
    if status in _VERIFIED:
        return f"Status on release: ran once on CLI {version}{via} — {_remark(remarks)}", False
    if status == "Not supported":
        return f"not supported — {_remark(remarks, limit=400)}", True
    if remarks.startswith("CLI defect fixed in "):
        return f"Status on release: CLI defect fixed, untried since — {_remark(remarks)}", False
    note = _blocker(remarks)
    if note:
        return (
            f"Status on release: observed blocker — {note}. Re-check before relying on it.",
            False,
        )
    return "Status on release: untried; no live run recorded.", False


def body(record: dict[str, object], matrix: dict[str, dict[str, object]]) -> str:
    command_id = str(record["command_id"])
    path = str(record["command_path"])
    result = str(record.get("result_model") or "JSON result envelope")
    example = str(record.get("agent_example") or f"mammoth {path} --output json --no-input")
    mutation = str(record.get("mutation_class") or "unknown")
    wait = str(record.get("wait_policy") or "not_async")
    confirmation = str(record.get("confirmation") or "none")
    restriction = str(record.get("known_restrictions") or "")
    # These restrictions mark untyped or variadic contracts that the local CLI
    # rejects before dispatch, so catalog wording must not advertise success.
    fail_closed = restriction.startswith(_FAIL_CLOSED_PATCH_RESTRICTIONS)
    if fail_closed:
        example_note = (
            "Discovery only: this command is fail-closed and must not dispatch a request."
        )
        outcome = (
            "Execution is unavailable for the current contract and returns "
            "`unsupported_contract`. Do not infer request fields or retry it; use only a "
            "separately typed alternative."
        )
    elif confirmation == "confirm_target":
        example_note = (
            "Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target."
        )
    elif confirmation in {"prompt_or_yes", "yes_always"}:
        example_note = "Illustrative only: append `--yes` after observing an owned target."
    else:
        example_note = "Placeholders are illustrative; resolve IDs and input from observed reads."
    details = f"Known restriction: {restriction}\n\n" if fail_closed else ""
    status_line, refused = release_status(command_id, matrix)
    if fail_closed:
        outcome_block = f"{outcome}\n\n{details}"
    elif refused:
        outcome_block = f"Do not run: {status_line}\n\n"
    else:
        outcome_block = (
            f"Result: `{result}`; mutation `{mutation}`, confirmation `{confirmation}`, "
            f"wait policy `{wait}`.\n\n{status_line}\n\n"
        )
    return (
        f"### `{command_id}`\n\n"
        f"Run: `mammoth {path}`. Exact input fields: `mammoth schema get {command_id} "
        "--output json --no-input`.\n\n"
        f"Example: `{example}`. {example_note}\n\n"
        + (
            "Secret fields: pass the body as `--input FILE` (mode 0600); never inline.\n\n"
            if "--input /private/path/request.json" in example
            else ""
        )
        + outcome_block
    )


_GROUP_PREAMBLE = (
    "Every command returns the standard JSON envelope. On nonzero exit, read the error "
    "envelope and its `recovery_commands`; do not guess request fields. "
    "\"Status on release\" is joined from `docs/release-capability-matrix.json`: "
    "*ran once* means one bounded live run succeeded on the named CLI release, "
    "*untried* means nobody has run it, *not supported* means the backend refuses it. "
    "When this file disagrees with [capabilities](../capabilities.md) or a recipe, "
    "they win. Envelope shapes: [machine output](../machine-output.md).\n\n"
)


def render() -> dict[Path, str]:
    matrix = _load_matrix()
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in load_commands():
        groups[str(record["command_id"]).split(".", 1)[0]].append(record)
    output: dict[Path, str] = {}
    links: list[str] = []
    for group, records in sorted(groups.items()):
        path = REFS / f"{group}.md"
        output[path] = (
            f"# `{group}` commands\n\n"
            + _GROUP_PREAMBLE
            + "".join(body(record, matrix) for record in records)
        )
        links.append(f"- [{group}](commands/{group}.md) — {len(records)} published commands")
    output[INDEX] = (
        "# Published CLI command catalog\n\n"
        "This generated catalog is a lookup table for every command in the published CLI "
        f"manifest, currently {sum(len(items) for items in groups.values())}; each entry "
        "carries its release status line. It is a command-contract index, not an "
        "assertion that every backend/OpenAPI operation has a CLI binding. For an exact local "
        "CLI contract, run `mammoth schema get COMMAND_ID --output json --no-input`; "
        "`mammoth capability list` is an API-binding inventory and can omit typed/local CLI "
        "routes. For focused workflows, read the "
        "[recipes index](recipes/index.md). Sensitive structured input must come from a private "
        "file or pipe; never put secrets in literal argv.\n\n"
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
