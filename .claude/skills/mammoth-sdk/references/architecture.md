# SDK Architecture (v0.8.19)

## File Layout

```
mammoth/
├── __init__.py              # Public API exports (all enums, classes, constants)
├── client.py                # MammothClient + ViewsResource
├── view.py                  # View + ViewExport — core class with mixin inheritance
├── condition.py             # Condition + CompoundCondition
├── _expression_parser.py    # Math string expression parser (internal)
├── _param_templates.py      # Low-level task payload builders (internal)
├── helpers.py               # parse_path() URL utility
├── exceptions.py            # Exception hierarchy
├── _mixins/                 # View transformation mixin classes
│   ├── __init__.py
│   ├── _column_ops.py       # add_column, delete_columns, copy_columns, combine, convert, rename_columns
│   ├── _filter_ops.py       # filter_rows, set_values
│   ├── _math_ops.py         # math (string expression parser), small_large
│   ├── _text_ops.py         # text_transform, replace_values, bulk_replace, split, substring
│   ├── _date_ops.py         # extract_date, date_diff, increment_date
│   ├── _aggregate_ops.py    # pivot, window, crosstab
│   ├── _row_ops.py          # fill_missing, limit_rows, discard_duplicates, unnest, sort_rows
│   ├── _advanced_ops.py     # join, lookup, json_extract, gen_ai, sql
│   └── _host.py             # typing host for the mixins
├── api/                     # 42 API sub-clients, one per MammothClient attribute
│   ├── __init__.py
│   ├── _pagination.py
│   ├── activity_logs.py     # ActivityLogsAPI
│   ├── addons.py            # AddonsAPI
│   ├── agents.py            # AgentsAPI
│   ├── ai.py                # AIAPI — AI features
│   ├── annotations.py       # AnnotationsAPI
│   ├── automations.py       # AutomationsAPI
│   ├── batches.py           # BatchesAPI
│   ├── billing.py           # BillingAPI
│   ├── browse.py            # BrowseAPI
│   ├── checkpoints.py       # CheckpointsAPI
│   ├── clientapps.py        # ClientAppsAPI
│   ├── connector_ai.py      # ConnectorAIAPI
│   ├── connectors.py        # ConnectorsAPI
│   ├── dashboard_generated.py
│   ├── dashboards.py        # DashboardsAPI
│   ├── data_apps.py         # DataAppsAPI
│   ├── data_checks.py       # DataChecksAPI
│   ├── datasets.py          # DatasetsAPI
│   ├── dataviews.py         # DataviewsAPI
│   ├── derivatives.py       # DerivativesAPI
│   ├── exports.py           # ExportsAPI
│   ├── external_keys.py     # ExternalKeysAPI
│   ├── files.py             # FilesAPI — file upload
│   ├── folders.py           # FoldersAPI
│   ├── jobs.py              # JobsAPI — job tracking/polling
│   ├── notifications.py     # NotificationsAPI
│   ├── parameters.py        # ParametersAPI
│   ├── pipeline.py          # PipelineAPI — task management
│   ├── pipeline_versions.py # PipelineVersionsAPI
│   ├── projects.py          # ProjectsAPI
│   ├── reports.py           # ReportsAPI
│   ├── schedules.py         # SchedulesAPI
│   ├── snippets.py          # SnippetsAPI
│   ├── support.py           # SupportAPI
│   ├── templates.py         # TemplatesAPI
│   ├── trash.py             # TrashAPI
│   ├── user_profile.py      # UserProfileAPI
│   ├── users.py             # UsersAPI
│   ├── webhooks.py          # WebhooksAPI
│   ├── workflows.py         # WorkflowsAPI
│   ├── workspace.py         # WorkspaceAPI
│   └── workspaces.py        # WorkspacesAPI
├── _pure/                   # Pure (no HTTP, no View) param builders/resolvers over plain column metadata
├── models/                  # Pydantic v2 models for API schemas
│   ├── __init__.py
│   ├── automations.py
│   ├── batches.py
│   ├── clientapps.py
│   ├── connectors.py
│   ├── dashboard_generated.py
│   ├── dashboards.py
│   ├── datasets.py
│   ├── dataviews.py
│   ├── exports.py
│   ├── external_keys.py
│   ├── files.py
│   ├── folders.py
│   ├── jobs.py
│   ├── pagination.py
│   ├── pipeline.py          # Enums + dataclasses (SetValue, CopySpec, ConversionSpec, etc.)
│   ├── projects.py
│   ├── webhooks.py
│   └── workspaces.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

## Design Patterns

### Mixin Pattern for View Transformations

The View class inherits from 8 specialized mixin classes:

```python
class View(ColumnOpsMixin, FilterOpsMixin, MathOpsMixin, TextOpsMixin,
           DateOpsMixin, AggregateOpsMixin, RowOpsMixin, AdvancedOpsMixin):
    ...
