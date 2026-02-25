# Client API Reference

The `MammothClient` is the single entry point for all Mammoth API interactions. It manages authentication, provides organized sub-clients for every resource, and supports context manager usage.

## Constructor

```python
from mammoth import MammothClient

client = MammothClient(
    api_key: str,
    api_secret: str,
    workspace_id: int,
    base_url: str = "https://app.mammoth.io/api/v2",
    timeout: int = 30,
    job_timeout: int = 60,
    pipeline_timeout: int = 3600,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | *required* | Your Mammoth API key |
| `api_secret` | `str` | *required* | Your Mammoth API secret |
| `workspace_id` | `int` | *required* | Your Mammoth workspace ID |
| `base_url` | `str` | `"https://app.mammoth.io/api/v2"` | Base URL for the Mammoth API |
| `timeout` | `int` | `30` | Request timeout in seconds for individual HTTP calls |
| `job_timeout` | `int` | `60` | Maximum time in seconds to poll a job to completion |
| `pipeline_timeout` | `int` | `3600` | Maximum time in seconds to wait for pipeline tasks |

!!! note "No retries"
    The SDK does **not** implement automatic retries. If an API call fails, the error is raised immediately. Implement retry logic in your application if needed.

### Example

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
    timeout=60,
    job_timeout=120,
)
client.set_project_id(10)
```

## Methods

### set_project_id

```python
client.set_project_id(project_id: int) -> None
```

Set the default project ID for the client. Required before most operations (listing datasets, working with views, running pipeline tasks, etc.).

```python
client.set_project_id(10)
```

### get_view

```python
client.get_view(view_id: int) -> View
```

Shortcut for `client.views.get(view_id)`. Returns a rich [View](views.md) object. The dataset is auto-detected.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `view_id` | `int` | *required* | ID of the dataview |

```python
view = client.get_view(1039)
print(view.display_names)
```

### find_dataset_for_dataview

```python
client.find_dataset_for_dataview(dataview_id: int) -> int
```

Searches all datasets in the current project to find which one contains the specified dataview. Returns the dataset ID.

```python
dataset_id = client.find_dataset_for_dataview(1039)
```

### branch_out

```python
client.branch_out(
    view_id: int,
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    **kwargs,
) -> dict[str, Any]
```

Branch out (export) a view to another dataset. Convenience wrapper around `view.branch_out()`.

### test_connection

```python
client.test_connection() -> bool
```

Test connectivity and authentication. Returns `True` if the API is reachable and credentials are valid, `False` otherwise.

## Context manager

The client supports Python's context manager protocol. The HTTP session is closed automatically on exit:

```python
with MammothClient(
    api_key="...", api_secret="...", workspace_id=11
) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.export.to_csv("output.csv")
# Session closed automatically
```

## Sub-clients

All API resources are accessible as attributes on the client. Each sub-client handles a specific area of the Mammoth API.

### Core data sub-clients

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.views` | `ViewsResource` | Rich View objects with transformations (see [Views](views.md)) |
| `client.datasets` | `DatasetsAPI` | Dataset CRUD operations (see [Datasets](datasets.md)) |
| `client.dataviews` | `DataviewsAPI` | Low-level dataview operations (see [Dataviews](dataviews.md)) |
| `client.pipeline` | `PipelineAPI` | Pipeline task management (see [Pipeline](pipeline.md)) |
| `client.files` | `FilesAPI` | File upload and management (see [Files](files.md)) |
| `client.exports` | `ExportsAPI` | Export operations (see [Exports](exports.md)) |
| `client.jobs` | `JobsAPI` | Asynchronous job tracking (see [Jobs](jobs.md)) |
| `client.projects` | `ProjectsAPI` | Project CRUD (see [Projects](projects.md)) |

### Additional sub-clients

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.ai` | `AIAPI` | AI/LLM operations (see [Other APIs](other-apis.md)) |
| `client.connectors` | `ConnectorsAPI` | Data source connectors (see [Connectors](connectors.md)) |
| `client.dashboards` | `DashboardsAPI` | Dashboard management (see [Dashboards](dashboards.md)) |
| `client.webhooks` | `WebhooksAPI` | Webhook configuration (see [Webhooks](webhooks.md)) |
| `client.automations` | `AutomationsAPI` | Automation workflows (see [Automations](automations.md)) |
| `client.schedules` | `SchedulesAPI` | Scheduled operations (see [Automations](automations.md)) |
| `client.batches` | `BatchesAPI` | Batch operations (see [Other APIs](other-apis.md)) |
| `client.folders` | `FoldersAPI` | Folder management (see [Other APIs](other-apis.md)) |
| `client.workspaces` | `WorkspaceAPI` | Workspace operations (see [Workspace](workspace.md)) |
| `client.user_profile` | `UserProfileAPI` | User profile (see [Workspace](workspace.md)) |
| `client.activity_logs` | `ActivityLogsAPI` | Activity logs (see [Other APIs](other-apis.md)) |
| `client.browse` | `BrowseAPI` | Browse/search API (see [Other APIs](other-apis.md)) |
| `client.external_keys` | `ExternalKeysAPI` | External key management (see [Other APIs](other-apis.md)) |
| `client.client_apps` | `ClientAppsAPI` | Client app management (see [Other APIs](other-apis.md)) |
| `client.addons` | `AddonsAPI` | Addons (see [Other APIs](other-apis.md)) |
| `client.reports` | `ReportsAPI` | Reports (see [Other APIs](other-apis.md)) |

### ViewsResource

The `client.views` sub-client returns rich [View](views.md) objects (not raw dicts):

```python
# Get a single view
view = client.views.get(view_id=1039)

# List all views across all datasets in the project
views = client.views.list()

# Create a new view
view = client.views.create(dataset_id=42, name="My Analysis")

# Clone from an existing view
view = client.views.create(dataset_id=42, name="Copy", clone_from=1039)

# Delete a view
client.views.delete(view_id=1039)

# Bulk delete
client.views.bulk_delete(view_ids=[1039, 1040])
```

## Request handling

### Authentication headers

The client automatically attaches these headers to every request:

- `X-API-KEY` -- your API key
- `X-API-SECRET` -- your API secret
- `X-WORKSPACE-ID` -- your workspace ID
- `User-Agent` -- `mammoth-io/{version}`

### Error handling

The client raises specific exceptions for different error types:

| Exception | Trigger |
|-----------|---------|
| `MammothAuthError` | HTTP 401 (invalid credentials) |
| `MammothAPIError` | HTTP 4xx/5xx responses, network errors, timeouts |

See [Exceptions](exceptions.md) for the full error hierarchy.

```python
from mammoth import MammothClient, MammothAPIError, MammothAuthError

try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    client.set_project_id(10)
    datasets = client.datasets.list()
except MammothAuthError:
    print("Invalid credentials")
except MammothAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## See also

- [Views](views.md) -- View object and transformation methods
- [Exports](exports.md) -- Export operations
- [Exceptions](exceptions.md) -- Error handling
- [Quick Start](../quick-start.md) -- Getting started
