"""An export to a new dataset reports the dataset this run wrote, and never invites a re-export.

mammothsdk#488: a ``view export dataset`` read timed out after the export was accepted. The
read was labelled ``not_started`` ("changed nothing, retry"); the retry made a second
dataset, which the server named "Sales 2", and reported the first dataset's id.

Only the network is faked: a small model of the server's export routes behind an
``httpx.MockTransport``. Like mvc-service, it numbers a repeat dataset name
(``Datasource.get_unique_name``) and writes the numbered name back to the new export
trigger's ``DS_NAME`` (``actions_manager.py``, after a run).
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothExportError
from mammoth.view import View, _is_export_dataset_name

VIEW_ID = 1001
SOURCE_DATASET_ID = 500
PROJECT_ID = 2

_VIEW = {
    "id": VIEW_ID,
    "name": "Source view",
    "properties": {
        "columns": [{"display_name": "a", "internal_name": "column_a", "type": "TEXT"}],
    },
}


class _ExportServer:
    """The export, export-list and dataset-list routes of a Mammoth server, in memory."""

    def __init__(self) -> None:
        self.exports: list[dict[str, Any]] = []
        self.datasets: list[dict[str, Any]] = []
        self.timeout_reads_after_post = False
        self._posted = False
        self.client = MammothClient(api_key="k", api_secret="s", workspace_id=1)
        self.client.set_project_id(PROJECT_ID)
        self.client.session = httpx.AsyncClient(
            transport=httpx.MockTransport(self), headers=self.client.session.headers
        )

    def run_export(self, name: str, *, trigger: bool = True) -> int:
        """Write a new dataset from the view, as the server does; return its id."""
        taken = {ds["name"] for ds in self.datasets}
        unique, number = name, 2
        while unique in taken:
            unique, number = f"{name} {number}", number + 1
        dataset_id = 100 + len(self.datasets)
        self.datasets.append(
            {"id": dataset_id, "name": unique, "additional_info": {"DATAVIEW_ID": VIEW_ID}}
        )
        if trigger:
            self.exports.append(
                {
                    "id": len(self.exports) + 1,
                    "status": "executed",
                    "target_properties": {"DS_NAME": unique, "TARGET_DS_ID": dataset_id},
                }
            )
        return dataset_id

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path.endswith("/pipeline/exports"):
            body = json.loads(request.content)
            self.run_export(
                body["target_properties"]["DS_NAME"], trigger=body["trigger_type"] != "none"
            )
            self._posted = True
            return httpx.Response(200, json={"trigger_id": len(self.exports)})
        if self._posted and self.timeout_reads_after_post:
            raise httpx.ReadTimeout("read timed out", request=request)
        if path.endswith("/pipeline/exports"):
            return httpx.Response(200, json={"exports": self.exports, "next": ""})
        if path.endswith("/datasets"):
            return httpx.Response(200, json={"datasets": self.datasets, "next": ""})
        return httpx.Response(404, json={"message": f"unexpected {request.method} {path}"})


@pytest.fixture
def server() -> _ExportServer:
    return _ExportServer()


@pytest.fixture
def view(server: _ExportServer) -> View:
    return View(server.client, _VIEW, SOURCE_DATASET_ID)


async def test_a_rerun_reports_the_dataset_it_wrote_not_the_earlier_one(
    server: _ExportServer, view: View
) -> None:
    first = server.run_export("Sales")

    written = await view.export.to_dataset("Sales")

    assert written != first
    assert written == max(ds["id"] for ds in server.datasets)
    assert {ds["id"]: ds["name"] for ds in server.datasets}[written] == "Sales 2"


async def test_a_rerun_one_off_copy_reports_the_dataset_it_wrote(
    server: _ExportServer, view: View
) -> None:
    first = server.run_export("Copy", trigger=False)

    written = await view.export.to_dataset("Copy", trigger_type="none")

    assert written != first
    assert {ds["id"]: ds["name"] for ds in server.datasets}[written] == "Copy 2"


async def test_a_read_that_fails_after_the_export_is_accepted_says_do_not_export_again(
    server: _ExportServer, view: View
) -> None:
    server.timeout_reads_after_post = True

    with pytest.raises(MammothExportError) as raised:
        await view.export.to_dataset("Sales", timeout=5)

    details = raised.value.details
    assert details["export_pending"] is True
    assert details["dataset_name"] == "Sales"
    assert details["source_view_id"] == VIEW_ID
    assert details["readback_error"]["operation_state"] == "not_started"
    assert "Do not export again" in str(raised.value)
    assert len(server.datasets) == 1  # the export was written once


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Sales", True),
        ("Sales 2", True),
        ("Sales 12", True),
        ("Sales 1", False),
        ("Sales 2b", False),
        ("Sales Q2", False),
        ("Salesforce", False),
        (None, False),
    ],
)
def test_the_server_s_numbered_name_matches_the_requested_one(
    name: str | None, expected: bool
) -> None:
    assert _is_export_dataset_name(name, "Sales") is expected
