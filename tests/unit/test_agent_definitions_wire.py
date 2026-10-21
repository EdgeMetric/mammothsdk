"""AgentDefinitionsAPI: wire requests and argument validation.

Oracle: mvc-service commits 2a976c7d2c (``apiv2/apiv2/agent_definitions``: controller, schema,
``common/routes.py``) and 8bb6251331 (feedback route). These routes are not in the pinned
OpenAPI spec yet. The request models there are ``extra="forbid"``, so a body key the SDK
invents would be a 422.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

BASE = "/workspaces/1/agent-definitions"
# Fields accepted by AgentDefinitionCreate / AgentDefinitionUpdate in the backend schema.
CREATE_FIELDS = {"key", "name", "description", "charter", "role", "propose", "project_ids", "team"}
UPDATE_FIELDS = CREATE_FIELDS - {"key"}

Call = Callable[[MammothClient], Awaitable[Any]]

CASES: list[tuple[str, Call, str, str, dict[str, str], Any]] = [
    ("list", lambda c: c.agent_definitions.list(), "GET", BASE, {}, None),
    (
        "list_status",
        lambda c: c.agent_definitions.list(status="published"),
        "GET",
        BASE,
        {"status": "published"},
        None,
    ),
    ("roles", lambda c: c.agent_definitions.roles(), "GET", f"{BASE}/roles", {}, None),
    (
        "get",
        lambda c: c.agent_definitions.get("margin-watch"),
        "GET",
        f"{BASE}/margin-watch",
        {},
        None,
    ),
    (
        "delete",
        lambda c: c.agent_definitions.delete("margin-watch"),
        "DELETE",
        f"{BASE}/margin-watch",
        {},
        None,
    ),
    (
        "publish",
        lambda c: c.agent_definitions.publish("margin-watch"),
        "POST",
        f"{BASE}/margin-watch/publish",
        {},
        None,
    ),
    (
        "disable",
        lambda c: c.agent_definitions.disable("margin-watch"),
        "POST",
        f"{BASE}/margin-watch/disable",
        {},
        None,
    ),
    (
        "charter_versions",
        lambda c: c.agent_definitions.charter_versions("margin-watch"),
        "GET",
        f"{BASE}/margin-watch/charter-versions",
        {},
        None,
    ),
    (
        "charter_restore",
        lambda c: c.agent_definitions.charter_restore("margin-watch", 3),
        "POST",
        f"{BASE}/margin-watch/charter-versions/3/restore",
        {},
        None,
    ),
    (
        "goldens_list",
        lambda c: c.agent_definitions.goldens_list("margin-watch"),
        "GET",
        f"{BASE}/margin-watch/goldens",
        {},
        None,
    ),
    (
        "goldens_add",
        lambda c: c.agent_definitions.goldens_add("margin-watch", "Q?", "A."),
        "POST",
        f"{BASE}/margin-watch/goldens",
        {},
        {"question": "Q?", "expected": "A."},
    ),
    (
        "goldens_remove",
        lambda c: c.agent_definitions.goldens_remove("margin-watch", 8),
        "DELETE",
        f"{BASE}/margin-watch/goldens/8",
        {},
        None,
    ),
    (
        "goldens_run",
        lambda c: c.agent_definitions.goldens_run("margin-watch"),
        "POST",
        f"{BASE}/margin-watch/goldens/run",
        {},
        None,
    ),
    (
        "goldens_status",
        lambda c: c.agent_definitions.goldens_status("margin-watch"),
        "GET",
        f"{BASE}/margin-watch/goldens/run",
        {},
        None,
    ),
    (
        "notes_list_all",
        lambda c: c.agent_definitions.notes_list("margin-watch"),
        "GET",
        f"{BASE}/margin-watch/notes",
        {},
        None,
    ),
    (
        "notes_list_filtered",
        lambda c: c.agent_definitions.notes_list("margin-watch", project_id=4, kind="fact"),
        "GET",
        f"{BASE}/margin-watch/notes",
        {"project_id": "4", "kind": "fact"},
        None,
    ),
    (
        "notes_upsert",
        lambda c: c.agent_definitions.notes_upsert("margin-watch", 4, "scratch", "todo", "text"),
        "PUT",
        f"{BASE}/margin-watch/notes",
        {},
        {"project_id": 4, "kind": "scratch", "name": "todo", "content": "text"},
    ),
    (
        "notes_delete",
        lambda c: c.agent_definitions.notes_delete("margin-watch", 12),
        "DELETE",
        f"{BASE}/margin-watch/notes/12",
        {},
        None,
    ),
    (
        "feedback_list",
        lambda c: c.agent_definitions.feedback_list("margin-watch"),
        "GET",
        f"{BASE}/margin-watch/feedback",
        {},
        None,
    ),
]


@pytest.mark.parametrize(
    ("call", "method", "path", "query", "body"),
    [pytest.param(c, m, p, q, b, id=i) for i, c, m, p, q, b in CASES],
)
async def test_each_call_sends_the_backend_route(
    call: Call,
    method: str,
    path: str,
    query: dict[str, str],
    body: Any,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    server.answers[f"{method} {path}"] = {"result": [{"marker": 1}]}
    result = await call(client)
    assert server.requests == [{"method": method, "path": path, "query": query, "body": body}]
    assert result == {"result": [{"marker": 1}]}


async def test_204_answers_come_back_as_an_empty_dict(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {BASE}/margin-watch"] = (204, None)
    assert await client.agent_definitions.delete("margin-watch") == {}


async def test_create_sends_only_the_required_fields_by_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.agent_definitions.create("margin-watch", "Margin watch")
    assert server.requests == [
        {
            "method": "POST",
            "path": BASE,
            "query": {},
            "body": {"key": "margin-watch", "name": "Margin watch"},
        }
    ]


async def test_create_sends_every_given_field_under_the_backend_names(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.agent_definitions.create(
        "margin-watch",
        "Margin watch",
        description="d",
        charter="c" * 30,
        role="workspace_viewer",
        propose=False,
        project_ids=[1, 2],
        team={"agents": ["a"], "max_rounds": 2},
    )
    body = server.requests[0]["body"]
    assert body == {
        "key": "margin-watch",
        "name": "Margin watch",
        "description": "d",
        "charter": "c" * 30,
        "role": "workspace_viewer",
        "propose": False,  # False is a value, not "unset"
        "project_ids": [1, 2],
        "team": {"agents": ["a"], "max_rounds": 2},
    }
    assert set(body) <= CREATE_FIELDS


async def test_update_sends_only_changed_fields_including_falsy_ones(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.agent_definitions.update("margin-watch", propose=False, project_ids=[])
    assert server.requests == [
        {
            "method": "PATCH",
            "path": f"{BASE}/margin-watch",
            "query": {},
            "body": {"propose": False, "project_ids": []},
        }
    ]


async def test_update_every_field_uses_backend_names(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.agent_definitions.update(
        "margin-watch",
        name="n",
        description="d",
        charter="c",
        role="workspace_member",
        propose=True,
        project_ids=[9],
        team={"agents": [], "max_rounds": 1},
    )
    assert set(server.requests[0]["body"]) == UPDATE_FIELDS


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.get(""),
        lambda a: a.update(""),
        lambda a: a.delete(""),
        lambda a: a.publish(""),
        lambda a: a.disable(""),
        lambda a: a.charter_versions(""),
        lambda a: a.charter_restore("", 1),
        lambda a: a.goldens_list(""),
        lambda a: a.goldens_add("", "q", "e"),
        lambda a: a.goldens_remove("", 1),
        lambda a: a.goldens_run(""),
        lambda a: a.goldens_status(""),
        lambda a: a.notes_list(""),
        lambda a: a.notes_upsert("", 1, "fact", "n", "c"),
        lambda a: a.notes_delete("", 1),
        lambda a: a.feedback_list(""),
    ],
)
async def test_an_empty_agent_key_is_refused_before_any_request(
    call: Callable[[Any], Awaitable[Any]],
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="agent_key.*non-empty string"):
        await call(client.agent_definitions)
    assert server.requests == []


@pytest.mark.parametrize(
    ("call", "name"),
    [
        (lambda a: a.charter_restore("k", 0), "version"),
        (lambda a: a.goldens_remove("k", -1), "golden_id"),
        (lambda a: a.notes_delete("k", 0), "note_id"),
        (lambda a: a.notes_upsert("k", 0, "fact", "n", "c"), "project_id"),
    ],
)
async def test_non_positive_ids_are_refused_before_any_request(
    call: Callable[[Any], Awaitable[Any]],
    name: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=name):
        await call(client.agent_definitions)
    assert server.requests == []


async def test_note_kind_must_be_fact_or_scratch(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=r'"fact" or "scratch", got \'memo\''):
        await client.agent_definitions.notes_list("k", kind="memo")
    with pytest.raises(MammothValidationError, match=r'"fact" or "scratch", got \'memo\''):
        await client.agent_definitions.notes_upsert("k", 1, "memo", "n", "c")
    assert server.requests == []
