# Dataviews API Reference

The `DataviewsAPI` provides low-level CRUD operations on dataviews. For rich transformation methods, use `client.views` instead (see [Views](views.md)).

**Access**: `client.dataviews`

!!! tip "client.views vs client.dataviews"
    `client.views.get(id)` returns a rich `View` object with transformation methods, data access, and export helpers. `client.dataviews` is the lower-level API returning raw dicts.

## Methods

### list

```python
client.dataviews.list(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
    limit: int = 100,
    sort: str = "(created_at:desc)",
) -> dict[str, Any]
```

List dataviews in a dataset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `limit` | `int` | `100` | Maximum number of results |
| `sort` | `str` | `"(created_at:desc)"` | Sort order |

**Returns**: Dict containing `dataviews` list.

```python
resp = client.dataviews.list(dataset_id=42)
for dv in resp["dataviews"]:
    print(dv["id"], dv["name"])
```

### get

```python
client.dataviews.get(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get dataview information (raw dict).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_id` | `int` | *required* | ID of the dataview |

### create

```python
client.dataviews.create(
    dataset_id: int,
    name: str | None = "View",
    clone_config_from: int | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Create or duplicate a dataview.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `name` | `str \| None` | `"View"` | Name of the dataview |
| `clone_config_from` | `int \| None` | `None` | ID of dataview to clone pipeline from |

```python
# Create a blank view
dv = client.dataviews.create(dataset_id=42, name="Analysis")

# Clone an existing view's pipeline
dv = client.dataviews.create(dataset_id=42, name="Copy", clone_config_from=1039)
```

### update

```python
client.dataviews.update(
    dataset_id: int,
    dataview_id: int,
    patch_data: list[dict[str, Any]],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update dataview properties using JSON Patch operations.

### delete

```python
client.dataviews.delete(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a dataview.

### bulk_delete

```python
client.dataviews.bulk_delete(
    dataset_id: int,
    dataview_ids: list[int] | str,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete multiple dataviews.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_ids` | `list[int] \| str` | *required* | List of dataview IDs or comma-separated string |

### get_data

```python
client.dataviews.get_data(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
    timeout: int | None = None,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Get dataview data using GET method. Automatically polls the job until completion.

### query_data

```python
client.dataviews.query_data(
    dataset_id: int,
    dataview_id: int,
    sequence: int = 0,
    offset: int = 1,
    limit: int = 400,
    columns: list[str] | None = None,
    condition: dict[str, Any] | None = None,
    sort: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get dataview data with filtering options (POST method).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_id` | `int` | *required* | ID of the dataview |
| `sequence` | `int` | `0` | Pipeline step to fetch data at |
| `offset` | `int` | `1` | One-indexed starting row |
| `limit` | `int` | `400` | Number of rows to fetch |
| `columns` | `list[str] \| None` | `None` | Column names to fetch |
| `condition` | `dict \| None` | `None` | Filter condition dict |
| `sort` | `str \| None` | `None` | Sort specification |

### active_users

```python
client.dataviews.active_users(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get list of users currently active on this dataview.

### mark_active

```python
client.dataviews.mark_active(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Mark the current user as active on this dataview.

### conditional_format_list

```python
client.dataviews.conditional_format_list(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List conditional formatting rules for a dataview.

### conditional_format_create

```python
client.dataviews.conditional_format_create(
    dataset_id: int,
    dataview_id: int,
    rule: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a conditional formatting rule.

### conditional_format_update

```python
client.dataviews.conditional_format_update(
    dataset_id: int,
    dataview_id: int,
    rule: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a conditional formatting rule.

### conditional_format_delete

```python
client.dataviews.conditional_format_delete(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete all conditional formatting rules for a dataview.

### draft_mode

```python
client.dataviews.draft_mode(
    dataset_id: int,
    dataview_id: int,
    command: str,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Manage draft mode for the dataview pipeline.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_id` | `int` | *required* | ID of the dataview |
| `command` | `str` | *required* | `"enter"`, `"commit"`, or `"discard"` |

## See also

- [Views](views.md) -- Rich View objects with transformation methods
- [Pipeline](pipeline.md) -- Pipeline task management
- [Datasets](datasets.md) -- Dataset management
