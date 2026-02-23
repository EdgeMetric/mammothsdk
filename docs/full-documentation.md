# Mammoth Analytics Python SDK

**Version 0.3.0** | Python 3.10+ | [PyPI](https://pypi.org/project/mammoth-io/) | [GitHub](https://github.com/EdgeMetric/mm-pysdk)

The official Python SDK for the [Mammoth Analytics](https://mammoth.io) platform. Build data pipelines, apply transformations, and export results -- all from Python.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Authentication](#authentication)
- [Client](#client)
- [Views](#views)
- [Conditions](#conditions)
- [Transformations](#transformations)
- [Exports](#exports)
- [Files API](#files-api)
- [Enums & Data Classes](#enums--data-classes)
- [Exceptions](#exceptions)
- [Cookbook](#cookbook)
- [Configuration & Troubleshooting](#configuration--troubleshooting)

---

## Overview

The Mammoth Python SDK provides a rich, Pythonic interface to the Mammoth Analytics platform. It wraps the REST API with typed View objects, operator-overloaded condition builders, and export helpers so you can build complete data pipelines from Python.

### Features

- **MammothClient** -- single entry point with organized sub-clients for every API resource
- **View objects** -- rich domain objects with 25+ transformation methods (filter, set, join, pivot, window, math, and more)
- **Condition builder** -- Pythonic filter conditions with `&` (AND), `|` (OR), and `~` (NOT) operator overloading
- **Export helpers** -- download CSV, push to S3, PostgreSQL, BigQuery, and other destinations
- **Type safety** -- full type hints, enums for all parameters, Pydantic models for responses
- **MCP server** -- optional Model Context Protocol server for AI-assisted analytics (separate package)

### Quick example

```python
from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)

# Get a View and apply transformations
view = client.views.get(1039)
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)

# Export results
view.export.to_csv("output.csv")
```

---

## Installation

### Requirements

- Python 3.10 or higher
- pip or Poetry package manager

### Install from PyPI

```bash
pip install mammoth-io
```

Or with Poetry:

```bash
poetry add mammoth-io
```

### Dependencies

The SDK has two runtime dependencies, installed automatically:

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | ^2.32.0 | HTTP client for API requests |
| `pydantic` | ^2.11.0 | Data validation and response models |

### Development installation

Clone the repository and install with dev dependencies:

```bash
git clone https://github.com/EdgeMetric/mm-pysdk.git
cd mm-pysdk
poetry install
```

Or install the dev extras via pip:

```bash
pip install mammoth-io[dev]
```

### Verify installation

```python
from mammoth import MammothClient

print("Mammoth SDK installed successfully!")
```

---

## Authentication

The Mammoth SDK uses API key and secret-based authentication. Every request includes your credentials in HTTP headers automatically.

### Getting API credentials

1. Log in to your Mammoth Analytics dashboard
2. Navigate to your profile settings
3. Generate or retrieve your API key and secret
4. Store these credentials securely

### Client setup

**Direct authentication:**

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)
```

**Environment variables (recommended):**

```bash
export MAMMOTH_API_KEY="your-api-key"
export MAMMOTH_API_SECRET="your-api-secret"
```

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
```

**Configuration file:**

```python
# config.py
import os

MAMMOTH_CONFIG = {
    "api_key": os.getenv("MAMMOTH_API_KEY"),
    "api_secret": os.getenv("MAMMOTH_API_SECRET"),
    "workspace_id": int(os.getenv("MAMMOTH_WORKSPACE_ID", "11")),
    "base_url": os.getenv("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
}
```

```python
from mammoth import MammothClient
from config import MAMMOTH_CONFIG

client = MammothClient(**MAMMOTH_CONFIG)
```

### Authentication headers

The client adds these headers to every request automatically:

| Header | Value |
|--------|-------|
| `X-API-KEY` | Your API key |
| `X-API-SECRET` | Your API secret |
| `X-WORKSPACE-ID` | Your workspace ID |
| `User-Agent` | `mammoth-io/0.3.0` |

### Error handling

Authentication errors raise `MammothAuthError` (HTTP 401):

```python
from mammoth import MammothClient, MammothAuthError

try:
    client = MammothClient(
        api_key="invalid-key",
        api_secret="invalid-secret",
        workspace_id=1,
    )
    projects = client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API credentials")
```

### Security best practices

- **Never hardcode credentials** -- use environment variables or a secrets manager
- **Use different credentials per environment** -- separate dev, staging, and production keys
- **Rotate credentials regularly** -- regenerate API keys periodically and invalidate old ones
- **Do not commit credentials** -- add `.env` and config files with secrets to `.gitignore`

---

## Client

The `MammothClient` is the single entry point for all Mammoth API interactions. It manages authentication, provides organized sub-clients for every resource, and supports context manager usage.

### Constructor

```python
from mammoth import MammothClient

client = MammothClient(
    api_key: str,
    api_secret: str,
    workspace_id: int,
    base_url: str = "https://app.mammoth.io/api/v2",
    timeout: int = 30,
    job_timeout: int = 60,
    pipeline_timeout: int = 3600,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | *required* | Your Mammoth API key |
| `api_secret` | `str` | *required* | Your Mammoth API secret |
| `workspace_id` | `int` | *required* | Your Mammoth workspace ID |
| `base_url` | `str` | `"https://app.mammoth.io/api/v2"` | Base URL for the Mammoth API |
| `timeout` | `int` | `30` | Request timeout in seconds for individual HTTP calls |
| `job_timeout` | `int` | `60` | Maximum time in seconds to poll a job to completion |
| `pipeline_timeout` | `int` | `3600` | Maximum time in seconds to wait for pipeline tasks |

> **Note:** The SDK does **not** implement automatic retries. If an API call fails, the error is raised immediately. Implement retry logic in your application if needed.

### Methods

#### set_project_id

```python
client.set_project_id(project_id: int) -> None
```

Set the default project ID for the client. Required before most operations (listing datasets, working with views, running pipeline tasks, etc.).

```python
client.set_project_id(10)
```

#### get_view

```python
client.get_view(view_id: int, dataset_id: int | None = None) -> View
```

Shortcut for `client.views.get(view_id)`. Returns a rich [View](#views) object.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `view_id` | `int` | *required* | ID of the dataview |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected if not provided) |

```python
view = client.get_view(1039)
print(view.display_names)
```

#### find_dataset_for_dataview

```python
client.find_dataset_for_dataview(dataview_id: int) -> int
```

Searches all datasets in the current project to find which one contains the specified dataview. Returns the dataset ID.

```python
dataset_id = client.find_dataset_for_dataview(1039)
```

#### branch_out

```python
client.branch_out(
    view_id: int,
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    dataset_id: int | None = None,
    **kwargs,
) -> dict[str, Any]
```

Branch out (export) a view to another dataset. Convenience wrapper around `view.branch_out()`.

#### test_connection

```python
client.test_connection() -> bool
```

Test connectivity and authentication. Returns `True` if the API is reachable and credentials are valid, `False` otherwise.

### Context manager

The client supports Python's context manager protocol. The HTTP session is closed automatically on exit:

```python
with MammothClient(
    api_key="...", api_secret="...", workspace_id=11
) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.export.to_csv("output.csv")
# Session closed automatically
```

### Sub-clients

All API resources are accessible as attributes on the client. Each sub-client handles a specific area of the Mammoth API.

**Core data sub-clients:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.views` | `ViewsResource` | Rich View objects with transformations |
| `client.datasets` | `DatasetsAPI` | Dataset CRUD operations |
| `client.dataviews` | `DataviewsAPI` | Low-level dataview operations |
| `client.pipeline` | `PipelineAPI` | Pipeline task management |
| `client.files` | `FilesAPI` | File upload and management |
| `client.exports` | `ExportsAPI` | Export operations |
| `client.jobs` | `JobsAPI` | Asynchronous job tracking |
| `client.projects` | `ProjectsAPI` | Project CRUD |

**Additional sub-clients:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.ai` | `AIAPI` | AI/LLM operations |
| `client.connectors` | `ConnectorsAPI` | Data source connectors |
| `client.dashboards` | `DashboardsAPI` | Dashboard management |
| `client.webhooks` | `WebhooksAPI` | Webhook configuration |
| `client.automations` | `AutomationsAPI` | Automation workflows |
| `client.schedules` | `SchedulesAPI` | Scheduled operations |
| `client.batches` | `BatchesAPI` | Batch operations |
| `client.folders` | `FoldersAPI` | Folder management |
| `client.workspaces` | `WorkspaceAPI` | Workspace operations |
| `client.user_profile` | `UserProfileAPI` | User profile |
| `client.activity_logs` | `ActivityLogsAPI` | Activity logs |
| `client.browse` | `BrowseAPI` | Browse/search API |
| `client.external_keys` | `ExternalKeysAPI` | External key management |
| `client.client_apps` | `ClientAppsAPI` | Client app management |
| `client.addons` | `AddonsAPI` | Addons |
| `client.reports` | `ReportsAPI` | Reports |

### ViewsResource

The `client.views` sub-client returns rich [View](#views) objects (not raw dicts):

```python
# Get a single view
view = client.views.get(view_id=1039)

# List all views in a dataset
views = client.views.list(dataset_id=42)

# List all views across all datasets in the project
views = client.views.list()

# Create a new view
view = client.views.create(dataset_id=42, name="My Analysis")

# Clone from an existing view
view = client.views.create(dataset_id=42, name="Copy", clone_from=1039)

# Delete a view
client.views.delete(view_id=1039)

# Bulk delete
client.views.bulk_delete(view_ids=[1039, 1040], dataset_id=42)
```

### Error handling

The client raises specific exceptions for different error types:

| Exception | Trigger |
|-----------|---------|
| `MammothAuthError` | HTTP 401 (invalid credentials) |
| `MammothAPIError` | HTTP 4xx/5xx responses, network errors, timeouts |

```python
from mammoth import MammothClient, MammothAPIError, MammothAuthError

try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    client.set_project_id(10)
    datasets = client.datasets.list()
except MammothAuthError:
    print("Invalid credentials")
except MammothAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

---

## Views

The `View` class is the central interface for data transformations in the Mammoth SDK. It wraps a single dataview and provides 25+ transformation methods, data access, pipeline management, and export helpers.

### Getting a View

Views are created via `client.views.get()` -- not instantiated directly:

```python
from mammoth import MammothClient

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

view = client.views.get(1039)
```

You can also list, create, and delete views:

```python
# List all views in the project
views = client.views.list()

# Create a new view
view = client.views.create(dataset_id=42, name="My Analysis")

# Create by cloning
view = client.views.create(dataset_id=42, name="Copy", clone_from=1039)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `int` | Dataview ID |
| `name` | `str` | Dataview display name |
| `dataset_id` | `int` | Parent dataset ID |
| `columns` | `dict[str, str]` | Mapping of display names to internal names |
| `display_names` | `list[str]` | Ordered list of column display names |
| `column_types` | `dict[str, str]` | Mapping of display names to types (`TEXT`, `NUMERIC`, `DATE`) |
| `raw` | `dict` | Full raw API response dict |
| `export` | `ViewExport` | Export helper (see [Exports](#exports)) |

After every transformation, `display_names`, `columns`, and `column_types` are automatically refreshed -- including columns added by pipeline tasks (`math`, `set_values`, `add_column`, etc.).

```python
view = client.views.get(1039)

print(view.id)             # 1039
print(view.name)           # "Sales Data"
print(view.display_names)  # ["Sales", "Region", "Date"]
print(view.columns)        # {"Sales": "column_1", "Region": "column_2", ...}
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", "Date": "DATE"}

# After a transform, new columns appear immediately:
view.math("Sales * 1.1", new_column="Revenue")
print("Revenue" in view.display_names)   # True
```

### Data access

#### data()

Fetch rows from the dataview.

```python
view.data(
    limit: int = 400,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
    sort: str | None = None,
) -> dict[str, Any]
```

Returns a dict with two keys:

- `"data"` -- list of row dicts (keys are internal column names like `"column_1"`)
- `"paging"` -- pagination info

```python
# Fetch first 100 rows
result = view.data(limit=100)
rows = result["data"]       # list of row dicts
print(len(rows))            # number of rows returned

# Fetch specific columns
result = view.data(columns=["Sales", "Region"])

# Fetch with a filter
result = view.data(condition=Condition("Sales", Operator.GTE, 1000))
```

#### get_metadata()

Return the current column list as a list of dicts. Useful for inspecting the full column state after transformations.

```python
meta = view.get_metadata()
# [
#   {"display_name": "Sales", "internal_name": "column_1", "type": "NUMERIC"},
#   {"display_name": "Revenue", "internal_name": "column_xyzabc", "type": "NUMERIC"},
#   ...
# ]
```

#### refresh()

Re-fetch metadata from the API and update local state. Returns `self` for chaining.

```python
view.refresh()
```

### Pipeline management

#### list_tasks()

List all pipeline tasks on this dataview.

```python
tasks = view.list_tasks()
for task in tasks:
    print(task["id"], task["task_key"])
```

#### delete_task()

Delete a pipeline task by ID. Refreshes view metadata after deletion.

```python
view.delete_task(task_id=42)
```

#### preview_task()

Preview a task without applying it.

```python
preview = view.preview_task({"SELECT": "ALL", "CONDITION": {...}})
```

#### get_column_mapping()

Return a copy of the display-name-to-internal-name mapping.

```python
mapping = view.get_column_mapping()
# {"Sales": "column_1", "Region": "column_2", ...}
```

### Draft mode

By default, each transformation triggers an immediate pipeline run (auto-run mode). For large datasets or multi-step workflows, use **draft mode** to queue tasks and run the pipeline once.

#### draft() (context manager)

The recommended approach. Enters draft mode on entry, submits and runs on clean exit, discards on exception:

```python
with view.draft():
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.math("Price * 2", new_column="Double")
    view.add_column("Notes")
# Pipeline runs once for all 3 tasks, metadata refreshed
```

If an exception occurs inside the block, all queued tasks are discarded:

```python
try:
    with view.draft():
        view.add_column("Temp")
        raise ValueError("something went wrong")
except ValueError:
    pass  # "Temp" column was NOT added — draft was discarded
```

#### enter_draft_mode()

Enter draft mode explicitly. All subsequent `_add_task()` calls skip pipeline execution.

```python
view.enter_draft_mode() -> dict[str, Any]
```

#### submit_draft()

Submit queued tasks, run the pipeline, refresh metadata, and exit draft mode.

```python
view.submit_draft() -> dict[str, Any]
```

#### discard_draft()

Discard all queued tasks, exit draft mode, and refresh metadata to the pre-draft state.

```python
view.discard_draft() -> dict[str, Any]
```

#### set_auto_run()

Toggle auto-run on the pipeline. When disabled (`False`), the view enters draft mode and tasks are queued. When re-enabled (`True`), the view returns to auto-run mode.

```python
view.set_auto_run(enabled: bool) -> dict[str, Any]

view.set_auto_run(False)   # enter draft mode
view.set_auto_run(True)    # back to auto-run
```

#### is_draft_mode (property)

Check whether the view is currently in draft mode.

```python
if view.is_draft_mode:
    print("Tasks are being queued")
```

#### Explicit draft workflow

```python
view.enter_draft_mode()
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Price * 2", new_column="Double")
view.submit_draft()  # pipeline runs once, metadata refreshed
```

---

## Conditions

The condition module provides a Pythonic filter builder with operator overloading. Build conditions using `Condition` objects, combine them with `&` (AND), `|` (OR), and `~` (NOT), and pass them to View transformation methods.

### Condition

A single-column condition.

```python
from mammoth import Condition, Operator

Condition(
    column: str,
    operator: Operator | str,
    value: Any = None,
    case_sensitive: bool | None = None,
    value_is_column: bool = False,
    component: str | None = None,
    truncate: str | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column` | `str` | *required* | Display name of the column |
| `operator` | `Operator \| str` | *required* | Comparison operator (enum or raw string) |
| `value` | `Any` | `None` | Comparison value (omit for `IS_EMPTY` / `IS_NOT_EMPTY`) |
| `case_sensitive` | `bool \| None` | `None` | `None` = backend default (case-sensitive), `True` = case-sensitive, `False` = case-insensitive |
| `value_is_column` | `bool` | `False` | If `True`, `value` is treated as a column name for column-to-column comparison |
| `component` | `str \| None` | `None` | Date component for date-aware comparisons |
| `truncate` | `str \| None` | `None` | Date truncation level for date comparisons |

**Examples:**

```python
from mammoth import Condition, Operator

# Numeric comparisons
high_sales = Condition("Sales", Operator.GTE, 10000)
low_price = Condition("Price", Operator.LT, 5.0)

# Equality
west = Condition("Region", Operator.EQ, "West")

# List membership
selected = Condition("Region", Operator.IN_LIST, ["West", "East"])
excluded = Condition("Status", Operator.NOT_IN_LIST, ["Cancelled", "Refunded"])

# String matching
contains_corp = Condition("Name", Operator.CONTAINS, "Corp")
starts_with_a = Condition("Name", Operator.STARTS_WITH, "A")

# Null checks (no value needed)
empty = Condition("Name", Operator.IS_EMPTY)
not_empty = Condition("Email", Operator.IS_NOT_EMPTY)

# Aggregate checks
is_max = Condition("Sales", Operator.IS_MAXVAL)
is_min = Condition("Sales", Operator.IS_MINVAL)
```

### CompoundCondition

An AND/OR composition of conditions. Normally created automatically via `&` and `|` operators -- you rarely need to construct one directly.

```python
from mammoth import CompoundCondition

CompoundCondition(
    logic: str,          # "AND" or "OR"
    conditions: list[Condition | CompoundCondition | NotCondition],
)
```

### NotCondition

Negation of a condition. Created via the `~` (NOT) operator -- you rarely need to construct one directly.

```python
from mammoth import Condition, Operator

# Negate a single condition
not_closed = ~Condition("Status", Operator.EQ, "Closed")

# Negate a compound condition
not_priority = ~(Condition("Sales", Operator.GTE, 10000) & Condition("Region", Operator.EQ, "West"))

# Double negation cancels out: ~~cond returns the original condition
original = ~~not_closed  # same as Condition("Status", Operator.EQ, "Closed")

# Combine negated conditions with & and |
active = Condition("Status", Operator.EQ, "Active")
not_closed_and_active = ~Condition("Status", Operator.EQ, "Closed") & active
```

### Operator overloading

Combine conditions with `&` (AND), `|` (OR), and `~` (NOT). Use parentheses for grouping.

```python
from mammoth import Condition, Operator

high_sales = Condition("Sales", Operator.GTE, 10000)
west = Condition("Region", Operator.EQ, "West")
active = Condition("Status", Operator.EQ, "Active")

# AND: all conditions must be true
both = high_sales & west

# OR: at least one must be true
either = high_sales | west

# Nested: parentheses control grouping
complex_cond = (high_sales & west) | active

# Chain multiple
all_three = high_sales & west & active
```

Chaining is flat when using the same operator:

```python
# These are equivalent:
a & b & c           # CompoundCondition("AND", [a, b, c])
(a & b) & c         # CompoundCondition("AND", [a, b, c])
```

Mixing operators creates nesting:

```python
(a & b) | c         # CompoundCondition("OR", [CompoundCondition("AND", [a, b]), c])
```

### Using conditions with View methods

**filter_rows:**

```python
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

**set_values (conditional columns):**

```python
from mammoth import SetValue, ColumnType

view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
        SetValue("Basic"),  # default (no condition)
    ],
)
```

A global condition can also be applied to the entire task:

```python
view.set_values(
    existing_column="Label",
    values=[SetValue("Active")],
    condition=Condition("Status", Operator.EQ, "Active"),
)
```

**math, combine_columns, and other methods:**

Many transformation methods accept an optional `condition` parameter:

```python
view.math(
    "Price * 0.9",
    existing_column="Price",
    condition=Condition("Region", Operator.EQ, "West"),
)
```

### build()

The `build()` method converts a condition to the Mammoth API dict format. The SDK calls this automatically -- you normally do not need to call it yourself.

```python
cond = Condition("Sales", Operator.GTE, 1000)
payload = cond.build({"Sales": "column_1"})
# {"column_1": {"GTE": {"VALUE": 1000}}}

compound = cond & Condition("Region", Operator.EQ, "West")
payload = compound.build({"Sales": "column_1", "Region": "column_2"})
# {"AND": [{"column_1": {"GTE": {"VALUE": 1000}}}, {"column_2": {"EQ": {"VALUE": "West"}}}]}
```

### All operators

| Category | Operators |
|----------|-----------|
| Comparison | `GT`, `LT`, `GTE`, `LTE`, `EQ`, `NE` |
| List | `IN_LIST`, `NOT_IN_LIST`, `CONTAINS`, `NOT_CONTAINS` |
| String | `STARTS_WITH`, `ENDS_WITH`, `NOT_STARTS_WITH`, `NOT_ENDS_WITH` |
| Null | `IS_EMPTY`, `IS_NOT_EMPTY` |
| Aggregate | `IS_MAXVAL`, `IS_NOT_MAXVAL`, `IS_MINVAL`, `IS_NOT_MINVAL` |

---

## Transformations

All transformation methods are synchronous -- they block until the operation completes and the view metadata is refreshed (unless in draft mode, where tasks are queued). Each method returns the API response dict.

### filter_rows

Filter rows by condition (SELECT task).

```python
view.filter_rows(
    condition: Condition | CompoundCondition | NotCondition,
    filter_type: FilterType = FilterType.SHOW,
    prompt: str = "",
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `condition` | `Condition \| CompoundCondition \| NotCondition` | *required* | Filter condition |
| `filter_type` | `FilterType` | `SHOW` | `SHOW` to keep matching rows, `REMOVE` to discard |
| `prompt` | `str` | `""` | Natural-language description of the filter intent |

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)

# Combine conditions
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

### set_values

Create or update a column with conditional values (SET task).

```python
view.set_values(
    values: list[SetValue],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `values` | `list[SetValue]` | *required* | List of value specs (last one without a condition is the default) |
| `new_column` | `str \| None` | `None` | Name for a new column |
| `column_type` | `ColumnType` | `TEXT` | Type for the new column |
| `existing_column` | `str \| None` | `None` | Display name of existing column to update |
| `condition` | `Condition \| CompoundCondition \| NotCondition \| None` | `None` | Global condition applied to the whole task |

```python
from mammoth import SetValue, Condition, Operator, ColumnType

view.set_values(
    new_column="Risk Level",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Medium", condition=Condition("Sales", Operator.GTE, 5000)),
        SetValue("Low"),  # default
    ],
)
```

### math

Apply arithmetic operations (MATH task). Accepts a string expression that is parsed automatically.

```python
view.math(
    expression: str,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
# String expression (recommended)
view.math("Price * Quantity", new_column="Total")
view.math("(Price + Tax) * 1.1", new_column="Grand Total")

# Write to an existing column
view.math("Sales * 1.1", existing_column="Sales")
```

### add_column

Add an empty column (ADD_COLUMN task).

```python
view.add_column(name: str, column_type: ColumnType = ColumnType.TEXT) -> dict
```

```python
view.add_column("Notes", ColumnType.TEXT)
```

### delete_columns

Remove columns (DELETE task).

```python
view.delete_columns(columns: list[str]) -> dict
```

```python
view.delete_columns(["Temp Column", "Debug"])
```

### copy_columns

Duplicate columns (COPY task).

```python
view.copy_columns(copies: list[CopySpec]) -> dict
```

```python
from mammoth import CopySpec, ColumnType

view.copy_columns([
    CopySpec(source="Sales", as_name="Sales Backup", type=ColumnType.NUMERIC),
])
```

### combine_columns

Concatenate columns with a separator (COMBINE task).

```python
view.combine_columns(
    sources: list[str],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    separator: str = " ",
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
view.combine_columns(
    sources=["First Name", "Last Name"],
    new_column="Full Name",
    separator=" ",
)
```

### convert_type

Convert column data types (CONVERT task).

```python
view.convert_type(conversions: list[ConversionSpec]) -> dict
```

```python
from mammoth import ConversionSpec, ColumnType

view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Date", to=ColumnType.DATE),
])
```

### text_transform

Change text case or trim whitespace (TEXT_TRANSFORM task).

```python
view.text_transform(
    columns: list[str],
    case: TextCase | None = None,
    trim: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import TextCase

view.text_transform(columns=["Name"], case=TextCase.UPPER)
view.text_transform(columns=["Notes"], trim=True)
```

### replace_values

Find and replace text (REPLACE task).

```python
view.replace_values(
    columns: list[str],
    find: str,
    replace: str,
    match_case: bool = False,
    match_words: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
view.replace_values(columns=["Status"], find="N/A", replace="Unknown")
```

### bulk_replace

Bulk find-and-replace with multiple mappings (REPLACE with MAPPING).

```python
view.bulk_replace(
    columns: list[str],
    mapping: list[BulkReplaceMapping],
    match_case: bool = True,
    match_words: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import BulkReplaceMapping

view.bulk_replace(
    columns=["Item"],
    mapping=[
        BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE"),
        BulkReplaceMapping(search=["Small Coffee", "Large Coffee"], replace="Coffee"),
    ],
)
```

### split_column

Split a column by delimiter (SPLIT task).

```python
view.split_column(
    column: str,
    delimiter: str,
    new_columns: list[SplitColumnSpec],
) -> dict[str, Any]
```

```python
from mammoth import SplitColumnSpec

view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)
```

### substring

Extract a substring (SUBSTRING task).

```python
view.substring(
    column: str,
    direction: SubstringDirection | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    regex_pattern: str | None = None,
    regex_invert: bool = False,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

| Direction | Use with | Meaning |
|-----------|----------|---------|
| `START` | `num_char` | First N characters |
| `END` | `num_char` | Last N characters |
| `LEFT` | `char_position` | Characters before position |
| `RIGHT` | `char_position` | Characters after position |

```python
from mammoth import SubstringDirection

# First 3 characters
view.substring("Code", direction=SubstringDirection.START, num_char=3, new_column="Prefix")

# Regex extraction
view.substring("Email", regex_pattern=r"@(.+)$", new_column="Domain")
```

### extract_date

Extract date components (EXTRACT_DATE task).

```python
view.extract_date(
    column: str,
    component: DateComponent,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateComponent

view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")
view.extract_date("Order Date", DateComponent.MONTH_TEXT, new_column="Month Name")
```

### date_diff

Calculate date difference (DATE_DIFF task).

```python
view.date_diff(
    component: DateDiffUnit,
    start: str,
    end: str,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateDiffUnit

view.date_diff(
    DateDiffUnit.DAY,
    start="Start Date",
    end="End Date",
    new_column="Duration Days",
)
```

### increment_date

Add or subtract from a date (INCREMENT_DATE task).

```python
view.increment_date(
    column: str,
    delta: DateDelta,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateDelta

view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended Due Date")
view.increment_date("Start Date", delta=DateDelta(months=-1, years=2), new_column="Adjusted")
```

### pivot

Group and aggregate (PIVOT task).

```python
view.pivot(
    group_by: list[str],
    aggregations: list[AggregationSpec],
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import AggregateFunction, AggregationSpec

view.pivot(
    group_by=["Region"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### window

Apply a window function (WINDOW task).

```python
view.window(
    function: WindowFunction,
    column: str | None = None,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    partition_by: list[str] | None = None,
    order_by: list[list[str | SortDirection]] | None = None,
    range_type: WindowRange = WindowRange.UNBOUNDED,
) -> dict[str, Any]
```

```python
from mammoth import WindowFunction, SortDirection, WindowRange

# Row number per region, ordered by sales descending
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)

# Running sum
view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    order_by=[["Date", SortDirection.ASC]],
    range_type=WindowRange.RUNNING,
)
```

### crosstab

Crosstab / pivot table (CROSSTAB task).

```python
view.crosstab(
    rows: list[str],
    pivot_column: str,
    select: CrosstabSpec,
) -> dict[str, Any]
```

```python
from mammoth import CrosstabSpec

view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(column="Sales", function=AggregateFunction.SUM),
)
```

### fill_missing

Fill missing values forward or backward (FILL task).

```python
view.fill_missing(
    column: str,
    direction: FillDirection,
    partition_by: str | None = None,
    order_by: list[list[str | SortDirection]] | None = None,
) -> dict[str, Any]
```

```python
from mammoth import FillDirection, SortDirection

view.fill_missing(
    "Price",
    direction=FillDirection.LAST_VALUE,
    order_by=[["Date", SortDirection.ASC]],
)
```

### limit_rows

Keep top or bottom N rows (LIMIT task).

```python
view.limit_rows(
    n: int,
    bottom: bool = False,
    order_by: list[list[str | SortDirection]] | None = None,
) -> dict[str, Any]
```

```python
view.limit_rows(100, order_by=[["Sales", SortDirection.DESC]])
```

### discard_duplicates

Remove duplicate rows (DISCARD_DUPLICATES task).

```python
view.discard_duplicates(
    ignore_columns: list[str] | None = None,
) -> dict[str, Any]
```

```python
view.discard_duplicates()
view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

### unnest

Unpivot columns to rows (UNNEST task).

```python
view.unnest(
    columns: list[str],
    label_column: str = "Label",
    value_column: str = "Value",
) -> dict[str, Any]
```

```python
view.unnest(
    columns=["Q1 Sales", "Q2 Sales", "Q3 Sales", "Q4 Sales"],
    label_column="Quarter",
    value_column="Sales",
)
```

### join

Join with another dataview (JOIN task).

```python
view.join(
    foreign_view: int | View,
    join_type: JoinType,
    on: list[JoinKeySpec],
    select: list[str | JoinSelectSpec],
    column_prefix: str | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `foreign_view` | `int \| View` | View object or dataview ID to join with |
| `join_type` | `JoinType` | `INNER`, `LEFT`, `RIGHT`, or `OUTER` |
| `on` | `list[JoinKeySpec]` | Join keys as JoinKeySpec objects |
| `select` | `list[str \| JoinSelectSpec]` | Column names (str) or JoinSelectSpec objects |
| `column_prefix` | `str \| None` | Prefix for joined columns |

```python
from mammoth import JoinType, JoinKeySpec, JoinSelectSpec

# Join with a View object (display names everywhere)
other = client.views.get(2050)
view.join(
    foreign_view=other,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Name"],
)

# Join with a view ID (use internal names for the foreign view)
view.join(
    foreign_view=2050,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="column_1")],
    select=[JoinSelectSpec(column="column_7", alias="Category")],
)
```

### lookup

Look up values from another dataview (LOOKUP task).

```python
view.lookup(
    source: str,
    lookup_view_id: int,
    key: str,
    value: str,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
view.lookup(
    source="Product Code",
    lookup_view_id=2050,
    key="code",         # key column in the lookup view
    value="name",       # value column in the lookup view
    new_column="Product Name",
)
```

### json_extract

Extract data from a JSON column (JSON_HANDLE task).

```python
view.json_extract(
    column: str,
    json_type: JsonType = JsonType.OBJECT,
    keys: list[str] | None = None,
    extractions: list[JsonExtractionSpec] | None = None,
    keep_source: bool = False,
    op_type: JsonOpType | None = None,
) -> dict[str, Any]
```

```python
from mammoth import JsonType, JsonExtractionSpec, ColumnType

# Simple key extraction
view.json_extract("data", keys=["name", "email", "age"])

# Advanced with custom types
view.json_extract(
    "data",
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT),
        JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
    ],
)

# JSON list to rows
view.json_extract("items", json_type=JsonType.LIST)
```

### gen_ai

AI-powered transformation (GEN_AI task).

```python
view.gen_ai(
    prompt: str,
    context_columns: list[str],
    new_column: str = "AI Result",
    assistant_data: list[str] | None = None,
    context_columns_derivation: bool | None = None,
) -> dict[str, Any]
```

```python
view.gen_ai(
    prompt="Classify the sentiment of the review as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### generate_sql

Generate SQL from a natural language intent using Mammoth's LLM. Returns the generated SQL string. Also adds the task to the pipeline automatically.

```python
view.generate_sql(intent: str) -> str
```

```python
sql = view.generate_sql("count employees by department")
print(sql)  # "SELECT department, COUNT(*) ..."
```

### add_sql

Add a raw SQL query as a pipeline task.

```python
view.add_sql(query: str) -> dict[str, Any]
```

```python
view.add_sql("SELECT department, COUNT(*) as cnt FROM data GROUP BY department")
```

---

## Exports

The SDK provides two ways to export data:

1. **ViewExport** (`view.export`) -- export methods attached to a View object (recommended)
2. **ExportsAPI** (`client.exports`) -- lower-level export operations

### ViewExport

Access via `view.export`. This is the recommended way to export data from a View.

#### to_csv

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

#### to_s3

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

#### to_postgres

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

#### to_mysql

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

#### to_bigquery

Export to Google BigQuery.

```python
view.export.to_bigquery(**kwargs) -> dict[str, Any]
```

Pass BigQuery connection and table configuration as keyword arguments.

#### to_redshift

Export to Amazon Redshift.

```python
view.export.to_redshift(**kwargs) -> dict[str, Any]
```

#### to_elasticsearch

Export to Elasticsearch.

```python
view.export.to_elasticsearch(**kwargs) -> dict[str, Any]
```

#### to_ftp

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

#### to_sftp

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

#### to_email

Export via email.

```python
view.export.to_email(recipients: list[str], **kwargs) -> dict[str, Any]
```

```python
view.export.to_email(recipients=["analyst@example.com", "team@example.com"])
```

#### to_dataset

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

#### publish_to_db

Publish the dataview to a database.

```python
view.export.publish_to_db(**kwargs) -> dict[str, Any]
```

#### list

List all exports for this dataview.

```python
exports = view.export.list()
for exp in exports:
    print(exp["id"], exp["handler_type"])
```

#### delete

Delete an export by ID.

```python
view.export.delete(export_id=123)
```

### branch_out (View method)

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

### ExportsAPI

Lower-level export operations available via `client.exports`. These methods require explicit IDs rather than working through a View object.

#### client.exports.to_csv

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

#### client.exports.to_s3

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

#### client.exports.to_dataset

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

#### client.exports.list

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

#### client.exports.create

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

---

## Files API

The `FilesAPI` manages file uploads, listing, and deletion. Access it via `client.files`.

### upload()

Upload one or more files to create datasets. Each file becomes a separate dataset.

```python
client.files.upload(
    files: list[str | Path | BinaryIO] | str | Path | BinaryIO,
    folder_resource_id: str | None = None,
    append_to_ds_id: int | None = None,
    override_target_schema: bool | None = None,
    wait_for_completion: bool = True,
    timeout: int = 300,
) -> list[int] | int | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `str`, `Path`, `BinaryIO`, or list | *required* | File path(s), Path objects, or file-like objects to upload |
| `folder_resource_id` | `str` | `None` | Resource ID of target folder in Mammoth |
| `append_to_ds_id` | `int` | `None` | Dataset ID to append data to (instead of creating new) |
| `override_target_schema` | `bool` | `None` | Override target schema when appending |
| `wait_for_completion` | `bool` | `True` | Wait for upload processing to finish |
| `timeout` | `int` | `300` | Timeout in seconds when waiting |

**Returns:**

- Single file: `int` (the dataset ID)
- Multiple files: `list[int]` (list of dataset IDs)
- On failure or `wait_for_completion=False`: `None` or initial job ID

**Examples:**

```python
# Single file upload
dataset_id = client.files.upload("sales_data.csv")

# Multiple files
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx", "products.tsv"])

# Using Path objects
from pathlib import Path
dataset_id = client.files.upload(Path("data/report.csv"))

# Append to existing dataset
client.files.upload("new_rows.csv", append_to_ds_id=42)

# Upload to a specific folder
client.files.upload("data.csv", folder_resource_id="folder-abc-123")

# Non-blocking upload (returns job ID immediately)
job_id = client.files.upload("large_file.csv", wait_for_completion=False)
```

**After upload -- get a View:**

```python
dataset_id = client.files.upload("sales_data.csv")
views = client.views.list(dataset_id)
view = views[0]  # Default view created on upload
print(view.display_names)  # ["Column1", "Column2", ...]
```

### upload_folder()

Upload all files in a folder. Calls `upload()` under the hood.

```python
client.files.upload_folder(
    folder_path: str | Path,
    folder_resource_id: str | None = None,
    wait_for_completion: bool = True,
    timeout: int = 300,
) -> list[int] | int | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | `str` or `Path` | *required* | Path to the folder containing files |
| `folder_resource_id` | `str` | `None` | Resource ID of target folder in Mammoth |
| `wait_for_completion` | `bool` | `True` | Wait for upload processing to finish |
| `timeout` | `int` | `300` | Timeout in seconds when waiting |

```python
dataset_ids = client.files.upload_folder("./data/monthly_reports/")
```

### list()

List files in the current project with optional filtering and pagination.

```python
client.files.list(
    fields: str | None = None,
    file_ids: list[int] | None = None,
    names: list[str] | None = None,
    statuses: list[str] | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
) -> FilesList
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fields` | `str` | `None` | Fields to return (`"__standard"`, `"__full"`, `"__min"`) |
| `file_ids` | `list[int]` | `None` | Filter by specific file IDs |
| `names` | `list[str]` | `None` | Filter by file names |
| `statuses` | `list[str]` | `None` | Filter by file statuses |
| `created_at` | `str` | `None` | Date range filter for creation date |
| `updated_at` | `str` | `None` | Date range filter for update date |
| `limit` | `int` | `50` | Maximum results (0-100) |
| `offset` | `int` | `0` | Number of results to skip |
| `sort` | `str` | `None` | Sort spec (e.g., `"(id:asc)"`, `"(name:desc)"`) |

```python
files = client.files.list()
for f in files.files:
    print(f"{f.id}: {f.name} ({f.status})")

# Filter by name
files = client.files.list(names=["sales_data.csv"])
```

### get()

Get detailed information about a specific file.

```python
client.files.get(
    file_id: int,
    fields: str | None = None,
) -> FileSchema
```

```python
file_info = client.files.get(file_id=123)
print(f"Name: {file_info.name}")
print(f"Status: {file_info.status}")
```

### update()

Update file configuration (e.g., set password, extract sheets). Waits for the job to complete.

```python
client.files.update(
    file_id: int,
    patch_request: FilePatchRequest,
) -> ObjectJobSchema
```

This is the low-level method used internally by `set_password()` and `extract_sheets()`. You rarely need to call it directly.

### delete()

Delete a specific file.

```python
client.files.delete(file_id: int) -> None
```

```python
client.files.delete(file_id=123)
```

### bulk_delete()

Delete multiple files at once.

```python
client.files.bulk_delete(file_ids: list[int]) -> None
```

```python
client.files.bulk_delete([101, 102, 103])
```

### set_password()

Set a password for a password-protected file (e.g., encrypted Excel).

```python
client.files.set_password(file_id: int, password: str) -> ObjectJobSchema
```

### extract_sheets()

Extract specific sheets from an Excel file into separate datasets.

```python
client.files.extract_sheets(
    file_id: int,
    sheets: list[str],
    delete_file_after_extract: bool = True,
    combine_after_extract: bool = False,
) -> ObjectJobSchema
```

```python
client.files.extract_sheets(
    file_id=123,
    sheets=["Sheet1", "Revenue"],
    delete_file_after_extract=True,
)
```

### Supported file formats

| Category | Formats |
|----------|---------|
| Tabular | CSV, TSV, PSV, XLS, XLSX |
| Compressed | ZIP, BZ2, GZ, TAR, 7Z |
| Document | PDF |
| Image | TIFF, JPEG, PNG, HEIC, WEBP |

**Maximum file size:** 50 MB

---

## Enums & Data Classes

The SDK provides enums for all transformation parameters. Import them directly from `mammoth`:

```python
from mammoth import Operator, ColumnType, JoinType, DateComponent
```

All enums are `str` subclasses (`class MyEnum(str, Enum)`) so they can be used directly as strings where needed.

### Operator

Filter operators for use with `Condition`.

| Value | Description | Example value |
|-------|-------------|---------------|
| `Operator.GT` | Greater than | `1000` |
| `Operator.LT` | Less than | `5.0` |
| `Operator.GTE` | Greater than or equal | `1000` |
| `Operator.LTE` | Less than or equal | `100` |
| `Operator.EQ` | Equal | `"West"` |
| `Operator.NE` | Not equal | `"Cancelled"` |
| `Operator.IN_LIST` | Value is in list | `["West", "East"]` |
| `Operator.NOT_IN_LIST` | Value is not in list | `["Cancelled"]` |
| `Operator.CONTAINS` | String contains | `"Corp"` |
| `Operator.NOT_CONTAINS` | String does not contain | `"test"` |
| `Operator.STARTS_WITH` | String starts with | `"A"` |
| `Operator.ENDS_WITH` | String ends with | `"Inc"` |
| `Operator.NOT_STARTS_WITH` | String does not start with | `"X"` |
| `Operator.NOT_ENDS_WITH` | String does not end with | `"Ltd"` |
| `Operator.IS_EMPTY` | Value is null/empty | *(no value)* |
| `Operator.IS_NOT_EMPTY` | Value is not null/empty | *(no value)* |
| `Operator.IS_MAXVAL` | Value is the column max | *(no value)* |
| `Operator.IS_NOT_MAXVAL` | Value is not the column max | *(no value)* |
| `Operator.IS_MINVAL` | Value is the column min | *(no value)* |
| `Operator.IS_NOT_MINVAL` | Value is not the column min | *(no value)* |

### ColumnType

Column data types for new columns and type conversions.

| Value | Description |
|-------|-------------|
| `ColumnType.TEXT` | Text/string data |
| `ColumnType.NUMERIC` | Numeric data (integers and decimals) |
| `ColumnType.DATE` | Date/datetime data |

### ValueType

Value types for expressions in pipeline tasks.

| Value | Description |
|-------|-------------|
| `ValueType.FIXED` | A literal value |
| `ValueType.EXPRESSION` | A system expression |
| `ValueType.COLUMN` | A column reference |
| `ValueType.NUMBER` | A numeric literal |
| `ValueType.OPERATOR` | An arithmetic operator |

### JoinType

Join types for combining dataviews.

| Value | Description |
|-------|-------------|
| `JoinType.INNER` | Inner join -- only matching rows |
| `JoinType.LEFT` | Left join -- all rows from left, matching from right |
| `JoinType.RIGHT` | Right join -- all rows from right, matching from left |
| `JoinType.OUTER` | Outer join -- all rows from both sides |

### TextCase

Text case transformations for `text_transform()`.

| Value | Description |
|-------|-------------|
| `TextCase.UPPER` | Convert to UPPERCASE |
| `TextCase.LOWER` | Convert to lowercase |
| `TextCase.TITLE` | Convert to Title Case |

### DateComponent

Date components for `extract_date()`. Values are lowercase to match the backend format.

**Basic components:**

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.YEAR` | NUMERIC | Year (e.g., 2025) |
| `DateComponent.MONTH` | NUMERIC | Month number (1-12) |
| `DateComponent.DAY` | NUMERIC | Day of month (1-31) |
| `DateComponent.HOUR` | NUMERIC | Hour (0-23) |
| `DateComponent.MINUTE` | NUMERIC | Minute (0-59) |
| `DateComponent.SECOND` | NUMERIC | Second (0-59) |
| `DateComponent.WEEK` | NUMERIC | Week of year |
| `DateComponent.QUARTER` | NUMERIC | Quarter (1-4) |
| `DateComponent.DAY_OF_WEEK` | NUMERIC | Day of week number |
| `DateComponent.DAY_OF_YEAR` | NUMERIC | Day of year (1-366) |

**Text-based extractions:**

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.WEEKDAY_TEXT` | TEXT | Day name (e.g., "Monday") |
| `DateComponent.MONTH_TEXT` | TEXT | Month name (e.g., "January") |

**Composite formats:**

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.YEAR_MONTH` | NUMERIC | Year-month composite |
| `DateComponent.YEAR_WEEK` | NUMERIC | Year-week composite |
| `DateComponent.YEAR_QUARTER` | NUMERIC | Year-quarter composite |
| `DateComponent.MONTH_DAY` | NUMERIC | Month-day composite |
| `DateComponent.HOUR_MINUTE` | NUMERIC | Hour-minute composite |
| `DateComponent.HOUR_MINUTE_SECOND` | NUMERIC | Hour-minute-second composite |
| `DateComponent.YEAR_MONTH_DAY` | NUMERIC | Year-month-day composite |
| `DateComponent.YEAR_MONTH_DAY_AS_DATE` | TEXT | Date as formatted text |
| `DateComponent.MONTH_DAY_YEAR_HOUR_MINUTE_SECOND` | TEXT | Full datetime as text |
| `DateComponent.DATE_ONLY` | NUMERIC | Date-only component |

### DateDiffUnit

Units for `date_diff()` calculations. Values are UPPERCASE (distinct from `DateComponent`).

| Value | Description |
|-------|-------------|
| `DateDiffUnit.YEAR` | Difference in years |
| `DateDiffUnit.MONTH` | Difference in months |
| `DateDiffUnit.DAY` | Difference in days |
| `DateDiffUnit.HOUR` | Difference in hours |
| `DateDiffUnit.MINUTE` | Difference in minutes |
| `DateDiffUnit.SECOND` | Difference in seconds |
| `DateDiffUnit.WEEK` | Difference in weeks |
| `DateDiffUnit.QUARTER` | Difference in quarters |

### AggregateFunction

Aggregate functions for `pivot()` and group operations.

| Value | Description |
|-------|-------------|
| `AggregateFunction.SUM` | Sum of values |
| `AggregateFunction.AVG` | Average of values |
| `AggregateFunction.MIN` | Minimum value |
| `AggregateFunction.MAX` | Maximum value |
| `AggregateFunction.COUNT` | Count of values |
| `AggregateFunction.COUNT_DISTINCT` | Count of distinct values |
| `AggregateFunction.STDDEV` | Standard deviation |
| `AggregateFunction.VARIANCE` | Variance |
| `AggregateFunction.MEDIAN` | Median value |
| `AggregateFunction.FIRST` | First value |
| `AggregateFunction.LAST` | Last value |
| `AggregateFunction.CONCAT` | Concatenate values |

### WindowFunction

Window functions for `window()`.

| Value | Description |
|-------|-------------|
| `WindowFunction.ROW_NUMBER` | Sequential row number |
| `WindowFunction.RANK` | Rank with gaps |
| `WindowFunction.DENSE_RANK` | Rank without gaps |
| `WindowFunction.LAG` | Previous row value |
| `WindowFunction.LEAD` | Next row value |
| `WindowFunction.SUM` | Window sum |
| `WindowFunction.AVG` | Window average |
| `WindowFunction.MIN` | Window minimum |
| `WindowFunction.MAX` | Window maximum |
| `WindowFunction.COUNT` | Window count |
| `WindowFunction.FIRST_VALUE` | First value in window |
| `WindowFunction.LAST_VALUE` | Last value in window |
| `WindowFunction.STDDEV` | Window standard deviation |
| `WindowFunction.VARIANCE` | Window variance |
| `WindowFunction.PERCENT_RANK` | Percent rank |
| `WindowFunction.NTILE` | N-tile distribution |

### WindowRange

Window range types for `window()`.

| Value | Description |
|-------|-------------|
| `WindowRange.UNBOUNDED` | Entire partition |
| `WindowRange.RUNNING` | Running window (start of partition to current row) |

### FillDirection

Fill directions for `fill_missing()`.

| Value | Description |
|-------|-------------|
| `FillDirection.FIRST_VALUE` | Fill with the first non-null value going forward |
| `FillDirection.LAST_VALUE` | Fill with the last non-null value going backward |

### SortDirection

Sort direction for `order_by` parameters.

| Value | Description |
|-------|-------------|
| `SortDirection.ASC` | Ascending order |
| `SortDirection.DESC` | Descending order |

### MathOperator

Arithmetic operators for math expressions.

| Value | Symbol | Description |
|-------|--------|-------------|
| `MathOperator.ADD` | `+` | Addition |
| `MathOperator.SUBTRACT` | `-` | Subtraction |
| `MathOperator.MULTIPLY` | `*` | Multiplication |
| `MathOperator.DIVIDE` | `/` | Division |
| `MathOperator.MODULO` | `%` | Modulo (remainder) |

### SubstringDirection

Extraction direction for `substring()`.

| Value | Use with | Description |
|-------|----------|-------------|
| `SubstringDirection.START` | `num_char` | Extract first N characters |
| `SubstringDirection.END` | `num_char` | Extract last N characters |
| `SubstringDirection.LEFT` | `char_position` | Extract characters before position |
| `SubstringDirection.RIGHT` | `char_position` | Extract characters after position |

### JsonType

JSON structure types for `json_extract()`.

| Value | Description |
|-------|-------------|
| `JsonType.OBJECT` | JSON object (`{...}`) -- extract keys to columns |
| `JsonType.LIST` | JSON list (`[...]`) -- extract items to rows |

### JsonOpType

Operation types for `json_extract()`.

| Value | Description |
|-------|-------------|
| `JsonOpType.JSON_OBJECT_TO_COLUMNS` | Extract object keys to separate columns |
| `JsonOpType.JSON_LIST_TO_ROWS` | Extract list items to separate rows |

### FilterType

Filter types for `filter_rows()`.

| Value | Description |
|-------|-------------|
| `FilterType.SHOW` | Keep rows that match the condition |
| `FilterType.REMOVE` | Discard rows that match the condition |

### ProviderType

Value provider types for SET task values.

| Value | Description |
|-------|-------------|
| `ProviderType.FIXED` | A literal value (e.g., `"High"`, `42`) |
| `ProviderType.EXPRESSION` | A system expression (e.g., `"__TIME__"` for current timestamp) |

### TaskType

Pipeline task type identifiers.

| Value | Description |
|-------|-------------|
| `TaskType.SET` | Set/label values |
| `TaskType.SELECT` | Filter rows |
| `TaskType.MATH` | Arithmetic operations |
| `TaskType.JOIN` | Join dataviews |
| `TaskType.PIVOT` | Group and aggregate |
| `TaskType.WINDOW` | Window functions |
| `TaskType.FILL` | Fill missing values |
| `TaskType.LIMIT` | Limit rows |
| `TaskType.LOOKUP` | Lookup from another view |
| `TaskType.COMBINE` | Concatenate columns |
| `TaskType.CONVERT` | Convert column types |
| `TaskType.COPY` | Copy columns |
| `TaskType.DELETE` | Delete columns |
| `TaskType.ADD_COLUMN` | Add empty column |
| `TaskType.REPLACE` | Find and replace |
| `TaskType.SPLIT` | Split column |
| `TaskType.SUBSTRING` | Extract substring |
| `TaskType.TEXT_TRANSFORM` | Text case / trim |
| `TaskType.EXTRACT_DATE` | Extract date part |
| `TaskType.DATE_DIFF` | Date difference |
| `TaskType.INCREMENT_DATE` | Add/subtract from date |
| `TaskType.UNNEST` | Unpivot columns to rows |
| `TaskType.CROSSTAB` | Crosstab / pivot table |
| `TaskType.JSON_HANDLE` | JSON extraction |
| `TaskType.GEN_AI` | AI transformation |
| `TaskType.SQL` | SQL query |
| `TaskType.DISCARD_DUPLICATES` | Remove duplicate rows |

### ExportFileType

File types for `to_s3()` export.

| Value | Description |
|-------|-------------|
| `ExportFileType.CSV` | CSV format |
| `ExportFileType.JSON` | JSON format |
| `ExportFileType.PARQUET` | Parquet format |

### Data Classes

#### SetValue

Value spec for `set_values()`.

```python
from mammoth import SetValue, Condition, Operator

SetValue(
    value: Any,
    condition: Condition | CompoundCondition | NotCondition | None = None,
)

values = [
    SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
    SetValue("Low"),  # default value (no condition)
]
```

#### CopySpec

Spec for `copy_columns()`.

```python
from mammoth import CopySpec, ColumnType

CopySpec(
    source: str,              # Source column display name
    as_name: str,             # New column display name
    type: ColumnType = ColumnType.TEXT,  # Column type
)
```

#### ConversionSpec

Spec for `convert_type()`.

```python
from mammoth import ConversionSpec, ColumnType

ConversionSpec(
    column: str,              # Column display name
    to: ColumnType,           # Target type
    format: str | None = None,  # Date format (for TEXT→DATE)
)
```

#### AggregationSpec

Spec for `pivot()` aggregations.

```python
from mammoth import AggregationSpec, AggregateFunction

AggregationSpec(
    column: str,                 # Column to aggregate
    function: AggregateFunction, # Aggregation function
    as_name: str | None = None,  # Output column name (auto-generated if None)
    delimiter: str | None = None,  # Delimiter for CONCAT function
)
```

#### CrosstabSpec

Spec for `crosstab()` aggregation.

```python
from mammoth import CrosstabSpec, AggregateFunction

CrosstabSpec(
    function: AggregateFunction,  # Aggregation function
    column: str | None = None,    # Column to aggregate (None for COUNT)
)
```

#### JoinKeySpec

Join key mapping for `join()`.

```python
from mammoth import JoinKeySpec

JoinKeySpec(
    left: str,   # Column from the left (current) view
    right: str,  # Column from the right (foreign) view
)
```

#### JoinSelectSpec

Column selection for `join()` foreign columns.

```python
from mammoth import JoinSelectSpec

JoinSelectSpec(
    column: str,                  # Foreign column name
    alias: str | None = None,     # Alias in the joined result
)
```

#### SplitColumnSpec

Spec for `split_column()` output columns.

```python
from mammoth import SplitColumnSpec, ColumnType

SplitColumnSpec(
    name: str,                          # New column name
    type: ColumnType = ColumnType.TEXT,  # Column type
)
```

#### BulkReplaceMapping

Mapping for `bulk_replace()`.

```python
from mammoth import BulkReplaceMapping

BulkReplaceMapping(
    search: list[str],  # Values to search for
    replace: str,       # Replacement value
)
```

#### DateDelta

Time delta for `increment_date()`.

```python
from mammoth import DateDelta

DateDelta(
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
)
```

```python
# Add 30 days
view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended")

# Subtract 1 month, add 2 years
view.increment_date("Start", delta=DateDelta(months=-1, years=2), new_column="Adjusted")
```

#### JsonExtractionSpec

Spec for `json_extract()` custom extractions.

```python
from mammoth import JsonExtractionSpec, ColumnType

JsonExtractionSpec(
    key: str,                           # JSON key to extract
    as_name: str | None = None,         # Output column name (defaults to key)
    type: ColumnType = ColumnType.TEXT,  # Output column type
)
```

---

## Exceptions

The SDK provides a hierarchy of exception classes for precise error handling.

### Exception hierarchy

```
MammothError                     # Base exception for all SDK errors
  +-- MammothAPIError            # API request failures (HTTP errors, network errors)
  |     +-- MammothAuthError     # Authentication failures (HTTP 401)
  +-- MammothJobTimeoutError     # Job polling timeout
  +-- MammothJobFailedError      # Job execution failure
  +-- MammothTransformError      # Transformation task failure
  +-- MammothColumnError         # Column name resolution failure
```

### MammothError

Base exception for all Mammoth SDK errors.

```python
class MammothError(Exception):
    message: str
    details: dict[str, Any]
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error message |
| `details` | `dict` | Additional error details (default `{}`) |

### MammothAPIError

Raised for API-related errors: HTTP 4xx/5xx responses, network errors, timeouts, and invalid responses.

```python
class MammothAPIError(MammothError):
    status_code: int | None
    response_body: dict[str, Any]
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `status_code` | `int \| None` | HTTP status code (if available) |
| `response_body` | `dict` | Full API response body (default `{}`) |
| `details` | `dict` | Additional error details |

### MammothAuthError

Raised when authentication fails (HTTP 401). Subclass of `MammothAPIError`.

```python
class MammothAuthError(MammothAPIError):
    pass  # status_code is always 401
```

### MammothJobTimeoutError

Raised when a job does not complete within the allowed timeout.

```python
class MammothJobTimeoutError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["job_id"]` | `int` | ID of the timed-out job |
| `details["timeout"]` | `int` | Timeout value in seconds |

### MammothJobFailedError

Raised when a job completes with a failure status.

```python
class MammothJobFailedError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["job_id"]` | `int` | ID of the failed job |
| `details["failure_reason"]` | `str \| None` | Reason for failure |

### MammothTransformError

Raised when a transformation task fails. Includes the task key for identification.

```python
class MammothTransformError(MammothError):
    task_key: str | None
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `task_key` | `str \| None` | Pipeline task key (e.g., `"SET"`, `"MATH"`) |
| `details` | `dict` | Additional error details |

### MammothColumnError

Raised when a column display name cannot be resolved to an internal name. Includes the list of available columns for easy debugging.

```python
class MammothColumnError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["column_name"]` | `str` | The column name that was not found |
| `details["available_columns"]` | `list[str] \| None` | List of valid column names |

### Error handling patterns

**Catch specific exceptions:**

```python
from mammoth import (
    MammothAPIError,
    MammothAuthError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothColumnError,
)

try:
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")

except MammothAuthError:
    print("Invalid credentials -- check API key and secret")

except MammothColumnError as e:
    print(f"Column not found: {e.details['column_name']}")
    print(f"Available: {e.details['available_columns']}")

except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out")

except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed: {e.details['failure_reason']}")

except MammothAPIError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

**Use the base class as a catch-all:**

```python
from mammoth import MammothError

try:
    view.math("Price * Quantity", new_column="Total")
except MammothError as e:
    print(f"Mammoth error: {e.message}")
```

---

## Cookbook

Practical examples of common workflows using the Mammoth SDK. All examples assume the following setup:

```python
from mammoth import (
    MammothClient, Condition, CompoundCondition, Operator,
    ColumnType, SetValue, JoinType, JoinKeySpec, JoinSelectSpec,
    AggregateFunction, AggregationSpec, CrosstabSpec, CopySpec,
    ConversionSpec, SplitColumnSpec, BulkReplaceMapping, DateDelta,
    WindowFunction, SortDirection, WindowRange, DateComponent,
    DateDiffUnit, TextCase, FillDirection, SubstringDirection,
    FilterType, JsonType, JsonExtractionSpec, ExportFileType,
)

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)
view = client.views.get(1039)
```

### End-to-end: upload, transform, export

```python
from mammoth import MammothClient, Condition, Operator

# 1. Initialize
client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)

# 2. Upload CSV
ds_id = client.files.upload("sales_data.csv")

# 3. Get the default view
views = client.views.list(ds_id)
view = views[0]
print(view.display_names)  # ["Product", "Region", "Sales", "Date", ...]

# 4. Apply transformations
view.filter_rows(Condition("Sales", Operator.GTE, 100))
view.text_transform(columns=["Region"], case="UPPER")
view.math("Sales * 0.1", new_column="Tax")

# 5. Export
view.export.to_csv("filtered_sales.csv")
```

### Data analysis pipeline

```python
# Get a working view
view = client.views.create(dataset_id=ds_id, name="analysis")

# Convert date columns (required for CSV uploads)
view.convert_type([ConversionSpec(column="order_date", to=ColumnType.DATE)])

# Extract date components
view.extract_date("order_date", component="year", new_column="Year")
view.extract_date("order_date", component="month", new_column="Month")

# Calculate derived columns
view.math("Revenue - Cost", new_column="Profit")

# Group and aggregate
view.pivot(
    group_by=["Year", "Region"],
    aggregations=[
        AggregationSpec(column="Revenue", function=AggregateFunction.SUM, as_name="Total Revenue"),
        AggregationSpec(column="Profit", function=AggregateFunction.AVG, as_name="Avg Profit"),
        AggregationSpec(column="Order ID", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### Working with conditions

```python
# Simple conditions
high_sales = Condition("Sales", Operator.GTE, 10000)
west_region = Condition("Region", Operator.EQ, "West")
empty_email = Condition("Email", Operator.IS_EMPTY)
in_list = Condition("Status", Operator.IN_LIST, ["Active", "Pending"])

# AND — keep rows matching ALL conditions
view.filter_rows(high_sales & west_region)

# OR — keep rows matching ANY condition
view.filter_rows(
    Condition("Region", Operator.EQ, "West")
    | Condition("Region", Operator.EQ, "East")
)

# Nested
complex = (high_sales & west_region) | empty_email

# Use in set_values for conditional labeling
view.set_values(
    new_column="Priority",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Urgent", condition=high_sales & west_region),
        SetValue("Review", condition=high_sales),
        SetValue("Normal"),  # default — no condition
    ],
)
```

### Text processing

```python
# Split full name
view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)

# Combine columns
view.combine_columns(
    sources=["City", "State"],
    separator=", ",
    new_column="Location",
)

# Find and replace
view.replace_values(
    columns=["Status"],
    find="N/A",
    replace="Unknown",
)

# Bulk replace
view.bulk_replace(
    columns=["Category"],
    mapping=[
        BulkReplaceMapping(search=["Cat A", "Category A"], replace="A"),
        BulkReplaceMapping(search=["Cat B", "Category B"], replace="B"),
    ],
)

# Extract substring
view.substring(column="Phone", direction="START", num_char=3, new_column="Area Code")
```

### Window functions

```python
# Rank employees by salary within each department
view.window(
    function="ROW_NUMBER",
    new_column="Salary Rank",
    partition_by=["department"],
    order_by=[["base_salary", "DESC"]],
)

# Running total of sales by region
view.window(
    function="SUM",
    column="Sales",
    new_column="Running Total",
    partition_by=["Region"],
    order_by=[["Order Date", "ASC"]],
)
```

### Join two views

```python
# Get both views
orders = client.views.get(view_id=1001)
customers = client.views.get(view_id=1002)

# Join — View object auto-resolves display names
orders.join(
    foreign_view=customers,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Name", "Segment"],
)
```

### AI features

```python
# SQL from natural language
result = view.sql("count employees by department")

# Just generate the SQL without applying
sql = view.generate_sql("show top 10 products by revenue")
print(sql)  # "SELECT product, SUM(revenue) FROM ... GROUP BY product ORDER BY ..."

# Add custom SQL
view.add_sql("SELECT region, SUM(sales) AS total FROM __THIS__ GROUP BY region")

# AI-powered column generation
view.gen_ai(
    prompt="Classify the sentiment as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### Draft mode (batch transformations)

```python
# Context manager — pipeline runs once on clean exit, discards on exception
with view.draft():
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.math("Price * 2", new_column="Double")
    view.add_column("Notes")
# Pipeline runs once for all 3 tasks

# Explicit approach
view.enter_draft_mode()
view.add_column("Status")
view.set_values(
    new_column="Flag", column_type=ColumnType.TEXT,
    values=[SetValue("x")],
)
view.submit_draft()  # runs pipeline, refreshes metadata, exits draft

# Discard queued tasks
view.enter_draft_mode()
view.add_column("Temp")
view.discard_draft()  # reverts, "Temp" is not added

# Check mode
print(view.is_draft_mode)  # False
```

### Cleaning data

```python
# Remove duplicates
view.discard_duplicates()
view.discard_duplicates(ignore_columns=["Timestamp"])

# Fill missing values
view.fill_missing(column="Price", direction="LAST_VALUE")

# Remove rows with missing values
view.filter_rows(Condition("Email", Operator.IS_NOT_EMPTY))

# Trim whitespace
view.text_transform(columns=["Name", "City", "Email"], trim=True)

# Convert types
view.convert_type([
    ConversionSpec(column="price", to=ColumnType.NUMERIC),
    ConversionSpec(column="date", to=ColumnType.DATE),
])
```

### Export destinations

```python
# CSV download
path = view.export.to_csv("output.csv")

# PostgreSQL
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="sales_summary",
    username="user", password="pass",
)

# MySQL
view.export.to_mysql(
    host="mysql.example.com", port=3306,
    database="warehouse", table="output",
    username="user", password="pass",
)

# SFTP
view.export.to_sftp(
    host="sftp.example.com", port=22,
    path="/uploads/report.csv",
    username="user", password="pass",
)

# Email
view.export.to_email(recipients=["team@example.com", "manager@example.com"])

# S3
view.export.to_s3(file_name="report.csv", file_type=ExportFileType.CSV)

# Branch out to another dataset
view.branch_out(dest_dataset_id=42)
```

### Error handling

```python
from mammoth import (
    MammothError, MammothAPIError, MammothAuthError,
    MammothColumnError, MammothJobTimeoutError,
)

try:
    view.filter_rows(Condition("NonexistentColumn", Operator.EQ, "x"))
except MammothColumnError as e:
    print(f"Column not found: {e}")
    print(f"Available columns: {view.display_names}")

try:
    view.sql("complex query that might fail")
except MammothAPIError as e:
    print(f"API error: {e}")

try:
    view.pivot(group_by=["Region"], aggregations=[...])
except MammothJobTimeoutError as e:
    print(f"Job timed out: {e}")
```

### Inspecting a view

```python
view = client.views.get(1039)

# Column info
print(view.display_names)        # ["Sales", "Region", "Date", ...]
print(view.column_types)         # {"Sales": "NUMERIC", "Region": "TEXT", ...}
print(view.columns)              # {"Sales": "column_abc", "Region": "column_def", ...}
print(view.get_column_mapping()) # same as view.columns

# Data sample
data = view.data(limit=5)

# Full metadata
print(view.raw)  # complete API response dict
print(view.id, view.dataset_id, view.name)
```

### Using parse_path helper

```python
from mammoth import parse_path

ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039")
# {"workspace_id": 11, "project_id": 10, "dataview_id": 1039}
```

### Context manager

```python
with MammothClient(api_key="...", api_secret="...", workspace_id=11) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
# Session is cleaned up on exit
```

### Complete workflow

```python
import os
from mammoth import (
    MammothClient, Condition, Operator, ColumnType,
    SetValue, AggregateFunction, AggregationSpec,
    ConversionSpec, SortDirection, TextCase,
)

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# 1. Get the view
view = client.views.get(1039)
print(f"Starting with {len(view.display_names)} columns")

# 2. Clean: trim whitespace, convert types
view.text_transform(columns=["Customer Name", "Region"], trim=True)
view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Order Date", to=ColumnType.DATE),
])

# 3. Filter: remove empty sales
view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))

# 4. Transform: add calculated columns
view.math("Price * Quantity", new_column="Revenue")
view.set_values(
    new_column="Segment",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Enterprise", condition=Condition("Revenue", Operator.GTE, 100000)),
        SetValue("Mid-Market", condition=Condition("Revenue", Operator.GTE, 10000)),
        SetValue("SMB"),
    ],
)

# 5. Aggregate
view.pivot(
    group_by=["Region", "Segment"],
    aggregations=[
        AggregationSpec(column="Revenue", function=AggregateFunction.SUM, as_name="Total Revenue"),
        AggregationSpec(column="Revenue", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)

# 6. Export
view.export.to_csv("revenue_summary.csv")
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="revenue_summary",
    username="user", password="pass",
)

print("Done!")
```

---

## Configuration & Troubleshooting

### Client parameters

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
    base_url="https://app.mammoth.io/api/v2",
    timeout=30,
    job_timeout=60,
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `"https://app.mammoth.io/api/v2"` | API base URL. Change for custom Mammoth deployments. |
| `timeout` | `30` | HTTP request timeout in seconds. Applies to each individual API call. |
| `job_timeout` | `60` | Maximum time in seconds to poll a job to completion. Used by `jobs.wait_for_job()` and internally by View transformation methods. |

### Custom instance URLs

If your organization uses a custom Mammoth deployment:

```python
client = MammothClient(
    api_key="...",
    api_secret="...",
    workspace_id=11,
    base_url="https://your-instance.mammoth.io/api/v2",
)
```

The SDK normalizes the URL: if you pass `"https://your-instance.mammoth.io"` without the `/api/v2` suffix, it is appended automatically.

### Timeout tuning

**Request timeout:** The `timeout` parameter controls how long each HTTP request waits before raising `MammothAPIError`. Increase it for slow networks:

```python
client = MammothClient(..., timeout=120)  # 2 minutes per request
```

**Job timeout:** The `job_timeout` parameter controls how long the SDK polls when waiting for a job to complete. Increase it for large datasets or complex transformations:

```python
client = MammothClient(..., job_timeout=300)  # 5 minutes for jobs
```

Note that CSV exports have their own timeout parameter:

```python
view.export.to_csv("output.csv", timeout=600)  # 10 minutes
```

### No automatic retries

The SDK does not implement retries. If an API call fails due to a transient error, the exception is raised immediately. Implement retry logic at the application level if needed:

```python
import time
from mammoth import MammothAPIError

def with_retry(fn, max_retries=3, backoff=2):
    for attempt in range(max_retries):
        try:
            return fn()
        except MammothAPIError as e:
            if e.status_code and 400 <= e.status_code < 500:
                raise  # Do not retry client errors
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff ** attempt)
```

### Environment-based configuration

```python
import os

config = {
    "api_key": os.environ["MAMMOTH_API_KEY"],
    "api_secret": os.environ["MAMMOTH_API_SECRET"],
    "workspace_id": int(os.environ["MAMMOTH_WORKSPACE_ID"]),
    "base_url": os.getenv("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
    "timeout": int(os.getenv("MAMMOTH_TIMEOUT", "30")),
    "job_timeout": int(os.getenv("MAMMOTH_JOB_TIMEOUT", "60")),
}

client = MammothClient(**config)
```

### Troubleshooting

**Authentication errors**

Symptom: `MammothAuthError: Authentication failed`

- Verify your API key and secret are correct
- Confirm the `workspace_id` matches your account
- Check that the `base_url` points to the correct Mammoth instance
- Ensure your API credentials have not been revoked or rotated

```python
try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    if client.test_connection():
        print("Credentials are valid")
except MammothAuthError:
    print("Credentials are invalid")
```

**Column not found**

Symptom: `MammothColumnError: Column 'X' not found. Available columns: [...]`

- Check the exact column display name (case-sensitive)
- Call `view.refresh()` if the view was modified externally
- Print `view.display_names` to see available columns

```python
print(view.display_names)
# ['Sales Amount', 'Region', 'Order Date']
# Note: "Sales" vs "Sales Amount" matters
```

**Job timeout**

Symptom: `MammothJobTimeoutError: Job X timed out after Y seconds`

- Increase `job_timeout` on the client for large datasets
- For CSV exports, increase the `timeout` parameter on `to_csv()`
- Check the Mammoth dashboard to see if the job is still running

```python
client = MammothClient(..., job_timeout=300)
view.export.to_csv("output.csv", timeout=600)
```

**Job failed**

Symptom: `MammothJobFailedError: Job X failed: <reason>`

- Read the failure reason in `e.details["failure_reason"]`
- Check the Mammoth dashboard for detailed error logs
- Common causes: invalid column types for operations, data format issues

**project_id not set**

Symptom: `ValueError: project_id must be set on the client using client.set_project_id()`

Solution: Call `client.set_project_id(id)` before performing operations.

**Date columns not working**

Symptom: Date operations fail on columns uploaded from CSV.

Cause: CSV date columns are uploaded as TEXT type by default.

Solution: Convert to DATE type first:

```python
view.convert_type([ConversionSpec(column="Order Date", to=ColumnType.DATE)])
# Now date operations work
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
```

**Network / connection errors**

Symptom: `MammothAPIError: Connection error: ...` or `Request timeout: ...`

- Check your network connectivity
- Verify the `base_url` is reachable
- Increase the `timeout` for slow networks: `MammothClient(..., timeout=120)`

**Import errors**

Symptom: `ImportError` or `ModuleNotFoundError` when importing from mammoth

- Ensure the package is installed: `pip install mammoth-io`
- Verify Python 3.10+: `python --version`
- Check you are importing from the correct package: `from mammoth import MammothClient`
