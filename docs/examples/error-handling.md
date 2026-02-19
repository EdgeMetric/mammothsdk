# Error Handling Guide

The Mammoth SDK provides specific exception types for different error scenarios. This guide shows how to handle them.

## Exception hierarchy

```
MammothError                     # Base -- catch-all for any SDK error
  +-- MammothAPIError            # HTTP errors, network errors, invalid responses
  |     +-- MammothAuthError     # HTTP 401 (bad credentials)
  +-- MammothJobTimeoutError     # Job polling exceeded timeout
  +-- MammothJobFailedError      # Job completed with failure status
  +-- MammothTransformError      # Transformation task failure
  +-- MammothColumnError         # Column name not found
```

## Handling specific exceptions

### Authentication errors

```python
from mammoth import MammothClient, MammothAuthError

try:
    client = MammothClient(api_key="bad", api_secret="bad", workspace_id=1)
    client.set_project_id(1)
    client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API key and secret")
```

### API errors

```python
from mammoth import MammothAPIError

try:
    datasets = client.datasets.list()
except MammothAPIError as e:
    print(f"API error: {e.message}")
    print(f"HTTP status: {e.status_code}")
    print(f"Response body: {e.response_body}")

    if e.status_code == 404:
        print("Resource not found")
    elif e.status_code and e.status_code >= 500:
        print("Server error -- try again later")
```

### Column errors

```python
from mammoth import MammothColumnError, Condition, Operator

try:
    view.filter_rows(Condition("Nonexistent Column", Operator.GTE, 100))
except MammothColumnError as e:
    print(e.message)
    # "Column 'Nonexistent Column' not found. Available columns: ['Sales', 'Region', ...]"
    print(f"Available columns: {e.details['available_columns']}")
```

### Job timeout

```python
from mammoth import MammothJobTimeoutError

try:
    view.pivot(
        group_by=["Region"],
        aggregations=[{"column": "Sales", "function": "SUM", "as": "Total"}],
    )
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out after {e.details['timeout']}s")
    print("The job may still be processing -- check the Mammoth dashboard")
```

### Job failure

```python
from mammoth import MammothJobFailedError

try:
    view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed")
    print(f"Reason: {e.details.get('failure_reason', 'Unknown')}")
```

### Transform errors

```python
from mammoth import MammothTransformError

try:
    view.math("InvalidExpr @@@ 2", new_column="Result")
except MammothTransformError as e:
    print(f"Transformation failed: {e.message}")
    print(f"Task key: {e.task_key}")
```

## Recommended pattern

Handle exceptions from most specific to least specific:

```python
from mammoth import (
    MammothAuthError,
    MammothColumnError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothTransformError,
    MammothAPIError,
    MammothError,
)

try:
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")

except MammothAuthError:
    print("Bad credentials")

except MammothColumnError as e:
    print(f"Column not found: {e.details['column_name']}")

except MammothJobTimeoutError as e:
    print(f"Job timed out: {e.details['job_id']}")

except MammothJobFailedError as e:
    print(f"Job failed: {e.details.get('failure_reason')}")

except MammothTransformError as e:
    print(f"Transform error: {e.message}")

except MammothAPIError as e:
    print(f"API error ({e.status_code}): {e.message}")

except MammothError as e:
    print(f"SDK error: {e.message}")
```

## Logging errors

```python
import logging
from mammoth import MammothAPIError, MammothJobFailedError

logger = logging.getLogger("mammoth_app")

try:
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
except MammothJobFailedError as e:
    logger.error(
        "Pipeline job failed",
        extra={
            "job_id": e.details.get("job_id"),
            "reason": e.details.get("failure_reason"),
        },
    )
    raise
except MammothAPIError as e:
    logger.error(f"API error ({e.status_code}): {e.message}")
    raise
```

## Increasing timeouts

If jobs time out, increase the `job_timeout` on the client:

```python
client = MammothClient(
    api_key="...",
    api_secret="...",
    workspace_id=11,
    job_timeout=300,  # 5 minutes instead of default 60s
)
```

Or increase the timeout for CSV exports:

```python
view.export.to_csv("output.csv", timeout=600)  # 10 minutes
```

## See also

- [Exceptions reference](../api/exceptions.md) -- full exception class documentation
- [Client API](../api/client.md) -- timeout configuration
