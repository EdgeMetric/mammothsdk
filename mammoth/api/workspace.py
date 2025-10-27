"""
Workspace API client for managing workspaces in Mammoth.
"""

from typing import Dict, Any


class WorkspaceAPI:
    """Client for interacting with Mammoth Workspace API."""
    
    def __init__(self, client):
        self._client = client
    
    def list_workspaces(self, limit: int = 100) -> Dict[str, Any]:
        """
        List all accessible workspaces.
        
        Args:
            limit: Maximum number of results (default: 100)
            
        Returns:
            Dict containing workspaces with id and name
            
        Raises:
            MammothAPIError: If the API request fails
        """
        params = {
            "fields": "id,name",
            "limit": limit
        }
            
        response = self._client._request(
            "GET",
            "/workspaces",
            params=params
        )
        return response