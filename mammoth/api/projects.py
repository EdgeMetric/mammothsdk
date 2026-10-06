"""
Projects API client for managing projects in Mammoth.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Literal

from pydantic import ValidationError

from ..exceptions import MammothDeletionVerificationError, MammothValidationError
from ..models.projects import DataSyncPatchItem

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

#: Largest ``limit`` the projects route accepts (``4GENR007`` above it).
MAX_PAGE_SIZE = 100

#: Views fetched per page when mapping views to their datasets.
MAX_VIEW_PAGE_SIZE = 1000

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_COPY_NAME = "`name` must be 1 to 63 characters."
ERR_COPY_DATASETS = "`dataset_ids` must hold at least one dataset id, or be omitted to copy all."
_PROJECT_NAME_MAX = 63
ERR_USER_OR_INVITE_ID_REQUIRED = (
    "Exactly one of `user_id` or `invite_id` must be provided, got user_id={0!r}, "
    "invite_id={1!r}."
)


def _agent_memory_items(project: dict[str, Any]) -> _list[str]:
    """Return the caller's ``properties.agent_memory`` list (empty when absent)."""
    return _list((project.get("properties") or {}).get("agent_memory") or [])


def _attention_row(kind: str, view_id: int | None, **detail: Any) -> dict[str, Any]:
    return {"kind": kind, "view_id": view_id, "view_name": None, **detail}


def _attention_pipeline_rows(pending: dict[str, Any]) -> _list[dict[str, Any]]:
    """Error and draft rows from ``pending_changes`` (the web app keeps numeric keys only)."""
    rows: _list[dict[str, Any]] = []
    for key, change in (pending.get("pending_changes") or {}).items():
        if not str(key).isdigit():
            continue
        kind = "pipeline_error" if change.get("is_pipeline_in_error") else "pending_pipeline"
        rows.append(
            _attention_row(
                kind,
                change.get("dataview_id"),
                view_name=change.get("dataview_name"),
                dataset_name=change.get("datasource_name"),
                pending_steps_count=change.get("pending_steps_count"),
                tasks_in_error=_list((change.get("tasks_in_error") or {}).values()),
                actions_in_error=_list((change.get("actions_in_error") or {}).values()),
            )
        )
    return rows


def _attention_action_rows(pending: dict[str, Any]) -> _list[dict[str, Any]]:
    """Files and datasets waiting for a person (``ds_action_needed_items``).

    ``action`` is the web app's row title: ``unstructured_rows``, ``ambiguous_date_format``,
    ``password_required``, ``sheet_selection_required`` or ``schema_mismatch``. Only a
    dataset row carries its own ``dataset_id``; an upload still being read does not.
    """
    rows: _list[dict[str, Any]] = []
    for item in pending.get("ds_action_needed_items") or []:
        is_dataset = item.get("resource_type") == "datasource"
        row = _attention_row(
            "needs_input",
            None,
            action=(item.get("action_needed") or {}).get("type"),
            name=item.get("name"),
            resource_type=item.get("resource_type"),
            append_to_dataset_id=item.get("append_to_ds_id"),
            needs_review=item.get("needs_review", True),
        )
        row["dataset_id"] = item.get("id") if is_dataset else None
        rows.append(row)
    return rows


def _attention_items(
    pending: dict[str, Any],
    checkpoints: _list[dict[str, Any]],
    data_checks: _list[dict[str, Any]],
) -> _list[dict[str, Any]]:
    rows = _attention_pipeline_rows(pending) + _attention_action_rows(pending)
    for dep in pending.get("pending_data_update_items") or []:
        if dep.get("data_update_pending"):
            rows.append(
                _attention_row(
                    "pending_data",
                    dep.get("source_dataview_id"),
                    operation_id=dep.get("op_id"),
                    operation_type=dep.get("op_type"),
                    operation_name=dep.get("op_name"),
                )
            )
    rows.extend(
        _attention_row(
            "checkpoint", c.get("dataview_id"), checkpoint_id=c.get("id"), name=c.get("name")
        )
        for c in checkpoints
        if c.get("status") == "needs_approval" and c.get("checkpoint_type") == "approval"
    )
    rows.extend(
        _attention_row("data_check", d.get("dataview_id"), data_check_id=d.get("id"))
        for d in data_checks
        if d.get("status") == "failed"
    )
    return rows


