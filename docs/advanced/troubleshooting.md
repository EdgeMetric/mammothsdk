# Troubleshooting

Common issues and their solutions.

## Authentication errors

**Symptom**: `MammothAuthError: Authentication failed`

**Solutions**:

- Verify your API key and secret are correct
- Confirm the `workspace_id` matches your account
- Check that the `base_url` points to the correct Mammoth instance
- Ensure your API credentials have not been revoked or rotated

```python
# Verify your credentials
try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    if client.test_connection():
        print("Credentials are valid")
except MammothAuthError:
    print("Credentials are invalid")
```

## Column not found

**Symptom**: `MammothColumnError: Column 'X' not found. Available columns: [...]`

**Solutions**:

- Check the exact column display name (case-sensitive)
- Call `view.refresh()` if the view was modified externally
- Print `view.display_names` to see available columns

```python
print(view.display_names)
# ['Sales Amount', 'Region', 'Order Date']
# Note: "Sales" vs "Sales Amount" matters
```

## Job timeout

**Symptom**: `MammothJobTimeoutError: Job X timed out after Y seconds`

**Solutions**:

- Increase `job_timeout` on the client for large datasets
- For CSV exports, increase the `timeout` parameter on `to_csv()`
- Check the Mammoth dashboard to see if the job is still running

```python
# Increase job timeout
client = MammothClient(..., job_timeout=300)

# Increase CSV export timeout
view.export.to_csv("output.csv", timeout=600)
```

## Job failed

**Symptom**: `MammothJobFailedError: Job X failed: <reason>`

**Solutions**:

- Read the failure reason in `e.details["failure_reason"]`
- Check the Mammoth dashboard for detailed error logs
- Common causes: invalid column types for operations, data format issues

```python
try:
    view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
except MammothJobFailedError as e:
    print(f"Reason: {e.details['failure_reason']}")
```

## project_id not set

**Symptom**: `ValueError: project_id must be set on the client using client.set_project_id()`

**Solution**: Call `client.set_project_id(id)` before performing operations:

```python
client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)  # Required before most operations
```

## Date columns not working

**Symptom**: Date operations fail on columns uploaded from CSV.

**Cause**: CSV date columns are uploaded as TEXT type by default.

**Solution**: Convert to DATE type first:

```python
view.convert_type([{"column": "Order Date", "to": "DATE"}])
# Now date operations work
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
```

## Network / connection errors

**Symptom**: `MammothAPIError: Connection error: ...` or `Request timeout: ...`

**Solutions**:

- Check your network connectivity
- Verify the `base_url` is reachable
- Increase the `timeout` for slow networks

```python
client = MammothClient(..., timeout=120)  # 2 minutes per request
```

## Import errors

**Symptom**: `ImportError` or `ModuleNotFoundError` when importing from mammoth

**Solutions**:

- Ensure the package is installed: `pip install mammoth-io`
- Verify Python 3.10+: `python --version`
- Check you are importing from the correct package: `from mammoth import MammothClient`

## See also

- [Exceptions reference](../api/exceptions.md) -- error class documentation
- [Configuration](configuration.md) -- timeout and URL settings
- [Error handling guide](../examples/error-handling.md) -- handling patterns
