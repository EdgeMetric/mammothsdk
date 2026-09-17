#!/usr/bin/env python3
"""Report a candidate OpenAPI's safe, review-required matrix drift.

The committed ``docs/release-capability-matrix.json`` is the canonical release
inventory. This script does not fetch the network and never changes that file.
It compares a supplied OpenAPI document by stable ``METHOD path`` identity and
writes deterministic review artifacts:

* unchanged rows, whose IDs, statuses, and evidence are retained verbatim;
* additions scaffolded as ``Unassessed``; and
* removals and operation-ID changes, which require reviewer action.

Usage::

    python scripts/report_release_capability_drift.py \
      --openapi /path/to/candidate-openapi.json \
      --report-out /tmp/capability-drift.json \
      --scaffold-out /tmp/capability-additions.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HTTP_METHODS = frozenset({"get", "put", "post", "delete", "options", "head", "patch", "trace"})
DEFAULT_MATRIX = Path(__file__).resolve().parent.parent / "docs" / "release-capability-matrix.json"


def identity(method: str, path: str) -> str:
    """Return the matrix's stable method-and-path identity."""
    return f"{method.upper()} {path}"


def openapi_operations(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return OpenAPI operations keyed by method/path, rejecting ambiguity."""
    result: dict[str, dict[str, Any]] = {}
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        raise ValueError("OpenAPI paths must be an object")
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if not isinstance(method, str) or method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                raise ValueError(f"OpenAPI operation must be an object: {method} {path}")
            key = identity(method, path)
            if key in result:
                raise ValueError(f"duplicate OpenAPI method/path: {key}")
            operation_id = operation.get("operationId")
            result[key] = {
                "method": method.upper(),
                "path": path,
                "operation_id": operation_id if isinstance(operation_id, str) else None,
            }
    return result


def matrix_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return canonical release rows keyed by method/path."""
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("matrix must contain a rows array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("matrix row must be an object")
        method, path = row.get("method"), row.get("path")
        if not isinstance(method, str) or not isinstance(path, str):
            raise ValueError("matrix row must contain string method and path")
        key = identity(method, path)
        if key in result:
            raise ValueError(f"duplicate matrix method/path: {key}")
        result[key] = row
    return result


def addition_id(operation: dict[str, Any]) -> str:
    """Give an addition a deterministic temporary ID, never a release ID."""
    digest = hashlib.sha256(identity(operation["method"], operation["path"]).encode()).hexdigest()
    return f"NEW-{digest[:12].upper()}"


def scaffold_addition(operation: dict[str, Any]) -> dict[str, Any]:
    """Create a deliberately unassessed row for reviewer assignment."""
    return {
        "capability_id": addition_id(operation),
        "capability": f"Review {operation['method']} {operation['path']}",
        "status": "Unassessed",
        "remarks": "New OpenAPI operation; assign ownership and evidence before any support claim.",
        "core_vs_misc": "Unclassified",
        "operation_id": operation["operation_id"],
        "method": operation["method"],
        "path": operation["path"],
        "canonical_command": None,
        "schema_id": None,
        "sdk_symbol": None,
        "mapping_state": "unmapped",
        "mapping_gap_reason": "No reviewed CLI or SDK mapping recorded.",
        "evidence": None,
        "evidence_version": None,
    }


def build_report(matrix: dict[str, Any], candidate: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build stable review data without modifying any existing row."""
    existing = matrix_rows(matrix)
    observed = openapi_operations(candidate)
    existing_keys, observed_keys = set(existing), set(observed)
    added = [scaffold_addition(observed[key]) for key in sorted(observed_keys - existing_keys)]
    removed = [
        {"identity": key, "capability_id": existing[key].get("capability_id"), "operation_id": existing[key].get("operation_id")}
        for key in sorted(existing_keys - observed_keys)
    ]
    operation_id_changed = [
        {
            "identity": key,
            "capability_id": existing[key].get("capability_id"),
            "matrix_operation_id": existing[key].get("operation_id"),
            "candidate_operation_id": observed[key]["operation_id"],
            "review_action": "Review semantic compatibility before updating the canonical row.",
        }
        for key in sorted(existing_keys & observed_keys)
        if existing[key].get("operation_id") != observed[key]["operation_id"]
    ]
    preserved = [
        {
            "identity": key,
            "capability_id": existing[key].get("capability_id"),
            "status": existing[key].get("status"),
            "evidence": existing[key].get("evidence"),
            "evidence_version": existing[key].get("evidence_version"),
            "mapping_state": existing[key].get("mapping_state"),
        }
        for key in sorted(existing_keys & observed_keys)
    ]
    report = {
        "artifact": "mammoth-cli-release-capability-drift",
        "identity": "METHOD path",
        "matrix_row_count": len(existing),
        "candidate_operation_count": len(observed),
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "operation_id_changed": len(operation_id_changed),
            "preserved_method_path_rows": len(preserved),
        },
        "added_scaffolds": added,
        "removed_review": removed,
        "operation_id_changed_review": operation_id_changed,
        "preserved": preserved,
        "implementation_queue": [
            {
                "identity": identity(row["method"], row["path"]),
                "capability_id": row["capability_id"],
                "action": "Discover contract, implement, test, and obtain review; remain Unassessed until evidence is accepted.",
            }
            for row in added
        ]
        + [
            {
                "identity": item["identity"],
                "capability_id": item["capability_id"],
                "action": item["review_action"],
            }
            for item in operation_id_changed
        ]
        + [
            {
                "identity": item["identity"],
                "capability_id": item["capability_id"],
                "action": "Review removal before deleting or deprecating the canonical row.",
            }
            for item in removed
        ],
        "note": "Report-only: no route is implemented and no support status is promoted automatically.",
    }
    return report, added


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, required=True, help="candidate OpenAPI JSON")
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX, help="canonical release matrix")
    parser.add_argument("--report-out", type=Path, required=True)
    parser.add_argument("--scaffold-out", type=Path, required=True)
    args = parser.parse_args()
    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    candidate = json.loads(args.openapi.read_text(encoding="utf-8"))
    report, additions = build_report(matrix, candidate)
    write_json(args.report_out, report)
    write_json(args.scaffold_out, {"rows": additions})


if __name__ == "__main__":
    main()
