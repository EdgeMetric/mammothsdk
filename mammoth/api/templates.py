"""Workspace templates API client for Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_TEMPLATE_ID_POSITIVE = "`template_id` must be a positive integer, got {0}."


class TemplatesAPI:
    """Client for workspace template operations.

    Templates are workspace-scoped, reusable pipeline/project blueprints.

    Access via ``client.templates``::

        template = client.templates.create(body={"name": "Sales starter"})
        client.templates.delete(template["id"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    @staticmethod
    def _check_template_id(template_id: int) -> None:
        if template_id <= 0:
            raise MammothValidationError(ERR_TEMPLATE_ID_POSITIVE.format(template_id))

    def list(self) -> dict[str, Any]:
        """List templates in the workspace.

        Returns:
            Dict with the templates list.
        """
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/templates")

    def get(self, template_id: int) -> dict[str, Any]:
        """Get details of a template.

        Args:
            template_id: ID of the template.

        Returns:
            Dict with template details.

        Raises:
            MammothValidationError: If *template_id* is not a positive integer.
        """
        self._check_template_id(template_id)
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/templates/{template_id}"
        )

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create a new template.

        Args:
            body: Template creation payload.

        Returns:
            Dict with the created template.
        """
        return self._client._request_json("POST", f"/workspaces/{self._ws()}/templates", json=body)

    def update(self, template_id: int, body: dict[str, Any]) -> dict[str, Any]:
        """Update a template via patch operations.

        Args:
            template_id: ID of the template.
            body: Patch operations payload.

        Returns:
            Dict with the updated template.

        Raises:
            MammothValidationError: If *template_id* is not a positive integer.
        """
        self._check_template_id(template_id)
        return self._client._request_json(
            "PATCH", f"/workspaces/{self._ws()}/templates/{template_id}", json=body
        )

    def delete(self, template_id: int) -> dict[str, Any]:
        """Delete a template.

        Args:
            template_id: ID of the template.

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *template_id* is not a positive integer.
        """
        self._check_template_id(template_id)
        return self._client._request_json(
            "DELETE", f"/workspaces/{self._ws()}/templates/{template_id}"
        )
