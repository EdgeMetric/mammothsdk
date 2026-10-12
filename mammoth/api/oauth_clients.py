"""OAuth clients API: the apps a workspace registers to sign users in through Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias: OAuthClientsAPI.list shadows the builtin in later annotations.


class OAuthClientsAPI:
    """Client for a workspace's OAuth clients.

    Access via ``client.oauth_clients``::

        created = await client.oauth_clients.create(
            "Reporting app", ["https://app.example.com/callback"]
        )
        # created["client_secret"] is returned once; store it at once.
        await client.oauth_clients.revoke_grant(created["id"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self, workspace_id: int | None) -> int:
        return workspace_id or self._client.workspace_id

    async def list(self, workspace_id: int | None = None) -> dict[str, Any]:
        """List the workspace's OAuth clients.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict ``{"result": [...]}``; each client has ``id``, ``client_id``, ``name``,
            ``redirect_uris``, ``token_endpoint_auth_method`` and ``created_at``.
            No secret is returned here.
        """
        return await self._client._request_json(
            "GET", f"/workspaces/{self._ws(workspace_id)}/oauth-clients"
        )

    async def create(
        self,
        name: str,
        redirect_uris: _list[str],
        *,
        description: str | None = None,
        logo_url: str | None = None,
        tos_url: str | None = None,
        privacy_url: str | None = None,
        token_endpoint_auth_method: str = "client_secret_basic",
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Register an OAuth client in the workspace.

        Args:
            name: Name shown on the consent screen (1 to 100 characters).
            redirect_uris: Allowed redirect URIs (1 to 10).
            description: Optional description (up to 500 characters).
            logo_url: Optional https:// logo URL for the consent screen.
            tos_url: Optional https:// terms-of-service URL.
            privacy_url: Optional https:// privacy-policy URL.
            token_endpoint_auth_method: ``client_secret_basic`` (confidential, the
                default) or ``none`` (a public client with PKCE and no secret).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with the new client. A confidential client also has
            ``client_secret``, returned exactly once.
        """
        body: dict[str, Any] = {
            "name": name,
            "redirect_uris": redirect_uris,
            "token_endpoint_auth_method": token_endpoint_auth_method,
            **{
                key: value
                for key, value in (
                    ("description", description),
                    ("logo_url", logo_url),
                    ("tos_url", tos_url),
                    ("privacy_url", privacy_url),
                )
                if value is not None
            },
        }
        return await self._client._request_json(
            "POST", f"/workspaces/{self._ws(workspace_id)}/oauth-clients", json=body
        )

    async def delete(self, oauth_client_id: int, workspace_id: int | None = None) -> dict[str, Any]:
        """Delete an OAuth client. Its grants stop working.

        Args:
            oauth_client_id: ID of the OAuth client.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Empty dict on success (the server answers 204).
        """
        return await self._client._request_json(
            "DELETE", f"/workspaces/{self._ws(workspace_id)}/oauth-clients/{oauth_client_id}"
        )

    async def revoke_grant(
        self, oauth_client_id: int, workspace_id: int | None = None
    ) -> dict[str, Any]:
        """Revoke every grant the client holds, so its users must authorise again.

        Args:
            oauth_client_id: ID of the OAuth client.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Empty dict on success (the server answers 204).
        """
        return await self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws(workspace_id)}/oauth-clients/{oauth_client_id}/grant",
        )
