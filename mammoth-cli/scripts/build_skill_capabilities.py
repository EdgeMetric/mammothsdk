#!/usr/bin/env python3
"""Generate the packaged skill's release capability reference from the matrix.

``docs/release-capability-matrix.json`` is the canonical record of what has
been exercised on release and with what outcome. This script projects it into
``references/capabilities.md`` so an agent can tell, per command, whether the
route is proven, known-blocked, or simply untried, without reading evidence
files. Regenerate on every release, after the matrix is updated.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mammoth_cli.manifest.loader import load_commands  # noqa: E402

MATRIX = ROOT / "docs" / "release-capability-matrix.json"
_CLI_VERSION = re.compile(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)")
_REFS = ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli" / "references"
OUTPUT = _REFS / "capabilities.md"
OUTPUT_MISC = _REFS / "capabilities-misc.md"
# Families an ETL / dashboard task touches; everything else is administration
# and goes to the companion file so the main one stays small.
_CORE_FAMILIES = frozenset({"dashboard", "dataset", "file", "folder", "job", "project", "view"})

_VERIFIED = {"Full", "Partial"}
# Remark markers that mean "the route itself answered with an error", as
# opposed to "no fixture was available" or "out of scope for that sweep".
_BLOCKER_MARKERS = (
    "server_error",
    "backend",
    "HTTP 400",
    "HTTP 404",
    "HTTP 405",
    "HTTP 409",
    "HTTP 500",
    "cli_error",
    "validation_error",
    "not_supported",
)


def _family(command_id: str) -> str:
    return command_id.split(".", 1)[0]


def _blocker(remarks: str) -> str | None:
    if not any(marker in remarks for marker in _BLOCKER_MARKERS):
        return None
    # Keep the observation clause only; drop the leading status prose.
    text = remarks.split("observed", 1)[-1].strip(" :;") if "observed" in remarks else remarks
    text = text.split(". ", 1)[0].rstrip(".")
    return text[:180]


def _cell(text: object) -> str:
    return " ".join(str(text).split()).replace("|", "/")


def build() -> str:
    return build_all()[OUTPUT]


def build_all() -> dict[Path, str]:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    rows = [row for row in matrix["rows"] if row.get("canonical_command")]
    # Rows carry the CLI release their evidence was collected on, in mixed
    # spellings ("2.0.15", "1.1.11-pypi", "mammoth-cli 1.1.11; mammoth-io
    # 0.7.1"); compare parsed versions, never the strings.
    observed = sorted(
        {
            tuple(int(part) for part in match.groups())
            for row in rows
            if (match := _CLI_VERSION.search(str(row.get("evidence_version") or "")))
        }
    )
    version_range = (
        f"{'.'.join(map(str, observed[0]))} through {'.'.join(map(str, observed[-1]))}"
        if observed
        else "unknown"
    )
    families: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        families[_family(str(row["canonical_command"]))].append(row)

    verified = sum(1 for row in rows if row["status"] in _VERIFIED)
    unsupported = sum(1 for row in rows if row["status"] == "Not supported")
    published = sum(1 for _ in load_commands())
    total_operations = len(matrix["rows"])
    lines = [
        "# What is proven on release",
        "",
        "Generated from `docs/release-capability-matrix.json`; do not edit by hand.",
        f"The CLI publishes {published} commands. {len(rows)} of them bind one of the "
        f"{total_operations} API operations in the matrix; the remainder are local "
        "commands (`schema`, `auth`, `doctor`, `log`, ...) or typed variants that share "
        "an operation (every `view transform *` command submits through "
        f"`view.task.add`). {verified} bound commands ran once successfully on release, "
        f"{unsupported} are not supported there, and the rest are untried. Untried is "
        "not broken: discover the contract with "
        "`mammoth schema get COMMAND_ID`, run it, and "
        "treat the structured error envelope as the answer.",
        "",
        "Status meanings:",
        "",
        "- **ran once**: one bounded live run on release returned a success "
        "envelope (single path; variants and error paths are usually untested). "
        "It is not a guarantee that the route works for other inputs.",
        "- **not supported**: the backend refuses the route on release; the note "
        "says why and what to use instead.",
        "- **observed blocker**: the last run hit an error; the note quotes it. "
        "Re-check before relying on the route, and do not retry the same input.",
        "- **CLI defect fixed, untried since**: the failure was on the CLI side "
        "and this release repairs it; nobody has re-run the route yet.",
        "- Commands not listed under a family are untried.",
        "",
        "The typed `view transform *` commands all submit through `view.task.add`; "
        "its matrix row names the transformations that ran end to end and were read "
        "back (filter, fill-missing, join, pivot, set-values with a condition, text, "
        "bulk-replace, convert-type, discard-duplicates). A transformation not named "
        "there has the same untried status as any other command.",
        "",
        "## Coverage by family",
        "",
        "| Family | Commands | Ran once | Not supported | Untried |",
        "|---|---|---|---|---|",
    ]
    for family in sorted(families, key=lambda name: (-len(families[name]), name)):
        group = families[family]
        v = sum(1 for row in group if row["status"] in _VERIFIED)
        n = sum(1 for row in group if row["status"] == "Not supported")
        lines.append(f"| `{family}` | {len(group)} | {v} | {n} | {len(group) - v - n} |")
    lines.append("")

    misc: list[str] = [
        "# What is proven on release: administration families",
        "",
        "Generated from `docs/release-capability-matrix.json`; do not edit by hand. "
        "Companion to [capabilities](capabilities.md), which holds the status "
        "meanings, the coverage table and the core families (dashboard, dataset, "
        "file, folder, job, project, view). Load this file only for a task in one "
        "of the families below.",
        "",
    ]
    lines.append(
        "Administration families (`workspace`, `user`, `billing`, `support`, "
        "`connector`, ...) are in [capabilities-misc](capabilities-misc.md)."
    )
    lines.append("")
    for family in sorted(families):
        target = lines if family in _CORE_FAMILIES else misc
        group = sorted(families[family], key=lambda row: str(row["canonical_command"]))
        verified_ids = sorted(
            {str(row["canonical_command"]) for row in group if row["status"] in _VERIFIED}
        )
        unsupported_rows = [row for row in group if row["status"] == "Not supported"]
        blocked: dict[str, str] = {}
        fixed: dict[str, str] = {}
        for row in group:
            if row["status"] in _VERIFIED or row["status"] == "Not supported":
                continue
            remarks = str(row.get("remarks") or "")
            if remarks.startswith("CLI defect fixed in "):
                prefix_len = len("CLI defect fixed in ")
                fixed[str(row["canonical_command"])] = remarks.split(";", 1)[0][prefix_len:]
                continue
            note = _blocker(remarks)
            if note:
                blocked.setdefault(str(row["canonical_command"]), note)
        if not (verified_ids or unsupported_rows or blocked or fixed):
            continue
        target.append(f"## `{family}`")
        target.append("")
        if verified_ids:
            target.append("Ran once: " + ", ".join(f"`{cid}`" for cid in verified_ids))
            target.append("")
        if unsupported_rows or blocked or fixed:
            target.append("| Command | State | Note |")
            target.append("|---|---|---|")
            for row in unsupported_rows:
                target.append(
                    f"| `{row['canonical_command']}` | not supported | {_cell(row['remarks'])} |"
                )
            for cid, note in sorted(blocked.items()):
                target.append(f"| `{cid}` | observed blocker | {_cell(note)} |")
            for cid, note in sorted(fixed.items()):
                target.append(f"| `{cid}` | CLI defect fixed, untried since | {_cell(note)} |")
            target.append("")
    footer = (
        f"Evidence collected on CLI releases {version_range}; each row's release is "
        "recorded in `docs/release-capability-matrix.json` (`evidence_version`). A row "
        "that ran on an older release has not been re-run since unless its note says so. "
        "Details: `docs/capability-evidence/` in the repository."
    )
    lines += [footer, ""]
    misc += [footer, ""]
    return {OUTPUT: "\n".join(lines), OUTPUT_MISC: "\n".join(misc)}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    outputs = build_all()
    if "--check" in args:
        for path, content in outputs.items():
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != content:
                print(f"{path} is stale; run scripts/build_skill_capabilities.py", file=sys.stderr)
                return 1
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
