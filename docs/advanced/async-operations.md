# Async Operations & Timeouts

All SDK operations are **synchronous** — transformation methods block until the operation completes and view metadata is refreshed. The backend processes tasks asynchronously, but the SDK handles this transparently.

## Timeouts

The `job_timeout` and `pipeline_timeout` client parameters control how long the SDK waits:

```python
client = MammothClient(
    ...,
    job_timeout=300,  # Wait up to 5 minutes for jobs
)
```

If a job does not complete in time, `MammothJobTimeoutError` is raised:

```python
from mammoth import MammothJobTimeoutError, AggregateFunction, AggregationSpec

try:
    view.pivot(
        group_by=["Region"],
        aggregations=[AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total")],
    )
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} is still running")
```

## Pipeline tasks

Each View maintains an ordered list of pipeline tasks. You can inspect and manage them:

```python
# List all tasks
tasks = view.list_tasks()
for task in tasks:
    print(f"Task {task['id']}: {task.get('task_key')} (seq {task.get('sequence')})")

# Delete a task (re-runs the pipeline without it)
view.delete_task(task_id=42)

# Preview a task before applying
preview = view.preview_task(task_spec)
```

## Draft mode

By default, each transformation triggers an immediate pipeline run. For batch operations on large datasets, use **draft mode** to queue tasks and run the pipeline once:

```python
from mammoth import Condition, Operator, SetValue, ColumnType

# Context manager approach (recommended)
with view.draft():
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.math("Price * 2", new_column="Double")
# Pipeline runs once for both tasks

# Explicit approach
view.enter_draft_mode()
view.add_column("Notes")
view.set_values(new_column="Flag", column_type=ColumnType.TEXT, values=[SetValue("x")])
view.submit_draft()  # runs pipeline, refreshes metadata, exits draft mode
```

If an exception occurs inside the `with view.draft():` block, all queued tasks are discarded automatically. You can also discard explicitly with `view.discard_draft()`.

See [Views reference](../api/views.md#draft-mode) for the full API.

## See also

- [Views](../api/views.md) -- transformation methods
- [Exceptions](../api/exceptions.md) -- job-related exceptions
- [Configuration](configuration.md) -- timeout settings
