"""
Client Apps API for managing API tokens and client applications in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

from pydantic import ValidationError

from ..models.clientapps import (
    ClientAppPostResponse,
    ClientAppSchema,
    ClientAppsListResponse,
    PatchRequest,
)


class ClientAppsAPI:
    """Client for interacting with Mammoth Client Apps API.

    Access via client.client_apps:
        apps = client.client_apps.list()
        app = client.client_apps.create(app_name="My App")
        client.client_apps.delete(client_key="...")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    async def list(
        self,
        workspace_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
        fields: str | None = None,
        sort: str | None = None,
    ) -> ClientAppsListResponse:
        """List client apps for a workspace.

        .. note::

            Requires admin role — non-admin users receive HTTP 401.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            limit: Maximum number of results (0-100, default 10).
            offset: Number of results to skip (default 0).
            fields: Fields to return (e.g., "id,app_name").
            sort: Sort specification.

        Returns:
            ClientAppsListResponse with list of client apps.
        """
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {}
        if limit != 10:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if fields:
            params["fields"] = fields
        if sort:
            params["sort"] = sort
        response = await self._client._request_json(
            "GET", f"/workspaces/{ws}/clientapps", params=params
        )
        return ClientAppsListResponse(**response)

    async def create(
        self,
        app_name: str,
        description: str | None = None,
        workspace_id: int | None = None,
    ) -> ClientAppPostResponse:
        """Create a new client app to generate API tokens.

        Args:
            app_name: Name for the client app.
            description: Optional description.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            ClientAppPostResponse with created app details and tokens.
        """
        ws = workspace_id or self._ws()
        payload = {"app_name": app_name, "description": description or ""}
        response = await self._client._request_json(
            "POST", f"/workspaces/{ws}/clientapps", json=payload
        )
        try:
            return ClientAppPostResponse(**response)
        except ValidationError:
            # The key already exists and its token is shown only in this
            # response: hand it back rather than lose it to a model mismatch.
            return ClientAppPostResponse.model_construct(**response)

    async def get(
        self,
        client_key: str,
        workspace_id: int | None = None,
        fields: str | None = None,
    ) -> ClientAppSchema:
        """Get details of a specific client app.

        Args:
            client_key: Client key/ID of the app.
            workspace_id: ID of the workspace (uses client default if not provided).
            fields: Fields to return.

        Returns:
            ClientAppSchema with client app details.
        """
        ws = workspace_id or self._ws()
        params = {}
        if fields:
            params["fields"] = fields
        response = await self._client._request_json(
            "GET", f"/workspaces/{ws}/clientapps/{client_key}", params=params
        )
        return ClientAppSchema(**response)

    async def update(
        self,
        client_key: str,
        patch_request: PatchRequest,
        workspace_id: int | None = None,
    ) -> ClientAppSchema:
        """Update client app details.

        Args:
            client_key: Client key/ID of the app.
            patch_request: PatchRequest containing patch operations.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            ClientAppSchema with updated details.
        """
        ws = workspace_id or self._ws()
        response = await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/clientapps/{client_key}", json=patch_request.model_dump()
        )
        return ClientAppSchema(**response)

    async def delete(
        self,
        client_key: str,
        workspace_id: int | None = None,
    ) -> None:
        """Delete a client app.

        Args:
            client_key: Client key/ID of the app to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        await self._client._request_json("DELETE", f"/workspaces/{ws}/clientapps/{client_key}")
