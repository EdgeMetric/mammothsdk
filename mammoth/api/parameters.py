"""Parameters API client for managing workspace/project parameters in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_PARAMETER_ID_POSITIVE = "`parameter_id` must be a positive integer, got {0}."
ERR_GROUP_ID_POSITIVE = "`group_id` must be a positive integer, got {0}."
ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."


class ParametersAPI:
    """Client for managing workspace and project parameters.

    Access via ``client.parameters``::

        parameters = client.parameters.list()
        parameter = client.parameters.create(
            name="start_date", param_type="DATE", value="2026-01-01", project_id=1,
        )
        client.parameters.rerun(parameter["id"])
        client.parameters.delete(parameter["id"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    @staticmethod
    def _check_parameter_id(parameter_id: int) -> None:
        if parameter_id <= 0:
            raise MammothValidationError(ERR_PARAMETER_ID_POSITIVE.format(parameter_id))

    @staticmethod
    def _check_group_id(group_id: int) -> None:
        if group_id <= 0:
            raise MammothValidationError(ERR_GROUP_ID_POSITIVE.format(group_id))

    @staticmethod
    def _check_project_id(project_id: int | None) -> None:
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))

    def list(
        self,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        group_id: int | None = None,
        sort: str | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """List parameters in the workspace.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.
            search: Free-text search over parameter names.
            group_id: Filter by parameter group ID.
            sort: Sort specification.
            project_id: Filter to a project's parameters (omit for
                workspace-scoped parameters only).

        Returns:
            Dict with the parameters list and pagination info.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if search is not None:
            params["search"] = search
        if group_id is not None:
            params["group_id"] = group_id
        if sort is not None:
            params["sort"] = sort
        if project_id is not None:
            params["project_id"] = project_id
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/parameters", params=params or None
        )

    def create(
        self,
        name: str,
        param_type: str,
        value: str | float | int,
        description: str | None = None,
        group_id: int | None = None,
        scope: str = "project",
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new parameter at workspace or project scope.

        Args:
            name: Parameter name (max 100 chars).
            param_type: Parameter type: ``"NUMERIC"``, ``"TEXT"``, or ``"DATE"``.
            value: Parameter value (a number for ``NUMERIC``, a string for
                ``TEXT``/``DATE``).
            description: Optional description (max 500 chars).
            group_id: Optional parameter group ID to organize the parameter.
            scope: ``"project"`` or ``"workspace"`` (default ``"project"``).
            project_id: Required when *scope* is ``"project"``.

        Returns:
            Dict with created parameter info.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        body: dict[str, Any] = {
            "name": name,
            "param_type": param_type,
            "value": value,
            "scope": scope,
        }
        if description is not None:
            body["description"] = description
        if group_id is not None:
            body["group_id"] = group_id
        if project_id is not None:
            body["project_id"] = project_id
        return self._client._request_json("POST", f"/workspaces/{self._ws()}/parameters", json=body)

    def get(self, parameter_id: int) -> dict[str, Any]:
        """Get parameter details.

        Args:
            parameter_id: ID of the parameter (must be > 0).

        Returns:
            Dict with parameter details.

        Raises:
            MammothValidationError: If *parameter_id* <= 0.
        """
        self._check_parameter_id(parameter_id)
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/parameters/{parameter_id}"
        )

    def update(
        self,
        parameter_id: int,
        name: str | None = None,
        value: str | float | int | None = None,
        param_type: str | None = None,
        description: str | None = None,
        group_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a parameter.

        Args:
            parameter_id: ID of the parameter (must be > 0).
            name: New parameter name (max 100 chars).
            value: New parameter value.
            param_type: New parameter type.
            description: New description (max 500 chars).
            group_id: New parameter group ID.

        Returns:
            Dict with updated parameter info.

        Raises:
            MammothValidationError: If *parameter_id* <= 0.
        """
        self._check_parameter_id(parameter_id)
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if value is not None:
            body["value"] = value
        if param_type is not None:
            body["param_type"] = param_type
        if description is not None:
            body["description"] = description
        if group_id is not None:
            body["group_id"] = group_id
        return self._client._request_json(
            "PATCH", f"/workspaces/{self._ws()}/parameters/{parameter_id}", json=body
        )

    def delete(self, parameter_id: int) -> dict[str, Any]:
        """Delete a parameter.

        Args:
            parameter_id: ID of the parameter (must be > 0).

        Returns:
            Dict with deletion result.

        Raises:
            MammothValidationError: If *parameter_id* <= 0.
        """
        self._check_parameter_id(parameter_id)
        return self._client._request_json(
            "DELETE", f"/workspaces/{self._ws()}/parameters/{parameter_id}"
        )

    def dependencies(self, parameter_id: int) -> dict[str, Any]:
        """Get objects that depend on a parameter.

        Args:
            parameter_id: ID of the parameter (must be > 0).

        Returns:
            Dict with dependency info.

        Raises:
            MammothValidationError: If *parameter_id* <= 0.
        """
        self._check_parameter_id(parameter_id)
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/parameters/{parameter_id}/dependencies"
        )

    def duplicate(self, parameter_id: int) -> dict[str, Any]:
        """Duplicate a parameter.

        Args:
            parameter_id: ID of the parameter (must be > 0).

        Returns:
            Dict with the duplicated parameter info.

        Raises:
            MammothValidationError: If *parameter_id* <= 0.
        """
        self._check_parameter_id(parameter_id)
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/parameters/{parameter_id}/duplicate"
        )

    def rerun(self, parameter_id: int) -> dict[str, Any]:
        """Rerun a single parameter's computation.

        Args:
            parameter_id: ID of the parameter (must be > 0).

        Returns:
            Dict with rerun result.

        Raises:
            MammothValidationError: If *parameter_id* <= 0.
        """
        self._check_parameter_id(parameter_id)
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/parameters/{parameter_id}/rerun"
        )

    def rerun_all_stale(self, project_id: int) -> dict[str, Any]:
        """Rerun all stale parameters in a project.

        Args:
            project_id: ID of the project (must be > 0).

        Returns:
            Dict with rerun result.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/parameters/rerun-all-stale",
            params={"project_id": project_id},
        )

    def group_list(
        self,
        project_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List parameter groups in the workspace.

        Args:
            project_id: Filter to a project's groups (omit for
                workspace-scoped groups only).
            limit: Maximum number of results.
            offset: Number of results to skip.
            sort: Sort specification.

        Returns:
            Dict with the parameter groups list and pagination info.
        """
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort is not None:
            params["sort"] = sort
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/parameters/groups", params=params or None
        )

    def group_create(
        self,
        name: str,
        color: str = "#3B82F6",
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a parameter group.

        Args:
            name: Group name (max 100 chars).
            color: Hex color code (max 7 chars, default ``"#3B82F6"``).
            project_id: Project ID to scope the group to (query parameter).

        Returns:
            Dict with created group info.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        body = {"name": name, "color": color}
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/parameters/groups",
            params=params or None,
            json=body,
        )

    def group_update(
        self,
        group_id: int,
        name: str | None = None,
        color: str | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a parameter group.

        Args:
            group_id: ID of the group (must be > 0).
            name: New group name (max 100 chars).
            color: New hex color code (max 7 chars).
            project_id: Project ID to scope the update to (query parameter).

        Returns:
            Dict with updated group info.

        Raises:
            MammothValidationError: If *group_id* <= 0 or *project_id* <= 0.
        """
        self._check_group_id(group_id)
        self._check_project_id(project_id)
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if color is not None:
            body["color"] = color
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/parameters/groups/{group_id}",
            params=params or None,
            json=body,
        )

    def group_delete(self, group_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Delete a parameter group.

        Args:
            group_id: ID of the group (must be > 0).
            project_id: Project ID to scope the deletion to (query parameter).

        Returns:
            Dict with deletion result.

        Raises:
            MammothValidationError: If *group_id* <= 0 or *project_id* <= 0.
        """
        self._check_group_id(group_id)
        self._check_project_id(project_id)
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/parameters/groups/{group_id}",
            params=params or None,
        )

    def group_reorder(
        self,
        order: _list[int],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Reorder parameter groups.

        Args:
            order: List of group IDs in the desired sort order.
            project_id: Project ID to scope the reorder to (query parameter).

        Returns:
            Dict with reorder result.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        body = {"order": order}
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/parameters/groups/reorder",
            params=params or None,
            json=body,
        )
