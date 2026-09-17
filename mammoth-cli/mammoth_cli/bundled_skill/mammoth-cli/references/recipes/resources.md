# Files, datasets, views and settings

Discover exact contracts, then upload and read back explicit parents:

```bash
mammoth schema get file.upload --output json --no-input
mammoth file upload ./SOURCE.csv --project PROJECT_ID --output json --no-input
mammoth dataset list --project PROJECT_ID --output json --no-input
mammoth view list DATASET_ID --project PROJECT_ID --output json --no-input
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
```

Use display names from the exact view schema. For settings, folders and other
families, use `schema find`/`schema get` first. Snapshot all pre-existing
resource IDs by type; cleanup only IDs returned by this task.
