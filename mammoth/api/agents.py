"""Agents API client for Mammoth AI chat agents."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothAPIError, MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

ERR_SESSION_ID_REQUIRED = "`session_id` must be a non-empty string, got {0!r}."
ERR_ID_REQUIRED = "`{0}` must be a non-empty string, got {1!r}."
ERR_NO_PLAN = "Session {0!r} has no plan to act on."
ERR_SESSION_NOT_LISTED = (
    "Session {0!r} is not among your recent sessions, so its scope is unknown; pass `scope`."
)
ERR_NO_PROPOSED_STEP = "Session {0!r} has no proposed plan step to approve."
ERR_VISIBILITY_INVALID = '`visibility` must be "private" or "shared", got {0!r}.'

VALID_VISIBILITIES = frozenset({"private", "shared"})

ERR_ACCESS_NOTHING_TO_CHANGE = "Give at least one {0} field to change."
ERR_ACCESS_NEEDS_PEOPLE = "`emails` must list at least one address."
ERR_ACCESS_NEEDS_ITEMS = "`items` must list at least one project."
ERR_GRANT_LEVEL_INVALID = '`level` must be "ask" or "explore", got {0!r}.'
ERR_REQUEST_STATUS_INVALID = (
    '`status` must be "open", "done", "declined" or "dismissed", got {0!r}.'
)
ERR_RESOLVE_STATUS_INVALID = '`status` must be "done", "declined" or "dismissed", got {0!r}.'
ERR_REQUEST_KIND_INVALID = '`kind` must be "access", "change" or "feedback", got {0!r}.'
ERR_REQUEST_TEXT_LENGTH = "`text` must be 1 to {0} characters."
ERR_RATING_INVALID = '`rating` must be "up" or "down", got {0!r}.'
ERR_COMMENT_LENGTH = "`comment` must be at most {0} characters."

VALID_GRANT_LEVELS = frozenset({"ask", "explore"})
VALID_REQUEST_STATUSES = frozenset({"open", "done", "declined", "dismissed"})
VALID_RESOLVE_STATUSES = frozenset({"done", "declined", "dismissed"})
VALID_REQUEST_KINDS = frozenset({"access", "change", "feedback"})
VALID_RATINGS = frozenset({"up", "down"})
#: The server's length limit on a request's text and on a rating's comment.
REQUEST_TEXT_MAX = 2000

#: Gateway statuses on which a chat submit is sent again with the same ``request_key``.
CHAT_RETRY_STATUSES = frozenset({502, 503, 504})
CHAT_MAX_ATTEMPTS = 3
CHAT_POLL_SECONDS = 2.0
#: How many of the caller's newest sessions are searched for a plan decision's chat.
SESSION_LOOKUP_LIMIT = 100


class AgentsAPI:
    """Client for Mammoth AI agent chat and session operations.

    Access via ``client.agents``::

        reply = await client.agents.chat(
            message="What changed in this dataset?",
            scope={"type": "workspace", "workspace_id": 2},
        )
        sessions = await client.agents.session_list()
        await client.agents.session_set_visibility(session_id, "shared")
        await client.agents.session_delete(session_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    async def chat(
        self,
        message: str,
        scope: dict[str, Any],
        agent_key: str | None = None,
        session_id: str | None = None,
        client_context: dict[str, Any] | None = None,
        selection: dict[str, Any] | None = None,
        request_key: str | None = None,
        wait: float | None = None,
        plan_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a chat message to a Mammoth AI agent.

        The server starts the turn and answers at once with its ids. Each submit
        carries a ``request_key`` (made here unless given): a send that fails on a
        gateway error is repeated with the same key and gets the turn it already
        started, never a second one.

        Args:
            message: Chat message text (1-20000 characters).
            scope: Scope of the chat, e.g.
                ``{"type": "workspace", "workspace_id": 2}``. ``type`` must be
                one of ``"workspace"``, ``"user"``, or ``"account"``.
            agent_key: Identifier of the agent to chat with (max 80 chars).
            session_id: Existing session ID to continue (max 128 chars).
            client_context: Free-form context dict passed through to the agent.
            selection: Prior clarification answers, e.g.
                ``{"request_id": "...", "answers": {"field": ["value"]}}``.
            request_key: Idempotency id of this submit (1-128 chars). Leave unset
                to have one made; pass the same value to repeat a submit.
            wait: Seconds to wait for the turn to finish. ``None`` returns as
                soon as the turn has started.
            plan_ref: The step of the chat's current plan this message points at,
                e.g. ``{"plan_id": "..."}`` (the whole plan: Run it). Prefer
                :meth:`plan_approve`, :meth:`plan_skip` and :meth:`plan_discard`.

        Returns:
            Dict with ``session_id``, ``turn_id`` and ``request_key``. With
            *wait*, also ``working`` (still writing when the wait ran out) and
            ``reply`` (the newest assistant message, or ``None``).
        """
        key = request_key or uuid.uuid4().hex
        body: dict[str, Any] = {"request_key": key, "message": message, "scope": scope}
        if agent_key is not None:
            body["agent_key"] = agent_key
        if session_id is not None:
            body["session_id"] = session_id
        if client_context is not None:
            body["client_context"] = client_context
        if selection is not None:
            body["selection"] = selection
        if plan_ref is not None:
            body["plan_ref"] = plan_ref
        started = await self._submit_chat(body)
        started["request_key"] = key
        if wait is None:
            return started
        return await self._wait_for_reply(started, wait)

    async def plan_approve(
        self, session_id: str, scope: dict[str, Any] | None = None, wait: float | None = None
    ) -> dict[str, Any]:
        """Approve (Run it) every proposed step of the chat's current plan.

        This is what the web app's Run it button sends. Typing "Run it" as a chat
        message does not approve anything.

        Args:
            session_id: ID of the chat session.
            scope: Scope of the chat, as for :meth:`chat`; left out, it is read
                from the session (one of your own recent sessions).
            wait: Seconds to wait for the turn to finish; ``None`` returns once it started.

        Returns:
            The :meth:`chat` result (``session_id``, ``turn_id``, ``request_key``).

        Raises:
            MammothValidationError: If the chat has no plan, or no proposed step.
        """
        plan = await self._current_plan(session_id)
        if not any(step.get("status") == "proposed" for step in plan.get("steps", [])):
            raise MammothValidationError(ERR_NO_PROPOSED_STEP.format(session_id))
        return await self._plan_decision(session_id, scope, {"plan_id": plan["plan_id"]}, wait)

    async def plan_skip(
        self,
        session_id: str,
        n: int,
        scope: dict[str, Any] | None = None,
        wait: float | None = None,
    ) -> dict[str, Any]:
        """Skip one proposed step (*n*, 1-based) of the chat's current plan.

        Args:
            session_id: ID of the chat session.
            scope: Scope of the chat, as for :meth:`chat`; left out, it is read
                from the session (one of your own recent sessions).
            n: Number of the proposed step to skip.
            wait: Seconds to wait for the turn to finish; ``None`` returns once it started.

        Returns:
            The :meth:`chat` result.

        Raises:
            MammothValidationError: If the chat has no plan.
        """
        plan = await self._current_plan(session_id)
        ref = {"plan_id": plan["plan_id"], "n": n, "action": "skip"}
        return await self._plan_decision(session_id, scope, ref, wait)

    async def plan_discard(
        self, session_id: str, scope: dict[str, Any] | None = None, wait: float | None = None
    ) -> dict[str, Any]:
        """Skip every proposed step of the chat's current plan.

        Args:
            session_id: ID of the chat session.
            scope: Scope of the chat, as for :meth:`chat`; left out, it is read
                from the session (one of your own recent sessions).
            wait: Seconds to wait for the turn to finish; ``None`` returns once it started.

        Returns:
            The :meth:`chat` result.

        Raises:
            MammothValidationError: If the chat has no plan.
        """
        plan = await self._current_plan(session_id)
        ref = {"plan_id": plan["plan_id"], "action": "discard"}
        return await self._plan_decision(session_id, scope, ref, wait)

    async def _current_plan(self, session_id: str) -> dict[str, Any]:
        """The plan in force in the session; raises when the chat has none."""
        _require_id("session_id", session_id)
        plan: dict[str, Any] | None = (await self.session_messages(session_id)).get("plan")
        if not plan:
            raise MammothValidationError(ERR_NO_PLAN.format(session_id))
        return plan

    async def _plan_decision(
        self,
        session_id: str,
        scope: dict[str, Any] | None,
        plan_ref: dict[str, Any],
        wait: float | None,
    ) -> dict[str, Any]:
        """Send an empty chat message that carries only the plan reference.

        The chat's agent, scope and project come from the session itself, so the
        turn lands in the same chat the plan belongs to.
        """
        target = await self._session_target(session_id)
        if scope is not None:
            target["scope"] = scope
        if "scope" not in target:
            raise MammothValidationError(ERR_SESSION_NOT_LISTED.format(session_id))
        return await self.chat(
            message="", session_id=session_id, plan_ref=plan_ref, wait=wait, **target
        )

    async def _session_target(self, session_id: str) -> dict[str, Any]:
        """``agent_key``, ``scope`` and ``client_context`` of one of the caller's sessions."""
        listed = await self.session_list(limit=SESSION_LOOKUP_LIMIT)
        found = next(
            (s for s in listed.get("sessions", []) if s.get("session_id") == session_id), None
        )
        if found is None:
            return {}
        target: dict[str, Any] = {"agent_key": found["agent_key"]}
        kind, scope_id = found.get("scope_type"), found.get("scope_id")
        if kind in ("workspace", "user") and scope_id is not None:
            target["scope"] = {"type": kind, f"{kind}_id": scope_id}
        elif kind == "account":
            target["scope"] = {"type": "account"}
        if found.get("project_id") is not None:
            target["client_context"] = {"project_id": found["project_id"]}
        return target

    async def _submit_chat(self, body: dict[str, Any]) -> dict[str, Any]:
        """POST the chat, repeating it with the same body on a gateway error."""
        for attempt in range(1, CHAT_MAX_ATTEMPTS + 1):
            try:
                return await self._client._request_json("POST", "/agents/chat", json=body)
            except MammothAPIError as error:
                if error.status_code not in CHAT_RETRY_STATUSES or attempt == CHAT_MAX_ATTEMPTS:
                    raise
                await asyncio.sleep(attempt)
        raise AssertionError("unreachable")

    async def _wait_for_reply(self, started: dict[str, Any], wait: float) -> dict[str, Any]:
        """Poll the session's messages until its turn is no longer writing."""
        deadline = time.monotonic() + wait
        while True:
            page = await self.session_messages(started["session_id"])
            working = bool(page.get("working")) and page.get("turn_id") in (
                None,
                started["turn_id"],
            )
            if not working or time.monotonic() >= deadline:
                break
            await asyncio.sleep(CHAT_POLL_SECONDS)
        replies = [m for m in page.get("messages", []) if m.get("role") == "assistant"]
        return {**started, "working": working, "reply": replies[-1] if replies else None}

    async def session_delete(self, session_id: str) -> dict[str, Any]:
        """Delete an agent chat session.

        Args:
            session_id: ID of the session to delete.

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        if not session_id:
            raise MammothValidationError(ERR_SESSION_ID_REQUIRED.format(session_id))
        return await self._client._request_json("DELETE", f"/agents/sessions/{session_id}")

    async def session_list(
        self,
        agent_key: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_shared: bool | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """List agent chat sessions.

        Args:
            agent_key: Filter by agent identifier.
            limit: Maximum number of results.
            offset: Number of results to skip.
            include_shared: Whether to include sessions shared by other users.
            workspace_id: Filter by workspace ID.

        Returns:
            Dict with the sessions list.
        """
        params: dict[str, Any] = {}
        if agent_key is not None:
            params["agent_key"] = agent_key
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if include_shared is not None:
            params["include_shared"] = include_shared
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return await self._client._request_json("GET", "/agents/sessions", params=params or None)

    async def session_messages(self, session_id: str) -> dict[str, Any]:
        """Get the messages for an agent chat session.

        Args:
            session_id: ID of the session.

        Returns:
            Dict with the session ID and its messages.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        if not session_id:
            raise MammothValidationError(ERR_SESSION_ID_REQUIRED.format(session_id))
        return await self._client._request_json("GET", f"/agents/sessions/{session_id}/messages")

    async def session_set_visibility(self, session_id: str, visibility: str) -> dict[str, Any]:
        """Set the visibility of an agent chat session.

        Args:
            session_id: ID of the session.
            visibility: Either ``"private"`` or ``"shared"``.

        Returns:
            Dict with the updated session summary.

        Raises:
            MammothValidationError: If *session_id* is empty or *visibility* is
                not one of ``"private"``/``"shared"``.
        """
        if not session_id:
            raise MammothValidationError(ERR_SESSION_ID_REQUIRED.format(session_id))
        if visibility not in VALID_VISIBILITIES:
            raise MammothValidationError(ERR_VISIBILITY_INVALID.format(visibility))
        return await self._client._request_json(
            "PATCH",
            f"/agents/sessions/{session_id}",
            json={"visibility": visibility},
        )

    async def action_list(self, session_id: str) -> dict[str, Any]:
        """List the changes an agent chat session made (its write record).

        Args:
            session_id: ID of the session.

        Returns:
            Dict with the session's recorded actions, each marking whether the
            chat created the object it touched.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        _require_id("session_id", session_id)
        return await self._client._request_json("GET", f"/agents/sessions/{session_id}/actions")

    async def action_delete(self, session_id: str, action_id: str) -> dict[str, Any]:
        """Delete the object an agent chat session created, by its action id.

        The server refuses an action whose object the chat did not create.

        Args:
            session_id: ID of the session.
            action_id: ID of the recorded action.

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *session_id* or *action_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("action_id", action_id)
        return await self._client._request_json(
            "DELETE", f"/agents/sessions/{session_id}/actions/{action_id}"
        )

    async def run_status(self, session_id: str) -> dict[str, Any]:
        """Get the current durable run of an agent chat session.

        Args:
            session_id: ID of the session.

        Returns:
            Dict with the session's current run (state, step, active time).

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        _require_id("session_id", session_id)
        return await self._client._request_json("GET", f"/agents/sessions/{session_id}/run")

    async def run_list(self, session_id: str) -> dict[str, Any]:
        """List the durable runs of an agent chat session.

        Args:
            session_id: ID of the session.

        Returns:
            Dict with the session's runs.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        _require_id("session_id", session_id)
        return await self._client._request_json("GET", f"/agents/sessions/{session_id}/runs")

    async def run_pause(self, session_id: str, run_id: str) -> dict[str, Any]:
        """Pause a run after its current call.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.

        Returns:
            Dict with the run after the request.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        return await self._run_action(session_id, run_id, "pause")

    async def run_resume(self, session_id: str, run_id: str) -> dict[str, Any]:
        """Resume a paused run. The server refuses this from inside the run itself.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.

        Returns:
            Dict with the run after the request.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        return await self._run_action(session_id, run_id, "resume")

    async def run_stop(self, session_id: str, run_id: str) -> dict[str, Any]:
        """Stop a run and cancel its live step.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.

        Returns:
            Dict with the run after the request.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        return await self._run_action(session_id, run_id, "stop")

    async def run_extend(self, session_id: str, run_id: str) -> dict[str, Any]:
        """Give a capped run a fresh time budget. The server refuses this from inside the run.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.

        Returns:
            Dict with the run after the request.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        return await self._run_action(session_id, run_id, "extend")

    async def run_units_set(
        self, session_id: str, run_id: str, step: int, kind: str, units: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Report the objects a plan step of a run will work on, once, as queued units.

        The server shows them in the run panel and measures progress and the time left
        from their completions; the agent never states either. A unit already listed
        is left as it is.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.
            step: Number of the plan step that will work on the units.
            kind: Kind of the objects, e.g. ``"dataset"`` or ``"view"``.
            units: Objects, each ``{"id": 12, "name": "Sales", "project_id": 3}``
                (``name`` and ``project_id`` optional); 1 to 1000.

        Returns:
            Dict with ``registered`` (units sent) and ``units_total`` (the run's total).

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        return await self._client._request_json(
            "POST",
            f"/agents/sessions/{session_id}/runs/{run_id}/units",
            json={"step": step, "kind": kind, "units": units},
        )

    async def turn_cancel(self, session_id: str, turn_id: str) -> dict[str, Any]:
        """Stop one agent turn. Only the session's owner may.

        The turn starts no further model or tool call, the call running is cut, and the
        turn ends with a ``stopped`` event listing the writes already made. Repeating the
        call, or calling after the turn ended, is safe.

        Args:
            session_id: ID of the session.
            turn_id: ID of the turn.

        Returns:
            Dict with ``session_id``, ``turn_id`` and ``status``: ``stopping``,
            ``stopped`` or ``ended``.

        Raises:
            MammothValidationError: If *session_id* or *turn_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("turn_id", turn_id)
        return await self._client._request_json(
            "POST", f"/agents/sessions/{session_id}/turns/{turn_id}/cancel"
        )

    async def run_units_list(
        self,
        session_id: str,
        run_id: str,
        step: int | None = None,
        state: str | None = None,
        cursor: int | None = None,
    ) -> dict[str, Any]:
        """List the units of work a run's steps do, one page at a time.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.
            step: Only the units of this plan step.
            state: Only the units in this state: ``queued``, ``running``, ``done``,
                ``failed`` or ``skipped``.
            cursor: Offset of the page to read.

        Returns:
            Dict with the page of units.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        params = {
            key: value
            for key, value in {"step": step, "state": state, "cursor": cursor}.items()
            if value is not None
        }
        return await self._client._request_json(
            "GET",
            f"/agents/sessions/{session_id}/runs/{run_id}/units",
            params=params or None,
        )

    async def run_instances_list(self, session_id: str, run_id: str) -> dict[str, Any]:
        """List the agents of a run: the main agent, its workers and recon helpers.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.

        Returns:
            Dict with the run's agent instances.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        return await self._client._request_json(
            "GET", f"/agents/sessions/{session_id}/runs/{run_id}/instances"
        )

    async def run_instance_messages(
        self, session_id: str, run_id: str, instance_id: str
    ) -> dict[str, Any]:
        """List the messages an agent of a run sent or received.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.
            instance_id: ID of the agent instance (from ``run_instances_list``).

        Returns:
            Dict with the instance's messages.

        Raises:
            MammothValidationError: If *session_id*, *run_id* or *instance_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        _require_id("instance_id", instance_id)
        return await self._client._request_json(
            "GET",
            f"/agents/sessions/{session_id}/runs/{run_id}/instances/{instance_id}/messages",
        )

    async def run_instance_transcript(
        self, session_id: str, run_id: str, instance_id: str
    ) -> dict[str, Any]:
        """Get the model messages of an agent of a run, with credentials redacted.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.
            instance_id: ID of the agent instance (from ``run_instances_list``).

        Returns:
            Dict with the instance's model messages.

        Raises:
            MammothValidationError: If *session_id*, *run_id* or *instance_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        _require_id("instance_id", instance_id)
        return await self._client._request_json(
            "GET",
            f"/agents/sessions/{session_id}/runs/{run_id}/instances/{instance_id}/transcript",
        )

    async def run_retry(self, session_id: str, run_id: str) -> dict[str, Any]:
        """Retry a failed or stopped run as a new run. Starts paid model work.

        Args:
            session_id: ID of the session.
            run_id: ID of the run.

        Returns:
            Dict with the new run.

        Raises:
            MammothValidationError: If *session_id* or *run_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        return await self._client._request_json(
            "POST", f"/agents/sessions/{session_id}/runs/{run_id}/retry"
        )

    async def message_set_request_kind(
        self, session_id: str, message_id: str, request_kind: str
    ) -> dict[str, Any]:
        """Correct the request kind a reply answered. Only the session's creator may.

        Args:
            session_id: ID of the session.
            message_id: ID of the reply message.
            request_kind: One of ``"ask"``, ``"insight"``, ``"build"``, ``"automate"``
                or ``"fix"``.

        Returns:
            Dict with the updated message.

        Raises:
            MammothValidationError: If *session_id* or *message_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("message_id", message_id)
        return await self._client._request_json(
            "PATCH",
            f"/agents/sessions/{session_id}/messages/{message_id}/request-kind",
            json={"request_kind": request_kind},
        )

    async def plan_edit_proposal(
        self,
        session_id: str,
        plan_id: str,
        action: str,
        key: str,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Rename or remove an item of the plan's waiting workflow proposal. Creator only.

        Args:
            session_id: ID of the session.
            plan_id: ID of the plan.
            action: ``"rename"`` or ``"remove"``.
            key: Key of the proposal item to change.
            name: New name; required for ``"rename"``.

        Returns:
            Dict with the updated proposal.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        _require_id("session_id", session_id)
        body: dict[str, Any] = {"plan_id": plan_id, "action": action, "key": key}
        if name is not None:
            body["name"] = name
        return await self._client._request_json(
            "PATCH", f"/agents/sessions/{session_id}/plan/proposal", json=body
        )

    # -- Access: who may use the agent, how far, and the requests they make ------------------
    # Settings > AI Agent. All of it is scoped to the client's workspace (X-WORKSPACE-ID).

    async def access_me(
        self, project_id: int | None = None, preview_user_id: int | None = None
    ) -> dict[str, Any]:
        """What the agent may do for the caller in this workspace.

        Args:
            project_id: Read the level for this project (``None`` when the caller cannot
                open it) instead of the highest of the caller's levels.
            preview_user_id: A manager of AI Agent settings may read the same for this
                person; anyone else gets 403.

        Returns:
            Dict with ``enabled``, ``level``, ``levels`` (by project id), ``can_manage``,
            ``downloads`` and ``grant_only`` (projects held only through a "can ask" grant).
        """
        params = {
            key: value
            for key, value in {"project_id": project_id, "preview_user_id": preview_user_id}.items()
            if value is not None
        }
        return await self._client._request_json("GET", "/agents/access/me", params=params or None)

    async def access_settings_get(self) -> dict[str, Any]:
        """Get the workspace's AI Agent controls. Managers only.

        Returns:
            Dict with ``enabled``, ``can_make_changes``, ``downloads``, ``viewers_explore``,
            ``managers`` and ``role_exceptions``.
        """
        return await self._client._request_json("GET", "/agents/access/settings")

    async def access_settings_update(
        self,
        enabled: bool | None = None,
        can_make_changes: bool | None = None,
        downloads: bool | None = None,
        viewers_explore: bool | None = None,
        managers: list[str] | None = None,
        role_exceptions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Change the workspace's AI Agent controls. Managers only.

        Only the fields given are sent; one left out stays as it is.

        Args:
            enabled: Whether the agent is on in the workspace.
            can_make_changes: Whether the agent may change things, not only read.
            downloads: Whether the agent may offer downloads.
            viewers_explore: Whether viewers can explore with the agent.
            managers: The people or roles that manage these settings.
            role_exceptions: Per-role overrides, each ``{"role", "has_agent",
                "can_make_changes"}``.

        Returns:
            Dict with the settings after the change.

        Raises:
            MammothValidationError: If nothing to change was given.
        """
        fields: dict[str, Any] = {
            "enabled": enabled,
            "can_make_changes": can_make_changes,
            "downloads": downloads,
            "viewers_explore": viewers_explore,
            "managers": managers,
            "role_exceptions": role_exceptions,
        }
        body = {key: value for key, value in fields.items() if value is not None}
        if not body:
            raise MammothValidationError(ERR_ACCESS_NOTHING_TO_CHANGE.format("settings"))
        return await self._client._request_json("PATCH", "/agents/access/settings", json=body)

    async def access_grants_list(self) -> list[dict[str, Any]]:
        """List who can ask the agent about projects without opening the data. Managers only.

        Returns:
            One dict per grant: ``id``, ``user``, ``level``, ``items`` (projects, and the
            files when not the whole project), ``granted_by`` and ``created_at``.
        """
        return await self._client._request_list("GET", "/agents/access/grants")

    async def access_grant_give(
        self, emails: list[str], level: str, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Give people access to ask about projects. Managers only.

        People outside the workspace are invited as free guests. A person who can already
        open a project gets no grant for it.

        Args:
            emails: Email addresses of the people (at least one).
            level: ``"ask"`` or ``"explore"``.
            items: What to cover (at least one), each ``{"project_id": 1}`` for the whole
                project or ``{"project_id": 1, "file_ids": [2, 3]}`` for those files only.

        Returns:
            Dict with ``grants`` (new grant ids), ``invited`` and ``already_had_access``.

        Raises:
            MammothValidationError: If *emails* or *items* is empty, or *level* is not
                ``"ask"`` or ``"explore"``.
        """
        if not emails:
            raise MammothValidationError(ERR_ACCESS_NEEDS_PEOPLE)
        if not items:
            raise MammothValidationError(ERR_ACCESS_NEEDS_ITEMS)
        if level not in VALID_GRANT_LEVELS:
            raise MammothValidationError(ERR_GRANT_LEVEL_INVALID.format(level))
        return await self._client._request_json(
            "POST",
            "/agents/access/grants",
            json={"emails": emails, "level": level, "items": items},
        )

    async def access_grant_update(
        self,
        grant_id: int,
        level: str | None = None,
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Change a person's access. Managers only.

        Args:
            grant_id: ID of the grant (from :meth:`access_grants_list`).
            level: New level, ``"ask"`` or ``"explore"``.
            items: New coverage, replacing the old: ``{"project_id", "file_ids"}`` entries.

        Returns:
            Empty dict (the server answers 204).

        Raises:
            MammothValidationError: If nothing to change was given, or *level* is invalid.
        """
        if level is None and items is None:
            raise MammothValidationError(ERR_ACCESS_NOTHING_TO_CHANGE.format("grant"))
        if level is not None and level not in VALID_GRANT_LEVELS:
            raise MammothValidationError(ERR_GRANT_LEVEL_INVALID.format(level))
        body: dict[str, Any] = {}
        if level is not None:
            body["level"] = level
        if items is not None:
            body["items"] = items
        return await self._client._request_json(
            "PATCH", f"/agents/access/grants/{grant_id}", json=body
        )

    async def access_grant_revoke(self, grant_id: int) -> dict[str, Any]:
        """Revoke a person's access. Managers only.

        Args:
            grant_id: ID of the grant (from :meth:`access_grants_list`).

        Returns:
            Empty dict (the server answers 204).
        """
        return await self._client._request_json("DELETE", f"/agents/access/grants/{grant_id}")

    async def access_people(self, search: str | None = None) -> list[dict[str, Any]]:
        """List the workspace's members and what their own access gives their agent.

        Managers only.

        Args:
            search: Keep only people whose name or email matches.

        Returns:
            One dict per person: ``user`` and ``summary`` (a level per project).
        """
        return await self._client._request_list(
            "GET", "/agents/access/people", params={"search": search} if search else None
        )

    async def access_tree(self) -> list[dict[str, Any]]:
        """List the projects and files the Give access tree offers. Managers only.

        Returns:
            One dict per project: ``project_id``, ``name`` and ``files``.
        """
        return await self._client._request_list("GET", "/agents/access/tree")

    async def access_project_askers(self, project_id: int) -> dict[str, Any]:
        """Count the people who can ask about a project without opening it.

        For workspace managers and for anyone who manages the project's people.

        Args:
            project_id: ID of the project.

        Returns:
            Dict with ``count``.
        """
        return await self._client._request_json(
            "GET", f"/agents/access/projects/{project_id}/askers"
        )

    async def access_reach(self, user_id: int | None = None) -> list[dict[str, Any]]:
        """List what one person's agent can see.

        Any member reads their own; another person's is for managers only.

        Args:
            user_id: The person; leave out (or pass the caller) for the caller's own.

        Returns:
            One dict per project: ``project_id``, ``name``, ``level``, ``files`` and
            ``starters`` (suggested questions).
        """
        return await self._client._request_list(
            "GET",
            "/agents/access/reach",
            params={"user_id": user_id} if user_id is not None else None,
        )

    async def access_requests_list(self, status: str | None = None) -> list[dict[str, Any]]:
        """List the workspace's agent requests. Owners and admins.

        Args:
            status: ``"open"`` (the server's default), ``"done"``, ``"declined"`` or
                ``"dismissed"``.

        Returns:
            One dict per request: ``id``, ``kind``, ``requester``, ``text``, ``status`` ...

        Raises:
            MammothValidationError: If *status* is not one of the four.
        """
        if status is not None and status not in VALID_REQUEST_STATUSES:
            raise MammothValidationError(ERR_REQUEST_STATUS_INVALID.format(status))
        return await self._client._request_list(
            "GET",
            "/agents/access/requests",
            params={"status": status} if status is not None else None,
        )

    async def access_requests_mine(self, session_id: str) -> list[dict[str, Any]]:
        """List the caller's own requests made from one chat.

        Args:
            session_id: ID of the chat session.

        Returns:
            One dict per request, as in :meth:`access_requests_list`.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        _require_id("session_id", session_id)
        return await self._client._request_list(
            "GET", "/agents/access/requests/mine", params={"session_id": session_id}
        )

    async def access_request_create(
        self,
        kind: str,
        text: str,
        project_id: int | None = None,
        file_id: int | None = None,
        asked: str | None = None,
        session_id: str | None = None,
        turn_id: str | None = None,
        dashboard_id: int | None = None,
    ) -> dict[str, Any]:
        """Ask for access or a change, or flag an answer, from the chat. Any member.

        The same person asking the same thing of the same turn again gets the open request
        back. An access or change request tells the workspace's owners and admins.

        Args:
            kind: ``"access"``, ``"change"`` or ``"feedback"``.
            text: What is asked (1-2000 characters).
            project_id: The project it is about.
            file_id: The file it is about.
            asked: The question the person asked the agent (1-200 characters).
            session_id: The chat session it was raised from.
            turn_id: The turn it is about.
            dashboard_id: The dashboard it is about.

        Returns:
            Dict with the request.

        Raises:
            MammothValidationError: If *kind* is invalid or *text* is empty or too long.
        """
        if kind not in VALID_REQUEST_KINDS:
            raise MammothValidationError(ERR_REQUEST_KIND_INVALID.format(kind))
        if not text or len(text) > REQUEST_TEXT_MAX:
            raise MammothValidationError(ERR_REQUEST_TEXT_LENGTH.format(REQUEST_TEXT_MAX))
        fields: dict[str, Any] = {
            "project_id": project_id,
            "file_id": file_id,
            "asked": asked,
            "session_id": session_id,
            "turn_id": turn_id,
            "dashboard_id": dashboard_id,
        }
        body: dict[str, Any] = {"kind": kind, "text": text}
        body.update({key: value for key, value in fields.items() if value is not None})
        return await self._client._request_json("POST", "/agents/access/requests", json=body)

    async def access_request_resolve(self, request_id: int, status: str) -> dict[str, Any]:
        """Close a request. Owners, admins and the file's keeper.

        Args:
            request_id: ID of the request.
            status: ``"done"``, ``"declined"`` or ``"dismissed"``.

        Returns:
            Dict with the closed request.

        Raises:
            MammothValidationError: If *status* is not one of the three.
        """
        if status not in VALID_RESOLVE_STATUSES:
            raise MammothValidationError(ERR_RESOLVE_STATUS_INVALID.format(status))
        return await self._client._request_json(
            "PATCH", f"/agents/access/requests/{request_id}", json={"status": status}
        )

    async def access_request_add_to_context(self, request_id: int) -> dict[str, Any]:
        """Keep a thumbs-down's correction in the project's agent context. Owners and admins.

        Keeps the comment of a feedback request in the project's agent context, which
        every agent reading the project gets, and marks the request done.

        Args:
            request_id: ID of the feedback request.

        Returns:
            Dict with the request.
        """
        return await self._client._request_json(
            "POST", f"/agents/access/requests/{request_id}/project-context"
        )

    async def access_chart_save(
        self,
        session_id: str,
        turn_id: str,
        dashboard_id: int | None = None,
        new_dashboard_name: str | None = None,
    ) -> dict[str, Any]:
        """Save the chart of an answer to the caller's own dashboard (Explore level).

        The dashboard builder draws the chart in the background from the intent alone.

        Args:
            session_id: ID of the chat session (the caller's own).
            turn_id: ID of the turn whose chart to save.
            dashboard_id: A dashboard the caller saved to before. Leave out to make a new one.
            new_dashboard_name: Name of the new dashboard (up to 200 characters).

        Returns:
            Dict with ``dashboard_id``.

        Raises:
            MammothValidationError: If *session_id* or *turn_id* is empty.
        """
        _require_id("session_id", session_id)
        _require_id("turn_id", turn_id)
        body: dict[str, Any] = {"session_id": session_id, "turn_id": turn_id}
        if dashboard_id is not None:
            body["dashboard_id"] = dashboard_id
        if new_dashboard_name is not None:
            body["new_dashboard_name"] = new_dashboard_name
        return await self._client._request_json("POST", "/agents/access/saved-charts", json=body)

    # -- Ratings of a chat's replies -----------------------------------------------------------

    async def turn_feedback_list(self, session_id: str) -> list[dict[str, Any]]:
        """List the ratings the creator gave one chat's replies.

        Args:
            session_id: ID of the chat session.

        Returns:
            One dict per rated turn: ``turn_id``, ``rating``, ``comment``, ``user_id`` and
            ``created_at``.

        Raises:
            MammothValidationError: If *session_id* is empty.
        """
        _require_id("session_id", session_id)
        return await self._client._request_list("GET", f"/agents/sessions/{session_id}/feedback")

    async def turn_rate(
        self, session_id: str, turn_id: str, rating: str, comment: str | None = None
    ) -> dict[str, Any]:
        """Rate one agent reply. Only the chat's creator may.

        A later rating of the same turn replaces the earlier one.

        Args:
            session_id: ID of the chat session.
            turn_id: ID of the turn (the reply).
            rating: ``"up"`` or ``"down"``.
            comment: Why (up to 2000 characters).

        Returns:
            Empty dict (the server answers 204).

        Raises:
            MammothValidationError: If an id is empty, *rating* is not ``"up"`` or
                ``"down"``, or *comment* is too long.
        """
        _require_id("session_id", session_id)
        _require_id("turn_id", turn_id)
        if rating not in VALID_RATINGS:
            raise MammothValidationError(ERR_RATING_INVALID.format(rating))
        if comment is not None and len(comment) > REQUEST_TEXT_MAX:
            raise MammothValidationError(ERR_COMMENT_LENGTH.format(REQUEST_TEXT_MAX))
        body: dict[str, Any] = {"rating": rating}
        if comment is not None:
            body["comment"] = comment
        return await self._client._request_json(
            "POST", f"/agents/sessions/{session_id}/turns/{turn_id}/feedback", json=body
        )

    async def _run_action(self, session_id: str, run_id: str, action: str) -> dict[str, Any]:
        _require_id("session_id", session_id)
        _require_id("run_id", run_id)
        return await self._client._request_json(
            "POST", f"/agents/sessions/{session_id}/runs/{run_id}/{action}"
        )


def _require_id(name: str, value: str) -> None:
    if not value:
        raise MammothValidationError(ERR_ID_REQUIRED.format(name, value))
