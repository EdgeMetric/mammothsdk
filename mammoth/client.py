"""
Main client for the Mammoth Analytics SDK.
"""

import requests
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin

from .exceptions import MammothAPIError, MammothAuthError
from .api.files import FilesAPI
from .api.jobs import JobsAPI
from .api.exports import ExportsAPI
from .api.workspace import WorkspaceAPI
from .api.clientapps import ClientAppsAPI
from .api.projects import ProjectsAPI
from .api.folders import FoldersAPI
from .api.datasets import DatasetsAPI
from .api.dataviews import DataviewsAPI
from .api.pipeline import PipelineAPI
from .api.connectors import ConnectorsAPI
from .api.dashboards import DashboardsAPI
from .api.webhooks import WebhooksAPI
from .api.automations import AutomationsAPI
from .api.ai import AIAPI


class ViewsResource:
    """Resource that returns rich View objects.

    Access via client.views:
        view = client.views.get(view_id)           # returns View object
        views = client.views.list(dataset_id)       # returns list of View objects
        view = client.views.create(dataset_id)      # returns View object
    """

    def __init__(self, client):
        self._client = client

    def get(self, view_id: int, dataset_id: Optional[int] = None) -> "View":
        """Get a rich View object for a dataview.

        Args:
            view_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            View object with transformation methods and metadata.

        Example:
            view = client.views.get(1039)
            print(view.display_names)  # ["Sales", "Region", ...]
            view.filter_rows(Condition("Sales", Operator.GTE, 1000))
        """
        from .view import View

        if dataset_id is None:
            dataset_id = self._client.pipeline._find_dataset_for_dataview(view_id)

        data = self._client.dataviews.get(
            dataset_id=dataset_id,
            dataview_id=view_id,
        )
        return View(self._client, data, dataset_id)

    def list(self, dataset_id: int) -> "List[View]":
        """List all dataviews in a dataset as View objects.

        Args:
            dataset_id: ID of the dataset.

        Returns:
            List of View objects.
        """
        from .view import View

        response = self._client.dataviews.list(dataset_id=dataset_id)
        views = []
        for dv in response.get("dataviews", []):
            views.append(View(self._client, dv, dataset_id))
        return views

    def create(
        self,
        dataset_id: int,
        name: str = "View",
        clone_from: Optional[int] = None,
    ) -> "View":
        """Create a new dataview and return as View object.

        Args:
            dataset_id: ID of the dataset.
            name: Name for the new dataview (default "View").
            clone_from: ID of dataview to clone config from (optional).

        Returns:
            View object for the newly created dataview.
        """
        from .view import View

        data = self._client.dataviews.create(
            dataset_id=dataset_id,
            name=name,
            clone_config_from=clone_from,
        )
        return View(self._client, data, dataset_id)

    def delete(self, view_id: int, dataset_id: Optional[int] = None) -> dict:
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

    def bulk_delete(self, dataset_id: int, view_ids: List[int]) -> dict:
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

    Example:
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

        # Connectors, dashboards, AI, etc.
        client.connectors.list()
        client.dashboards.list()
        client.ai.generate_profile(dataview_id=1039)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        workspace_id: int,
        base_url: str = "https://app.mammoth.io/api/v2",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize the Mammoth client.

        Args:
            api_key: Your Mammoth API key.
            api_secret: Your Mammoth API secret.
            workspace_id: Your Mammoth workspace ID.
            base_url: Base URL for the Mammoth API (default: https://app.mammoth.io/api/v2).
            timeout: Request timeout in seconds (default 30).
            max_retries: Maximum retries for failed requests (default 3).
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.workspace_id = workspace_id
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries

        # Optional project_id that can be set for convenience
        self.project_id = None

        # Ensure base URL includes API version path
        if not self.base_url.endswith('/api/v2'):
            self.base_url = urljoin(self.base_url, '/api/v2')

        # Initialize session with authentication headers
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': self.api_key,
            'X-API-SECRET': self.api_secret,
            'User-Agent': 'mammoth-python-sdk/0.1.0',
        })

        # ── Existing sub-clients ──
        self.files = FilesAPI(self)
        self.jobs = JobsAPI(self)
        self.exports = ExportsAPI(self)
        self.workspaces = WorkspaceAPI(self)
        self.client_apps = ClientAppsAPI(self)
        self.projects = ProjectsAPI(self)
        self.folders = FoldersAPI(self)
        self.datasets = DatasetsAPI(self)
        self.dataviews = DataviewsAPI(self)

        # ── New sub-clients ──
        self.pipeline = PipelineAPI(self)
        self.views = ViewsResource(self)
        self.connectors = ConnectorsAPI(self)
        self.dashboards = DashboardsAPI(self)
        self.webhooks = WebhooksAPI(self)
        self.automations = AutomationsAPI(self)
        self.ai = AIAPI(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[List] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
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
            MammothAPIError: If the API returns an error.
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

        request_kwargs = {
            'timeout': self.timeout,
            **kwargs,
        }

        if params:
            request_kwargs['params'] = params

        headers = self.session.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        if files:
            request_kwargs['files'] = files
            request_kwargs['headers'] = headers
        elif json:
            headers['Content-Type'] = 'application/json'
            request_kwargs['headers'] = headers
            request_kwargs['json'] = json
        else:
            request_kwargs['headers'] = headers

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, **request_kwargs)

                if response.status_code == 401:
                    raise MammothAuthError("Invalid API credentials")

                if 200 <= response.status_code < 300:
                    if response.status_code == 204 or not response.content:
                        return {}
                    try:
                        return response.json()
                    except ValueError as e:
                        raise MammothAPIError(
                            f"Invalid JSON response: {str(e)}",
                            status_code=response.status_code,
                            response_body=response.text,
                        )

                error_detail = "Unknown error"
                response_data = {}
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        error_detail = response_data.get('detail', f"HTTP {response.status_code}")
                    else:
                        error_detail = f"HTTP {response.status_code}"
                except ValueError:
                    error_detail = f"HTTP {response.status_code}: {response.text[:200]}"

                raise MammothAPIError(
                    f"API request failed: {error_detail}",
                    status_code=response.status_code,
                    response_body=response_data,
                )

            except requests.exceptions.Timeout as e:
                last_exception = MammothAPIError(f"Request timeout: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                last_exception = MammothAPIError(f"Connection error: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_exception = MammothAPIError(f"Request error: {str(e)}")
            except MammothAPIError:
                raise

            if attempt < self.max_retries:
                import time
                time.sleep(2 ** attempt)

        raise last_exception

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
            headers = {"x-workspace-id": str(self.workspace_id)}
            self._request("GET", "/jobs", params={"job_ids": ""}, headers=headers)
            return True
        except MammothAuthError:
            return False
        except MammothAPIError as e:
            return e.status_code == 400
        except Exception:
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            self.session.close()
