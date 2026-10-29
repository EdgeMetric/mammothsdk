"""``DatasetsAPI.list`` / ``list_all`` ask the server for named dataset ids only.

The datasets list route filters on a comma-separated ``id`` query parameter
(mvc-service ``apiv2/apiv2/datasets/controller.py`` ``get_datasets``, ``id: DatasetIdsType``).
"""

from __future__ import annotations

from mammoth.client import MammothClient

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

LISTING = "/workspaces/1/projects/25654/datasets"


async def test_list_without_ids_sends_no_id_filter(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {LISTING}"] = {"datasets": []}

    await client.datasets.list()

    assert "id" not in server.requests[-1]["query"]


async def test_list_with_ids_sends_one_comma_separated_id_filter(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {LISTING}"] = {"datasets": [{"id": 7}]}

    await client.datasets.list(ids=[7, 9])

    assert server.requests[-1]["query"]["id"] == "7,9"


async def test_list_all_with_one_id_is_a_single_small_request(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {LISTING}"] = {"datasets": []}

    result = await client.datasets.list_all(ids=[7])

    assert result["datasets"] == []
    assert len(server.requests) == 1
    assert server.requests[0]["query"]["id"] == "7"
