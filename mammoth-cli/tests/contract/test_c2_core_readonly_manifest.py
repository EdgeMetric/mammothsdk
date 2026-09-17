"""Offline C2 oracle for the first ten Core read-only capability cases."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path(__file__).parent / "fixtures" / "C2-CORE-READONLY-001-010.json"
EXPECTED = {
    "P0-READ-001": "/workspaces/4/projects/3/datasets",
    "P0-READ-002": "/workspaces/4/projects/3/datasets/<dataset_id>",
    "P0-READ-003": "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews",
    "P0-READ-004": "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/data",
    "P0-READ-005": "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/preview",
    "P0-READ-006": "/workspaces/4/projects/3/files",
    "P0-READ-007": "/workspaces/4/projects/3/files/<file_id>",
    "P0-READ-008": "/workspaces/4/projects/3/folders",
    "P0-READ-009": "/workspaces/4/projects/3/folders/<folder_id>",
    "P0-READ-010": "/workspaces/4/projects/3/trash",
}


def test_first_ten_cases_have_exact_scoped_get_oracles() -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = document["cases"]
    assert document["status"] == "offline_contract_only"
    assert len(cases) == 10
    assert {case["case_id"] for case in cases} == set(EXPECTED)
    for case in cases:
        assert case["method"] == "GET"
        assert case["path"] == EXPECTED[case["case_id"]]
        assert case["request"]["body"] is None
        assert case["negative"]


def test_dependent_cases_require_observed_parent_ids_and_no_mutation() -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for case in document["cases"]:
        serialized = json.dumps(case)
        assert "observed" in serialized or case["case_id"] in {
            "P0-READ-001", "P0-READ-006", "P0-READ-008", "P0-READ-010"
        }
        assert case["method"] == "GET"
    assert document["scope"]["effect"] == "read-only"
