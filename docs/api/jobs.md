# Jobs API Reference

The `JobsAPI` tracks asynchronous job status. Many Mammoth operations (data fetches, pipeline tasks, exports) create background jobs. The SDK polls these jobs automatically in most cases, but the Jobs API is available for manual control.

**Access**: `client.jobs`

## Methods

### get_job

```python
client.jobs.get_job(
    job_id: int,
    timeout: int = 300,
) -> dict[str, Any]
```

Get job status by ID.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_id` | `int` | *required* | ID of the job |
| `timeout` | `int` | `300` | Request timeout (compatibility parameter) |

**Returns**: Dict with job information including `status`, `response`, and timestamps.

```python
job = client.jobs.get_job(12345)
print(job["status"])  # "success", "processing", "failure", "error"
```

### get_jobs

```python
client.jobs.get_jobs(
    job_ids: list[int] | str,
) -> dict[str, Any]
```

Track multiple jobs at once.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_ids` | `list[int] \| str` | *required* | List of job IDs or comma-separated string |

**Returns**: Dict containing `jobs` list with status information.

```python
result = client.jobs.get_jobs([12345, 12346])
for job in result.get("jobs", []):
    print(job["id"], job["status"])
```

### wait_for_job

```python
client.jobs.wait_for_job(
    job_id: int,
    timeout: int | None = None,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Wait for a job to complete by polling until it reaches a terminal state.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_id` | `int` | *required* | ID of the job |
| `timeout` | `int \| None` | `None` | Maximum wait time in seconds (default: `client.job_timeout`) |
| `poll_interval` | `int` | `2` | Seconds between polling attempts |

**Returns**: Dict with completed job information.

**Raises**:

- `MammothJobFailedError` -- if the job fails
- `MammothJobTimeoutError` -- if timeout is exceeded

```python
job = client.jobs.wait_for_job(12345, timeout=120)
print(job["response"])
```

### wait_for_jobs

```python
client.jobs.wait_for_jobs(
    job_ids: list[int] | str,
    timeout: int | None = None,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Wait for multiple jobs to complete.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_ids` | `list[int] \| str` | *required* | List of job IDs or comma-separated string |
| `timeout` | `int \| None` | `None` | Maximum wait time in seconds (default: `client.job_timeout`) |
| `poll_interval` | `int` | `2` | Seconds between polling attempts |

**Returns**: Dict containing `jobs` list with all completed jobs.

**Raises**:

- `MammothJobFailedError` -- if any job fails
- `MammothJobTimeoutError` -- if timeout is exceeded

## Job statuses

| Status | Description |
|--------|-------------|
| `processing` | Job is still running |
| `success` | Job completed successfully |
| `failure` | Job failed (check `response.error` for details) |
| `error` | Job encountered an error |

## See also

- [Pipeline](pipeline.md) -- Pipeline tasks create jobs
- [Exceptions](exceptions.md) -- `MammothJobFailedError`, `MammothJobTimeoutError`
- [Job Lifecycle](../advanced/async-operations.md) -- Detailed async operations guide
