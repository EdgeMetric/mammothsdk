"""Main client for the Mammoth Analytics SDK.

Provides ``MammothClient`` — the single entry point for all API interactions.
All sub-clients (projects, datasets, views, pipeline, exports, connectors,
dashboards, webhooks, automations, ai) are accessible as attributes.

Example::

    from mammoth import MammothClient

    client = MammothClient(
        api_key="your-api-key",
        api_secret="your-api-secret",
        workspace_id=11,
        base_url="https://app.mammoth.io/api/v2",
    )
    client.set_project_id(10)

    # List projects
    projects = client.projects.list()

    # Get a rich View object and apply transformations
    view = client.get_view(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests

from mammoth.api.activity_logs import ActivityLogsAPI
from mammoth.api.addons import AddonsAPI
from mammoth.api.ai import AIAPI
from mammoth.api.automations import AutomationsAPI
from mammoth.api.batches import BatchesAPI
from mammoth.api.browse import BrowseAPI
from mammoth.api.clientapps import ClientAppsAPI
from mammoth.api.connectors import ConnectorsAPI
from mammoth.api.dashboards import DashboardsAPI
from mammoth.api.datasets import DatasetsAPI
from mammoth.api.dataviews import DataviewsAPI
from mammoth.api.exports import ExportsAPI
from mammoth.api.external_keys import ExternalKeysAPI
from mammoth.api.files import FilesAPI
from mammoth.api.folders import FoldersAPI
from mammoth.api.jobs import JobsAPI
from mammoth.api.pipeline import PipelineAPI
from mammoth.api.projects import ProjectsAPI
from mammoth.api.reports import ReportsAPI
from mammoth.api.schedules import SchedulesAPI
from mammoth.api.user_profile import UserProfileAPI
from mammoth.api.webhooks import WebhooksAPI
from mammoth.api.workspace import WorkspaceAPI
from mammoth.exceptions import MammothAPIError, MammothAuthError


# Lazy __version__ import to avoid circular dependency with __init__
def _get_version() -> str:
    try:
        from mammoth import __version__
        return __version__
    except ImportError:
        return "0.2.0"

# ── Configurable defaults ─────────────────────────────────────
DEFAULT_TIMEOUT = 30  # seconds — max time for any single API call
DEFAULT_JOB_TIMEOUT = 60  # seconds — max time to poll a job to completion

_list = list  # Alias to avoid shadowing by method name


class ViewsResource:
    """Resource that returns rich View objects.

    Access via client.views::

        view = client.views.get(view_id)           # returns View object
        views = client.views.list(dataset_id)       # returns list of View objects
        view = client.views.create(dataset_id)      # returns View object
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def get(self, view_id: int, dataset_id: int | None = None) -> View:
        """Get a rich View object for a dataview.

        Args:
            view_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            View object with transformation methods and metadata.
        """
        from mammoth.view import View

        if dataset_id is None:
            dataset_id = self._client.pipeline._find_dataset_for_dataview(view_id)

        data = self._client.dataviews.get(
            dataset_id=dataset_id,
            dataview_id=view_id,
        )
        return View(self._client, data, dataset_id)

    def list(self, dataset_id: int) -> _list[View]:
        """List all dataviews in a dataset as View objects.

        Args:
            dataset_id: ID of the dataset.

        Returns:
            List of View objects.
        """
        from mammoth.view import View

        response = self._client.dataviews.list(dataset_id=dataset_id)
        views = []
        for dv in response.get("dataviews", []):
            views.append(View(self._client, dv, dataset_id))
        return views

    def create(
        self,
        dataset_id: int,
        name: str = "View",
        clone_from: int | None = None,
    ) -> View:
        """Create a new dataview and return as View object.

        Args:
            dataset_id: ID of the dataset.
            name: Name for the new dataview (default "View").
            clone_from: ID of dataview to clone config from (optional).

        Returns:
            View object for the newly created dataview.
        """
        from mammoth.view import View

        data = self._client.dataviews.create(
            dataset_id=dataset_id,
            name=name,
            clone_config_from=clone_from,
        )
        view_id = data.get("dataview_id") or data.get("id")
        if view_id:
            full_data = self._client.dataviews.get(
                dataset_id=dataset_id,
                dataview_id=view_id,
            )
            return View(self._client, full_data, dataset_id)
        return View(self._client, data, dataset_id)

    def delete(self, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """Delete a dataview.

        Args:
            view_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Dict with deletion result.
        """
        if dataset_id is None:
            dataset_id = self._client.pipeline._find_dataset_for_dataview(view_id)
        return self._client.dataviews.delete(dataset_id=dataset_id, dataview_id=view_id)

    def bulk_delete(self, dataset_id: int, view_ids: _list[int]) -> dict[str, Any]:
        """Delete multiple dataviews.

        Args:
            dataset_id: ID of the dataset.
            view_ids: List of dataview IDs to delete.

        Returns:
            Dict with bulk deletion result.
        """
        return self._client.dataviews.bulk_delete(dataset_id=dataset_id, dataview_ids=view_ids)


class MammothClient:
    """Main client for interacting with the Mammoth Analytics API.

    Provides access to all API endpoints through organized sub-clients.

    Example::

        client = MammothClient(
            api_key="your-api-key",
            api_secret="your-api-secret",
            workspace_id=11,
        )
        client.set_project_id(10)

        # Resource-based CRUD
        projects = client.projects.list()
        datasets = client.datasets.list()

        # Rich View objects with transformations
        view = client.views.get(1039)
        view.filter_rows(Condition("Sales", Operator.GTE, 1000))
        view.export.to_csv("output.csv")
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        workspace_id: int,
        base_url: str = "https://app.mammoth.io/api/v2",
        timeout: int = DEFAULT_TIMEOUT,
        job_timeout: int = DEFAULT_JOB_TIMEOUT,
    ) -> None:
        """Initialize the Mammoth client.

        Args:
            api_key: Your Mammoth API key.
            api_secret: Your Mammoth API secret.
            workspace_id: Your Mammoth workspace ID.
            base_url: Base URL for the Mammoth API.
            timeout: Request timeout in seconds.
            job_timeout: Job polling timeout in seconds.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.workspace_id = workspace_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.job_timeout = job_timeout

        self.project_id: int | None = None

        if not self.base_url.endswith("/api/v2"):
            self.base_url = urljoin(self.base_url, "/api/v2")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-KEY": self.api_key,
                "X-API-SECRET": self.api_secret,
                "X-WORKSPACE-ID": str(self.workspace_id),
                "User-Agent": f"mammoth-io/{_get_version()}",
            }
        )

        # ── Sub-clients ──
        self.files = FilesAPI(self)
        self.jobs = JobsAPI(self)
        self.exports = ExportsAPI(self)
        self.workspaces = WorkspaceAPI(self)
        self.client_apps = ClientAppsAPI(self)
        self.projects = ProjectsAPI(self)
        self.folders = FoldersAPI(self)
        self.datasets = DatasetsAPI(self)
        self.dataviews = DataviewsAPI(self)
        self.pipeline = PipelineAPI(self)
        self.views = ViewsResource(self)
        self.connectors = ConnectorsAPI(self)
        self.dashboards = DashboardsAPI(self)
        self.webhooks = WebhooksAPI(self)
        self.automations = AutomationsAPI(self)
        self.ai = AIAPI(self)
        self.schedules = SchedulesAPI(self)
        self.batches = BatchesAPI(self)
        self.external_keys = ExternalKeysAPI(self)
        self.activity_logs = ActivityLogsAPI(self)
        self.browse = BrowseAPI(self)
        self.user_profile = UserProfileAPI(self)
        self.addons = AddonsAPI(self)
        self.reports = ReportsAPI(self)

    def find_dataset_for_dataview(self, dataview_id: int) -> int:
        """Find the dataset ID for a given dataview.

        Searches all datasets in the current project to find
        which dataset contains the specified dataview.

        Args:
            dataview_id: ID of the dataview.

        Returns:
            Dataset ID that contains the dataview.

        Raises:
            MammothAPIError: If the dataview cannot be found.
        """
        return self.pipeline._find_dataset_for_dataview(dataview_id)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: list[Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make an authenticated request to the Mammoth API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint (without base URL).
            params: Query parameters.
            json: JSON body for the request.
            files: Files for multipart upload.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Parsed JSON response.

        Raises:
            MammothAuthError: If authentication fails.
            MammothAPIError: If the API returns an error or network fails.
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        request_kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            **kwargs,
        }

        if params:
            request_kwargs["params"] = params

        headers = dict(self.session.headers)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        if files:
            request_kwargs["files"] = files
            request_kwargs["headers"] = headers
        elif json:
            headers["Content-Type"] = "application/json"
            request_kwargs["headers"] = headers
            request_kwargs["json"] = json
        else:
            request_kwargs["headers"] = headers

        try:
            response = self.session.request(method, url, **request_kwargs)
        except requests.exceptions.Timeout as e:
            raise MammothAPIError(f"Request timeout: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise MammothAPIError(f"Connection error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise MammothAPIError(f"Request error: {e}") from e

        if response.status_code == 401:
            raise MammothAuthError("Invalid API credentials")

        if 200 <= response.status_code < 300:
            if response.status_code == 204 or not response.content:
                return {}
            try:
                return response.json()
            except ValueError as e:
                raise MammothAPIError(
                    f"Invalid JSON response: {e}",
                    status_code=response.status_code,
                    response_body={"raw": response.text},
                ) from e

        error_detail = "Unknown error"
        response_data: dict[str, Any] = {}
        try:
            response_data = response.json()
            if isinstance(response_data, dict):
                error_detail = response_data.get("detail", f"HTTP {response.status_code}")
            else:
                error_detail = f"HTTP {response.status_code}"
        except ValueError:
            error_detail = f"HTTP {response.status_code}: {response.text[:200]}"

        raise MammothAPIError(
            f"API request failed: {error_detail}",
            status_code=response.status_code,
            response_body=response_data,
        )

    def _request_json(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: list[Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request expecting a dict response."""
        result = self._request(method, endpoint, params=params, json=json, files=files, **kwargs)
        if isinstance(result, list):
            raise MammothAPIError("Expected dict response from API, got list")
        return result

    def _request_list(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Make an authenticated request expecting a list response."""
        result = self._request(method, endpoint, params=params, json=json, **kwargs)
        if isinstance(result, dict):
            return [result]
        return result

    def set_project_id(self, project_id: int) -> None:
        """Set the default project ID for the client.

        Args:
            project_id: ID of the project to use as default.
        """
        self.project_id = project_id

    def test_connection(self) -> bool:
        """Test the connection to Mammoth API.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            self._request("GET", "/jobs", params={"job_ids": ""})
            return True
        except MammothAuthError:
            return False
        except MammothAPIError as e:
            return e.status_code == 400
        except Exception:
            return False

    # ── Top-level Convenience Methods ──────────────────────────

    def get_view(self, view_id: int, dataset_id: int | None = None) -> View:
        """Get a rich View object by dataview ID.

        Shortcut for ``client.views.get(view_id)``.

        Args:
            view_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            View object with transformation methods and metadata.
        """
        return self.views.get(view_id, dataset_id)

    def branch_out(
        self,
        view_id: int,
        dest_dataset_id: int,
        column_mapping: dict[str, str] | None = None,
        dataset_id: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Branch out a view to another dataset.

        Args:
            view_id: Source dataview ID.
            dest_dataset_id: Target dataset ID.
            column_mapping: Column mapping dict (optional).
            dataset_id: Source dataset ID (auto-detected if not provided).
            **kwargs: Additional export options.

        Returns:
            Export result dict.
        """
        view = self.views.get(view_id, dataset_id)
        return view.branch_out(dest_dataset_id, column_mapping, **kwargs)

    def __enter__(self) -> MammothClient:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        if self.session:
            self.session.close()


# Type alias for forward references
from mammoth.view import View as View  # noqa: E402
