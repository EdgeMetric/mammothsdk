"""Addons API client for managing workspace addons in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class AddonsAPI:
    """Client for managing workspace addons (connectors, storage, users).

    Access via client.addons::

        client.addons.add_connector(config={...})
        client.addons.remove_connector(config={...})
        client.addons.add_storage(config={...})
        client.addons.remove_storage(config={...})
        client.addons.add_users(config={...})
        client.addons.remove_users(config={...})
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> dict[str, Any]:
        """List active addons for the workspace.

        Returns:
            Dict with addon information.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/addons")

    def add_connector(self, config: dict[str, Any]) -> dict[str, Any]:
        """Add a connector addon to the workspace.

        Args:
            config: Connector addon configuration.

        Returns:
            Dict with addon result.
        """
        ws = self._ws()
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/addons/connectors", json=config
        )

    def remove_connector(self, config: dict[str, Any]) -> dict[str, Any]:
        """Remove a connector addon from the workspace.

        Args:
            config: Connector addon identification (connector_id, etc.).

        Returns:
            Dict with removal result.
        """
        ws = self._ws()
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/addons/connectors", json=config
        )

    def add_storage(self, config: dict[str, Any]) -> dict[str, Any]:
        """Add a storage addon to the workspace.

        Args:
            config: Storage addon configuration.

        Returns:
            Dict with addon result.
        """
        ws = self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/addons/storage", json=config)

    def remove_storage(self, config: dict[str, Any]) -> dict[str, Any]:
        """Remove a storage addon from the workspace.

        Args:
            config: Storage addon identification.

        Returns:
            Dict with removal result.
        """
        ws = self._ws()
        return self._client._request_json("DELETE", f"/workspaces/{ws}/addons/storage", json=config)

    def add_users(self, config: dict[str, Any]) -> dict[str, Any]:
        """Add a users addon to the workspace.

        Args:
            config: Users addon configuration.

        Returns:
            Dict with addon result.
        """
        ws = self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/addons/users", json=config)

    def remove_users(self, config: dict[str, Any]) -> dict[str, Any]:
        """Remove a users addon from the workspace.

        Args:
            config: Users addon identification.

        Returns:
            Dict with removal result.
        """
        ws = self._ws()
        return self._client._request_json("DELETE", f"/workspaces/{ws}/addons/users", json=config)
