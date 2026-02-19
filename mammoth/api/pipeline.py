"""
Pipeline tasks HTTP client for managing dataview transformations.

Internal module used by the View object to manage transformation pipeline tasks.
Not intended for direct use — use client.views.get(id) to get a View object instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..exceptions import MammothAPIError

if TYPE_CHECKING:
    from ..client import MammothClient


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

    def _find_dataset_for_dataview(self, dataview_id: int) -> int:
        """Find which dataset contains the specified dataview.

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

        datasets_response = self._client.datasets.list(
            workspace_id=workspace_id, project_id=project_id
        )

        for dataset in datasets_response.get("datasets", []):
            dataset_id = dataset["id"]
            try:
                dataviews_response = self._client.dataviews.list(
                    dataset_id=dataset_id, workspace_id=workspace_id, project_id=project_id
                )
                for dv in dataviews_response.get("dataviews", []):
                    if dv.get("id") == dataview_id:
                        return dataset_id
            except (MammothAPIError, KeyError):
                continue

        raise ValueError(f"Dataview {dataview_id} not found in any dataset in project {project_id}")

    def _base_url(self, ws_id: int, proj_id: int, ds_id: int, dv_id: int) -> str:
        return f"/workspaces/{ws_id}/projects/{proj_id}/datasets/{ds_id}/dataviews/{dv_id}/pipeline"

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
        return self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/tasks", json=payload
        )

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
        return self._client._request_json(
            "PATCH", f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}", json=task_spec
        )

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
        return self._client._request_json(
            "DELETE", f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}"
        )

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
        return self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/tasks/preview", json=task_spec
        )

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
        return self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/draft", json={"command": command}
        )
