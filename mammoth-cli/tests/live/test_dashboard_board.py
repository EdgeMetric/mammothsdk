"""Live: a generated board is waited for, listed by project, and answers an RLS value search.

Replaces the fake-socket realcode tests ``test_generated_dashboard_async_result_waits_for_job``,
``test_dashboard_list_nullable_project_query_full_stack`` and
``test_generated_dashboard_path_query_full_stack``. One board is generated for the module (it is
the only paid call) and deleted at the end.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


@pytest.fixture(scope="module")
def generated(live_cli: LiveCli, sales_data: SalesData) -> Iterator[dict[str, Any]]:
    built, _ = live_cli.ok(
        *("dashboard", "v3", "generate"),
        *_input(
            {"body": {"params": {"intent": "Revenue overview", "dataview_id": sales_data.view}}}
        ),
        project=sales_data.project,
    )
    yield built
    board = int(built["id"])
    live_cli.run(
        *("dashboard", "delete", str(board), "--yes", "--confirm", str(board)),
        project=sales_data.project,
    )


def test_a_generated_board_is_waited_for_checked_and_read_back(generated: dict[str, Any]) -> None:
    assert generated["id"]
    assert generated["verify"]["verified"] is True and generated["verify"]["state"] == "done"
    assert generated["deliverable_check"]["checked"] is True
    assert generated["state"]["kind"] == "object"
    assert generated["state"]["read_by"] == f"dashboard.get {generated['id']}"
    assert generated["state"]["object"]["id"] == generated["id"]


def test_dashboard_list_by_project_lists_only_that_projects_boards(
    live_cli: LiveCli, sales_data: SalesData, generated: dict[str, Any]
) -> None:
    data, _ = live_cli.ok("dashboard", "list", project=sales_data.project)
    assert generated["id"] in [d["id"] for d in data]

    empty, _ = live_cli.ok("project", "create", f"uqa-live-empty-{int(time.time())}", "--yes")
    other = int(empty["id"])
    try:
        elsewhere, _ = live_cli.ok("dashboard", "list", project=other)
    finally:
        live_cli.run("project", "delete", str(other), "--yes", "--confirm", str(other))

    assert elsewhere == []


def test_the_rls_value_search_returns_the_values_the_column_holds(
    live_cli: LiveCli, sales_data: SalesData, generated: dict[str, Any]
) -> None:
    data, _ = live_cli.ok(
        *("dashboard", "rls", "value", "list", str(generated["id"])),
        *_input({"column": "Region", "search": "Nor"}),
        project=sales_data.project,
    )

    assert data["values"] == ["North"]
