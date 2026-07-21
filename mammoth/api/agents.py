"""Agents API client for Mammoth AI chat agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

ERR_SESSION_ID_REQUIRED = "`session_id` must be a non-empty string, got {0!r}."
ERR_VISIBILITY_INVALID = '`visibility` must be "private" or "shared", got {0!r}.'

VALID_VISIBILITIES = frozenset({"private", "shared"})


class AgentsAPI:
    """Client for Mammoth AI agent chat and session operations.

    Access via ``client.agents``::

        reply = client.agents.chat(
            message="What changed in this dataset?",
            scope={"type": "workspace", "workspace_id": 2},
        )
        sessions = client.agents.session_list()
        client.agents.session_set_visibility(session_id, "shared")
        client.agents.session_delete(session_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def chat(
        self,
        message: str,
        scope: dict[str, Any],
        agent_key: str | None = None,
        session_id: str | None = None,
        client_context: dict[str, Any] | None = None,
        selection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a chat message to a Mammoth AI agent.

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

        Returns:
            Dict with the agent's chat response.
        """
        body: dict[str, Any] = {"message": message, "scope": scope}
        if agent_key is not None:
            body["agent_key"] = agent_key
        if session_id is not None:
            body["session_id"] = session_id
        if client_context is not None:
            body["client_context"] = client_context
        if selection is not None:
            body["selection"] = selection
        return self._client._request_json("POST", "/agents/chat", json=body)

    def session_delete(self, session_id: str) -> dict[str, Any]:
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
        return self._client._request_json("DELETE", f"/agents/sessions/{session_id}")

    def session_list(
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
        return self._client._request_json("GET", "/agents/sessions", params=params or None)

    def session_messages(self, session_id: str) -> dict[str, Any]:
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
        return self._client._request_json("GET", f"/agents/sessions/{session_id}/messages")

    def session_set_visibility(self, session_id: str, visibility: str) -> dict[str, Any]:
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
        return self._client._request_json(
            "PATCH",
            f"/agents/sessions/{session_id}",
            json={"visibility": visibility},
        )
