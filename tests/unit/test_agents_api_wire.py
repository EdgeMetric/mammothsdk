"""AgentsAPI: chat submit/retry/wait, plan decisions, and the session/run routes on the wire.

Routes, query names and bodies come from the pinned prod OpenAPI spec (AgentChat,
AgentChatRequest, PlanRef, GetAgentSessionMessages, ListAgentSessions,
SetAgentSessionVisibility, ListAgentSessionActions, DeleteAgentSessionAction, the run routes,
RegisterAgentRunUnits, ListAgentRunUnits, CancelAgentTurn, CorrectAgentRequestKind,
EditAgentPlanProposal).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

SCOPE = {"type": "workspace", "workspace_id": 1}
STARTED = {"session_id": "s1", "turn_id": "t1"}


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record backoff / poll sleeps instead of waiting; the loopback server is unaffected."""
    slept: list[float] = []

    async def fake(seconds: float, *_: Any) -> None:
        slept.append(seconds)

    monkeypatch.setattr("mammoth.api.agents.asyncio.sleep", fake)
    return slept


class Script(dict[str, Any]):
    """Answers by 'METHOD path', each route taking its answers in order (last one repeats)."""

    def __init__(self, server: RecordingServer, routes: dict[str, list[Any]]) -> None:
        super().__init__()
        self._server = server
        self._routes = {k: list(v) for k, v in routes.items()}
        self._seen: dict[str, int] = {}

    def get(self, key: str, default: Any = None) -> Any:
        if key not in self._routes:
            return default
        n = self._seen.get(key, 0)
        self._seen[key] = n + 1
        answers = self._routes[key]
        return answers[min(n, len(answers) - 1)]


def _script(server: RecordingServer, routes: dict[str, list[Any]]) -> None:
    server.answers = Script(server, routes)


# --- chat -----------------------------------------------------------------------------------


