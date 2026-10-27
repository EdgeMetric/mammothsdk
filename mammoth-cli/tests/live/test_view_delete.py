"""Live check: `view delete` returns only once the view is gone.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=... \\
        pytest tests/live/test_view_delete.py -m live -v

The server answers the delete with 202 and a job; the view stays readable until that job has
run. A command that read the view back on a short timer reported ``delete_not_applied`` for a
delete the server went on to finish (issue #333).
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_a_deleted_view_is_gone_when_the_command_returns(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    project, dataset = sales_data.project, sales_data.dataset
    created, _ = live_cli.ok("view", "create", str(dataset), "--yes", project=project)
    view = str(created["id"])

    live_cli.ok(
        *("view", "delete", view, "--yes", "--confirm", view),
        *("--input", json.dumps({"dataset_id": dataset})),
        project=project,
    )

    # Read straight after the command returned: the view must already be gone.
    error = live_cli.err("view", "get", view, str(dataset), project=project)
    gone = (
        error["code"] == "resource_not_found" or error["details"].get("backend_code") == "4DTVW019"
    )
    assert gone, error
