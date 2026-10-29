"""Live: a delete is read back and says so, for an automation, a file and a dashboard.

Also covers two behaviours of this branch that unit tests could only fake: a join without
``foreign_dataset_id`` after a read of the foreign view (the parent comes from the cache that
read filled), and ``dataset interpretation confirm`` returning the columns and row count. Runs
the real CLI in-process against a real tenant (no doubles) in a scratch project; every test
deletes what it made.

    pytest tests/live/test_delete_verify.py -m live -v
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli, SalesData, upload_csv

pytestmark = pytest.mark.live

_PREAMBLE = (
    "Data Source,World Development Indicators,\n"
    "\n"
    "Last Updated Date,2026-07-01,\n"
    "\n"
    "Country Name,Country Code,1960,1961,1962\n"
    "Aruba,ABW,54608,55811,56682\n"
    "Andorra,AND,13411,14375,15370\n"
    "Angola,AGO,5357195,5441333,5521400\n"
    "Albania,ALB,1608800,1659800,1711319\n"
    "Argentina,ARG,20481781,20817270,21153042\n"
)
_SETTLE_SECONDS = 180


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def _wait_for(read: Any, done: Any) -> Any:
    deadline = time.monotonic() + _SETTLE_SECONDS
    while True:
        value = read()
        if done(value) or time.monotonic() > deadline:
            return value
        time.sleep(5)


def _state_says_gone(data: dict[str, Any]) -> None:
    """The delete result carries the id in ``deleted`` and a read-back that found it absent."""
    state = data.get("state") or {}
    verify = data.get("verify") or {}
    assert state.get("absent") is True or verify.get("verified") is True, data


def test_an_automation_delete_is_read_back_as_gone(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    task = {
        "task_type": "send_an_alert",
        "details": {
            "alert_type": "email",
            "recipients": ["ops@example.com"],
            "subject": "Delete check",
            "attachments": {"dataview_ids": [sales_data.view]},
        },
    }
    body = {"description": "d", "tasks": [task], "condition_mode": "and"}
    created, _ = live_cli.ok(
        "automation", "create", "Delete check", *_input(body), "--yes", project=sales_data.project
    )
    automation = int(created.get("id") or created["automation"]["id"])
    deleted = live_cli.run(
        "automation", "delete", str(automation), "--yes", project=sales_data.project
    )
    assert "error" not in deleted, deleted
    assert deleted["data"]["deleted"] == [automation]
    _state_says_gone(deleted["data"])


def test_a_file_delete_is_read_back_as_gone(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> None:
    name = f"uqa_delete_verify_{int(time.time())}.csv"
    source = tmp_path / name
    source.write_text("A,B\n1,2\n3,4\n", encoding="utf-8")
    uploaded, _ = live_cli.ok("file", "upload", str(source), "--yes", project=scratch_project)
    dataset = str(uploaded["dataset_id"])
    try:
        listed, _ = live_cli.ok("file", "list", *_input({"names": [name]}), project=scratch_project)
        rows = listed.get("files", listed) if isinstance(listed, dict) else listed
        matches = [row for row in rows if isinstance(row, dict) and row.get("name") == name]
        if not matches:
            pytest.skip("the uploaded file is not listed by name; cannot address it")
        file_id = int(matches[0]["id"])
        deleted = live_cli.run("file", "delete", str(file_id), "--yes", project=scratch_project)
        assert "error" not in deleted, deleted
        assert deleted["data"]["deleted"] == [file_id]
        _state_says_gone(deleted["data"])
    finally:
        live_cli.run(
            *("dataset", "delete", dataset, "--yes", "--confirm", dataset), project=scratch_project
        )


def test_a_dashboard_delete_is_verified(live_cli: LiveCli, sales_data: SalesData) -> None:
    created, _ = live_cli.ok(
        "dashboard",
        "create-blank",
        *_input({"params": {"dataview_id": sales_data.view, "title": "Delete check"}}),
        "--yes",
        project=sales_data.project,
    )
    board = int(created["id"])
    deleted = live_cli.run(
        *("dashboard", "delete", str(board), "--yes", "--confirm", str(board)),
        project=sales_data.project,
    )
    try:
        assert "error" not in deleted, deleted
        assert deleted["data"]["deleted"] == [board]
        assert deleted["data"]["verify"]["verified"] is True, deleted
        listed, _ = live_cli.ok("dashboard", "list", project=sales_data.project)
        assert board not in [d["id"] for d in listed]
    finally:
        if "error" in deleted:
            live_cli.run(
                *("dashboard", "delete", str(board), "--yes", "--confirm", str(board)),
                project=sales_data.project,
            )


def test_a_join_without_the_foreign_parent_uses_the_one_a_view_read_cached(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> None:
    sales = "Key,Units\n" + "".join(f"K{n},{n % 9 + 1}\n" for n in range(10))
    customers = "Key,Tier\n" + "".join(f"K{n},T{n % 3}\n" for n in range(10))
    sales_ds, sales_view = upload_csv(live_cli, scratch_project, tmp_path / "s.csv", sales)
    cust_ds, cust_view = upload_csv(live_cli, scratch_project, tmp_path / "c.csv", customers)
    try:
        # The read pays for parent discovery and the CLI remembers the answer.
        live_cli.ok("view", "get", str(cust_view), project=scratch_project)
        document = {
            "dataset_id": sales_ds,
            "foreign_view": cust_view,
            "join_type": "LEFT",
            "on": [{"left": "Key", "right": "Key"}],
            "select": [{"column": "Tier", "alias": "Customer Tier"}],
        }
        data, _ = live_cli.ok(
            *("view", "transform", "join", str(sales_view), "--input", json.dumps(document)),
            "--yes",
            project=scratch_project,
        )
        assert data["join_check"]["rows_after"] == 10, data
    finally:
        for dataset in (sales_ds, cust_ds):
            live_cli.run(
                *("dataset", "delete", str(dataset), "--yes", "--confirm", str(dataset)),
                project=scratch_project,
            )


def test_interpretation_confirm_returns_columns_and_row_count(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> None:
    source = tmp_path / "uqa_confirm_shape.csv"
    source.write_text(_PREAMBLE, encoding="utf-8")
    uploaded, _ = live_cli.ok("file", "upload", str(source), "--yes", project=scratch_project)
    dataset = str(uploaded["dataset_id"])
    try:
        record = _wait_for(
            lambda: live_cli.ok("dataset", "get", dataset, project=scratch_project)[0],
            lambda r: bool((r.get("additional_info") or {}).get("interpretation")),
        )
        stored = (record.get("additional_info") or {}).get("interpretation") or {}
        suggestions = stored.get("instruction_suggestions") or []
        if not suggestions:
            pytest.skip("the backend read this file without holding it for interpretation")
        confirmed, _ = live_cli.ok(
            *("dataset", "interpretation", "confirm", dataset),
            *_input({"user_instruction": suggestions[0]}),
            project=scratch_project,
        )
        assert confirmed["row_count"] == 5, confirmed
        names = [column["name"] for column in confirmed["columns"]]
        assert names[:2] == ["Country Name", "Country Code"], confirmed
    finally:
        live_cli.run(
            *("dataset", "delete", dataset, "--yes", "--confirm", dataset),
            project=scratch_project,
        )
