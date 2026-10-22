"""Unit tests for MammothClient initialization and request handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
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


def test_user_agent_prefixes_the_sdk_agent() -> None:
    client = MammothClient(api_token="mm_unit", user_agent="my-tool/1.2")
    agent = client.session.headers["User-Agent"]
    assert agent.startswith("my-tool/1.2 mammoth-io/")
    assert (
        MammothClient(api_token="mm_unit").session.headers["User-Agent"].startswith("mammoth-io/")
    )


class TestWorkspaceHintAndLookup:
    """The workspace of a token client: hinted, or learned without blocking the loop."""

    async def test_token_accepts_a_workspace_hint_and_never_looks_it_up(self):
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json={"ok": True})

        shared = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        client = MammothClient(api_token="mm_hint", workspace_id=7, http_client=shared)
        assert client.workspace_id == 7
        await client.request_json("GET", "/ping")
        assert [r.url.path for r in seen] == ["/api/v2/ping"]
        assert "X-WORKSPACE-ID" not in seen[0].headers
        await shared.aclose()

    async def test_unknown_workspace_is_learned_asynchronously_before_a_url_is_built(self):
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            if request.url.path.endswith("/workspaces/current"):
                return httpx.Response(200, json={"id": 4242})
            return httpx.Response(200, json=[])

        shared = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        client = MammothClient(
            api_token="mm_lookup_async",
            base_url="https://lookup.example/api/v2",
            http_client=shared,
        )
        client.set_project_id(1)
        await client.folders.list()
        assert client.workspace_id == 4242
        assert [r.url.path for r in seen][0].endswith("/workspaces/current")
        assert "4242" in str(seen[1].url)
        await shared.aclose()

    async def test_resolve_workspace_id_is_a_no_op_once_known(self):
        client = MammothClient(api_key="k", api_secret="s", workspace_id=3)
        assert await client.resolve_workspace_id() == 3
        await client.close()


class TestSharedHttpClient:
    """Two callers sharing one pool: each sends its own credentials, nobody closes the pool."""

    async def test_each_client_sends_its_own_authorization_and_close_keeps_the_pool(self):
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json={})

        shared = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        first = MammothClient(api_token="mm_first", workspace_id=1, http_client=shared)
        second = MammothClient(
            api_token="mm_second", workspace_id=2, http_client=shared, user_agent="tool/1"
        )
        key_client = MammothClient(
            api_key="kk", api_secret="ss", workspace_id=3, http_client=shared
        )
        await first.request_json("GET", "/a")
        await second.request_json("GET", "/b")
        await key_client.request_json("GET", "/c")
        assert seen[0].headers["Authorization"] == "Bearer mm_first"
        assert seen[1].headers["Authorization"] == "Bearer mm_second"
        assert seen[1].headers["User-Agent"].startswith("tool/1 mammoth-io/")
        assert seen[2].headers["X-API-KEY"] == "kk"
        assert "Authorization" not in seen[2].headers
        assert seen[2].headers["X-WORKSPACE-ID"] == "3"
        for header in ("Authorization", "X-API-KEY", "X-API-SECRET", "X-WORKSPACE-ID"):
            assert header not in shared.headers
        first.set_workspace_id(9)
        assert "X-WORKSPACE-ID" not in shared.headers
        await first.close()
        await second.close()
        assert not shared.is_closed
        await shared.aclose()

    async def test_default_headers_stay_with_their_own_client_on_a_shared_pool(self):
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json={})

        shared = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        alice = MammothClient(
            api_token="mm_alice",
            workspace_id=1,
            http_client=shared,
            default_headers={"Cookie": "sid=alice", "X-Run": "r1"},
        )
        bob = MammothClient(api_token="mm_bob", workspace_id=2, http_client=shared)
        bob.add_default_headers({"cookie": "sid=bob"})
        alice.add_default_headers({"COOKIE": "sid=alice2"})
        await alice.request_json("GET", "/a")
        await bob.request_json("GET", "/b")
        await alice.request_json("GET", "/c")
        assert seen[0].headers["Cookie"] == "sid=alice2"
        assert seen[0].headers["X-Run"] == "r1"
        assert seen[1].headers["Cookie"] == "sid=bob"
        assert "X-Run" not in seen[1].headers
        assert seen[1].headers["Authorization"] == "Bearer mm_bob"
        assert seen[2].headers["Authorization"] == "Bearer mm_alice"
        for header in ("Cookie", "X-Run", "Authorization"):
            assert header not in shared.headers
        await shared.aclose()

    async def test_default_headers_override_the_credential_headers_on_an_owned_pool(self):
        client = MammothClient(
            api_token="mm_own", workspace_id=1, default_headers={"Authorization": "Bearer other"}
        )
        assert client.session.headers["Authorization"] == "Bearer other"
        assert len([k for k in client._default_headers if k.lower() == "authorization"]) == 1
        await client.close()

    async def test_shared_http_client_keeps_no_cookies_and_no_redirects(self):
        from mammoth.client import shared_http_client

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, headers={"Set-Cookie": "sid=1"}, json={})

        pool = shared_http_client()
        pool._transport = httpx.MockTransport(handler)
        await pool.get("https://box.example/api/v2/x")
        assert len(pool.cookies) == 0
        assert pool.follow_redirects is False
        await pool.aclose()

    async def test_an_owned_pool_is_closed(self):
        client = MammothClient(api_token="mm_own", workspace_id=1)
        await client.close()
        assert client.session.is_closed


async def test_direct_read_in_a_running_loop_still_works_and_warns_once(caplog):
    import mammoth.client as client_module

    client_module._blocking_lookup_warned = False
    client = MammothClient(api_token="mm_direct_read", base_url="https://direct.example/api/v2")
    response = httpx.Response(200, json={"id": 11}, request=httpx.Request("GET", "https://x"))
    with patch("mammoth.client.httpx.get", return_value=response), caplog.at_level("WARNING"):
        assert client.workspace_id == 11
    assert sum("resolve_workspace_id" in r.getMessage() for r in caplog.records) == 1
    await client.close()
