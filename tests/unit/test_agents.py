"""Unit tests for the Agents API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.agents import AgentsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[AgentsAPI, MagicMock]:
    """Create an AgentsAPI with a mocked client."""
    mock_client = MagicMock()
    api = AgentsAPI(mock_client)
    return api, mock_client


class TestAgentsAPIChat:
    async def test_chat_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"reply": "hi"})
        scope = {"type": "workspace", "workspace_id": 2}
        result = await api.chat(message="hello", scope=scope)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/agents/chat",
            json={"message": "hello", "scope": scope},
        )
        assert result == {"reply": "hi"}

    async def test_chat_all_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        scope = {"type": "user", "user_id": 9}
        await api.chat(
            message="hello",
            scope=scope,
            agent_key="support",
            session_id="sess-1",
            client_context={"page": "dashboard"},
            selection={"request_id": "r1", "answers": {"field": ["a"]}},
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["agent_key"] == "support"
        assert call_json["session_id"] == "sess-1"
        assert call_json["client_context"] == {"page": "dashboard"}
        assert call_json["selection"] == {"request_id": "r1", "answers": {"field": ["a"]}}


class TestAgentsAPISessionDelete:
    async def test_session_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.session_delete("sess-1")
        mock_client._request_json.assert_called_once_with("DELETE", "/agents/sessions/sess-1")

    async def test_session_delete_empty_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            await api.session_delete("")


class TestAgentsAPISessionList:
    async def test_session_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"sessions": []})
        result = await api.session_list()
        mock_client._request_json.assert_called_once_with("GET", "/agents/sessions", params=None)
        assert result == {"sessions": []}

    async def test_session_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"sessions": []})
        await api.session_list(
            agent_key="support", limit=10, offset=5, include_shared=True, workspace_id=2
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/agents/sessions",
            params={
                "agent_key": "support",
                "limit": 10,
                "offset": 5,
                "include_shared": True,
                "workspace_id": 2,
            },
        )


class TestAgentsAPISessionMessages:
    async def test_session_messages(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"session_id": "sess-1", "messages": []})
        result = await api.session_messages("sess-1")
        mock_client._request_json.assert_called_once_with("GET", "/agents/sessions/sess-1/messages")
        assert result["session_id"] == "sess-1"

    async def test_session_messages_empty_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            await api.session_messages("")


class TestAgentsAPISessionSetVisibility:
    async def test_set_visibility_shared(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"visibility": "shared"})
        result = await api.session_set_visibility("sess-1", "shared")
        mock_client._request_json.assert_called_once_with(
            "PATCH", "/agents/sessions/sess-1", json={"visibility": "shared"}
        )
        assert result["visibility"] == "shared"

    async def test_set_visibility_invalid(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="visibility"):
            await api.session_set_visibility("sess-1", "public")

    async def test_set_visibility_empty_session_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            await api.session_set_visibility("", "shared")
