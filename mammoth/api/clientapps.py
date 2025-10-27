"""
Client Apps API for managing API tokens and client applications in Mammoth.
"""

from typing import Optional, List
from ..models.clientapps import (
    ClientAppsListResponse, ClientAppSchema, ClientAppPostResponse, 
    ClientAppCreate, PatchRequest
)


class ClientAppsAPI:
    """Client for interacting with Mammoth Client Apps API."""
    
    def __init__(self, client):
        self._client = client
        self._workspace_id = None
    
    def _get_workspace_id(self) -> int:
        """
        Get the workspace ID associated with the current API credentials.
        Uses the main client's get_workspace_id method.
        """
        workspace_id = self._client.get_workspace_id()
        if workspace_id is None:
            raise ValueError("Unable to determine workspace ID from API credentials")
        return workspace_id
    
    def list_client_apps(
        self,
        workspace_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
        fields: Optional[str] = None,
        sort: Optional[str] = None
    ) -> ClientAppsListResponse:
        """
        List client apps for a workspace.
        
        Args:
            workspace_id: ID of the workspace (auto-detected if not provided)
            limit: Maximum number of results (0-100, default: 10)
            offset: Number of results to skip (default: 0)
            fields: Fields to return (e.g., "id,app_name", default: "__standard")
            sort: Sort specification (e.g., "(last_usage:asc),(id:desc)")
            
        Returns:
            ClientAppsListResponse: List of client apps
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._get_workspace_id()
            
        params = {}
        if limit != 10:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if fields:
            params["fields"] = fields
        if sort:
            params["sort"] = sort
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/clientapps",
            params=params
        )
        return ClientAppsListResponse(**response)
    
    def create_client_app(
        self,
        app_name: str,
        description: Optional[str] = None,
        workspace_id: Optional[int] = None
    ) -> ClientAppPostResponse:
        """
        Create a new client app to generate API tokens.
        
        Args:
            app_name: Name for the client app
            description: Optional description for the app
            workspace_id: ID of the workspace (auto-detected if not provided)
            
        Returns:
            ClientAppPostResponse: Created client app details with tokens
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._get_workspace_id()
            
        payload = {"app_name": app_name}
        if description:
            payload["description"] = description
            
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/clientapps",
            json=payload
        )
        return ClientAppPostResponse(**response)
    
    def get_client_app(
        self,
        client_key: str,
        workspace_id: Optional[int] = None,
        fields: Optional[str] = None
    ) -> ClientAppSchema:
        """
        Get details of a specific client app.
        
        Args:
            client_key: Client key/ID of the app
            workspace_id: ID of the workspace (auto-detected if not provided)
            fields: Fields to return (e.g., "id,app_name", default: "__standard")
            
        Returns:
            ClientAppSchema: Client app details
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._get_workspace_id()
            
        params = {}
        if fields:
            params["fields"] = fields
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/clientapps/{client_key}",
            params=params
        )
        return ClientAppSchema(**response)
    
    def update_client_app(
        self,
        client_key: str,
        patch_request: PatchRequest,
        workspace_id: Optional[int] = None
    ) -> ClientAppSchema:
        """
        Update client app details like name, description, etc.
        
        Args:
            client_key: Client key/ID of the app
            patch_request: PatchRequest containing patch operations
            workspace_id: ID of the workspace (auto-detected if not provided)
            
        Returns:
            ClientAppSchema: Updated client app details
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._get_workspace_id()
            
        response = self._client._request(
            "PATCH",
            f"/workspaces/{workspace_id}/clientapps/{client_key}",
            json=patch_request.dict()
        )
        return ClientAppSchema(**response)
    
    def delete_client_app(
        self,
        client_key: str,
        workspace_id: Optional[int] = None
    ) -> None:
        """
        Delete a client app.
        
        Args:
            client_key: Client key/ID of the app to delete
            workspace_id: ID of the workspace (auto-detected if not provided)
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._get_workspace_id()
            
        self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/clientapps/{client_key}"
        )