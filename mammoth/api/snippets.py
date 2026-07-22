"""Snippets API client for managing reusable SQL/expression snippets in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

ERR_SNIPPET_ID_POSITIVE = "`snippet_id` must be a positive integer, got {0}."
ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."


class SnippetsAPI:
    """Client for managing workspace and project snippets.

    Access via ``client.snippets``::

        snippets = client.snippets.list()
        snippet = client.snippets.create(
            name="my_snippet", code="SELECT * FROM table", language="sql", project_id=1,
        )
        client.snippets.rerun(snippet["id"])
        client.snippets.delete(snippet["id"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    @staticmethod
    def _check_snippet_id(snippet_id: int) -> None:
        if snippet_id <= 0:
            raise MammothValidationError(ERR_SNIPPET_ID_POSITIVE.format(snippet_id))

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
        """List snippets in the workspace.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.
            search: Free-text search over snippet names.
            group_id: Filter by parameter group ID.
            sort: Sort specification.
            project_id: Filter to a project's snippets (omit for
                workspace-scoped snippets only).

        Returns:
            Dict with the snippets list and pagination info.
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
            "GET", f"/workspaces/{self._ws()}/snippets", params=params or None
        )

    def create(
        self,
        name: str,
        code: str,
        language: str,
        description: str | None = None,
        group_id: int | None = None,
        scope: str = "project",
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new snippet at workspace or project scope.

        Args:
            name: Snippet name (max 100 chars).
            code: Snippet source code.
            language: Language of the snippet (``"sql"`` or ``"expression"``).
            description: Optional description (max 500 chars).
            group_id: Optional parameter group ID to organize the snippet.
            scope: ``"project"`` or ``"workspace"`` (default ``"project"``).
            project_id: Required when *scope* is ``"project"``.

        Returns:
            Dict with created snippet info.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        body: dict[str, Any] = {
            "name": name,
            "code": code,
            "language": language,
            "scope": scope,
        }
        if description is not None:
            body["description"] = description
        if group_id is not None:
            body["group_id"] = group_id
        if project_id is not None:
            body["project_id"] = project_id
        return self._client._request_json("POST", f"/workspaces/{self._ws()}/snippets", json=body)

    def get(self, snippet_id: int) -> dict[str, Any]:
        """Get snippet details.

        Args:
            snippet_id: ID of the snippet (must be > 0).

        Returns:
            Dict with snippet details.

        Raises:
            MammothValidationError: If *snippet_id* <= 0.
        """
        self._check_snippet_id(snippet_id)
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/snippets/{snippet_id}")

    def update(
        self,
        snippet_id: int,
        name: str | None = None,
        code: str | None = None,
        language: str | None = None,
        description: str | None = None,
        group_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a snippet.

        Args:
            snippet_id: ID of the snippet (must be > 0).
            name: New snippet name (max 100 chars).
            code: New snippet source code.
            language: New language of the snippet.
            description: New description (max 500 chars).
            group_id: New parameter group ID.

        Returns:
            Dict with updated snippet info.

        Raises:
            MammothValidationError: If *snippet_id* <= 0.
        """
        self._check_snippet_id(snippet_id)
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if code is not None:
            body["code"] = code
        if language is not None:
            body["language"] = language
        if description is not None:
            body["description"] = description
        if group_id is not None:
            body["group_id"] = group_id
        return self._client._request_json(
            "PATCH", f"/workspaces/{self._ws()}/snippets/{snippet_id}", json=body
        )

    def delete(self, snippet_id: int) -> dict[str, Any]:
        """Delete a snippet.

        Args:
            snippet_id: ID of the snippet (must be > 0).

        Returns:
            Dict with deletion result.

        Raises:
            MammothValidationError: If *snippet_id* <= 0.
        """
        self._check_snippet_id(snippet_id)
        return self._client._request_json(
            "DELETE", f"/workspaces/{self._ws()}/snippets/{snippet_id}"
        )

    def dependencies(self, snippet_id: int) -> dict[str, Any]:
        """Get objects that depend on a snippet.

        Args:
            snippet_id: ID of the snippet (must be > 0).

        Returns:
            Dict with dependency info.

        Raises:
            MammothValidationError: If *snippet_id* <= 0.
        """
        self._check_snippet_id(snippet_id)
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/snippets/{snippet_id}/dependencies"
        )

    def duplicate(self, snippet_id: int) -> dict[str, Any]:
        """Duplicate a snippet.

        Args:
            snippet_id: ID of the snippet (must be > 0).

        Returns:
            Dict with the duplicated snippet info.

        Raises:
            MammothValidationError: If *snippet_id* <= 0.
        """
        self._check_snippet_id(snippet_id)
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/snippets/{snippet_id}/duplicate"
        )

    def rerun(self, snippet_id: int) -> dict[str, Any]:
        """Rerun a snippet.

        Args:
            snippet_id: ID of the snippet (must be > 0).

        Returns:
            Dict with rerun result.

        Raises:
            MammothValidationError: If *snippet_id* <= 0.
        """
        self._check_snippet_id(snippet_id)
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/snippets/{snippet_id}/rerun"
        )
