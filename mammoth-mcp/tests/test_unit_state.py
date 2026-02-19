"""Unit tests for mammoth_mcp.state — view cache and manager registry."""

from __future__ import annotations

import time
from collections import OrderedDict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mammoth_mcp.config import MammothConfig
from mammoth_mcp.state import (
    ClientManager,
    UserClientRegistry,
    _TTLEntry,
    _VIEW_CACHE_MAX,
    _VIEW_CACHE_TTL,
    _MANAGER_CACHE_MAX,
)


# ── _TTLEntry ─────────────────────────────────────────────────


class TestTTLEntry:
    def test_touch_updates_timestamp(self):
        v = MagicMock()
        entry = _TTLEntry(v)
        old_ts = entry.accessed_at
        time.sleep(0.01)
        entry.touch()
        assert entry.accessed_at > old_ts

    def test_is_expired(self):
        v = MagicMock()
        entry = _TTLEntry(v)
        assert not entry.is_expired(10.0)
        entry.accessed_at = time.monotonic() - 11.0
        assert entry.is_expired(10.0)


# ── ClientManager cache ──────────────────────────────────────


class TestClientManagerCache:
    def _make_manager(self):
        """Create a ClientManager with mocked SDK client."""
        config = MammothConfig(
            api_key="test",
            api_secret="test",
            workspace_id=1,
            project_id=1,
        )
        with patch("mammoth_mcp.state.MammothClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.project_id = 1
            mock_pipeline = MagicMock()
            mock_client.pipeline = mock_pipeline
            mock_views = MagicMock()
            mock_client.views = mock_views
            manager = ClientManager(config)
            return manager, mock_client

    def test_cache_hit(self):
        manager, mock_client = self._make_manager()
        mock_view = MagicMock()
        mock_view.id = 100

        # Pre-populate cache
        manager._view_cache[100] = _TTLEntry(mock_view)

        result = manager.get_view(100)
        assert result is mock_view
        mock_view.refresh.assert_called_once()
        # Should NOT call client.views.get since it's cached
        mock_client.views.get.assert_not_called()

    def test_cache_miss_fetches_from_api(self):
        manager, mock_client = self._make_manager()
        mock_view = MagicMock()
        mock_client.views.get.return_value = mock_view
        # Make _find_dataset_for_dataview succeed (view found in current project)
        mock_client.pipeline._find_dataset_for_dataview.return_value = 1

        result = manager.get_view(200)
        assert result is mock_view
        mock_client.views.get.assert_called_once_with(200, None)
        assert 200 in manager._view_cache

    def test_lru_eviction(self):
        manager, mock_client = self._make_manager()
        mock_client.pipeline._find_dataset_for_dataview.return_value = 1

        # Fill cache to max
        for i in range(_VIEW_CACHE_MAX):
            mock_view = MagicMock()
            mock_view.id = i
            manager._view_cache[i] = _TTLEntry(mock_view)

        assert len(manager._view_cache) == _VIEW_CACHE_MAX

        # Add one more — should evict the oldest
        new_view = MagicMock()
        mock_client.views.get.return_value = new_view
        manager.get_view(9999)

        assert len(manager._view_cache) == _VIEW_CACHE_MAX
        assert 0 not in manager._view_cache  # First entry evicted
        assert 9999 in manager._view_cache

    def test_ttl_eviction(self):
        manager, mock_client = self._make_manager()

        # Add an expired entry
        mock_view = MagicMock()
        entry = _TTLEntry(mock_view)
        entry.accessed_at = time.monotonic() - _VIEW_CACHE_TTL - 1
        manager._view_cache[500] = entry

        # Add a fresh entry
        fresh_view = MagicMock()
        manager._view_cache[501] = _TTLEntry(fresh_view)

        # Trigger eviction
        manager._evict_expired_views()

        assert 500 not in manager._view_cache
        assert 501 in manager._view_cache

    def test_invalidate_removes_entry(self):
        manager, _ = self._make_manager()
        mock_view = MagicMock()
        manager._view_cache[100] = _TTLEntry(mock_view)

        manager.invalidate_view(100)
        assert 100 not in manager._view_cache

    def test_set_project_clears_cache(self):
        manager, mock_client = self._make_manager()
        mock_view = MagicMock()
        manager._view_cache[100] = _TTLEntry(mock_view)

        manager.set_project(99)
        assert len(manager._view_cache) == 0
        assert manager.config.project_id == 99


# ── UserClientRegistry ────────────────────────────────────────


class TestUserClientRegistry:
    @pytest.mark.asyncio
    async def test_creates_manager_on_first_access(self):
        store = MagicMock()
        store.get_token = AsyncMock(return_value={
            "credentials": {
                "api_key": "k",
                "api_secret": "s",
                "workspace_id": 1,
            },
        })

        with patch("mammoth_mcp.state.MammothClient"):
            registry = UserClientRegistry(store, job_timeout=30)
            manager = await registry.get_manager("token_abc")

            assert isinstance(manager, ClientManager)
            assert "token_abc" in registry._managers

    @pytest.mark.asyncio
    async def test_returns_cached_manager(self):
        store = MagicMock()
        store.get_token = AsyncMock(return_value={
            "credentials": {
                "api_key": "k",
                "api_secret": "s",
                "workspace_id": 1,
            },
        })

        with patch("mammoth_mcp.state.MammothClient"):
            registry = UserClientRegistry(store, job_timeout=30)
            m1 = await registry.get_manager("token_abc")
            m2 = await registry.get_manager("token_abc")
            assert m1 is m2

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self):
        store = MagicMock()
        store.get_token = AsyncMock(return_value=None)

        registry = UserClientRegistry(store, job_timeout=30)
        with pytest.raises(RuntimeError, match="Invalid or expired"):
            await registry.get_manager("bad_token")

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        store = MagicMock()
        store.get_token = AsyncMock(return_value={
            "credentials": {
                "api_key": "k",
                "api_secret": "s",
                "workspace_id": 1,
            },
        })

        with patch("mammoth_mcp.state.MammothClient"):
            registry = UserClientRegistry(store, job_timeout=30)

            # Fill to max
            for i in range(_MANAGER_CACHE_MAX):
                await registry.get_manager(f"token_{i}")

            assert len(registry._managers) == _MANAGER_CACHE_MAX

            # Add one more
            await registry.get_manager("token_overflow")

            assert len(registry._managers) == _MANAGER_CACHE_MAX
            assert "token_0" not in registry._managers
            assert "token_overflow" in registry._managers
