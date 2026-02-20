# API Sub-Clients Reference

All sub-clients are accessible as attributes of `MammothClient`. Most methods accept optional `workspace_id` and `project_id` parameters that default to the client's configured values.

---

## ViewsResource (`client.views`)

Returns rich **View** objects (not raw dicts).

```python
view = client.views.get(view_id)                           # View object
view = client.views.get(view_id, dataset_id=123)           # with explicit dataset
views = client.views.list(dataset_id)                       # list of View objects
view = client.views.create(dataset_id, name="My View")      # new View
client.views.delete(view_id, dataset_id)                    # delete
```

### View metadata attributes

After any transformation, `view.display_names`, `view.columns`, and `view.column_types` are automatically refreshed and include pipeline-added columns:

```python
view.math(expression="Price * 1.1", new_column="adj_price")
print("adj_price" in view.display_names)    # True
print(view.columns["adj_price"])            # "column_xyzabc1234" (internal name)
print(view.column_types["adj_price"])       # "NUMERIC"
```

### `view.get_metadata()`

Returns the full column list as a list of dicts — useful for debugging column resolution after transforms:

```python
for col in view.get_metadata():
    print(col)
# {"display_name": "adj_price", "internal_name": "column_xyzabc1234", "type": "NUMERIC"}
```

> **How it works:** column metadata is read from `taskwise_info[last_seq]["metadata"]` in the API response — the highest sequence number is the last task, and its `metadata` list is the complete post-pipeline column list. For fresh views with no tasks yet, `taskwise_info` is null so the top-level `metadata` field is used instead.

### View attributes & metadata

`view.display_names`, `view.columns`, and `view.column_types` are automatically
refreshed after **every** transformation — including columns added by pipeline
tasks (`math`, `set_values`, `add_column`, etc.).

```python
view.display_names   # ["Sales", "Region", "Revenue"]  — updated after each transform
view.columns         # {"Sales": "column_1", ...}
view.column_types    # {"Sales": "NUMERIC", ...}

# Inspect full column list with types (useful after transforms):
meta = view.get_metadata()
# [{"display_name": "Revenue", "internal_name": "column_x1y2z3", "type": "NUMERIC"}, ...]

# Force re-fetch from API:
view.refresh()
```

**Implementation note:** After a transformation the API places new columns in
`dependencies_info.dependents[str(view_id)]["METADATA"]`, not in the top-level
`metadata` field. The SDK reads from that path so new columns are always visible.

---

## ProjectsAPI (`client.projects`)

```python
projects = client.projects.list()                           # list all projects
project = client.projects.get(project_id=10)                # get one
project = client.projects.create(config={...})              # create
client.projects.update(project_id=10, config={...})         # update
client.projects.delete(project_id=10)                       # delete
```

---

## DatasetsAPI (`client.datasets`)

```python
datasets = client.datasets.list()                            # list all
dataset = client.datasets.get(dataset_id=123)                # get one
client.datasets.delete(dataset_id=123)                       # delete
batches = client.datasets.list_batches(dataset_id=123)       # list data batches
```

---

## FilesAPI (`client.files`)

```python
# Upload a file (returns dataset_id)
ds_id = client.files.upload("path/to/data.csv")

# Upload with folder
ds_id = client.files.upload("data.csv", folder_id=5)

# List files
files = client.files.list()

# Delete
client.files.delete(file_id=42)
```

---

## DataviewsAPI (`client.dataviews`)

Low-level dataview operations (prefer `client.views` for rich View objects).

```python
# List dataviews in a dataset
dataviews = client.dataviews.list(dataset_id=123)

# Get dataview with full metadata
dv = client.dataviews.get(dataset_id=123, dataview_id=456)

# Query data with filters
data = client.dataviews.query_data(
    dataset_id=123, dataview_id=456,
    limit=100, offset=1,
    columns=["column_1", "column_2"],  # internal names
)

# Create a new dataview
dv = client.dataviews.create(dataset_id=123, name="New View")

# Delete
client.dataviews.delete(dataset_id=123, dataview_id=456)

# Draft mode
client.dataviews.draft_mode(dataset_id=123, dataview_id=456, command="enable")
```

