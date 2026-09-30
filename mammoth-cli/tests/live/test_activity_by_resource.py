"""Live checks: asking the activity log about one view finds that view's entries.

QA (UQA-RT17-06): "who changed this view today?" got a confident "no changes" on a view
edited five times that day. The log keys each entry by ``dataview_<id>``; the agent
passed the bare id ``3882``, the filter matched nothing and nothing said why.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_activity_by_resource.py -m live -v
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def test_a_bare_id_is_refused_with_the_form_the_log_uses(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    error = live_cli.err(
        "activity", "list", "--input", json.dumps({"resource_id": str(sales_data.view)})
    )

    assert error["code"] == "invalid_argument"
    assert f"dataview_{sales_data.view}" in error["message"]
    retry = json.dumps({"resource_id": f"dataview_{sales_data.view}"})
    assert f"mammoth activity list --input '{retry}'" in error["recovery_commands"]


def test_the_view_form_finds_the_views_own_entries(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    resource = f"dataview_{sales_data.view}"

    found, _ = live_cli.ok("activity", "list", "--input", json.dumps({"resource_id": resource}))

    assert found["activity_logs"], f"no activity for {resource}"
    assert {row["primary_object"]["resource_id"] for row in found["activity_logs"]} == {resource}
