"""
Connectors API client for managing cloud data source connectors and connections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class ConnectorsAPI:
    """Client for managing cloud data source connectors and connections.

    Access via client.connectors:
        connectors = client.connectors.list()
        conn = client.connectors.create_connection("postgres", config={...})
        client.connectors.delete_connection("postgres", "conn_key")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    def list(self) -> _list[dict[str, Any]]:
        """List all available connectors.

        Returns:
            List of connector dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/connectors")
        if isinstance(response, _list):
            return response
        return response.get("connectors", [])

    def get(self, connector_key: str) -> dict[str, Any]:
        """Get details of a specific connector.

        Args:
            connector_key: Key identifying the connector type (e.g., "postgres", "mysql").

        Returns:
            Dict with connector details.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/connectors/{connector_key}"
        )

    def list_connections(
        self, connector_key: str, project_id: int | None = None
    ) -> _list[dict[str, Any]]:
        """List connections for a connector type.

        Args:
            connector_key: Key identifying the connector type.
            project_id: Project ID (uses client default if not provided).

        Returns:
            List of connection dicts.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        response = self._client._request(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections",
        )
        if isinstance(response, _list):
            return response
        return response.get("connections", [])

    def create_connection(
        self, connector_key: str, config: dict[str, Any], project_id: int | None = None
    ) -> dict[str, Any]:
        """Create a new connection for a connector.

        Args:
            connector_key: Key identifying the connector type.
            config: Connection configuration (host, port, database, credentials, etc.).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with created connection info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections",
            json=config,
        )

    def get_connection(
        self, connector_key: str, connection_key: str, project_id: int | None = None
    ) -> dict[str, Any]:
        """Get details of a specific connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with connection details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}",
        )

    def update_connection(
        self,
        connector_key: str,
        connection_key: str,
        config: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a connection's configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            config: Updated connection configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated connection info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}",
            json=config,
        )

    def delete_connection(
        self, connector_key: str, connection_key: str, project_id: int | None = None
    ) -> dict[str, Any]:
        """Delete a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}",
        )

    def list_ds_configs(
        self, connector_key: str, connection_key: str, project_id: int | None = None
    ) -> _list[dict[str, Any]]:
        """List data source configurations for a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            List of data source config dicts.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        response = self._client._request(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs",
        )
        if isinstance(response, _list):
            return response
        return response.get("ds_configs", [])

    def create_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        config: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            config: Data source configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with created data source config.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs",
            json=config,
        )

    def get_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        ds_config_key: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get a specific data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with data source config details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
        )

    def update_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        ds_config_key: str,
        config: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            config: Updated data source configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated config.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
            json=config,
        )

    def delete_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        ds_config_key: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
        )

    def active_connectors(self) -> _list[dict[str, Any]]:
        """List active connectors with established connections.

        Returns:
            List of active connector dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/active_connectors")
        if isinstance(response, _list):
            return response
        return response.get("connectors", [])
