"""A `view export dataset` read that fails after the export is accepted is pending, not a retry.

mammothsdk#488: the export POST was accepted, a read after it timed out, and the CLI said
"Retry the read once; it changed nothing". The retry wrote a second dataset. The real SDK
runs here against a server faked at the HTTP boundary only.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from mammoth.client import MammothClient
from mammoth.exceptions import MammothError
from mammoth.view import View

from mammoth_cli.commands.view.export_dataset import _pending_dataset_export
from mammoth_cli.services.mapping import map_sdk_exception

VIEW_ID = 1001
PROJECT_ID = 2


class _AcceptThenTimeOut:
    """Accept the export, then time out every read after it, as on 23 Nov."""

    def __init__(self) -> None:
        self.posted = False

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/pipeline/exports"):
            self.posted = True
            return httpx.Response(200, json={"trigger_id": 1})
        if self.posted:
            raise httpx.ReadTimeout("read timed out", request=request)
        if request.url.path.endswith("/pipeline/exports"):
            return httpx.Response(200, json={"exports": [], "next": ""})
        if request.url.path.endswith("/datasets"):
            # The datasets earlier exports of this view made, read before this one is sent.
            return httpx.Response(200, json={"datasets": [], "total": 0})
        return httpx.Response(404, json={"message": json.dumps(request.url.path)})


@pytest.fixture
def view() -> View:
    client = MammothClient(api_key="k", api_secret="s", workspace_id=1)
    client.set_project_id(PROJECT_ID)
    client.session = httpx.AsyncClient(
        transport=httpx.MockTransport(_AcceptThenTimeOut()), headers=client.session.headers
    )
    columns = [{"display_name": "a", "internal_name": "column_a", "type": "TEXT"}]
    return View(client, {"id": VIEW_ID, "name": "v", "properties": {"columns": columns}}, 500)


def test_a_timed_out_read_after_the_export_never_says_retry(view: View) -> None:
    with pytest.raises(MammothError) as raised:
        asyncio.run(view.export.to_dataset("Sales", timeout=5))

    mapped = map_sdk_exception(raised.value, project_id=PROJECT_ID)

    assert mapped.code != "retryable"
    assert "changed nothing" not in (mapped.hint or "")
    assert mapped.details.get("export_pending") is True
    pending = _pending_dataset_export(mapped, VIEW_ID, PROJECT_ID)
    assert pending["status"] == "pending"
    assert "Do not export again" in pending["note"]
    assert pending["next"] == f"mammoth dataset find Sales --project {PROJECT_ID}"
