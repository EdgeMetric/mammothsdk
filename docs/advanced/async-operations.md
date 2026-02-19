# Job Lifecycle

The Mammoth platform processes many operations asynchronously via jobs. Understanding the job lifecycle helps you work effectively with the SDK.

## How jobs work

When you apply a transformation, export data, or perform other operations, the backend creates a job:

1. The SDK sends the task to the API
2. The API returns a job ID
3. The SDK polls the job until it completes (or times out)
4. On success, the SDK refreshes view metadata

Most of this is handled automatically by View transformation methods. You only need to interact with jobs directly for advanced use cases.

## Automatic job handling

View transformation methods handle jobs internally:

```python
# This sends a task, waits for the job, and refreshes the view -- all in one call
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
```

The `_add_task()` internal method:

1. Calls `pipeline.add_task()` to submit the task
2. Extracts the job ID from the response
3. Calls `jobs.wait_for_job(job_id)` to poll until completion
4. Calls `view.refresh()` to update metadata

## Job timeout

The `job_timeout` client parameter controls how long the SDK waits:

```python
client = MammothClient(
    ...,
    job_timeout=300,  # Wait up to 5 minutes for jobs
)
```

If a job does not complete in time, `MammothJobTimeoutError` is raised:

```python
from mammoth import MammothJobTimeoutError

try:
    view.pivot(
        group_by=["Region"],
        aggregations=[{"column": "Sales", "function": "SUM", "as": "Total"}],
    )
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} is still running")
```

## Manual job management

For advanced scenarios, use the jobs sub-client directly:

```python
# Get job status
job = client.jobs.get_job(job_id=12345)

# Wait for a job with custom timeout
completed = client.jobs.wait_for_job(job_id=12345, timeout=600)

# Check the result
if completed.get("status") == "success":
    print("Job completed successfully")
else:
    print(f"Job failed: {completed.get('response', {}).get('response', {}).get('detail')}")
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

## See also

- [Views](../api/views.md) -- transformation methods
- [Exceptions](../api/exceptions.md) -- job-related exceptions
- [Configuration](configuration.md) -- timeout settings
