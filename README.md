# Mammoth Python SDK

A Python SDK for programmatic access to Mammoth Analytics' services. Enables automated data workflows through file ingestion and flexible data export capabilities. Upload datasets directly to your workspace, then download transformed views as CSV files or push results to S3 storage. Designed for data engineers building automated pipelines and integrating Mammoth's transformation engine into existing data infrastructure.


## Installation

```bash
pip install git+ssh://git@github.com/EdgeMetric/mm-pysdk.git
```

## Quick Start

### 1. Create credentials for API access
- Log in to your Mammoth account.
- Navigate to **Workspace Settings > API Keys**.
- Create a new API key and secret for your workspace using the **Create Token** button.
- Give name of the token, description, and project where it will be used.
- Copy the generated **API Secret** as it will not be shown again.
- Click **Submit** to store the API key.
- Copy the **API Key**.
- Note down the **Workspace ID** and **Project ID** from the URL or settings.


### 2. Client Setup

```python
from mammoth import MammothClient

MAMMOTH_WORKSPACE_ID = <your_workspace_id>
MAMMOTH_PROJECT_ID = <your_project_id>
MAMMOTH_API_KEY = "<your_api_key>"
MAMMOTH_API_SECRET = "<your_api_secret>"
# Method 1: Direct initialization
client = MammothClient(
    api_key=MAMMOTH_API_KEY,
    api_secret=MAMMOTH_API_SECRET,
    workspace_id=MAMMOTH_WORKSPACE_ID,
)
client.set_project_id(MAMMOTH_PROJECT_ID)

# Method 2: Extract from URL
# You can also extract workspace and project IDs from a Mammoth URL
from mammoth import parse_path
url = "https://mirai.mammoth.io/#/workspaces/11/projects/426/views/1707"
parsed_ids = parse_path(url)
MAMMOTH_WORKSPACE_ID = parsed_ids['workspace_id']
MAMMOTH_PROJECT_ID = parsed_ids['project_id']
MAMMOTH_API_KEY = "<your_api_key>"
MAMMOTH_API_SECRET = "<your_api_secret>"

client = MammothClient(
    api_key=MAMMOTH_API_KEY,
    api_secret=MAMMOTH_API_SECRET,
    workspace_id=MAMMOTH_WORKSPACE_ID,
)
client.set_project_id(MAMMOTH_PROJECT_ID)
```

### 3. Upload Files

```python
# Upload single file
# Supported file types: .txt .csv .tsv .psv .xls .xlsx .zip .bz2 .gz .tar .7z .pdf .tiff .jpeg .jpg .png .heic .webp
# Maximum file size: 50MB
FILE_PATH = "<path/to/your/file.csv>"
dataset_id = client.files.upload_files(files=FILE_PATH)

# Upload multiple files
LIST_OF_FILES = ["file1.csv", "file2.xlsx"]
dataset_ids = client.files.upload_files(files=LIST_OF_FILES)

# Upload folder
folder_path = "<path/to/your/folder>"
dataset_ids = client.files.upload_folder(folder_path=folder_path)
```

### 4. Download Data as csv

```python
# Method 1: If you know view id
# Download view as CSV
VIEW_ID = <your_view_id>
output_path = "./exported_data.csv"
csv_file = client.exports.download_dataview_csv(
    dataview_id=VIEW_ID,
    output_path=output_path
)

# Method 2: If you know url of the view
url = "https://app.mammoth.io/#/workspaces/11/projects/426/views/1707"
parsed_ids = parse_path(url)
VIEW_ID = parsed_ids['dataview_id']
csv_file = client.exports.download_dataview_csv(
    dataview_id=VIEW_ID,
    output_path=output_path
)



```

### 5. Create S3 Export

```python
# Method 1: If you know view id
VIEW_ID = <your_view_id>
# Create S3 export for a dataview
s3_result = client.exports.create_s3_export(
    dataview_id=VIEW_ID,
    file="exported_data.csv"
)
print(f"Export URL: {s3_result['url']}")  

# Method 2: If you know url of the view
url = "https://app.mammoth.io/#/workspaces/11/projects/426/views/1707"
parsed_ids = parse_path(url)
VIEW_ID = parsed_ids['dataview_id']
s3_result = client.exports.create_s3_export(
    dataview_id=VIEW_ID,
    file="exported_data.csv"
)
print(f"Export URL: {s3_result['url']}")
```

## Working with Uploaded Files

### Exporting uploaded files to s3

```python
# Upload file and get dataset_id
FILE_PATH = "sales_data.csv"
dataset_id = client.files.upload_files(files=FILE_PATH)

# List views in the dataset
views = client.dataviews.list_dataviews(dataset_id=dataset_id)
# By default, one view is created for a dataset, pick the first view
view_id = views['dataviews'][0]['id']

# Download processed data
csv_file = client.exports.download_dataview_csv(
    dataview_id=view_id,
    dataset_id=dataset_id,  # Use known dataset_id
    output_path="./processed_sales.csv"
)

# Create S3 export for the dataview
s3_result = client.exports.create_s3_export(
    dataview_id=view_id,
    dataset_id=dataset_id,  # Use known dataset_id
    file="automated_export.csv"
)
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

## Key APIs

| Method | Description |
|--------|-------------|
| `client.files.upload_files()` | Upload files, create datasets |
| `client.files.upload_folder()` | Upload folder structure |
| `client.exports.download_dataview_csv()` | Download as CSV |
| `client.exports.create_s3_export()` | Create S3 export |
| `client.dataviews.list_dataviews()` | List dataviews |
| `client.jobs.wait_for_job()` | Wait for async jobs |


## Support

- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mm-pysdk/issues)
- **Documentation**: [https://mammoth.io/docs](https://mammoth.io/docs)