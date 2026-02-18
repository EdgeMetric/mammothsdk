# SDK Architecture (v0.2.0)

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
│   ├── _column_ops.py       # add_column, delete_columns, copy_columns, combine, convert
│   ├── _filter_ops.py       # filter_rows, set_values
│   ├── _math_ops.py         # math (string expression + raw format)
│   ├── _text_ops.py         # text_transform, replace_values, bulk_replace, split, substring
│   ├── _date_ops.py         # extract_date, date_diff, increment_date
│   ├── _aggregate_ops.py    # pivot, window, crosstab
│   ├── _row_ops.py          # fill_missing, limit_rows, discard_duplicates, unnest
│   └── _advanced_ops.py     # join, lookup, json_extract, gen_ai, sql
├── api/                     # 23 API sub-client classes
│   ├── __init__.py
│   ├── activity_logs.py     # ActivityLogsAPI
│   ├── addons.py            # AddonsAPI
│   ├── ai.py                # AIAPI — AI features
│   ├── automations.py       # AutomationsAPI
│   ├── batches.py           # BatchesAPI
│   ├── browse.py            # BrowseAPI
│   ├── clientapps.py        # ClientAppsAPI
│   ├── connectors.py        # ConnectorsAPI
│   ├── dashboards.py        # DashboardsAPI
│   ├── datasets.py          # DatasetsAPI
│   ├── dataviews.py         # DataviewsAPI
│   ├── exports.py           # ExportsAPI
│   ├── external_keys.py     # ExternalKeysAPI
│   ├── files.py             # FilesAPI — file upload
│   ├── folders.py           # FoldersAPI
│   ├── jobs.py              # JobsAPI — job tracking/polling
│   ├── pipeline.py          # PipelineAPI — task management
│   ├── projects.py          # ProjectsAPI
│   ├── reports.py           # ReportsAPI
│   ├── schedules.py         # SchedulesAPI
│   ├── user_profile.py      # UserProfileAPI
│   ├── webhooks.py          # WebhooksAPI
│   └── workspace.py         # WorkspaceAPI
├── models/                  # Pydantic v2 models for API schemas
│   ├── __init__.py
│   ├── automations.py
│   ├── clientapps.py
│   ├── connectors.py
│   ├── dashboards.py
│   ├── datasets.py
│   ├── dataviews.py
│   ├── exports.py
│   ├── files.py
│   ├── folders.py
│   ├── jobs.py
│   ├── pipeline.py          # Enums + SetValue dataclass
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
- Accept both enum values AND raw strings in method parameters

### Pipeline Task Flow

```
view.method()
  → Build task payload dict
  → self._add_task(payload)
    → client.pipeline.add_task(dataset_id, view_id, params)
    → Wait for job completion (client.jobs.wait_for_job())
    → Refresh view metadata (self.refresh())
  → Return API response
```

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
├── MammothJobTimeoutError # Job polling timeout
└── MammothJobFailedError  # Job completed with failure
```

## Testing

- **Unit tests** (`tests/unit/`): 143 tests, ~0.5s, no API calls needed
- **Integration tests** (`tests/test_live_api.py`): 43 tests, ~6 min, requires release.mammoth.io
- Run: `pytest tests/unit/ -q` (unit) or `pytest tests/test_live_api.py -q` (integration)

## Code Quality

- **Python**: ^3.10 with `from __future__ import annotations` on all files
- **Type hints**: PEP 585 (`dict` not `Dict`, `X | None` not `Optional[X]`)
- **Formatting**: black (line-length 100)
- **Linting**: ruff (E, F, I, N, W, UP, B, SIM rules)
- **Models**: Pydantic v2 with `model_config` style
