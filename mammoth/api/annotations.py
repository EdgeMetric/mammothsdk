"""Annotations API client for commenting on Mammoth resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

ERR_ANNOTATION_ID_POSITIVE = "`annotation_id` must be a positive integer, got {0}."
ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_TARGET_ID_POSITIVE = "`target_id` must be a positive integer, got {0}."
ERR_TARGET_TYPE_INVALID = "`target_type` must be one of {valid}, got {value!r}."
ERR_STATUS_INVALID = "`status` must be one of {valid}, got {value!r}."
ERR_BODY_REQUIRED = "`body` must be a non-empty string."

VALID_TARGET_TYPES = frozenset({"dataset", "dataview", "workflow"})
VALID_STATUSES = frozenset({"open", "resolved"})


class AnnotationsAPI:
    """Client for managing annotations (comment threads) on project resources.

    Access via ``client.annotations``::

        annotation = client.annotations.create(
            target_type="dataview", target_id=42, body="Looks off, please check."
        )
        client.annotations.comment_add(annotation["id"], body="Fixed in latest run.")
        client.annotations.update(annotation["id"], status="resolved")
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
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """List annotations for a project.

        Args:
            project_id: Project ID (uses client default if not provided).
            target_type: Filter by target type (``"dataset"``, ``"dataview"``,
                or ``"workflow"``).
            target_id: Filter by target resource ID.

        Returns:
            List of annotation dicts.

        Raises:
            MammothValidationError: If *target_type* is given and invalid.
        """
        if target_type is not None and target_type not in VALID_TARGET_TYPES:
            raise MammothValidationError(
                ERR_TARGET_TYPE_INVALID.format(valid=sorted(VALID_TARGET_TYPES), value=target_type)
            )
        ws = self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if target_type is not None:
            params["target_type"] = target_type
        if target_id is not None:
            params["target_id"] = target_id
        return self._client._request_list(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/annotations",
            params=params or None,
        )

    def create(
        self,
        target_type: str,
        target_id: int,
        body: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new annotation on a resource.

        Args:
            target_type: Type of the annotated resource (``"dataset"``,
                ``"dataview"``, or ``"workflow"``).
            target_id: ID of the annotated resource (must be > 0).
            body: Initial comment body (non-empty).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the created annotation.

        Raises:
            MammothValidationError: If *target_type* is invalid, *target_id*
                is not positive, or *body* is empty.
        """
        if target_type not in VALID_TARGET_TYPES:
            raise MammothValidationError(
                ERR_TARGET_TYPE_INVALID.format(valid=sorted(VALID_TARGET_TYPES), value=target_type)
            )
        if target_id <= 0:
            raise MammothValidationError(ERR_TARGET_ID_POSITIVE.format(target_id))
        if not body:
            raise MammothValidationError(ERR_BODY_REQUIRED)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/annotations",
            json={"target_type": target_type, "target_id": target_id, "body": body},
        )

    def delete(self, annotation_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Delete an annotation.

        Args:
            annotation_id: ID of the annotation to delete (must be > 0).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *annotation_id* is not positive.
        """
        if annotation_id <= 0:
            raise MammothValidationError(ERR_ANNOTATION_ID_POSITIVE.format(annotation_id))
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/annotations/{annotation_id}"
        )

    def update(
        self,
        annotation_id: int,
        status: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an annotation's status.

        Args:
            annotation_id: ID of the annotation to update (must be > 0).
            status: New status, either ``"open"`` or ``"resolved"``.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the updated annotation.

        Raises:
            MammothValidationError: If *annotation_id* is not positive or
                *status* is invalid.
        """
        if annotation_id <= 0:
            raise MammothValidationError(ERR_ANNOTATION_ID_POSITIVE.format(annotation_id))
        if status not in VALID_STATUSES:
            raise MammothValidationError(
                ERR_STATUS_INVALID.format(valid=sorted(VALID_STATUSES), value=status)
            )
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/annotations/{annotation_id}",
            json={"status": status},
        )

    def comment_add(
        self,
        annotation_id: int,
        body: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Add a comment to an existing annotation thread.

        Args:
            annotation_id: ID of the annotation (must be > 0).
            body: Comment text (non-empty).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the created comment.

        Raises:
            MammothValidationError: If *annotation_id* is not positive or
                *body* is empty.
        """
        if annotation_id <= 0:
            raise MammothValidationError(ERR_ANNOTATION_ID_POSITIVE.format(annotation_id))
        if not body:
            raise MammothValidationError(ERR_BODY_REQUIRED)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/annotations/{annotation_id}/comments",
            json={"body": body},
        )
