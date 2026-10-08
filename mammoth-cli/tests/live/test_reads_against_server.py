"""Live replacements for the fake-socket realcode tests of project reads and draft status.

``project get``, ``project resource-status``, ``view draft status`` and the error
mapping of a missing resource, each run against a real tenant instead of a
scripted HTTP socket.
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_resource_status_of_a_quiet_project_says_what_it_covers(
    live_cli: LiveCli, scratch_project: int
) -> None:
    data, _ = live_cli.ok("project", "resource-status", project=scratch_project)

    assert data["in_flight"] == {}
    assert "covers" in data


def test_project_get_names_what_it_does_not_cover(live_cli: LiveCli, scratch_project: int) -> None:
    data, _ = live_cli.ok("project", "get", str(scratch_project), project=scratch_project)

    assert data["id"] == scratch_project
    assert "datasets" in data["covers"]


def test_a_view_in_draft_is_reported_as_draft(live_cli: LiveCli, sales_data: SalesData) -> None:
    view = str(sales_data.view)
    parent = ("--input", json.dumps({"dataset_id": sales_data.dataset}))
    live_cli.ok("view", "draft", "enter", view, *parent, "--yes", project=sales_data.project)
    try:
        status, _ = live_cli.ok("view", "draft", "status", view, project=sales_data.project)
    finally:
        live_cli.ok("view", "draft", "discard", view, *parent, "--yes", project=sales_data.project)

    assert status["is_draft"] is True


def test_a_missing_project_maps_to_resource_not_found(live_cli: LiveCli) -> None:
    error = live_cli.err("project", "get", "999999999")

    assert error["code"] == "resource_not_found"
