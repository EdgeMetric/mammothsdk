# Pipeline API Reference

The `PipelineAPI` manages the transformation pipeline on dataviews. Each dataview has an ordered list of pipeline tasks (filter, join, pivot, etc.) that transform the data.

**Access**: `client.pipeline`

!!! note "Internal use"
    The `PipelineAPI` is primarily used internally by `View` objects. For most use cases, use `view.filter_rows()`, `view.math()`, etc. instead of calling `client.pipeline` directly.

## Methods

### get_pipeline

```python
client.pipeline.get_pipeline(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Get the current pipeline state for a dataview.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected if not provided) |

**Returns**: Pipeline state dict including `state` (e.g. `"ready"`, `"running"`), task list, and metadata.

```python
pipeline = client.pipeline.get_pipeline(dataview_id=1039)
print(pipeline["state"])  # "ready"
```

### list_tasks

```python
client.pipeline.list_tasks(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

List all pipeline tasks for a dataview.

**Returns**: Dict with `tasks` list, each containing task type, parameters, and sequence number.

```python
resp = client.pipeline.list_tasks(dataview_id=1039)
for task in resp.get("tasks", []):
    print(task["id"], task.get("params", {}).get("TYPE"))
```

### add_task

```python
client.pipeline.add_task(
    dataview_id: int,
    task_spec: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Add a new transformation task to the pipeline. Waits for the async job to complete.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `task_spec` | `dict` | *required* | Task specification (varies by task type) |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected if not provided) |

**Returns**: Dict with created task info.

### get_task

```python
client.pipeline.get_task(
    dataview_id: int,
    task_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Get a specific pipeline task by ID.

### update_task

```python
client.pipeline.update_task(
    dataview_id: int,
    task_id: int,
    task_spec: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Update an existing pipeline task. Waits for the async job to complete.

### delete_task

```python
client.pipeline.delete_task(
    dataview_id: int,
    task_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Delete a pipeline task. This is how transformations are "undone" -- each task removal is reversible.

```python
client.pipeline.delete_task(dataview_id=1039, task_id=5678)
```

### preview_task

```python
client.pipeline.preview_task(
    dataview_id: int,
    task_spec: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Preview task results without adding to the pipeline. Useful for testing transformations before committing.

### draft_mode

```python
client.pipeline.draft_mode(
    dataview_id: int,
    command: str,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Manage draft mode for a dataview pipeline. Draft mode lets you add multiple tasks before committing them all at once.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `command` | `str` | *required* | `"enter"`, `"commit"`, or `"discard"` |

### edit_pipeline

```python
client.pipeline.edit_pipeline(
    dataview_id: int,
    patches: list[dict[str, Any]],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

PATCH pipeline with operations (auto_run, run, reset, etc.).

### wait_for_pipeline

```python
client.pipeline.wait_for_pipeline(
    dataview_id: int,
    dataset_id: int | None = None,
    timeout: int | None = None,
    poll_interval: int = 3,
) -> dict[str, Any]
```

Poll pipeline state until it reaches a terminal state (`ready`, `runtime_error`, `ref_error`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected) |
| `timeout` | `int \| None` | `None` | Max wait time in seconds (default: `client.pipeline_timeout`) |
| `poll_interval` | `int` | `3` | Seconds between polls |

**Raises**:

- `MammothTransformError` -- if pipeline reaches `runtime_error` or `ref_error`
- `MammothJobTimeoutError` -- if timeout is exceeded

```python
# Wait for pipeline after an external change
pipeline = client.pipeline.wait_for_pipeline(dataview_id=1039, timeout=120)
print(pipeline["state"])  # "ready"
```

## Pipeline states

| State | Description |
|-------|-------------|
| `ready` | Pipeline complete, data is available |
| `running` | Pipeline is executing tasks |
| `modifying` | Pipeline is being modified |
| `modified` | Changes pending execution |
| `runtime_error` | A task failed during execution |
| `ref_error` | A dependency reference is broken |

## See also

- [Views](views.md) -- Rich View objects that wrap pipeline operations
- [Jobs](jobs.md) -- Job tracking for async operations
- [Dataviews](dataviews.md) -- Low-level dataview CRUD
