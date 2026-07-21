# Normative appendix: SDK view and transformation command catalog

This appendix is normative for the public SDK surface inspected on 2026-07-21.
It covers each public method declared by `View`, `ViewsResource`, `PipelineAPI`,
the typing-only `ViewHost` protocol, and the eight transformation mixins
inherited by `View`. `ViewExport` belongs to the export command manifest and is
outside this appendix.

The production OpenAPI inventory remains the coverage authority. A record here
does not prove that its endpoint exists in production. Reconcile every record
with the pinned OpenAPI snapshot before implementation. If OpenAPI and the
current SDK differ, extend or correct the public typed SDK first.

## Catalog rules

- Each signature below omits only `self`. Types and Python defaults match the
  current public SDK. `_list` is the source alias for the built-in `list`.
- `VIEW_ID`, `DATASET_ID`, `TASK_ID`, `TARGET_DS_ID`, and every other resource
  ID are positive integers. Resolve a view's dataset through a new public typed
  SDK method. Do not scan from CLI code or call a private resolver.
- Every command also accepts the global options in plan 02. `--input FILE|-`
  follows plan 02: strict JSON or YAML, `extra="forbid"`, safe YAML, explicit
  stdin format, and scalar flags override document fields. A repeatable flag
  replaces the complete document list for that field.
- Conditions are document-only and use the shared recursive condition contract
  in plan 02. No command in this appendix adds condition flags.
- Resolve all display column names before mutation. Reject an empty name, an
  empty required list, duplicates where ordering does not require duplicates,
  and an unresolved column before an SDK mutation call.
- Exactly one of `new_column` and `existing_column` is required whenever both
  appear in a request. An existing destination must resolve before mutation.
- Unless a row says otherwise, a transformation returns
  `PipelineMutationResult`, uses `always_wait`, is a `reversible_pipeline`
  mutation without confirmation, supports server-backed draft state, and can
  be undone only by `view task delete VIEW_ID TASK_ID` when the result contains
  a stable task ID. Do not promise undo without that ID.
- `always_wait` means wait for the submitted job and final pipeline state when
  auto-run is active. In server-backed draft mode, return the queued task and
  draft state without pretending that output data is final. Do not add
  `--no-wait` until the SDK has a stable typed start result.
- The standard transformation acceptance class is
  `live_disposable_project`. Its live tests are specified but blocked by `B8`
  until the test principal can create a dataset or upload a file.
- Test columns contain representative IDs. Each canonical command must also
  receive all applicable IDs required by plan 04.

## Shared request vocabulary

Use the exact SDK enum values below as case-insensitive CLI input. Emit the
shown canonical value in machine output and SDK conversion.

| Type | Accepted canonical values |
|---|---|
| `ColumnType` | `TEXT`, `NUMERIC`, `DATE` |
| `FilterType` | `SHOW`, `REMOVE` |
| `TextCase` | `UPPER`, `LOWER`, `TITLE` |
| `SmallLargeFunction` | `SMALL`, `LARGE` |
| `FillDirection` | `FIRST_VALUE`, `LAST_VALUE` |
| `SortDirection` | `ASC`, `DESC` |
| `SubstringDirection` | `START`, `END`, `LEFT`, `RIGHT` |
| `JoinType` | `INNER`, `LEFT`, `RIGHT`, `OUTER` |
| `JsonType` | `OBJECT`, `LIST` |
| `JsonOpType` | `JSON_OBJECT_TO_COLUMNS`, `JSON_LIST_TO_ROWS` |
| `SaveAsDatasetMode` | `REPLACE_IN_DS`, `APPEND_TO_DS` |
| `WindowRange` | `UNBOUNDED`, `RUNNING` |
| `WindowFunction` | `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `FIRST_VALUE`, `LAST_VALUE`, `STDDEV`, `VARIANCE`, `PERCENT_RANK`, `NTILE` |
| `AggregateFunction` | `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `COUNT_DISTINCT`, `STDDEV`, `VARIANCE`, `MEDIAN`, `FIRST`, `LAST`, `CONCAT` |
| `DateDiffUnit` | `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`, `WEEK`, `QUARTER` |
| `DateComponent` | `year`, `month`, `day`, `hour`, `minute`, `second`, `week`, `quarter`, `day_of_week`, `day_of_year`, `weekday_text`, `month_text`, `year_month`, `year_month_number`, `year_week`, `year_quarter`, `month_day`, `hour_minute`, `hour_minute_second`, `year_month_day`, `year_month_day_as_date`, `month_day_year_hour_minute_second`, `date_only` |

All nested records reject unknown fields. These are the strict CLI document
shapes and their conversions to current SDK dataclasses:

