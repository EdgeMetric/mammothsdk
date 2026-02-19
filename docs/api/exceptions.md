# Exceptions Reference

The SDK provides a hierarchy of exception classes for precise error handling.

## Exception hierarchy

```
MammothError                     # Base exception for all SDK errors
  +-- MammothAPIError            # API request failures (HTTP errors, network errors)
  |     +-- MammothAuthError     # Authentication failures (HTTP 401)
  +-- MammothJobTimeoutError     # Job polling timeout
  +-- MammothJobFailedError      # Job execution failure
  +-- MammothTransformError      # Transformation task failure
  +-- MammothColumnError         # Column name resolution failure
```

## MammothError

Base exception for all Mammoth SDK errors.

```python
class MammothError(Exception):
    message: str
    details: dict[str, Any]
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error message |
| `details` | `dict` | Additional error details (default `{}`) |

```python
from mammoth import MammothError

try:
    ...
except MammothError as e:
    print(e.message)
    print(e.details)
```

## MammothAPIError

Raised for API-related errors: HTTP 4xx/5xx responses, network errors, timeouts, and invalid responses.

```python
class MammothAPIError(MammothError):
    status_code: int | None
    response_body: dict[str, Any]
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `status_code` | `int \| None` | HTTP status code (if available) |
| `response_body` | `dict` | Full API response body (default `{}`) |
| `details` | `dict` | Additional error details |

```python
from mammoth import MammothAPIError

try:
    datasets = client.datasets.list()
except MammothAPIError as e:
    print(f"API error: {e.message}")
    print(f"HTTP status: {e.status_code}")
    print(f"Response: {e.response_body}")
```

## MammothAuthError

Raised when authentication fails (HTTP 401). Subclass of `MammothAPIError`.

```python
class MammothAuthError(MammothAPIError):
    pass  # status_code is always 401
```

```python
from mammoth import MammothAuthError

try:
    client = MammothClient(api_key="bad", api_secret="bad", workspace_id=1)
    client.set_project_id(1)
    client.projects.list()
except MammothAuthError:
    print("Invalid API credentials")
```

## MammothJobTimeoutError

Raised when a job does not complete within the allowed timeout.

```python
class MammothJobTimeoutError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["job_id"]` | `int` | ID of the timed-out job |
| `details["timeout"]` | `int` | Timeout value in seconds |

```python
from mammoth import MammothJobTimeoutError

try:
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
except MammothJobTimeoutError as e:
    job_id = e.details["job_id"]
    timeout = e.details["timeout"]
    print(f"Job {job_id} timed out after {timeout}s")
```

## MammothJobFailedError

Raised when a job completes with a failure status.

```python
class MammothJobFailedError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["job_id"]` | `int` | ID of the failed job |
| `details["failure_reason"]` | `str \| None` | Reason for failure |

```python
from mammoth import MammothJobFailedError

try:
    view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed: {e.details['failure_reason']}")
```

## MammothTransformError

Raised when a transformation task fails. Includes the task key for identification.

```python
class MammothTransformError(MammothError):
    task_key: str | None
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `task_key` | `str \| None` | Pipeline task key (e.g., `"SET"`, `"MATH"`) |
| `details` | `dict` | Additional error details |

```python
from mammoth import MammothTransformError

try:
    view.math("InvalidColumn * 2", new_column="Result")
except MammothTransformError as e:
    print(f"Transform failed: {e.message}")
    print(f"Task: {e.task_key}")
```

## MammothColumnError

Raised when a column display name cannot be resolved to an internal name. Includes the list of available columns for easy debugging.

```python
class MammothColumnError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["column_name"]` | `str` | The column name that was not found |
| `details["available_columns"]` | `list[str] \| None` | List of valid column names |

```python
from mammoth import MammothColumnError

try:
    view.filter_rows(Condition("Nonexistent", Operator.GTE, 100))
except MammothColumnError as e:
    print(e.message)
    # "Column 'Nonexistent' not found. Available columns: ['Sales', 'Region', ...]"
```

## Error handling patterns

### Catch specific exceptions

```python
from mammoth import (
    MammothAPIError,
    MammothAuthError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothColumnError,
)

try:
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")

except MammothAuthError:
    print("Invalid credentials -- check API key and secret")

except MammothColumnError as e:
    print(f"Column not found: {e.details['column_name']}")
    print(f"Available: {e.details['available_columns']}")

except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out")

except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed: {e.details['failure_reason']}")

except MammothAPIError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

### Use the base class as a catch-all

```python
from mammoth import MammothError

try:
    view.math("Price * Quantity", new_column="Total")
except MammothError as e:
    print(f"Mammoth error: {e.message}")
```

## See also

- [Client](client.md) -- how the client raises exceptions
- [Views](views.md) -- transformation methods that can raise errors
