"""CollectionsAPI wire requests held to the pinned spec.

Spec operations: GetCollection, GetCollectionByUrl, CreateCollection, UpdateCollection,
DeleteCollection, AddDashboards, RemoveDashboard, ShareCollection, RemoveMember,
CollectionsForDashboard, CollectionActivity, PipelineChanges, UploadFile.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec


def _only(server: RecordingServer) -> dict[str, Any]:
    assert len(server.requests) == 1
    return server.requests[0]


def _declared(path: str, method: str) -> set[str]:
    op = spec()["paths"][path][method]
    return {p["name"] for p in op.get("parameters", []) if p["in"] == "query"}


# --- get / get_by_url ---------------------------------------------------------------------------


async def test_get_reads_one_collection(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /collections/5"] = {"id": 5}
    assert await client.collections.get(5) == {"id": 5}
    assert _only(server) == {"method": "GET", "path": "/collections/5", "query": {}, "body": None}


async def test_get_by_url_percent_encodes_the_slug_and_drops_empty_filters(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.get_by_url("my pack/2")
    await client.collections.get_by_url("slug", t="tok", email="a@x.io")
    first, second = server.requests
    assert first["path"] == "/collections/url/my%20pack%2F2" and first["query"] == {}
    assert second["path"] == "/collections/url/slug"
    assert second["query"] == {"t": "tok", "email": "a@x.io"}


@pytest.mark.parametrize("url", ["", None, 5])
async def test_get_by_url_needs_a_string(
    url: Any, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`url` must be a non-empty string"):
        await client.collections.get_by_url(url)
    assert server.requests == []


# --- create -----------------------------------------------------------------------------------


async def test_create_defaults_project_from_the_client_and_sends_the_spec_fields(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.create("Pack")
    assert _only(server)["body"] == {
        "project_id": 25654,
        "name": "Pack",
        "description": None,
        "dashboard_ids": [],
    }
    assert set(schema("CreateCollectionPayload")["required"]) <= set(_only(server)["body"])


async def test_create_takes_an_explicit_project_over_the_client_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.create("Pack", project_id=3, description="d", dashboard_ids=[1])
    assert _only(server)["body"] == {
        "project_id": 3,
        "name": "Pack",
        "description": "d",
        "dashboard_ids": [1],
    }


async def test_create_without_any_project_fails_before_a_request(server: RecordingServer) -> None:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.project_id = None  # type: ignore[assignment]
    with pytest.raises(ValueError, match="project_id must be set"):
        await c.collections.create("Pack")
    assert server.requests == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": ""}, "`name` must be 1 to 120 characters"),
        ({"name": "x" * 121}, "`name` must be 1 to 120 characters"),
        ({"name": None}, "`name` must be 1 to 120 characters"),
        ({"name": "ok", "project_id": 0}, "`project_id` must be a positive integer, got 0"),
        ({"name": "ok", "dashboard_ids": [1, 0]}, "`dashboard_ids` must be a positive integer"),
        ({"name": "ok", "dashboard_ids": [True]}, "`dashboard_ids` must be a positive integer"),
    ],
)
async def test_create_validates_before_any_request(
    kwargs: dict[str, Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.collections.create(**kwargs)
    assert server.requests == []


async def test_create_accepts_the_maximum_name_length(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.create("x" * 120)
    assert len(_only(server)["body"]["name"]) == 120


# --- update -----------------------------------------------------------------------------------


async def test_update_sends_only_the_fields_that_were_set(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.update(
        4,
        name="New",
        description="",
        order=[3, 1],
        tab_labels={"3": "Tab", "1": None},
        automation_id=9,
        unlink_automation=True,
    )
    assert _only(server) == {
        "method": "PATCH",
        "path": "/collections/4",
        "query": {},
        "body": {
            "name": "New",
            "description": "",
            "order": [3, 1],
            "tab_labels": {"3": "Tab", "1": None},
            "automation_id": 9,
            "unlink_automation": True,
        },
    }
    assert set(_only(server)["body"]) <= set(schema("UpdateCollectionPayload")["properties"])


async def test_update_with_one_field_sends_just_that_field(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.update(4, name="Only")
    assert _only(server)["body"] == {"name": "Only"}


async def test_update_unlink_automation_alone_is_a_valid_change(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.update(4, unlink_automation=True)
    assert _only(server)["body"] == {"unlink_automation": True}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({}, "Give at least one field to change"),
        ({"name": ""}, "`name` must be 1 to 120 characters"),
        ({"name": "x" * 121}, "`name` must be 1 to 120 characters"),
        ({"order": [1, -1]}, "`order` must be a positive integer, got -1"),
        ({"automation_id": 0}, "`automation_id` must be a positive integer, got 0"),
    ],
)
async def test_update_validates_before_any_request(
    kwargs: dict[str, Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.collections.update(4, **kwargs)
    assert server.requests == []


# --- delete / dashboards / members ------------------------------------------------------------


async def test_delete_returns_a_confirmation_the_server_does_not_send(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    result = await client.collections.delete(8)
    assert result == {"collection_id": 8, "deleted": True}
    assert _only(server)["method"] == "DELETE" and _only(server)["path"] == "/collections/8"


async def test_add_dashboards_posts_ids_and_the_notify_flag(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.add_dashboards(2, [5, 6])
    await client.collections.add_dashboards(2, [7], notify=True)
    assert [r["body"] for r in server.requests] == [
        {"dashboard_ids": [5, 6], "notify": False},
        {"dashboard_ids": [7], "notify": True},
    ]
    assert all(
        r["method"] == "POST" and r["path"] == "/collections/2/dashboards" for r in server.requests
    )


@pytest.mark.parametrize(
    ("ids", "message"),
    [
        ([], "`dashboard_ids` must be a non-empty list"),
        ([1, 0], "`dashboard_ids` must be a positive integer, got 0"),
    ],
)
async def test_add_dashboards_validates_before_any_request(
    ids: list[int], message: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.collections.add_dashboards(2, ids)
    assert server.requests == []


async def test_remove_dashboard_deletes_the_membership_and_confirms(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    result = await client.collections.remove_dashboard(2, 5)
    assert result == {"collection_id": 2, "dashboard_id": 5, "removed": True}
    assert (_only(server)["method"], _only(server)["path"]) == (
        "DELETE",
        "/collections/2/dashboards/5",
    )


async def test_remove_dashboard_validates_both_ids(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`collection_id` must be a positive"):
        await client.collections.remove_dashboard(0, 5)
    with pytest.raises(MammothValidationError, match="`dashboard_id` must be a positive"):
        await client.collections.remove_dashboard(2, 0)
    assert server.requests == []


async def test_share_posts_the_emails(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.share(2, ["a@x.io"])
    assert _only(server) == {
        "method": "POST",
        "path": "/collections/2/share",
        "query": {},
        "body": {"emails": ["a@x.io"]},
    }


async def test_share_accepts_200_emails_but_not_201_or_none(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.share(2, [f"u{i}@x.io" for i in range(200)])
    assert len(_only(server)["body"]["emails"]) == 200
    server.requests.clear()
    for emails in ([], [f"u{i}@x.io" for i in range(201)]):
        with pytest.raises(MammothValidationError, match="`emails` must be 1 to 200"):
            await client.collections.share(2, emails)
    assert server.requests == []


async def test_remove_member_sends_the_email_query_the_spec_requires(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    result = await client.collections.remove_member(2, "a@x.io")
    assert result == {"collection_id": 2, "email": "a@x.io", "removed": True}
    assert _only(server)["method"] == "DELETE"
    assert _only(server)["path"] == "/collections/2/members"
    assert _only(server)["query"] == {"email": "a@x.io"}
    assert "email" in _declared("/collections/{collection_id}/members", "delete")


@pytest.mark.parametrize("email", ["", None])
async def test_remove_member_needs_an_email(
    email: Any, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`email` must be a non-empty string"):
        await client.collections.remove_member(2, email)
    assert server.requests == []


# --- read-only extras ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("call", "path", "template"),
    [
        (
            lambda c: c.collections.for_dashboard(9),
            "/collections/for-dashboard/9",
            "/collections/for-dashboard/{dashboard_id}",
        ),
        (
            lambda c: c.collections.activity(2),
            "/collections/2/activity",
            "/collections/{collection_id}/activity",
        ),
        (
            lambda c: c.collections.pipeline_changes(2),
            "/collections/2/pipeline-changes",
            "/collections/{collection_id}/pipeline-changes",
        ),
    ],
)
async def test_read_routes_are_plain_gets(
    call: Any,
    path: str,
    template: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    server.answers[f"GET {path}"] = {"ok": 1}
    assert await call(client) == {"ok": 1}
    assert _only(server) == {"method": "GET", "path": path, "query": {}, "body": None}
    assert "get" in spec()["paths"][template]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.collections.for_dashboard(0),
        lambda c: c.collections.activity(0),
        lambda c: c.collections.pipeline_changes(-1),
        lambda c: c.collections.get(0),
        lambda c: c.collections.delete(True),
    ],
)
async def test_read_routes_refuse_non_positive_ids(
    call: Any, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="must be a positive integer"):
        await call(client)
    assert server.requests == []


# --- file upload -------------------------------------------------------------------------------


async def test_upload_files_sends_a_multipart_part_per_file_named_files(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("x,y\n1,2\n")
    b.write_text("p\n3\n")
    await client.collections.upload_files(2, [str(a), str(b)])
    sent = _only(server)
    assert (sent["method"], sent["path"], sent["query"]) == ("POST", "/collections/2/files", {})
    body = sent["body"]
    assert body.count('name="files"') == 2
    assert 'filename="a.csv"' in body and "x,y\n1,2\n" in body
    assert 'filename="b.csv"' in body and "p\n3\n" in body


async def test_upload_files_appends_to_a_dataset_when_asked(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    f = tmp_path / "a.csv"
    f.write_text("x\n1\n")
    await client.collections.upload_files(2, [str(f)], append_to_ds_id=44)
    assert _only(server)["query"] == {"append_to_ds_id": "44"}
    assert "append_to_ds_id" in _declared("/collections/{collection_id}/files", "post")


@pytest.mark.parametrize(
    ("files", "append", "message"),
    [
        ([], None, "`files` must be a non-empty list"),
        (["/definitely/not/here.csv"], None, "File not found: /definitely/not/here.csv"),
        (["REAL"], 0, "`append_to_ds_id` must be a positive integer, got 0"),
    ],
)
async def test_upload_files_validates_before_any_request(
    files: list[str],
    append: int | None,
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
    tmp_path: Path,
) -> None:
    real = tmp_path / "r.csv"
    real.write_text("x\n")
    files = [str(real) if f == "REAL" else f for f in files]
    with pytest.raises(MammothValidationError, match=message):
        await client.collections.upload_files(2, files, append_to_ds_id=append)
    assert server.requests == []


# --- email updates: PUT /collections/{id}/email-updates ------------------------------------


async def test_set_email_updates_puts_the_spec_settings_body(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.set_email_updates(
        2,
        True,
        "Asia/Kolkata",
        trigger="schedule",
        frequency="weekly",
        weekday=0,
        monthday=28,
        time_of_day="07:30",
        numbers={"11": ["k1", "k2"]},
    )
    assert _only(server) == {
        "method": "PUT",
        "path": "/collections/2/email-updates",
        "query": {},
        "body": {
            "enabled": True,
            "timezone": "Asia/Kolkata",
            "trigger": "schedule",
            "frequency": "weekly",
            "weekday": 0,
            "monthday": 28,
            "time_of_day": "07:30",
            "numbers": {"11": ["k1", "k2"]},
        },
    }
    props = schema("EmailUpdateSettingsBody")["properties"]
    assert set(_only(server)["body"]) <= set(props)
    assert _only(server)["body"]["trigger"] in schema("Trigger")["enum"]
    assert _only(server)["body"]["frequency"] in schema("Frequency")["enum"]


async def test_set_email_updates_sends_only_the_required_fields_by_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.collections.set_email_updates(2, False, "UTC")
    assert _only(server)["method"] == "PUT"
    assert _only(server)["body"] == {"enabled": False, "timezone": "UTC"}
    assert set(schema("EmailUpdateSettingsBody")["required"]) == {"enabled", "timezone"}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"enabled": "yes", "timezone": "UTC"}, "`enabled` must be true or false"),
        ({"enabled": True, "timezone": ""}, "`timezone` must be an IANA time zone name"),
        ({"enabled": True, "timezone": "UTC", "trigger": "hourly"}, "`trigger` must be one of"),
        ({"enabled": True, "timezone": "UTC", "frequency": "yearly"}, "`frequency` must be one of"),
        ({"enabled": True, "timezone": "UTC", "weekday": 7}, "`weekday` must be 0"),
        ({"enabled": True, "timezone": "UTC", "monthday": 29}, "`monthday` must be 1 to 28"),
        ({"enabled": True, "timezone": "UTC", "time_of_day": "24:00"}, "`time_of_day` must be"),
        ({"enabled": True, "timezone": "UTC", "numbers": {"1": "k"}}, "`numbers` must map"),
    ],
)
async def test_set_email_updates_validates_before_any_request(
    kwargs: dict[str, Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.collections.set_email_updates(2, **kwargs)
    assert server.requests == []
