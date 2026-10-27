"""Input validation of the project-move, bulk-download and From URL calls.

Each call must refuse bad input before it sends any request; the loopback server only
records that nothing was sent. What the calls send and receive is covered by the live
and integration tests against a real server.
"""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

# --- project moves -----------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, -1])
async def test_move_calls_refuse_a_non_positive_id_before_any_request(
    server: RecordingServer, client: MammothClient, bad: int  # noqa: F811
) -> None:
    support = client.support
    for call in (
        support.workspace_project_list(bad),
        support.project_move_check(bad, 6, 7),
        support.project_move_check(5, bad, 7),
        support.project_move_check(5, 6, bad),
        support.project_move_start(bad, 6, 7),
        support.project_move_start(5, 6, bad),
        support.project_move_get(bad),
        support.project_move_purge(bad),
    ):
        with pytest.raises(MammothValidationError):
            await call
    assert server.requests == []


# --- bulk download -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"resource_ids": []}, "resource_ids"),
        ({"resource_ids": [1], "name": ""}, "name"),
        ({"resource_ids": [1], "name": "x" * 201}, "name"),
        ({"resource_ids": [1], "file_type": "pdf"}, "file_type"),
    ],
)
async def test_bulk_download_url_refuses_bad_input_before_any_request(
    server: RecordingServer,  # noqa: F811
    client: MammothClient,  # noqa: F811
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(MammothValidationError, match=match):
        await client.exports.bulk_download_url(**{"name": "all", **kwargs})  # type: ignore[arg-type]
    assert server.requests == []


# --- follow_link -------------------------------------------------------------------------


@pytest.mark.parametrize(("dataset_id", "follow"), [(0, True), (-3, True), (7, "yes"), (7, 1)])
async def test_follow_link_refuses_bad_input_before_any_request(
    server: RecordingServer, client: MammothClient, dataset_id: int, follow: object  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.datasets.follow_link(dataset_id, follow=follow)  # type: ignore[arg-type]
    assert server.requests == []


# --- link_preview ------------------------------------------------------------------------


async def test_link_preview_needs_a_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    client.project_id = None
    with pytest.raises(ValueError, match="project_id must be set"):
        await client.connector_drafts.link_preview("https://x.test/a.csv")
    assert server.requests == []
