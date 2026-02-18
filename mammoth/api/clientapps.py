"""
Client Apps API for managing API tokens and client applications in Mammoth.
"""

from typing import Optional
from ..models.clientapps import (
    ClientAppsListResponse, ClientAppSchema, ClientAppPostResponse,
    ClientAppCreate, PatchRequest
)


class ClientAppsAPI:
    """Client for interacting with Mammoth Client Apps API.

    Access via client.client_apps:
        apps = client.client_apps.list()
        app = client.client_apps.create(app_name="My App")
        client.client_apps.delete(client_key="...")
    """

    def __init__(self, client):
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(
        self,
        workspace_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> ClientAppsListResponse:
        """List client apps for a workspace.

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
        params = {}
        if limit != 10:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if fields:
            params["fields"] = fields
        if sort:
            params["sort"] = sort
        response = self._client._request("GET", f"/workspaces/{ws}/clientapps", params=params)
        return ClientAppsListResponse(**response)

    def create(
        self,
        app_name: str,
        description: Optional[str] = None,
        workspace_id: Optional[int] = None,
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
        payload = {"app_name": app_name}
        if description:
            payload["description"] = description
        response = self._client._request("POST", f"/workspaces/{ws}/clientapps", json=payload)
        return ClientAppPostResponse(**response)

    def get(
        self,
        client_key: str,
        workspace_id: Optional[int] = None,
        fields: Optional[str] = None,
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
        response = self._client._request("GET", f"/workspaces/{ws}/clientapps/{client_key}", params=params)
        return ClientAppSchema(**response)

    def update(
        self,
        client_key: str,
        patch_request: PatchRequest,
        workspace_id: Optional[int] = None,
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
        response = self._client._request("PATCH", f"/workspaces/{ws}/clientapps/{client_key}", json=patch_request.dict())
        return ClientAppSchema(**response)

    def delete(
        self,
        client_key: str,
        workspace_id: Optional[int] = None,
    ) -> None:
        """Delete a client app.

        Args:
            client_key: Client key/ID of the app to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        self._client._request("DELETE", f"/workspaces/{ws}/clientapps/{client_key}")
