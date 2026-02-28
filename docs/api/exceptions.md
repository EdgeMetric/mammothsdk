# Exceptions Reference

All SDK exceptions inherit from `MammothError`. Import them from `mammoth`:

```python
from mammoth import (
    MammothError,
    MammothAPIError,
    MammothAuthError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothTransformError,
    MammothColumnError,
)
```

## Hierarchy

```
MammothError
├── MammothAPIError
│   └── MammothAuthError
├── MammothJobTimeoutError
├── MammothJobFailedError
├── MammothTransformError
└── MammothColumnError
```

## Error handling example

```python
from mammoth import MammothClient, MammothAPIError, MammothAuthError

try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    client.set_project_id(10)
    view = client.get_view(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
except MammothAuthError:
    print("Invalid credentials")
except MammothAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
    print(f"Response: {e.response_body}")
except MammothColumnError as e:
    print(f"Column {e.details['column_name']} not found")
    print(f"Available: {e.details['available_columns']}")
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out after {e.details['timeout']}s")
```

---

## Full API Reference

::: mammoth.exceptions.MammothError

::: mammoth.exceptions.MammothAPIError

::: mammoth.exceptions.MammothAuthError

::: mammoth.exceptions.MammothJobTimeoutError

::: mammoth.exceptions.MammothJobFailedError

::: mammoth.exceptions.MammothTransformError

::: mammoth.exceptions.MammothColumnError

## See also

- [Client](client.md) -- error handling in the client
- [Views](views.md) -- transformation methods that raise these exceptions
