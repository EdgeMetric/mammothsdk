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

    def list(self) -> _list[dict[str, Any]]:
        """List all available connectors.

        Returns:
            List of connector dicts.
        """
        response = self._client._request_json("GET", f"/workspaces/{self._ws()}/connectors")
        return response.get("connectors", response if isinstance(response, _list) else [])

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

    def list_connections(self, connector_key: str) -> _list[dict[str, Any]]:
        """List connections for a connector type.

        Args:
            connector_key: Key identifying the connector type.

        Returns:
            List of connection dicts.
        """
        response = self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/connectors/{connector_key}/connections"
        )
        return response.get("connections", response if isinstance(response, _list) else [])

    def create_connection(self, connector_key: str, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new connection for a connector.

        Args:
            connector_key: Key identifying the connector type.
            config: Connection configuration (host, port, database, credentials, etc.).

        Returns:
            Dict with created connection info.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/connectors/{connector_key}/connections", json=config
        )

    def get_connection(self, connector_key: str, connection_key: str) -> dict[str, Any]:
        """Get details of a specific connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.

        Returns:
            Dict with connection details.
        """
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}",
        )

    def update_connection(
        self, connector_key: str, connection_key: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a connection's configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            config: Updated connection configuration.

        Returns:
            Dict with updated connection info.
        """
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}",
            json=config,
        )

    def delete_connection(self, connector_key: str, connection_key: str) -> dict[str, Any]:
        """Delete a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}",
        )

    def list_ds_configs(self, connector_key: str, connection_key: str) -> _list[dict[str, Any]]:
        """List data source configurations for a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.

        Returns:
            List of data source config dicts.
        """
        response = self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}/ds_configs",
        )
        return response.get("ds_configs", response if isinstance(response, _list) else [])

    def create_ds_config(
        self, connector_key: str, connection_key: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            config: Data source configuration.

        Returns:
            Dict with created data source config.
        """
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}/ds_configs",
            json=config,
        )

    def get_ds_config(
        self, connector_key: str, connection_key: str, ds_config_key: str
    ) -> dict[str, Any]:
        """Get a specific data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.

        Returns:
            Dict with data source config details.
        """
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
        )

    def update_ds_config(
        self, connector_key: str, connection_key: str, ds_config_key: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            config: Updated data source configuration.

        Returns:
            Dict with updated config.
        """
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
            json=config,
        )

    def delete_ds_config(
        self, connector_key: str, connection_key: str, ds_config_key: str
    ) -> dict[str, Any]:
        """Delete a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
        )

    def active_connectors(self) -> _list[dict[str, Any]]:
        """List active connectors with established connections.

        Returns:
            List of active connector dicts.
        """
        response = self._client._request_json("GET", f"/workspaces/{self._ws()}/active_connectors")
        return response.get("connectors", response if isinstance(response, _list) else [])
