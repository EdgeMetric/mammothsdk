"""Live checks: ONE board answers "per region" through a filter control, and a built-in
tile can be hidden through ``dashboard canvas save``.

Runs the real CLI in-process against a real tenant (no doubles). The module uploads its
own sales CSV into a scratch project, builds a board on it, and deletes the board.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_dashboard_filter.py -m live -v
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


@pytest.fixture
def board(live_cli: LiveCli, sales_data: SalesData) -> Iterator[int]:
    built, _ = live_cli.ok(
        *("dashboard", "v3", "generate"),
        *_input(
            {"body": {"params": {"intent": "Revenue overview", "dataview_id": sales_data.view}}}
        ),
        project=sales_data.project,
    )
    dashboard = int(built.get("id") or built.get("dashboard_id"))
    yield dashboard
    live_cli.run(
        *("dashboard", "delete", str(dashboard), "--yes", "--confirm", str(dashboard)),
        project=sales_data.project,
    )


def _declared(live_cli: LiveCli, sales_data: SalesData, board: int) -> dict[str, dict[str, Any]]:
    """The board's filters as the CANVAS reports them (not as the filter command does)."""
    doc, _ = live_cli.ok("dashboard", "canvas", "get", str(board), project=sales_data.project)
    return {f["field"]: f for f in doc["canvas"].get("filters") or []}


def test_a_filter_control_is_added_read_back_and_removed(
    live_cli: LiveCli, sales_data: SalesData, board: int
) -> None:
    """Region gets a dropdown on the one board; the canvas shows it; remove takes it off."""
    project = sales_data.project
    added, _ = live_cli.ok(
        *("dashboard", "filter", "add", str(board)),
        *_input({"field": "Region", "control": "dropdown", "label": "Pick a region"}),
        project=project,
    )
    assert any(f["field"] == "Region" for f in added["filters"])

    on_canvas = _declared(live_cli, sales_data, board)
    assert on_canvas["Region"]["control"] == "dropdown"
    assert on_canvas["Region"]["label"] == "Pick a region"
    listed, _ = live_cli.ok("dashboard", "filter", "list", str(board), project=project)
    assert {f["field"] for f in listed["filters"]} == set(on_canvas)

    again, _ = live_cli.ok(
        *("dashboard", "filter", "add", str(board)),
        *_input({"field": "Region", "control": "chips"}),
        project=project,
    )
    assert [f["field"] for f in again["filters"]].count("Region") == 1

    live_cli.ok(
        *("dashboard", "filter", "remove", str(board)),
        *_input({"field": "Region"}),
        project=project,
    )
    assert "Region" not in _declared(live_cli, sales_data, board)
    error = live_cli.err(
        *("dashboard", "filter", "remove", str(board)),
        *_input({"field": "Region"}),
        project=project,
    )
    assert "Region" in error["message"]


def test_a_filter_on_a_column_the_board_does_not_have_is_refused(
    live_cli: LiveCli, sales_data: SalesData, board: int
) -> None:
    error = live_cli.err(
        *("dashboard", "filter", "add", str(board)),
        *_input({"field": "No Such Column"}),
        project=sales_data.project,
    )
    assert "No Such Column" in json.dumps(error)
    assert "No Such Column" not in _declared(live_cli, sales_data, board)


def test_a_built_in_tile_is_hidden_through_canvas_save(
    live_cli: LiveCli, sales_data: SalesData, board: int
) -> None:
    """pages[i].hidden (or hidden on a flat canvas) persists through canvas save."""
    project = sales_data.project
    doc, _ = live_cli.ok("dashboard", "canvas", "get", str(board), project=project)
    canvas = doc["canvas"]
    page = canvas["pages"][0] if canvas.get("pages") else canvas
    page["hidden"] = sorted({*page.get("hidden", []), "summary"})
    live_cli.ok(
        *("dashboard", "canvas", "save", str(board)),
        *_input({"body": {"params": {"canvas": canvas}}}),
        project=project,
    )
    after, _ = live_cli.ok("dashboard", "canvas", "get", str(board), project=project)
    saved = after["canvas"]
    saved_page = saved["pages"][0] if saved.get("pages") else saved
    assert "summary" in saved_page["hidden"]
