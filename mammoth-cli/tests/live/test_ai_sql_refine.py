"""Live check: `ai sql generate` takes `current_query` and refines it instead of writing anew.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=... \\
        pytest tests/live/test_ai_sql_refine.py -m live -v

Needs the AI add-on and a server with mvc-service #6889.
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_current_query_is_refined_as_asked(live_cli: LiveCli, sales_data: SalesData) -> None:
    spec = {"dataset_id": sales_data.dataset, "current_query": "SELECT * FROM input_table"}
    generated, _ = live_cli.ok(
        *("ai", "sql", "generate", "Keep only the first 7 rows", "--input", json.dumps(spec)),
        project=sales_data.project,
    )
    assert "7" in json.dumps(generated)
