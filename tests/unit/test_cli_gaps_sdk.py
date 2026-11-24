"""PRD-3685 SDK gaps: comment edit/delete/access, canvas expected_version, link fire, unset.

The loopback server records each request; nothing here reaches a real server.
"""

from __future__ import annotations

from urllib.parse import urlsplit

import pytest

from mammoth.api.workflow_triggers import check_link_host, parse_link
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

_PROJ = "/workspaces/1/projects/25654"
_WF = f"{_PROJ}/workflows/41"


def _routes(server: RecordingServer) -> list[tuple[object, object]]:
    return [(r["method"], r["path"]) for r in server.requests]


async def test_comment_edit_patches_the_comment_with_the_new_body(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {_PROJ}/annotations/5/comments/9"] = {"id": 9, "body": "new"}
    assert await client.annotations.comment_edit(5, 9, body="new") == {"id": 9, "body": "new"}
    assert _routes(server) == [("PATCH", f"{_PROJ}/annotations/5/comments/9")]
    assert server.requests[0]["body"] == {"body": "new"}


async def test_comment_delete_deletes_the_comment_and_takes_a_204(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {_PROJ}/annotations/5/comments/9"] = (204, None)
    assert await client.annotations.comment_delete(5, 9) == {}
    assert _routes(server) == [("DELETE", f"{_PROJ}/annotations/5/comments/9")]


async def test_access_reads_the_access_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    body = {"can_post": True, "can_moderate": False, "people": [{"id": 3, "name": "Ann"}]}
    server.answers[f"GET {_PROJ}/annotations/access"] = body
    assert await client.annotations.access() == body


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.comment_edit(0, 9, body="x"),
        lambda api: api.comment_edit(5, 0, body="x"),
        lambda api: api.comment_edit(5, 9, body=""),
        lambda api: api.comment_delete(5, -1),
    ],
)
async def test_comment_calls_refuse_bad_arguments_before_any_request(
    call: object, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await call(client.annotations)  # type: ignore[operator]
    assert server.requests == []


async def test_canvas_sends_expected_version_only_when_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workflows.canvas(41, {"a": 1})
    await client.workflows.canvas(41, {"a": 1}, expected_version=3)
    assert [r["body"] for r in server.requests] == [
        {"canvas_state": {"a": 1}},
        {"canvas_state": {"a": 1}, "expected_version": 3},
    ]


async def test_link_fire_posts_the_link_and_returns_the_run(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /workflow-runs/41/s3cret"] = (
        202,
        {"run_id": "r", "already_running": False},
    )
    assert await client.workflow_triggers.link_fire("/workflow-runs/41/s3cret") == {
        "run_id": "r",
        "already_running": False,
    }
    assert _routes(server) == [("POST", "/workflow-runs/41/s3cret")]


@pytest.mark.parametrize(
    "link",
    [
        "/workflow-runs/41/s3cret",
        "{base_url}/workflow-runs/41/s3cret",
        "  /workflow-runs/41/s3cret/ ",
    ],
)
async def test_link_fire_takes_the_path_or_url_link_create_returns(
    link: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workflow_triggers.link_fire(link.format(base_url=client.base_url))
    assert _routes(server) == [("POST", "/workflow-runs/41/s3cret")]


@pytest.mark.parametrize(
    "link",
    [
        "https://orion.mammoth.io/api/v2/workflow-runs/41/s3cret",
        "//orion.mammoth.io/workflow-runs/41/s3cret",
        "orion.mammoth.io/workflow-runs/41/s3cret",
        "http://{host}.example.com/workflow-runs/41/s3cret",
        "https://orion.mammoth.io/{host}/workflow-runs/41/s3cret",
        "http://{host}@orion.mammoth.io/workflow-runs/41/s3cret",
        "https://[x/workflow-runs/41/s3cret",
        "https://orion.mammoth.io:x/workflow-runs/41/s3cret",
    ],
)
async def test_link_fire_never_sends_another_servers_secret(
    link: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError) as error:
        await client.workflow_triggers.link_fire(
            link.format(host=urlsplit(client.base_url).hostname)
        )
    assert "s3cret" not in str(error.value)
    assert server.requests == []


@pytest.mark.parametrize(
    "link",
    [
        "https://app.mammoth.io/api/v2/workflow-runs/41/s3cret",
        "https://app.mammoth.io:443/api/v2/workflow-runs/41/s3cret",
        "HTTPS://App.Mammoth.IO/api/v2/workflow-runs/41/s3cret",
    ],
)
def test_a_link_of_the_clients_server_is_accepted_however_it_is_written(link: str) -> None:
    check_link_host(link, "https://app.mammoth.io/api/v2")


@pytest.mark.parametrize(
    "link",
    ["app.mammoth.io/api/v2/workflow-runs/41/s3cret", "https://[x/workflow-runs/41/s3cret"],
)
def test_a_link_that_is_neither_path_nor_url_is_named_as_such(link: str) -> None:
    with pytest.raises(MammothValidationError, match="from its https://") as error:
        check_link_host(link, "https://app.mammoth.io/api/v2")
    assert "s3cret" not in str(error.value)


@pytest.mark.parametrize(
    "link",
    [
        "https://app.mammoth.io:8443/workflow-runs/41/s3cret",
        "https://app.mammoth.io.example.com/workflow-runs/41/s3cret",
        "https://orion.mammoth.io/app.mammoth.io/workflow-runs/41/s3cret",
        "https://app.mammoth.io@orion.mammoth.io/workflow-runs/41/s3cret",
    ],
)
def test_a_link_that_only_contains_the_clients_host_is_another_servers(link: str) -> None:
    with pytest.raises(MammothValidationError, match="another server") as error:
        check_link_host(link, "https://app.mammoth.io/api/v2")
    assert "s3cret" not in str(error.value)


@pytest.mark.parametrize(
    "link",
    [
        "",
        "/workflow-runs/x/y",
        "/other/41/s3cret",
        "s3cret",
        "app.mammoth.io/workflow-runs/41/s3cret",
        "//app.mammoth.io/workflow-runs/41/s3cret",
        "https://[x/workflow-runs/41/s3cret",
        "https://app.mammoth.io:x/workflow-runs/41/s3cret",
    ],
)
def test_parse_link_refuses_what_is_not_a_link_without_echoing_it(link: str) -> None:
    with pytest.raises(MammothValidationError) as error:
        parse_link(link)
    assert "s3cret" not in str(error.value)


async def test_schedule_and_after_unset_delete_their_routes_and_take_a_204(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {_WF}/schedule"] = (204, None)
    server.answers[f"DELETE {_WF}/after"] = (204, None)
    assert await client.workflow_triggers.schedule_unset(41) == {}
    assert await client.workflow_triggers.after_unset(41) == {}
    assert _routes(server) == [("DELETE", f"{_WF}/schedule"), ("DELETE", f"{_WF}/after")]


async def test_unset_refuses_a_bad_workflow_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.workflow_triggers.schedule_unset(0)
    assert server.requests == []
