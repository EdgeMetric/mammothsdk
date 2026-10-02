"""Main client for the Mammoth Analytics SDK.

Provides ``MammothClient`` — the single entry point for all API interactions.
All sub-clients (projects, datasets, views, pipeline, exports, connectors,
dashboards, webhooks, automations, ai) are accessible as attributes.

Example::

    from mammoth import MammothClient

    client = MammothClient(
        api_token="mm_...",
        base_url="https://app.mammoth.io/api/v2",
    )
    client.set_project_id(10)

    # List projects
    projects = await client.projects.list()

    # Get a rich View object and apply transformations
    view = await client.get_view(1039)
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import math
import time
from collections.abc import Awaitable, Callable
from ipaddress import ip_address
from typing import Any, cast
from urllib.parse import urljoin, urlsplit

import httpx

from mammoth.api.activity_logs import ActivityLogsAPI
from mammoth.api.addons import AddonsAPI
from mammoth.api.agents import AgentsAPI
from mammoth.api.ai import AIAPI
from mammoth.api.annotations import AnnotationsAPI
from mammoth.api.automations import AutomationsAPI
from mammoth.api.batches import BatchesAPI
from mammoth.api.billing import BillingAPI
from mammoth.api.browse import BrowseAPI
from mammoth.api.checkpoints import CheckpointsAPI
from mammoth.api.clientapps import ClientAppsAPI
from mammoth.api.connector_ai import ConnectorAIAPI
from mammoth.api.connectors import ConnectorsAPI
from mammoth.api.dashboards import DashboardsAPI
from mammoth.api.data_apps import DataAppsAPI
from mammoth.api.data_checks import DataChecksAPI
from mammoth.api.datasets import DatasetsAPI
from mammoth.api.dataviews import DataviewsAPI
from mammoth.api.derivatives import DerivativesAPI
from mammoth.api.exports import ExportsAPI
from mammoth.api.external_keys import ExternalKeysAPI
from mammoth.api.files import FilesAPI
from mammoth.api.folders import FoldersAPI
from mammoth.api.jobs import JobsAPI
from mammoth.api.notifications import NotificationsAPI
from mammoth.api.parameters import ParametersAPI
from mammoth.api.pipeline import PipelineAPI
from mammoth.api.pipeline_versions import PipelineVersionsAPI
from mammoth.api.projects import ProjectsAPI
from mammoth.api.reports import ReportsAPI
from mammoth.api.schedules import SchedulesAPI
from mammoth.api.snippets import SnippetsAPI
from mammoth.api.support import SupportAPI
from mammoth.api.templates import TemplatesAPI
from mammoth.api.trash import TrashAPI
from mammoth.api.user_profile import UserProfileAPI
from mammoth.api.users import UsersAPI
from mammoth.api.webhooks import WebhooksAPI
from mammoth.api.workflows import WorkflowsAPI
from mammoth.api.workspace import WorkspaceAPI
from mammoth.api.workspaces import WorkspacesAPI
from mammoth.exceptions import MammothAPIError, MammothAuthError, safe_response_body


# Lazy __version__ import to avoid circular dependency with __init__
def _get_version() -> str:
    try:
        from mammoth import __version__

        return __version__
    except ImportError:
        return "0.2.0"


def _is_loopback_host(hostname: str | None) -> bool:
    """Return whether a parsed host is an explicit local development target."""
    if hostname == "localhost":
        return True
    if hostname is None:
        return False
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


# ── Configurable defaults ─────────────────────────────────────
DEFAULT_TIMEOUT = 30  # seconds — max time for any single API call
DEFAULT_JOB_TIMEOUT = 60  # seconds — max time to poll a job to completion
# seconds between polls of a running job. Two suits a script that started a long
# build; a caller answering a person wants a fraction of it.
DEFAULT_JOB_POLL_SECONDS = 2
DEFAULT_PIPELINE_TIMEOUT = 3600  # seconds — max time to wait for pipeline readiness

_list = list  # Alias to avoid shadowing by method name


#: Transport log. Silent unless a handler is attached (the CLI attaches one
#: per invocation). Records carry a ``mammoth`` dict in ``extra``: method,
#: path, status, duration_ms, request_id, outcome. Never headers or bodies.
_HTTP_LOG = logging.getLogger("mammoth.http")


def _log_http(
    method: str,
    endpoint: str,
    *,
    started: float,
    status: int | None,
    request_id: str | None = None,
    outcome: str,
    attempt: int | None = None,
    error: str | None = None,
) -> None:
    if not _HTTP_LOG.isEnabledFor(logging.INFO):
        return
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    tried = f" attempt={attempt}/{_MAX_READ_RETRIES + 1}" if attempt else ""
    failed = f" error={error}" if error else ""
    _HTTP_LOG.info(
        "http %s %s%s outcome=%s status=%s%s elapsed_ms=%s",
        method,
        endpoint.split("?", 1)[0],
        tried,
        outcome,
        status,
        failed,
        elapsed_ms,
        extra={
            "mammoth": {
                "event": "http",
                "method": method,
                "path": endpoint,
                "status": status,
                "duration_ms": elapsed_ms,
                "request_id": request_id,
                "outcome": outcome,
            }
        },
    )


def _log_attempt_start(method: str, endpoint: str, attempt: int, timeout: Any) -> None:
    """One line when a request attempt starts, so a hang shows which attempt never ended."""
    if _HTTP_LOG.isEnabledFor(logging.INFO):
        _HTTP_LOG.info(
            "http %s %s attempt=%s/%s start timeout=%s",
            method,
            endpoint.split("?", 1)[0],
            attempt,
            _MAX_READ_RETRIES + 1,
            timeout,
        )


_RETRY_STATUSES = frozenset({502, 503, 504})
_RETRY_METHODS = frozenset({"GET", "HEAD"})
_MAX_READ_RETRIES = 2
_RETRY_BACKOFF_S = 0.25
_RETRY_AFTER_CAP_S = 5.0


def _retry_delay(attempt: int, retry_after: str | None) -> float:
    """Backoff before retry ``attempt`` (0-based); honours a numeric Retry-After, capped."""
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), _RETRY_AFTER_CAP_S)
        except ValueError:
            pass
    return min(_RETRY_BACKOFF_S * 2**attempt, _RETRY_AFTER_CAP_S)


class ViewsResource:
    """Resource that returns rich View objects.

    Access via client.views::

        view = await client.views.get(view_id)           # returns View object
        views = await client.views.list()                 # returns list of View objects
        view = await client.views.create(dataset_id)      # returns View object
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    async def get(self, view_id: int, dataset_id: int | None = None) -> View:
        """Get a rich View object for a dataview.

        Args:
            view_id: ID of the dataview.
            dataset_id: Known parent dataset ID. When supplied, the SDK uses
                that exact parent and does not probe other datasets.

        Returns:
            View object with transformation methods and metadata.
        """
        from mammoth.view import View

        if dataset_id is None:
            dataset_id = await self._client.pipeline.find_dataset_for_dataview(view_id)

        data = await self._client.dataviews.get(
            dataset_id=dataset_id,
            dataview_id=view_id,
        )
        return View(self._client, data, dataset_id)

    async def list(self, dataset_id: int) -> _list[View]:
        """List all dataviews in a dataset as View objects.

        Args:
            dataset_id: ID of the dataset to list views from.

        Returns:
            List of View objects.
        """
        from mammoth.view import View

        dv_resp = await self._client.dataviews.list(dataset_id=dataset_id)
        views: _list[View] = []
        for dv in dv_resp.get("dataviews", []):
            views.append(View(self._client, dv, dataset_id))
        return views

    async def create(
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

        data = await self._client.dataviews.create(
            dataset_id=dataset_id,
            name=name,
            clone_config_from=clone_from,
        )
        view_id = data.get("dataview_id") or data.get("id")
        if view_id:
            full_data = await self._client.dataviews.get(
                dataset_id=dataset_id,
                dataview_id=view_id,
            )
            return View(self._client, full_data, dataset_id)
        return View(self._client, data, dataset_id)

    async def delete(self, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """Delete a dataview.

        Args:
            view_id: ID of the dataview.
            dataset_id: Known parent dataset ID. When supplied, deletion is
                sent directly to that nested endpoint and parent discovery is
                skipped; API errors (including 403) are preserved.

        Returns:
            Dict with deletion result.
        """
        if dataset_id is None:
            dataset_id = await self._client.pipeline.find_dataset_for_dataview(view_id)
        return await self._client.dataviews.delete(dataset_id=dataset_id, dataview_id=view_id)

    async def bulk_delete(
        self, view_ids: _list[int], dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Delete multiple dataviews.

        Args:
            view_ids: List of dataview IDs to delete.

        Returns:
            Dict with bulk deletion result.
        """
        if not view_ids:
            raise ValueError("view_ids must contain at least one dataview ID")
        if dataset_id is None:
            dataset_id = await self._client.pipeline.find_dataset_for_dataview(view_ids[0])
        return await self._client.dataviews.bulk_delete(
            dataset_id=dataset_id, dataview_ids=view_ids
        )


#: Artifact media types returned as text rather than base64.
_TEXT_ARTIFACT_TYPES = frozenset(
    {"text/html", "text/plain", "text/csv", "application/xml", "text/xml"}
)


def _read_error_detail(body: dict[str, Any]) -> str | None:
    """The sentence a server sent with a refusal, whichever field carries it.

    Mammoth puts it in `message`, and on a 404 sends `detail: null` beside it —
    a key that is present and empty, so reading `detail` with `message` as a
    fallback found the null and stopped there. On a business error `detail` is
    an object instead of a sentence. Either way the reason was lost and the
    caller was handed a bare status code, which nobody can act on.

    Args:
        body: The parsed response body of a failed request.

    Returns:
        The first sentence found, or None when the body carries none.
    """
    for value in (body.get("message"), body.get("detail")):
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            nested = value.get("message") or value.get("detail")
            if isinstance(nested, str) and nested.strip():
                return nested
    return None


_TOKEN_WORKSPACES: dict[tuple[str, str], int] = {}


def resolve_token_workspace_id(base_url: str, api_token: str, timeout: float) -> int:
    """Ask the server which workspace an ``mm_`` token belongs to.

    The answer is cached per (server, token) for the life of the process.

    Args:
        base_url: The API base url, ending in ``/api/v2``.
        api_token: The ``mm_...`` Bearer token.
        timeout: Request timeout in seconds.

    Raises:
        MammothAuthError: The server rejected the token.
        MammothAPIError: The request failed or the answer carried no workspace id.
    """
    key = (base_url, api_token)
    if key not in _TOKEN_WORKSPACES:
        try:
            response = httpx.get(
                f"{base_url}/workspaces/current",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=timeout,
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise MammothAPIError(
                "Could not reach Mammoth to resolve the token's workspace"
            ) from exc
        if response.status_code == 401:
            raise MammothAuthError("Invalid API credentials")
        workspace_id = response.json().get("id") if response.status_code == 200 else None
        if not isinstance(workspace_id, int) or workspace_id <= 0:
            raise MammothAPIError(
                "Mammoth did not return the token's workspace", status_code=response.status_code
            )
        _TOKEN_WORKSPACES[key] = workspace_id
    return _TOKEN_WORKSPACES[key]


class MammothClient:
    """Main client for interacting with the Mammoth Analytics API.

    Provides access to all API endpoints through organized sub-clients.

    Example::

        client = MammothClient(api_token="mm_...")
        client.set_project_id(10)

        # Resource-based CRUD
        projects = await client.projects.list()
        datasets = await client.datasets.list()

        # Rich View objects with transformations
        view = await client.views.get(1039)
        await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
        await view.export.to_csv("output.csv")
    """

    workspace_id: int

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        workspace_id: int | None = None,
        base_url: str = "https://app.mammoth.io/api/v2",
        timeout: float = DEFAULT_TIMEOUT,
        job_timeout: float = DEFAULT_JOB_TIMEOUT,
        job_poll_seconds: float = DEFAULT_JOB_POLL_SECONDS,
        pipeline_timeout: float = DEFAULT_PIPELINE_TIMEOUT,
        allow_insecure_loopback_http: bool = False,
        *,
        api_token: str | None = None,
        api_root: str | None = "/api/v2",
    ) -> None:
        """Initialize the Mammoth client.

        Pass either ``api_token`` (the ``mm_...`` token from Workspace settings
        -> API Tokens, sent as ``Authorization: Bearer``) or the deprecated
        ``api_key`` + ``api_secret`` pair, never both.

        Args:
            api_key: Deprecated API key; use ``api_token``.
            api_secret: Deprecated API secret; use ``api_token``.
            workspace_id: Your Mammoth workspace ID. Only for the deprecated
                ``api_key`` + ``api_secret`` pair; an ``api_token`` names its
                own workspace and rejects this argument.
            base_url: Base URL for the Mammoth API.
            timeout: Request timeout in seconds.
            job_timeout: Job polling timeout in seconds.
            job_poll_seconds: How long to wait between polls of a running
                job. Lower it when a person is waiting on the answer.
            pipeline_timeout: Pipeline readiness polling timeout in seconds.
            allow_insecure_loopback_http: Permit HTTP only for an explicit
                loopback development endpoint. Production API credentials must
                use HTTPS.
            api_token: Your Mammoth API token (``mm_...``).
            api_root: The path the API is served under, appended to
                ``base_url`` when it is not already there. ``None`` takes
                ``base_url`` exactly as given, which is what a caller inside
                the network needs: the server mounts these routes at their own
                paths, and whatever sits in front of it adds the prefix.
        """
        if api_token is not None and (api_key is not None or api_secret is not None):
            raise ValueError("pass api_token or api_key + api_secret, not both")
        if api_token is None and (not api_key or not api_secret):
            raise ValueError("pass api_token (mm_...) or both api_key and api_secret")
        if api_token is not None and (not isinstance(api_token, str) or not api_token.strip()):
            raise ValueError("api_token must be a non-empty string")
        if api_token is not None and workspace_id is not None:
            raise ValueError("workspace_id is not accepted with api_token: the token names it")
        if api_token is None and workspace_id is None:
            raise ValueError("workspace_id is required")
        if not isinstance(base_url, str):
            raise ValueError("base_url must be an HTTPS URL")
        self.base_url = base_url.rstrip("/")
        supplied_base_url = urlsplit(self.base_url)
        has_unsafe_url_components = any(
            (
                supplied_base_url.username,
                supplied_base_url.password,
                supplied_base_url.query,
                supplied_base_url.fragment,
            )
        )
        if api_root is not None and not self.base_url.endswith(api_root):
            self.base_url = urljoin(self.base_url, api_root)
        parsed_base_url = urlsplit(self.base_url)
        valid_base_url = not has_unsafe_url_components and (
            parsed_base_url.scheme == "https"
            and parsed_base_url.hostname is not None
            or (
                parsed_base_url.scheme == "http"
                and allow_insecure_loopback_http is True
                and _is_loopback_host(parsed_base_url.hostname)
            )
        )
        if not valid_base_url:
            raise ValueError(
                "base_url must use HTTPS; HTTP is permitted only for an explicit "
                "loopback development endpoint"
            )

        self.api_token = api_token.strip() if api_token is not None else None
        self.api_key = api_key
        self.api_secret = api_secret
        if workspace_id is not None:
            self.workspace_id = workspace_id
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout must be a positive finite number")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        for name, value in (
            ("job_timeout", job_timeout),
            ("job_poll_seconds", job_poll_seconds),
            ("pipeline_timeout", pipeline_timeout),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a positive finite number")
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        self.timeout = timeout
        self.job_timeout = job_timeout
        self.job_poll_seconds = job_poll_seconds
        self.pipeline_timeout = pipeline_timeout

        self.project_id: int | None = None

        self.session = httpx.AsyncClient(timeout=self.timeout, follow_redirects=False)
        if self.api_token is not None:
            credential_headers = {"Authorization": f"Bearer {self.api_token}"}
        else:
            credential_headers = {
                "X-API-KEY": str(self.api_key),
                "X-API-SECRET": str(self.api_secret),
                "X-WORKSPACE-ID": str(workspace_id),
            }
        self.session.headers.update(
            {
                **credential_headers,
                "User-Agent": f"mammoth-io/{_get_version()}",
            }
        )
        # Signed export URLs are commonly served from a storage origin rather
        # than the API origin.  Keep that traffic on a separate session so API
        # credentials are never attached to a signed URL (or its redirects).
        self.download_session = httpx.AsyncClient(timeout=self.timeout)

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
        self.agents = AgentsAPI(self)
        self.annotations = AnnotationsAPI(self)
        self.billing = BillingAPI(self)
        self.checkpoints = CheckpointsAPI(self)
        self.connector_ai = ConnectorAIAPI(self)
        self.data_apps = DataAppsAPI(self)
        self.data_checks = DataChecksAPI(self)
        self.derivatives = DerivativesAPI(self)
        self.notifications = NotificationsAPI(self)
        self.parameters = ParametersAPI(self)
        self.pipeline_versions = PipelineVersionsAPI(self)
        self.snippets = SnippetsAPI(self)
        self.support = SupportAPI(self)
        self.templates = TemplatesAPI(self)
        self.trash = TrashAPI(self)
        self.users = UsersAPI(self)
        self.workflows = WorkflowsAPI(self)
        # ``workspaces`` (WorkspaceAPI) is the current-workspace CRUD seam kept
        # for backward compatibility; ``workspace`` (WorkspacesAPI) exposes the
        # workspace-collection, membership, invite, usage, and AI operations.
        self.workspace = WorkspacesAPI(self)

    async def find_dataset_for_dataview(
        self, dataview_id: int, dataset_id: int | None = None
    ) -> int:
        """Find the parent dataset ID for a given dataview.

        Searches all datasets in the current project to locate which
        dataset contains the specified dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Known parent dataset ID. When supplied, no unrelated
                dataset is probed.

        Returns:
            Dataset ID that contains the dataview.

        Raises:
            MammothAPIError: If the dataview cannot be found in any dataset.

        Example::

            dataset_id = await client.find_dataset_for_dataview(1039)
        """
        if dataset_id is None:
            return await self.pipeline.find_dataset_for_dataview(dataview_id)
        return await self.pipeline.find_dataset_for_dataview(dataview_id, dataset_id)

    async def _send_with_read_retry(
        self, method: str, endpoint: str, url: str, request_kwargs: dict[str, Any]
    ) -> httpx.Response:
        """Send once; retry only GET/HEAD on 502/503/504 or connect errors, at most twice.

        A draining worker answers a read with one transient gateway error.
        Writes are never replayed. When retries run out the last response (or
        connect error) is returned/raised for the normal error mapping.
        """
        retryable = method in _RETRY_METHODS
        for attempt in range(_MAX_READ_RETRIES + 1):
            started = time.perf_counter()
            last = attempt == _MAX_READ_RETRIES or not retryable
            _log_attempt_start(method, endpoint, attempt + 1, request_kwargs.get("timeout"))
            try:
                response = await self.session.request(method, url, **request_kwargs)
            except httpx.ConnectError as e:
                if last:
                    raise
                _log_http(
                    method,
                    endpoint,
                    started=started,
                    status=None,
                    outcome="retry",
                    attempt=attempt + 1,
                    error=type(e).__name__,
                )
                await asyncio.sleep(_retry_delay(attempt, None))
                continue
            if last or response.status_code not in _RETRY_STATUSES:
                return response
            _log_http(
                method,
                endpoint,
                started=started,
                status=response.status_code,
                outcome="retry",
                attempt=attempt + 1,
            )
            await asyncio.sleep(_retry_delay(attempt, response.headers.get("Retry-After")))
        raise AssertionError("unreachable")

    def __getattr__(self, name: str) -> Any:
        """Learn ``workspace_id`` from the server on first use, for an ``api_token``.

        Given at construction with ``api_key`` + ``api_secret``; an ``api_token``
        names its own workspace, so the attribute is absent until read and is
        then fetched once and kept.
        """
        token = self.__dict__.get("api_token")
        if name == "workspace_id" and token is not None:
            self.workspace_id = resolve_token_workspace_id(self.base_url, token, self.timeout)
            return self.workspace_id
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: list[Any] | None = None,
        operation_effect: str | None = None,
        expected_response_shape: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make an authenticated request to the Mammoth API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint (without base URL).
            params: Query parameters.
            json: JSON body for the request.
            files: Files for multipart upload.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            Parsed JSON response.

        Raises:
            MammothAuthError: If authentication fails.
            MammothAPIError: If the API returns an error or network fails.
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        api_origin = urlsplit(self.base_url)
        request_origin = urlsplit(url)
        if (
            request_origin.scheme.lower(),
            request_origin.netloc.lower(),
        ) != (
            api_origin.scheme.lower(),
            api_origin.netloc.lower(),
        ):
            raise ValueError("Authenticated API requests must target the configured API origin")

        if kwargs.pop("allow_redirects", False):
            raise ValueError("Authenticated API requests do not support redirects")

        request_kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            # httpx otherwise follows redirects and preserves these
            # custom session headers across origins.  API credentials must
            # never leave the authenticated API request's original URL.
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

        request_method = method.upper()
        if operation_effect not in {None, "read", "mutation"}:
            raise ValueError("operation_effect must be 'read', 'mutation', or None")
        is_mutation = operation_effect == "mutation" or (
            operation_effect is None and request_method not in {"GET", "HEAD", "OPTIONS"}
        )
        operation_state = "outcome_unknown" if is_mutation else "not_started"

        started = time.perf_counter()
        try:
            response = await self._send_with_read_retry(
                request_method, endpoint, url, request_kwargs
            )
        except httpx.TimeoutException as e:
            _log_http(
                request_method,
                endpoint,
                started=started,
                status=None,
                outcome="timeout",
                error=type(e).__name__,
            )
            raise MammothAPIError(
                "Request timed out",
                details={"exception_type": type(e).__name__},
                method=request_method,
                operation_state=operation_state,
                phase="request",
                endpoint=endpoint,
            ) from e
        except httpx.ConnectError as e:
            _log_http(
                request_method,
                endpoint,
                started=started,
                status=None,
                outcome="connection_error",
                error=type(e).__name__,
            )
            raise MammothAPIError(
                "Connection error",
                details={"exception_type": type(e).__name__},
                method=request_method,
                operation_state=operation_state,
                phase="request",
                endpoint=endpoint,
            ) from e
        except httpx.HTTPError as e:
            _log_http(
                request_method,
                endpoint,
                started=started,
                status=None,
                outcome="request_failed",
                error=type(e).__name__,
            )
            raise MammothAPIError(
                "Request failed",
                details={"exception_type": type(e).__name__},
                method=request_method,
                operation_state=operation_state,
                phase="request",
                endpoint=endpoint,
            ) from e

        response_headers = getattr(response, "headers", {})

        def response_header(*names: str) -> str | None:
            for name in names:
                try:
                    value = response_headers.get(name)
                except AttributeError, TypeError:
                    value = None
                if value is not None:
                    return str(value)
            try:
                lowered = {str(key).lower(): value for key, value in response_headers.items()}
            except AttributeError, TypeError:
                lowered = {}
            for name in names:
                value = lowered.get(name.lower())
                if value is not None:
                    return str(value)
            return None

        request_id = response_header("X-Request-ID", "X-Correlation-ID", "Request-ID")
        retry_after = response_header("Retry-After")
        _log_http(
            request_method,
            endpoint,
            started=started,
            status=response.status_code,
            request_id=request_id,
            outcome="ok" if 200 <= response.status_code < 300 else "error",
        )

        body: dict[str, Any] = {}
        if not 200 <= response.status_code < 300:
            try:
                parsed_body = response.json()
                if isinstance(parsed_body, dict):
                    body = safe_response_body(parsed_body)
            except ValueError, TypeError:
                body = {}

        def observed_handles(data: dict[str, Any]) -> tuple[object | None, object | None]:
            job_handle: object | None = data.get("job_id")
            job = data.get("job")
            if job_handle is None and isinstance(job, dict):
                job_handle = job.get("id") or job.get("job_id")
            if job_handle is None and data.get("status") in {
                "processing",
                "success",
                "failure",
                "error",
            }:
                job_handle = data.get("id")
            resource_handle = data.get("resource_id") or data.get("dataset_id")
            resource = data.get("resource")
            if resource_handle is None and isinstance(resource, dict):
                resource_handle = resource.get("id") or resource.get("resource_id")
            return job_handle, resource_handle

        job_handle, resource_handle = observed_handles(body)
        observed_phase = body.get("phase") or body.get("execution_phase")
        phase = observed_phase if isinstance(observed_phase, str) else "response"
        error_details = {
            "response_body": body,
            "exception_type": None,
        }

        if response.status_code == 401:
            detail = "Invalid API credentials"
            candidate = body.get("message", body.get("detail"))
            if isinstance(candidate, str) and candidate:
                detail = candidate
            raise MammothAuthError(
                detail,
                response_body=body,
                details=error_details,
                method=request_method,
                request_id=request_id,
                retry_after=retry_after,
                operation_state="failed",
                phase=phase,
                job_handle=job_handle,
                resource_handle=resource_handle,
                endpoint=endpoint,
            )

        if 200 <= response.status_code < 300:
            if expected_response_shape == "binary":
                # Artifact routes (PNG, PDF, MP4, HTML) are not JSON. Describe
                # the body instead of parsing it, so callers get a stable dict.
                content = response.content or b""
                content_type = response.headers.get("Content-Type", "") or ""
                payload: dict[str, Any] = {
                    "content_type": content_type,
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
                if content_type.split(";", 1)[0].strip() in _TEXT_ARTIFACT_TYPES:
                    payload["text"] = response.text
                else:
                    payload["content_base64"] = base64.b64encode(content).decode("ascii")
                return payload
            if response.status_code == 204 or not response.content:
                if expected_response_shape == "list_or_dict":
                    return []
                return {}
            try:
                parsed_response = response.json()
            except (ValueError, TypeError) as e:
                raise MammothAPIError(
                    "Invalid JSON response",
                    status_code=response.status_code,
                    response_body={},
                    details={"exception_type": type(e).__name__},
                    method=request_method,
                    request_id=request_id,
                    retry_after=retry_after,
                    # A mutation may have committed before an intermediary
                    # truncated or corrupted its successful response.  Do not
                    # tell callers it failed and invite a duplicate write.
                    operation_state=operation_state,
                    phase=phase,
                    endpoint=endpoint,
                ) from e
            if expected_response_shape == "dict" and not isinstance(parsed_response, dict):
                # A 2xx is the server's confirmation. Several routes that
                # declare no response schema (202 "processing continues
                # off-line" deletes, PATCH /segments, DELETE file_settings)
                # answer with a scalar or null; a list is likewise data. Keep
                # the body and the status instead of reporting a committed
                # write as outcome_unknown.
                return {"status_code": response.status_code, "response": parsed_response}
            if expected_response_shape == "list_or_dict" and not isinstance(
                parsed_response, (list, dict)
            ):
                return {"status_code": response.status_code, "response": parsed_response}
            return parsed_response

        error_detail = _read_error_detail(body) or f"HTTP {response.status_code}"

        # A mutation is definitively not applied only when the server returns
        # an ordinary client-side rejection.  Redirects, timeouts/rate limits,
        # and server/gateway errors can all happen after a write is committed.
        # Preserve that uncertainty so callers reconcile instead of replaying.
        response_operation_state = operation_state
        if not is_mutation or (
            400 <= response.status_code < 500 and response.status_code not in {408, 425, 429}
        ):
            response_operation_state = "failed"

        raise MammothAPIError(
            f"API request failed: {error_detail}",
            status_code=response.status_code,
            response_body=body,
            details=error_details,
            method=request_method,
            request_id=request_id,
            retry_after=retry_after,
            operation_state=response_operation_state,
            phase=phase,
            job_handle=job_handle,
            resource_handle=resource_handle,
            endpoint=endpoint,
        )

    async def _request_json(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: list[Any] | None = None,
        operation_effect: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request expecting a dict response."""
        result = await self._request(
            method,
            endpoint,
            params=params,
            json=json,
            files=files,
            operation_effect=operation_effect,
            expected_response_shape="dict",
            **kwargs,
        )
        # ``expected_response_shape`` above rejects every non-dict successful
        # response before it reaches this typed wrapper.
        return cast(dict[str, Any], result)

    async def _request_binary(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request for a non-JSON artifact.

        Returns ``{"content_type", "size_bytes", "sha256"}`` plus ``"text"``
        for HTML/plain-text bodies or ``"content_base64"`` for binary ones.
        """
        result = await self._request(
            method, endpoint, params=params, expected_response_shape="binary", **kwargs
        )
        assert isinstance(result, dict)
        return result

    async def _request_list(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        operation_effect: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Make an authenticated request expecting a list response."""
        result = await self._request(
            method,
            endpoint,
            params=params,
            json=json,
            operation_effect=operation_effect,
            # Several established list endpoints legitimately return a single
            # object.  Preserve that SDK compatibility while still rejecting
            # scalar/null response-contract violations.
            expected_response_shape="list_or_dict",
            **kwargs,
        )
        if isinstance(result, dict):
            return [result]
        return result

    async def _wait_if_job(
        self,
        response: dict[str, Any],
        timeout: int | None = None,
        poll_interval: float | None = None,
        fetch: Callable[[int, float], Awaitable[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Detect job references in API responses and wait for completion.

        Handles three job response schemas:
        - ``{"job_id": N}`` (ObjectJobSchema)
        - ``{"job": {"id": N, ...}}`` (JobResponse)
        - ``{"id": N, "status": "processing|..."}`` (ResponseJobSchema)

        Args:
            response: Raw API response dict.
            timeout: Max wait time in seconds (default: client.job_timeout).
            poll_interval: Seconds between polls (default:
                ``client.job_poll_seconds``).

        Returns:
            Completed job's inner response data, or the original response
            if no job reference was detected.
        """
        if not isinstance(response, dict):
            return response

        job_id = None

        # Pattern 1: {"job_id": N}
        if "job_id" in response:
            job_id = response["job_id"]
        # Pattern 2: {"job": {"id": N}}
        elif isinstance(response.get("job"), dict):
            job_id = response["job"].get("id")
        # Pattern 3: {"id": N, "status": "processing|..."}
        elif "id" in response and response.get("status") in (
            "processing",
            "success",
            "failure",
            "error",
        ):
            job_id = response["id"]
        # Pattern 4: PipelineModificationResp — {"future_id": N, ...}
        elif "future_id" in response and response.get("future_id") is not None:
            job_id = response["future_id"]

        if job_id:
            t = timeout if timeout is not None else self.job_timeout
            every = poll_interval if poll_interval is not None else self.job_poll_seconds
            completed = await self.jobs.wait_for_job(
                job_id, timeout=t, poll_interval=every, fetch=fetch
            )
            return completed.get("response", completed)

        return response

    async def wait_if_job(
        self,
        response: dict[str, Any],
        timeout: int | None = None,
        poll_interval: float | None = None,
        fetch: Callable[[int, float], Awaitable[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Wait when an API response contains a recognized job reference.

        This is the public counterpart to the SDK's internal response helper,
        intended for integrations that dispatch generated SDK methods and must
        apply the same job timeout and polling semantics as handwritten APIs.
        ``fetch`` swaps the job observer, e.g.
        ``client.dashboards.job_by_url`` for published-dashboard jobs, which
        ``GET /jobs/{id}`` refuses with ``4PERM002``.
        """
        return await self._wait_if_job(
            response, timeout=timeout, poll_interval=poll_interval, fetch=fetch
        )

    def set_project_id(self, project_id: int) -> None:
        """Set the active project for subsequent API calls.

        Most operations (datasets, views, pipeline) require a project context.
        Call this once after creating the client.

        Args:
            project_id: ID of the project to use.

        Example::

            client.set_project_id(1134)
        """
        self.project_id = project_id

    async def test_connection(self) -> bool:
        """Test the connection to the Mammoth API.

        Makes a lightweight API call to verify credentials and network
        connectivity.

        Returns:
            ``True`` if credentials are valid and API is reachable,
            ``False`` otherwise.

        Example::

            if await client.test_connection():
                print("Connected!")
        """
        try:
            await self._request(
                "GET",
                f"/workspaces/{self.workspace_id}/projects",
                params={"fields": "id", "limit": 1},
            )
            return True
        except MammothAuthError:
            return False
        except Exception:
            return False

    # ── Top-level Convenience Methods ──────────────────────────

    async def get_view(self, view_id: int) -> View:
        """Get a rich View object by dataview ID.

        Shortcut for ``client.views.get(view_id)``. Automatically finds
        the parent dataset.

        Args:
            view_id: ID of the dataview.

        Returns:
            :class:`~mammoth.view.View` with transformation methods and
            metadata.

        Example::

            view = await client.get_view(1039)
            print(view.display_names)
        """
        return await self.views.get(view_id)

    async def branch_out(
        self,
        view_id: int,
        dataset_name: str,
        *,
        target_ds_id: int | None = None,
        column_mapping: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> int:
        """Branch out a view — save its data as a Mammoth dataset.

        Args:
            view_id: Source dataview ID.
            dataset_name: Name for the new dataset (display name when writing
                into an existing one).
            target_ds_id: Existing dataset to write into; None creates a new one.
            column_mapping: Source -> destination column-name map (optional).
            **kwargs: Additional options forwarded to :meth:`View.branch_out`
                (``save_as_mode``, ``label_ids``, ``condition``, ``timeout``).

        Returns:
            The id of the dataset written to (new when ``target_ds_id`` is None,
            otherwise ``target_ds_id``).
        """
        view = await self.views.get(view_id)
        return await view.branch_out(
            dataset_name, target_ds_id=target_ds_id, column_mapping=column_mapping, **kwargs
        )

    async def close(self) -> None:
        """Close the owned HTTP session.

        Safe to call more than once. After a CLI command completes, the caller
        closes the client deterministically instead of relying on interpreter
        shutdown.
        """
        closed_sessions: set[int] = set()
        for name in ("session", "download_session"):
            session = getattr(self, name, None)
            if session is not None and id(session) not in closed_sessions:
                await session.aclose()
                closed_sessions.add(id(session))

    async def __aenter__(self) -> MammothClient:
        """Context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        await self.close()


# Type alias for forward references
from mammoth.view import View as View  # noqa: E402
