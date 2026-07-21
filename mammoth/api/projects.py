"""
Projects API client for managing projects in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_USER_OR_INVITE_ID_REQUIRED = (
    "Exactly one of `user_id` or `invite_id` must be provided, got user_id={0!r}, "
    "invite_id={1!r}."
)


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
        project_access: str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            name: Name for the new project.
            color: Color hex code (e.g., "#337FBD"). Defaults to server-assigned color.
            project_access: Access level — "only_me", "some_members_of_workspace",
                or "all_members_of_workspace". Defaults to "only_me".
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with created project info including id, name, properties, etc.
        """
        ws = workspace_id or self._ws()
        properties: dict[str, Any] = {}
        if color:
            properties["color"] = color
        if project_access:
            properties["project_access"] = project_access
        payload: dict[str, Any] = {"name": name, "properties": properties}
        return self._client._request_json("POST", f"/workspaces/{ws}/projects", json=payload)

    def update(
        self,
        project_id: int,
        name: str | None = None,
        color: str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a project.

        .. note::

            Requires admin role — non-admin users receive HTTP 401.

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
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects", params={"ids": str(project_id)}
        )

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
        fields: str | None = None,
        name: str | None = None,
        browse_type: str | None = None,
        sort: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Browse project contents (datasets, folders).

        .. note::

            This endpoint may return HTTP 500 on some server versions.

        Args:
            project_id: ID of the project.
            workspace_id: ID of the workspace (uses client default if not provided).
            fields: Comma-separated list of fields to return.
            name: Filter by name.
            browse_type: Filter by resource type.
            sort: Sort specification.
            offset: Number of results to skip.
            limit: Maximum number of results.

        Returns:
            Dict with project contents.
        """
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if name is not None:
            params["name"] = name
        if browse_type is not None:
            params["browse_type"] = browse_type
        if sort is not None:
            params["sort"] = sort
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/browse",
            params=params or None,
        )

    def checkpoint_list(
        self,
        project_id: int,
        workspace_id: int | None = None,
        fields: str | None = None,
        sort: str | None = None,
        dataview_id: int | None = None,
        sequence: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List pipeline checkpoints across all dataviews in a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).
            fields: Fields to return (e.g., "__standard", "__full", "__min").
            sort: Sort specification.
            dataview_id: Filter to checkpoints for a specific dataview.
            sequence: Filter by pipeline task sequence number.
            status: Filter by checkpoint status.

        Returns:
            Dict with the checkpoints list.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        if dataview_id is not None:
            params["dataview_id"] = dataview_id
        if sequence is not None:
            params["sequence"] = sequence
        if status is not None:
            params["status"] = status
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/checkpoints",
            params=params or None,
        )

    def data_check_list(
        self,
        project_id: int,
        workspace_id: int | None = None,
        fields: str | None = None,
        sort: str | None = None,
        dataview_id: int | None = None,
        sequence: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List data checks across all dataviews in a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).
            fields: Fields to return (e.g., "__standard", "__full", "__min").
            sort: Sort specification.
            dataview_id: Filter to data checks for a specific dataview.
            sequence: Filter by pipeline task sequence number.
            status: Filter by data check status.

        Returns:
            Dict with the data checks list.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        if dataview_id is not None:
            params["dataview_id"] = dataview_id
        if sequence is not None:
            params["sequence"] = sequence
        if status is not None:
            params["status"] = status
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/data-checks",
            params=params or None,
        )

    def pending_changes(
        self,
        project_id: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Get pending (uncommitted) changes for a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict describing the project's pending changes.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{project_id}/pending-changes"
        )

    def publish_credentials(
        self,
        project_id: int,
        odbc_type: Literal["postgres", "bigquery"],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Get ODBC publish credentials for a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            odbc_type: ODBC connector type — "postgres" or "bigquery".
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with the publish credentials.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/credentials",
            params={"odbc_type": odbc_type},
        )

    def resource_dependencies(
        self,
        project_id: int,
        resource_ids: _list[str],
        is_recursive: bool | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the dependency graph for a set of resources in a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            resource_ids: Resource IDs to look up dependencies for.
            is_recursive: Recursively traverse the dependency graph.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict keyed by resource_id with each resource's dependency graph.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {"resource_ids": ",".join(resource_ids)}
        if is_recursive is not None:
            params["is_recursive"] = is_recursive
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/resource-dependencies",
            params=params,
        )

    def resource_status(
        self,
        project_id: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Get resource status summary for a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with the project's resource status summary.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{project_id}/resource-status"
        )

    def sample_flow(
        self,
        project_id: int,
        label_resource_id: int | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a sample flow: ingest a sample file into the project.

        Args:
            project_id: ID of the project (must be a positive integer).
            label_resource_id: Parent folder resource ID to place the imported
                file under (optional; defaults to the project root).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with the created sample file's name and ingestion job_id.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        payload: dict[str, Any] = {}
        if label_resource_id is not None:
            payload["label_resource_id"] = label_resource_id
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{project_id}/sample-flow", json=payload
        )

    def user_update(
        self,
        project_id: int,
        role: Literal["project_admin", "project_analyst"],
        user_id: int | None = None,
        invite_id: int | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a project user's or pending invite's role.

        Exactly one of *user_id* or *invite_id* must be given to identify the
        target of the role change.

        Args:
            project_id: ID of the project (must be a positive integer).
            role: New role — "project_admin" or "project_analyst".
            user_id: ID of the existing project user to update.
            invite_id: ID of the pending invite to update.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with the update result.

        Raises:
            MammothValidationError: If project_id is not a positive integer, or
                if *user_id* and *invite_id* are not given exactly one at a time.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        if (user_id is None) == (invite_id is None):
            raise MammothValidationError(ERR_USER_OR_INVITE_ID_REQUIRED.format(user_id, invite_id))
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        if invite_id is not None:
            params["invite_id"] = invite_id
        payload = {"patch": [{"op": "replace", "path": "permissions", "value": role}]}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{project_id}/users",
            params=params,
            json=payload,
        )
