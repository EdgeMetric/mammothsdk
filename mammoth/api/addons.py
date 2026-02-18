"""Addons API client for managing workspace addons in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class AddonsAPI:
    """Client for managing workspace addons (connectors, storage, users).

    Access via client.addons::

        addons = client.addons.list()
        client.addons.activate(addon_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> dict[str, Any]:
        """List available addons for the workspace.

        Returns:
            Dict with addons list.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/addons")

    def get(self, addon_id: int) -> dict[str, Any]:
        """Get addon details.

        Args:
            addon_id: ID of the addon.

        Returns:
            Dict with addon details.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/addons/{addon_id}")

    def activate(self, addon_id: int) -> dict[str, Any]:
        """Activate an addon.

        Args:
            addon_id: ID of the addon to activate.

        Returns:
            Dict with activation result.
        """
        ws = self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/addons/{addon_id}/activate")

    def deactivate(self, addon_id: int) -> dict[str, Any]:
        """Deactivate an addon.

        Args:
            addon_id: ID of the addon to deactivate.

        Returns:
            Dict with deactivation result.
        """
        ws = self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/addons/{addon_id}/deactivate")

    def get_usage(self, addon_id: int) -> dict[str, Any]:
        """Get addon usage statistics.

        Args:
            addon_id: ID of the addon.

        Returns:
            Dict with usage statistics.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/addons/{addon_id}/usage")

    def update_config(self, addon_id: int, config: dict[str, Any]) -> dict[str, Any]:
        """Update addon configuration.

        Args:
            addon_id: ID of the addon.
            config: Updated configuration.

        Returns:
            Dict with updated addon info.
        """
        ws = self._ws()
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/addons/{addon_id}",
            json=config,
        )
