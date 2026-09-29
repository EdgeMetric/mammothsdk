"""Live check that a join's match rate covers the whole view, not its first page.

UQA-RT4-07: a LEFT join whose first data page all matched reported
``match_rate: 1.0`` on a view where 26% of the keys found no match, and the
agent told the user every row matched. The module uploads a sales file whose
first half matches the customer file and whose second half does not::

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_join_check.py -m live -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

_MATCHED = 600
_UNMATCHED = 600


def _upload(live_cli: LiveCli, project: int, path: Path, text: str) -> tuple[int, int]:
    path.write_text(text, encoding="utf-8")
    uploaded, _ = live_cli.ok("file", "upload", str(path), "--yes", project=project)
    dataset = int(uploaded["dataset_id"])
    listed, _ = live_cli.ok("view", "list", str(dataset), project=project)
    if listed["dataviews"]:
        return dataset, int(listed["dataviews"][0]["id"])
    created, _ = live_cli.ok("view", "create", str(dataset), "--yes", project=project)
    return dataset, int(created["id"])


def test_a_join_counts_unmatched_rows_beyond_the_first_page(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> None:
    customers = "Key,Tier\n" + "".join(f"K{n},T{n % 3}\n" for n in range(_MATCHED))
    sales = "Key,Units\n" + "".join(f"K{n},{n % 9 + 1}\n" for n in range(_MATCHED + _UNMATCHED))
    sales_ds, sales_view = _upload(live_cli, scratch_project, tmp_path / "sales.csv", sales)
    cust_ds, cust_view = _upload(live_cli, scratch_project, tmp_path / "customers.csv", customers)

    document = {
        "dataset_id": sales_ds,
        "foreign_dataset_id": cust_ds,
        "foreign_view": cust_view,
        "join_type": "LEFT",
        "on": [{"left": "Key", "right": "Key"}],
        "select": [{"column": "Tier", "alias": "Customer Tier"}],
    }
    data, _ = live_cli.ok(
        "view",
        "transform",
        "join",
        str(sales_view),
        "--input",
        json.dumps(document),
        "--yes",
        project=scratch_project,
    )

    check = data["join_check"]
    assert check["rows_after"] == _MATCHED + _UNMATCHED, check
    assert check["unmatched_rows"] == _UNMATCHED, check
    assert check["match_rate"] == 0.5, check
