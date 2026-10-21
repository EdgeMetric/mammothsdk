"""The wire each access, billing, plan, connection and chat-attachment SDK call sends.

Runs against a real loopback HTTP server that records every request (127.0.0.1 only: nothing
here can reach app.mammoth.io), so the method, path, query, JSON body and multipart parts are
checked as sent, not as a mock was called.
"""

from __future__ import annotations

import zipfile
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


def _zip_with(tmp_path: Path, name: str, member: str, pad: int) -> Path:
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member, "x" * pad)
    return path


def _limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink the caps (20 MB for PDF and Word, 50 MB for anything else) to 100 and 400 bytes."""
    monkeypatch.setattr("mammoth.api.dashboards.CHAT_ATTACHMENT_DOCUMENT_MAX_BYTES", 100)
    monkeypatch.setattr("mammoth.api.dashboards.CHAT_ATTACHMENT_MAX_BYTES", 400)


async def test_chat_attachment_refuses_an_empty_file_before_sending(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_bytes(b"")
    with pytest.raises(MammothValidationError, match="empty"):
        await client.dashboards.chat_attachment_upload(9, empty)
    assert server.requests == []


@pytest.mark.parametrize(
    ("content", "name"),
    [
        (b"%PDF-" + b"x" * 95, "a.pdf"),  # exactly the 100-byte document cap
        (b"x" * 150, "notes.txt"),  # text over the document cap, under the overall cap
        (b"\x89PNG\r\n\x1a\n" + b"x" * 142, "photo.png"),  # a picture over the document cap
        (b"x" * 400, "notes.txt"),  # exactly the overall cap
    ],
)
async def test_chat_attachment_sends_a_file_at_or_under_its_limit(
    content: bytes,
    name: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _limits(monkeypatch)
    path = tmp_path / name
    path.write_bytes(content)
    await client.dashboards.chat_attachment_upload(9, path)
    assert [r["method"] for r in server.requests] == ["POST"]


async def test_chat_attachment_sends_a_big_zip_that_is_not_a_word_file(
    server: RecordingServer,
    client: MammothClient,
    tmp_path: Path,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The server decides about other zips (a workbook is refused there, by its content)."""
    _limits(monkeypatch)
    other = _zip_with(tmp_path, "book.zip", "xl/sheet.xml", 150)
    assert other.stat().st_size > 100
    await client.dashboards.chat_attachment_upload(9, other)
    assert len(server.requests) == 1


@pytest.mark.parametrize("kind", ["pdf", "docx"])
async def test_chat_attachment_refuses_a_pdf_or_word_file_over_the_document_cap(
    kind: str,
    server: RecordingServer,
    client: MammothClient,
    tmp_path: Path,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _limits(monkeypatch)
    if kind == "pdf":
        path = tmp_path / "a.pdf"
        path.write_bytes(b"%PDF-" + b"x" * 96)  # one byte over
    else:
        path = _zip_with(tmp_path, "a.docx", "word/document.xml", 150)
    assert 100 < path.stat().st_size <= 400
    with pytest.raises(MammothValidationError, match="PDF or Word"):
        await client.dashboards.chat_attachment_upload(9, path)
    assert server.requests == []


@pytest.mark.parametrize("name", ["notes.txt", "photo.png"])
async def test_chat_attachment_refuses_any_file_over_the_overall_cap(
    name: str,
    server: RecordingServer,
    client: MammothClient,
    tmp_path: Path,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _limits(monkeypatch)
    path = tmp_path / name
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 393 if name.endswith("png") else b"x" * 401)
    with pytest.raises(MammothValidationError, match="50 MB"):
        await client.dashboards.chat_attachment_upload(9, path)
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
    await client.support.plan_update_entitlements(
        7, {"dashboardBranding": "no_branding", "maxProjects": 5}
    )

    assert server.requests == [
        {
            "method": "PUT",
            "path": "/subscription/plans/7/entitlements",
            "query": {},
            "body": {"values": {"dashboardBranding": "no_branding", "maxProjects": 5}},
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
