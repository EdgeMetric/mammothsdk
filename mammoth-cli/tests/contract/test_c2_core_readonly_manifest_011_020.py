"""Offline oracle for the second ten Core read-only cases.

This test intentionally reads only the checked-in fixture.  It proves the
manifest is bounded and truthful without contacting an API or asserting any
live post-state.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path(__file__).parent / "fixtures" / "C2-CORE-READONLY-011-020.json"
EXPECTED = {
    f"P0-READ-{number:03d}": path
    for number, path in enumerate(
        (
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/conditional-format",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/data/generate",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/derivatives",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/parameter-context",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/pipeline/data-checks",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/pipeline/exports",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/pipeline/exports/<export_id>",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/pipeline/tasks",
            "/workspaces/4/projects/3/datasets/<dataset_id>/dataviews/<view_id>/pipeline/tasks/<task_id>",
        ),
        start=11,
    )
}


def test_second_ten_cases_have_exact_read_only_oracles() -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = document["cases"]
    assert document["status"] == "offline_contract_only"
    assert document["scope"]["effect"] == "read-only"
    assert {case["case_id"] for case in cases} == set(EXPECTED)
    for case in cases:
        assert case["method"] == "GET"
        assert case["path"] == EXPECTED[case["case_id"]]
        assert case["request"]["body"] is None
        assert case["negative"]
        assert "observed" in json.dumps(case)
