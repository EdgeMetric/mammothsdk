"""Live: a file on an SFTP server becomes a dataset (QA ISS-189).

Connector connection create, then ``dataset create`` with ``ds_creation_type: cloud``,
against the QA SFTP server named by ``SFTP_HOST``, ``SFTP_PORT``, ``SFTP_USER``,
``SFTP_PASS``, ``SFTP_IMPORT_PATH`` and ``SFTP_IMPORT_ROWS`` (skips when unset)::

    pytest tests/live/test_sftp_import.py -m live -v
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

_VARS = ("SFTP_HOST", "SFTP_PORT", "SFTP_USER", "SFTP_PASS", "SFTP_IMPORT_PATH", "SFTP_IMPORT_ROWS")


@pytest.fixture(scope="module")
def connection(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[str]:
    """A password SFTP connection to the QA server, deleted at the end."""
    missing = [name for name in _VARS if not os.environ.get(name)]
    if missing:
        pytest.skip(f"SFTP QA server not configured: {', '.join(missing)}")
    config = {
        "domain": os.environ["SFTP_HOST"],
        "port": int(os.environ["SFTP_PORT"]),
        "username": os.environ["SFTP_USER"],
        "password": os.environ["SFTP_PASS"],
    }
    body = tmp_path_factory.mktemp("sftp") / "connection.json"
    body.write_text(json.dumps({"config": config}), encoding="utf-8")
    body.chmod(0o600)
    created, _ = live_cli.ok(
        *("connector", "connection", "create", "sftp", "--input", str(body), "--yes"),
        project=scratch_project,
    )
    key = str(created["identity_key"])
    try:
        yield key
    finally:
        live_cli.run(
            *("connector", "connection", "delete", "sftp", key, "--yes"), project=scratch_project
        )


def test_a_file_on_the_sftp_server_imports_as_a_dataset(
    live_cli: LiveCli, scratch_project: int, connection: str
) -> None:
    name = f"sftp-import-{int(time.time())}"
    spec = {
        "ds_creation_type": "cloud",
        "dataset_spec": {
            "connector_key": "sftp",
            "connection_key": connection,
            "query_properties": {"ds_name": name, "file_path": os.environ["SFTP_IMPORT_PATH"]},
        },
    }

    created, _ = live_cli.ok(
        *("dataset", "create", "--input", json.dumps(spec), "--yes"), project=scratch_project
    )
    dataset = int(created["dataset_id"])
    try:
        view, _ = live_cli.ok("view", "list", str(dataset), project=scratch_project)
        view_id = int(view["dataviews"][0]["id"])
        data, _ = live_cli.ok(
            *("view", "data", "get", str(view_id), "--input", '{"limit": 100}'),
            project=scratch_project,
        )
        assert len(data["data"]) == int(os.environ["SFTP_IMPORT_ROWS"]), data
    finally:
        live_cli.run(
            *("dataset", "delete", str(dataset), "--yes", "--confirm", str(dataset)),
            project=scratch_project,
        )


def test_a_missing_sftp_file_fails_the_create_instead_of_reporting_success(
    live_cli: LiveCli, scratch_project: int, connection: str
) -> None:
    spec = {
        "ds_creation_type": "cloud",
        "dataset_spec": {
            "connector_key": "sftp",
            "connection_key": connection,
            "query_properties": {
                "ds_name": f"sftp-missing-{int(time.time())}",
                "file_path": "/data/no-such-file.csv",
            },
        },
    }

    error = live_cli.err(
        *("dataset", "create", "--input", json.dumps(spec), "--yes"), project=scratch_project
    )

    assert error["code"] == "job_failed", error


def test_a_data_pull_file_that_is_not_a_listed_value_names_the_allowed_ones(
    live_cli: LiveCli, scratch_project: int, connection: str
) -> None:
    spec = {
        "ds_creation_type": "cloud",
        "dataset_spec": {
            "connector_key": "sftp",
            "connection_key": connection,
            "query_properties": {
                "ds_name": "sftp-bad-pull",
                "file_path": os.environ["SFTP_IMPORT_PATH"],
                "data_pull_file": True,
            },
        },
    }

    error = live_cli.err(
        *("dataset", "create", "--input", json.dumps(spec), "--yes"), project=scratch_project
    )

    assert error["code"] == "invalid_argument", error
    assert "Pull same file" in error["message"], error


def test_an_import_scheduled_for_later_reports_scheduled_not_failed(
    live_cli: LiveCli, scratch_project: int, connection: str
) -> None:
    later = (datetime.now() + timedelta(days=2)).isoformat()
    spec = {
        "ds_creation_type": "cloud",
        "dataset_spec": {
            "connector_key": "sftp",
            "connection_key": connection,
            "query_properties": {
                "ds_name": f"sftp-later-{int(time.time())}",
                "file_path": os.environ["SFTP_IMPORT_PATH"],
            },
            "schedule_properties": {
                "schedule_type": "period",
                "first_pull_at": "later",
                "on_refresh_action": "combine",
            },
            "recurrence_info": {"interval": 1, "frequency": "daily", "start_at": later},
        },
    }

    created, _ = live_cli.ok(
        *("dataset", "create", "--input", json.dumps(spec), "--yes"), project=scratch_project
    )

    assert created["status"] == "scheduled", created
    assert created["datasource_config_id"], created
