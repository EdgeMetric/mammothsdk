"""Unit tests for MammothClient initialization and request handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mammoth.client import MammothClient


class TestClientInit:
    """Test MammothClient constructor."""

    async def test_default_base_url(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        assert client.base_url == "https://app.mammoth.io/api/v2"

    async def test_custom_base_url(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                base_url="https://custom.example.com/api/v2",
            )
        assert client.base_url == "https://custom.example.com/api/v2"

    async def test_an_api_root_of_none_takes_the_url_exactly_as_given(self):
        # The server that mounts these routes does not itself serve them under
        # /api/v2 — whatever sits in front adds that. A caller inside the
        # network reaches the routes directly, and must be able to say so.
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                base_url="http://127.0.0.1:8260",
                api_root=None,
                allow_insecure_loopback_http=True,
            )
        assert client.base_url == "http://127.0.0.1:8260"

    async def test_an_api_root_of_none_still_refuses_a_public_http_url(self):
        # Dropping the prefix must not drop the rule that credentials never
        # travel unencrypted off this machine.
        with patch("mammoth.client.httpx.AsyncClient"), pytest.raises(ValueError):
            MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                base_url="http://example.invalid",
                api_root=None,
            )

    async def test_base_url_normalization(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(
                api_key="key",
                api_secret="secret",
                workspace_id=1,
                base_url="https://custom.example.com",
            )
        assert client.base_url.endswith("/api/v2")

    async def test_session_headers_set(self):
        with patch("mammoth.client.httpx.AsyncClient") as mock_session_cls:
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

    async def test_bearer_token_headers(self):
        with patch("mammoth.client.httpx.AsyncClient") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.headers = MagicMock()
            mock_session_cls.return_value = mock_session
            client = MammothClient(api_token=" mm_abc123 ")
        headers = mock_session.headers.update.call_args_list[0][0][0]
        assert headers["Authorization"] == "Bearer mm_abc123"
        assert "X-API-KEY" not in headers and "X-API-SECRET" not in headers
        assert "X-WORKSPACE-ID" not in headers
        assert client.api_token == "mm_abc123"

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"workspace_id": 1},
            {"api_key": "k", "workspace_id": 1},
            {"api_token": "mm_x", "api_key": "k", "api_secret": "s", "workspace_id": 1},
            {"api_token": "  "},
            {"api_token": "mm_x", "workspace_id": 1},
        ],
    )
    async def test_credential_combinations_are_validated(self, kwargs):
        with pytest.raises(ValueError):
            MammothClient(**kwargs)

    async def test_set_project_id(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        assert client.project_id is None
        client.set_project_id(100)
        assert client.project_id == 100

    async def test_timeout_defaults(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        assert client.timeout == 30
        assert client.job_timeout == 60

    async def test_custom_timeouts(self):
        with patch("mammoth.client.httpx.AsyncClient"):
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

    async def test_all_sub_clients_exist(self):
        with patch("mammoth.client.httpx.AsyncClient"):
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

    async def test_context_manager(self):
        with patch("mammoth.client.httpx.AsyncClient") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.headers = MagicMock()
            mock_session.aclose = AsyncMock()
            mock_session_cls.return_value = mock_session
            async with MammothClient(api_key="key", api_secret="secret", workspace_id=1) as client:
                assert client is not None
            mock_session.aclose.assert_called_once()


class TestViewsResource:
    """Test ViewsResource auto-detects dataset_id."""

    @pytest.fixture
    def client(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            c = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        c.set_project_id(100)
        return c

    async def test_get_auto_detects_dataset(self, client):
        """await views.get(view_id) auto-detects dataset_id via pipeline API."""
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        client.dataviews.get = AsyncMock(
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
        view = await client.views.get(42)
        client.pipeline._find_dataset_for_dataview.assert_called_once_with(42)
        client.dataviews.get.assert_called_once_with(dataset_id=500, dataview_id=42)
        assert view.id == 42

    async def test_get_with_parent_dataset_never_probes_other_datasets(self, client):
        """A known parent is part of the resource identity, not a hint to scan."""
        client.pipeline.find_dataset_for_dataview = AsyncMock(side_effect=AssertionError)
        client.dataviews.get = AsyncMock(
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

        view = await client.views.get(42, dataset_id=700)

        assert view.dataset_id == 700
        client.dataviews.get.assert_called_once_with(dataset_id=700, dataview_id=42)

    async def test_delete_auto_detects_dataset(self, client):
        """await views.delete(view_id) auto-detects dataset_id."""
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        client.dataviews.delete = AsyncMock(return_value={"status": "deleted"})
        result = await client.views.delete(42)
        client.pipeline._find_dataset_for_dataview.assert_called_once_with(42)
        client.dataviews.delete.assert_called_once_with(dataset_id=500, dataview_id=42)
        assert result["status"] == "deleted"

    async def test_delete_with_parent_skips_discovery(self, client):
        """A known parent is used exactly and never falls back to discovery."""
        client.pipeline.find_dataset_for_dataview = AsyncMock(side_effect=AssertionError)
        client.dataviews.delete = AsyncMock(return_value={"status": "deleted"})

        result = await client.views.delete(42, dataset_id=700)

        client.dataviews.delete.assert_called_once_with(dataset_id=700, dataview_id=42)
        assert result["status"] == "deleted"

    async def test_bulk_delete_auto_detects_dataset(self, client):
        """await views.bulk_delete(view_ids) auto-detects dataset_id from first view."""
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        client.dataviews.bulk_delete = AsyncMock(return_value={"status": "deleted"})
        result = await client.views.bulk_delete([42, 43])
        client.pipeline._find_dataset_for_dataview.assert_called_once_with(42)
        client.dataviews.bulk_delete.assert_called_once_with(dataset_id=500, dataview_ids=[42, 43])
        assert result["status"] == "deleted"

    async def test_list_with_dataset_id(self, client):
        """await views.list(dataset_id) lists views from a specific dataset."""
        client.dataviews.list = AsyncMock(
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
        views = await client.views.list(dataset_id=500)
        assert len(views) == 1
        assert views[0].id == 10
        client.dataviews.list.assert_called_once_with(dataset_id=500)

    async def test_create_requires_dataset_id(self, client):
        """await views.create() still requires dataset_id."""
        client.dataviews.create = AsyncMock(
            return_value={
                "dataview_id": 99,
                "id": 99,
            }
        )
        client.dataviews.get = AsyncMock(
            return_value={
                "id": 99,
                "name": "New View",
                "properties": {
                    "columns": [{"display_name": "c", "internal_name": "column_c", "type": "TEXT"}]
                },
            }
        )
        view = await client.views.create(dataset_id=500, name="New View")
        client.dataviews.create.assert_called_once_with(
            dataset_id=500, name="New View", clone_config_from=None
        )
        assert view.id == 99


class TestClientBranchOut:
    """``MammothClient.branch_out`` hands back the view's result, not a coroutine."""

    async def test_returns_the_dataset_id_the_view_wrote(self) -> None:
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(api_key="k", api_secret="s", workspace_id=1)
        view = MagicMock()
        view.branch_out = AsyncMock(return_value=321)
        client.views.get = AsyncMock(return_value=view)

        result = await client.branch_out(7, "copy", target_ds_id=321)

        assert result == 321
        view.branch_out.assert_awaited_once_with("copy", target_ds_id=321, column_mapping=None)
