"""Focused, local-only tests for release capability matrix drift reporting."""

from __future__ import annotations

import importlib.util
from pathlib import Path


CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = CLI_ROOT / "scripts" / "report_release_capability_drift.py"


def _script_module():
    spec = importlib.util.spec_from_file_location("release_capability_drift", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_drift_uses_method_path_and_preserves_existing_evidence() -> None:
    drift = _script_module()
    kept = {
        "capability_id": "REL-001",
        "method": "GET",
        "path": "/kept",
        "operation_id": "OldName",
        "status": "Partial",
        "evidence": {"artifact": "sanitized.json"},
        "evidence_version": "1.1.11",
        "mapping_state": "cli_and_sdk_mapped",
    }
    changed = {
        "capability_id": "REL-002",
        "method": "POST",
        "path": "/changed",
        "operation_id": "BeforeRename",
        "status": "Unassessed",
        "evidence": None,
        "evidence_version": None,
        "mapping_state": "unmapped",
    }
    removed = {"capability_id": "REL-003", "method": "DELETE", "path": "/removed", "operation_id": "Gone"}
    candidate = {
        "paths": {
            "/kept": {"get": {"operationId": "DifferentNameIsReviewedSeparately"}},
            "/changed": {"post": {"operationId": "AfterRename"}},
            "/new": {"patch": {"operationId": "NewOperation"}},
        }
    }
    report, scaffolds = drift.build_report({"rows": [kept, changed, removed]}, candidate)

    assert report["summary"] == {
        "added": 1,
        "removed": 1,
        "operation_id_changed": 2,
        "preserved_method_path_rows": 2,
    }
    assert {item["capability_id"] for item in report["preserved"]} == {"REL-001", "REL-002"}
    preserved_kept = next(item for item in report["preserved"] if item["capability_id"] == "REL-001")
    assert preserved_kept["status"] == "Partial"
    assert preserved_kept["evidence"] == {"artifact": "sanitized.json"}
    assert report["removed_review"] == [{"identity": "DELETE /removed", "capability_id": "REL-003", "operation_id": "Gone"}]
    assert scaffolds[0]["status"] == "Unassessed"
    assert scaffolds[0]["canonical_command"] is None
    assert scaffolds[0]["schema_id"] is None
    assert scaffolds[0]["sdk_symbol"] is None
    assert scaffolds[0]["mapping_state"] == "unmapped"
    assert report["note"].startswith("Report-only")


def test_unmapped_scaffold_has_explicit_gap_and_no_support_claim() -> None:
    drift = _script_module()
    row = drift.scaffold_addition(
        {"method": "GET", "path": "/not-yet-reviewed", "operation_id": "FutureRead"}
    )
    assert row["canonical_command"] is None
    assert row["schema_id"] is None
    assert row["sdk_symbol"] is None
    assert row["mapping_state"] == "unmapped"
    assert row["mapping_gap_reason"]
    assert row["status"] == "Unassessed"
    assert row["evidence"] is None and row["evidence_version"] is None
