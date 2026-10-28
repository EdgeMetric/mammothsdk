"""Live: ``dataset file-settings update`` takes one field alone, without a delimiter.

pytest tests/live/test_file_settings_single_field.py -m live -v
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_file_settings_update_accepts_a_single_field(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """A lone ``initial_skip_count`` is accepted; the old rule demanded a delimiter too."""
    live_cli.ok(
        "dataset",
        "file-settings",
        "update",
        str(sales_data.dataset),
        "--input",
        json.dumps({"initial_skip_count": 0}),
        "--yes",
        project=sales_data.project,
    )
