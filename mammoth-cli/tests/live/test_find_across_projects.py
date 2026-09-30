"""Live checks: a dataset's name finds it even when the call runs under another project.

The in-product agent runs every call under the project the user last opened. Asked
for a dataset by name that lives in a different project, both name searches looked
only in that one project and the agent answered that the dataset did not exist.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_find_across_projects.py -m live -v
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def other_project(live_cli: LiveCli) -> Iterator[int]:
    """An empty project the calls run under; deleted at the end, even on failure."""
    data, _ = live_cli.ok("project", "create", f"live-find-other-{int(time.time())}", "--yes")
    project = int(data["id"])
    try:
        yield project
    finally:
        removed = live_cli.run(
            *("project", "delete", str(project), "--yes", "--confirm", str(project)),
            project=None,
        )
        assert "error" not in removed, f"project {project} not deleted: {removed}"


def test_dataset_list_by_name_names_the_project_the_match_is_in(
    live_cli: LiveCli, sales_data: SalesData, other_project: int
) -> None:
    found, _ = live_cli.ok(
        "dataset", "list", "--input", json.dumps({"name": "SALES_"}), project=other_project
    )

    assert found["matched"] == 0
    elsewhere = {row["id"]: row["project_id"] for row in found["in_other_projects"]}
    assert elsewhere[sales_data.dataset] == sales_data.project


def test_dataset_find_searches_past_the_project_the_call_runs_under(
    live_cli: LiveCli, sales_data: SalesData, other_project: int
) -> None:
    found, _ = live_cli.ok("dataset", "find", "SALES_", project=other_project)

    matches = {row["id"]: row["project_id"] for row in found["matches"]}
    assert matches[sales_data.dataset] == sales_data.project
