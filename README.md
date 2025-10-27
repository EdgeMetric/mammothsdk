# Mammoth Python SDK

A production-ready Python SDK for the Mammoth Analytics platform, providing easy access to file management, dataset operations, and job tracking functionality.

## Features

- **Simple Authentication**: API key and secret-based authentication
- **File Management**: Upload, list, update, and delete files
- **Dataset Creation**: Automatic dataset creation from uploaded files
- **Job Tracking**: Comprehensive async job monitoring with automatic waiting
- **Type Safety**: Full type hints and Pydantic models for IDE support
- **Error Handling**: Comprehensive exception handling with detailed error information
- **Automatic Retries**: Built-in retry logic for robust API interactions

## Installation

### Using Poetry (Recommended)

```bash
poetry add git+ssh://git@github.com/EdgeMetric/mm-pysdk.git
```

### Using pip

```bash
pip install git+ssh://git@github.com/EdgeMetric/mm-pysdk.git
```

## Quick Start

```python
from mammoth import MammothClient

# Initialize client
client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    base_url="https://app.mammoth.io/api/v2"
)

# Upload a file and create dataset
dataset_id = client.files.upload_files(
    workspace_id=1,
    project_id=1,
    files="data.csv"
)

print(f"Created dataset: {dataset_id}")
```

## Common Use Cases

### 1. Upload File and Download as CSV

**Problem:** You have a raw data file (CSV, Excel, etc.) that you want to upload to Mammoth, let it process and standardize the data, then download the cleaned version as a CSV file for further analysis.

```python
from mammoth import MammothClient

# Initialize client
client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    base_url="https://app.mammoth.io/api/v2"
)

# Step 1: Upload a file and create dataset
dataset_id = client.files.upload_files(
    workspace_id=11,
    project_id=98,
    files="path/to/your/data.csv"
)
print(f"✅ Dataset created: {dataset_id}")

# Step 2: Get the dataset's dataviews
dataviews = client.dataviews.list_dataviews(
    dataset_id=dataset_id,
    workspace_id=11,
    project_id=98
)

# Step 3: Download the first dataview as CSV
if dataviews['dataviews']:
    dataview_id = dataviews['dataviews'][0]['id']
    
    csv_file = client.exports.download_dataview_csv(
        workspace_id=11,
        project_id=98,
        dataset_id=dataset_id,
        dataview_id=dataview_id,
        output_path="exported_data.csv"
    )
    print(f"✅ CSV exported to: {csv_file}")
```

### 2. Auto-detect Workspace and Project

**Problem:** You don't want to hardcode workspace and project IDs in your scripts. You want the SDK to automatically figure out which workspace and project to use based on your API credentials.

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    base_url="https://app.mammoth.io/api/v2"
)

# Auto-detect workspace ID
workspace_id = client.get_workspace_id()
print(f"Using workspace: {workspace_id}")

# Auto-detect or select project (if only one exists)
project = client.projects.get_project(workspace_id=workspace_id)
project_id = project['id']
print(f"Using project: {project_id} - {project['name']}")

# Upload file using auto-detected IDs
dataset_id = client.files.upload_files(
    workspace_id=workspace_id,
    project_id=project_id,
    files="data.csv"
)
```

### 3. Upload Multiple Files

**Problem:** You have several data files that need to be uploaded and processed together, or you want to maintain a folder structure in Mammoth that matches your local file organization.

```python
# Upload multiple files at once
dataset_ids = client.files.upload_files(
    workspace_id=11,
    project_id=98,
    files=["file1.csv", "file2.xlsx", "file3.json"]
)
print(f"Created datasets: {dataset_ids}")

# Or upload files in a folder structure
dataset_ids = client.files.upload_files(
    workspace_id=11,
    project_id=98,
    files=["data/sales.csv", "data/customers.csv"],
    folder_resource_id="folder_12345"  # Optional: target folder
)
```

### 4. Async Upload (Don't Wait)

**Problem:** You're uploading large files or multiple files and don't want your script to block waiting for completion. You want to start uploads and check their status later or handle multiple uploads in parallel.

```python
# Start upload without waiting for completion
job_id = client.files.upload_files(
    workspace_id=11,
    project_id=98,
    files="large_file.csv",
    wait_for_completion=False
)
print(f"Upload job started: {job_id}")

# Later, check job status
job_status = client.jobs.get_job(job_id, workspace_id=11)
print(f"Job status: {job_status['status']}")

