"""
Workspace API client for managing workspaces in Mammoth.
"""

from typing import Optional, Dict, Any, List


class WorkspaceAPI:
    """Client for interacting with Mammoth Workspace API.

    Access via client.workspaces:
        workspaces = client.workspaces.list()
        workspace = client.workspaces.get()
        users = client.workspaces.list_users()
    """

    def __init__(self, client):
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self, limit: int = 100) -> Dict[str, Any]:
        """List all accessible workspaces.

        Args:
            limit: Maximum number of results (default 100).

        Returns:
            Dict containing workspaces list with id and name.
        """
        params = {"fields": "id,name", "limit": limit}
        return self._client._request("GET", "/workspaces", params=params)

    def get(self, workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Get details of a specific workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with workspace details.
        """
        ws = workspace_id or self._ws()
        return self._client._request("GET", f"/workspaces/{ws}")

    def update(self, config: Dict[str, Any], workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Update workspace settings.

        Args:
            config: Patch operations for the workspace.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated workspace info.
        """
        ws = workspace_id or self._ws()
        return self._client._request("PATCH", f"/workspaces/{ws}", json=config)

    def delete(self, workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Delete a workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        return self._client._request("DELETE", f"/workspaces/{ws}")

    def reactivate(self, workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Reactivate a deactivated workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with reactivation result.
        """
        ws = workspace_id or self._ws()
        return self._client._request("POST", f"/workspaces/{ws}/reactivate")

    def list_users(self, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all users in a workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            List of user dicts.
        """
        ws = workspace_id or self._ws()
        response = self._client._request("GET", f"/workspaces/{ws}/users")
        return response.get("users", response if isinstance(response, list) else [])

    def get_user(self, user_id: str, workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Get details of a specific user.

        Args:
            user_id: ID of the user.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with user details.
        """
        ws = workspace_id or self._ws()
        return self._client._request("GET", f"/workspaces/{ws}/users/{user_id}")

    def update_user(self, user_id: str, config: Dict[str, Any], workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Update a user's settings in the workspace.

        Args:
            user_id: ID of the user.
            config: Patch operations for the user.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated user info.
        """
        ws = workspace_id or self._ws()
        return self._client._request("PATCH", f"/workspaces/{ws}/users/{user_id}", json=config)
