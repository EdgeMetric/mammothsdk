# Datasets API Reference

The `DatasetsAPI` manages datasets within a project. A dataset is a data table stored in Mammoth, created from file uploads, connectors, or cloning.

**Access**: `client.datasets`

```python
# List datasets in the current project
datasets = client.datasets.list()

# Get a specific dataset
ds = client.datasets.get(dataset_id=42)
```

---

::: mammoth.api.datasets.DatasetsAPI
    options:
      show_root_heading: true
      heading_level: 2
