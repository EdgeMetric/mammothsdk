"""
Main client for the Mammoth Analytics SDK.
"""

import requests
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin

from .api.exports import ExportsAPI

from .exceptions import MammothAPIError, MammothAuthError
from .api.files import FilesAPI
from .api.jobs import JobsAPI
from .api.workspace import WorkspaceAPI
from .api.clientapps import ClientAppsAPI
from .api.projects import ProjectsAPI
from .api.folders import FoldersAPI
from .api.datasets import DatasetsAPI
from .api.dataviews import DataviewsAPI


class MammothClient:
    """
    Main client for interacting with the Mammoth Analytics API.
    
    This client provides access to all Mammoth API endpoints through
    organized sub-clients (files, jobs, etc.).
    
    Example:
        client = MammothClient(
            api_key="your-api-key",
            api_secret="your-api-secret",
            workspace_id=11,
            base_url="https://your-mammoth-instance.com/api/v2"
        )
        
        # Upload a file
        dataset_id = client.files.upload_files(
            project_id=1,
            files="data.csv"
        )
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        workspace_id: int,
        base_url: str = "https://app.mammoth.io/api/v2",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the Mammoth client.
        
        Args:
            api_key: Your Mammoth API key
            api_secret: Your Mammoth API secret
            workspace_id: Your Mammoth workspace ID
            base_url: Base URL for the Mammoth API (default: https://app.mammoth.io/api/v2)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
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
            'User-Agent': 'mammoth-python-sdk/0.1.0'
        })
        
        # Initialize API clients
        self.files = FilesAPI(self)
        self.jobs = JobsAPI(self)
        self.exports = ExportsAPI(self)
        self.workspaces = WorkspaceAPI(self)
        self.client_apps = ClientAppsAPI(self)
        self.projects = ProjectsAPI(self)
        self.folders = FoldersAPI(self)
        self.datasets = DatasetsAPI(self)
        self.dataviews = DataviewsAPI(self)
        
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[List] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make an authenticated request to the Mammoth API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json: JSON body for the request
            files: Files for multipart upload
            **kwargs: Additional arguments passed to requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            MammothAuthError: If authentication fails
            MammothAPIError: If the API returns an error
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        # Prepare request arguments
        request_kwargs = {
            'timeout': self.timeout,
            **kwargs
        }
        
        if params:
            request_kwargs['params'] = params
        
        # Handle headers
        headers = self.session.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        if files:
            # Remove Content-Type header for multipart requests
            request_kwargs['files'] = files
            request_kwargs['headers'] = headers
        elif json:
            headers['Content-Type'] = 'application/json'
            request_kwargs['headers'] = headers
            request_kwargs['json'] = json
        else:
            request_kwargs['headers'] = headers
        
        # Make request with retries
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, **request_kwargs)
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise MammothAuthError("Invalid API credentials")
                
                # Handle successful responses (200-299)
                if 200 <= response.status_code < 300:
                    # Handle empty responses (like DELETE operations)
                    if response.status_code == 204 or not response.content:
                        return {}
                    
                    try:
                        return response.json()
                    except ValueError as e:
                        raise MammothAPIError(
                            f"Invalid JSON response: {str(e)}",
                            status_code=response.status_code,
                            response_body=response.text
                        )
                
                # Handle client and server errors
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
                    response_body=response_data
                )
                
            except requests.exceptions.Timeout as e:
                last_exception = MammothAPIError(f"Request timeout: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                last_exception = MammothAPIError(f"Connection error: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_exception = MammothAPIError(f"Request error: {str(e)}")
            except MammothAPIError:
                # Re-raise API errors immediately
                raise
            
            # If this isn't the last attempt, wait before retrying
            if attempt < self.max_retries:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # If all retries failed, raise the last exception
        raise last_exception
    
    def set_project_id(self, project_id: int) -> None:
        """
        Set the default project ID for the client.
        
        Args:
            project_id: ID of the project to use as default
        """
        self.project_id = project_id
    
    def test_connection(self) -> bool:
        """
        Test the connection to Mammoth API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Use a simple endpoint to test connectivity
            # Since we don't have a dedicated health endpoint, we'll use jobs with invalid params
            # This should return a 400 error but confirm we can connect and authenticate
            headers = {"x-workspace-id": str(self.workspace_id)}
            self._request("GET", "/jobs", params={"job_ids": ""}, headers=headers)
            return True
        except MammothAuthError:
            return False
        except MammothAPIError as e:
            # If we get a 400 error, it means we connected successfully but sent bad params
            # This confirms our authentication works
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
