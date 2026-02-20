# Integrations

This guide demonstrates how to integrate the Mammoth SDK with external systems.

## Export to PostgreSQL

Use the View export to push data directly to a PostgreSQL database:

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

## Export to MySQL

```python
view.export.to_mysql(
    host="mysql.example.com",
    port=3306,
    database="warehouse",
    table="processed_data",
    username="user",
    password="pass",
)
```

## Export to S3

```python
result = view.export.to_s3(file_name="report.csv")
```

## Export to BigQuery

```python
view.export.to_bigquery(
    project="my-gcp-project",
    dataset="analytics",
    table="results",
    # additional BigQuery configuration as needed
)
```

## Import from external sources

Pull data from an external database and upload to Mammoth:

```python
import pandas as pd
from mammoth import MammothClient

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# 1. Export from your source database to CSV
df = pd.read_sql("SELECT * FROM customers WHERE status = 'active'", connection)
df.to_csv("customers.csv", index=False)

# 2. Upload to Mammoth
client.files.upload("customers.csv")
```

## Branch out to another dataset

Send processed data from one view to another Mammoth dataset:

```python
view.branch_out(dest_dataset_id=42)

# With column mapping
view.branch_out(
    dest_dataset_id=42,
    column_mapping={"Sales": "revenue", "Region": "area"},
)
```

## Webhook integration

Set up webhooks to receive notifications on pipeline events:

```python
webhooks = client.webhooks.list()
```

## Scheduled automation

Use automations and schedules for recurring workflows:

```python
schedules = client.schedules.list()
automations = client.automations.list()
```

## See also

- [Exports reference](../api/exports.md) -- all export destinations
- [Client API](../api/client.md) -- sub-clients for webhooks, automations, schedules
