# Files API Reference

The `FilesAPI` manages file uploads, listing, and deletion.

**Access**: `client.files`

```python
# Upload a CSV file
result = client.files.upload("data.csv", dataset_name="Sales Data")

# Upload an Excel file
result = client.files.upload("report.xlsx", dataset_name="Report")
```

---

::: mammoth.api.files.FilesAPI
    options:
      show_root_heading: true
      heading_level: 2
