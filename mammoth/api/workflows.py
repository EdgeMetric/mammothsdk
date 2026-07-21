"""Workflows API client for managing project workflows in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by the `list` method name

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_WORKFLOW_ID_POSITIVE = "`workflow_id` must be a positive integer, got {0}."
ERR_BLOCK_ID_POSITIVE = "`block_id` must be a positive integer, got {0}."


class WorkflowsAPI:
    """Client for managing workflows under projects.

    Access via ``client.workflows``::

        workflows = client.workflows.list()
        workflow = client.workflows.create(name="Sales pipeline")
        client.workflows.block_add(workflow["id"], block_type="source")
        client.workflows.delete(workflow["id"])
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

    @staticmethod
    def _check_project_id(project_id: int | None) -> None:
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))

    @staticmethod
    def _check_workflow_id(workflow_id: int) -> None:
        if workflow_id <= 0:
            raise MammothValidationError(ERR_WORKFLOW_ID_POSITIVE.format(workflow_id))

    @staticmethod
    def _check_block_id(block_id: int) -> None:
        if block_id <= 0:
            raise MammothValidationError(ERR_BLOCK_ID_POSITIVE.format(block_id))

    def list(self, project_id: int | None = None) -> _list[dict[str, Any]]:
        """List workflows in a project.

        Args:
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            List of workflow dicts.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_list("GET", f"/workspaces/{ws}/projects/{proj}/workflows")

    def create(
        self,
        name: str,
        shape: str = "blank",
        purpose: str | None = None,
        seed_datasource_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new workflow.

        Args:
            name: Workflow name (max 200 chars).
            shape: Shape template: ``"blank"``, ``"pipeline"``, ``"merge"``,
                ``"split"``, or ``"full"`` (default ``"blank"``).
            purpose: Optional natural-language purpose for the workflow.
            seed_datasource_id: Optional existing datasource ID to anchor the
                workflow to.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with created workflow info.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {"name": name, "shape": shape}
        if purpose is not None:
            body["purpose"] = purpose
        if seed_datasource_id is not None:
            body["seed_datasource_id"] = seed_datasource_id
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows", json=body
        )

    def get(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Get workflow details.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with workflow details.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}"
        )

    def update(
        self,
        workflow_id: int,
        name: str | None = None,
        purpose: str | None = None,
        pipeline_summary: str | None = None,
        notes: str | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update workflow metadata.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            name: New workflow name (max 200 chars).
            purpose: New natural-language purpose.
            pipeline_summary: New pipeline summary text.
            notes: New free-form notes.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with updated workflow info.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if purpose is not None:
            body["purpose"] = purpose
        if pipeline_summary is not None:
            body["pipeline_summary"] = pipeline_summary
        if notes is not None:
            body["notes"] = notes
        return self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}", json=body
        )

    def delete(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Delete a workflow.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with deletion result.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}"
        )

    def graph(self, project_id: int | None = None) -> dict[str, Any]:
        """Get the project's workflow graph.

        Args:
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict describing the project workflow graph.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/graph"
        )

    def cleanup(self, project_id: int | None = None) -> dict[str, Any]:
        """Clean up ghost (orphaned skeleton) workflows in a project.

        Args:
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with cleanup result.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows/cleanup"
        )

    def from_template(
        self,
        template_id: int,
        workflow_name: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Instantiate a new workflow from a workspace template.

        Args:
            template_id: ID of the workspace template to instantiate.
            workflow_name: Name for the new workflow (max 200 chars).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the newly created workflow info.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"template_id": template_id, "workflow_name": workflow_name}
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows/from-template", json=body
        )

    def workspace_datasets(self, project_id: int | None = None) -> _list[dict[str, Any]]:
        """List workspace datasets available to workflows in a project.

        Args:
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            List of dataset dicts.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/workspace-datasets"
        )

    def workspace_exports(self, project_id: int | None = None) -> _list[dict[str, Any]]:
        """List workspace exports available to workflows in a project.

        Args:
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            List of export dicts.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/workspace-exports"
        )

    def workspace_sources(self, project_id: int | None = None) -> _list[dict[str, Any]]:
        """List workspace sources available to workflows in a project.

        Args:
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            List of source dicts.

        Raises:
            MammothValidationError: If *project_id* <= 0.
        """
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/workspace-sources"
        )

    def block_add(
        self,
        workflow_id: int,
        block_type: str,
        display_name: str | None = None,
        connection_type: str | None = None,
        position_hint: dict[str, Any] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Add a skeleton block to a workflow.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            block_type: Block type: ``"source"``, ``"dataset"``, or ``"export"``.
            display_name: Optional display name for the block (max 200 chars).
            connection_type: Optional connector or handler type (max 32 chars).
            position_hint: Optional canvas position hint.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the created skeleton block info.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {"block_type": block_type}
        if display_name is not None:
            body["display_name"] = display_name
        if connection_type is not None:
            body["connection_type"] = connection_type
        if position_hint is not None:
            body["position_hint"] = position_hint
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks",
            json=body,
        )

    def block_auth(
        self,
        workflow_id: int,
        block_id: int,
        auth_data: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Patch a workflow block's auth credentials.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            block_id: ID of the block (must be > 0).
            auth_data: Auth credentials for the block.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the updated block info.

        Raises:
            MammothValidationError: If *workflow_id* <= 0, *block_id* <= 0, or
                *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_block_id(block_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"auth_data": auth_data}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks/{block_id}/auth",
            json=body,
        )

    def block_type(
        self,
        workflow_id: int,
        block_id: int,
        connection_type: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Patch a workflow block's connector/handler type.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            block_id: ID of the block (must be > 0).
            connection_type: Connector or handler type (max 32 chars).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the updated block info.

        Raises:
            MammothValidationError: If *workflow_id* <= 0, *block_id* <= 0, or
                *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_block_id(block_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"connection_type": connection_type}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks/{block_id}/type",
            json=body,
        )

    def block_config(
        self,
        workflow_id: int,
        block_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Promote a configured skeleton block to a real DB row.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            block_id: ID of the block (must be > 0).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the promoted block/resource info.

        Raises:
            MammothValidationError: If *workflow_id* <= 0, *block_id* <= 0, or
                *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_block_id(block_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks/{block_id}/config",
        )

    def canvas(
        self,
        workflow_id: int,
        canvas_state: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a workflow's canvas state.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            canvas_state: Canvas state JSON payload.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the updated canvas state.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"canvas_state": canvas_state}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/canvas",
            json=body,
        )
