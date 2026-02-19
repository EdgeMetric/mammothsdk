# Configuration

Advanced configuration options for the Mammoth SDK client.

## Client parameters

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
    base_url="https://app.mammoth.io/api/v2",
    timeout=30,
    job_timeout=60,
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `"https://app.mammoth.io/api/v2"` | API base URL. Change for custom Mammoth deployments. |
| `timeout` | `30` | HTTP request timeout in seconds. Applies to each individual API call. |
| `job_timeout` | `60` | Maximum time in seconds to poll a job to completion. Used by `jobs.wait_for_job()` and internally by View transformation methods. |

## Custom instance URLs

If your organization uses a custom Mammoth deployment:

```python
client = MammothClient(
    api_key="...",
    api_secret="...",
    workspace_id=11,
    base_url="https://your-instance.mammoth.io/api/v2",
)
```

The SDK normalizes the URL: if you pass `"https://your-instance.mammoth.io"` without the `/api/v2` suffix, it is appended automatically.

## Timeout tuning

### Request timeout

The `timeout` parameter controls how long each HTTP request waits before raising `MammothAPIError`. Increase it for slow networks:

```python
client = MammothClient(..., timeout=120)  # 2 minutes per request
```

### Job timeout

The `job_timeout` parameter controls how long the SDK polls when waiting for a job to complete. Increase it for large datasets or complex transformations:

```python
client = MammothClient(..., job_timeout=300)  # 5 minutes for jobs
```

Note that CSV exports have their own timeout parameter:

```python
view.export.to_csv("output.csv", timeout=600)  # 10 minutes
```

## No automatic retries

The SDK does not implement retries. If an API call fails due to a transient error, the exception is raised immediately. Implement retry logic at the application level if needed:

```python
import time
from mammoth import MammothAPIError

def with_retry(fn, max_retries=3, backoff=2):
    for attempt in range(max_retries):
        try:
            return fn()
        except MammothAPIError as e:
            if e.status_code and 400 <= e.status_code < 500:
                raise  # Do not retry client errors
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff ** attempt)
```

## Environment-based configuration

```python
import os

config = {
    "api_key": os.environ["MAMMOTH_API_KEY"],
    "api_secret": os.environ["MAMMOTH_API_SECRET"],
    "workspace_id": int(os.environ["MAMMOTH_WORKSPACE_ID"]),
    "base_url": os.getenv("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
    "timeout": int(os.getenv("MAMMOTH_TIMEOUT", "30")),
    "job_timeout": int(os.getenv("MAMMOTH_JOB_TIMEOUT", "60")),
}

client = MammothClient(**config)
```

## See also

- [Client API](../api/client.md) -- full client reference
- [Authentication](../authentication.md) -- credential management
