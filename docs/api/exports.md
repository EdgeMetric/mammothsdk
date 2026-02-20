# Exports Reference

The SDK provides two ways to export data:

1. **ViewExport** (`view.export`) -- export methods attached to a View object
2. **ExportsAPI** (`client.exports`) -- lower-level export operations

## ViewExport

Access via `view.export`. This is the recommended way to export data from a View.

### to_csv

Download the view data as a local CSV file.

```python
view.export.to_csv(
    output_path: str | None = None,
    timeout: int = 300,
) -> Path
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_path` | `str \| None` | `None` | Output file path (auto-generated if not provided) |
| `timeout` | `int` | `300` | Timeout in seconds for the export job |

Returns a `pathlib.Path` to the downloaded file.

```python
path = view.export.to_csv("output.csv")
print(f"Downloaded to {path}")

# Auto-generated filename
path = view.export.to_csv()
```

### to_s3

Export to S3 storage.

```python
view.export.to_s3(
    file_name: str | None = None,
    file_type: ExportFileType = ExportFileType.CSV,
    include_hidden: bool = False,
    **kwargs,
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | `str \| None` | `None` | Output filename (auto-generated if not provided) |
| `file_type` | `ExportFileType` | `ExportFileType.CSV` | File format enum |
| `include_hidden` | `bool` | `False` | Include hidden columns |

```python
from mammoth import ExportFileType

result = view.export.to_s3(file_name="report.csv")
result = view.export.to_s3(file_name="data.json", file_type=ExportFileType.JSON, include_hidden=True)
```

### to_postgres

Export to a PostgreSQL database.

```python
view.export.to_postgres(
    host: str,
    port: int,
    database: str,
    table: str,
    username: str,
    password: str,
    **kwargs,
) -> dict[str, Any]
```

```python
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_data",
    username="user",
    password="pass",
)
```

### to_mysql

Export to a MySQL database.

```python
view.export.to_mysql(
    host: str,
    port: int,
    database: str,
    table: str,
    username: str,
    password: str,
    **kwargs,
) -> dict[str, Any]
```

```python
view.export.to_mysql(
    host="mysql.example.com",
    port=3306,
    database="analytics",
    table="sales_data",
    username="user",
    password="pass",
)
```

### to_bigquery

Export to Google BigQuery.

```python
view.export.to_bigquery(**kwargs) -> dict[str, Any]
```

Pass BigQuery connection and table configuration as keyword arguments.

### to_redshift

Export to Amazon Redshift.

```python
view.export.to_redshift(**kwargs) -> dict[str, Any]
```

### to_elasticsearch

Export to Elasticsearch.

```python
view.export.to_elasticsearch(**kwargs) -> dict[str, Any]
```

### to_ftp

Export to an FTP server.

```python
view.export.to_ftp(
    host: str,
    path: str,
    username: str,
    password: str,
    port: int = 21,
    **kwargs,
) -> dict[str, Any]
```

### to_sftp

Export to an SFTP server.

```python
view.export.to_sftp(
    host: str,
    path: str,
    username: str,
    password: str,
    port: int = 22,
    **kwargs,
) -> dict[str, Any]
```

### to_email

Export via email.

```python
view.export.to_email(recipients: list[str], **kwargs) -> dict[str, Any]
```

```python
view.export.to_email(recipients=["analyst@example.com", "team@example.com"])
```

### to_dataset

Export to another Mammoth dataset (branch out).

```python
view.export.to_dataset(
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    **kwargs,
) -> dict[str, Any]
```

```python
view.export.to_dataset(dest_dataset_id=42)
view.export.to_dataset(
    dest_dataset_id=42,
    column_mapping={"Sales": "revenue", "Region": "area"},
)
```

### publish_to_db

Publish the dataview to a database.

```python
view.export.publish_to_db(**kwargs) -> dict[str, Any]
```

### list

List all exports for this dataview.

```python
exports = view.export.list()
for exp in exports:
    print(exp["id"], exp["handler_type"])
```

### delete

Delete an export by ID.

```python
view.export.delete(export_id=123)
```

## branch_out (View method)

Convenience method on the View itself. Equivalent to `view.export.to_dataset()`.

```python
view.branch_out(
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    **kwargs,
) -> dict[str, Any]
```

```python
view.branch_out(dest_dataset_id=42)
```

---

## ExportsAPI

Lower-level export operations available via `client.exports`. These methods require explicit IDs rather than working through a View object.

### client.exports.to_csv

Download dataview data as CSV.

```python
client.exports.to_csv(
    dataview_id: int,
    output_path: str | Path | None = None,
    timeout: int = 300,
    dataset_id: int | None = None,
) -> Path
```

```python
path = client.exports.to_csv(dataview_id=1039, output_path="export.csv")
```

### client.exports.to_s3

Create an S3 export. Waits for job completion and returns the download URL.

```python
client.exports.to_s3(
    dataview_id: int,
    file: str | None = None,
    file_type: str = "csv",
    include_hidden: bool = False,
    dataset_id: int | None = None,
    ...,
) -> dict[str, Any]
```

```python
result = client.exports.to_s3(dataview_id=1039, file="report.csv")
print(result["url"])  # download URL
```

### client.exports.to_dataset

Create an internal dataset export (branch out).

```python
client.exports.to_dataset(
    dataview_id: int,
    dataset_name: str,
    column_mapping: dict[str, Any] | None = None,
    ...,
) -> PipelineExportsModificationResp | JobResponse
```

```python
client.exports.to_dataset(dataview_id=1039, dataset_name="processed_data")
```

### client.exports.list

List exports for a dataview with filtering and pagination.

```python
client.exports.list(
    dataview_id: int,
    fields: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
    status: ExportStatus | None = None,
    handler_type: HandlerType | None = None,
    ...,
) -> PipelineExportsPaginated
```

### client.exports.create

Create a new export with full control over the export specification.

```python
from mammoth.models.exports import AddExportSpec, HandlerType, TriggerType

spec = AddExportSpec(
    DATAVIEW_ID=1039,
    handler_type=HandlerType.S3,
    trigger_type=TriggerType.PIPELINE,
    target_properties={
        "file": "report.csv",
        "file_type": "csv",
        "include_hidden": False,
        "is_format_set": True,
        "use_format": True,
    },
    additional_properties={},
    condition={},
    run_immediately=True,
    validate_only=False,
)

result = client.exports.create(
    dataview_id=1039,
    export_spec=spec,
    dataset_id=42,
)
```

## Export workflow example

```python
from mammoth import MammothClient, Condition, Operator

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# Get a view and transform it
view = client.views.get(1039)
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Export to CSV locally
csv_path = view.export.to_csv("filtered_sales.csv")
print(f"CSV saved to {csv_path}")

# Export to S3
s3_result = view.export.to_s3(file_name="filtered_sales.csv")

# Export to PostgreSQL
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="filtered_sales",
    username="user",
    password="pass",
)

# Branch out to another dataset
view.branch_out(dest_dataset_id=42)
```

## See also

- [Views](views.md) -- View object and transformation methods
- [Client](client.md) -- MammothClient and sub-clients