async def test_chat_posts_the_spec_body_and_returns_the_started_turn_with_its_key(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /agents/chat"] = (202, STARTED)
    started = await client.agents.chat(
        "hello",
        SCOPE,
        agent_key="analyst",
        session_id="s1",
        client_context={"project_id": 4},
        selection={"kind": "dataset"},
        request_key="rk-1",
        plan_ref={"plan_id": "p1", "action": "skip", "n": 2},
    )
    assert server.requests == [
        {
            "method": "POST",
            "path": "/agents/chat",
            "query": {},
            "body": {
                "request_key": "rk-1",
                "message": "hello",
                "scope": SCOPE,
                "agent_key": "analyst",
                "session_id": "s1",
                "client_context": {"project_id": 4},
                "selection": {"kind": "dataset"},
                "plan_ref": {"plan_id": "p1", "action": "skip", "n": 2},
            },
        }
    ]
    assert started == {**STARTED, "request_key": "rk-1"}
    assert set(server.requests[0]["body"]) <= set(schema("AgentChatRequest")["properties"])


async def test_chat_minimal_body_has_a_generated_request_key(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /agents/chat"] = (202, STARTED)
    a = await client.agents.chat("hi", SCOPE)
    b = await client.agents.chat("hi", SCOPE)
    body = server.requests[0]["body"]
    assert set(body) == {"request_key", "message", "scope"}
    assert body["request_key"] == a["request_key"] != b["request_key"]
    assert set(schema("AgentChatRequest")["required"]) <= set(body)


async def test_chat_resubmits_with_the_same_key_after_gateway_errors(
    server: RecordingServer, client: MammothClient, _no_real_sleep: list[float]  # noqa: F811
) -> None:
    _script(
        server,
        {
            "POST /agents/chat": [
                (502, {"detail": "bad gateway"}),
                (503, {"detail": "unavailable"}),
                (202, STARTED),
            ]
        },
    )
    started = await client.agents.chat("hi", SCOPE, request_key="rk-9")
    assert started["turn_id"] == "t1"
    assert [r["body"]["request_key"] for r in server.requests] == ["rk-9"] * 3
    assert _no_real_sleep == [1, 2]  # linear backoff between attempts


async def test_chat_gives_up_after_three_gateway_errors(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /agents/chat"] = (504, {"detail": "timeout"})
    with pytest.raises(MammothAPIError) as exc:
        await client.agents.chat("hi", SCOPE)
    assert exc.value.status_code == 504
    assert len(server.requests) == 3


async def test_chat_does_not_retry_a_client_error(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /agents/chat"] = (400, {"detail": "bad scope"})
    with pytest.raises(MammothAPIError) as exc:
        await client.agents.chat("hi", SCOPE)
    assert exc.value.status_code == 400
    assert len(server.requests) == 1


async def test_chat_with_wait_returns_the_assistant_reply_once_the_turn_is_done(
    server: RecordingServer, client: MammothClient, _no_real_sleep: list[float]  # noqa: F811
) -> None:
    messages = "GET /agents/sessions/s1/messages"
    _script(
        server,
        {
            "POST /agents/chat": [(202, STARTED)],
            messages: [
                {"session_id": "s1", "messages": [], "working": True, "turn_id": "t1"},
                {
                    "session_id": "s1",
                    "working": False,
                    "turn_id": "t1",
                    "messages": [
                        {"role": "user", "text": "hi"},
                        {"role": "assistant", "text": "first"},
                        {"role": "assistant", "text": "final"},
                    ],
                },
            ],
        },
    )
    result = await client.agents.chat("hi", SCOPE, request_key="rk", wait=30)
    assert result["working"] is False
    assert result["reply"] == {"role": "assistant", "text": "final"}
    assert result["session_id"] == "s1" and result["request_key"] == "rk"
    assert _no_real_sleep == [2.0]  # one poll pause between the two reads


async def test_chat_wait_stops_at_the_deadline_with_the_turn_still_working(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /agents/chat"] = (202, STARTED)
    server.answers["GET /agents/sessions/s1/messages"] = {
        "session_id": "s1",
        "messages": [],
        "working": True,
        "turn_id": "t1",
    }
    result = await client.agents.chat("hi", SCOPE, wait=0)
    assert result["working"] is True and result["reply"] is None


async def test_chat_wait_ignores_a_different_turn_that_is_working(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /agents/chat"] = (202, STARTED)
    server.answers["GET /agents/sessions/s1/messages"] = {
        "session_id": "s1",
        "messages": [{"role": "assistant", "text": "old"}],
        "working": True,
        "turn_id": "someone-elses-turn",
    }
    result = await client.agents.chat("hi", SCOPE, wait=30)
    assert result["working"] is False
    assert result["reply"] == {"role": "assistant", "text": "old"}


# --- plan decisions ---------------------------------------------------------------------------

PLAN = {
    "plan_id": "plan-7",
    "steps": [
        {"n": 1, "title": "a", "status": "done"},
        {"n": 2, "title": "b", "status": "proposed"},
    ],
}
SESSION_ROW = {
    "session_id": "s1",
    "agent_key": "analyst",
    "scope_type": "workspace",
    "scope_id": 1,
    "project_id": 4,
}


def _plan_routes(
    server: RecordingServer, plan: dict[str, Any] | None, rows: list[dict[str, Any]]
) -> None:
    server.answers["GET /agents/sessions/s1/messages"] = {
        "session_id": "s1",
        "messages": [],
        "plan": plan,
    }
    server.answers["GET /agents/sessions"] = {"sessions": rows}
    server.answers["POST /agents/chat"] = (202, STARTED)


def _chat_body(server: RecordingServer) -> dict[str, Any]:
    return next(r["body"] for r in server.requests if r["path"] == "/agents/chat")


async def test_plan_approve_chats_an_empty_message_with_the_plan_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _plan_routes(server, PLAN, [SESSION_ROW])
    await client.agents.plan_approve("s1")
    body = _chat_body(server)
    assert body["message"] == ""
    assert body["plan_ref"] == {"plan_id": "plan-7"}
    assert body["session_id"] == "s1" and body["agent_key"] == "analyst"
    assert body["scope"] == {"type": "workspace", "workspace_id": 1}
    assert body["client_context"] == {"project_id": 4}
    lookup = next(r for r in server.requests if r["path"] == "/agents/sessions")
    assert lookup["query"] == {"limit": "100"}


async def test_plan_skip_and_discard_send_the_spec_plan_ref(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _plan_routes(server, PLAN, [SESSION_ROW])
    await client.agents.plan_skip("s1", 2)
    assert _chat_body(server)["plan_ref"] == {"plan_id": "plan-7", "n": 2, "action": "skip"}
    server.requests.clear()
    await client.agents.plan_discard("s1")
    assert _chat_body(server)["plan_ref"] == {"plan_id": "plan-7", "action": "discard"}
    assert {"skip", "discard"} <= set(schema("PlanRef")["properties"]["action"]["enum"])


async def test_plan_decision_maps_user_and_account_sessions_to_a_scope(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _plan_routes(
        server, PLAN, [{**SESSION_ROW, "scope_type": "user", "scope_id": 8, "project_id": None}]
    )
    await client.agents.plan_discard("s1")
    body = _chat_body(server)
    assert body["scope"] == {"type": "user", "user_id": 8}
    assert "client_context" not in body
    server.requests.clear()
    _plan_routes(server, PLAN, [{**SESSION_ROW, "scope_type": "account", "scope_id": None}])
    await client.agents.plan_discard("s1")
    assert _chat_body(server)["scope"] == {"type": "account"}


async def test_plan_decision_prefers_an_explicit_scope_for_an_unlisted_session(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _plan_routes(server, PLAN, [])
    await client.agents.plan_approve("s1", scope=SCOPE)
    body = _chat_body(server)
    assert body["scope"] == SCOPE
    assert "agent_key" not in body


async def test_plan_decision_needs_a_scope_when_the_session_is_not_listed(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _plan_routes(server, PLAN, [])
    with pytest.raises(MammothValidationError, match="not among your recent sessions"):
        await client.agents.plan_discard("s1")
    assert not any(r["path"] == "/agents/chat" for r in server.requests)


async def test_plan_approve_needs_a_proposed_step(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    done = {"plan_id": "p", "steps": [{"n": 1, "title": "a", "status": "done"}]}
    _plan_routes(server, done, [SESSION_ROW])
    with pytest.raises(MammothValidationError, match="no proposed plan step to approve"):
        await client.agents.plan_approve("s1")
    assert not any(r["path"] == "/agents/chat" for r in server.requests)


@pytest.mark.parametrize("method", ["plan_approve", "plan_discard"])
async def test_plan_decisions_need_a_plan(
    method: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _plan_routes(server, None, [SESSION_ROW])
    with pytest.raises(MammothValidationError, match="has no plan to act on"):
        await getattr(client.agents, method)("s1")


async def test_plan_decisions_reject_an_empty_session_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`session_id` must be a non-empty string"):
        await client.agents.plan_skip("", 1)
    assert server.requests == []


# --- session / run routes ----------------------------------------------------------------------

S = "/agents/sessions/s1"
Call = Callable[[MammothClient], Awaitable[Any]]
CASES: list[tuple[str, Call, str, str, dict[str, str], Any]] = [
    ("action_list", lambda c: c.agents.action_list("s1"), "GET", f"{S}/actions", {}, None),
    (
        "action_delete",
        lambda c: c.agents.action_delete("s1", "a9"),
        "DELETE",
        f"{S}/actions/a9",
        {},
        None,
    ),
    ("run_status", lambda c: c.agents.run_status("s1"), "GET", f"{S}/run", {}, None),
    ("run_list", lambda c: c.agents.run_list("s1"), "GET", f"{S}/runs", {}, None),
    ("run_pause", lambda c: c.agents.run_pause("s1", "r1"), "POST", f"{S}/runs/r1/pause", {}, None),
    (
        "run_resume",
        lambda c: c.agents.run_resume("s1", "r1"),
        "POST",
        f"{S}/runs/r1/resume",
        {},
        None,
    ),
    ("run_stop", lambda c: c.agents.run_stop("s1", "r1"), "POST", f"{S}/runs/r1/stop", {}, None),
    (
        "run_extend",
        lambda c: c.agents.run_extend("s1", "r1"),
        "POST",
        f"{S}/runs/r1/extend",
        {},
        None,
    ),
    ("run_retry", lambda c: c.agents.run_retry("s1", "r1"), "POST", f"{S}/runs/r1/retry", {}, None),
    (
        "run_units_set",
        lambda c: c.agents.run_units_set("s1", "r1", 2, "row", [{"key": "a"}]),
        "POST",
        f"{S}/runs/r1/units",
        {},
        {"step": 2, "kind": "row", "units": [{"key": "a"}]},
    ),
    (
        "run_units_list",
        lambda c: c.agents.run_units_list("s1", "r1"),
        "GET",
        f"{S}/runs/r1/units",
        {},
        None,
    ),
    (
        "run_units_list_filtered",
        lambda c: c.agents.run_units_list("s1", "r1", step=2, state="failed", cursor=0),
        "GET",
        f"{S}/runs/r1/units",
        {"step": "2", "state": "failed", "cursor": "0"},
        None,
    ),
    (
        "run_instances_list",
        lambda c: c.agents.run_instances_list("s1", "r1"),
        "GET",
        f"{S}/runs/r1/instances",
        {},
        None,
    ),
    (
        "run_instance_messages",
        lambda c: c.agents.run_instance_messages("s1", "r1", "i1"),
        "GET",
        f"{S}/runs/r1/instances/i1/messages",
        {},
        None,
    ),
    (
        "run_instance_transcript",
        lambda c: c.agents.run_instance_transcript("s1", "r1", "i1"),
        "GET",
        f"{S}/runs/r1/instances/i1/transcript",
        {},
        None,
    ),
    (
        "turn_cancel",
        lambda c: c.agents.turn_cancel("s1", "t1"),
        "POST",
        f"{S}/turns/t1/cancel",
        {},
        None,
    ),
    (
        "message_set_request_kind",
        lambda c: c.agents.message_set_request_kind("s1", "m1", "build"),
        "PATCH",
        f"{S}/messages/m1/request-kind",
        {},
        {"request_kind": "build"},
    ),
    (
        "plan_edit_proposal",
        lambda c: c.agents.plan_edit_proposal("s1", "plan-7", "rename", "k1", name="New"),
        "PATCH",
        f"{S}/plan/proposal",
        {},
        {"plan_id": "plan-7", "action": "rename", "key": "k1", "name": "New"},
    ),
    (
        "plan_edit_proposal_no_name",
        lambda c: c.agents.plan_edit_proposal("s1", "plan-7", "drop", "k1"),
        "PATCH",
        f"{S}/plan/proposal",
        {},
        {"plan_id": "plan-7", "action": "drop", "key": "k1"},
    ),
    ("session_delete", lambda c: c.agents.session_delete("s1"), "DELETE", S, {}, None),
    (
        "session_set_visibility",
        lambda c: c.agents.session_set_visibility("s1", "shared"),
        "PATCH",
        S,
        {},
        {"visibility": "shared"},
    ),
    (
        "session_list_all_filters",
        lambda c: c.agents.session_list(
            agent_key="analyst", limit=5, offset=10, include_shared=False, workspace_id=1
        ),
        "GET",
        "/agents/sessions",
        {
            "agent_key": "analyst",
            "limit": "5",
            "offset": "10",
            "include_shared": "false",
            "workspace_id": "1",
        },
        None,
    ),
]


@pytest.mark.parametrize(
    ("call", "method", "path", "query", "body"),
    [pytest.param(c, m, p, q, b, id=i) for i, c, m, p, q, b in CASES],
)
async def test_each_route_is_the_spec_operation(
    call: Call,
    method: str,
    path: str,
    query: dict[str, str],
    body: Any,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    server.answers[f"{method} {path}"] = {"ok": "yes"}
    assert await call(client) == {"ok": "yes"}
    assert server.requests == [{"method": method, "path": path, "query": query, "body": body}]
    template = (
        path.replace("/s1", "/{session_id}")
        .replace("/r1", "/{run_id}")
        .replace("/i1", "/{instance_id}")
        .replace("/t1", "/{turn_id}")
        .replace("/m1", "/{message_id}")
        .replace("/a9", "/{action_id}")
    )
    op = spec()["paths"][template][method.lower()]
    declared = {p["name"] for p in op.get("parameters", []) if p["in"] == "query"}
    assert set(query) <= declared
    assert (body is not None) == ("requestBody" in op)


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.action_list(""),
        lambda a: a.action_delete("s", ""),
        lambda a: a.run_status(""),
        lambda a: a.run_list(""),
        lambda a: a.run_pause("s", ""),
        lambda a: a.run_resume("", "r"),
        lambda a: a.run_units_set("s", "", 1, "k", []),
        lambda a: a.run_units_list("", "r"),
        lambda a: a.run_instances_list("s", ""),
        lambda a: a.run_instance_messages("s", "r", ""),
        lambda a: a.run_instance_transcript("s", "", "i"),
        lambda a: a.run_retry("s", ""),
        lambda a: a.turn_cancel("s", ""),
        lambda a: a.message_set_request_kind("s", "", "build"),
        lambda a: a.plan_edit_proposal("", "p", "a", "k"),
        lambda a: a.session_delete(""),
        lambda a: a.session_messages(""),
        lambda a: a.session_set_visibility("", "shared"),
    ],
)
async def test_empty_ids_are_refused_before_any_request(
    call: Callable[[Any], Awaitable[Any]],
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="must be a non-empty string"):
        await call(client.agents)
    assert server.requests == []


async def test_visibility_must_be_private_or_shared(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=r'"private" or "shared", got \'public\''):
        await client.agents.session_set_visibility("s1", "public")
    assert server.requests == []
