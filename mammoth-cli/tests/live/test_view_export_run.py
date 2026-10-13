"""Live: a database export returns after the export has run, and ``job wait`` says the same.

A real view in a scratch project exported to a real PostgreSQL the platform can reach. The
destination comes from the environment (no existing live test has one)::

    MAMMOTH_LIVE_PG_HOST  MAMMOTH_LIVE_PG_PORT  MAMMOTH_LIVE_PG_DATABASE
    MAMMOTH_LIVE_PG_USERNAME  MAMMOTH_LIVE_PG_PASSWORD

Run on the box with the test identity (see ``conftest.py``)::

    pytest tests/live/test_view_export_run.py -m live -v
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live

_PG_VARIABLES = (
    "MAMMOTH_LIVE_PG_HOST",
    "MAMMOTH_LIVE_PG_PORT",
    "MAMMOTH_LIVE_PG_DATABASE",
    "MAMMOTH_LIVE_PG_USERNAME",
    "MAMMOTH_LIVE_PG_PASSWORD",
)


@pytest.fixture
def pg_target() -> dict[str, Any]:
    """The reachable PostgreSQL destination, or skip when the box has none configured."""
    missing = [name for name in _PG_VARIABLES if not os.environ.get(name)]
    if missing:
        pytest.skip(f"no live PostgreSQL destination: set {', '.join(missing)}")
    return {
        "host": os.environ["MAMMOTH_LIVE_PG_HOST"],
        "port": int(os.environ["MAMMOTH_LIVE_PG_PORT"]),
        "database": os.environ["MAMMOTH_LIVE_PG_DATABASE"],
        "username": os.environ["MAMMOTH_LIVE_PG_USERNAME"],
        "password": os.environ["MAMMOTH_LIVE_PG_PASSWORD"],
        "replace_table": True,
    }


def _export_postgres(
    live_cli: LiveCli, sales: SalesData, tmp_path: Path, document: dict[str, Any]
) -> dict[str, Any]:
    """Run ``view export postgres`` with the body in a 0600 file (it holds the password)."""
    body = tmp_path / f"pg_{time.time_ns()}.json"
    body.write_text(json.dumps({**document, "dataset_id": sales.dataset}), encoding="utf-8")
    body.chmod(0o600)
    return live_cli.run(
        *("view", "export", "postgres", str(sales.view), "--input", str(body), "--yes"),
        project=sales.project,
    )


def _table() -> str:
    return f"uqa_run_{int(time.time())}"


def test_a_postgres_export_returns_after_the_run_with_its_outcome(
    live_cli: LiveCli, sales_data: SalesData, pg_target: dict[str, Any], tmp_path: Path
) -> None:
    envelope = _export_postgres(live_cli, sales_data, tmp_path, {**pg_target, "table": _table()})

    assert "error" not in envelope, envelope
    export = envelope["data"]["export"]
    assert export["status"] == "ok", export
    assert export["error"] is None
    assert export["ran_at"], export
    stored, _ = live_cli.ok(
        *("view", "export", "list", str(sales_data.view), str(sales_data.dataset)),
        project=sales_data.project,
    )
    (saved,) = [e for e in stored["exports"] if e["id"] == export["id"]]
    assert saved["status"] == "executed" and saved["runnable"] is True


def test_a_postgres_export_that_fails_to_run_is_an_export_failed_error(
    live_cli: LiveCli, sales_data: SalesData, pg_target: dict[str, Any], tmp_path: Path
) -> None:
    refused = {**pg_target, "password": "not-the-password", "table": _table()}

    envelope = _export_postgres(live_cli, sales_data, tmp_path, refused)

    assert envelope.get("error", {}).get("code") == "export_failed", envelope
    assert envelope["error"]["details"]["export"]["error"]


def test_an_export_that_is_not_to_run_now_returns_scheduled_at_once(
    live_cli: LiveCli, sales_data: SalesData, pg_target: dict[str, Any], tmp_path: Path
) -> None:
    document = {**pg_target, "table": _table(), "run_immediately": False}
    started = time.monotonic()

    envelope = _export_postgres(live_cli, sales_data, tmp_path, document)

    assert "error" not in envelope, envelope
    assert envelope["data"]["export"]["status"] == "scheduled", envelope["data"]
    assert time.monotonic() - started < 20


def test_job_wait_on_the_add_job_returns_the_export_run(
    live_cli: LiveCli, sales_data: SalesData, pg_target: dict[str, Any], tmp_path: Path
) -> None:
    added = _export_postgres(live_cli, sales_data, tmp_path, {**pg_target, "table": _table()})
    assert "error" not in added, added

    waited, _ = live_cli.ok("job", "wait", str(added["data"]["job"]["id"]))

    assert waited["export"] == added["data"]["export"]
