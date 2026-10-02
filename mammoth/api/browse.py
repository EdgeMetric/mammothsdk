"""Browse API client for resource discovery in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


def _page(fields: str | None, limit: int | None, offset: int | None) -> dict[str, Any] | None:
    """The query a browse route takes to narrow and page what it returns.

    A caller that asks for nothing sends nothing, so the route keeps its own
    defaults.
    """
    params: dict[str, Any] = {}
    if fields is not None:
        params["fields"] = fields
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return params or None


def _resource_query(**fields: Any) -> dict[str, Any] | None:
    """The resources-v2 query: only the filters the caller set."""
    return {key: value for key, value in fields.items() if value is not None} or None


class BrowseAPI:
    """Client for browsing and discovering resources.

    Access via client.browse::

        resources = await client.browse.workspaces()
        resources = await client.browse.projects()
        resources = await client.browse.datasets(project_id=10)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    async def root(
        self,
        fields: str | None = None,
        name: str | None = None,
        browse_type: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        sort: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        ids: str | None = None,
        include_hidden: bool | None = None,
        level: int | None = None,
        permissions: str | None = None,
    ) -> dict[str, Any]:
        """Browse resources across all workspaces the caller has access to.

        This is the top-level, non-workspace-scoped browse endpoint (``/browse``).

        Args:
            fields: Comma-separated list of fields to include in the response.
            name: Filter by resource name.
            browse_type: Filter by resource type (e.g. "workspace", "project").
            created_at: Filter by creation date.
            updated_at: Filter by last-updated date.
            sort: Sort order for results.
            offset: Number of results to skip.
            limit: Maximum number of results.
            ids: Comma-separated list of resource IDs to filter by.
            include_hidden: Whether to include hidden resources.
            level: Depth of children to include.
            permissions: Filter by permission level.

        Returns:
            Dict with browse resources.
        """
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if name is not None:
            params["name"] = name
        if browse_type is not None:
            params["browse_type"] = browse_type
        if created_at is not None:
            params["created_at"] = created_at
        if updated_at is not None:
            params["updated_at"] = updated_at
        if sort is not None:
            params["sort"] = sort
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if ids is not None:
            params["ids"] = ids
        if include_hidden is not None:
            params["include_hidden"] = include_hidden
        if level is not None:
            params["level"] = level
        if permissions is not None:
            params["permissions"] = permissions
        return await self._client._request_json("GET", "/browse", params=params or None)

    async def workspaces(
        self,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Browse available workspaces.

        Args:
            fields: Field set to return, e.g. ``"__min"``; server default if
                omitted.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Dict with workspace resources.
        """
        return await self._client._request_json(
            "GET", "/workspaces", params=_page(fields, limit, offset)
        )

    async def projects(
        self,
        workspace_id: int | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Browse projects in a workspace.

        Args:
            workspace_id: Workspace ID (uses client default if not provided).
            fields: Field set to return, e.g. ``"__min"``; server default if
                omitted.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Dict with project resources.
        """
        ws = workspace_id or self._ws()
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects", params=_page(fields, limit, offset)
        )

    async def datasets(
        self,
        project_id: int | None = None,
        workspace_id: int | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Browse datasets in a project.

        Args:
            project_id: Project ID (uses client default if not provided).
            workspace_id: Workspace ID (uses client default if not provided).
            fields: Field set to return, e.g. ``"__min"``; server default if
                omitted.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Dict with dataset resources.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets",
            params=_page(fields, limit, offset),
        )

    async def dataviews(
        self,
        dataset_id: int,
        project_id: int | None = None,
        workspace_id: int | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Browse dataviews in a dataset.

        Args:
            dataset_id: ID of the dataset.
            project_id: Project ID (uses client default if not provided).
            workspace_id: Workspace ID (uses client default if not provided).
            fields: Field set to return, e.g. ``"__min"``; server default if
                omitted.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Dict with dataview resources.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params=_page(fields, limit, offset),
        )

    async def workspace_resources(
        self,
        workspace_id: int | None = None,
        level: int = 2,
        fields: str = "__min",
        limit: int = 100,
    ) -> dict[str, Any]:
        """Browse all resources in a workspace (projects, datasets, folders).

        Args:
            workspace_id: Workspace ID (uses client default if not provided).
            level: Depth of children to include (1 or 2, default 2).
            fields: Fields to return (default "__min").
            limit: Max resources to return (default 100).

        Returns:
            Dict with hierarchical resource list.
        """
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {"level": level, "fields": fields, "limit": limit}
        return await self._client._request_json("GET", f"/workspaces/{ws}/browse", params=params)

    async def folder_resources(
        self,
        folder_id: int,
        project_id: int | None = None,
        workspace_id: int | None = None,
        level: int = 2,
        fields: str = "__min",
    ) -> dict[str, Any]:
        """Browse resources inside a folder.

        Args:
            folder_id: ID of the folder (label).
            project_id: Project ID (uses client default if not provided).
            workspace_id: Workspace ID (uses client default if not provided).
            level: Depth of children to include (1 or 2, default 2).
            fields: Fields to return (default "__min").

        Returns:
            Dict with folder's child resources.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {"level": level, "fields": fields}
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/folders/{folder_id}/browse",
            params=params,
        )

    async def resources_list(
        self,
        project_id: int | None = None,
        parent_type: str | None = None,
        parent_id: int | None = None,
        resource_type: str | None = None,
        search: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        sort: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """List one project's resources, a cursor page at a time (resources v2).

        Args:
            project_id: Project ID (uses the client default if not provided).
            parent_type: Type of the folder-like parent to list inside.
            parent_id: ID of that parent; omit for the project root.
            resource_type: Keep only this resource type.
            search: Keep only resources whose name matches.
            cursor: ``next_cursor`` of the previous page.
            limit: Page size; the route defaults to 50.
            sort: Sort specification.
            fields: Field set to return; the route defaults to ``standard``.

        Returns:
            Dict with ``resources``, ``next_cursor`` and ``has_more``.
        """
        params = _resource_query(
            parent_type=parent_type,
            parent_id=parent_id,
            type=resource_type,
            search=search,
            cursor=cursor,
            limit=limit,
            sort=sort,
            fields=fields,
        )
        return await self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/projects/{self._proj(project_id)}/resources",
            params=params,
        )

    async def resource_get(
        self, resource_type: str, object_id: int, project_id: int | None = None
    ) -> dict[str, Any]:
        """Get one resource with its full properties (resources v2).

        Args:
            resource_type: Resource type, e.g. ``dataset`` or ``dataview``.
            object_id: ID of the resource within that type.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            Dict ``{"resource": {...}}``.
        """
        return await self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/projects/{self._proj(project_id)}"
            f"/resources/{resource_type}/{object_id}",
        )

    async def resource_ancestors(
        self, resource_id: int, project_id: int | None = None
    ) -> dict[str, Any]:
        """Get the folder path of a folder: the chain from the project root down to it.

        The breadcrumb for a deep link that knows only the folder's id.

        Args:
            resource_id: The folder's ``resource_id`` as resources v2 returns it
                (not its object id). A value of 0 or less means the project root.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            Dict ``{"resources": [...]}``, root first and ending with the folder
            itself; empty for the project root. The route answers 404 when the
            id is not a live folder in the project.
        """
        return await self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/projects/{self._proj(project_id)}/resources/ancestors",
            params={"resource_id": resource_id},
        )

    async def resources_search(
        self,
        search: str | None = None,
        resource_type: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        sort: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Search resources across every project the user can open in the workspace.

        Args:
            search: Keep only resources whose name matches.
            resource_type: Keep only these types (comma-separated).
            cursor: ``next_cursor`` of the previous page.
            limit: Page size; the route defaults to 50.
            sort: Sort specification.
            fields: Field set to return; the route defaults to ``standard``.

        Returns:
            Dict with ``resources``, ``next_cursor`` and ``has_more``.
        """
        params = _resource_query(
            search=search,
            type=resource_type,
            cursor=cursor,
            limit=limit,
            sort=sort,
            fields=fields,
        )
        return await self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/resources", params=params
        )
