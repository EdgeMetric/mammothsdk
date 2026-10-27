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

# Names the query to change and what to keep. "Keep only the first ten rows" alone let the model
# write a fresh query without the column in 2 of 8 runs; this wording kept it in 8 of 8.
_REFINE_INTENT = "Change the current query to return only the first ten rows; keep all else in it."


def test_current_query_is_refined_as_asked(live_cli: LiveCli, sales_data: SalesData) -> None:
    spec = {
        "dataset_id": sales_data.dataset,
        # The server writes against the table of this view; without it, against its default view 4.
        "dataview_id": sales_data.view,
        "current_query": "SELECT *, 'North' AS source_tag FROM input_table",
    }
    generated, _ = live_cli.ok(
        *("ai", "sql", "generate", _REFINE_INTENT, "--input", json.dumps(spec)),
        project=sales_data.project,
    )
    # "North" is only in current_query: the answer keeps it only if the query was refined.
    assert "North" in json.dumps(generated)


def test_a_request_without_a_view_is_refused_before_the_server_is_asked(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """Without ``dataview_id`` the server writes against its default view 4, not the caller's."""
    spec = {"dataset_id": sales_data.dataset, "current_query": "SELECT * FROM input_table"}
    error = live_cli.err(
        *("ai", "sql", "generate", "Keep only the first ten rows", "--input", json.dumps(spec)),
        project=sales_data.project,
    )
    assert "dataview_id" in json.dumps(error)
