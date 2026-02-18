"""Unit tests for MammothClient initialization and request handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mammoth.client import MammothClient


class TestClientInit:
    """Test MammothClient constructor."""

    def test_default_base_url(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        assert client.base_url == "https://app.mammoth.io/api/v2"

    def test_custom_base_url(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                base_url="https://custom.example.com/api/v2",
            )
        assert client.base_url == "https://custom.example.com/api/v2"

    def test_base_url_normalization(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                base_url="https://custom.example.com",
            )
        assert client.base_url.endswith("/api/v2")

    def test_session_headers_set(self):
        with patch("mammoth.client.requests.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.headers = MagicMock()
            mock_session_cls.return_value = mock_session
            MammothClient(
                api_key="my-key",
                api_secret="my-secret",
                workspace_id=42,
            )
        mock_session.headers.update.assert_called_once()
        headers = mock_session.headers.update.call_args[0][0]
        assert headers["X-API-KEY"] == "my-key"
        assert headers["X-API-SECRET"] == "my-secret"
        assert headers["X-WORKSPACE-ID"] == "42"

    def test_set_project_id(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        assert client.project_id is None
        client.set_project_id(100)
        assert client.project_id == 100

    def test_timeout_defaults(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        assert client.timeout == 30
        assert client.job_timeout == 60

    def test_custom_timeouts(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                timeout=10,
                job_timeout=120,
            )
        assert client.timeout == 10
        assert client.job_timeout == 120


class TestClientSubClients:
    """Test that all sub-clients are registered."""

    def test_all_sub_clients_exist(self):
        with patch("mammoth.client.requests.Session"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        attrs = [
            "files",
            "jobs",
            "exports",
            "workspaces",
            "client_apps",
            "projects",
            "folders",
            "datasets",
            "dataviews",
            "pipeline",
            "views",
            "connectors",
            "dashboards",
            "webhooks",
            "automations",
            "ai",
            "schedules",
            "batches",
            "external_keys",
            "activity_logs",
            "browse",
            "user_profile",
            "addons",
            "reports",
        ]
        for attr in attrs:
            assert hasattr(client, attr), f"Missing sub-client: {attr}"


class TestClientContextManager:
    """Test context manager usage."""

    def test_context_manager(self):
        with patch("mammoth.client.requests.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.headers = MagicMock()
            mock_session_cls.return_value = mock_session
            with MammothClient(api_key="key", api_secret="secret", workspace_id=1) as client:
                assert client is not None
            mock_session.close.assert_called_once()
