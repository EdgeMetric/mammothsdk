# Datasets API Reference

The `DatasetsAPI` manages datasets within a project. A dataset is a data table stored in Mammoth, created from file uploads, connectors, or cloning.

**Access**: `client.datasets`

!!! note "Requires project_id"
    Most methods require a project ID. Set it on the client with `client.set_project_id(10)` or pass `project_id` explicitly.

## Methods

### list

```python
client.datasets.list(
    workspace_id: int | None = None,
    project_id: int | None = None,
    limit: int = 100,
    sort: str = "(created_at:desc)",
) -> dict[str, Any]
```

List datasets in a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default) |
| `project_id` | `int \| None` | `None` | Project ID (uses client default) |
| `limit` | `int` | `100` | Maximum number of results |
| `sort` | `str` | `"(created_at:desc)"` | Sort order |

**Returns**: Dict containing `datasets` list with `id` and `name` fields.

```python
resp = client.datasets.list()
for ds in resp["datasets"]:
    print(ds["id"], ds["name"])
```

### get

```python
client.datasets.get(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get dataset details by ID.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |

**Returns**: Dict with complete dataset information including metadata, column info, and settings.

```python
ds = client.datasets.get(42)
print(ds["name"], ds.get("row_count"))
```

### get_data

```python
client.datasets.get_data(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
    timeout: int = 300,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Get the actual data rows from a dataset. This triggers a job and polls until completion.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `timeout` | `int` | `300` | Maximum wait time in seconds |
| `poll_interval` | `int` | `2` | Polling interval in seconds |

**Returns**: Dict with dataset data rows.

```python
data = client.datasets.get_data(42)
```

### create

```python
client.datasets.create(
    dataset_spec: dict[str, Any],
    ds_creation_type: str,
    folder_resource_id: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new dataset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_spec` | `dict` | *required* | Dataset specification (varies by creation type) |
| `ds_creation_type` | `str` | *required* | Type: `"clone"`, `"cloud"`, `"sketch"`, or `"weburl"` |
| `folder_resource_id` | `str \| None` | `None` | Folder to place the dataset in |

```python
# Clone an existing dataset
ds = client.datasets.create(
    dataset_spec={"source_dataset_id": 42},
    ds_creation_type="clone",
)
```

### update

```python
client.datasets.update(
    dataset_id: int,
    patch_data: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a dataset using JSON Patch operations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `patch_data` | `dict` | *required* | Patch operation data |

### delete

```python
client.datasets.delete(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> None
```

Delete a dataset.

### bulk_update

```python
client.datasets.bulk_update(
    patch_data: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update multiple datasets (bulk operation).

### bulk_delete

```python
client.datasets.bulk_delete(
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> None
```

Delete multiple datasets (bulk operation).

### browse

```python
client.datasets.browse(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Browse dataset contents (dataviews, metadata).

```python
contents = client.datasets.browse(42)
```

### list_batches

```python
client.datasets.list_batches(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List batches for a dataset. A batch represents a data upload or refresh event.

**Returns**: List of batch dicts.

### get_batch

```python
client.datasets.get_batch(
    dataset_id: int,
    batch_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific batch.

### get_file_settings

```python
client.datasets.get_file_settings(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get file settings for a dataset (delimiter, encoding, etc.).

## See also

- [Client](client.md) -- MammothClient and sub-clients overview
- [Dataviews](dataviews.md) -- Dataview management within datasets
- [Views](views.md) -- Rich View objects for transformations
