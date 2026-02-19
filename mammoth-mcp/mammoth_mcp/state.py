"""Client lifecycle and view cache management."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mammoth import MammothClient, View

from mammoth_mcp.config import MammothConfig

if TYPE_CHECKING:
    from mammoth_mcp.token_store import RedisTokenStore

logger = logging.getLogger(__name__)


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
        )
        if config.project_id:
            self.client.set_project_id(config.project_id)

        self._view_cache: dict[int, View] = {}

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
                    view_id, self.client.project_id,
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
                    view_id, pid, pname,
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
                    pid, pname, view_id, exc_info=True,
                )
                continue

        # Restore original project if we didn't find the view
        if original_project_id is not None:
            self.client.set_project_id(original_project_id)

        raise ValueError(
            f"View {view_id} not found in any project in workspace "
            f"{self.client.workspace_id}"
        )

    def get_view(self, view_id: int, dataset_id: int | None = None) -> View:
        """Get a View, using cache if available, always refreshing metadata.

        Auto-discovers the project if needed (first call for a view).
        """
        if view_id in self._view_cache:
            view = self._view_cache[view_id]
            view.refresh()
            return view

        # Auto-discover project (handles both "no project set" and
        # "wrong project set" by checking current project first)
        self._ensure_project_for_view(view_id)

        view = self.client.views.get(view_id, dataset_id)
        self._view_cache[view_id] = view
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
    """Per-user ClientManager instances, keyed by bearer token."""

    def __init__(self, token_store: RedisTokenStore, job_timeout: int = 120):
        self._token_store = token_store
        self._job_timeout = job_timeout
        self._managers: dict[str, ClientManager] = {}

    async def get_manager(self, bearer_token: str) -> ClientManager:
        if bearer_token in self._managers:
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
        )
        manager = ClientManager(config)
        self._managers[bearer_token] = manager
        logger.info("Created ClientManager for token %s...", bearer_token[:8])
        return manager
