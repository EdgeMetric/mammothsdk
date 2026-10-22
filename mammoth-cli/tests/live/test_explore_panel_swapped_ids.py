"""Live check: ``view explore-panel set DATASET VIEW`` says the ids are the wrong way round.

An agent passed the dataset id where the view id belongs. The refusal names which id
is which and gives the corrected command.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=jupiter \\
        pytest tests/live/test_explore_panel_swapped_ids.py -m live -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_swapped_ids_are_named_with_the_corrected_command(
    live_cli: LiveCli, sales_data: SalesData, tmp_path: Path
) -> None:
    panel = tmp_path / "panel.json"
    panel.write_text(json.dumps({"panel": {"columns": "all"}}), encoding="utf-8")
    argv = (
        "view",
        "explore-panel",
        "set",
        str(sales_data.dataset),
        str(sales_data.view),
        "--input",
        str(panel),
    )
    error = live_cli.err(*argv, project=sales_data.project)
    assert error["code"] == "invalid_argument"
    assert f"mammoth view explore-panel set {sales_data.view} {sales_data.dataset}" in error["hint"]
