"""Connector AI chat API client for Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_SESSION_ID_POSITIVE = "`session_id` must be a positive integer, got {0}."


class ConnectorAIAPI:
    """Client for AI-assisted connector chat operations.

    Access via ``client.connector_ai``::

        client.connector_ai.chat(body={"message": "Connect to Postgres"})
        sessions = client.connector_ai.session_list()
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    def _check_project_id(self, project_id: int | None) -> None:
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))

    def chat(self, body: dict[str, Any], project_id: int | None = None) -> dict[str, Any]:
        """Send a message to the connector AI chat assistant.

        Args:
            body: Chat request payload (message, connection context, etc.).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the assistant's response.

        Raises:
            MammothValidationError: If *project_id* is not a positive integer.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/ai/connector-chat",
            json=body,
        )

    def history(self, connection_key: str, project_id: int | None = None) -> dict[str, Any]:
        """Get chat history for a connection.

        Args:
            connection_key: Key identifying the connector chat connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the chat history.

        Raises:
            MammothValidationError: If *project_id* is not a positive integer.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/ai/connector-chat/history",
            params={"connection_key": connection_key},
        )

    def session_list(self, project_id: int | None = None) -> dict[str, Any]:
        """List connector chat sessions.

        Args:
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the sessions list.

        Raises:
            MammothValidationError: If *project_id* is not a positive integer.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/ai/connector-chat/sessions"
        )

    def session_messages(self, session_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Get messages for a connector chat session.

        Args:
            session_id: ID of the chat session.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the session messages.

        Raises:
            MammothValidationError: If *session_id* or *project_id* is not a
                positive integer.
        """
        if session_id <= 0:
            raise MammothValidationError(ERR_SESSION_ID_POSITIVE.format(session_id))
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/ai/connector-chat/sessions/{session_id}/messages",
        )

    def submit_column_selection(
        self, body: dict[str, Any], project_id: int | None = None
    ) -> dict[str, Any]:
        """Submit a column selection back to the connector chat flow.

        Args:
            body: Column selection submission payload.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the updated chat state.

        Raises:
            MammothValidationError: If *project_id* is not a positive integer.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/ai/connector-chat/column-selection",
            json=body,
        )

    def submit_credentials(
        self, body: dict[str, Any], project_id: int | None = None
    ) -> dict[str, Any]:
        """Submit connector credentials back to the connector chat flow.

        Args:
            body: Credential submission payload.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the updated chat state.

        Raises:
            MammothValidationError: If *project_id* is not a positive integer.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/ai/connector-chat/credentials",
            json=body,
        )
