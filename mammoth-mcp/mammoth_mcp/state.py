"""Client lifecycle and view cache management."""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from typing import TYPE_CHECKING

from mammoth import MammothClient, View
from mammoth_mcp.config import MammothConfig

if TYPE_CHECKING:
    from mammoth_mcp.token_store import RedisTokenStore

logger = logging.getLogger(__name__)

# Cache limits
_VIEW_CACHE_MAX = 50
_VIEW_CACHE_TTL = 1800  # 30 minutes
_MANAGER_CACHE_MAX = 100


class _TTLEntry:
    """A cache entry with a timestamp for TTL eviction."""

    __slots__ = ("value", "accessed_at")

    def __init__(self, value: View) -> None:
        self.value = value
        self.accessed_at = time.monotonic()

    def touch(self) -> None:
        self.accessed_at = time.monotonic()

    def is_expired(self, ttl: float) -> bool:
        return (time.monotonic() - self.accessed_at) > ttl


class ClientManager:
    """Manages the MammothClient instance and a view cache."""

    def __init__(self, config: MammothConfig) -> None:
        self.config = config
        self.client = MammothClient(
            api_key=config.api_key,
            api_secret=config.api_secret,
            workspace_id=config.workspace_id,
            base_url=config.base_url,
            job_timeout=config.job_timeout,
            pipeline_timeout=config.pipeline_timeout,
        )
        if config.project_id:
            self.client.set_project_id(config.project_id)

        # LRU + TTL view cache (OrderedDict for LRU ordering)
        self._view_cache: OrderedDict[int, _TTLEntry] = OrderedDict()

    def _evict_expired_views(self) -> None:
        """Remove entries older than TTL."""
        expired = [
            vid for vid, entry in self._view_cache.items() if entry.is_expired(_VIEW_CACHE_TTL)
        ]
        for vid in expired:
            del self._view_cache[vid]

    def _ensure_project_for_view(self, view_id: int) -> None:
        """Auto-discover and set the project containing a view ID.

        Uses the SDK's _find_dataset_for_dataview per project. Sets the
        project on the client so subsequent calls work.
        """
        # Fast path: current project already has the view
        if getattr(self.client, "project_id", None) is not None:
            try:
                self.client.pipeline._find_dataset_for_dataview(view_id)
                return  # Found in current project
            except Exception:
                logger.info(
                    "View %d not in current project %s, searching others...",
                    view_id,
                    self.client.project_id,
                )

        # Search all projects
        original_project_id = getattr(self.client, "project_id", None)
        projects = self.client.projects.list()

        for proj in projects.get("projects", []):
            pid = proj["id"]
            pname = proj.get("name", "")
            try:
                # Temporarily set project on client so SDK methods work
                self.client.set_project_id(pid)
                self.client.pipeline._find_dataset_for_dataview(view_id)
                # Found it!
                self.config.project_id = pid
                self._view_cache.clear()
                logger.info(
                    "Auto-discovered view %d in project %d (%s)",
                    view_id,
                    pid,
                    pname,
                )
                return
            except ValueError:
                # View not in this project (normal case)
                logger.debug("View %d not in project %d (%s)", view_id, pid, pname)
                continue
            except Exception:
                # API error (500, network, etc.) — log and continue
                logger.warning(
                    "Error searching project %d (%s) for view %d",
                    pid,
                    pname,
                    view_id,
                    exc_info=True,
                )
                continue

        # Restore original project if we didn't find the view
        if original_project_id is not None:
            self.client.set_project_id(original_project_id)

        raise ValueError(
            f"View {view_id} not found in any project in workspace " f"{self.client.workspace_id}"
        )

    def get_view(self, view_id: int) -> View:
        """Get a View, using cache if available, always refreshing metadata.

        Auto-discovers the project if needed (first call for a view).
        Uses LRU eviction (max 50) and TTL (30 min).
        """
        # Evict expired entries periodically
        self._evict_expired_views()

        if view_id in self._view_cache:
            entry = self._view_cache[view_id]
            entry.touch()
            # Move to end for LRU ordering
            self._view_cache.move_to_end(view_id)
            entry.value.refresh()
            return entry.value

        # Auto-discover project (handles both "no project set" and
        # "wrong project set" by checking current project first)
        self._ensure_project_for_view(view_id)

        view = self.client.views.get(view_id)

        # Evict oldest entry if at capacity
        if len(self._view_cache) >= _VIEW_CACHE_MAX:
            self._view_cache.popitem(last=False)

        self._view_cache[view_id] = _TTLEntry(view)
        return view

    def invalidate_view(self, view_id: int) -> None:
        """Remove a view from the cache."""
        self._view_cache.pop(view_id, None)

    def set_project(self, project_id: int) -> None:
        """Update the active project."""
        self.config.project_id = project_id
        self.client.set_project_id(project_id)
        self._view_cache.clear()


class UserClientRegistry:
    """Per-user ClientManager instances, keyed by bearer token.

    Uses LRU eviction to prevent unbounded growth.
    """

    def __init__(
        self, token_store: RedisTokenStore, job_timeout: int = 120, pipeline_timeout: int = 3600
    ):
        self._token_store = token_store
        self._job_timeout = job_timeout
        self._pipeline_timeout = pipeline_timeout
        self._managers: OrderedDict[str, ClientManager] = OrderedDict()

    async def get_manager(self, bearer_token: str) -> ClientManager:
        if bearer_token in self._managers:
            # Move to end for LRU
            self._managers.move_to_end(bearer_token)
            return self._managers[bearer_token]

        token_data = await self._token_store.get_token(bearer_token)
        if not token_data:
            raise RuntimeError("Invalid or expired token")

        creds = token_data["credentials"]
        config = MammothConfig(
            api_key=creds["api_key"],
            api_secret=creds["api_secret"],
            workspace_id=creds["workspace_id"],
            base_url=creds.get("base_url", "https://app.mammoth.io/api/v2"),
            job_timeout=self._job_timeout,
            pipeline_timeout=self._pipeline_timeout,
        )
        manager = ClientManager(config)

        # Evict oldest manager if at capacity
        if len(self._managers) >= _MANAGER_CACHE_MAX:
            evicted_token, _ = self._managers.popitem(last=False)
            logger.info("Evicted manager for token %s... (LRU)", evicted_token[:8])

        self._managers[bearer_token] = manager
        logger.info("Created ClientManager for token %s...", bearer_token[:8])
        return manager
