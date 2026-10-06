"""Live checks: ``view optimize`` finds the view's dataset itself and refuses a wrong one.

An agent passed the right view (5224) with the wrong dataset (5214) and the API
answered "Invalid hierarchy". The dataset is now optional; a given one is checked
against the view's real parent before the write.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=koyal \\
        pytest tests/live/test_view_optimize_parent.py -m live -v
"""

from __future__ import annotations

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_one_id_is_enough(live_cli: LiveCli, sales_data: SalesData) -> None:
    data, _ = live_cli.ok(
        "view", "optimize", str(sales_data.view), "--yes", project=sales_data.project
    )
    assert "applied" in data


def test_the_right_dataset_still_works(live_cli: LiveCli, sales_data: SalesData) -> None:
    argv = ("view", "optimize", str(sales_data.view), str(sales_data.dataset), "--yes")
    data, _ = live_cli.ok(*argv, project=sales_data.project)
    assert "applied" in data


def test_a_wrong_dataset_is_refused_naming_the_real_one(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    wrong = sales_data.dataset + 1
    argv = ("view", "optimize", str(sales_data.view), str(wrong), "--yes")
    error = live_cli.err(*argv, project=sales_data.project)
    assert (
        error["message"]
        == f"view {sales_data.view} belongs to dataset {sales_data.dataset}, not {wrong}"
    )
