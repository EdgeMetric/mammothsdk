"""
Pipeline tasks HTTP client for managing dataview transformations.

Internal module used by the View object to manage transformation pipeline tasks.
Not intended for direct use — use client.views.get(id) to get a View object instead.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from ..exceptions import MammothAPIError, MammothJobTimeoutError, MammothTransformError

_list = list  # Alias to avoid shadowing by method name

if TYPE_CHECKING:
    from ..client import MammothClient

logger = logging.getLogger(__name__)

PIPELINE_TERMINAL_STATES = frozenset({"ready", "runtime_error", "ref_error"})


class PipelineAPI:
    """Low-level HTTP client for pipeline task endpoints.

    Used internally by View objects. Access via client.pipeline.
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _resolve_ids(
        self, dataview_id: int, dataset_id: int | None = None
    ) -> tuple[int, int, int, int]:
        """Resolve workspace, project, dataset IDs for a dataview.

        Args:
            dataview_id: ID of the target dataview.
            dataset_id: Dataset ID if known (avoids lookup).

        Returns:
            Tuple of (workspace_id, project_id, dataset_id, dataview_id).
        """
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        return workspace_id, project_id, dataset_id, dataview_id

    def find_dataset_for_dataview(self, dataview_id: int) -> int:
        """Public typed resolver: find the dataset that contains a dataview.

        This is the supported public seam for dataview-to-dataset resolution.
        Callers must not reach into the private ``_find_dataset_for_dataview``
        helper across sub-clients.

        Args:
            dataview_id: ID of the dataview to resolve.

        Returns:
            The dataset_id that contains this dataview.
        """
        return self._find_dataset_for_dataview(dataview_id)

    def _find_dataset_for_dataview(self, dataview_id: int) -> int:
        """Find which dataset contains the specified dataview.

        Uses the browse API to discover datasets (including those nested
        inside folders), then checks each dataset for the dataview.

        Args:
            dataview_id: ID of the dataview to search for.

        Returns:
            The dataset_id that contains this dataview.

        Raises:
            ValueError: If dataview is not found in any dataset.
        """
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        # Use workspace browse to get project's children (datasets + folders)
        browse_response = self._client.browse.workspace_resources(
            workspace_id=workspace_id, level=2
        )
        project_children: _list[dict[str, Any]] = []
        for resource in browse_response.get("resources", []):
            if resource.get("id") == project_id:
                project_children = resource.get("children", [])
                break

        # DFS through folders to collect all dataset IDs
        dataset_ids = self._collect_dataset_ids(project_children, project_id, workspace_id)

        # Check each dataset for the dataview
        for dataset_id in dataset_ids:
            try:
                self._client.dataviews.get(
                    dataset_id=dataset_id,
                    dataview_id=dataview_id,
                    workspace_id=workspace_id,
                    project_id=project_id,
                )
                return dataset_id
            except MammothAPIError, KeyError:
                continue

        raise ValueError(f"Dataview {dataview_id} not found in any dataset in project {project_id}")

    def _collect_dataset_ids(
        self,
        children: _list[dict[str, Any]],
        project_id: int,
        workspace_id: int,
    ) -> _list[int]:
        """Collect all dataset IDs from browse children, recursing into folders.

        Folder browsing is parallelized to avoid sequential latency when
        projects have many nested folders.

        Args:
            children: List of browse resource children.
            project_id: Current project ID.
            workspace_id: Current workspace ID.

        Returns:
            List of dataset IDs found.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        dataset_ids: _list[int] = []
        folders: _list[dict[str, Any]] = []

        for child in children:
            child_type = child.get("type", "")
            if child_type == "datasource":
                dataset_ids.append(child["id"])
            elif child_type == "label":
                folders.append(child)

        if not folders:
            return dataset_ids

        def _browse_folder(folder_id: int) -> _list[dict[str, Any]]:
            resp = self._client.browse.folder_resources(
                folder_id=folder_id,
                project_id=project_id,
                workspace_id=workspace_id,
                level=2,
            )
            all_children: _list[dict[str, Any]] = []
            for sub_resource in resp.get("resources", []):
                all_children.extend(sub_resource.get("children", []))
            return all_children

        with ThreadPoolExecutor(max_workers=min(len(folders), 8)) as pool:
            futures = {pool.submit(_browse_folder, folder["id"]): folder for folder in folders}
            for future in as_completed(futures):
                try:
                    sub_children = future.result()
                    dataset_ids.extend(
                        self._collect_dataset_ids(sub_children, project_id, workspace_id)
                    )
                except MammothAPIError:
                    continue

        return dataset_ids

    def _base_url(self, ws_id: int, proj_id: int, ds_id: int, dv_id: int) -> str:
        return f"/workspaces/{ws_id}/projects/{proj_id}/datasets/{ds_id}/dataviews/{dv_id}/pipeline"

    def _dv_url(self, ws_id: int, proj_id: int, ds_id: int, dv_id: int) -> str:
        return f"/workspaces/{ws_id}/projects/{proj_id}/datasets/{ds_id}/dataviews/{dv_id}"

    def get_pipeline(self, dataview_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """Get pipeline state for a dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Pipeline state dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json("GET", self._base_url(ws, proj, ds, dv))

    def list_tasks(self, dataview_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """List all pipeline tasks for a dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Dict with tasks list.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json("GET", f"{self._base_url(ws, proj, ds, dv)}/tasks")

    def add_task(
        self, dataview_id: int, task_spec: dict[str, Any], dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Add a new transformation task to the pipeline.

        Args:
            dataview_id: ID of the dataview.
            task_spec: Task specification dict (varies by task type).
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Dict with created task info or job info.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        payload = {"DATAVIEW_ID": dv, **task_spec}
        response = self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/tasks", json=payload
        )
        return self._client._wait_if_job(response)

    def get_task(
        self, dataview_id: int, task_id: int, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Get a specific pipeline task.

        Args:
            dataview_id: ID of the dataview.
            task_id: ID of the task.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Task details dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json(
            "GET", f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}"
        )

    def update_task(
        self,
        dataview_id: int,
        task_id: int,
        task_spec: dict[str, Any],
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing pipeline task.

        Args:
            dataview_id: ID of the dataview.
            task_id: ID of the task to update.
            task_spec: Updated task specification.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Updated task dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "PATCH", f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}", json=task_spec
        )
        return self._client._wait_if_job(response)

    def delete_task(
        self, dataview_id: int, task_id: int, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Delete a pipeline task.

        Args:
            dataview_id: ID of the dataview.
            task_id: ID of the task to delete.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Delete confirmation dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "DELETE", f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}"
        )
        return self._client._wait_if_job(response)

    def preview_task(
        self, dataview_id: int, task_spec: dict[str, Any], dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Preview task results without adding to pipeline.

        Args:
            dataview_id: ID of the dataview.
            task_spec: Task specification to preview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Preview result dict with sample data.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/task_preview", json=task_spec
        )
        return self._client._wait_if_job(response)

    def draft_mode(
        self, dataview_id: int, command: str, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Manage draft mode for a dataview pipeline.

        Args:
            dataview_id: ID of the dataview.
            command: Draft mode command ("enter", "commit", "discard").
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Draft mode state dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "POST",
            f"{self._dv_url(ws, proj, ds, dv)}/draft-mode",
            json={"draft_operation": command},
        )
        return self._client._wait_if_job(response)

    def get_draft_status(self, dataview_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """Read server-backed draft state for a dataview pipeline.

        Draft state must be read from the server so it is consistent across
        separate processes. This reads the current pipeline and reports whether
        the dataview is in draft mode, using the server's own pipeline state
        rather than any process-local flag.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            A dict with ``dataview_id``, ``is_draft``, and the raw pipeline
            ``draft`` section when the server provides one.
        """
        pipeline = self.get_pipeline(dataview_id, dataset_id)
        draft_section = pipeline.get("draft")
        if draft_section is None:
            draft_section = pipeline.get("draft_mode")
        is_draft = bool(
            pipeline.get("is_draft")
            or pipeline.get("in_draft_mode")
            or (isinstance(draft_section, dict) and draft_section.get("active"))
            or (isinstance(draft_section, dict) and draft_section.get("is_draft"))
        )
        return {
            "dataview_id": dataview_id,
            "is_draft": is_draft,
            "draft": draft_section,
        }

    def edit_pipeline(
        self,
        dataview_id: int,
        patches: _list[dict[str, Any]],
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """PATCH pipeline with operations (auto_run, run, reset, etc.).

        Args:
            dataview_id: ID of the dataview.
            patches: List of patch operation dicts.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Updated pipeline state dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json(
            "PATCH", self._base_url(ws, proj, ds, dv), json={"patches": patches}
        )

    def wait_for_pipeline(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
        timeout: int | None = None,
        poll_interval: int = 3,
    ) -> dict[str, Any]:
        """Poll pipeline state until it reaches a terminal state.

        After any pipeline mutation (add_task, delete_task, sql_generation),
        the pipeline transitions through transient states before data is ready:
        ``modifying → modified → running → ready``.

        This method blocks until the pipeline reaches a terminal state
        (``ready``, ``runtime_error``, ``ref_error``).

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).
            timeout: Max wait time in seconds (default: client.pipeline_timeout).
            poll_interval: Seconds between polls (default: 3).

        Returns:
            Final pipeline state dict.

        Raises:
            MammothTransformError: If pipeline reaches ``runtime_error`` or ``ref_error``.
            MammothJobTimeoutError: If timeout is exceeded.
        """
        effective_timeout = (
            timeout if timeout is not None else int(getattr(self._client, "pipeline_timeout", 3600))
        )

        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        url = self._base_url(ws, proj, ds, dv)
        deadline = time.monotonic() + effective_timeout

        while True:
            pipeline = self._client._request_json("GET", url)
            state = pipeline.get("state", "").lower()

            if state in PIPELINE_TERMINAL_STATES:
                if state in ("runtime_error", "ref_error"):
                    detail = pipeline.get("error", state)
                    raise MammothTransformError(
                        f"Pipeline failed with state '{state}': {detail}",
                        details={"pipeline_state": state, "pipeline": pipeline},
                    )
                logger.debug("Pipeline ready for dataview %d (state=%s)", dataview_id, state)
                return pipeline

            if time.monotonic() >= deadline:
                raise MammothJobTimeoutError(job_id=dataview_id, timeout_seconds=effective_timeout)

            logger.debug("Pipeline state for dataview %d: %s — waiting...", dataview_id, state)
            time.sleep(poll_interval)
