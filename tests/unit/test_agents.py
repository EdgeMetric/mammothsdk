"""Unit tests for the Agents API client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.agents import AgentsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[AgentsAPI, MagicMock]:
    """Create an AgentsAPI with a mocked client."""
    mock_client = MagicMock()
    api = AgentsAPI(mock_client)
    return api, mock_client


class TestAgentsAPIChat:
    def test_chat_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"reply": "hi"}
        scope = {"type": "workspace", "workspace_id": 2}
        result = api.chat(message="hello", scope=scope)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/agents/chat",
            json={"message": "hello", "scope": scope},
        )
        assert result == {"reply": "hi"}

    def test_chat_all_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        scope = {"type": "user", "user_id": 9}
        api.chat(
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
    def test_session_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.session_delete("sess-1")
        mock_client._request_json.assert_called_once_with("DELETE", "/agents/sessions/sess-1")

    def test_session_delete_empty_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            api.session_delete("")


class TestAgentsAPISessionList:
    def test_session_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"sessions": []}
        result = api.session_list()
        mock_client._request_json.assert_called_once_with("GET", "/agents/sessions", params=None)
        assert result == {"sessions": []}

    def test_session_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"sessions": []}
        api.session_list(
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
    def test_session_messages(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"session_id": "sess-1", "messages": []}
        result = api.session_messages("sess-1")
        mock_client._request_json.assert_called_once_with("GET", "/agents/sessions/sess-1/messages")
        assert result["session_id"] == "sess-1"

    def test_session_messages_empty_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            api.session_messages("")


class TestAgentsAPISessionSetVisibility:
    def test_set_visibility_shared(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"visibility": "shared"}
        result = api.session_set_visibility("sess-1", "shared")
        mock_client._request_json.assert_called_once_with(
            "PATCH", "/agents/sessions/sess-1", json={"visibility": "shared"}
        )
        assert result["visibility"] == "shared"

    def test_set_visibility_invalid(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="visibility"):
            api.session_set_visibility("sess-1", "public")

    def test_set_visibility_empty_session_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            api.session_set_visibility("", "shared")
