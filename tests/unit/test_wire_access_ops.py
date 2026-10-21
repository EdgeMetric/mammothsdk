"""The wire each access, billing, plan, connection and chat-attachment SDK call sends.

Runs against a real loopback HTTP server that records every request (127.0.0.1 only: nothing
here can reach app.mammoth.io), so the method, path, query, JSON body and multipart parts are
checked as sent, not as a mock was called.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401


async def test_chat_attachment_upload_sends_one_multipart_file_part(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    picture = tmp_path / "chart shot.png"
    picture.write_bytes(b"\x89PNG-bytes")
    server.answers["POST /dashboards/9/chat/attachments"] = {"ref": "att:abc", "kind": "image"}

    result = await client.dashboards.chat_attachment_upload(9, picture)

    assert result == {"ref": "att:abc", "kind": "image"}
    assert [(r["method"], r["path"]) for r in server.requests] == [
        ("POST", "/dashboards/9/chat/attachments")
    ]
    content_type = str(server.wire[0]["content_type"])
    assert content_type.startswith("multipart/form-data; boundary=")
    raw = bytes(server.wire[0]["raw"])  # type: ignore[arg-type]
    assert b'name="file"' in raw
    assert b'filename="chart shot.png"' in raw
    assert b"Content-Type: application/octet-stream" in raw
    assert b"\x89PNG-bytes" in raw


async def test_chat_attachment_refuses_an_empty_and_an_oversized_file_before_sending(
    server: RecordingServer,
    client: MammothClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,  # noqa: F811
) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_bytes(b"")
    with pytest.raises(MammothValidationError, match="empty"):
        await client.dashboards.chat_attachment_upload(9, empty)

    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * 11)
    monkeypatch.setattr("mammoth.api.dashboards.CHAT_ATTACHMENT_MAX_BYTES", 10)
    with pytest.raises(MammothValidationError, match="20 MB|over"):
        await client.dashboards.chat_attachment_upload(9, big)

    assert server.requests == []


async def test_grant_give_posts_emails_level_and_items(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    items = [{"project_id": 3}]
    await client.agents.access_grant_give(["a@example.com"], "ask", items)

    assert server.requests == [
        {
            "method": "POST",
            "path": "/agents/access/grants",
            "query": {},
            "body": {"emails": ["a@example.com"], "level": "ask", "items": items},
        }
    ]


async def test_grant_update_refuses_empty_items_before_sending(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="project"):
        await client.agents.access_grant_update(4, items=[])
    assert server.requests == []


async def test_held_change_cancel_posts_to_the_workspace_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /workspaces/1/subscription/held-change/cancel"] = {
        "cancelled": False,
        "landed": True,
    }

    result = await client.billing.stripe_held_change_cancel()

    assert result == {"cancelled": False, "landed": True}
    assert [(r["method"], r["path"], r["body"]) for r in server.requests] == [
        ("POST", "/workspaces/1/subscription/held-change/cancel", None)
    ]


async def test_update_entitlements_puts_the_values_under_values(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.support.plan_update_entitlements(7, {"dashboardBranding": True, "maxProjects": 5})

    assert server.requests == [
        {
            "method": "PUT",
            "path": "/subscription/plans/7/entitlements",
            "query": {},
            "body": {"values": {"dashboardBranding": True, "maxProjects": 5}},
        }
    ]


async def test_task_preview_cancel_deletes_the_preview_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[
        "DELETE /workspaces/1/projects/25654/datasets/8/dataviews/3/pipeline/task_preview/55"
    ] = (
        204,
        None,
    )

    await client.pipeline.preview_cancel(3, 55, dataset_id=8)

    assert [(r["method"], r["path"]) for r in server.requests] == [
        ("DELETE", "/workspaces/1/projects/25654/datasets/8/dataviews/3/pipeline/task_preview/55")
    ]


async def test_connection_test_encodes_the_connection_key(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.connectors.test_connection("my db/prod?x")

    assert [(r["method"], r["path"]) for r in server.requests] == [
        ("PATCH", "/workspaces/1/projects/25654/connections/my%20db%2Fprod%3Fx/test")
    ]


async def test_turn_rating_and_feedback_encode_session_and_turn_ids(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.agents.turn_rate("s/1", "t 2", "up", comment="good")
    await client.agents.turn_feedback_list("s/1")

    assert [(r["method"], r["path"], r["body"]) for r in server.requests] == [
        (
            "POST",
            "/agents/sessions/s%2F1/turns/t%202/feedback",
            {"rating": "up", "comment": "good"},
        ),
        ("GET", "/agents/sessions/s%2F1/feedback", None),
    ]
