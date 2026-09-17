#!/usr/bin/env python3
"""Generate sanitized repository-facing release capability matrix artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CURRENT_CHECKOUT_BINDINGS = {
    "REL-002": ("dashboard.tags.delete", "mammoth.api.dashboards.DashboardsAPI.delete_tag"),
    "REL-081": ("dashboard.tags.list", "mammoth.api.dashboards.DashboardsAPI.list_tags"),
    "REL-268": ("dashboard.tags.rename", "mammoth.api.dashboards.DashboardsAPI.rename_tag"),
    "REL-519": ("dashboard.tags.set", "mammoth.api.dashboards.DashboardsAPI.set_tags"),
    "REL-327": ("dashboard.tags.merge", "mammoth.api.dashboards.DashboardsAPI.merge_tag"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    source = json.loads(raw)
    # ``docs/release-capability-matrix.json`` is now the canonical repository
    # inventory.  Accept it directly as well as the historical workbook export
    # used for one-time imports; never bake a release's row counts into code.
    rows = source.get("rows", source.get("operations"))
    if not isinstance(rows, list):
        raise ValueError("source must contain an operations or rows array")
    counts = {"Full": 0, "Partial": 0, "Not supported": 0, "Unassessed": 0}
    safe_rows = []
    for row in rows:
        status = row.get("status") or "Unassessed"
        if status not in counts:
            raise ValueError(f"unexpected status: {status}")
        counts[status] += 1
        remarks = row.get("remarks") or "Unassessed pending approval and release evidence."
        if status == "Partial" and "Partial" not in remarks:
            remarks = f"Partial bounded evidence only; {remarks}"
        safe_rows.append(
            {
                "capability_id": row["capability_id"],
                "capability": row["capability"],
                "status": status,
                "remarks": remarks,
                "core_vs_misc": row["core_vs_misc"],
                "operation_id": row["operation_id"],
                "method": row["method"],
                "path": row["path"],
                "canonical_command": row.get("canonical_command"),
                "schema_id": row.get("schema_id", row.get("canonical_command")),
                "sdk_symbol": row.get("sdk_symbol"),
                "mapping_state": row.get("mapping_state"),
                "mapping_gap_reason": row.get("mapping_gap_reason"),
                "evidence": row.get("evidence"),
                "evidence_version": row.get("evidence_version"),
            }
        )
        if row["capability_id"] in CURRENT_CHECKOUT_BINDINGS:
            command, symbol = CURRENT_CHECKOUT_BINDINGS[row["capability_id"]]
            safe_rows[-1]["canonical_command"] = command
            safe_rows[-1]["sdk_symbol"] = symbol
            binding_note = (
                "Current checkout binding is committed structural mapping; release behavior "
                "remains unverified."
            )
            if binding_note not in safe_rows[-1]["remarks"]:
                safe_rows[-1]["remarks"] = safe_rows[-1]["remarks"].rstrip() + " " + binding_note
    identities = {(row["method"].upper(), row["path"]) for row in safe_rows}
    if len(identities) != len(safe_rows):
        raise ValueError("matrix integrity failed: duplicate method/path identity")
    # Preserve the upstream workbook digest when regenerating the canonical
    # matrix. This keeps repeated JSON/Markdown generation idempotent instead
    # of hashing the generated JSON (which would change on every run).
    digest = source.get("source_sha256") or hashlib.sha256(raw).hexdigest()
    provenance = dict(source.get("source_provenance", source.get("provenance", {})))
    payload = {
        "artifact": "mammoth-cli-release-capability-matrix",
        "source_sha256": digest,
        "source_provenance": provenance,
        "counts": counts,
        "rows": safe_rows,
        "note": (
            "Sanitized row-level inventory; workbook remains authoritative. "
            "No credentials or pilot payloads are included."
        ),
    }
    args.json_out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Release capability matrix (sanitized)",
        "",
        f"Source workbook SHA-256: `{digest}`.",
        f"Current release OpenAPI: {len(safe_rows)} operations / {len({row['path'] for row in safe_rows})} paths.",
        "Statuses: " + ", ".join(f"{counts[name]} {name}" for name in counts) + ".",
        "This is the canonical sanitized repository inventory; historical workbooks retain their original evidence context.",
        "",
        (
            "| ID | Capability | Status | Remarks | Group | Operation | Method | "
            "Path | CLI | Schema ID | SDK | Mapping state | Mapping gap | Evidence | Evidence version |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in safe_rows:

        def cell(value: object) -> str:
            if value is None:
                rendered = "—"
            elif isinstance(value, dict):
                # Keep artifact links readable in Markdown instead of leaking
                # Python's raw dictionary representation into the matrix.
                def item_text(item: object) -> str:
                    if isinstance(item, list):
                        return ", ".join(str(entry) for entry in item)
                    return str(item)

                rendered = "; ".join(
                    f"{key}={item_text(item)}"
                    for key, item in value.items()
                    if item is not None
                )
            else:
                rendered = str(value)
            return rendered.replace("|", "\\|").replace("\n", " ")

        lines.append(
            "| "
            + " | ".join(
                cell(row[key])
                for key in (
                    "capability_id",
                    "capability",
                    "status",
                    "remarks",
                    "core_vs_misc",
                    "operation_id",
                    "method",
                    "path",
                    "canonical_command",
                    "schema_id",
                    "sdk_symbol",
                    "mapping_state",
                    "mapping_gap_reason",
                    "evidence",
                    "evidence_version",
                )
            )
            + " |"
        )
    args.markdown_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
