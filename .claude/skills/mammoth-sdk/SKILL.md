---
name: mammoth-sdk
description: Practical knowledge base for the Mammoth Analytics Python SDK — client setup, View transformations, condition building, exports, and documented API sub-clients. Use this skill when the user asks to "use the SDK", "write SDK code", "apply a transformation", "build a condition", "export data", mentions "MammothClient", "View", "Condition", "Operator", "filter_rows", "set_values", "pivot", "window", "join", "export", or needs to understand or write code using the Mammoth Python SDK. Covers documented SDK workflows from authentication through transformations to exports.
---

# Mammoth Python SDK Knowledge Base (v0.8.22)

The Mammoth Python SDK (`mammoth` package) provides programmatic access to the Mammoth Analytics platform. It wraps the REST API with Pythonic classes, rich View objects, a condition builder with operator overloading, and export helpers.

## Quick Start

```python
from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

client = MammothClient(
    api_token="mm_your-token",
    workspace_id=11,
    base_url="https://app.mammoth.io/api/v2",  # default
)
client.set_project_id(10)

# Get a View and transform
view = await client.views.get(1039)
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
await view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)
await view.export.to_csv("output.csv")
```

The SDK is async (0.8.0+): every method that reaches the API is a coroutine — `await` it, including the async property `await view.is_draft_mode`. Pure builders stay sync (`client.set_project_id`, `Condition`, the spec models). Snippets here use top-level `await`; in a script, wrap them in `async def main()` and call `asyncio.run(main())`. Use `async with MammothClient(...) as client:` or `await client.close()`.

## Architecture Overview

See [references/architecture.md](references/architecture.md) for the full SDK architecture, file layout, and design patterns.

## Core Concepts

### MammothClient

Single entry point. Authenticates with an API token (`api_token="mm_..."`, sent as Bearer) or an `api_key`/`api_secret` pair (which needs `workspace_id`). All 42 sub-clients are attributes; the first 24 are below, the rest are listed after the table:

| Attribute | Class | Purpose |
|-----------|-------|---------|
| `client.views` | ViewsResource | Get/list/create View objects |
| `client.projects` | ProjectsAPI | Project CRUD |
| `client.datasets` | DatasetsAPI | Dataset CRUD |
| `client.dataviews` | DataviewsAPI | Raw dataview API |
| `client.pipeline` | PipelineAPI | Pipeline task management |
| `client.files` | FilesAPI | File upload/management |
| `client.exports` | ExportsAPI | Export operations |
| `client.jobs` | JobsAPI | Job tracking/polling |
| `client.folders` | FoldersAPI | Folder management |
| `client.connectors` | ConnectorsAPI | Third-party connectors |
| `client.dashboards` | DashboardsAPI | AI dashboards |
| `client.webhooks` | WebhooksAPI | Webhook management |
| `client.automations` | AutomationsAPI | Automation/scheduling |
| `client.ai` | AIAPI | AI features (profiling, SQL gen) |
| `client.workspaces` | WorkspaceAPI | Workspace management |
| `client.client_apps` | ClientAppsAPI | Client app management |
| `client.schedules` | SchedulesAPI | Schedule CRUD |
| `client.batches` | BatchesAPI | Dataset batch management |
| `client.external_keys` | ExternalKeysAPI | API key management |
| `client.activity_logs` | ActivityLogsAPI | Activity log queries |
| `client.browse` | BrowseAPI | Resource discovery |
| `client.user_profile` | UserProfileAPI | User profile management |
| `client.addons` | AddonsAPI | Workspace addons |
| `client.reports` | ReportsAPI | Report listing |