| Document field | Strict shape and validation |
|---|---|
| `copies` | Nonempty list of `{source, as_name?, type="TEXT", destination?, condition?}`. `as_name` and `destination` are mutually exclusive. If both are absent, the new-column `as_name` defaults to `"<source> Copy"`. Convert to `CopySpec`. |
| `conversions` | Nonempty list of `{column, to, format?}`. `format` is allowed only for a `DATE` target. Convert to `ConversionSpec`. |
| `values` | Nonempty list of `{value, condition?}`. `value` is required and can be null. Convert to `SetValue`. |
| `mapping` | Nonempty list of `{search, replace}`. `search` is a nonempty unique string list. `replace` is required and can be empty. Convert to `BulkReplaceMapping`. |
| `new_columns` | Nonempty list of `{name, type="TEXT"}` with unique nonempty names. Convert to `SplitColumnSpec`. |
| `delta` | `{years=0, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0}`. Require at least one nonzero signed integer. Convert to `DateDelta`. |
| `aggregations` | Nonempty list of `{column, function, as_name?, delimiter?}`. `delimiter` is allowed only for `CONCAT`. Convert to `AggregationSpec`. |
| `order_by` | Nonempty list of `{column, direction}`. Convert each item to `[column, SortDirection]`. |
| `on` | Nonempty list of `{left, right}` with unique pairs. Convert to `JoinKeySpec`. |
| `select` for join | Nonempty list of `{column, alias?}`. Convert to `JoinSelectSpec`; plain SDK strings are normalized to this shape. |
| `extractions` | Nonempty list of `{key, as_name?, type="TEXT"}` with unique output names. Convert to `JsonExtractionSpec`. |
| `select` for crosstab | Nonempty list of `{function, column?}`. `COUNT` forbids `column`; the other supported crosstab functions require it. Convert to `CrosstabSpec`. Crosstab rejects `MEDIAN`, `FIRST`, `LAST`, and `CONCAT` even though pivot accepts them. |
| `column_mapping` | Object of unique nonempty source names to nonempty destination names. |
| `patches` | Nonempty typed discriminated list. Do not expose arbitrary JSON Patch until the OpenAPI operation and permitted paths are frozen. |
| `task` | One member of the typed discriminated pipeline-task union. Do not expose a free-form dictionary. |

The standard result models are `ViewResult`, `ViewListResult`, `ViewDataResult`,
`PipelineResult`, `PipelineTaskResult`, `PipelineTaskListResult`,
`PipelineMutationResult`, `DraftStateResult`, `TaskPreviewResult`, and
`DatasetMaterializationResult`. Add these as public typed SDK or CLI contract
models before handlers. `ViewResult` includes `id`, `dataset_id`, `name`, and
ordered column metadata. It never serializes the client, session, or export
helper.

Policy cells have this fixed order: **wait; draft; undo; safety; live**.
`no-draft` means that draft state does not affect the operation. `task-delete`
means conditional rollback by stable task ID. `none` means no rollback claim.

## `mammoth.client.ViewsResource`

| Exact public signature | Canonical command and exact local input | Result and policy | Blockers | Representative tests |
|---|---|---|---|---|
| `get(view_id: int) -> View` | `view get VIEW_ID` | `ViewResult`; `not_async; no-draft; none; read; live_disposable_project` | B1, B2, B8 | `UT-VIEW-GET`, `CT-VIEW-GET-JSON`, `LT-VIEW-GET` |
| `list(dataset_id: int) -> _list[View]` | `view list DATASET_ID`; no local flags. Do not add `--all` yet. | `ViewListResult`; `not_async; no-draft; none; read; live_disposable_project`; `single_page` until pagination is fixed | B2, B5, B8 | `UT-VIEW-LIST`, `CT-VIEW-LIST-JSON`, `LT-VIEW-LIST` |
| `create(dataset_id: int, name: str = "View", clone_from: int \| None = None) -> View` | `view create DATASET_ID [--name TEXT] [--clone-from VIEW_ID]`; nonempty name, default `View`. | `ViewResult`; `always_wait; no-draft; view-delete; benign_mutation; live_disposable_project` | B2, B4, B8 | `UT-VIEW-CREATE`, `CT-VIEW-CREATE-WAIT`, `LT-VIEW-CREATE` |
| `delete(view_id: int) -> dict[str, Any]` | `view delete VIEW_ID... [--yes]`; one ID calls `delete`; more than one uses the repaired bulk path. Prompt or `--yes` is required. | `DeleteResult`; `always_wait; no-draft; none; destructive; live_disposable_project` | B1, B2, B4, B6, B8 | `UT-VIEW-DELETE`, `CT-VIEW-DELETE-ERROR`, `LT-VIEW-DELETE` |
| `bulk_delete(view_ids: _list[int]) -> dict[str, Any]` | Alias of `view delete VIEW_ID...`; require at least two unique IDs. For more than one ID also require `--confirm` with the sorted comma-separated IDs. | `BulkDeleteResult`; `always_wait; no-draft; none; high_impact; live_disposable_project` | B1, B2, B4, B6, B8 | `UT-VIEW-BULK-DELETE`, `CT-VIEW-BULK-DELETE-ERROR`, `LT-VIEW-BULK-DELETE` |

## Methods declared by `mammoth.view.View`

