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
    rows = source["operations"]
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
                "sdk_symbol": row.get("sdk_symbol"),
                "evidence": row.get("evidence"),
            }
        )
        if row["capability_id"] in CURRENT_CHECKOUT_BINDINGS:
            command, symbol = CURRENT_CHECKOUT_BINDINGS[row["capability_id"]]
            safe_rows[-1]["canonical_command"] = command
            safe_rows[-1]["sdk_symbol"] = symbol
            safe_rows[-1]["remarks"] += (
                " Current checkout binding is committed structural mapping; release behavior "
                "remains unverified."
            )
    expected_counts = {"Full": 0, "Partial": 7, "Not supported": 0, "Unassessed": 521}
    if len(safe_rows) != 528 or counts != expected_counts:
        raise ValueError(f"matrix integrity failed: rows={len(safe_rows)} counts={counts}")
    digest = hashlib.sha256(raw).hexdigest()
    provenance = dict(source["provenance"])
    provenance["primary_source_file"] = "workbook/OPENAPI-release-20260916.json"
    provenance["pinned_source"] = "repo/mammoth-cli/spec/openapi/openapi.json"
    provenance["manifest"] = "repo/mammoth-cli/spec/manifests/openapi-operations.yaml"
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
        "Current release OpenAPI: 528 operations / 355 paths; 230 Core / 298 Miscellaneous.",
        "Statuses: 7 Partial (bounded evidence only), 521 Unassessed, 0 Full, 0 Not supported.",
        "This is a sanitized inventory; the readiness workbook remains authoritative.",
        "",
        (
            "| ID | Capability | Status | Remarks | Group | Operation | Method | "
            "Path | CLI | SDK | Evidence |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|",
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
                    "sdk_symbol",
                    "evidence",
                )
            )
            + " |"
        )
    args.markdown_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
