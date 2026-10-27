"""Live checks: `dataset download-plan` sizes a bulk download and `dataset download` writes it.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=... \\
        pytest tests/live/test_dataset_download.py -m live -v

The server needs mvc-service's downloads routes (#7203).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from live_harness import LiveCli, SalesData, open_live_service

pytestmark = pytest.mark.live


def _resource_id(sales_data: SalesData) -> int:
    """The scratch dataset's resource id, which the downloads routes take."""
    with open_live_service(sales_data.project) as service:
        listed = service.call(
            "mammoth.api.browse.BrowseAPI.resources_list", project_id=sales_data.project, limit=100
        )
    # A dataset is a "datasource" resource whose ``object_id`` is the dataset id; ``id`` is the
    # resource's own row id, and ``resource_id`` is what the downloads routes take.
    return next(
        row["resource_id"]
        for row in listed["resources"]
        if row["resource_type"] == "datasource" and row["object_id"] == sales_data.dataset
    )


def test_plan_counts_one_dataset(live_cli: LiveCli, sales_data: SalesData) -> None:
    resource = _resource_id(sales_data)
    plan, _ = live_cli.ok(
        *("dataset", "download-plan", "--input", json.dumps({"resource_ids": [resource]})),
        project=sales_data.project,
    )
    assert plan == {"datasets": 1, "stacked_files": 1, "skipped": 0}


def test_download_writes_a_csv_with_the_rows(
    live_cli: LiveCli, sales_data: SalesData, tmp_path: Path
) -> None:
    resource = _resource_id(sales_data)
    target = tmp_path / "sales_out.csv"
    spec = {"resource_ids": [resource], "name": "sales_out", "output_path": str(target)}
    done, _ = live_cli.ok(
        *("dataset", "download", "--input", json.dumps(spec)), project=sales_data.project
    )
    assert done["output_path"] == str(target)
    assert len(target.read_text(encoding="utf-8").splitlines()) > 1
