# Files API Reference

The `FilesAPI` manages file uploads, listing, and deletion. Access it via `client.files`.

## upload()

Upload one or more files to create datasets. Each file becomes a separate dataset.

```python
client.files.upload(
    files: list[str | Path | BinaryIO] | str | Path | BinaryIO,
    folder_resource_id: str | None = None,
    append_to_ds_id: int | None = None,
    override_target_schema: bool | None = None,
    wait_for_completion: bool = True,
    timeout: int = 300,
) -> list[int] | int | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `str`, `Path`, `BinaryIO`, or list | *required* | File path(s), Path objects, or file-like objects to upload |
| `folder_resource_id` | `str` | `None` | Resource ID of target folder in Mammoth |
| `append_to_ds_id` | `int` | `None` | Dataset ID to append data to (instead of creating new) |
| `override_target_schema` | `bool` | `None` | Override target schema when appending |
| `wait_for_completion` | `bool` | `True` | Wait for upload processing to finish |
| `timeout` | `int` | `300` | Timeout in seconds when waiting |

**Returns:**

- Single file: `int` (the dataset ID)
- Multiple files: `list[int]` (list of dataset IDs)
- On failure or `wait_for_completion=False`: `None` or initial job ID

### Examples

```python
# Single file upload
dataset_id = client.files.upload("sales_data.csv")

# Multiple files
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx", "products.tsv"])

# Using Path objects
from pathlib import Path
dataset_id = client.files.upload(Path("data/report.csv"))

# Append to existing dataset
client.files.upload("new_rows.csv", append_to_ds_id=42)

# Upload to a specific folder
client.files.upload("data.csv", folder_resource_id="folder-abc-123")

# Non-blocking upload (returns job ID immediately)
job_id = client.files.upload("large_file.csv", wait_for_completion=False)
```

### After upload: get a View

```python
dataset_id = client.files.upload("sales_data.csv")
views = client.views.list(dataset_id)
view = views[0]  # Default view created on upload
print(view.display_names)  # ["Column1", "Column2", ...]
```

---

## upload_folder()

Upload all files in a folder. Calls `upload()` under the hood.

```python
client.files.upload_folder(
    folder_path: str | Path,
    folder_resource_id: str | None = None,
    wait_for_completion: bool = True,
    timeout: int = 300,
) -> list[int] | int | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | `str` or `Path` | *required* | Path to the folder containing files |
| `folder_resource_id` | `str` | `None` | Resource ID of target folder in Mammoth |
| `wait_for_completion` | `bool` | `True` | Wait for upload processing to finish |
| `timeout` | `int` | `300` | Timeout in seconds when waiting |

### Example

```python
# Upload everything in a folder
dataset_ids = client.files.upload_folder("./data/monthly_reports/")
```

---

## list()

List files in the current project with optional filtering and pagination.

```python
client.files.list(
    fields: str | None = None,
    file_ids: list[int] | None = None,
    names: list[str] | None = None,
    statuses: list[str] | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
) -> FilesList
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fields` | `str` | `None` | Fields to return (`"__standard"`, `"__full"`, `"__min"`) |
| `file_ids` | `list[int]` | `None` | Filter by specific file IDs |
| `names` | `list[str]` | `None` | Filter by file names |
| `statuses` | `list[str]` | `None` | Filter by file statuses |
| `created_at` | `str` | `None` | Date range filter for creation date |
| `updated_at` | `str` | `None` | Date range filter for update date |
| `limit` | `int` | `50` | Maximum results (0-100) |
| `offset` | `int` | `0` | Number of results to skip |
| `sort` | `str` | `None` | Sort spec (e.g., `"(id:asc)"`, `"(name:desc)"`) |

### Example

```python
files = client.files.list()
for f in files.files:
    print(f"{f.id}: {f.name} ({f.status})")

# Filter by name
files = client.files.list(names=["sales_data.csv"])
```

---

## get()

Get detailed information about a specific file.

```python
client.files.get(
    file_id: int,
    fields: str | None = None,
) -> FileSchema
```

### Example

```python
file_info = client.files.get(file_id=123)
print(f"Name: {file_info.name}")
print(f"Status: {file_info.status}")
```

---

## update()

Update file configuration (e.g., set password, extract sheets). Waits for the job to complete.

```python
client.files.update(
    file_id: int,
    patch_request: FilePatchRequest,
) -> ObjectJobSchema
```

This is the low-level method used internally by `set_password()` and `extract_sheets()`. You rarely need to call it directly.

---

## delete()

Delete a specific file.

```python
client.files.delete(file_id: int) -> None
```

### Example

```python
client.files.delete(file_id=123)
```

---

## bulk_delete()

Delete multiple files at once.

```python
client.files.bulk_delete(file_ids: list[int]) -> None
```

### Example

```python
client.files.bulk_delete([101, 102, 103])
```

---

## set_password()

Set a password for a password-protected file (e.g., encrypted Excel).

```python
client.files.set_password(file_id: int, password: str) -> ObjectJobSchema
```

---

## extract_sheets()

Extract specific sheets from an Excel file into separate datasets.

```python
client.files.extract_sheets(
    file_id: int,
    sheets: list[str],
    delete_file_after_extract: bool = True,
    combine_after_extract: bool = False,
) -> ObjectJobSchema
```

### Example

```python
client.files.extract_sheets(
    file_id=123,
    sheets=["Sheet1", "Revenue"],
    delete_file_after_extract=True,
)
```

---

## Supported file formats

| Category | Formats |
|----------|---------|
| Tabular | CSV, TSV, PSV, XLS, XLSX |
| Compressed | ZIP, BZ2, GZ, TAR, 7Z |
| Document | PDF |
| Image | TIFF, JPEG, PNG, HEIC, WEBP |

**Maximum file size:** 50 MB

---

## See also

- [End-to-End Workflow](../guides/end-to-end-workflow.md) -- upload, transform, and export
- [Client API](client.md) -- `MammothClient` and all sub-clients
- [Views](views.md) -- work with uploaded data
