"""
Datasets API client for managing datasets in Mammoth.
"""

from typing import Optional, Dict, Any, List


class DatasetsAPI:
    """Client for interacting with Mammoth Datasets API.

    Access via client.datasets:
        datasets = client.datasets.list()
        dataset = client.datasets.get(123)
        data = client.datasets.get_data(123)
    """

    def __init__(self, client):
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: Optional[int] = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, 'project_id', None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    def list(
        self,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        limit: int = 100,
        sort: str = "(created_at:desc)",
    ) -> Dict[str, Any]:
        """Get list of datasets in a project.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            limit: Maximum number of results (default 100).
            sort: Sort order (default "(created_at:desc)").

        Returns:
            Dict containing datasets list with id, name and other info.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params = {"fields": "id,name", "limit": limit, "sort": sort}
        return self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets", params=params)

    def get(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get dataset details by ID.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with complete dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}")

    def get_data(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> Dict[str, Any]:
        """Get the actual data from a dataset. Polls the job until completion.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Maximum wait time in seconds (default 300).
            poll_interval: Polling interval in seconds (default 2).

        Returns:
            Dict with dataset data.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        response = self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/data")

        if isinstance(response, dict) and 'job_id' in response:
            job_id = response['job_id']
            completed_job = self._client.jobs.wait_for_job(
                job_id=job_id, timeout=timeout, poll_interval=poll_interval,
            )
            return completed_job.get('response', completed_job)

        return response

    def create(
        self,
        dataset_spec: Dict[str, Any],
        ds_creation_type: str,
        folder_resource_id: Optional[str] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new dataset.

        Args:
            dataset_spec: Dataset specification (varies by creation type).
            ds_creation_type: Type of creation: "clone", "cloud", "sketch", "weburl".
            folder_resource_id: Optional folder resource ID.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        payload: Dict[str, Any] = {"dataset_spec": dataset_spec, "ds_creation_type": ds_creation_type}
        if folder_resource_id is not None:
            payload["folder_resource_id"] = folder_resource_id

        return self._client._request("POST", f"/workspaces/{ws}/projects/{proj}/datasets", json=payload)

    def update(
        self,
        dataset_id: int,
        patch_data: Dict[str, Any],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update a dataset.

        Args:
            dataset_id: ID of the dataset to update.
            patch_data: Patch operation data.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request("PATCH", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}", json={"patch": patch_data})

    def delete(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> None:
        """Delete a dataset.

        Args:
            dataset_id: ID of the dataset to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        self._client._request("DELETE", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}")

    def bulk_update(
        self,
        patch_data: Dict[str, Any],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update multiple datasets (bulk operation).

        Args:
            patch_data: Patch operation data for multiple datasets.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with bulk update result.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request("PATCH", f"/workspaces/{ws}/projects/{proj}/datasets", json={"patch": patch_data})

    def bulk_delete(
        self,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> None:
        """Delete multiple datasets (bulk operation).

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        self._client._request("DELETE", f"/workspaces/{ws}/projects/{proj}/datasets")

    def browse(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Browse dataset contents (dataviews, metadata).

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with dataset contents.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/browse")

    def list_batches(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> list:
        """List batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            List of batch dicts.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        response = self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches")
        return response.get("batches", response if isinstance(response, list) else [])

    def get_batch(
        self,
        dataset_id: int,
        batch_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get details of a specific batch.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with batch details.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}")

    def get_file_settings(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get file settings for a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with file settings.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request("GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings")
