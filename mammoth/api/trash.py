"""Trash API client for bulk trash/restore operations in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias: TrashAPI.list shadows the builtin in later annotations.

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_ITEMS_EMPTY = "`items` must be a non-empty list."
ERR_ITEM_MISSING_KEYS = '`items` entries must have "id" and "type" keys, got {0!r}.'
ERR_ITEM_ID_POSITIVE = "`items` entry `id` must be a positive integer, got {0}."
ERR_ITEM_TYPE_INVALID = "`items` entry `type` must be one of {valid}, got {value!r}."

VALID_TRASH_ITEM_TYPES = frozenset({"dataview", "dataset", "dashboard", "automation"})


def _validate_items(items: list[dict[str, Any]]) -> None:
    """Validate the shape of a bulk trash/restore `items` list."""
    if not items:
        raise MammothValidationError(ERR_ITEMS_EMPTY)
    for item in items:
        if "id" not in item or "type" not in item:
            raise MammothValidationError(ERR_ITEM_MISSING_KEYS.format(item))
        if item["id"] <= 0:
            raise MammothValidationError(ERR_ITEM_ID_POSITIVE.format(item["id"]))
        if item["type"] not in VALID_TRASH_ITEM_TYPES:
            raise MammothValidationError(
                ERR_ITEM_TYPE_INVALID.format(
                    valid=sorted(VALID_TRASH_ITEM_TYPES), value=item["type"]
                )
            )


class TrashAPI:
    """Client for managing trashed resources in a project.

    Access via ``client.trash``::

        trashed = client.trash.list()
        client.trash.add(items=[{"id": 42, "type": "dataview"}])
        client.trash.restore(items=[{"id": 42, "type": "dataview"}])
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

    def list(
        self,
        project_id: int | None = None,
        type: str | None = None,
        sort: str | None = None,
        order: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        q: str | None = None,
        trashed_by: int | None = None,
        trashed_after: str | None = None,
        trashed_before: str | None = None,
        expiring_within_days: int | None = None,
        folder_path: str | None = None,
        folder_root: str | None = None,
    ) -> dict[str, Any]:
        """List trashed resources in a project.

        Args:
            project_id: Project ID (uses client default if not provided).
            type: Filter by resource type (``"dataview"``, ``"dataset"``,
                ``"dashboard"``, or ``"automation"``).
            sort: Sort specification.
            order: Sort order (e.g. ``"asc"`` or ``"desc"``).
            limit: Maximum number of results.
            offset: Number of results to skip.
            q: Free-text search query.
            trashed_by: Filter by the user ID who trashed the item.
            trashed_after: Only items trashed after this timestamp.
            trashed_before: Only items trashed before this timestamp.
            expiring_within_days: Only items expiring within this many days.
            folder_path: Filter by originating folder path.
            folder_root: Filter by originating folder root.

        Returns:
            Dict with the trashed items list and pagination info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if type is not None:
            params["type"] = type
        if sort is not None:
            params["sort"] = sort
        if order is not None:
            params["order"] = order
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if q is not None:
            params["q"] = q
        if trashed_by is not None:
            params["trashed_by"] = trashed_by
        if trashed_after is not None:
            params["trashed_after"] = trashed_after
        if trashed_before is not None:
            params["trashed_before"] = trashed_before
        if expiring_within_days is not None:
            params["expiring_within_days"] = expiring_within_days
        if folder_path is not None:
            params["folder_path"] = folder_path
        if folder_root is not None:
            params["folder_root"] = folder_root
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/trash",
            params=params or None,
        )

    def add(self, items: _list[dict[str, Any]], project_id: int | None = None) -> dict[str, Any]:
        """Move resources to trash in bulk.

        Args:
            items: Non-empty list of ``{"id": int, "type": str}`` dicts, where
                ``type`` is one of ``"dataview"``, ``"dataset"``,
                ``"dashboard"``, or ``"automation"``.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the async job info for the bulk-trash operation.

        Raises:
            MammothValidationError: If *items* is empty or any entry is
                malformed.
        """
        _validate_items(items)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/trash",
            json={"items": items},
        )

    def restore(
        self, items: _list[dict[str, Any]], project_id: int | None = None
    ) -> dict[str, Any]:
        """Restore resources from trash in bulk.

        Args:
            items: Non-empty list of ``{"id": int, "type": str}`` dicts, where
                ``type`` is one of ``"dataview"``, ``"dataset"``,
                ``"dashboard"``, or ``"automation"``.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the async job info for the bulk-restore operation.

        Raises:
            MammothValidationError: If *items* is empty or any entry is
                malformed.
        """
        _validate_items(items)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/trash/restore",
            json={"items": items},
        )