# Wait for completion when ready
completed_job = client.jobs.wait_for_job(job_id, workspace_id=11)
print(f"Job completed: {completed_job}")
```

### 5. File Management

**Problem:** You need to browse, inspect, and manage files that have been uploaded to your Mammoth workspace. You want to see what files exist, check their processing status, and clean up old files.

```python
# List files in a project
files = client.files.list_files(
    workspace_id=11,
    project_id=98,
    limit=20,
    statuses=["ready", "processing"]
)
print(f"Found {len(files.files)} files")

# Get detailed file information
file_details = client.files.get_file_details(
    workspace_id=11,
    project_id=98,
    file_id=123
)
print(f"File: {file_details.name} - Status: {file_details.status}")

# Delete a file
client.files.delete_file(
    workspace_id=11,
    project_id=98,
    file_id=123
)
```

## Authentication

Get your API credentials from your Mammoth dashboard:

```python
client = MammothClient(
    api_key="your-api-key",      # X-API-KEY header
    api_secret="your-api-secret", # X-API-SECRET header
    base_url="https://app.mammoth.io/api/v2"  # Or your instance URL
)

# Test connection
if client.test_connection():
    print("Connected successfully!")
```

## Core Concepts

### Files vs Datasets
- **Files**: Raw uploaded files (CSV, Excel, etc.)
- **Datasets**: Processed, standardized data stored in Mammoth's warehouse
- When you upload a file, Mammoth processes it and creates a dataset

### Jobs
- Many operations are asynchronous and return job IDs
- Use the Jobs API to track progress and get results
- The SDK automatically handles job waiting for file uploads

## URL Parsing Helper

The SDK includes a helpful utility for extracting workspace, project, and dataview IDs directly from Mammoth URLs:

```python
from mammoth import parse_path

# Parse a Mammoth URL to extract IDs
url = "https://mirai.mammoth.io/#/workspaces/11/projects/426/views/1699"
parsed_ids = parse_path(url)

print(f"Workspace ID: {parsed_ids['workspace_id']}")  # 11
print(f"Project ID: {parsed_ids['project_id']}")      # 426
print(f"Dataview ID: {parsed_ids['dataview_id']}")    # 1699

# Use extracted IDs in API calls
client = MammothClient(api_key="...", api_secret="...", base_url="...")

# Export dataview using extracted IDs
csv_file = client.exports.download_dataview_csv(
    workspace_id=parsed_ids['workspace_id'],
    project_id=parsed_ids['project_id'],
    dataset_id=1576,  # You'll need to provide the dataset ID
    dataview_id=parsed_ids['dataview_id'],
    output_path="exported_data.csv"
)
```

## Advanced Examples

### Working with Exports

**Problem:** You want to set up automated data exports that trigger when your data is updated, or create different export formats (S3, internal datasets) for different use cases.

```python
from mammoth import MammothClient

client = MammothClient(api_key="...", api_secret="...", base_url="...")

# Create an S3 export for automated CSV generation
s3_export = client.exports.create_s3_export(
    workspace_id=11,
    project_id=98,
    dataset_id=1569,
    dataview_id=2847,
    file="daily_report.csv",
    file_type="csv",
    trigger_type="pipeline",  # Auto-trigger when data updates
    end_of_pipeline=True
)

# Create an internal dataset export (copy dataview to new dataset)
dataset_export = client.exports.create_internal_dataset_export(
    workspace_id=11,
    project_id=98,
    dataset_id=1569,
    dataview_id=2847,
    dataset_name="Processed Customer Data",
    column_mapping={"customer_id": "Customer ID", "revenue": "Total Revenue"}
)

# List all exports for a dataview
exports = client.exports.list_exports(
    workspace_id=11,
    project_id=98,
    dataset_id=1569,
    dataview_id=2847,
    status="active",
    handler_type="s3"
)
```

### Working with Datasets and Dataviews

**Problem:** You need to explore and understand the structure of your data in Mammoth. You want to see what datasets exist, what dataviews are available, and examine the schema/columns of your processed data.

```python
# List all datasets in a project
datasets = client.datasets.list_datasets(
    workspace_id=11,
    project_id=98,
    limit=50,
    sort="(created_at:desc)"
)

for dataset in datasets['datasets']:
    print(f"Dataset: {dataset['name']} (ID: {dataset['id']})")

# Get dataviews for a specific dataset
dataviews = client.dataviews.list_dataviews(
    dataset_id=1569,
    workspace_id=11,
    project_id=98
)

for dataview in dataviews['dataviews']:
    print(f"Dataview: {dataview['name']} (ID: {dataview['id']})")
    
    # Show column metadata
    for col in dataview.get('metadata', []):
        print(f"  - {col['display_name']} ({col['type']})")
