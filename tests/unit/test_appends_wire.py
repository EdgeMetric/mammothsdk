"""``client.appends.finish`` and ``append`` against a real local HTTP server.

The pure helpers (``schema_mismatches``, ``refuse_override``) are tested on plain data in
``test_appends.py``. These tests hold the wiring: ``finish`` must read the target's pending
batches off the batch listing and report a held-back file as ``append_failed``, and
``append`` must refuse ``override_target_schema`` before anything is uploaded.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from mammoth.appends import EFFECTS
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

DATASET = "/workspaces/1/projects/25654/datasets/77"
BATCHES = f"{DATASET}/batches"
OLD_BATCH = {"id": 1, "name": "", "source": {"file_name": "first.csv"}}


def _plan(mode: str = "add") -> dict[str, Any]:
    return {
        "target": 77,
        "update_method": {"mode": mode, "effect": EFFECTS[mode]},
        "mode_changed": False,
        "rows_before": 6,
        "batch_ids_before": [1],
        "held_back_before": [],
    }


def _held_back(dataset_id: int, target: int = 77) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "name": "orders.csv",
        "additional_data": {"schema_mismatch": True, "schema_mismatch_target_ds_id": target},
    }


def _script(
    server: RecordingServer,
    *,
    batches: list[dict[str, Any]],
    pending: list[dict[str, Any]],
    mode: str = "combine",
    rows: int = 6,
) -> None:
    server.answers[f"GET {DATASET}"] = {
        "id": 77,
        "status": "ready",
        "stats": {"row_count": rows},
        "configurations": {"schema_properties": {"data_addition_mode": mode}},
    }
    server.answers[f"GET {BATCHES}"] = {"batches": batches, "pending_batches": pending}


async def test_finish_reports_a_file_the_server_held_back_as_append_failed(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _script(server, batches=[OLD_BATCH], pending=[_held_back(900)])

    report = await client.appends.finish(
        _plan(), ["orders.csv"], [900], wait_seconds=5, poll_seconds=0.01
    )

    assert report["append_failed"] is True
    assert report["failure"] == "schema_mismatch"
    assert report["kept_dataset_ids"] == [900]
    assert "900" in report["reason"]
    assert "900" in report["next_step"]
    assert report["rows_added"] == 0
    assert report["batch_ids"] == []
    assert "append_pending" not in report
    # It read the target's batch listing, which is where the flag sits.
    assert any(r["path"] == BATCHES for r in server.requests)


async def test_finish_reads_the_flag_from_the_pending_batches_not_the_dataset(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    # Same dataset read, no flag on the pending batches: nothing landed, nothing failed,
    # so the wait ends pending rather than as a mismatch.
    _script(server, batches=[OLD_BATCH], pending=[])

    report = await client.appends.finish(
        _plan(), ["orders.csv"], [900], wait_seconds=0.2, poll_seconds=0.01
    )

    assert report.get("append_pending") is True
    assert "append_failed" not in report
    assert "failure" not in report


async def test_finish_ignores_a_flag_that_names_another_dataset(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _script(server, batches=[OLD_BATCH], pending=[_held_back(900, target=78)])

    report = await client.appends.finish(
        _plan(), ["orders.csv"], [900], wait_seconds=0.2, poll_seconds=0.01
    )

    assert "append_failed" not in report
    assert report.get("append_pending") is True


async def test_finish_does_not_report_a_held_back_file_the_dataset_already_had(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    plan = {**_plan(), "held_back_before": [900]}
    _script(server, batches=[OLD_BATCH], pending=[_held_back(900)])

    report = await client.appends.finish(
        plan, ["orders.csv"], [900], wait_seconds=0.2, poll_seconds=0.01
    )

    assert "append_failed" not in report


async def test_finish_reports_a_landed_batch_when_nothing_was_held_back(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    new_batch = {"id": 2, "name": "", "source": {"file_name": "orders.csv"}}
    _script(server, batches=[OLD_BATCH, new_batch], pending=[], rows=9)

    report = await client.appends.finish(
        _plan(), ["orders.csv"], [900], wait_seconds=5, poll_seconds=0.01
    )

    assert report["batch_ids"] == [2]
    assert report["rows_added"] == 3
    assert "append_failed" not in report
    assert "append_pending" not in report


async def test_append_refuses_override_target_schema_under_add_before_uploading(
    server: RecordingServer, client: MammothClient, tmp_path: Any  # noqa: F811
) -> None:
    _script(server, batches=[OLD_BATCH], pending=[], mode="combine")
    path = tmp_path / "orders.csv"
    path.write_text("a,b\n1,2\n")

    with pytest.raises(MammothValidationError, match="override_target_schema"):
        await client.appends.append(path, dataset_id=77, override_target_schema=True)

    assert [r["method"] for r in server.requests if r["method"] != "GET"] == []


async def test_finish_never_reports_zero_rows_when_the_batch_is_listed_but_the_count_is_stale(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    new_batch = {"id": 2, "name": "", "source": {"file_name": "orders.csv"}}
    _script(server, batches=[OLD_BATCH, new_batch], pending=[])

    report = await client.appends.finish(
        _plan(), ["orders.csv"], [900], wait_seconds=0.2, poll_seconds=0.01
    )

    # The batch is listed but the dataset still reads 6 rows: pending, not "0 rows added".
    assert report.get("append_pending") is True
    assert report["batch_ids"] == [2]


async def test_finish_keeps_polling_until_the_row_count_moves(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    new_batch = {"id": 2, "name": "", "source": {"file_name": "orders.csv"}}
    _script(server, batches=[OLD_BATCH, new_batch], pending=[])
    waiting = asyncio.create_task(
        client.appends.finish(_plan(), ["orders.csv"], [900], wait_seconds=5, poll_seconds=0.01)
    )
    await asyncio.sleep(0.15)
    _script(server, batches=[OLD_BATCH, new_batch], pending=[], rows=10)

    report = await waiting

    assert report["rows_after"] == 10
    assert report["rows_added"] == 4
    assert "append_pending" not in report