```

Each mixin accesses View methods via `self._add_task()`, `self._resolve_column()`, etc.
Mixins use `# type: ignore[attr-defined]` for these cross-references.

### str,Enum Pattern

All enums extend `(str, Enum)` so they:
- Work as plain strings in JSON serialization (`json.dumps` handles them)
- Support string comparison: `ColumnType.TEXT == "TEXT"` is True
- Support string methods: `column_type.upper()` works
- Require enum values in method parameters (raw strings no longer accepted)

### Pipeline Task Flow

```
view.method()
  → Build task payload dict
  → self._add_task(payload)
    → client.pipeline.add_task(dataset_id, view_id, params)
    → If NOT draft mode:
        → Wait for pipeline completion (client.pipeline.wait_for_pipeline())
        → Refresh view metadata (self.refresh())
    → If draft mode: return immediately (task is queued)
  → Return API response
```

### Draft Mode

Views support draft mode where tasks are queued without executing the pipeline:

```python
async with view.draft():
    await view.filter_rows(...)   # queued, no pipeline run
    await view.math(...)          # queued, no pipeline run
# Pipeline runs once here for all queued tasks
```

The `_DraftContext` class (context manager) calls `enter_draft_mode()` on entry,
`submit_draft()` on clean exit, or `discard_draft()` on exception. The `_draft_mode`
flag on View controls whether `_add_task()` skips waiting and metadata refresh.

### Column Resolution

Display names → internal names mapping:
- `view.columns`: `{"emp_id": "column_abc1234567", ...}`
- `view._resolve_column("emp_id")` → `"column_abc1234567"`
- All public methods accept display names; internal names are resolved transparently

### Error Handling

```
MammothError (base)
├── MammothAPIError      # HTTP errors, timeouts, connection issues
│   └── MammothAuthError # 401 authentication failures
├── MammothColumnError   # Column not found in view
├── MammothTransformError # Transform validation failures
├── MammothValidationError # Bad arguments, raised before any request
├── MammothExportError   # Export finished but its result could not be resolved
├── MammothPaginationError # Paged read made no forward progress
├── MammothDeletionVerificationError # Delete not reconciled to absence
├── MammothJobTimeoutError # Job polling timeout
│   └── MammothPipelineTimeoutError # View pipeline wait timeout
└── MammothJobFailedError  # Job completed with failure
```

## Testing

- **Unit tests** (`tests/unit/`): ~2,400 tests, ~2s collect, no API calls needed
- **Integration tests** (`tests/integration/`, `tests/test_live_api.py`): live API, requires credentials
- Run: `pytest tests/unit/ -q` (unit) or `pytest tests/integration/ -q` (integration)

## Code Quality

- **Python**: >=3.12,<3.15 with `from __future__ import annotations` on all files
- **Type hints**: PEP 585 (`dict` not `Dict`, `X | None` not `Optional[X]`)
- **Formatting**: black (line-length 100)
- **Linting**: ruff (E, F, I, N, W, UP, B, SIM rules)
- **Models**: Pydantic v2 with `model_config` style
