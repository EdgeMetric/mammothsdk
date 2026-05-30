# Exports Reference

The SDK provides two ways to export data:

1. **ViewExport** (`view.export`) -- export methods attached to a View object
2. **ExportsAPI** (`client.exports`) -- lower-level export operations

## Quick examples

```python
# Download as CSV
path = view.export.to_csv("output.csv")

# Export to S3
view.export.to_s3(file_name="report.csv")

# Export to PostgreSQL
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="sales",
    username="user", password="pass",
)

# Branch out to another dataset
view.branch_out(dest_dataset_id=42)

# List and delete exports
exports = view.export.list()
view.export.delete(exports[0]["id"])
```

!!! note "External service exports"
    Methods like `to_postgres`, `to_mysql`, `to_ftp`, `to_sftp`, `to_email`, `to_bigquery`, `to_redshift`, and `to_elasticsearch` require pre-configured external services accessible from the Mammoth platform.

---

## ViewExport API Reference

::: mammoth.view.ViewExport
    options:
      members:
        - to_csv
        - to_s3
        - to_postgres
        - to_mysql
        - to_dataset
        - to_ftp
        - to_sftp
        - to_email
        - to_bigquery
        - to_redshift
        - to_elasticsearch
        - publish_to_db
        - list
        - delete

---

## ExportsAPI (low-level)

The `client.exports` sub-client provides lower-level export operations. Most users should prefer the `ViewExport` methods above.

::: mammoth.api.exports.ExportsAPI
    options:
      show_root_heading: true
      heading_level: 3

## See also

- [Views](views.md) -- View object and transformation methods
- [Client](client.md) -- sub-client overview
