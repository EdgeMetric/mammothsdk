"""
Dashboards API client for managing dashboards in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class DashboardsAPI:
    """Client for managing Mammoth dashboards.

    Access via client.dashboards:
        dashboards = client.dashboards.list()
        dashboard = client.dashboards.create(config={...})
        client.dashboards.share(dashboard_id, config={...})
        client.dashboards.delete(dashboard_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def list(self) -> _list[dict[str, Any]]:
        """List all dashboards.

        Returns:
            List of dashboard dicts.
        """
        response = self._client._request_json("GET", "/dashboards")
        return response.get("dashboards", response if isinstance(response, _list) else [])

    def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new dashboard.

        Args:
            config: Dashboard configuration (name, sources, layout, etc.).

        Returns:
            Dict with created dashboard info (may include job ID for async creation).
        """
        return self._client._request_json(
            "POST", "/dashboards", json=config
        )

    def get(self, dashboard_id: int) -> dict[str, Any]:
        """Get dashboard details.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with dashboard details.
        """
        return self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}"
        )

    def update(self, dashboard_id: int, config: dict[str, Any]) -> dict[str, Any]:
        """Update a dashboard.

        Args:
            dashboard_id: ID of the dashboard.
            config: Updated dashboard configuration.

        Returns:
            Dict with updated dashboard info.
        """
        return self._client._request_json(
            "PATCH", f"/dashboards/{dashboard_id}", json=config
        )

    def delete(self, dashboard_id: int) -> dict[str, Any]:
        """Delete a dashboard.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE", f"/dashboards/{dashboard_id}"
        )

    def get_sources(self) -> _list[dict[str, Any]]:
        """Get available dashboard data sources.

        Returns:
            List of source dicts.
        """
        response = self._client._request_json("GET", "/dashboards/sources")
        return response.get("sources", response if isinstance(response, _list) else [])

    def get_analytics(self, dashboard_id: int) -> dict[str, Any]:
        """Get dashboard analytics (views, users).

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with analytics data.
        """
        return self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/analytics"
        )

    def share(self, dashboard_id: int, config: dict[str, Any]) -> dict[str, Any]:
        """Share a dashboard.

        Args:
            dashboard_id: ID of the dashboard.
            config: Sharing configuration (users, permissions, etc.).

        Returns:
            Dict with sharing result.
        """
        return self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/share", json=config
        )

    def action(self, dashboard_id: int, action_config: dict[str, Any]) -> dict[str, Any]:
        """Perform an action on a dashboard.

        Args:
            dashboard_id: ID of the dashboard.
            action_config: Action configuration.

        Returns:
            Dict with action result.
        """
        return self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/action", json=action_config
        )

    def get_by_url(self, url: str) -> dict[str, Any]:
        """Get dashboard by URL slug.

        Args:
            url: Dashboard URL slug.

        Returns:
            Dict with dashboard details.
        """
        return self._client._request_json("GET", f"/dashboards/url/{url}")

    def get_draft_data(self, dashboard_id: int, sql: str) -> dict[str, Any]:
        """Get draft data using SQL query.

        Args:
            dashboard_id: ID of the dashboard.
            sql: SQL query to execute against draft data.

        Returns:
            Dict with query results.
        """
        return self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/getDraftData",
            json={"sql": sql},
        )

    def get_publish_data(self, dashboard_id: int, sql: str) -> dict[str, Any]:
        """Get published data using SQL query.

        Args:
            dashboard_id: ID of the dashboard.
            sql: SQL query to execute against published data.

        Returns:
            Dict with query results.
        """
        return self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/getPublishData",
            json={"sql": sql},
        )
