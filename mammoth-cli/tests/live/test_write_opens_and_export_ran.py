"""Live: a write's envelope names the object it opens, and an export add says if it ran.

Real datasets in a scratch project. Run on the box with the test identity (see
``conftest.py``)::

    pytest tests/live/test_write_opens_and_export_ran.py -m live -v
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest
from live_harness import LiveCli, SalesData, upload_csv

pytestmark = pytest.mark.live

_CSV = "a,b\n1,2\n3,4\n"


def _opens(live_cli: LiveCli, project: int, *args: str) -> list[dict[str, Any]]:
    envelope = live_cli.run(*args, "--yes", project=project)
    assert "error" not in envelope, envelope
    opens: list[dict[str, Any]] = envelope["meta"]["opens"]
    return opens


def test_an_edit_opens_the_object_it_changed_and_a_create_the_one_it_made(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> None:
    stamp = int(time.time())
    dataset, _ = upload_csv(
        live_cli, scratch_project, tmp_path_factory.mktemp("opens") / f"o_{stamp}.csv", _CSV
    )
    rename = ("dataset", "rename", str(dataset), "--input", json.dumps({"name": f"R {stamp}"}))

    (edited,) = _opens(live_cli, scratch_project, *rename)
    (made,) = _opens(live_cli, scratch_project, "view", "create", str(dataset))

    assert (edited["kind"], edited["id"], edited["created"]) == ("dataset", dataset, False)
    assert edited["url"].endswith(f"/projects/{scratch_project}/datasets/{dataset}")
    assert (made["kind"], made["created"]) == ("view", True)
    assert made["url"].endswith(f"/projects/{scratch_project}/views/{made['id']}")


def test_a_read_has_no_opens(live_cli: LiveCli, sales_data: SalesData) -> None:
    _, meta = live_cli.ok("view", "get", str(sales_data.view), project=sales_data.project)

    assert "opens" not in meta


def test_an_export_that_queued_nothing_says_it_has_not_run(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    spec = {
        "DATAVIEW_ID": sales_data.view,
        "handler_type": "postgres",
        "trigger_type": "none",
        "run_immediately": False,
        "target_properties": {
            "host": "localhost",
            "port": 5432,
            "database": "nodb",
            "table": f"t_{int(time.time())}",
            "username": "u",
            "password": "p",
        },
    }
    envelope = live_cli.run(
        *("view", "export", "create", str(sales_data.view), "--yes"),
        *("--input", json.dumps({"export_spec": spec, "dataset_id": sales_data.dataset})),
        project=sales_data.project,
    )

    assert "error" not in envelope, envelope
    assert envelope["data"]["ran"] is False
    assert "pipeline" in envelope["data"]["hint"]
