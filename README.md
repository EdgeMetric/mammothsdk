# Mammoth Python SDK

Python SDK for the Mammoth Analytics platform with simplified API design.

## Installation

```bash
pip install git+ssh://git@github.com/EdgeMetric/mm-pysdk.git
```

## Quick Start

### 1. Client Setup

```python
from mammoth import MammothClient, parse_path

# Method 1: Direct initialization
client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
    base_url="https://mirai.mammoth.io/api/v2"
)
client.set_project_id(426)

# Method 2: Extract from URL
url = "https://mirai.mammoth.io/#/workspaces/11/projects/426/views/1707"
parsed_ids = parse_path(url)

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret", 
    workspace_id=parsed_ids['workspace_id'],
    base_url="https://mirai.mammoth.io/api/v2"
)
client.set_project_id(parsed_ids['project_id'])
```

### 2. Upload Files

```python
# Upload single file
dataset_id = client.files.upload_files(files="data.csv")

# Upload multiple files 
dataset_ids = client.files.upload_files(files=["file1.csv", "file2.xlsx"])

# Upload folder
dataset_ids = client.files.upload_folder(folder_path="./data_folder")
```

### 3. Download Data

```python
# Download dataview as CSV (use existing dataview_id you have access to)
csv_file = client.exports.download_dataview_csv(
    dataview_id=1707,  # Replace with your dataview_id
    output_path="./export.csv"
)

# Create S3 export
s3_result = client.exports.create_s3_export(dataview_id=1707)  # Replace with your dataview_id
print(f"URL: {s3_result['url']}")
```

## Working with Uploaded Files

### Use Dataset ID from Upload

```python
# Upload file and get dataset_id
dataset_id = client.files.upload_files(files="sales_data.csv")

# List dataviews in the dataset
dataviews = client.dataviews.list_dataviews(dataset_id=dataset_id)
dataview_id = dataviews['dataviews'][0]['id']

# Download processed data
csv_file = client.exports.download_dataview_csv(
    dataview_id=dataview_id,
    dataset_id=dataset_id,  # Use known dataset_id
    output_path="./processed_sales.csv"
)

# Create S3 export for the dataview
s3_result = client.exports.create_s3_export(
    dataview_id=dataview_id,
    dataset_id=dataset_id,  # Use known dataset_id
    file="automated_export.csv"
)
```

### File Management

```python
# List uploaded files
files = client.files.list_files(limit=10)
for file in files.files:
    print(f"File: {file.name} - Status: {file.status}")

# Get file details
file_details = client.files.get_file_details(file_id=123)

# Delete files
client.files.delete_file(file_id=123)
client.files.delete_files(file_ids=[123, 124, 125])
```

### Complete Workflow Example

```python
from mammoth import MammothClient, parse_path

# Initialize from URL
url = "https://mirai.mammoth.io/#/workspaces/11/projects/426/views/1707"
parsed_ids = parse_path(url)

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=parsed_ids['workspace_id'],
    base_url="https://mirai.mammoth.io/api/v2"
)
client.set_project_id(parsed_ids['project_id'])

# Upload → Process → Export workflow
dataset_id = client.files.upload_files(files="data.csv")
dataviews = client.dataviews.list_dataviews(dataset_id=dataset_id)
dataview_id = dataviews['dataviews'][0]['id']

# Download processed CSV
csv_file = client.exports.download_dataview_csv(
    dataview_id=dataview_id,
    dataset_id=dataset_id,
    output_path="./processed.csv"
)

# Create automated S3 export
s3_result = client.exports.create_s3_export(
    dataview_id=dataview_id,
    dataset_id=dataset_id,
    file="daily_export.csv"
)
print(f"Export URL: {s3_result['url']}")
```

### Dataset Operations

```python
# List all datasets
datasets = client.datasets.list_datasets(limit=20)
for dataset in datasets['datasets']:
    print(f"Dataset: {dataset['name']} (ID: {dataset['id']})")

# Get dataset details
dataset_info = client.datasets.get_dataset(dataset_id=1576)
print(f"Rows: {dataset_info.row_count}, Columns: {dataset_info.column_count}")
```

### Export Management

```python
# List exports for a dataview
exports = client.exports.list_exports(
    dataview_id=dataview_id,  # Use your dataview_id
    status="active"
)

# Create internal dataset export (copy data)
dataset_export = client.exports.create_internal_dataset_export(
    dataview_id=dataview_id,  # Use your dataview_id  
    dataset_id=dataset_id,    # Use your dataset_id
    dataset_name="Customer Analysis Copy"
)
```

## Async Operations

```python
# Start upload without waiting
job_id = client.files.upload_files(
    files="large_file.csv",
    wait_for_completion=False
)

# Check status later
job_status = client.jobs.get_job(job_id)
completed_job = client.jobs.wait_for_job(job_id, timeout=600)
```

## Key APIs

| Method | Description |
|--------|-------------|
| `client.files.upload_files()` | Upload files, create datasets |
| `client.files.upload_folder()` | Upload folder structure |
| `client.exports.download_dataview_csv()` | Download as CSV |
| `client.exports.create_s3_export()` | Create S3 export |
| `client.dataviews.list_dataviews()` | List dataviews |
| `client.jobs.wait_for_job()` | Wait for async jobs |

## Error Handling

```python
from mammoth.exceptions import MammothAPIError, MammothJobTimeoutError

try:
    dataset_id = client.files.upload_files(files="data.csv")
except MammothJobTimeoutError:
    print("Upload timed out")
except MammothAPIError as e:
    print(f"API error: {e}")
```

## Support

- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mm-pysdk/issues)
- **Documentation**: [https://mammoth.io/docs](https://mammoth.io/docs)