"""
Webhooks API client for managing event notification webhooks in Mammoth.
"""

from typing import Dict, Any


class WebhooksAPI:
    """Client for managing webhooks for event notifications.

    Access via client.webhooks:
        webhooks = client.webhooks.list()
        webhook = client.webhooks.create(config={"name": "...", "url": "...", "events": [...]})
        client.webhooks.delete(webhook_id)
    """

    def __init__(self, client):
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> list:
        """List all webhooks.

        Returns:
            List of webhook dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/webhooks")
        return response.get("webhooks", response if isinstance(response, list) else [])

    def create(self, config: Dict[str, Any]) -> dict:
        """Create a new webhook.

        Args:
            config: Webhook configuration (name, url, events, secret, etc.).

        Returns:
            Dict with created webhook info.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/webhooks", json=config)

    def get(self, webhook_id: int) -> dict:
        """Get webhook details.

        Args:
            webhook_id: ID of the webhook.

        Returns:
            Dict with webhook details.
        """
        return self._client._request("GET", f"/workspaces/{self._ws()}/webhooks/{webhook_id}")

    def update(self, webhook_id: int, config: Dict[str, Any]) -> dict:
        """Update a webhook.

        Args:
            webhook_id: ID of the webhook.
            config: Updated webhook configuration.

        Returns:
            Dict with updated webhook info.
        """
        return self._client._request("PATCH", f"/workspaces/{self._ws()}/webhooks/{webhook_id}", json=config)

    def delete(self, webhook_id: int) -> dict:
        """Delete a webhook.

        Args:
            webhook_id: ID of the webhook.

        Returns:
            Dict with deletion result.
        """
        return self._client._request("DELETE", f"/workspaces/{self._ws()}/webhooks/{webhook_id}")
