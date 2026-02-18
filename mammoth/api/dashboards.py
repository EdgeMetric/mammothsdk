"""
Dashboards API client for managing dashboards in Mammoth.
"""

from typing import Optional, Dict, Any


class DashboardsAPI:
    """Client for managing Mammoth dashboards.

    Access via client.dashboards:
        dashboards = client.dashboards.list()
        dashboard = client.dashboards.create(config={...})
        client.dashboards.share(dashboard_id, config={...})
        client.dashboards.delete(dashboard_id)
    """

    def __init__(self, client):
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> list:
        """List all dashboards.

        Returns:
            List of dashboard dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/dashboards")
        return response.get("dashboards", response if isinstance(response, list) else [])

    def create(self, config: Dict[str, Any]) -> dict:
        """Create a new dashboard.

        Args:
            config: Dashboard configuration (name, sources, layout, etc.).

        Returns:
            Dict with created dashboard info (may include job ID for async creation).
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/dashboards", json=config)

    def get(self, dashboard_id: int) -> dict:
        """Get dashboard details.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with dashboard details.
        """
        return self._client._request("GET", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}")

    def update(self, dashboard_id: int, config: Dict[str, Any]) -> dict:
        """Update a dashboard.

        Args:
            dashboard_id: ID of the dashboard.
            config: Updated dashboard configuration.

        Returns:
            Dict with updated dashboard info.
        """
        return self._client._request("PATCH", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}", json=config)

    def delete(self, dashboard_id: int) -> dict:
        """Delete a dashboard.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with deletion result.
        """
        return self._client._request("DELETE", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}")

    def get_sources(self) -> list:
        """Get available dashboard data sources.

        Returns:
            List of source dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/dashboards/sources")
        return response.get("sources", response if isinstance(response, list) else [])

    def get_analytics(self, dashboard_id: int) -> dict:
        """Get dashboard analytics (views, users).

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with analytics data.
        """
        return self._client._request("GET", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}/analytics")

    def share(self, dashboard_id: int, config: Dict[str, Any]) -> dict:
        """Share a dashboard.

        Args:
            dashboard_id: ID of the dashboard.
            config: Sharing configuration (users, permissions, etc.).

        Returns:
            Dict with sharing result.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}/share", json=config)

    def action(self, dashboard_id: int, action_config: Dict[str, Any]) -> dict:
        """Perform an action on a dashboard.

        Args:
            dashboard_id: ID of the dashboard.
            action_config: Action configuration.

        Returns:
            Dict with action result.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}/action", json=action_config)

    def get_by_url(self, url: str) -> dict:
        """Get dashboard by URL slug.

        Args:
            url: Dashboard URL slug.

        Returns:
            Dict with dashboard details.
        """
        return self._client._request("GET", f"/workspaces/{self._ws()}/dashboards/url/{url}")

    def get_draft_data(self, dashboard_id: int, sql: str) -> dict:
        """Get draft data using SQL query.

        Args:
            dashboard_id: ID of the dashboard.
            sql: SQL query to execute against draft data.

        Returns:
            Dict with query results.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}/getDraftData", json={"sql": sql})

    def get_publish_data(self, dashboard_id: int, sql: str) -> dict:
        """Get published data using SQL query.

        Args:
            dashboard_id: ID of the dashboard.
            sql: SQL query to execute against published data.

        Returns:
            Dict with query results.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/dashboards/{dashboard_id}/getPublishData", json={"sql": sql})
