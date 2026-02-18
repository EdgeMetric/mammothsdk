"""
Webhooks API client for managing event notification webhooks in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class WebhooksAPI:
    """Client for managing webhooks for event notifications.

    Access via client.webhooks:
        webhooks = client.webhooks.list()
        webhook = client.webhooks.create(config={"name": "...", "url": "...", "events": [...]})
        client.webhooks.delete(webhook_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self) -> int:
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return proj

    def list(self) -> _list[dict[str, Any]]:
        """List all webhooks.

        Returns:
            List of webhook dicts.
        """
        response = self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks"
        )
        return response.get("webhooks", response if isinstance(response, _list) else [])

    def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new webhook.

        Args:
            config: Webhook configuration (name, url, events, secret, etc.).

        Returns:
            Dict with created webhook info.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks", json=config
        )

    def get(self, webhook_id: int) -> dict[str, Any]:
        """Get webhook details.

        Args:
            webhook_id: ID of the webhook.

        Returns:
            Dict with webhook details.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks/{webhook_id}"
        )

    def update(self, webhook_id: int, config: dict[str, Any]) -> dict[str, Any]:
        """Update a webhook.

        Args:
            webhook_id: ID of the webhook.
            config: Updated webhook configuration.

        Returns:
            Dict with updated webhook info.
        """
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks/{webhook_id}",
            json=config,
        )

    def delete(self, webhook_id: int) -> dict[str, Any]:
        """Delete a webhook.

        Args:
            webhook_id: ID of the webhook.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE", f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks/{webhook_id}"
        )
