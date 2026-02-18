"""Client lifecycle and view cache management."""

from __future__ import annotations

from mammoth import MammothClient, View

from mammoth_mcp.config import MammothConfig


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

    def get_view(self, view_id: int, dataset_id: int | None = None) -> View:
        """Get a View, using cache if available, always refreshing metadata."""
        if view_id in self._view_cache:
            view = self._view_cache[view_id]
            view.refresh()
            return view

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
