"""Wire requests and input validation of the project-move, bulk-download and From URL calls.

SupportAPI project moves, ExportsAPI.bulk_download_url, DatasetsAPI.follow_link and
ConnectorDraftsAPI.link_preview, each against the loopback server.
"""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

DOWNLOADS = "/workspaces/1/projects/25654/downloads"
JOB = {
    "id": 90,
    "status": "success",
    "response": {},
    "operation": "x",
    "path": "/x",
    "created_at": "2026-09-01T10:00:00",
    "last_updated_at": "2026-09-01T10:00:05",
}


def _last(server: RecordingServer) -> dict[str, object]:
    return server.requests[-1]


# --- project moves -----------------------------------------------------------------------


async def test_workspace_project_list_reads_the_workspace(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.support.workspace_project_list(5)
    assert (_last(server)["method"], _last(server)["path"]) == (
        "GET",
        "/support/workspaces/5/projects",
    )


async def test_move_check_sends_the_target_as_a_query(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.support.project_move_check(5, 6, 7)
    assert _last(server) == {
        "method": "GET",
        "path": "/support/workspaces/5/projects/6/move",
        "query": {"target_workspace_id": "7"},
        "body": None,
    }


async def test_move_start_sends_target_and_acknowledged_warnings(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.support.project_move_start(5, 6, 7, acknowledged_warnings=["W1"])
    assert _last(server)["path"] == "/support/workspaces/5/projects/6/move"
    assert _last(server)["body"] == {"target_workspace_id": 7, "acknowledged_warnings": ["W1"]}


async def test_move_start_acknowledges_nothing_by_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.support.project_move_start(5, 6, 7)
    assert _last(server)["body"] == {"target_workspace_id": 7, "acknowledged_warnings": []}


async def test_move_get_and_purge_address_the_move(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.support.project_move_get(11)
    assert (_last(server)["method"], _last(server)["path"]) == ("GET", "/support/project-moves/11")
    await client.support.project_move_purge(11)
    assert (_last(server)["method"], _last(server)["path"]) == (
        "POST",
        "/support/project-moves/11/purge",
    )


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


async def test_bulk_download_url_queues_waits_and_returns_the_signed_url(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {DOWNLOADS}"] = (202, {"job": JOB})
    server.answers["GET /jobs/90"] = {"job": {**JOB, "response": {"url": "https://files/x.zip"}}}

    result = await client.exports.bulk_download_url([3, 4], "all", stack=True, views={3: 8})

    assert result == {"url": "https://files/x.zip", "job_id": 90}
    queued = server.requests[0]
    assert queued["path"] == DOWNLOADS
    assert queued["body"] == {
        "resource_ids": [3, 4],
        "views": {"3": 8},
        "file_type": "csv",
        "stack": True,
        "name": "all",
        "numbered": False,
    }


async def test_bulk_download_url_raises_when_the_job_holds_no_url(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {DOWNLOADS}"] = (202, {"job": JOB})
    server.answers["GET /jobs/90"] = {"job": {**JOB, "response": {"rows": 3}}}

    with pytest.raises(ValueError, match="No download URL found in completed job 90"):
        await client.exports.bulk_download_url([3], "all")


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


async def test_follow_link_patches_the_follow_setting(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.datasets.follow_link(7, follow=False)
    assert _last(server)["method"] == "PATCH"
    assert _last(server)["path"] == "/workspaces/1/projects/25654/datasets/7"
    assert _last(server)["body"] == {
        "patch": {"op": "replace", "path": "follow_link", "value": False}
    }


@pytest.mark.parametrize(("dataset_id", "follow"), [(0, True), (-3, True), (7, "yes"), (7, 1)])
async def test_follow_link_refuses_bad_input_before_any_request(
    server: RecordingServer, client: MammothClient, dataset_id: int, follow: object  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.datasets.follow_link(dataset_id, follow=follow)  # type: ignore[arg-type]
    assert server.requests == []


# --- link_preview ------------------------------------------------------------------------


async def test_link_preview_posts_the_url_to_the_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.connector_drafts.link_preview("https://x.test/a.csv")
    assert _last(server)["method"] == "POST"
    assert _last(server)["path"] == "/workspaces/1/projects/25654/connector-drafts/link-preview"
    assert _last(server)["body"] == {"url": "https://x.test/a.csv"}


async def test_link_preview_needs_a_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    client.project_id = None
    with pytest.raises(ValueError, match="project_id must be set"):
        await client.connector_drafts.link_preview("https://x.test/a.csv")
    assert server.requests == []
