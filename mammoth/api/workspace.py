"""
Workspace API client for managing workspaces in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class WorkspaceAPI:
    """Client for interacting with Mammoth Workspace API.

    Access via client.workspaces:
        workspaces = client.workspaces.list()
        workspace = client.workspaces.get()
        users = client.workspaces.list_users()
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self, limit: int = 100) -> dict[str, Any]:
        """List all accessible workspaces.

        Args:
            limit: Maximum number of results (default 100).

        Returns:
            Dict containing workspaces list with id and name.
        """
        params = {"fields": "id,name", "limit": limit}
        return self._client._request_json("GET", "/workspaces", params=params)

    def get(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Get details of a specific workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with workspace details.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}")

    def update(self, config: dict[str, Any], workspace_id: int | None = None) -> dict[str, Any]:
        """Update workspace settings.

        Args:
            config: Patch operations for the workspace.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated workspace info.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("PATCH", f"/workspaces/{ws}", json=config)

    def delete(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Delete a workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("DELETE", f"/workspaces/{ws}")

    def reactivate(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Reactivate a deactivated workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with reactivation result.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/reactivate")

    def list_users(self, workspace_id: int | None = None) -> _list[dict[str, Any]]:
        """List all users in a workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            List of user dicts.
        """
        ws = workspace_id or self._ws()
        response = self._client._request_json("GET", f"/workspaces/{ws}/users")
        return response.get("users", response if isinstance(response, _list) else [])

    def get_user(self, user_id: str, workspace_id: int | None = None) -> dict[str, Any]:
        """Get details of a specific user.

        .. note::

            Requires workspace admin permissions. Non-admin users may
            receive HTTP 405.

        Args:
            user_id: ID of the user.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with user details.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/users/{user_id}")

    def update_user(
        self, user_id: str, config: dict[str, Any], workspace_id: int | None = None
    ) -> dict[str, Any]:
        """Update a user's settings in the workspace.

        Args:
            user_id: ID of the user.
            config: Patch operations for the user.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated user info.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("PATCH", f"/workspaces/{ws}/users/{user_id}", json=config)
