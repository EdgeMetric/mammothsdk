"""Live checks: ``view variants create`` makes one filtered view per value in one call.

Runs the real CLI in-process against a real tenant (no doubles). The module's sales CSV
has four regions with 14 rows each (the blank-region rows are 4 of the 60).

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_view_variants.py -m live -v
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live

_ROWS_PER_REGION = 14


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def _row_count(live_cli: LiveCli, sales_data: SalesData, view_id: int) -> int:
    view, _ = live_cli.ok("view", "get", str(view_id), project=sales_data.project)
    return int(view["row_count"])


def test_each_value_gets_its_own_filtered_view(live_cli: LiveCli, sales_data: SalesData) -> None:
    result, _ = live_cli.ok(
        *("view", "variants", "create", str(sales_data.dataset)),
        *_input(
            {
                "from_view": sales_data.view,
                "column": "Region",
                "values": ["East", "West"],
                "name_template": "Sales - {value}",
            }
        ),
        project=sales_data.project,
    )
    assert [entry["value"] for entry in result["variants"]] == ["East", "West"]
    assert [entry["name"] for entry in result["variants"]] == ["Sales - East", "Sales - West"]
    assert len(set(result["view_ids"])) == 2
    for view_id in result["view_ids"]:
        assert _row_count(live_cli, sales_data, view_id) == _ROWS_PER_REGION
    assert _row_count(live_cli, sales_data, sales_data.view) == 60


def test_an_unknown_column_is_refused_before_any_view_is_created(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    before, _ = live_cli.ok("view", "list", str(sales_data.dataset), project=sales_data.project)
    error = live_cli.err(
        *("view", "variants", "create", str(sales_data.dataset)),
        *_input({"from_view": sales_data.view, "column": "No Such Column", "values": ["x"]}),
        project=sales_data.project,
    )
    assert "No Such Column" in error["message"]
    after, _ = live_cli.ok("view", "list", str(sales_data.dataset), project=sales_data.project)
    assert len(after["dataviews"]) == len(before["dataviews"])
