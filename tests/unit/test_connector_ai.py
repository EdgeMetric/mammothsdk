"""Unit tests for the ConnectorAIAPI client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.connector_ai import ConnectorAIAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[ConnectorAIAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = ConnectorAIAPI(mock_client)
    return api, mock_client


class TestConnectorAIAPIChat:
    def test_chat(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"reply": "hi"}
        result = api.chat(body={"message": "connect to postgres"})
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/ai/connector-chat",
            json={"message": "connect to postgres"},
        )
        assert result == {"reply": "hi"}

    def test_chat_explicit_project(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.chat(body={"message": "hi"}, project_id=200)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/200/ai/connector-chat",
            json={"message": "hi"},
        )

    def test_chat_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="project_id"):
            api.chat(body={}, project_id=0)


class TestConnectorAIAPIHistory:
    def test_history(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"messages": []}
        api.history(connection_key="abc123")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/ai/connector-chat/history",
            params={"connection_key": "abc123"},
        )


class TestConnectorAIAPISessionList:
    def test_session_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"sessions": []}
        api.session_list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/ai/connector-chat/sessions"
        )


class TestConnectorAIAPISessionMessages:
    def test_session_messages(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"messages": []}
        api.session_messages(9)
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/ai/connector-chat/sessions/9/messages",
        )

    def test_session_messages_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="session_id"):
            api.session_messages(0)


class TestConnectorAIAPISubmitColumnSelection:
    def test_submit_column_selection(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.submit_column_selection(body={"columns": ["a", "b"]})
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/ai/connector-chat/column-selection",
            json={"columns": ["a", "b"]},
        )


class TestConnectorAIAPISubmitCredentials:
    def test_submit_credentials(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.submit_credentials(body={"username": "u", "password": "p"})
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/ai/connector-chat/credentials",
            json={"username": "u", "password": "p"},
        )


class TestConnectorAIAPIProjectRequired:
    def test_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = ConnectorAIAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            api.session_list()
