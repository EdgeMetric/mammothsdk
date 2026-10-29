"""A lookup after a read of the lookup view needs no ``lookup_dataset_id`` (issue #354).

The real SDK client talks to a loopback server that answers the two dataview reads, so the
foreign view's own columns decide how ``key`` and ``value`` resolve.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest
from mammoth.client import MammothClient

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import parents
from mammoth_cli.services.sdk_service import SdkMammothService

PROJECT = 4300
TARGET_VIEW, TARGET_DATASET = 10, 1
SOURCE_VIEW, SOURCE_DATASET = 20, 77
TARGET = f"/api/v2/workspaces/4/projects/{PROJECT}/datasets/{TARGET_DATASET}/dataviews/10"
SOURCE = f"/api/v2/workspaces/4/projects/{PROJECT}/datasets/{SOURCE_DATASET}/dataviews/20"


def _view(view_id: int, key_internal: str, value_internal: str | None) -> dict[str, Any]:
    """A dataview record whose ``Year key`` column has its own internal name."""
    columns = [{"name": key_internal, "display_name": "Year key", "type": "TEXT"}]
    if value_internal is not None:
        columns.append({"name": value_internal, "display_name": "name", "type": "TEXT"})
    return {"id": view_id, "name": f"view {view_id}", "metadata": columns}


class _Handler(BaseHTTPRequestHandler):
    """Answers the two dataview reads and records every path asked."""

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        self.server.paths.append(path)  # type: ignore[attr-defined]
        answers = {
            TARGET: _view(TARGET_VIEW, "column_target_key", None),
            SOURCE: _view(SOURCE_VIEW, "column_source_key", "column_source_name"),
        }
        body = json.dumps(answers.get(path, {})).encode()
        self.send_response(200 if path in answers else 404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[HTTPServer]:
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    srv.paths = []  # type: ignore[attr-defined]
    threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def service(server: HTTPServer) -> Iterator[SdkMammothService]:
    instance = SdkMammothService(
        ResolvedAuth(
            api_key="key",
            api_secret="secret",
            workspace_id=4,
            base_url="https://unused.invalid/api/v2",
        )
    )
    # The same SDK client, aimed at the loopback server (the service builds its own for https).
    instance._client = MammothClient(
        "key",
        "secret",
        workspace_id=4,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    instance._client.set_project_id(PROJECT)
    try:
        yield instance
    finally:
        instance.close()


def _lookup(service: SdkMammothService, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = service.call_view(
        TARGET_VIEW,
        "lookup",
        dataset_id=TARGET_DATASET,
        build_only=True,
        source="Year key",
        lookup_view_id=SOURCE_VIEW,
        key="Year key",
        value="name",
        new_column="Year Code",
        **extra,
    )
    return result


def test_a_lookup_view_read_earlier_needs_no_lookup_dataset_id(
    service: SdkMammothService, server: HTTPServer
) -> None:
    # What `view list` leaves behind: the lookup view's id and its parent dataset.
    parents.remember_records(
        service._profile, service._workspace_id, [{"id": SOURCE_VIEW, "dataset_id": SOURCE_DATASET}]
    )

    spec = _lookup(service)["task_spec"]["LOOKUP"]

    # `Year key` resolved against each view's own columns, from the remembered parent.
    assert spec["SOURCE"] == "column_target_key"
    assert spec["KEY"] == "column_source_key"
    assert spec["VALUE"] == "column_source_name"
    assert spec["DATAVIEW_ID"] == SOURCE_VIEW
    assert server.paths == [TARGET, SOURCE]  # type: ignore[attr-defined]


def test_an_explicit_lookup_dataset_id_gives_the_same_task(
    service: SdkMammothService,
) -> None:
    spec = _lookup(service, lookup_dataset_id=SOURCE_DATASET)["task_spec"]["LOOKUP"]

    assert spec["KEY"] == "column_source_key"
    assert spec["VALUE"] == "column_source_name"


def test_an_unread_lookup_view_asks_for_its_dataset_and_sends_no_probe(
    service: SdkMammothService, server: HTTPServer
) -> None:
    with pytest.raises(CliError) as raised:
        _lookup(service)

    assert raised.value.code == "missing_argument"
    assert raised.value.details["missing_field"] == "lookup_dataset_id"
    assert server.paths == [TARGET]  # type: ignore[attr-defined]
