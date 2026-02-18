"""External Keys API client for managing API keys in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class ExternalKeysAPI:
    """Client for managing external API keys.

    Access via client.external_keys::

        keys = client.external_keys.list()
        key = client.external_keys.create(name="My Key")
        client.external_keys.delete(key_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> dict[str, Any]:
        """List all external API keys.

        Returns:
            Dict with API keys list.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/external_keys")

    def get(self, key_id: int) -> dict[str, Any]:
        """Get external key details.

        Args:
            key_id: ID of the API key.

        Returns:
            Dict with key details.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/external_keys/{key_id}")

    def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new external API key.

        Args:
            config: Key configuration (name, permissions, etc.).

        Returns:
            Dict with created key info.
        """
        ws = self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/external_keys", json=config)

    def delete(self, key_id: int) -> dict[str, Any]:
        """Delete an external API key.

        Args:
            key_id: ID of the key to delete.

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        return self._client._request_json("DELETE", f"/workspaces/{ws}/external_keys/{key_id}")
