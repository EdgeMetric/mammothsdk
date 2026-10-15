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
ERR_RUN_ID_EMPTY = "`run_id` must be a non-empty string."
ERR_STEP_NEGATIVE = "`step` must be an integer >= 0, got {0!r}."
ERR_DUPLICATE_NAME = "`name` must be 1 to 255 characters."
ERR_DUPLICATE_DATASETS = "`dataset_ids` must be a non-empty list of positive dataset ids."
_NAME_MAX = 255


class WorkflowsAPI:
    """Client for managing workflows under projects.

    Access via ``client.workflows``::

        workflows = await client.workflows.list()
        workflow = await client.workflows.create(name="Sales pipeline")
        await client.workflows.block_add(workflow["id"], block_type="source")
        await client.workflows.delete(workflow["id"])
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
    def _check_run_id(run_id: str) -> None:
        if not isinstance(run_id, str) or not run_id.strip() or "/" in run_id:
            raise MammothValidationError(ERR_RUN_ID_EMPTY)

    @staticmethod
    def _check_block_id(block_id: int) -> None:
        if block_id <= 0:
            raise MammothValidationError(ERR_BLOCK_ID_POSITIVE.format(block_id))

    async def list(self, project_id: int | None = None) -> _list[dict[str, Any]]:
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
        return await self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows"
        )

    async def create(
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
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows", json=body
        )

    async def get(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
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
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}"
        )

    async def update(
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
        return await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}", json=body
        )

    async def delete(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
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
        return await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}"
        )

    async def graph(self, project_id: int | None = None) -> dict[str, Any]:
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
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/graph"
        )

    async def cleanup(self, project_id: int | None = None) -> dict[str, Any]:
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
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows/cleanup"
        )

    async def from_template(
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
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows/from-template", json=body
        )

    async def workspace_datasets(self, project_id: int | None = None) -> _list[dict[str, Any]]:
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
        return await self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/workspace-datasets"
        )

    async def workspace_exports(self, project_id: int | None = None) -> _list[dict[str, Any]]:
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
        return await self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/workspace-exports"
        )

    async def workspace_sources(self, project_id: int | None = None) -> _list[dict[str, Any]]:
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
        return await self._client._request_list(
            "GET", f"/workspaces/{ws}/projects/{proj}/workflows/workspace-sources"
        )

    async def block_add(
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
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks",
            json=body,
        )

    async def block_auth(
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
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks/{block_id}/auth",
            json=body,
        )

    async def block_type(
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
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks/{block_id}/type",
            json=body,
        )

    async def block_config(
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
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/blocks/{block_id}/config",
        )

    async def canvas(
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
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/canvas",
            json=body,
        )

    async def save(
        self,
        workflow_id: int,
        keys: _list[str] | None = None,
        expected_version: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Save a workflow's unsaved canvas changes.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            keys: Save only these unsaved changes (by key) and what they need; the
                rest stay unsaved. Omitted: save every change.
            expected_version: The canvas version the client last read; the server
                answers 409 if it has moved.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the saved workflow.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"keys": keys, "expected_version": expected_version}
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/save",
            json={name: value for name, value in body.items() if value is not None},
        )

    async def duplicate(
        self,
        name: str,
        dataset_ids: _list[int],
        source_workflow_id: int | None = None,
        wait: bool = True,
        timeout: float | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Duplicate a workflow into the same project as a new workflow.

        Copies the workflow's datasets with their rows, views and steps in one background
        job. Send-tos between the copies are recreated; datasets the workflow only joins
        are shared, not copied; automations and outside exports are not copied.

        Args:
            name: Name of the new workflow (1-255 characters).
            dataset_ids: IDs of the datasets to copy (at least one, each > 0).
            source_workflow_id: ID of the workflow being copied (optional).
            wait: Wait for the job to finish (default True). False returns the queued job.
            timeout: Seconds to wait (uses ``client.job_timeout`` if not provided).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            The queued job dict (``job_id``) when *wait* is False; the finished job
            otherwise, whose ``response`` carries ``workflow_id``.

        Raises:
            MammothValidationError: If *name* or *dataset_ids* are invalid, or *project_id*
                or *source_workflow_id* <= 0.
            MammothJobFailedError: If the job fails (when *wait* is True).
            MammothJobTimeoutError: If the job does not finish in time (when *wait* is True).
        """
        if not isinstance(name, str) or not 1 <= len(name) <= _NAME_MAX:
            raise MammothValidationError(ERR_DUPLICATE_NAME)
        if not dataset_ids or any(
            isinstance(d, bool) or not isinstance(d, int) or d <= 0 for d in dataset_ids
        ):
            raise MammothValidationError(ERR_DUPLICATE_DATASETS)
        if source_workflow_id is not None:
            self._check_workflow_id(source_workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {"name": name, "dataset_ids": dataset_ids}
        if source_workflow_id is not None:
            body["source_workflow_id"] = source_workflow_id
        queued = await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/workflows/duplicate", json=body
        )
        job_id = queued.get("job_id")
        if not wait or job_id is None:
            return queued
        return await self._client.jobs.wait_for_job(job_id, timeout=timeout)

    async def undo_save(
        self,
        workflow_id: int,
        run_id: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Undo a workflow's latest finished Save.

        Puts back what that Save built, newest first, as a run of its own
        (``canvas_state.save_run``, kind ``undo``). Refused while a Save runs, for an older
        Save, or when something was built since on what it made. Unsaved changes stay
        discarded.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            run_id: ID of the Save run to undo.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the workflow and its canvas state.

        Raises:
            MammothValidationError: If *workflow_id* or *project_id* <= 0, or *run_id* is empty.
        """
        self._check_workflow_id(workflow_id)
        self._check_run_id(run_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/save/{run_id}/undo",
        )

    async def cancel_save_step(
        self,
        workflow_id: int,
        run_id: str,
        step: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Cancel one step of the workflow's running Save.

        The step ends cancelled and the steps that need it are skipped. Best effort: a
        Mammoth job the step started may still finish, so a step that creates something
        is held for a check.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            run_id: ID of the running Save.
            step: Index of the step to cancel (>= 0).
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the workflow and its canvas state.

        Raises:
            MammothValidationError: If *workflow_id* or *project_id* <= 0, *run_id* is
                empty or *step* is negative.
        """
        self._check_workflow_id(workflow_id)
        self._check_run_id(run_id)
        if isinstance(step, bool) or not isinstance(step, int) or step < 0:
            raise MammothValidationError(ERR_STEP_NEGATIVE.format(step))
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/save/{run_id}"
            f"/steps/{step}/cancel",
        )

    async def set_archived(
        self,
        workflow_id: int,
        archived: bool,
        dataset_ids: _list[int] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Archive a workflow, or bring it back.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            archived: True to archive, False to bring the workflow back.
            dataset_ids: The workflow's datasets now; it reads as active once it
                has others.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the workflow metadata.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {"archived": archived}
        if dataset_ids is not None:
            body["dataset_ids"] = dataset_ids
        return await self._client._request_json(
            "PUT",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/archived",
            json=body,
        )

    async def attach_dataset(
        self,
        workflow_id: int,
        datasource_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Attach a dataset to a workflow.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            datasource_id: ID of the dataset to attach.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the workflow metadata and its skeleton blocks.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/datasets",
            json={"datasource_id": datasource_id},
        )

    async def resolve_held(
        self,
        workflow_id: int,
        key: str,
        built: bool,
        expected_version: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Settle a change that a Save held back.

        Args:
            workflow_id: ID of the workflow (must be > 0).
            key: The held change's key.
            built: True when the change is already in Mammoth (it is not built
                again); False to lift the hold so the next Save builds it.
            expected_version: The canvas version the client last read.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with the workflow metadata and its skeleton blocks.

        Raises:
            MammothValidationError: If *workflow_id* <= 0 or *project_id* <= 0.
        """
        self._check_workflow_id(workflow_id)
        self._check_project_id(project_id)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {"key": key, "built": built}
        if expected_version is not None:
            body["expected_version"] = expected_version
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/workflows/{workflow_id}/held/resolve",
            json=body,
        )
