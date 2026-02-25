# Other APIs Reference

This page covers smaller utility sub-clients that provide access to folders, batches, browse, client apps, external keys, activity logs, addons, reports, and AI features.

---

## FoldersAPI

**Access**: `client.folders`

Manage folders within projects for organizing datasets and resources.

### list

```python
client.folders.list(
    workspace_id: int | None = None,
    project_id: int | None = None,
    fields: str | None = None,
    folder_ids: list[int] | None = None,
    names: list[str] | None = None,
    statuses: list[str] | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    created_by: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
) -> FoldersList
```

List folders with filtering and pagination. Returns a `FoldersList` Pydantic model.

```python
folders = client.folders.list()
```

### create

```python
client.folders.create(
    name: str,
    parent_resource_id: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> FolderSchema
```

Create a new folder. Returns a `FolderSchema` Pydantic model with `id`, `name`, `resource_id`, etc.

```python
folder = client.folders.create(name="Reports")
print(folder.id, folder.resource_id)
```

### delete

```python
client.folders.delete(
    folder_ids: list[int],
    workspace_id: int | None = None,
    project_id: int | None = None,
    check_dependency: bool = True,
    remove_contents: bool = True,
) -> None
```

Delete folders.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_ids` | `list[int]` | *required* | List of folder IDs to delete |
| `check_dependency` | `bool` | `True` | Check for dependencies before deleting |
| `remove_contents` | `bool` | `True` | Remove folder contents before deleting |

### move

```python
client.folders.move(
    resource_ids: list[str],
    target_folder_resource_id: str | None = None,
    source_folder_resource_id: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> ObjectJobSchema
```

Move resources between folders. Returns an `ObjectJobSchema` with job information.

---

## BatchesAPI

**Access**: `client.batches`

Manage dataset batches (data upload/refresh events).

### list

```python
client.batches.list(
    dataset_id: int,
    project_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]
```

List batches for a dataset.

### get

```python
client.batches.get(
    dataset_id: int,
    batch_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get batch details.

### create

```python
client.batches.create(
    dataset_id: int,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new batch for a dataset.

### update

```python
client.batches.update(
    dataset_id: int,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update batches for a dataset.

### delete

```python
client.batches.delete(
    dataset_id: int,
    batch_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a batch.

---

## BrowseAPI

**Access**: `client.browse`

Quick resource discovery and navigation through the hierarchy.

### workspaces

```python
client.browse.workspaces() -> dict[str, Any]
```

Browse available workspaces.

### projects

```python
client.browse.projects(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse projects in a workspace.

### datasets

```python
client.browse.datasets(
    project_id: int | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse datasets in a project.

### dataviews

```python
client.browse.dataviews(
    dataset_id: int,
    project_id: int | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse dataviews in a dataset.

```python
# Walk the hierarchy
projects = client.browse.projects()
datasets = client.browse.datasets(project_id=10)
dataviews = client.browse.dataviews(dataset_id=42)
```

---

## ClientAppsAPI

**Access**: `client.client_apps`

Manage API tokens and client applications. Client apps generate API key/secret pairs for programmatic access.

### list

```python
client.client_apps.list(
    workspace_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
    fields: str | None = None,
    sort: str | None = None,
) -> ClientAppsListResponse
```

List client apps. Returns a `ClientAppsListResponse` Pydantic model.

### create

```python
client.client_apps.create(
    app_name: str,
    description: str | None = None,
    workspace_id: int | None = None,
) -> ClientAppPostResponse
```

Create a new client app to generate API tokens. Returns a `ClientAppPostResponse` with the app details and tokens.

```python
app = client.client_apps.create(app_name="My Integration")
print(app.api_key, app.api_secret)
```

### get

```python
client.client_apps.get(
    client_key: str,
    workspace_id: int | None = None,
    fields: str | None = None,
) -> ClientAppSchema
```

Get details of a specific client app.

### update

```python
client.client_apps.update(
    client_key: str,
    patch_request: PatchRequest,
    workspace_id: int | None = None,
) -> ClientAppSchema
```

Update client app details.

### delete

```python
client.client_apps.delete(
    client_key: str,
    workspace_id: int | None = None,
) -> None
```

Delete a client app.

---

## ExternalKeysAPI

**Access**: `client.external_keys`

Manage external API keys for workspace integrations.

### list

```python
client.external_keys.list() -> dict[str, Any]
```

List all external API keys.

### get

```python
client.external_keys.get(key_id: int) -> dict[str, Any]
```

Get external key details.

### create

```python
client.external_keys.create(config: dict[str, Any]) -> dict[str, Any]
```

Create a new external API key.

### delete

```python
client.external_keys.delete(key_id: int) -> dict[str, Any]
```

Delete an external API key.

---

## ActivityLogsAPI

**Access**: `client.activity_logs`

Query and export activity logs for audit purposes.

### list

```python
client.activity_logs.list(
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
    **filters: Any,
) -> dict[str, Any]
```

List activity logs with pagination and filtering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `50` | Maximum number of results |
| `offset` | `int` | `0` | Number of results to skip |
| `sort` | `str \| None` | `None` | Sort specification |
| `**filters` | `Any` | | Additional filters (user, action, resource, etc.) |

```python
logs = client.activity_logs.list(limit=20)
```

### export

```python
client.activity_logs.export(
    format: str = "csv",
    **filters: Any,
) -> dict[str, Any]
```

Export activity logs to a file.

---

## AddonsAPI

**Access**: `client.addons`

Manage workspace addons for connectors, storage, and user capacity.

### add_connector / remove_connector

```python
client.addons.add_connector(config: dict[str, Any]) -> dict[str, Any]
client.addons.remove_connector(config: dict[str, Any]) -> dict[str, Any]
```

### add_storage / remove_storage

```python
client.addons.add_storage(config: dict[str, Any]) -> dict[str, Any]
client.addons.remove_storage(config: dict[str, Any]) -> dict[str, Any]
```

### add_users / remove_users

```python
client.addons.add_users(config: dict[str, Any]) -> dict[str, Any]
client.addons.remove_users(config: dict[str, Any]) -> dict[str, Any]
```

---

## ReportsAPI

**Access**: `client.reports`

List workspace reports.

### list

```python
client.reports.list(
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]
```

List all reports.

---

## AIAPI

**Access**: `client.ai`

AI-powered features including profiling, data generation, SQL generation, and suggestions.

### generate_profile

```python
client.ai.generate_profile(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Generate an AI profile/summary of the dataview data. Waits for the async job.

### generate_data

```python
client.ai.generate_data(
    dataview_id: int,
    config: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Generate synthetic data for a dataview.

### get_data_gen_info

```python
client.ai.get_data_gen_info(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Get data generation information for a dataview.

### generate_sql

```python
client.ai.generate_sql(
    intent: str,
    sequence_number: int = 0,
) -> dict[str, Any]
```

Generate SQL from natural language intent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `intent` | `str` | *required* | Natural language description of the query |
| `sequence_number` | `int` | `0` | Sequence number for the request |

```python
result = client.ai.generate_sql("total sales by region for Q4")
```

### get_suggestions

```python
client.ai.get_suggestions() -> dict[str, Any]
```

Get AI-powered transformation suggestions for the current project.

### query_gen

```python
client.ai.query_gen(
    connector_key: str,
    connection_key: str,
    prompt: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Generate a query for a connector using AI.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key |
| `connection_key` | `str` | *required* | Connection key |
| `prompt` | `str` | *required* | Natural language prompt describing the query |

## See also

- [Client](client.md) -- Full list of sub-clients
- [Projects](projects.md) -- Project management
- [Datasets](datasets.md) -- Dataset management
