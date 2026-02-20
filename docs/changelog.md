# Changelog

## v0.3.0

### Breaking changes

- **Removed `dataset_id` from ViewsResource methods** — `views.get()`, `views.list()`, `views.delete()`, `views.bulk_delete()`, `get_view()`, and `branch_out()` no longer accept a `dataset_id` parameter. The dataset is auto-detected via the pipeline API. `views.create()` still requires `dataset_id`.
- **Dict fallback paths removed** — all transformation methods now accept only typed dataclasses, not raw dicts:
    - `copy_columns()`: `list[CopySpec]` (not `list[dict]`)
    - `convert_type()`: `list[ConversionSpec]` (not `list[dict]`)
    - `set_values()`: `list[SetValue]` (not `list[dict]`)
    - `pivot()`: `list[AggregationSpec]` (not `list[dict]`)
    - `crosstab()`: `CrosstabSpec` (not `dict`)
    - `split_column()`: `list[SplitColumnSpec]` (not `list[dict]`)
    - `bulk_replace()`: `list[BulkReplaceMapping]` (not `list[dict]`)
    - `increment_date()`: `DateDelta` (not `dict`)
    - `join()`: `list[JoinKeySpec]` and `list[JoinSelectSpec]` (not `list[dict]`)
    - `json_extract()`: `list[JsonExtractionSpec]` and `JsonOpType` (not `list[dict]` and `str`)
    - `math()`: `str` only (removed `list[dict]` expression format)
- **String fields changed to enums** in dataclasses:
    - `CopySpec.type`: `ColumnType` (was `str`)
    - `ConversionSpec.to`: `ColumnType` (was `str`)
    - `AggregationSpec.function`: `AggregateFunction` (was `str | AggregateFunction`)
    - `CrosstabSpec.function`: `AggregateFunction` (was `str | AggregateFunction`)
    - `JsonExtractionSpec.type`: `ColumnType` (was `str`)
- **`to_s3()` file_type** — now `ExportFileType` enum (was `str`)

### Added

- **`SplitColumnSpec`** dataclass for `split_column()` new column specs
- **`BulkReplaceMapping`** dataclass for `bulk_replace()` search/replace mappings
- **`DateDelta`** dataclass for `increment_date()` with named fields (`years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds`)
- **`JsonOpType`** enum — `JSON_OBJECT_TO_COLUMNS`, `JSON_LIST_TO_ROWS`
- **`ExportFileType`** enum — `CSV`, `JSON`, `PARQUET`
- **`HandlerType`** and **`TriggerType`** enums re-exported from top-level `mammoth` package

---

## v0.2.4

### Added

- **Draft mode** — batch multiple transformations and run the pipeline once:
    - `view.draft()` context manager (recommended): enters draft on entry, submits on clean exit, discards on exception
    - `view.enter_draft_mode()`, `view.submit_draft()`, `view.discard_draft()` for explicit control
    - `view.set_auto_run(enabled)` to toggle auto-run
    - `view.is_draft_mode` property to check current state
- **`DraftCommand` enum** — `ENTER`, `SUBMIT`, `DISCARD`, `EXIT` values for draft mode operations

### Fixed

- **`draft_mode()` API payload** — both `PipelineAPI.draft_mode()` and `DataviewsAPI.draft_mode()` now send `{"draft_operation": command}` instead of the incorrect `{"command": command}`

---

## v0.2.3

### Fixed

- **`_build_column_maps` now uses `taskwise_info` exclusively** — removed incorrect use of `dependencies_info.dependents` for column metadata resolution. `taskwise_info[last_seq]["metadata"]` is the authoritative post-pipeline column list; falls back to top-level `metadata` only for fresh views with no tasks.

---

## v0.2.2

### Fixed

- **`display_names` not updated after transforms** — `_build_column_maps` now reads column metadata from `taskwise_info[last_seq]["metadata"]` (the authoritative post-pipeline column list), so columns added by `math`, `set_values`, `add_column`, and other transforms appear immediately in `view.display_names`, `view.columns`, and `view.column_types`.

### Added

- **`view.get_metadata()`** — returns the current column list as `[{"display_name", "internal_name", "type"}, ...]`. Useful for inspecting all columns (including pipeline-added ones) after transforms.

---

## v0.2.0

Major release with rich View objects, transformation methods, and the condition builder.

### Added

- **View objects** -- rich domain objects wrapping Mammoth dataviews with 25+ transformation methods:
    - Filter: `filter_rows`, `set_values`
    - Math: `math` (string expression parser)
    - Column ops: `add_column`, `delete_columns`, `copy_columns`, `combine_columns`, `convert_type`
    - Text: `text_transform`, `replace_values`, `bulk_replace`, `split_column`, `substring`
    - Date: `extract_date`, `date_diff`, `increment_date`
    - Aggregation: `pivot`, `window`, `crosstab`
    - Row ops: `fill_missing`, `limit_rows`, `discard_duplicates`, `unnest`
    - Advanced: `join`, `lookup`, `json_extract`, `gen_ai`, `generate_sql`, `add_sql`, `sql`
- **Condition builder** -- `Condition` and `CompoundCondition` classes with `&` (AND) and `|` (OR) operator overloading
- **Enums** for all transformation parameters: `Operator`, `ColumnType`, `JoinType`, `TextCase`, `DateComponent`, `DateDiffUnit`, `WindowFunction`, `WindowRange`, `FillDirection`, `AggregateFunction`, `SortDirection`, `MathOperator`, `SubstringDirection`, `JsonType`, `FilterType`, `ProviderType`, `TaskType`, `ValueType`
- **SetValue dataclass** for conditional value specifications
- **ViewExport** class with export methods: `to_csv`, `to_s3`, `to_postgres`, `to_mysql`, `to_bigquery`, `to_redshift`, `to_elasticsearch`, `to_ftp`, `to_sftp`, `to_email`, `to_dataset`, `publish_to_db`
- **ViewsResource** (`client.views`) for get, list, create, delete, and bulk_delete operations returning rich View objects
- **MCP server** for Model Context Protocol integration with AI assistants
- **New exceptions**: `MammothTransformError`, `MammothColumnError`
- **New sub-clients**: `ai`, `connectors`, `dashboards`, `webhooks`, `automations`, `schedules`, `batches`, `browse`, `activity_logs`, `external_keys`, `client_apps`, `addons`, `reports`, `user_profile`, `workspaces`, `folders`
- `workspace_id` as a required constructor parameter on `MammothClient`
- `set_project_id()` method on the client
- `get_view()` convenience method on the client
- `find_dataset_for_dataview()` method on the client
- `parse_path()` helper for extracting IDs from Mammoth URLs
- Type hints throughout the codebase
- Pydantic response models for pipeline tasks and exports

### Changed

- `MammothClient` constructor now requires `workspace_id`
- Default `base_url` is now `"https://app.mammoth.io/api/v2"`
- `DEFAULT_TIMEOUT` is 30 seconds; `DEFAULT_JOB_TIMEOUT` is 60 seconds

## v0.1.0

Initial release.

### Added

- `MammothClient` with API key/secret authentication
- File upload and management via `client.files`
- Job tracking and polling via `client.jobs`
- CSV and S3 export via `client.exports`
- Dataset and dataview CRUD via `client.datasets` and `client.dataviews`
- Pipeline task management via `client.pipeline`
- Project management via `client.projects`
- Exception hierarchy: `MammothError`, `MammothAPIError`, `MammothAuthError`, `MammothJobTimeoutError`, `MammothJobFailedError`
- Context manager support for automatic session cleanup
