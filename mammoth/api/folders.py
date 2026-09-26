"""
Folders API client for managing folders in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

from ..exceptions import MammothValidationError
from ..models.folders import CreateFolder, FolderSchema, FoldersList
from ..models.jobs import JobResponse, ObjectJobSchema

_list = list  # Alias to avoid shadowing by method name

ERR_FOLDER_ID_POSITIVE = "`folder_id` must be a positive integer, got {0}."


class FoldersAPI:
    """Client for interacting with Mammoth Folders API.

    Access via client.folders:
        folders = client.folders.list()
        folder = client.folders.create(name="Reports")
        client.folders.delete([folder_id])
        client.folders.move(resource_ids=[...], target_folder_resource_id="...")
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

    def get_project_root(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> FolderSchema:
        """Get a FolderSchema representing the project root folder.

        In Mammoth, the project root is not a physical folder entity — it is the
        implicit top-level container.  The returned object has
        ``resource_id=None``.  When passed to ``files.upload(folder_resource_id=...)``,
        a ``None`` resource_id causes files to be placed at the project root (the
        same as omitting the parameter entirely).

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            FolderSchema with ``name="Project Root"`` and ``resource_id=None``.
        """
        # Validate that project_id is set (raises ValueError if not)
        self._proj(project_id)
        return FolderSchema(
            id=0,
            name="Project Root",
            status=None,
            created_at=None,
            updated_at=None,
            resource_id=None,
            created_by=None,
            parent_id=None,
            resource_path=None,
        )

    def list(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
        fields: str | None = None,
        folder_ids: _list[int] | None = None,
        names: _list[str] | None = None,
        statuses: _list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        created_by: _list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> FoldersList:
        """List folders in a project with optional filtering and pagination.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            fields: Fields to return (e.g., "__standard", "__full", "__min").
            folder_ids: List of specific folder IDs to retrieve.
            names: List of folder names to filter by.
            statuses: List of statuses to filter by.
            created_at: Date range filter for creation date.
            updated_at: Date range filter for update date.
            created_by: List of user names who created folders.
            limit: Maximum number of results (0-100, default 50).
            offset: Number of results to skip (default 0).
            sort: Sort specification (e.g., "(id:asc),(name:desc)").

        Returns:
            FoldersList with folders and pagination info.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        if folder_ids:
            params["id"] = ",".join(str(fid) for fid in folder_ids)
        if names:
            params["name"] = ",".join(names)
        if statuses:
            params["status"] = ",".join(statuses)
        if created_at:
            params["created_at"] = created_at
        if updated_at:
            params["updated_at"] = updated_at
        if created_by:
            params["created_by"] = ",".join(created_by)
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if sort:
            params["sort"] = sort

        response = self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/folders", params=params
        )
        return FoldersList(**response)

    def create(
        self,
        name: str,
        parent_resource_id: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> FolderSchema:
        """Create a new folder.

        Args:
            name: Name for the new folder.
            parent_resource_id: Parent folder resource ID (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            FolderSchema with created folder info (id, name, resource_id, etc.).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        folder_data = CreateFolder(name=name, parent_resource_id=parent_resource_id)
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/folders",
            json=folder_data.model_dump(exclude_none=True),
        )
        return FolderSchema(**response.get("folder", response))

    def delete(
        self,
        folder_ids: _list[int],
        workspace_id: int | None = None,
        project_id: int | None = None,
        check_dependency: bool = True,
        remove_contents: bool = True,
    ) -> None:
        """Delete multiple folders.

        Args:
            folder_ids: List of folder IDs to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            check_dependency: Check for dependency before deleting.
            remove_contents: Remove folder contents before deleting.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params = {
            "ids": ",".join(str(fid) for fid in folder_ids),
            "check_dependency": check_dependency,
            "remove_contents": remove_contents,
        }
        self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/folders", params=params
        )

    def _resolve_resource_ids(
        self,
        ws: int,
        proj: int,
        dataset_ids: _list[int],
        view_ids: _list[int],
    ) -> _list[int]:
        """Resolve dataset/view object ids to the resource ids the folder-move
        endpoint requires.

        A dataset's or view's own id (the ``id`` field ``dataset get``/``view
        get`` return) is a different number from its ``resource_id`` — the
        value the server's move endpoint actually matches against. This calls
        the bulk resource-lookup endpoint to translate object ids to resource
        ids in one round trip, and fails loudly (rather than moving the wrong
        thing or hitting a misleading permission error) when an id can't be
        resolved.
        """
        requested = [("datasource", i) for i in dataset_ids] + [("dataview", i) for i in view_ids]
        if not requested:
            return []
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/resources/bulk",
            json={"ids": [{"type": type_, "id": oid} for type_, oid in requested]},
            operation_effect="read",
        )
        found: dict[tuple[str, int], int] = {}
        for item in response.get("resources", []):
            resource_id = item.get("resource_id")
            object_id = item.get("object_id")
            if resource_id is not None and object_id is not None:
                found[(item.get("resource_type"), object_id)] = int(resource_id)
        resolved: list[int] = []
        missing: list[str] = []
        for type_, oid in requested:
            resource_id = found.get((type_, oid))
            if resource_id is None:
                kind = "dataset" if type_ == "datasource" else "view"
                missing.append(f"{kind} {oid}")
            else:
                resolved.append(resource_id)
        if missing:
            raise MammothValidationError(
                "Could not resolve a resource id for: "
                + ", ".join(missing)
                + ". Check that the id(s) exist in this project and that you have"
                " access to them."
            )
        return resolved

    def move(
        self,
        resource_ids: _list[str] | None = None,
        target_folder_resource_id: str | None = None,
        source_folder_resource_id: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
        *,
        dataset_ids: _list[int] | None = None,
        view_ids: _list[int] | None = None,
    ) -> ObjectJobSchema:
        """Move resources between folders.

        Args:
            resource_ids: Raw resource ids to move. This is NOT a dataset's or
                view's own id — it is the ``resource_id`` field returned by
                the resources lookup the SDK uses internally for
                ``dataset_ids``/``view_ids`` below. Prefer those two params
                unless you already have a resource id from elsewhere.
            target_folder_resource_id: The target folder's id — the ``id``
                field ``folder list``/``folder get``/``folder create``
                return (despite this parameter's name, NOT the folder's
                ``resource_id`` field). ``None``/``""``/``"root"`` moves to
                the project root.
            source_folder_resource_id: Same id kind as
                ``target_folder_resource_id``. Accepted for compatibility;
                the route infers the source itself.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            dataset_ids: Dataset ids, as returned by ``dataset get``/``dataset
                list`` (their ``id`` field). Resolved to resource ids
                automatically — use this instead of ``resource_ids`` when all
                you have is the dataset's own id.
            view_ids: View ids, as returned by ``view get``/``view list``
                (their ``id`` field). Resolved to resource ids automatically —
                use this instead of ``resource_ids`` when all you have is the
                view's own id.

        Returns:
            ObjectJobSchema with job information for the move.

        Raises:
            MammothValidationError: If no ids are given in any of
                ``resource_ids``/``dataset_ids``/``view_ids``, or if a
                dataset/view id in ``dataset_ids``/``view_ids`` can't be
                resolved to a resource id.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        # ``BulkFolderPatchRequest``: ``patch`` of ``{op: "move", from: [resource
        # ids], path: destination folder id | "root"}``. ``source_folder_resource_id``
        # is accepted for compatibility; the route infers the source.
        moved: list[int] = []
        if resource_ids:
            try:
                moved.extend(int(item) for item in resource_ids)
            except (TypeError, ValueError) as exc:
                raise MammothValidationError(
                    f"resource_ids must be integer resource ids, got {resource_ids!r}"
                ) from exc
        moved.extend(
            self._resolve_resource_ids(ws, proj, list(dataset_ids or []), list(view_ids or []))
        )
        if not moved:
            raise MammothValidationError(
                "Provide at least one id via resource_ids, dataset_ids, or view_ids."
            )
        destination: int | str = "root"
        if target_folder_resource_id not in (None, "", "root"):
            destination = (
                int(target_folder_resource_id)
                if str(target_folder_resource_id).isdigit()
                else str(target_folder_resource_id)
            )
        response = self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/folders",
            json={"patch": [{"op": "move", "from": moved, "path": destination}]},
        )
        return ObjectJobSchema(**response)

    def bulk_delete(
        self,
        folder_ids: _list[int] | None = None,
        check_dependency: bool | None = None,
        remove_contents: bool | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> None:
        """Bulk delete folders, matching the ``DeleteFolders`` operation directly.

        Unlike :meth:`delete`, every query parameter here is optional — omitting
        ``folder_ids`` lets the server apply its own default deletion scope.

        Args:
            folder_ids: Folder IDs to delete (optional).
            check_dependency: Whether to check for dependencies before deleting.
            remove_contents: Whether to remove folder contents before deleting.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            None.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if folder_ids is not None:
            params["ids"] = ",".join(str(fid) for fid in folder_ids)
        if check_dependency is not None:
            params["check_dependency"] = check_dependency
        if remove_contents is not None:
            params["remove_contents"] = remove_contents
        self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/folders", params=params or None
        )

    def get(
        self,
        folder_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        fields: str | None = None,
    ) -> FolderSchema:
        """Get a single folder by ID.

        Args:
            folder_id: ID of the folder (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            fields: Fields to return (e.g., "__standard", "__full", "__min").

        Returns:
            FolderSchema with the folder's details.

        Raises:
            MammothValidationError: If folder_id is not a positive integer.
        """
        if folder_id <= 0:
            raise MammothValidationError(ERR_FOLDER_ID_POSITIVE.format(folder_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        response = self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/folders/{folder_id}",
            params=params or None,
        )
        return FolderSchema(**response.get("folder", response))

    def trash(
        self,
        folder_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> JobResponse:
        """Trash a folder's contents and hard-delete the now-empty folder.

        Args:
            folder_id: ID of the folder to trash (must be a positive integer).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            JobResponse with job information for the trash operation.

        Raises:
            MammothValidationError: If folder_id is not a positive integer.
        """
        if folder_id <= 0:
            raise MammothValidationError(ERR_FOLDER_ID_POSITIVE.format(folder_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        response = self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/folders/{folder_id}/trash"
        )
        return JobResponse(**response)

    def update(
        self,
        folder_id: int,
        name: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> FolderSchema:
        """Update folder details (currently supports renaming only).

        Args:
            folder_id: ID of the folder to update (must be a positive integer).
            name: New name for the folder.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            FolderSchema with the updated folder details.

        Raises:
            MammothValidationError: If folder_id is not a positive integer.
        """
        if folder_id <= 0:
            raise MammothValidationError(ERR_FOLDER_ID_POSITIVE.format(folder_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        payload = {"patch": [{"op": "replace", "path": "name", "value": name}]}
        response = self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{proj}/folders/{folder_id}", json=payload
        )
        return FolderSchema(**response.get("folder", response))