| Exact public signature | Canonical command and exact local input | Result and policy | Blockers | Representative tests |
|---|---|---|---|---|
| `data(limit: int = 400, offset: int = 1, columns: list[str] \| None = None, condition: Condition \| CompoundCondition \| None = None, sort: str \| None = None) -> dict[str, Any]` | `view data query VIEW_ID [--limit 400] [--offset 1] [--column TEXT]... [--sort TEXT] [--input FILE\|-]`; positive limit and offset. Condition is document-only. | `ViewDataResult`; `always_wait; no-draft; none; read; live_disposable_project`; `offset` only after B5, otherwise `single_page` | B2, B4, B5, B8 | `UT-VIEW-DATA-QUERY`, `CT-VIEW-DATA-QUERY-JSON`, `LT-VIEW-DATA-QUERY` |
| `refresh() -> View` | SDK alias of `view get VIEW_ID`; a CLI process always fetches a fresh view, so no `refresh` command exists. | `ViewResult`; `not_async; no-draft; none; read; live_disposable_project` | B2, B8 | `UT-VIEW-REFRESH-ALIAS`, `LT-VIEW-GET` |
| `get_metadata() -> list[dict[str, Any]]` | Local projection in `view get VIEW_ID`; machine output field `data.columns`. | `ColumnMetadataListResult`; `not_async; no-draft; none; read; live_disposable_project` | B2, B8 | `UT-VIEW-GET-METADATA-ALIAS`, `CT-VIEW-GET-JSON` |
| `list_tasks() -> list[dict[str, Any]]` | Alias of `view task list VIEW_ID`. | `PipelineTaskListResult`; `not_async; no-draft; none; read; live_disposable_project` | B2, B5, B8 | `UT-VIEW-TASK-LIST-ALIAS`, `LT-VIEW-TASK-LIST` |
| `delete_task(task_id: int) -> dict[str, Any]` | Alias of `view task delete VIEW_ID TASK_ID [--yes]`. | `PipelineMutationResult`; `always_wait; server-aware; none; destructive; live_disposable_project` | B2, B3, B4, B8 | `UT-VIEW-TASK-DELETE-ALIAS`, `CT-VIEW-TASK-DELETE-WAIT`, `LT-VIEW-TASK-DELETE` |
| `preview_task(task_spec: dict[str, Any]) -> dict[str, Any]` | Alias of `view task preview VIEW_ID --input FILE\|-`; strict `task`, no free-form dictionary or flags. | `TaskPreviewResult`; `always_wait; no-draft; none; read; live_disposable_project` | B2, B4, B9, B8 | `UT-VIEW-TASK-PREVIEW-ALIAS`, `LT-VIEW-TASK-PREVIEW` |
| `is_draft_mode -> bool (property)` | `view draft status VIEW_ID`; never read process-local state. | `DraftStateResult`; `not_async; server-state; none; read; live_disposable_project` | B3, B11, B8 | `UT-VIEW-DRAFT-STATUS`, `CT-VIEW-DRAFT-STATUS-JSON`, `LT-VIEW-DRAFT-STATUS` |
| `enter_draft_mode() -> dict[str, Any]` | `view draft enter VIEW_ID`; idempotent only when server state proves it is already active. | `DraftStateResult`; `always_wait; server-state; discard; reversible_pipeline; live_disposable_project` | B3, B4, B11, B8 | `UT-VIEW-DRAFT-ENTER`, `CT-VIEW-DRAFT-ENTER-WAIT`, `LT-VIEW-DRAFT-ENTER` |
| `submit_draft() -> dict[str, Any]` | `view draft submit VIEW_ID`; require server draft state before mutation. | `PipelineMutationResult`; `always_wait; server-state; task-delete; reversible_pipeline; live_disposable_project` | B3, B4, B11, B12, B8 | `UT-VIEW-DRAFT-SUBMIT`, `CT-VIEW-DRAFT-SUBMIT-WAIT`, `LT-VIEW-DRAFT-SUBMIT` |
| `discard_draft() -> dict[str, Any]` | `view draft discard VIEW_ID [--yes]`; prompt or `--yes` because queued tasks are deleted. | `DraftStateResult`; `always_wait; server-state; none; destructive; live_disposable_project` | B3, B4, B11, B8 | `UT-VIEW-DRAFT-DISCARD`, `CT-VIEW-DRAFT-DISCARD-ERROR`, `LT-VIEW-DRAFT-DISCARD` |
| `set_auto_run(enabled: bool) -> dict[str, Any]` | `view draft auto-run VIEW_ID --enabled\|--disabled`; exactly one required, no implicit default. | `DraftStateResult`; `always_wait; server-state; inverse-toggle; reversible_pipeline; live_disposable_project` | B2, B3, B4, B11, B8 | `UT-VIEW-DRAFT-AUTO-RUN`, `CT-VIEW-DRAFT-AUTO-RUN-JSON`, `LT-VIEW-DRAFT-AUTO-RUN` |
| `draft() -> _DraftContext` | SDK-only compound alias for `view draft enter`, followed by transforms, then `submit` or `discard`. It has no standalone CLI handler. | No serializable result; policy comes from the three canonical commands. | B3, B11 | `UT-VIEW-DRAFT-CONTEXT-ALIAS` |
| `get_column_mapping() -> dict[str, str]` | Local projection in `view get VIEW_ID`; machine output field `data.column_mapping`. | `ColumnMappingResult`; `not_async; no-draft; none; read; live_disposable_project` | B2, B8 | `UT-VIEW-COLUMN-MAPPING-ALIAS`, `CT-VIEW-GET-JSON` |
| `branch_out(dataset_name: str, *, target_ds_id: int \| None = None, save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE, column_mapping: dict[str, str] \| None = None, label_ids: list[int] \| None = None, condition: Condition \| CompoundCondition \| NotCondition \| None = None, timeout: int \| None = None) -> int` | Alias of `view export dataset VIEW_ID --dataset-name TEXT [--target-dataset DATASET_ID] [--save-as-mode REPLACE_IN_DS\|APPEND_TO_DS] [--label ID]... [--input FILE\|-]`. Default is `REPLACE_IN_DS`; append requires a target. Mapping and condition are document-only. Use global `--job-timeout`, not a duplicate local timeout. | `DatasetMaterializationResult`; `always_wait; no-draft; delete-created-dataset only; dynamic safety; live_disposable_project`. New target is `benign_mutation`; append needs `--yes`; replacement needs `--yes --confirm TARGET_DS_ID`. | B2, B4, B10, B8 | `UT-VIEW-EXPORT-DATASET`, `CT-VIEW-EXPORT-DATASET-WAIT`, `LT-VIEW-EXPORT-DATASET` |

