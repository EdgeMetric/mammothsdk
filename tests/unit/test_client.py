"""Unit tests for MammothClient initialization and request handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

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


class TestViewsResource:
    """Test ViewsResource auto-detects dataset_id."""

    @pytest.fixture
    def client(self):
        with patch("mammoth.client.requests.Session"):
            c = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        c.set_project_id(100)
        return c

    def test_get_auto_detects_dataset(self, client):
        """views.get(view_id) auto-detects dataset_id via pipeline API."""
        client.pipeline._find_dataset_for_dataview = MagicMock(return_value=500)
        client.dataviews.get = MagicMock(
            return_value={
                "id": 42,
                "name": "Test View",
                "properties": {
                    "columns": [
                        {"display_name": "col_a", "internal_name": "column_aaa", "type": "TEXT"}
                    ]
                },
            }
        )
        view = client.views.get(42)
        client.pipeline._find_dataset_for_dataview.assert_called_once_with(42)
        client.dataviews.get.assert_called_once_with(dataset_id=500, dataview_id=42)
        assert view.id == 42

    def test_delete_auto_detects_dataset(self, client):
        """views.delete(view_id) auto-detects dataset_id."""
        client.pipeline._find_dataset_for_dataview = MagicMock(return_value=500)
        client.dataviews.delete = MagicMock(return_value={"status": "deleted"})
        result = client.views.delete(42)
        client.pipeline._find_dataset_for_dataview.assert_called_once_with(42)
        client.dataviews.delete.assert_called_once_with(dataset_id=500, dataview_id=42)
        assert result["status"] == "deleted"

    def test_bulk_delete_auto_detects_dataset(self, client):
        """views.bulk_delete(view_ids) auto-detects dataset_id from first view."""
        client.pipeline._find_dataset_for_dataview = MagicMock(return_value=500)
        client.dataviews.bulk_delete = MagicMock(return_value={"status": "deleted"})
        result = client.views.bulk_delete([42, 43])
        client.pipeline._find_dataset_for_dataview.assert_called_once_with(42)
        client.dataviews.bulk_delete.assert_called_once_with(dataset_id=500, dataview_ids=[42, 43])
        assert result["status"] == "deleted"

    def test_list_with_dataset_id(self, client):
        """views.list(dataset_id) lists views from a specific dataset."""
        client.dataviews.list = MagicMock(
            return_value={
                "dataviews": [
                    {
                        "id": 10,
                        "name": "V1",
                        "properties": {
                            "columns": [
                                {
                                    "display_name": "c",
                                    "internal_name": "column_c",
                                    "type": "TEXT",
                                }
                            ]
                        },
                    }
                ]
            }
        )
        views = client.views.list(dataset_id=500)
        assert len(views) == 1
        assert views[0].id == 10
        client.dataviews.list.assert_called_once_with(dataset_id=500)

    def test_create_requires_dataset_id(self, client):
        """views.create() still requires dataset_id."""
        client.dataviews.create = MagicMock(
            return_value={
                "dataview_id": 99,
                "id": 99,
            }
        )
        client.dataviews.get = MagicMock(
            return_value={
                "id": 99,
                "name": "New View",
                "properties": {
                    "columns": [{"display_name": "c", "internal_name": "column_c", "type": "TEXT"}]
                },
            }
        )
        view = client.views.create(dataset_id=500, name="New View")
        client.dataviews.create.assert_called_once_with(
            dataset_id=500, name="New View", clone_config_from=None
        )
        assert view.id == 99