```

### Job Monitoring and Batch Operations

**Problem:** You're processing multiple files or operations in parallel and need to efficiently track their progress. You want to start multiple jobs and wait for all of them to complete before proceeding.

```python
# Upload multiple files and track all jobs
job_ids = []
files = ["sales_q1.csv", "sales_q2.csv", "sales_q3.csv", "sales_q4.csv"]

for file in files:
    job_id = client.files.upload_files(
        workspace_id=11,
        project_id=98,
        files=file,
        wait_for_completion=False
    )
    job_ids.append(job_id)
    print(f"Started upload job for {file}: {job_id}")

# Wait for all jobs to complete
print("Waiting for all uploads to complete...")
completed_jobs = client.jobs.wait_for_jobs(job_ids, timeout=600)

print("All uploads completed!")
for job in completed_jobs['jobs']:
    print(f"Job {job['id']}: {job['status']}")
```

### Error Handling and Retry Logic

**Problem:** Your data processing pipeline needs to be robust and handle various failure scenarios gracefully. You want to catch specific errors, implement timeouts, and provide meaningful error messages.

```python
from mammoth.exceptions import MammothAPIError, MammothJobTimeoutError

try:
    # Upload with custom timeout
    dataset_id = client.files.upload_files(
        workspace_id=11,
        project_id=98,
        files="large_dataset.csv",
        timeout=600  # 10 minutes
    )
    
    # Export with error handling
    csv_file = client.exports.download_dataview_csv(
        workspace_id=11,
        project_id=98,
        dataset_id=dataset_id,
        dataview_id=2847,
        output_path="export.csv",
        timeout=300
    )
    
except MammothJobTimeoutError as e:
    print(f"Operation timed out: {e}")
    # Could implement retry logic here
    
except MammothAPIError as e:
    print(f"API error: {e}")
    # Handle API errors (auth, network, etc.)
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Complete Workflow Example

**Problem:** You want a complete, reusable function that handles the entire data processing workflow from upload to export, with proper error handling and status reporting.

```python
def process_data_pipeline(file_path: str, workspace_id: int, project_id: int):
    """Complete data processing pipeline: upload → process → export"""
    
    print(f"🚀 Starting data pipeline for: {file_path}")
    
    # Step 1: Upload file
    print("📤 Uploading file...")
    dataset_id = client.files.upload_files(
        workspace_id=workspace_id,
        project_id=project_id,
        files=file_path
    )
    print(f"✅ Dataset created: {dataset_id}")
    
    # Step 2: Get dataview
    print("🔍 Getting dataview...")
    dataviews = client.dataviews.list_dataviews(
        dataset_id=dataset_id,
        workspace_id=workspace_id,
        project_id=project_id
    )
    
    if not dataviews['dataviews']:
        raise ValueError("No dataviews found for dataset")
    
    dataview_id = dataviews['dataviews'][0]['id']
    print(f"✅ Using dataview: {dataview_id}")
    
    # Step 3: Export as CSV
    print("📥 Exporting to CSV...")
    output_file = f"processed_{dataset_id}.csv"
    csv_file = client.exports.download_dataview_csv(
        workspace_id=workspace_id,
        project_id=project_id,
        dataset_id=dataset_id,
        dataview_id=dataview_id,
        output_path=output_file
    )
    
    print(f"🎉 Pipeline complete! Output: {csv_file}")
    return csv_file

# Run the pipeline
result = process_data_pipeline("input_data.csv", 11, 98)
```

## API Reference Overview

The Mammoth Python SDK provides access to the following APIs:

### Core APIs
- **`client.files`** - Upload, list, update, and delete files
- **`client.datasets`** - Manage datasets and view dataset information
- **`client.dataviews`** - List and manage dataviews within datasets
- **`client.exports`** - Create exports, download CSV files, and manage export pipelines
- **`client.jobs`** - Track job status and wait for async operations

### Supporting APIs
- **`client.workspaces`** - Workspace management and information
- **`client.projects`** - Project management within workspaces
- **`client.folders`** - Folder structure management
- **`client.clientapps`** - Client application management

### Key Methods

| Method | Description |
|--------|-------------|
| `client.files.upload_files()` | Upload files and create datasets |
| `client.exports.download_dataview_csv()` | Download dataview as CSV |
| `client.dataviews.list_dataviews()` | Get dataviews for a dataset |
| `client.jobs.wait_for_job()` | Wait for async job completion |
| `client.get_workspace_id()` | Auto-detect workspace from credentials |
| `client.projects.get_project()` | Auto-detect or select project |

For detailed API documentation, see the [API Reference](docs) directory.

## [API Reference](docs)

## Support

- **Mammoth Analytics Documentation**: [https://mammoth.io/docs](https://mammoth.io/docs)
- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mm-pysdk/issues)

## License

MIT License - see LICENSE file for details.
