"""Focused, local-only tests for release capability matrix drift reporting."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = CLI_ROOT / "scripts" / "report_release_capability_drift.py"
MATRIX = CLI_ROOT / "docs" / "release-capability-matrix.json"
RELEASE_BASELINE = CLI_ROOT / "spec" / "openapi" / "release-20260916.json"
RELEASE_METADATA = CLI_ROOT / "spec" / "openapi" / "release-20260916.metadata.json"


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
    removed = {
        "capability_id": "REL-003",
        "method": "DELETE",
        "path": "/removed",
        "operation_id": "Gone",
    }
    candidate = {
        "paths": {
            "/kept": {"get": {"operationId": "DifferentNameIsReviewedSeparately"}},
            "/changed": {
                "post": {
                    "operationId": "AfterRename",
                    "requestBody": {
                        "content": {"application/json": {"schema": {"type": "string"}}}
                    },
                }
            },
            "/new": {"patch": {"operationId": "NewOperation"}},
        }
    }
    baseline = {
        "paths": {
            "/kept": {"get": {"operationId": "OldName"}},
            "/changed": {
                "post": {
                    "operationId": "BeforeRename",
                    "requestBody": {
                        "content": {"application/json": {"schema": {"type": "integer"}}}
                    },
                }
            },
        }
    }
    report, scaffolds = drift.build_report({"rows": [kept, changed, removed]}, candidate, baseline)

    assert report["summary"] == {
        "added": 1,
        "removed": 1,
        "operation_id_changed": 2,
        "semantic_contract_changed": 1,
        "preserved_method_path_rows": 2,
    }
    assert {item["capability_id"] for item in report["preserved"]} == {"REL-001", "REL-002"}
    preserved_kept = next(
        item for item in report["preserved"] if item["capability_id"] == "REL-001"
    )
    assert preserved_kept["status"] == "Partial"
    assert preserved_kept["evidence"] == {"artifact": "sanitized.json"}
    assert preserved_kept["row"] is kept
    assert report["removed_review"] == [
        {"identity": "DELETE /removed", "capability_id": "REL-003", "operation_id": "Gone"}
    ]
    assert report["semantic_contract_changed_review"] == [
        {
            "identity": "POST /changed",
            "capability_id": "REL-002",
            "review_action": drift.SEMANTIC_REVIEW_ACTION,
        }
    ]
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


def test_release_baseline_matches_canonical_matrix_method_path_inventory() -> None:
    drift = _script_module()
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    baseline = json.loads(RELEASE_BASELINE.read_text(encoding="utf-8"))
    metadata = json.loads(RELEASE_METADATA.read_text(encoding="utf-8"))
    baseline_operations = drift.openapi_operations(baseline)
    canonical_rows = drift.matrix_rows(matrix)

    assert metadata["operation_count"] == 528
    assert len(baseline_operations) == metadata["operation_count"]
    assert len(canonical_rows) == metadata["operation_count"]
    assert set(baseline_operations) == set(canonical_rows)
