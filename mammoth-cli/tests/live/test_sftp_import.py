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
        "host": os.environ["SFTP_HOST"],
        "port": int(os.environ["SFTP_PORT"]),
        "username": os.environ["SFTP_USER"],
        "password": os.environ["SFTP_PASS"],
        "ssh_auth_type": "password",
    }
    body = tmp_path_factory.mktemp("sftp") / "connection.json"
    body.write_text(json.dumps({"config": config}), encoding="utf-8")
    body.chmod(0o600)
    created, _ = live_cli.ok(
        *("connector", "connection", "create", "sftp", "--input", str(body), "--yes"),
        project=scratch_project,
    )
    key = str(created["connection_key"])
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