Also on the client (method names in [references/api-reference.md](references/api-reference.md#other-sub-clients)): `agents`, `annotations`, `billing`, `checkpoints`, `connector_ai`, `data_apps`, `data_checks`, `derivatives`, `notifications`, `parameters`, `pipeline_versions`, `snippets`, `support`, `templates`, `trash`, `users`, `workflows`, and `workspace` (cross-workspace calls; note `workspaces` is `WorkspaceAPI`).

### View Object

Rich domain object for a dataview. Created via `client.views.get(id)` or `client.views.create(dataset_id)`.

**Architecture**: The View class uses a mixin pattern — transformation methods are organized into 8 mixin classes in `mammoth/_mixins/` (plus `_host.py`, the typing host):

- `ColumnOpsMixin`: add_column, delete_columns, copy_columns, combine_columns, convert_type, rename_columns
- `FilterOpsMixin`: filter_rows, set_values
- `MathOpsMixin`: math (string expression parser), small_large (Nth smallest/largest across columns)
- `TextOpsMixin`: text_transform, replace_values, bulk_replace, split_column, substring
- `DateOpsMixin`: extract_date, date_diff, increment_date
- `AggregateOpsMixin`: pivot, window, crosstab (materialises a NEW dataset; `dataset_name` is required and the call returns its id)
- `RowOpsMixin`: fill_missing, limit_rows, discard_duplicates, unnest, sort_rows
- `AdvancedOpsMixin`: join, lookup, json_extract, gen_ai, generate_sql, add_sql

**Metadata**: `view.columns`, `view.display_names`, `view.column_types`, `view.name`, `view.id`; `await view.refresh()`, `view.get_metadata()`, `view.get_column_mapping()`
**Data access**: `view.data(limit=100)`
**Pipeline management**: `view.list_tasks()`, `view.delete_task(id)`, `view.preview_task(spec)`
**Draft mode**: `view.draft()` (async context manager), `view.enter_draft_mode()`, `view.submit_draft()`, `view.discard_draft()`, `view.set_auto_run(bool)`
**Exports**: `view.export.to_csv()`, `view.export.to_postgres()`, etc.
**Save as dataset**: `await view.branch_out(dataset_name, target_ds_id=None, save_as_mode=SaveAsDatasetMode.REPLACE, column_mapping=None, condition=None)` returns the dataset id (new when `target_ds_id` is None); shortcut for `view.export.to_dataset`.
**Dry run**: `with view.build_only():` validates and builds each transform, returns `{"status": "validated", "task_spec": ...}` and sends nothing.

### Condition Builder

Pythonic filter conditions with `&` (AND) and `|` (OR) operator overloading:

```python
from mammoth import Condition, Operator

# Simple
cond = Condition("Sales", Operator.GTE, 1000)

# Compound
cond = (
    Condition("department", Operator.EQ, "Engineering")
    & Condition("base_salary", Operator.GTE, 80000)
)

# OR
cond = (
    Condition("department", Operator.EQ, "Engineering")
    | Condition("department", Operator.EQ, "Sales")
)

# Use with transformations
await view.filter_rows(cond)
await view.set_values(
    new_column="Label",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Priority", condition=cond),
        SetValue("Normal"),
    ],
)
```

### Math String Expressions

The `math()` method accepts human-readable string expressions:

```python
# String expression — column names resolved automatically
await view.math("Price * Quantity", new_column="Total")
await view.math("(Price + Tax) * 1.1", new_column="Grand Total")
```

### Join with View Objects

The `join()` method accepts View objects for automatic display name resolution:

```python
from mammoth import JoinType, JoinKeySpec

other = await client.views.get(2050)
await view.join(
    foreign_view=other,          # View object — display names auto-resolved
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Name"],  # Simple list of display names
)
```

**Operators** (from `mammoth.Operator`):
- Comparison: `GT`, `LT`, `GTE`, `LTE`, `EQ`, `NE`
- List: `IN_LIST`, `NOT_IN_LIST`, `CONTAINS`, `NOT_CONTAINS`
- String: `STARTS_WITH`, `ENDS_WITH`, `NOT_STARTS_WITH`, `NOT_ENDS_WITH`
- Null: `IS_EMPTY`, `IS_NOT_EMPTY`
- Aggregate: `IS_MAXVAL`, `IS_NOT_MAXVAL`, `IS_MINVAL`, `IS_NOT_MINVAL`
- Other: `IN_RANGE`, `ICONTAINS`

## Transformations Reference

See [references/transformations.md](references/transformations.md) for documented transformation methods with signatures, payload structures, and examples.

## API Sub-Clients Reference

See [references/api-reference.md](references/api-reference.md) for all API sub-client methods.

## Common Patterns & Examples

See [references/examples.md](references/examples.md) for end-to-end workflow examples.

## Key Enums

All enums extend `str, Enum` — they work as both enum values AND plain strings in JSON serialization.

| Enum | Values | Used By |
|------|--------|---------|
| `Operator` | GT, LT, GTE, LTE, EQ, NE, IN_LIST, NOT_IN_LIST, CONTAINS, NOT_CONTAINS, ICONTAINS, STARTS_WITH, ENDS_WITH, NOT_STARTS_WITH, NOT_ENDS_WITH, IS_EMPTY, IS_NOT_EMPTY, IS_MAXVAL, IS_NOT_MAXVAL, IS_MINVAL, IS_NOT_MINVAL, IN_RANGE | Condition builder |
| `ColumnType` | TEXT, NUMERIC, DATE | add_column, set_values, copy_columns, combine, math, window |
| `JoinType` | INNER, LEFT, RIGHT, OUTER | join() |
| `TextCase` | UPPER, LOWER, TITLE | text_transform() |
| `DateComponent` | year, month, day, hour, minute, second, millisecond, week, quarter, weekday, day_of_year, weekday_text, month_text, month_year, year_month, year_month_number, year_month_day, year_month_day_as_date, month_day_year, month_day_year_hour_minute_second, hour_minute_second, hour_minute_second_millisecond | extract_date() |
| `DateDiffUnit` | YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEK, QUARTER | date_diff() |
| `WindowFunction` | ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, SUM, AVG, MIN, MAX, COUNT, FIRST_VALUE, LAST_VALUE, STDDEV, VARIANCE, PERCENT_RANK, NTILE | window() |
| `WindowRange` | UNBOUNDED, RUNNING | window() |
| `AggregateFunction` | SUM, AVG, MIN, MAX, COUNT, COUNT_DISTINCT, STDDEV, VARIANCE, MEDIAN, FIRST, LAST, CONCAT | pivot(), crosstab() |
| `FillDirection` | FIRST_VALUE, LAST_VALUE | fill_missing() |
| `FilterType` | SHOW, REMOVE | filter_rows() |
| `SortDirection` | ASC, DESC | order_by in window, pivot, limit_rows |
| `MathOperator` | +, -, *, /, % | math expression parser |
| `SubstringDirection` | START, END, LEFT, RIGHT | substring() |
| `JsonType` | OBJECT, LIST | json_extract() |
| `JsonOpType` | JSON_OBJECT_TO_COLUMNS, JSON_LIST_TO_ROWS | json_extract() |
| `ExportFileType` | CSV, JSON, PARQUET | to_s3() |
| `TaskType` | SET, SELECT, MATH, JOIN, ... (27 values) | Pipeline task identification |
| `ProviderType` | FIXED, EXPRESSION | set_values() |
| `SaveAsDatasetMode` | REPLACE (`REPLACE_IN_DS`), APPEND (`APPEND_TO_DS`) | branch_out(), crosstab(), export.to_dataset() |
| `SmallLargeFunction` | SMALL, LARGE | small_large() |

## Dataclasses

| Class | Fields | Used By |
|-------|--------|---------|
| `SetValue` | `value: Any`, `condition: Condition \| CompoundCondition \| None` | set_values() |
| `CopySpec` | `source: str`, `as_name: str \| None`, `type: ColumnType = TEXT`, `condition: Condition \| None`, `destination: str \| None` | copy_columns() |
| `ConversionSpec` | `column: str`, `to: ColumnType`, `format: str \| None` | convert_type() |
| `AggregationSpec` | `column: str`, `function: AggregateFunction`, `as_name: str \| None`, `delimiter: str \| None` | pivot() |
| `CrosstabSpec` | `function: AggregateFunction`, `column: str \| None` | crosstab() |
| `JoinKeySpec` | `left: str`, `right: str` | join() on |
| `JoinSelectSpec` | `column: str`, `alias: str \| None` | join() select |
| `SplitColumnSpec` | `name: str`, `type: ColumnType = TEXT` | split_column() |
| `BulkReplaceMapping` | `search: list[str]`, `replace: str` | bulk_replace() |
| `DateDelta` | `years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds` (all `int = 0`) | increment_date() |
| `JsonExtractionSpec` | `key: str`, `as_name: str \| None`, `type: ColumnType = TEXT` | json_extract() |

## Exceptions

| Exception | When |
|-----------|------|
| `MammothError` | Base exception |
| `MammothAPIError` | Any API call fails (non-2xx, timeout, connection error) |
| `MammothAuthError` | Authentication fails (401); subclass of `MammothAPIError` |
| `MammothColumnError` | Column display name not found in view |
| `MammothTransformError` | Transformation validation fails |
| `MammothJobTimeoutError` | Job polling exceeds timeout |
| `MammothPipelineTimeoutError` | Waiting for a view's pipeline exceeds `pipeline_timeout`; subclass of `MammothJobTimeoutError` |
| `MammothJobFailedError` | Job completes with failure status |
| `MammothValidationError` | Input rejected locally before any request (e.g. `small_large` with no columns) |
| `MammothExportError` | An export completes but its result (e.g. the new dataset) cannot be resolved; `export_pending` may be set |
| `MammothPaginationError` | A paginated read cannot prove forward progress |
| `MammothDeletionVerificationError` | A delete acknowledgement cannot be reconciled to the resource's absence |

## Configuration Constants

```python
from mammoth import DEFAULT_TIMEOUT, DEFAULT_JOB_TIMEOUT, DEFAULT_PIPELINE_TIMEOUT, DEFAULT_JOB_POLL_SECONDS

# DEFAULT_TIMEOUT = 30   seconds — max time for any single API call
# DEFAULT_JOB_TIMEOUT = 60   seconds — max time to poll a job to completion
# DEFAULT_PIPELINE_TIMEOUT = 3600   seconds — max time to wait for a pipeline run
# DEFAULT_JOB_POLL_SECONDS = 2   seconds between job polls

# Override per-client:
client = MammothClient(
    api_token="mm_...", workspace_id=1,
    timeout=60,       # custom API timeout
    job_timeout=120,  # custom job timeout
    pipeline_timeout=7200,  # custom pipeline wait
)
```

## Workflow for Writing SDK Code

1. **Initialize client**: Create `MammothClient` with credentials, set project ID
2. **Get a View**: `client.views.get(view_id)` or `client.views.create(dataset_id, name="...")`
3. **Inspect columns**: Check `view.display_names` and `view.column_types`
4. **Apply transformations**: Chain methods — each waits for completion before returning
5. **Export results**: `view.export.to_csv()`, `view.export.to_postgres()`, etc.

For large datasets with many transformations, use draft mode to batch tasks:
1. Enter draft mode: `async with view.draft():` (or `view.enter_draft_mode()`)
2. Add all transformations — they queue without running the pipeline
3. On exit the pipeline runs once, metadata refreshes, and draft mode exits

## Important Notes

- **Column resolution**: All transformation methods accept display names (e.g. "Sales"), not internal names (e.g. "column_1"). The SDK resolves them automatically.
- **Async pipeline**: Each transformation is an async pipeline task. The SDK waits for job completion and refreshes metadata after each task (unless in draft mode).
- **Draft mode**: Use `async with view.draft():` to batch multiple transformations — the pipeline runs once on exit instead of after each task. See [references/examples.md](references/examples.md) for usage.
- **Chaining**: Transformations can be chained — the SDK handles sequencing automatically.
- **Immutable views**: Use `client.views.create(dataset_id)` to create a working copy before applying transformations.
- **Date columns**: CSV-uploaded date columns are TEXT type. Convert with `view.convert_type([ConversionSpec(column="date_col", to=ColumnType.DATE)])` before date operations.
- **Typed dataclasses**: Transformation methods accept typed dataclasses (e.g. `CopySpec`, `ConversionSpec`, `DateDelta`). Raw dicts also work as a fallback.

## Key File Paths

| File | Purpose |
|------|---------|
| `mammoth/client.py` | MammothClient, ViewsResource, auth, request handling |
| `mammoth/view.py` | View class (core), ViewExport |
| `mammoth/_mixins/*.py` | 8 mixin classes for View transformation methods |
| `mammoth/_expression_parser.py` | Math string expression parser |
| `mammoth/condition.py` | Condition, CompoundCondition — filter builder |
| `mammoth/models/pipeline.py` | Enums and dataclasses (SetValue, CopySpec, ConversionSpec, etc.) |
| `mammoth/_param_templates.py` | Internal task payload builders |
| `mammoth/exceptions.py` | Exception hierarchy |
| `mammoth/helpers.py` | parse_path() URL parser |
| `mammoth/__init__.py` | Public API exports |
| `mammoth/api/*.py` | 42 API sub-client classes (one module each, a few share) |
| `mammoth/models/*.py` | Pydantic models for API schemas |
| `tests/unit/` | ~2,400 unit tests (no API calls) |
| `tests/integration/`, `tests/test_live_api.py` | live API tests (need credentials) |
