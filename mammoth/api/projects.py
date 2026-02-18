"""
Projects API client for managing projects in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class ProjectsAPI:
    """Client for interacting with Mammoth Projects API.

    Access via client.projects:
        projects = client.projects.list()
        project = client.projects.get(123)
        client.projects.create(name="Analytics")
        client.projects.update(123, name="Analytics v2")
        client.projects.delete(123)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(
        self,
        workspace_id: int | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List all projects in a workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            limit: Maximum number of results (default 100).

        Returns:
            Dict containing projects list with id and name.
        """
        ws = workspace_id or self._ws()
        params = {"fields": "id,name", "limit": limit}
        return self._client._request_json("GET", f"/workspaces/{ws}/projects", params=params)

    def get(
        self,
        project: int | str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Get a single project by ID, name, or auto-selection.

        Behavior:
        - project=None: Auto-select if only 1 project exists.
        - project=123: Find project with ID 123.
        - project="My Project": Find project by name.

        Args:
            project: Project ID (int), name (str), or None for auto-selection.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with project id and name.

        Raises:
            ValueError: If project not found or multiple projects without specification.
        """
        projects_response = self.list(workspace_id=workspace_id)
        projects = projects_response.get("projects", [])

        if not projects:
            raise ValueError("No projects found in workspace")

        if isinstance(project, int):
            matching = [p for p in projects if p["id"] == project]
            if not matching:
                available = [(p["name"], p["id"]) for p in projects]
                raise ValueError(f"Project ID {project} not found. Available projects: {available}")
            return {"id": matching[0]["id"], "name": matching[0]["name"]}

        if project is None:
            if len(projects) == 1:
                return {"id": projects[0]["id"], "name": projects[0]["name"]}
            project_list = "\n".join([f"  - {p['name']} (ID: {p['id']})" for p in projects])
            raise ValueError(
                f"Multiple projects found ({len(projects)}). "
                f"Please specify project by name or ID:\n{project_list}"
            )

        if isinstance(project, str):
            matching = [p for p in projects if p["name"] == project]
            if not matching:
                available = [p["name"] for p in projects]
                raise ValueError(f"Project '{project}' not found. Available projects: {available}")
            if len(matching) > 1:
                project_list = "\n".join([f"  - {p['name']} (ID: {p['id']})" for p in matching])
                raise ValueError(
                    f"Multiple projects found with name '{project}':\n{project_list}\n"
                    "Please specify project by ID instead."
                )
            return {"id": matching[0]["id"], "name": matching[0]["name"]}

        raise ValueError(f"Invalid project type: {type(project)}. Expected int, str, or None")

    def create(
        self,
        name: str,
        color: str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            name: Name for the new project.
            color: Color code for the project (optional).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with created project info.
        """
        ws = workspace_id or self._ws()
        payload: dict[str, Any] = {"name": name}
        if color:
            payload["color"] = color
        return self._client._request_json("POST", f"/workspaces/{ws}/projects", json=payload)

    def update(
        self,
        project_id: int,
        name: str | None = None,
        color: str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a project.

        Args:
            project_id: ID of the project to update.
            name: New name (optional).
            color: New color code (optional).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated project info.
        """
        ws = workspace_id or self._ws()
        operations = []
        if name is not None:
            operations.append({"op": "replace", "path": "/name", "value": name})
        if color is not None:
            operations.append({"op": "replace", "path": "/color", "value": color})
        payload = {"patch": operations}
        return self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{project_id}", json=payload
        )

    def delete(
        self,
        project_id: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a project.

        Args:
            project_id: ID of the project to delete.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("DELETE", f"/workspaces/{ws}/projects/{project_id}")

    def bulk_update(
        self,
        patch_data: dict[str, Any],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Bulk update multiple projects.

        Args:
            patch_data: Patch operations for multiple projects.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with bulk update result.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("PATCH", f"/workspaces/{ws}/projects", json=patch_data)

    def bulk_delete(
        self,
        project_ids: _list[int],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Bulk delete multiple projects.

        Args:
            project_ids: List of project IDs to delete.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with bulk deletion result.
        """
        ws = workspace_id or self._ws()
        ids_str = ",".join(str(pid) for pid in project_ids)
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects", params={"ids": ids_str}
        )

    def add_users(
        self,
        project_id: int,
        user_ids: _list[str],
        role: str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Add users to a project.

        Args:
            project_id: ID of the project.
            user_ids: List of user email addresses or IDs.
            role: Role to assign (optional).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with result.
        """
        ws = workspace_id or self._ws()
        payload: dict[str, Any] = {"user_emails": user_ids}
        if role:
            payload["role"] = role
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{project_id}/users", json=payload
        )

    def remove_users(
        self,
        project_id: int,
        user_ids: _list[str],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Remove users from a project.

        Args:
            project_id: ID of the project.
            user_ids: List of user IDs to remove.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with result.
        """
        ws = workspace_id or self._ws()
        ids_str = ",".join(str(uid) for uid in user_ids)
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{project_id}/users", params={"ids": ids_str}
        )

    def browse(
        self,
        project_id: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Browse project contents (datasets, folders).

        Args:
            project_id: ID of the project.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with project contents.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/projects/{project_id}/browse")