---

## PipelineAPI (`client.pipeline`)

Low-level pipeline task management (prefer View transformation methods for high-level use).

```python
# List pipeline tasks
tasks = client.pipeline.list_tasks(dataview_id=456, dataset_id=123)

# Add a task (raw spec)
result = client.pipeline.add_task(
    dataview_id=456,
    task_spec={"DELETE": ["column_1"]},
    dataset_id=123,
)

# Get/update/delete specific task
task = client.pipeline.get_task(dataview_id=456, task_id=789, dataset_id=123)
client.pipeline.delete_task(dataview_id=456, task_id=789, dataset_id=123)

# Preview a task without applying
preview = client.pipeline.preview_task(dataview_id=456, task_spec={...}, dataset_id=123)
```

---

## JobsAPI (`client.jobs`)

Track async job status.

```python
# Get job status
job = client.jobs.get_job(job_id=12345)

# Wait for job completion (blocks)
result = client.jobs.wait_for_job(job_id=12345)
result = client.jobs.wait_for_job(job_id=12345, timeout=120)

# Track multiple jobs
results = client.jobs.wait_for_jobs([12345, 12346])
```

Job statuses: `processing`, `success`, `failure`, `error`

---

## ExportsAPI (`client.exports`)

```python
# List exports for a dataview
exports = client.exports.list(dataview_id=456, dataset_id=123)

# Create export
result = client.exports.create(
    dataview_id=456,
    export_spec=spec,  # AddExportSpec model
    dataset_id=123,
)

# Download as CSV
path = client.exports.to_csv(dataview_id=456, output_path="data.csv", dataset_id=123)
```

Prefer using `view.export.to_csv()`, `view.export.to_postgres()`, etc. on View objects.

---

## FoldersAPI (`client.folders`)

```python
folders = client.folders.list()
folder = client.folders.create(name="Reports")
client.folders.delete(folder_id=5)
```

---

## ConnectorsAPI (`client.connectors`)

Third-party data connectors (databases, APIs, cloud services).

```python
connectors = client.connectors.list()
connector = client.connectors.get("postgres")
connections = client.connectors.list_connections("postgres")
conn = client.connectors.create_connection("postgres", config={...})
```

---

## DashboardsAPI (`client.dashboards`)

AI-powered dashboards.

```python
dashboards = client.dashboards.list()
dashboard = client.dashboards.create(config={...})
data = client.dashboards.get_publish_data(dashboard_id=1, sql="SELECT ...")
```

---

## WebhooksAPI (`client.webhooks`)

```python
webhooks = client.webhooks.list()
webhook = client.webhooks.create(config={...})
client.webhooks.delete(webhook_id=1)
```

---

## AutomationsAPI (`client.automations`)

Scheduled tasks and orchestration.

```python
automations = client.automations.list()
automation = client.automations.create(config={...})
schedules = client.automations.list_schedules()
```

---

## AIAPI (`client.ai`)

AI features.

```python
# Generate data profile
profile = client.ai.generate_profile(dataview_id=456)

# Generate synthetic data
data = client.ai.generate_data(dataview_id=456, columns=["Name", "Age"], num_rows=100)

# Get AI suggestions for a view
suggestions = client.ai.get_suggestions(dataview_id=456)
```

---

## WorkspaceAPI (`client.workspaces`)

```python
workspaces = client.workspaces.list()
workspace = client.workspaces.get(workspace_id=11)
users = client.workspaces.list_users()
```

---

## ClientAppsAPI (`client.client_apps`)

```python
apps = client.client_apps.list()
app = client.client_apps.create(config={...})
```

---

## Convenience Methods on MammothClient

```python
# Quick access to View object
view = client.get_view(view_id=1039)
view = client.get_view(view_id=1039, dataset_id=123)

# Branch out (export view to another dataset)
client.branch_out(view_id=1039, dest_dataset_id=42)
```