## Typing-only `mammoth._mixins._host.ViewHost`

`ViewHost` has no runtime effect. Its two public protocol declarations still
appear in the complete SDK inventory, so they receive explicit alias records.

| Exact public signature | Disposition | Canonical behavior and test |
|---|---|---|
| `list_tasks() -> list[dict[str, Any]]` | `alias` | Same behavior as `View.list_tasks()` and `view task list VIEW_ID`; test `UT-VIEW-HOST-LIST-TASKS-ALIAS`. |
| `refresh() -> View` | `alias` | Same behavior as `View.refresh()` and `view get VIEW_ID`; test `UT-VIEW-HOST-REFRESH-ALIAS`. |

## `mammoth.api.pipeline.PipelineAPI`

`dataset_id` is an SDK optimization. It is not a CLI option because project
context and `VIEW_ID` identify the command target. The service may pass a known
dataset ID after public typed resolution.

| Exact public signature | Canonical command and exact local input | Result and policy | Blockers | Representative tests |
|---|---|---|---|---|
| `get_pipeline(dataview_id: int, dataset_id: int \| None = None) -> dict[str, Any]` | `view pipeline get VIEW_ID` | `PipelineResult`; `not_async; server-state; none; read; live_disposable_project` | B1, B2, B8 | `UT-VIEW-PIPELINE-GET`, `CT-VIEW-PIPELINE-GET-JSON`, `LT-VIEW-PIPELINE-GET` |
| `list_tasks(dataview_id: int, dataset_id: int \| None = None) -> dict[str, Any]` | `view task list VIEW_ID`; no `--all` until continuation is proven. | `PipelineTaskListResult`; `not_async; server-state; none; read; live_disposable_project`; `single_page` until B5 | B1, B2, B5, B8 | `UT-VIEW-TASK-LIST`, `CT-VIEW-TASK-LIST-JSON`, `LT-VIEW-TASK-LIST` |
| `add_task(dataview_id: int, task_spec: dict[str, Any], dataset_id: int \| None = None) -> dict[str, Any]` | `view task add VIEW_ID --input FILE\|-`; strict `task` discriminated union only. | `PipelineMutationResult`; `always_wait; server-aware; task-delete; reversible_pipeline; live_disposable_project` | B1, B2, B3, B4, B9, B12, B8 | `UT-VIEW-TASK-ADD`, `CT-VIEW-TASK-ADD-WAIT`, `LT-VIEW-TASK-ADD` |
| `get_task(dataview_id: int, task_id: int, dataset_id: int \| None = None) -> dict[str, Any]` | `view task get VIEW_ID TASK_ID` | `PipelineTaskResult`; `not_async; server-state; none; read; live_disposable_project` | B1, B2, B8 | `UT-VIEW-TASK-GET`, `CT-VIEW-TASK-GET-JSON`, `LT-VIEW-TASK-GET` |
| `update_task(dataview_id: int, task_id: int, task_spec: dict[str, Any], dataset_id: int \| None = None) -> dict[str, Any]` | `view task update VIEW_ID TASK_ID --input FILE\|-`; strict replacement `task` union. | `PipelineMutationResult`; `always_wait; server-aware; restore-prior-spec; reversible_pipeline; live_disposable_project` | B1, B2, B3, B4, B9, B12, B8 | `UT-VIEW-TASK-UPDATE`, `CT-VIEW-TASK-UPDATE-WAIT`, `LT-VIEW-TASK-UPDATE` |
| `delete_task(dataview_id: int, task_id: int, dataset_id: int \| None = None) -> dict[str, Any]` | `view task delete VIEW_ID TASK_ID [--yes]`; prompt or `--yes`. | `PipelineMutationResult`; `always_wait; server-aware; none; destructive; live_disposable_project` | B1, B2, B3, B4, B8 | `UT-VIEW-TASK-DELETE`, `CT-VIEW-TASK-DELETE-ERROR`, `LT-VIEW-TASK-DELETE` |
| `preview_task(dataview_id: int, task_spec: dict[str, Any], dataset_id: int \| None = None) -> dict[str, Any]` | `view task preview VIEW_ID --input FILE\|-`; strict `task` union. | `TaskPreviewResult`; `always_wait; no-draft; none; read; live_disposable_project` | B1, B2, B4, B9, B8 | `UT-VIEW-TASK-PREVIEW`, `CT-VIEW-TASK-PREVIEW-JSON`, `LT-VIEW-TASK-PREVIEW` |
| `draft_mode(dataview_id: int, command: str, dataset_id: int \| None = None) -> dict[str, Any]` | Typed SDK seam for `view draft enter\|submit\|discard\|exit VIEW_ID`. Accept only `enter`, `submit`, `discard`, or `exit`; never `commit`. `exit` is an internal step of submit/discard and is not a public CLI verb. | `DraftStateResult` or `PipelineMutationResult`; `always_wait; server-state; command-dependent; command-dependent; live_disposable_project` | B1, B2, B3, B4, B11, B8 | `UT-VIEW-DRAFT-COMMAND`, `CT-VIEW-DRAFT-SUBMIT-WAIT`, `LT-VIEW-DRAFT-CROSS-PROCESS` |
| `edit_pipeline(dataview_id: int, patches: _list[dict[str, Any]], dataset_id: int \| None = None) -> dict[str, Any]` | `view pipeline edit VIEW_ID --input FILE\|-`; strict nonempty `patches`. Each allowed path has a discriminated model and safety class. Empty and unknown patches fail. | `PipelineMutationResult`; `always_wait; server-state; operation-dependent; operation-dependent; live_disposable_project` | B1, B2, B3, B4, B9, B12, B8 | `UT-VIEW-PIPELINE-EDIT`, `CT-VIEW-PIPELINE-EDIT-ERROR`, `LT-VIEW-PIPELINE-EDIT` |
| `wait_for_pipeline(dataview_id: int, dataset_id: int \| None = None, timeout: int \| None = None, poll_interval: int = 3) -> dict[str, Any]` | `view pipeline wait VIEW_ID`; global `--pipeline-timeout` supplies `timeout`. Do not expose `poll_interval` in v1. | `PipelineResult`; `always_wait; server-state; none; read; live_disposable_project` | B1, B2, B8 | `UT-VIEW-PIPELINE-WAIT`, `CT-VIEW-PIPELINE-WAIT-TIMEOUT`, `LT-VIEW-PIPELINE-WAIT` |