def _attention_result(
    project_id: int,
    items: _list[dict[str, Any]],
    view_map: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    datasets: dict[int, dict[str, Any]] = {}
    unresolved: _list[int] = []
    counts: dict[str, int] = {}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
        found = view_map.get(item["view_id"]) if item["view_id"] is not None else None
        item["dataset_id"] = found["dataset_id"] if found else item.get("dataset_id")
        if found:
            item["view_name"] = item["view_name"] or found["view_name"]
            item["dataset_name"] = item.get("dataset_name") or found["dataset_name"]
            entry = datasets.setdefault(
                found["dataset_id"],
                {
                    "dataset_id": found["dataset_id"],
                    "dataset_name": found["dataset_name"],
                    "view_ids": [],
                },
            )
            if item["view_id"] not in entry["view_ids"]:
                entry["view_ids"].append(item["view_id"])
        elif item["view_id"] is not None and item["view_id"] not in unresolved:
            unresolved.append(item["view_id"])
        elif item["kind"] == "needs_input" and item["dataset_id"] is not None:
            datasets.setdefault(
                item["dataset_id"],
                {"dataset_id": item["dataset_id"], "dataset_name": item["name"], "view_ids": []},
            )
    return {
        "project_id": project_id,
        "items": items,
        "datasets": _list(datasets.values()),
        "counts": counts,
        "unresolved_view_ids": unresolved,
    }


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

    async def list(
        self,
        workspace_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        fields: str = "id,name",
        include_non_members: bool = False,
    ) -> dict[str, Any]:
        """List one page of projects in a workspace.

        By default only projects the caller is a member of are returned, which
        is what the Mammoth UI shows. A workspace owner or admin can read
        every project, but cannot open the ones they are not a member of.

        The backend caps ``limit`` at :data:`MAX_PAGE_SIZE` (100) and rejects
        larger values with a validation error; use :meth:`list_all` to walk
        every page.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            limit: Maximum number of results (default and maximum 100).
            offset: Number of leading projects to skip (server-side).
            fields: Comma-separated project fields to return (default ``id,name``).
            include_non_members: Also return projects the caller is not a member
                of; every row then carries ``member`` (true/false).

        Returns:
            Dict containing projects list with the requested fields, plus ``limit``,
            ``offset`` and ``next`` (empty when this is the last page).
        """
        ws = workspace_id or self._ws()
        page = await self._list_page(ws, limit, offset, fields, subscribed=not include_non_members)
        if include_non_members:
            await self._tag_members(ws, page.get("projects", []))
        return page

    async def _list_page(
        self, ws: int, limit: int, offset: int, fields: str, subscribed: bool
    ) -> dict[str, Any]:
        """Fetch one page; ``subscribed`` selects member projects only, else all."""
        params: dict[str, Any] = {"fields": fields, "limit": limit}
        if subscribed:
            params["subscribed"] = "true"
        if offset:
            params["offset"] = offset
        return await self._client._request_json("GET", f"/workspaces/{ws}/projects", params=params)

    async def _tag_members(self, ws: int, rows: _list[dict[str, Any]]) -> None:
        """Set ``member`` on each row from the caller's member-project ids."""
        member_ids = {p.get("id") for p in await self._fetch_all(ws, "id", subscribed=True)}
        for row in rows:
            row["member"] = row.get("id") in member_ids

    async def _fetch_all(self, ws: int, fields: str, subscribed: bool) -> _list[dict[str, Any]]:
        """Walk the 100-row pages of the projects route (untagged rows)."""
        projects: _list[dict[str, Any]] = []
        seen: set[Any] = set()
        offset = 0
        while True:
            page = await self._list_page(ws, MAX_PAGE_SIZE, offset, fields, subscribed)
            batch = page.get("projects", []) if isinstance(page, dict) else []
            fresh = [p for p in batch if p.get("id") not in seen]
            seen.update(p.get("id") for p in fresh)
            projects.extend(fresh)
            # A short page is the last one; a page with nothing new means the
            # server ignored the offset, so stop rather than loop.
            if len(batch) < MAX_PAGE_SIZE or not fresh:
                return projects
            offset += len(batch)

    async def list_all(
        self,
        workspace_id: int | None = None,
        fields: str = "id,name",
        include_non_members: bool = False,
    ) -> _list[dict[str, Any]]:
        """Return every project the caller is a member of, following the 100-row pages.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            fields: Comma-separated project fields to return (default ``id,name``).
            include_non_members: Also return projects the caller is not a member
                of; every row then carries ``member`` (true/false).

        Returns:
            List of project dicts with the requested fields across all pages.
        """
        ws = workspace_id or self._ws()
        projects = await self._fetch_all(ws, fields, subscribed=not include_non_members)
        if include_non_members:
            await self._tag_members(ws, projects)
        return projects

    async def get(
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
        # An explicit id or name may name a project the caller can read but is
        # not a member of; only the auto-selection is limited to member projects.
        projects = await self._fetch_all(
            workspace_id or self._ws(), "id,name", subscribed=project is None
        )

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

    async def create(
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
        return await self._client._request_json("POST", f"/workspaces/{ws}/projects", json=payload)

    async def copy(
        self,
        project_id: int,
        name: str,
        dataset_ids: _list[int] | None = None,
        include_dashboards: bool = False,
        exclude_data: bool = False,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Copy a project's datasets, views and pipelines into a new project (a write).

        Runs as one background job; wait for it with ``client.wait_if_job``. The job's
        result is ``{project_id, dataset_map, view_map, skipped, dashboards}``.

        Args:
            project_id: ID of the source project (must be > 0).
            name: Name of the new project (1 to 63 characters).
            dataset_ids: Datasets of the source project to copy; ``None`` copies them all.
            include_dashboards: Also copy the dashboards built on the copied datasets.
            exclude_data: Copy every dataset's pipeline without its rows.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with ``job_id``, the copy job to wait for.

        Raises:
            MammothValidationError: If *project_id* is not positive, *name* is not 1 to 63
                characters, or *dataset_ids* is an empty list.
        """
        if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        if not name or len(name) > _PROJECT_NAME_MAX:
            raise MammothValidationError(ERR_COPY_NAME)
        if dataset_ids is not None and not dataset_ids:
            raise MammothValidationError(ERR_COPY_DATASETS)
        ws = workspace_id or self._ws()
        payload: dict[str, Any] = {
            "name": name,
            "dataset_ids": None if dataset_ids is None else _list(dataset_ids),
            "include_dashboards": include_dashboards,
            "exclude_data": exclude_data,
        }
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{project_id}/copy", json=payload
        )

    async def update(
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
        # ``ProjectPatch``: ``patches`` of ``{op, path, value}`` where ``path``
        # is the bare name ``name`` or ``properties`` (colour lives inside
        # ``properties``). A JSON-pointer ``/name`` under ``patch`` is rejected.
        operations: list[dict[str, Any]] = []
        if name is not None:
            operations.append({"op": "replace", "path": "name", "value": name})
        if color is not None:
            operations.append({"op": "replace", "path": "properties", "value": {"color": color}})
        if not operations:
            raise MammothValidationError("Provide at least one of `name` or `color` to update.")
        payload = {"patches": operations}
        return await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{project_id}", json=payload
        )

    async def delete(
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
        return await self._client._request_json("DELETE", f"/workspaces/{ws}/projects/{project_id}")

    async def _wait_until_absent(
        self,
        project_ids: _list[int],
        ack: dict[str, Any],
        workspace_id: int | None,
        timeout: int | None,
        poll_interval: float,
    ) -> None:
        """Poll the project list until none of ``project_ids`` is in it.

        The delete routes answer 202 with no job id, so absence from the list
        is the only readback. Raises on timeout with the ids still present.
        """
        ws = workspace_id or self._ws()
        deadline = time.monotonic() + (
            timeout if timeout is not None else int(getattr(self._client, "job_timeout", 60))
        )
        while True:
            rows = await self._fetch_all(ws, "id", subscribed=False)
            present = sorted(set(project_ids) & {p.get("id") for p in rows})
            if not present:
                return
            if time.monotonic() >= deadline:
                raise MammothDeletionVerificationError(
                    "Project delete was acknowledged but absence was not verified.",
                    {
                        "project_ids": list(project_ids),
                        "still_present": present,
                        "status": "pending",
                        "verified": False,
                        "ack": ack,
                    },
                )
            await asyncio.sleep(poll_interval)

    async def delete_and_verify(
        self,
        project_id: int,
        workspace_id: int | None = None,
        *,
        timeout: int | None = None,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Delete one project and verify it is gone from the project list.

        The route acknowledges with 202 and an empty body, so this polls the
        list until the project is absent (bounded by the client job timeout).

        Raises:
            MammothDeletionVerificationError: still listed when the timeout ends.
        """
        ack = await self.delete(project_id, workspace_id=workspace_id)
        settled = await self._client._wait_if_job(ack)
        await self._wait_until_absent([project_id], settled, workspace_id, timeout, poll_interval)
        return {"project_id": project_id, "status": "deleted", "verified": True, "ack": settled}

    async def bulk_delete_and_verify(
        self,
        project_ids: _list[int],
        workspace_id: int | None = None,
        *,
        timeout: int | None = None,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Bulk delete projects and verify every id is gone from the project list.

        Raises:
            MammothDeletionVerificationError: some ids still listed at timeout.
        """
        ack = await self.bulk_delete(project_ids, workspace_id=workspace_id)
        settled = await self._client._wait_if_job(ack)
        await self._wait_until_absent(project_ids, settled, workspace_id, timeout, poll_interval)
        return {
            "project_ids": list(project_ids),
            "status": "deleted",
            "verified": True,
            "ack": settled,
        }

    async def bulk_update(
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
        return await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects", json=patch_data
        )

    async def bulk_delete(
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
        return await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects", params={"ids": ids_str}
        )

    async def add_users(
        self,
        project_id: int,
        user_ids: _list[int],
        role: str | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Add users to a project.

        The route takes ``{"users": [{"user_id", "role"}]}``; users are
        addressed by numeric id (see ``workspace user list``), not by email.

        Args:
            project_id: ID of the project.
            user_ids: Numeric user ids to add.
            role: ``project_admin`` or ``project_analyst`` (server default
                ``project_analyst``) applied to every listed user.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with result.
        """
        ws = workspace_id or self._ws()
        users: list[dict[str, Any]] = []
        for raw in user_ids:
            if isinstance(raw, bool) or not (
                isinstance(raw, int) or (isinstance(raw, str) and raw.isdigit())
            ):
                raise MammothValidationError(
                    f"user_ids must be numeric user ids, got {raw!r}; "
                    "look ids up with the workspace user list."
                )
            entry: dict[str, Any] = {"user_id": int(raw)}
            if role:
                entry["role"] = role
            users.append(entry)
        if not users:
            raise MammothValidationError("user_ids must contain at least one user id.")
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{project_id}/users", json={"users": users}
        )

    async def remove_users(
        self,
        project_id: int,
        user_ids: _list[str],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Remove users from a project.

        Args:
            project_id: ID of the project.
            user_ids: List of user IDs to remove (one DELETE per user).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with the last removal's result.

        Raises:
            MammothValidationError: If ``user_ids`` is empty.
        """
        if not user_ids:
            raise MammothValidationError("user_ids must contain at least one user id.")
        ws = workspace_id or self._ws()
        result: dict[str, Any] = {}
        for uid in user_ids:
            # The route takes ONE ``user_id`` query parameter per call.
            result = await self._client._request_json(
                "DELETE", f"/workspaces/{ws}/projects/{project_id}/users", params={"user_id": uid}
            )
        return result

    async def browse(
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
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/browse",
            params=params or None,
        )

    async def checkpoint_list(
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
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/checkpoints",
            params=params or None,
        )

    async def data_check_list(
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
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/data-checks",
            params=params or None,
        )

    async def pending_changes(
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
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{project_id}/pending-changes"
        )

    async def needs_attention(
        self,
        project_id: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Return the rows of the Monitor modal's "Needs Attention" tab, with dataset ids.

        Same sources and filters as the web app (mm-frontend
        ``resources.storePinia.js`` ``fetchPipelineChanges`` and
        ``monitor-needs-attention.vue``), for the view-bearing rows:

        - ``pipeline_error``: ``pending_changes`` entries with ``is_pipeline_in_error``.
        - ``pending_pipeline``: the remaining ``pending_changes`` entries (draft steps).
        - ``pending_data``: ``pending_data_update_items`` with ``data_update_pending``
          (one row per dependency; the web app groups JOIN/LOOKUP sources by destination).
        - ``checkpoint``: project checkpoints with status ``needs_approval`` and type ``approval``.
        - ``data_check``: project data checks with status ``failed``.
        - ``needs_input``: ``ds_action_needed_items`` -- files and datasets waiting for a
          person; ``action`` says which (``unstructured_rows``, ``ambiguous_date_format``,
          ``password_required``, ``sheet_selection_required``, ``schema_mismatch``).

        The web app also lists pending retentions, which the v2 route does not return, so
        they are not included. Each row carries ``view_id`` and the owning ``dataset_id``
        (null when the view is not found in the project), so a caller can act on the
        datasets.

        Args:
            project_id: ID of the project (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with ``items``, ``datasets`` (unique, each with its ``view_ids``),
            ``counts`` per kind and ``unresolved_view_ids``.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        pending = await self.pending_changes(project_id, ws)
        checkpoints = await self.checkpoint_list(project_id, ws)
        data_checks = await self.data_check_list(project_id, ws)
        items = _attention_items(
            pending.get("pending_items") or {},
            checkpoints.get("checkpoints") or [],
            data_checks.get("data_checks") or [],
        )
        view_ids = {item["view_id"] for item in items if item["view_id"] is not None}
        view_map = await self._dataset_of_views(project_id, ws, view_ids)
        return _attention_result(project_id, items, view_map)

    async def _dataset_of_views(
        self, project_id: int, ws: int, view_ids: set[int]
    ) -> dict[int, dict[str, Any]]:
        """Map each of ``view_ids`` to ``{dataset_id, dataset_name, view_name}``.

        One resources-bulk request per 100 views: each dataview row names its
        parent dataset, so the cost does not depend on how many datasets the
        project holds. A view the project does not hold stays unmapped.
        """
        found: dict[int, dict[str, Any]] = {}
        rows = await self._client.browse.resources_bulk(
            [("dataview", view_id) for view_id in sorted(view_ids)], project_id=project_id
        )
        for row in rows:
            dataset = row.get("dataset")
            if isinstance(dataset, dict) and dataset.get("id") is not None:
                found[row["object_id"]] = {
                    "dataset_id": dataset["id"],
                    "dataset_name": dataset.get("name"),
                    "view_name": row.get("name"),
                }
        return found

    async def list_agent_memory(
        self,
        project_id: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """List the caller's saved agent preferences for a project.

        Reads the project's ``properties.agent_memory`` (the caller's own list).

        Args:
            project_id: ID of the project (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with ``items``: the saved preferences, oldest first.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
            ValueError: If the project is not visible to the caller.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        projects = await self.list_all(workspace_id=workspace_id, fields="id,properties")
        for project in projects:
            if project.get("id") == project_id:
                return {"items": _agent_memory_items(project)}
        raise ValueError(f"Project ID {project_id} not found.")

    async def add_agent_memory(
        self,
        project_id: int,
        text: str,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Save one agent preference for the caller in a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            text: The preference, in the user's words.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with ``items``: the saved preferences after the add.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        return await self._patch_agent_memory(
            project_id, {"op": "add", "path": "agent_memory", "value": text}, workspace_id
        )

    async def remove_agent_memory(
        self,
        project_id: int,
        index: int,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Remove one of the caller's saved agent preferences in a project.

        Args:
            project_id: ID of the project (must be a positive integer).
            index: Zero-based position of the preference in ``list_agent_memory``.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with ``items``: the saved preferences after the removal.

        Raises:
            MammothValidationError: If project_id is not a positive integer.
        """
        return await self._patch_agent_memory(
            project_id, {"op": "remove", "path": "agent_memory", "value": index}, workspace_id
        )

    async def _patch_agent_memory(
        self, project_id: int, patch: dict[str, Any], workspace_id: int | None
    ) -> dict[str, Any]:
        """PATCH one agent_memory op onto the project and return the caller's list."""
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        ws = workspace_id or self._ws()
        project = await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{project_id}", json={"patches": [patch]}
        )
        return {"items": _agent_memory_items(project)}

    async def publish_credentials(
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
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/credentials",
            params={"odbc_type": odbc_type},
        )

    async def resource_dependencies(
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
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{project_id}/resource-dependencies",
            params=params,
        )

    async def resource_dependencies_update(
        self,
        project_id: int,
        patches: _list[DataSyncPatchItem],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Apply typed data-sync patches to resources in a project.

        The release API accepts one or more ``data_sync`` replacements and
        returns a job handle (HTTP 202). The CLI owns waiting and confirmation;
        this SDK method only validates/serializes the public request and emits
        the exact PATCH wire contract.
        """
        if project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        if workspace_id is not None and workspace_id <= 0:
            raise MammothValidationError("`workspace_id` must be a positive integer.")
        if not patches:
            raise MammothValidationError("`patches` must contain at least one operation.")
        try:
            typed = [
                (
                    item
                    if isinstance(item, DataSyncPatchItem)
                    else DataSyncPatchItem.model_validate(item)
                )
                for item in patches
            ]
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid data-sync patch: {exc}") from exc
        targets = [(item.value.context_type, item.value.context_id) for item in typed]
        if len(set(targets)) != len(targets):
            raise MammothValidationError("`patches` must not repeat a resource target.")
        ws = workspace_id if workspace_id is not None else self._ws()
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{project_id}/resource-dependencies",
            json={"patches": [item.model_dump(mode="json", exclude_unset=True) for item in typed]},
        )

    async def resource_status(
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
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{project_id}/resource-status"
        )

    async def sample_flow(
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
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{project_id}/sample-flow", json=payload
        )

    async def user_update(
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
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{project_id}/users",
            params=params,
            json=payload,
        )
