"""
Webhooks API client for managing webhook datasets in Mammoth.

Webhook datasets are HTTP endpoints that receive data into the platform.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.webhooks import WebhookMode

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class WebhooksAPI:
    """Client for managing webhook datasets.

    Access via client.webhooks:
        webhooks = client.webhooks.list()
        webhook = client.webhooks.create(name="My Webhook", mode=WebhookMode.REPLACE)
        client.webhooks.update(webhook_id, mode=WebhookMode.COMBINE)
        client.webhooks.delete(webhook_id)
        client.webhooks.send_data(webhook_uri, {"col1": "val1"})
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

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> _list[dict[str, Any]]:
        """List webhook datasets.

        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of webhook dicts.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks",
            params=params,
        )
        return response.get("webhooks", response if isinstance(response, _list) else [])

    def create(
        self,
        name: str = "Generic Webhook",
        mode: str | WebhookMode = "replace",
        folder_resource_id: str | None = None,
        origins: str = "*",
        is_secure: bool = False,
    ) -> dict[str, Any]:
        """Create a webhook dataset.

        Args:
            name: Name of the webhook.
            mode: Data ingestion mode — "replace" or "combine".
            folder_resource_id: Optional folder to place the webhook in.
            origins: Allowed CORS origins (default "*").
            is_secure: Whether to generate a secret for authentication.

        Returns:
            Dict with created webhook info.
        """
        mode_str = mode.value if isinstance(mode, WebhookMode) else mode
        payload: dict[str, Any] = {
            "name": name,
            "mode": mode_str,
            "origins": origins,
            "is_secure": is_secure,
        }
        if folder_resource_id is not None:
            payload["folder_resource_id"] = folder_resource_id
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks",
            json=payload,
        )

    def get(self, webhook_id: int) -> dict[str, Any]:
        """Get webhook details.

        Args:
            webhook_id: ID of the webhook.

        Returns:
            Dict with webhook details.
        """
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks/{webhook_id}",
        )

    def update(
        self,
        webhook_id: int,
        mode: str | WebhookMode | None = None,
        origins: str | None = None,
        is_secure: bool | None = None,
    ) -> dict[str, Any]:
        """Update a webhook using JSON Patch format.

        Args:
            webhook_id: ID of the webhook.
            mode: New data ingestion mode.
            origins: New allowed CORS origins.
            is_secure: Whether the webhook requires a secret.

        Returns:
            Dict with updated webhook info.
        """
        patch: _list[dict[str, Any]] = []
        if mode is not None:
            mode_str = mode.value if isinstance(mode, WebhookMode) else mode
            patch.append({"op": "replace", "path": "mode", "value": mode_str})
        if origins is not None:
            patch.append({"op": "replace", "path": "origins", "value": origins})
        if is_secure is not None:
            patch.append({"op": "replace", "path": "is_secure", "value": is_secure})
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks/{webhook_id}",
            json={"patch": patch},
        )

    def delete(self, webhook_id: int) -> dict[str, Any]:
        """Delete a webhook.

        Args:
            webhook_id: ID of the webhook.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/webhooks/{webhook_id}",
        )

    def send_data(self, webhook_uri: str, data: dict[str, Any]) -> dict[str, Any]:
        """Send data to a webhook via POST.

        Args:
            webhook_uri: The webhook URI path (e.g. "nHC1zIl97JzgDMopgcfpOgLV").
            data: Data payload to send.

        Returns:
            Dict with the API response.
        """
        return self._client._request_json(
            "POST",
            f"/webhooks/data/{webhook_uri}",
            json=data,
        )

    def send_data_get(
        self,
        webhook_uri: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send data to a webhook via GET query parameters.

        Args:
            webhook_uri: The webhook URI path (e.g. "nHC1zIl97JzgDMopgcfpOgLV").
            params: Data as query parameters.

        Returns:
            Dict with the API response.
        """
        return self._client._request_json(
            "GET",
            f"/webhooks/data/{webhook_uri}",
            params=params,
        )
