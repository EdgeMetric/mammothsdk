# Client API Reference

The `MammothClient` is the single entry point for all Mammoth API interactions. It manages authentication, provides organized sub-clients for every resource, and supports context manager usage.

## Quick start

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

!!! note "No retries"
    The SDK does **not** implement automatic retries. If an API call fails, the error is raised immediately. Implement retry logic in your application if needed.

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

---

## Full API Reference

::: mammoth.client.MammothClient
    options:
      members:
        - __init__
        - set_project_id
        - get_view
        - find_dataset_for_dataview
        - branch_out
        - test_connection

### ViewsResource

::: mammoth.client.ViewsResource
    options:
      members:
        - get
        - list
        - create
        - delete
        - bulk_delete

---

## Error handling

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