## Inherited transformation methods

### Column, filter, and math mixins

| Exact public signature | Canonical command and exact local input | Result and policy exceptions | Blockers | Representative tests |
|---|---|---|---|---|
| `add_column(name: str, column_type: ColumnType = ColumnType.TEXT) -> dict[str, Any]` | `view transform add-column VIEW_ID --name TEXT [--column-type TEXT\|NUMERIC\|DATE]`; default `TEXT`. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-ADD-COLUMN`, `CT-VIEW-ADD-COLUMN-JSON`, `LT-VIEW-ADD-COLUMN` |
| `delete_columns(columns: list[str]) -> dict[str, Any]` | `view transform delete-columns VIEW_ID --column TEXT...`; one or more unique columns. | Standard policy; task deletion restores columns only when the task ID is stable. | B2, B3, B12, B8 | `UT-VIEW-DELETE-COLUMNS`, `CT-VIEW-DELETE-COLUMNS-ERROR`, `LT-VIEW-DELETE-COLUMNS-UNDO` |
| `copy_columns(copies: list[CopySpec]) -> dict[str, Any]` | `view transform copy-columns VIEW_ID --input FILE\|-`; strict `copies`. Per-item conditions remain document-only. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-COPY-COLUMNS`, `CT-VIEW-COPY-COLUMNS-JSON`, `LT-VIEW-COPY-COLUMNS` |
| `combine_columns(sources: list[str], new_column: str \| None = None, column_type: ColumnType = ColumnType.TEXT, existing_column: str \| None = None, separator: str = " ", condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform combine-columns VIEW_ID --source TEXT... (--new-column TEXT\|--existing-column TEXT) [--column-type ...] [--separator TEXT] [--input FILE\|-]`; defaults `TEXT` and one space. Reject the SDK's undocumented `__literal__:` source escape at the CLI boundary. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-COMBINE-COLUMNS`, `CT-VIEW-COMBINE-COLUMNS-ERROR`, `LT-VIEW-COMBINE-COLUMNS` |
| `convert_type(conversions: list[ConversionSpec]) -> dict[str, Any]` | `view transform convert-type VIEW_ID --input FILE\|-`; strict `conversions`. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-CONVERT-TYPE`, `CT-VIEW-CONVERT-TYPE-JSON`, `LT-VIEW-CONVERT-TYPE` |
| `filter_rows(condition: Condition \| CompoundCondition \| NotCondition, filter_type: FilterType = FilterType.SHOW, prompt: str = "") -> dict[str, Any]` | `view transform filter VIEW_ID --input FILE\|- [--filter-type SHOW\|REMOVE] [--prompt TEXT]`; condition required; defaults `SHOW` and empty prompt. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-FILTER`, `CT-VIEW-FILTER-ERROR`, `LT-VIEW-FILTER` |
| `set_values(values: list[SetValue], new_column: str \| None = None, column_type: ColumnType = ColumnType.TEXT, existing_column: str \| None = None, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform set-values VIEW_ID --input FILE\|- [--new-column TEXT\|--existing-column TEXT] [--column-type ...]`; strict `values`, default `TEXT`, exactly one destination. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-SET-VALUES`, `CT-VIEW-SET-VALUES-JSON`, `LT-VIEW-SET-VALUES` |
| `math(expression: str, new_column: str \| None = None, column_type: ColumnType = ColumnType.NUMERIC, existing_column: str \| None = None, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform math VIEW_ID --expression TEXT (--new-column TEXT\|--existing-column TEXT) [--column-type ...] [--input FILE\|-]`; nonempty expression, default `NUMERIC`. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-MATH`, `CT-VIEW-MATH-ERROR`, `LT-VIEW-MATH` |
| `small_large(function: SmallLargeFunction, columns: list[str], index: int = 1, constants: list[float] \| None = None, new_column: str \| None = None, existing_column: str \| None = None) -> dict[str, Any]` | `view transform small-large VIEW_ID --function SMALL\|LARGE [--column TEXT]... [--constant NUMBER]... [--index 1] (--new-column TEXT\|--existing-column TEXT)`; at least one source, positive index, exactly one destination. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-SMALL-LARGE`, `CT-VIEW-SMALL-LARGE-ERROR`, `LT-VIEW-SMALL-LARGE` |

### Text and date mixins

| Exact public signature | Canonical command and exact local input | Result and policy exceptions | Blockers | Representative tests |
|---|---|---|---|---|
| `text_transform(columns: list[str], case: TextCase \| None = None, trim: bool = False, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform text VIEW_ID --column TEXT... [--case UPPER\|LOWER\|TITLE] [--trim\|--no-trim] [--input FILE\|-]`; trim defaults false. Require `case` or `trim=true`. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-TEXT`, `CT-VIEW-TEXT-ERROR`, `LT-VIEW-TEXT` |
| `replace_values(columns: list[str], find: str, replace: str, match_case: bool = False, match_words: bool = False, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform replace VIEW_ID --column TEXT... --find TEXT --replace TEXT [--match-case\|--ignore-case] [--match-words\|--match-substrings] [--input FILE\|-]`; defaults false/false. Presence validates `--replace`; empty replacement is valid. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-REPLACE`, `CT-VIEW-REPLACE-DEFAULTS`, `LT-VIEW-REPLACE-UNDO` |
| `bulk_replace(columns: list[str], mapping: list[BulkReplaceMapping], match_case: bool = True, match_words: bool = False, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform bulk-replace VIEW_ID`. The complete and controlling flags, shortcut/document exclusivity, defaults, result, draft, undo, and live contract is **Complete bulk-replace command contract** in plan 02. This appendix does not narrow or replace it. | Standard policy exactly as plan 02; defaults true/false. | B2, B3, B12, B8 | `UT-VIEW-BULK-REPLACE`, `CT-VIEW-BULK-REPLACE-DEFAULTS`, `CT-VIEW-BULK-REPLACE-INPUT-MODES`, `LT-VIEW-BULK-REPLACE-DRAFT`, `LT-VIEW-BULK-REPLACE-UNDO` |
| `split_column(column: str, delimiter: str, new_columns: list[SplitColumnSpec]) -> dict[str, Any]` | `view transform split VIEW_ID --column TEXT --delimiter TEXT --input FILE\|-`; strict `new_columns`; delimiter is required and can contain whitespace but cannot be empty. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-SPLIT`, `CT-VIEW-SPLIT-ERROR`, `LT-VIEW-SPLIT` |
| `substring(column: str, direction: SubstringDirection \| None = None, num_char: int \| None = None, char_position: int \| None = None, regex_pattern: str \| None = None, regex_invert: bool = False, new_column: str \| None = None, existing_column: str \| None = None, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform substring VIEW_ID --column TEXT (--new-column TEXT\|--existing-column TEXT) [--direction ...] [--num-char N] [--char-position N] [--regex-pattern TEXT] [--regex-invert\|--no-regex-invert] [--input FILE\|-]`. Choose exactly one position or regex mode. `START/END` require positive `num_char`; `LEFT/RIGHT` require nonnegative `char_position`; regex mode forbids all position fields. Default invert false. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-SUBSTRING`, `CT-VIEW-SUBSTRING-ERROR`, `LT-VIEW-SUBSTRING` |
| `extract_date(column: str, component: DateComponent, new_column: str \| None = None, existing_column: str \| None = None) -> dict[str, Any]` | `view transform extract-date VIEW_ID --column TEXT --component VALUE (--new-column TEXT\|--existing-column TEXT)`; exact DateComponent values are above. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-EXTRACT-DATE`, `CT-VIEW-EXTRACT-DATE-JSON`, `LT-VIEW-EXTRACT-DATE` |
| `date_diff(component: DateDiffUnit, start: str, end: str, new_column: str \| None = None, existing_column: str \| None = None) -> dict[str, Any]` | `view transform date-diff VIEW_ID --component UNIT --start TEXT --end TEXT (--new-column TEXT\|--existing-column TEXT)`; start and end columns must differ. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-DATE-DIFF`, `CT-VIEW-DATE-DIFF-ERROR`, `LT-VIEW-DATE-DIFF` |
| `increment_date(column: str, delta: DateDelta, new_column: str \| None = None, existing_column: str \| None = None, condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform increment-date VIEW_ID --column TEXT (--new-column TEXT\|--existing-column TEXT) --input FILE\|-`; strict nonzero `delta`; condition is document-only. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-INCREMENT-DATE`, `CT-VIEW-INCREMENT-DATE-ERROR`, `LT-VIEW-INCREMENT-DATE` |

### Aggregate, row, and advanced mixins

| Exact public signature | Canonical command and exact local input | Result and policy exceptions | Blockers | Representative tests |
|---|---|---|---|---|
| `pivot(group_by: list[str], aggregations: list[AggregationSpec], condition: Condition \| CompoundCondition \| NotCondition \| None = None) -> dict[str, Any]` | `view transform pivot VIEW_ID --input FILE\|-`; strict nonempty `group_by` and `aggregations`. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-PIVOT`, `CT-VIEW-PIVOT-ERROR`, `LT-VIEW-PIVOT` |
| `window(function: WindowFunction, column: str \| None = None, new_column: str \| None = None, column_type: ColumnType = ColumnType.NUMERIC, existing_column: str \| None = None, partition_by: list[str] \| None = None, order_by: list[list[str \| SortDirection]] \| None = None, range_type: WindowRange = WindowRange.UNBOUNDED) -> dict[str, Any]` | `view transform window VIEW_ID --function VALUE (--new-column TEXT\|--existing-column TEXT) [--column TEXT] [--column-type ...] [--partition-by TEXT]... [--range UNBOUNDED\|RUNNING] [--input FILE\|-]`; default type `NUMERIC`, range `UNBOUNDED`; `order_by` is document-only. Enforce function-specific source and ordering rules. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-WINDOW`, `CT-VIEW-WINDOW-ERROR`, `LT-VIEW-WINDOW` |
| `crosstab(rows: list[str], pivot_column: str, select: CrosstabSpec \| list[CrosstabSpec], *, dataset_name: str, save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE, target_ds_id: int \| None = None, condition: Condition \| CompoundCondition \| NotCondition \| None = None, timeout: int \| None = None) -> int` | `view transform crosstab VIEW_ID --dataset-name TEXT --input FILE\|- [--save-as-mode ...] [--target-dataset DATASET_ID]`; strict nonempty `rows` and crosstab `select`; use global `--job-timeout`. Default `REPLACE_IN_DS`; append requires target. | `DatasetMaterializationResult`; `always_wait; no-draft; delete-created-dataset only; dynamic safety; live_disposable_project`. New target needs no confirmation; append needs `--yes`; replace existing needs `--yes --confirm TARGET_DS_ID`. | B2, B4, B10, B8 | `UT-VIEW-CROSSTAB`, `CT-VIEW-CROSSTAB-WAIT`, `LT-VIEW-CROSSTAB` |
| `fill_missing(column: str, direction: FillDirection, partition_by: str \| None = None, order_by: list[list[str \| SortDirection]] \| None = None) -> dict[str, Any]` | `view transform fill-missing VIEW_ID --column TEXT --direction FIRST_VALUE\|LAST_VALUE [--partition-by TEXT] [--input FILE\|-]`; `order_by` is document-only. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-FILL-MISSING`, `CT-VIEW-FILL-MISSING-JSON`, `LT-VIEW-FILL-MISSING` |
| `limit_rows(n: int, bottom: bool = False, order_by: list[list[str \| SortDirection]] \| None = None) -> dict[str, Any]` | `view transform limit-rows VIEW_ID --rows N [--bottom\|--top] [--input FILE\|-]`; positive N, default top; `order_by` is document-only. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-LIMIT-ROWS`, `CT-VIEW-LIMIT-ROWS-ERROR`, `LT-VIEW-LIMIT-ROWS` |
| `discard_duplicates(ignore_columns: list[str] \| None = None) -> dict[str, Any]` | `view transform discard-duplicates VIEW_ID [--ignore-column TEXT]...`; omitted list means compare all columns. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-DISCARD-DUPLICATES`, `CT-VIEW-DISCARD-DUPLICATES-JSON`, `LT-VIEW-DISCARD-DUPLICATES` |
| `unnest(columns: list[str], label_column: str = "Label", value_column: str = "Value") -> dict[str, Any]` | `view transform unnest VIEW_ID --column TEXT... [--label-column TEXT] [--value-column TEXT]`; defaults `Label` and `Value`; output names must differ and not collide with retained columns. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-UNNEST`, `CT-VIEW-UNNEST-ERROR`, `LT-VIEW-UNNEST` |
| `join(foreign_view: int \| View, join_type: JoinType, on: list[JoinKeySpec], select: list[str \| JoinSelectSpec], column_prefix: str \| None = None) -> dict[str, Any]` | `view transform join VIEW_ID --foreign-view VIEW_ID --join-type TYPE --input FILE\|- [--column-prefix TEXT]`; strict `on` and normalized structured `select`. CLI always resolves the foreign view so both sides accept display names. | Standard transformation policy. | B1, B2, B3, B12, B8 | `UT-VIEW-JOIN`, `CT-VIEW-JOIN-ERROR`, `LT-VIEW-JOIN` |
| `lookup(source: str, lookup_view_id: int, key: str, value: str, new_column: str \| None = None, existing_column: str \| None = None) -> dict[str, Any]` | `view transform lookup VIEW_ID --source TEXT --lookup-view VIEW_ID --key TEXT --value TEXT (--new-column TEXT\|--existing-column TEXT)`; resolve lookup key and value through the public view resolver before mutation. | Standard transformation policy. | B1, B2, B3, B12, B8 | `UT-VIEW-LOOKUP`, `CT-VIEW-LOOKUP-ERROR`, `LT-VIEW-LOOKUP` |
| `json_extract(column: str, json_type: JsonType = JsonType.OBJECT, keys: list[str] \| None = None, extractions: list[JsonExtractionSpec] \| None = None, keep_source: bool = False, op_type: JsonOpType \| None = None) -> dict[str, Any]` | `view transform json-extract VIEW_ID --column TEXT [--json-type OBJECT\|LIST] [--key TEXT]... [--keep-source\|--drop-source] [--op-type VALUE] [--input FILE\|-]`; defaults `OBJECT`, drop source, and the type's default op. Choose exactly one of keys or document `extractions`. Enforce op/type compatibility. | Standard transformation policy. | B2, B3, B12, B8 | `UT-VIEW-JSON-EXTRACT`, `CT-VIEW-JSON-EXTRACT-ERROR`, `LT-VIEW-JSON-EXTRACT` |
| `gen_ai(prompt: str, context_columns: list[str], new_column: str = "AI Result", assistant_data: list[str] \| None = None, context_columns_derivation: bool \| None = None) -> dict[str, Any]` | `view transform ai VIEW_ID --prompt TEXT --context-column TEXT... [--new-column TEXT] [--assistant-data TEXT]... [--derive-context\|--no-derive-context]`; default new column `AI Result`; derivation default is unset, not false. | Standard transformation policy; record addon and data-processing notice in help. | B2, B3, B12, B13, B8 | `UT-VIEW-AI`, `CT-VIEW-AI-JSON`, `LT-VIEW-AI` |
| `generate_sql(intent: str) -> str` | `view transform generate-sql VIEW_ID --intent TEXT`; nonempty intent. The operation adds and executes a SQL task; it is not a read-only generator. | `GeneratedSqlMutationResult` containing query plus pipeline/task state; standard wait, draft, undo, safety, and live policies. | B2, B3, B4, B7, B12, B13, B8 | `UT-VIEW-GENERATE-SQL`, `CT-VIEW-GENERATE-SQL-WAIT`, `LT-VIEW-GENERATE-SQL` |
| `add_sql(query: str) -> dict[str, Any]` | `view transform add-sql VIEW_ID (--query TEXT\|--query-file FILE)`; exactly one source, nonempty query. `--query-file -` reads stdin. Do not reinterpret, template, or shell-evaluate SQL. | Standard transformation policy; record SQL-addon requirement. | B2, B3, B12, B13, B8 | `UT-VIEW-ADD-SQL`, `CT-VIEW-ADD-SQL-ERROR`, `LT-VIEW-ADD-SQL` |

## Blocking SDK and acceptance work

| ID | Required resolution |
|---|---|
| `B1` | Add a public typed dataview-to-dataset resolver. Remove public convenience methods' private cross-subclient calls. |
| `B2` | Replace raw dictionaries with strict public request and result models. Preserve normalized view, task, pipeline, draft, pagination, and request-ID data. |
| `B3` | Make draft status server-backed across processes. A new `View` object must observe active draft state. |
| `B4` | Separate typed start and wait results where the API returns jobs. Preserve stable job and task identities through waiting. |
| `B5` | Preserve list/data pagination envelopes and prove continuation before adding `--all`. |
| `B6` | Define and test bulk view deletion across datasets. Reject empty input. Never derive all targets from the first view's dataset. |
| `B7` | Add public typed SDK operations for SQL generation. CLI source must not call `_request_json`, `_next_sequence_number`, or other private members. |
| `B8` | Grant the guarded live principal dataset-create or file-upload access, then rerun isolated view, pipeline, draft, transformation, and undo tests. |
| `B9` | Add the typed discriminated task union and typed permitted pipeline patch union. Reject arbitrary dictionaries and unknown task keys. |
| `B10` | Add typed internal-dataset materialization start/wait results. Prove append and replacement behavior and cleanup semantics. |
| `B11` | Standardize draft vocabulary on `enter`, `submit`, `discard`, and `exit`. Add a public status read. Remove the stale `commit` wording. |
| `B12` | Return the stable created or changed task ID in every pipeline mutation result. Without it, suppress rollback instructions and undo claims. |
| `B13` | Prove SQL and AI addon availability in the disposable live fixture. Use contract tests when the addon is unavailable; do not treat authorization failure as server-disabled evidence. |

## Catalog acceptance gate

Before any handler in this appendix is implemented, generate manifest records
from this catalog and make these central tests fail only for missing production
code:

```text
test_sdk_view_catalog_matches_introspection
test_sdk_view_catalog_has_61_entries
test_sdk_view_catalog_signatures_and_defaults_match
test_sdk_view_catalog_commands_are_registered_or_aliases
test_sdk_view_catalog_has_strict_request_and_result_models
test_sdk_view_catalog_has_wait_draft_undo_safety_live_policy
test_sdk_view_catalog_has_representative_test_ids
test_sdk_view_catalog_blockers_are_known
test_transform_destination_exclusivity
test_transform_nonempty_source_contracts
test_transform_enum_values_match_sdk
test_transform_condition_is_document_only
test_transform_undo_requires_stable_task_id
test_bulk_replace_catalog_defers_to_plan_02
```

The generated public-SDK inventory remains the machine-readable source for
implementation. This appendix is the reviewed command-design input to that
inventory; it is not a substitute for the 376-operation OpenAPI disposition
review.
