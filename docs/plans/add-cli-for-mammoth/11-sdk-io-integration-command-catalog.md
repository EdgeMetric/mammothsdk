# SDK I/O and integration command catalog

## Normative status and scope

This appendix is the command freeze for the current public file, job, browse,
batch, connector, webhook, and export surfaces. It is normative with the
product, architecture, parity, test, and live-operation plans. A generated
manifest must reproduce this catalog before a handler is implemented.

The inspected SDK surface contains 70 public methods: 9 file, 4 job, 6 browse,
5 batch, 13 connector, 7 webhook, 5 `ExportsAPI`, and 21 `ViewExport` methods.
The export destination catalog also covers all 19 `HandlerType` values. It does
not treat private methods, stale MCP wrappers, or pure builders as commands.

Signatures below are exact as inspected. They omit only the leading `self`.
`_list` is the source module's alias for `list`. `ExportResult` means
`PipelineExportsModificationResp | JobResponse`. A CLI must not preserve an
untyped `dict[str, Any]`, `_list[dict[str, Any]]`, or `**kwargs: Any` boundary.
Those annotations identify typed-SDK work that must precede the command.

## Locked policy vocabulary

Use only these short codes in the tables:

| Code | Meaning |
|---|---|
| `NW` | `not_async` |
| `AW` | `always_wait` |
| `SW` | `start_or_wait` |
| `RJ` | `returns_job` |
| `N` | pagination `none` |
| `O` | pagination `offset` with a typed page envelope |
| `SP` | `single_page`; completeness is not promised |
| `R` | mutation class `read` |
| `B` | mutation class `benign_mutation` |
| `D` | mutation class `destructive` |
| `H` | mutation class `high_impact` |
| `E` | mutation class `external_effect` |
| `RO` | acceptance `live_read_only` |
| `DP` | acceptance `live_disposable_project` |
| `EF` | acceptance `live_dedicated_external_fixture` |
| `CO` | acceptance `contract_only_high_impact` |

`R` and `B` require no confirmation. `D` requires a prompt or `--yes`. `H`
requires `--yes --confirm TARGET`. `E` requires `--yes` when
`run_immediately=true`; validation-only and saved-but-not-run forms need no
confirmation. Never retry `B`, `D`, `H`, or `E` without a documented server
idempotency key. `webhook send-get` is a mutation despite HTTP `GET`, and it is
never retried.

Every canonical command supports `--output json --no-input`. Common scalar
flags override a typed `--input FILE|-` document. Unknown document fields are
rejected. Conditions are document-only and use `ConditionRequest`. Positive ID
types reject zero and negative values. Lists identified as nonempty reject an
empty value and duplicates where order has no meaning.

For each test stem `X`, generate at least `UT-X`, `CT-X-HUMAN`, `CT-X-JSON`,
and `CT-X-ERROR`. Add `CT-X-WAIT` and `CT-X-TIMEOUT` for `AW` and `SW`. Add
`CT-X-NOWAIT` for `SW`. Add `LT-X` only for `RO`, `DP`, or `EF`; a blocked live
test retains its ID with status `blocked_external`.

## Shared typed contracts

These names are required public contracts. Existing Pydantic models can satisfy
them only when their validation and redaction metadata match this table.

| Contract | Required content |
|---|---|
| `FileListRequest` / `FilePageResult` | All `FilesAPI.list` filters; `files`, `limit`, `offset`, and nullable `next` |
| `FileUploadRequest` / `FileUploadResult` | Nonempty local paths, target folder, append controls, wait controls; submitted job ID and final dataset IDs |
| `FilePatchRequest` / `FileMutationResult` | Discriminated `password` or `extract_sheets` patch; stable job and final state |
| `JobGetRequest`, `JobManyRequest`, `JobResult`, `JobPageResult` | Positive IDs, normalized case-insensitive state, stable response, failure, and resumable identity |
| `BrowseRequest` / `BrowseResult` | Typed resource union, hierarchy level, returned resources, and any proven continuation data |
| `BatchCreateRequest`, `BatchPatchRequest`, `BatchResult`, `BatchPageResult` | Positive source ID, nonempty mapping, discriminated replace/remove patch, typed response |
| `ConnectorConnectionRequest` | Discriminated union keyed by `connector_key`; each variant marks its secret fields |
| `DsConfigCreateRequest`, `DsConfigPatchRequest`, `DsConfigResult` | Exactly one of query/file source; validate/sample exclusion; typed replace paths |
| `WebhookCreateRequest`, `WebhookPatchRequest`, `WebhookSendRequest`, `WebhookResult`, `WebhookPageResult` | Valid mode, nonempty patch, strict payload/query maps, pagination metadata, secret metadata |
| `ExportCommonOptions` | `sequence`, `trigger_id`, `end_of_pipeline`, `trigger_type`, `condition`, `run_immediately`, and `validate_only`; no `**kwargs` |
| `ExportCreateRequest` | Discriminated destination union plus `ExportCommonOptions` |
| `ExportMutationResult` | Saved trigger or submitted job as a tagged union; never infer completion |
| `ExportPageResult` | `exports`, `limit`, `offset`, and nullable `next` |
| `ExportDownloadResult` | Final path, byte count, and source trigger/job identity |

Secret input is accepted only through a destination-specific environment
variable, keyring, hidden TTY prompt, `--secret-stdin FIELD`, or a
permission-checked file option. A normal positional, normal option, input
document, process listing, debug output, result, error, or snapshot must not
contain a secret. Secret-producing webhook creation requires `--secret-out`
to a new mode-`0600` file, or `--show-secret` on a TTY. It otherwise redacts
the value and reports that a secret was created.

## Files

Canonical `file delete FILE_ID...` accepts one or more IDs. Therefore the
single-delete and bulk-delete SDK methods are conversions of one command, not
two handlers. `file upload-folder` is nonrecursive.

| Public SDK method and exact signature | Canonical command or alias | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `FilesAPI.list(fields: str | None = None, file_ids: _list[int] | None = None, names: _list[str] | None = None, statuses: _list[str] | None = None, created_at: str | None = None, updated_at: str | None = None, limit: int = 50, offset: int = 0, sort: str | None = None) -> FilesList` | `file list` | `FileListRequest -> FilePageResult` | NW/O/R/RO | Make `next` nullable and implement proven `--all`; `FILE-LIST` |
| `FilesAPI.get(file_id: int, fields: str | None = None) -> FileSchema` | `file get FILE_ID` | `FileGetRequest -> FileResult` | NW/N/R/RO | Add strict result model if `FileSchema` remains permissive; `FILE-GET` |
| `FilesAPI.upload(files: _list[str | Path | BinaryIO] | str | Path | BinaryIO | None = None, folder_resource_id: str | int | None = None, append_to_ds_id: int | None = None, override_target_schema: bool | None = None, wait_for_completion: bool = True, timeout: int = 300) -> _list[int] | int | None` | `file upload PATH...` | `FileUploadRequest -> FileUploadResult` | SW/N/B/DP | Separate start/wait and remove scalar/list/None result ambiguity; live upload permission is blocked; `FILE-UPLOAD` |
| `FilesAPI.upload_folder(folder_path: str | Path, folder_resource_id: str | None = None, wait_for_completion: bool = True, timeout: int = 300) -> _list[int] | int | None` | `file upload-folder DIRECTORY` | `FileFolderUploadRequest -> FileUploadResult` | SW/N/B/DP | Alias through repaired upload contract; reject recursion and an empty folder; live upload permission is blocked; `FILE-UPLOAD-FOLDER` |
| `FilesAPI.delete(file_id: int) -> None` | `file delete FILE_ID...` | `FileDeleteRequest -> DeleteResult` | NW/N/D/DP | Resolve every ID before confirmation; `FILE-DELETE` |
| `FilesAPI.bulk_delete(file_ids: _list[int]) -> None` | SDK alias of `file delete FILE_ID...` | `FileDeleteRequest -> DeleteResult` | NW/N/D/DP | Reject an empty ID set and confirm the sorted immutable set; alias test `ALIAS-FILE-BULK-DELETE` |
| `FilesAPI.update(file_id: int, patch_request: FilePatchRequest) -> ObjectJobSchema` | `file update FILE_ID` | `FilePatchRequest -> FileMutationResult` | AW/N/B/DP | Existing method waits but returns the pre-wait response; return stable final state; `FILE-UPDATE` |
| `FilesAPI.set_password(file_id: int, password: str) -> ObjectJobSchema` | `file set-password FILE_ID` | `FilePasswordRequest -> FileMutationResult` | AW/N/H/CO | `password` is secret and never a normal flag; do not live-test password changes; `FILE-SET-PASSWORD` |
| `FilesAPI.extract_sheets(file_id: int, sheets: _list[str], delete_file_after_extract: bool = True, combine_after_extract: bool = False) -> ObjectJobSchema` | `file extract-sheets FILE_ID` | `FileExtractSheetsRequest -> FileMutationResult` | AW/N/B/DP | Require unique nonempty sheet names and expose both boolean spellings; live upload permission is blocked; `FILE-EXTRACT-SHEETS` |

## Jobs

The CLI names are `job get`, `job get-many`, `job wait`, and `job wait-many`.
`timeout` on current `get_job` is unused and stays visible here only because it
is part of the public compatibility signature. Remove it in a reviewed SDK
breaking release or make it control the HTTP request.

| Public SDK method and exact signature | Canonical command | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `JobsAPI.get_job(job_id: int, timeout: int = 300) -> dict[str, Any]` | `job get JOB_ID` | `JobGetRequest -> JobResult` | NW/N/R/RO | Replace dict result; specify the unused timeout; `JOB-GET` |
| `JobsAPI.get_jobs(job_ids: list[int] | str) -> dict[str, Any]` | `job get-many JOB_ID...` | `JobManyRequest -> JobPageResult` | NW/N/R/RO | CLI accepts repeatable positive integers, not comma strings; detect missing jobs; `JOB-GET-MANY` |
| `JobsAPI.wait_for_job(job_id: int, timeout: int | None = None, poll_interval: int = 2) -> dict[str, Any]` | `job wait JOB_ID` | `JobWaitRequest -> JobResult` | AW/N/R/RO | Normalize status case, unrecognized states, interruption, and resumable timeout; `JOB-WAIT` |
| `JobsAPI.wait_for_jobs(job_ids: list[int] | str, timeout: int | None = None, poll_interval: int = 2) -> dict[str, Any]` | `job wait-many JOB_ID...` | `JobWaitManyRequest -> JobPageResult` | AW/N/R/RO | Reject empty IDs; do not succeed when the server omits a requested job; `JOB-WAIT-MANY` |

Live job tests need known jobs created inside the disposable project. Their
read-only calls are safe, but `LT-JOB-*` remains `blocked_external` until file
upload or another permitted operation can create success and failure fixtures.

## Browse

The first four methods are compatibility aliases for resource-list commands.
Only `workspace_resources` and `folder_resources` call browse endpoints.

| Public SDK method and exact signature | Canonical command or alias | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `BrowseAPI.workspaces() -> dict[str, Any]` | alias `browse workspaces` -> `workspace list` | `WorkspaceListRequest -> WorkspacePageResult` | NW/SP/R/RO | Do not claim complete pagination; `ALIAS-BROWSE-WORKSPACES` |
| `BrowseAPI.projects(workspace_id: int | None = None) -> dict[str, Any]` | alias `browse projects` -> `project list` | `ProjectListRequest -> ProjectPageResult` | NW/SP/R/RO | Project listing must continue beyond 100 only after a proven contract; `ALIAS-BROWSE-PROJECTS` |
| `BrowseAPI.datasets(project_id: int | None = None, workspace_id: int | None = None) -> dict[str, Any]` | alias `browse datasets` -> `dataset list` | `DatasetListRequest -> DatasetPageResult` | NW/SP/R/RO | Replace dict result; `ALIAS-BROWSE-DATASETS` |
| `BrowseAPI.dataviews(dataset_id: int, project_id: int | None = None, workspace_id: int | None = None) -> dict[str, Any]` | alias `browse views` -> `view list` | `ViewListRequest -> ViewPageResult` | NW/SP/R/RO | Replace dict result; `ALIAS-BROWSE-VIEWS` |
| `BrowseAPI.workspace_resources(workspace_id: int | None = None, level: int = 2, fields: str = '__min', limit: int = 100) -> dict[str, Any]` | `browse workspace` | `WorkspaceBrowseRequest -> BrowseResult` | NW/SP/R/RO | Validate `level` against the OpenAPI enum and report truncation; `BROWSE-WORKSPACE` |
| `BrowseAPI.folder_resources(folder_id: int, project_id: int | None = None, workspace_id: int | None = None, level: int = 2, fields: str = '__min') -> dict[str, Any]` | `browse folder FOLDER_ID` | `FolderBrowseRequest -> BrowseResult` | NW/SP/R/RO | Validate level and add continuation only if proven; `BROWSE-FOLDER` |

## Batches

`mapping`, `new_ds_params`, `change_map`, and `patch` are document fields.
`batch update` uses a discriminated union of replace and remove operations.

| Public SDK method and exact signature | Canonical command | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `BatchesAPI.list(dataset_id: int, project_id: int | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]` | `batch list DATASET_ID` | `BatchListRequest -> BatchPageResult` | NW/O/R/RO | Preserve page metadata; live dataset permission is blocked; `BATCH-LIST` |
| `BatchesAPI.get(dataset_id: int, batch_id: int, project_id: int | None = None) -> dict[str, Any]` | `batch get DATASET_ID BATCH_ID` | `BatchGetRequest -> BatchResult` | NW/N/R/RO | Add typed response; live dataset permission is blocked; `BATCH-GET` |
| `BatchesAPI.create(dataset_id: int, source_id: int, mapping: dict[str, str], project_id: int | None = None, new_ds_params: dict[str, Any] | None = None, is_validation_required: bool | None = None, change_map: dict[str, Any] | None = None, delete_source_ds: bool = False) -> dict[str, Any]` | `batch create DATASET_ID` | `BatchCreateRequest -> BatchMutationResult` | RJ/N/B/DP | Type nested maps and stable job/result union; `delete_source_ds=true` changes class to D and requires confirmation; live dataset permission is blocked; `BATCH-CREATE` |
| `BatchesAPI.update(dataset_id: int, patch: _list[dict[str, Any]], project_id: int | None = None) -> dict[str, Any]` | `batch update DATASET_ID` | `BatchPatchRequest -> BatchMutationResult` | RJ/N/B/DP | Replace raw patch dicts; any remove operation changes class to D; live dataset permission is blocked; `BATCH-UPDATE` |
| `BatchesAPI.delete(dataset_id: int, batch_id: int, project_id: int | None = None) -> dict[str, Any]` | `batch delete DATASET_ID BATCH_ID` | `BatchDeleteRequest -> DeleteResult` | RJ/N/D/DP | Resolve the batch before confirmation; live dataset permission is blocked; `BATCH-DELETE` |

## Connectors

Connection documents are discriminated by `connector_key`. At minimum, freeze
typed variants for every connector key in the pinned OpenAPI. Do not expose a
catch-all credential dictionary in the CLI. Secret metadata includes common
fields named `password`, `private_key`, `passphrase`, `code`, `connection_data`,
`personal_access_token`, `client_secret`, `token`, `refresh_token`, and nested
equivalents. Connector reads must redact returned configuration recursively.

| Public SDK method and exact signature | Canonical command | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `ConnectorsAPI.list() -> _list[dict[str, Any]]` | `connector list` | `ConnectorListRequest -> ConnectorPageResult` | NW/SP/R/RO | Preserve any server page metadata; `CONNECTOR-LIST` |
| `ConnectorsAPI.get(connector_key: str) -> dict[str, Any]` | `connector get CONNECTOR_KEY` | `ConnectorGetRequest -> ConnectorResult` | NW/N/R/RO | Validate key against discovery without rejecting future server keys; `CONNECTOR-GET` |
| `ConnectorsAPI.list_connections(connector_key: str, project_id: int | None = None) -> _list[dict[str, Any]]` | `connector connection list CONNECTOR_KEY` | `ConnectionListRequest -> ConnectionPageResult` | NW/SP/R/EF | Dedicated connector fixture required; `CONNECTOR-CONNECTION-LIST` |
| `ConnectorsAPI.create_connection(connector_key: str, config: dict[str, Any], project_id: int | None = None) -> dict[str, Any]` | `connector connection create CONNECTOR_KEY` | `ConnectorConnectionRequest -> ConnectionResult` | NW/N/E/EF | Add discriminated typed models and secret metadata; fixture required; `CONNECTOR-CONNECTION-CREATE` |
| `ConnectorsAPI.get_connection(connector_key: str, connection_key: str, project_id: int | None = None) -> dict[str, Any]` | `connector connection get CONNECTOR_KEY CONNECTION_KEY` | `ConnectionGetRequest -> ConnectionResult` | NW/N/R/EF | Redact returned config; fixture required; `CONNECTOR-CONNECTION-GET` |
| `ConnectorsAPI.update_connection(connector_key: str, connection_key: str, credentials: dict[str, Any], project_id: int | None = None) -> dict[str, Any]` | `connector connection update CONNECTOR_KEY CONNECTION_KEY` | `ConnectorConnectionRequest -> ConnectionResult` | NW/N/E/EF | Add typed variants; require `--yes` if validation contacts the destination; fixture required; `CONNECTOR-CONNECTION-UPDATE` |
| `ConnectorsAPI.delete_connection(connector_key: str, connection_key: str, project_id: int | None = None) -> dict[str, Any]` | `connector connection delete CONNECTOR_KEY CONNECTION_KEY` | `ConnectionDeleteRequest -> DeleteResult` | NW/N/D/EF | Resolve immutable key before confirmation; fixture required; `CONNECTOR-CONNECTION-DELETE` |
| `ConnectorsAPI.list_ds_configs(connector_key: str, connection_key: str, project_id: int | None = None) -> _list[dict[str, Any]]` | `connector ds-config list CONNECTOR_KEY CONNECTION_KEY` | `DsConfigListRequest -> DsConfigPageResult` | NW/SP/R/EF | Preserve pagination and redact nested configuration; fixture required; `CONNECTOR-DS-CONFIG-LIST` |
| `ConnectorsAPI.create_ds_config(connector_key: str, connection_key: str, *, query: str | None = None, file_source: str | None = None, table: str | None = None, profile: str | None = None, validate: bool = True, data_sample: bool = False, project_id: int | None = None) -> dict[str, Any]` | `connector ds-config create CONNECTOR_KEY CONNECTION_KEY` | `DsConfigCreateRequest -> DsConfigResult` | NW/N/E/EF | Require exactly one source and reject `validate && data_sample`; fixture required; `CONNECTOR-DS-CONFIG-CREATE` |
| `ConnectorsAPI.get_ds_config(connector_key: str, connection_key: str, ds_config_key: str, project_id: int | None = None) -> dict[str, Any]` | `connector ds-config get CONNECTOR_KEY CONNECTION_KEY DS_CONFIG_KEY` | `DsConfigGetRequest -> DsConfigResult` | NW/N/R/EF | Add typed redacted response; fixture required; `CONNECTOR-DS-CONFIG-GET` |
| `ConnectorsAPI.update_ds_config(connector_key: str, connection_key: str, ds_config_key: str, patch: _list[DsConfigPatchOp], project_id: int | None = None) -> dict[str, Any]` | `connector ds-config update CONNECTOR_KEY CONNECTION_KEY DS_CONFIG_KEY` | `DsConfigPatchRequest -> DsConfigResult` | NW/N/E/EF | Only `query` has current server support; other enum paths remain blocked pending successful server evidence; `CONNECTOR-DS-CONFIG-UPDATE` |
| `ConnectorsAPI.delete_ds_config(connector_key: str, connection_key: str, ds_config_key: str, project_id: int | None = None) -> dict[str, Any]` | `connector ds-config delete CONNECTOR_KEY CONNECTION_KEY DS_CONFIG_KEY` | `DsConfigDeleteRequest -> DeleteResult` | NW/N/D/EF | Resolve immutable key before confirmation; fixture required; `CONNECTOR-DS-CONFIG-DELETE` |
| `ConnectorsAPI.active_connectors() -> _list[dict[str, Any]]` | `connector active` | `ActiveConnectorListRequest -> ConnectorPageResult` | NW/SP/R/RO | Preserve any page metadata; `CONNECTOR-ACTIVE` |

## Webhooks

`webhook send` accepts data only in `WebhookSendRequest`. `webhook send-get`
accepts a strict scalar query map and is retained because the production API
defines it as ingestion. Neither command accepts a full URL; `WEBHOOK_URI` is a
single server-issued path token.

| Public SDK method and exact signature | Canonical command | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `WebhooksAPI.list(limit: int = 50, offset: int = 0) -> _list[dict[str, Any]]` | `webhook list` | `WebhookListRequest -> WebhookPageResult` | NW/O/R/RO | Current SDK discards pagination metadata; `WEBHOOK-LIST` |
| `WebhooksAPI.create(name: str = 'Generic Webhook', mode: str | WebhookMode = 'replace', folder_resource_id: str | None = None, origins: str = '*', is_secure: bool = False) -> dict[str, Any]` | `webhook create` | `WebhookCreateRequest -> WebhookResult` | NW/N/B/DP | Validate enum and origin syntax; secure creation uses the secret-output rule; `WEBHOOK-CREATE` |
| `WebhooksAPI.get(webhook_id: int) -> dict[str, Any]` | `webhook get WEBHOOK_ID` | `WebhookGetRequest -> WebhookResult` | NW/N/R/RO | Redact `secret`; `WEBHOOK-GET` |
| `WebhooksAPI.update(webhook_id: int, mode: str | WebhookMode | None = None, origins: str | None = None, is_secure: bool | None = None) -> dict[str, Any]` | `webhook update WEBHOOK_ID` | `WebhookPatchRequest -> WebhookResult` | NW/N/B/DP | Reject an empty patch; a newly issued secret uses the secret-output rule; `WEBHOOK-UPDATE` |
| `WebhooksAPI.delete(webhook_id: int) -> dict[str, Any]` | `webhook delete WEBHOOK_ID` | `WebhookDeleteRequest -> DeleteResult` | NW/N/D/DP | Resolve webhook before confirmation; `WEBHOOK-DELETE` |
| `WebhooksAPI.send_data(webhook_uri: str, data: dict[str, Any]) -> dict[str, Any]` | `webhook send WEBHOOK_URI` | `WebhookSendRequest -> WebhookSendResult` | NW/N/B/DP | Never retry; requires a disposable webhook and dataset fixture; current dataset permission blocks live evidence; `WEBHOOK-SEND` |
| `WebhooksAPI.send_data_get(webhook_uri: str, params: dict[str, Any] | None = None) -> dict[str, Any]` | `webhook send-get WEBHOOK_URI` | `WebhookSendGetRequest -> WebhookSendResult` | NW/N/B/DP | Reject an empty query, never retry, and never log the URI if the server treats it as a capability; current dataset permission blocks live evidence; `WEBHOOK-SEND-GET` |

## Export control methods

The canonical resource is `view export`. Add public typed `ExportsAPI.get`,
`ExportsAPI.update`, and `ExportsAPI.delete` methods before their handlers.
`ViewExport.delete` can remain a convenience alias. Add a public typed
dataview-to-dataset resolver before any method scans datasets privately.

| Public SDK method and exact signature | Canonical command or alias | Typed request -> result | W/P/S/L | Blocker and test stem |
|---|---|---|---|---|
| `ExportsAPI.list(dataview_id: int, fields: str | None = None, limit: int = 50, offset: int = 0, sort: str | None = None, sequence: int | None = None, status: ExportStatus | None = None, reordered: bool | None = None, handler_type: HandlerType | None = None, end_of_pipeline: bool | None = None, runnable: bool | None = None) -> PipelineExportsPaginated` | `view export list VIEW_ID` | `ExportListRequest -> ExportPageResult` | NW/O/R/RO | Fix the wire key audit for current `reorderd`; use public resolver; `VIEW-EXPORT-LIST` |
| `ExportsAPI.create(dataview_id: int, export_spec: AddExportSpec, dataset_id: int | None = None, project_id: int | None = None) -> PipelineExportsModificationResp | JobResponse` | `view export create VIEW_ID` | `ExportCreateRequest -> ExportMutationResult` | RJ/N/E/EF | Replace open destination dictionaries with the union below; `VIEW-EXPORT-CREATE` |
| `ExportsAPI.to_s3(dataview_id: int, file: str | None = None, file_type: str = 'csv', include_hidden: bool = False, is_format_set: bool = True, use_format: bool = True, sequence: int | None = None, trigger_id: int | None = None, end_of_pipeline: bool = True, trigger_type: TriggerType = TriggerType.PIPELINE, condition: dict[str, Any] | None = None, run_immediately: bool = True, validate_only: bool = False, additional_properties: dict[str, Any] | None = None, dataset_id: int | None = None) -> PipelineExportsModificationResp | JobResponse | dict[str, Any]` | SDK alias of `view export managed-s3 VIEW_ID` | `ManagedS3ExportRequest -> ExportMutationResult` | AW/N/E/EF | Separate start/wait; replace dict result and untyped options; `ALIAS-EXPORTS-TO-S3` |
| `ExportsAPI.to_dataset(dataview_id: int, dataset_name: str, column_mapping: dict[str, Any] | None = None, sequence: int | None = None, trigger_id: int | None = None, end_of_pipeline: bool = True, trigger_type: TriggerType = TriggerType.PIPELINE, condition: dict[str, Any] | None = None, run_immediately: bool = True, validate_only: bool = False, additional_properties: dict[str, Any] | None = None) -> PipelineExportsModificationResp | JobResponse` | SDK alias of `view export dataset VIEW_ID` | `DatasetExportRequest -> ExportMutationResult` | RJ/N/B/DP | Reconcile with `ViewExport.to_dataset` semantics; `ALIAS-EXPORTS-TO-DATASET` |
| `ExportsAPI.to_csv(dataview_id: int, output_path: str | Path | None = None, timeout: int = 300, dataset_id: int | None = None) -> Path` | SDK target for `view export csv VIEW_ID` | `CsvDownloadRequest -> ExportDownloadResult` | AW/N/B/DP | Use partial file, fsync, atomic rename, and explicit `--overwrite`; live dataset permission is blocked; `VIEW-EXPORT-CSV` |
| `ViewExport.list() -> _list[dict[str, Any]]` | SDK alias of `view export list VIEW_ID` | `ExportListRequest -> ExportPageResult` | NW/O/R/RO | Stop discarding page metadata; alias test `ALIAS-VIEW-EXPORT-LIST` |
| `ViewExport.delete(export_id: int) -> dict[str, Any]` | SDK alias of `view export delete VIEW_ID EXPORT_ID` | `ExportDeleteRequest -> DeleteResult` | NW/N/D/DP | Add canonical `ExportsAPI.delete`; live dataset permission is blocked; `VIEW-EXPORT-DELETE` |

Reserved control commands complete OpenAPI CRUD:

| Command | Required SDK signature | Policy | Representative test |
|---|---|---|---|
| `view export get VIEW_ID EXPORT_ID` | `ExportsAPI.get(dataview_id: int, export_id: int, dataset_id: int | None = None, project_id: int | None = None) -> ItemExportInfo` | NW/N/R/RO | `UT-VIEW-EXPORT-GET` |
| `view export update VIEW_ID EXPORT_ID` | `ExportsAPI.update(dataview_id: int, export_id: int, request: ExportUpdateRequest, dataset_id: int | None = None, project_id: int | None = None) -> ExportMutationResult` | RJ/N/E/EF; confirmation follows the new effective destination and run policy | `UT-VIEW-EXPORT-UPDATE` |
| `view export delete VIEW_ID EXPORT_ID` | `ExportsAPI.delete(dataview_id: int, export_id: int, dataset_id: int | None = None, project_id: int | None = None) -> DeleteResult` | NW/N/D/DP | `UT-VIEW-EXPORT-DELETE` |

## Export destination commands

Every destination command takes positional `VIEW_ID` and a strict destination
document. External destination secrets use the shared secure transports.
`ExportCommonOptions` is available to all pipeline destinations. Its defaults
match the current helpers: `trigger_type=pipeline`, `run_immediately=true`,
`validate_only=false`, and `end_of_pipeline=true`. A command must reject both
`run_immediately=true` and `validate_only=true` if the server contract does not
define that combination.

| Handler value and canonical command | Typed destination request: required; optional/default; secrets | Result and W/S/L | Blocker and test stem |
|---|---|---|---|
| `postgres`: `view export postgres VIEW_ID` | `PostgresExportRequest`: `host,database,table,username`; `port=5432`; secret `password` | `ExportMutationResult`; RJ/E/EF | Current helper requires port and accepts `**kwargs`; add typed options; `VIEW-EXPORT-POSTGRES` |
| `mysql`: `view export mysql VIEW_ID` | `MysqlExportRequest`: `host,database,table,username`; `port=3306`; secret `password` | `ExportMutationResult`; RJ/E/EF | Current helper requires port and accepts `**kwargs`; add typed options; `VIEW-EXPORT-MYSQL` |
| `mssql`: `view export mssql VIEW_ID` | `MssqlExportRequest`: `host,database,table,username`; `port=1433`; secret `password` | `ExportMutationResult`; RJ/E/EF | Current helper requires port and accepts `**kwargs`; add typed options; `VIEW-EXPORT-MSSQL` |
| `redshift`: `view export redshift VIEW_ID` | `RedshiftExportRequest`: `host,database,table,username`; `port=5439`; secret `password` | `ExportMutationResult`; RJ/E/EF | Current helper requires port and accepts `**kwargs`; add typed options; `VIEW-EXPORT-REDSHIFT` |
| `s3`: `view export managed-s3 VIEW_ID`; alias `view export s3` | `ManagedS3ExportRequest`: optional `file_name`, `file_type=csv`, `include_hidden=false`, `is_format_set=true`, `use_format=true`; no user secret | `ExportMutationResult`; SW/B/DP for download-only, otherwise E/EF | Prove supported file types and distinguish start from wait; `VIEW-EXPORT-MANAGED-S3` |
| `csv_file`: reserved `view export csv-file VIEW_ID` | `CsvFileExportRequest`: server-confirmed fields required; none are approved yet | `ExportMutationResult`; RJ/E/EF | No public helper or builder contract exists. Do not alias it to the S3-backed local `csv` command. Block until the production server accepts a reviewed typed fixture; `VIEW-EXPORT-CSV-FILE` |
| `internal_dataset`: `view export dataset VIEW_ID` | `DatasetExportRequest`: `dataset_name`; optional `target_ds_id`, `save_as_mode=replace`, `column_mapping`, `label_ids`, `condition`, `timeout` | `DatasetExportResult`; AW/B/DP, or D when replacing an existing target | Reconcile divergent `ExportsAPI.to_dataset` and `ViewExport.to_dataset` wire shapes; live dataset permission is blocked; `VIEW-EXPORT-DATASET` |
| `ftp`: `view export ftp VIEW_ID` | `FtpExportRequest`: `domain,directory,file,username`; `port=21`; secret `password` | `ExportMutationResult`; RJ/E/EF | Add typed options; `VIEW-EXPORT-FTP` |
| `sftp`: `view export sftp VIEW_ID` | `SftpExportRequest`: `host,username`; optional `directory=''`, `file_name=''`, `port=22`, `randomize_file_name=false`, `ssh_key_authentication=false`; password mode secret `password`; key mode secrets `private_key,passphrase` | `ExportMutationResult`; RJ/E/EF | Enforce authentication-mode union and forbid irrelevant secrets; `VIEW-EXPORT-SFTP` |
| `email`: `view export email VIEW_ID` | `EmailExportRequest`: nonempty `emails`; optional `subject,message,resource`; no authentication secret | `ExportMutationResult`; RJ/E/CO | Outbound email stays contract-only until a dedicated sink and recipient allowlist exist; `VIEW-EXPORT-EMAIL` |
| `elasticsearch`: `view export elasticsearch VIEW_ID` | `ElasticsearchExportRequest`: `host,username,index`; `port=9243`, `connection=https`, `chunksize=200`; secret `password` | `ExportMutationResult`; RJ/E/EF | Validate protocol and positive chunk size; add typed options; `VIEW-EXPORT-ELASTICSEARCH` |
| `bigquery`: `view export bigquery VIEW_ID` | `BigQueryExportRequest`: typed `selected_profile,selected_identity,table`; `export_type=REPLACE`; optional typed `upsert_keys,partition`; nested identity secrets are secret | `ExportMutationResult`; RJ/E/EF | Require upsert keys for UPSERT and type both partition variants; `VIEW-EXPORT-BIGQUERY` |
| `azure_blob`: `view export azure-blob VIEW_ID` | `AzureBlobExportRequest`: `storage_account_name,tenant_id,client_id,container_name`; optional `folder_path,file_name`; secret `client_secret` | `ExportMutationResult`; RJ/E/EF | Add typed options; `VIEW-EXPORT-AZURE-BLOB` |
| `sharepoint`: `view export sharepoint VIEW_ID` | `SharePointExportRequest`: `tenant_id,client_id,site_url`; `document_library=Documents`; optional `folder_path,file_name`; secret `client_secret` | `ExportMutationResult`; RJ/E/EF | Add typed options and validate site URL; `VIEW-EXPORT-SHAREPOINT` |
| `onedrive`: `view export onedrive VIEW_ID` | `OneDriveExportRequest`: `tenant_id,client_id,user_id`; optional `folder_path,file_name`; secret `client_secret` | `ExportMutationResult`; RJ/E/EF | Add typed options; `VIEW-EXPORT-ONEDRIVE` |
| `tableau_server`: `view export tableau VIEW_ID`; alias `view export tableau-server` | `TableauExportRequest`: `server_url,token_name`; `site_name=''`, `project_name=Default`, `datasource_name=mammoth_export`; optional permission-checked `ca_bundle_path`; secret `token_secret` | `ExportMutationResult`; RJ/E/EF | Add typed options and prohibit secret in CA file; `VIEW-EXPORT-TABLEAU` |
| `powerbi`: `view export powerbi VIEW_ID` | `PowerBiExportRequest`: `username,client_id,dataset,table`; secret `password` | `ExportMutationResult`; RJ/E/EF | The handler enum and helper exist, but the pure contract omits it. Confirm camel-case `clientId` against the pinned server before enabling; `VIEW-EXPORT-POWERBI` |
| `generic_rest_api_export`: `view export rest VIEW_ID`; alias `view export rest-api` | `RestExportRequest`: `base_url,endpoint_path`; `auth_type=none`, `http_method=POST`, `wrap_path=records`, `batch_size=1000`, `timeout_seconds=30`, `ssl_verify=true`; optional typed headers, query, body; auth union secrets `key_value,token,password,client_secret,refresh_token` | `ExportMutationResult`; RJ/E/EF | Type all auth variants, reject secrets in static headers/query/body, and allow insecure TLS only with `--yes`; `VIEW-EXPORT-REST` |
| `publishdb`: `view export publish-db VIEW_ID` | `PublishDbRequest`: `table`; `odbc_type=postgres` (`postgres|bigquery`) | `JobStartResult`; RJ/B/DP | Current helper uses a dedicated endpoint, not `HandlerType.PUBLISHDB`; add typed result and public wait path; `VIEW-EXPORT-PUBLISH-DB` |

`view export csv VIEW_ID --output-path PATH` is a local download facade. It
uses a temporary managed-S3 export and is not a `HandlerType.CSV_FILE` alias.
It has `AW/N/B/DP`, requires `--overwrite` for an existing path, and uses test
stem `VIEW-EXPORT-CSV`.

## Existing `ViewExport` signature-to-command aliases

These exact signatures remain in the SDK inventory. Each must map to the one
destination handler above. An alias does not duplicate a CLI handler.

| Exact public signature | Canonical command | Alias test |
|---|---|---|
| `ViewExport.to_postgres(host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `view export postgres` | `ALIAS-VIEW-EXPORT-TO-POSTGRES` |
| `ViewExport.to_mysql(host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `view export mysql` | `ALIAS-VIEW-EXPORT-TO-MYSQL` |
| `ViewExport.to_s3(file_name: str | None = None, file_type: ExportFileType = ExportFileType.CSV, include_hidden: bool = False, **kwargs: Any) -> ExportResult` | `view export managed-s3` | `ALIAS-VIEW-EXPORT-TO-S3` |
| `ViewExport.to_dataset(dataset_name: str, *, target_ds_id: int | None = None, save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE, column_mapping: dict[str, str] | None = None, label_ids: list[int] | None = None, condition: Condition | CompoundCondition | NotCondition | None = None, timeout: int | None = None) -> int` | `view export dataset` | `ALIAS-VIEW-EXPORT-TO-DATASET` |
| `ViewExport.to_csv(output_path: str | None = None, timeout: int = 300) -> Path` | `view export csv` | `ALIAS-VIEW-EXPORT-TO-CSV` |
| `ViewExport.to_ftp(domain: str, directory: str, file: str, username: str, password: str, port: int = 21, **kwargs: Any) -> ExportResult` | `view export ftp` | `ALIAS-VIEW-EXPORT-TO-FTP` |
| `ViewExport.to_sftp(host: str, username: str, password: str = '', directory: str = '', file_name: str = '', port: int = 22, randomize_file_name: bool = False, ssh_key_authentication: bool = False, private_key: str = '', passphrase: str = '', **kwargs: Any) -> ExportResult` | `view export sftp` | `ALIAS-VIEW-EXPORT-TO-SFTP` |
| `ViewExport.to_email(emails: list[str], subject: str = '', message: str = '', resource: str = '', **kwargs: Any) -> ExportResult` | `view export email` | `ALIAS-VIEW-EXPORT-TO-EMAIL` |
| `ViewExport.to_mssql(host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `view export mssql` | `ALIAS-VIEW-EXPORT-TO-MSSQL` |
| `ViewExport.to_redshift(host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `view export redshift` | `ALIAS-VIEW-EXPORT-TO-REDSHIFT` |
| `ViewExport.to_bigquery(selected_profile: dict[str, Any], selected_identity: dict[str, Any], table: str, export_type: BigQueryExportType = BigQueryExportType.REPLACE, upsert_keys: list[dict[str, Any]] | None = None, partition: dict[str, Any] | None = None, **kwargs: Any) -> ExportResult` | `view export bigquery` | `ALIAS-VIEW-EXPORT-TO-BIGQUERY` |
| `ViewExport.to_elasticsearch(host: str, username: str, password: str, index: str, port: int = 9243, connection: str = 'https', chunksize: int = 200, **kwargs: Any) -> ExportResult` | `view export elasticsearch` | `ALIAS-VIEW-EXPORT-TO-ELASTICSEARCH` |
| `ViewExport.to_azure_blob(storage_account_name: str, tenant_id: str, client_id: str, client_secret: str, container_name: str, folder_path: str = '', file_name: str = '', **kwargs: Any) -> ExportResult` | `view export azure-blob` | `ALIAS-VIEW-EXPORT-TO-AZURE-BLOB` |
| `ViewExport.to_sharepoint(tenant_id: str, client_id: str, client_secret: str, site_url: str, document_library: str = 'Documents', folder_path: str = '', file_name: str = '', **kwargs: Any) -> ExportResult` | `view export sharepoint` | `ALIAS-VIEW-EXPORT-TO-SHAREPOINT` |
| `ViewExport.to_onedrive(tenant_id: str, client_id: str, client_secret: str, user_id: str, folder_path: str = '', file_name: str = '', **kwargs: Any) -> ExportResult` | `view export onedrive` | `ALIAS-VIEW-EXPORT-TO-ONEDRIVE` |
| `ViewExport.to_tableau(server_url: str, token_name: str, token_secret: str, site_name: str = '', project_name: str = 'Default', datasource_name: str = 'mammoth_export', ca_bundle_path: str = '', **kwargs: Any) -> ExportResult` | `view export tableau` | `ALIAS-VIEW-EXPORT-TO-TABLEAU` |
| `ViewExport.to_powerbi(username: str, password: str, client_id: str, dataset: str, table: str, **kwargs: Any) -> ExportResult` | `view export powerbi` | `ALIAS-VIEW-EXPORT-TO-POWERBI` |
| `ViewExport.to_rest_api(base_url: str, endpoint_path: str, auth_type: RestAuthType = RestAuthType.NONE, http_method: HttpMethod = HttpMethod.POST, wrap_path: str = 'records', batch_size: int = 1000, timeout_seconds: int = 30, ssl_verify: bool = True, auth: dict[str, Any] | None = None, headers: dict[str, str] | None = None, query_params: dict[str, str] | None = None, extra_body_fields: dict[str, Any] | None = None, **kwargs: Any) -> ExportResult` | `view export rest` | `ALIAS-VIEW-EXPORT-TO-REST-API` |
| `ViewExport.publish_to_db(table: str, odbc_type: OdbcType = OdbcType.POSTGRES) -> dict[str, Any]` | `view export publish-db` | `ALIAS-VIEW-EXPORT-PUBLISH-TO-DB` |

## Blocking ledger and release gate

The following blockers are normative. A command remains unregistered until its
blockers are resolved, but its manifest record and contract tests still exist.

| Blocker ID | Affected commands | Required evidence |
|---|---|---|
| `IO-TYPED-DICTS` | Current dict-returning batch, browse, connector, webhook, job, and `ViewExport` methods | Public strict request/result models and SDK URL/body/response tests |
| `IO-PAGINATION` | Every `O` and `SP` row | Typed continuation metadata; first, middle, final, empty, and repeated-token tests |
| `IO-JOB-SPLIT` | Uploads, batches, exports, and publish-db | Stable start result, public wait method, failure, timeout, interruption, and missing-job behavior |
| `IO-RESOLVER` | Export list/create/download | Public typed dataview-to-dataset resolution without private cross-subclient calls |
| `IO-EXPORT-CRUD` | Export get/update/delete | Public typed `ExportsAPI` methods for all three OpenAPI operations |
| `IO-EXPORT-OPTIONS` | Every helper with `**kwargs: Any` | `ExportCommonOptions` replaces kwargs and preserves every field |
| `IO-EXPORT-HANDLERS` | `csv_file`, `powerbi`, and any server-rejected handler | Successful contract fixture or reviewed sanitized server evidence; never infer support from the enum |
| `IO-CONNECTOR-TYPES` | Connector connection and ds-config mutations | Pinned-OpenAPI discriminated variants with recursive secret metadata |
| `IO-DOWNLOAD-SAFETY` | `view export csv` | Partial-file cleanup, fsync, atomic rename, traversal, and overwrite tests |
| `IO-LIVE-PERMISSION` | File upload, dataset, batch, webhook ingestion, and CSV export live tests | Release workspace preflight proves file-upload or dataset-create permission |
| `IO-EXTERNAL-FIXTURES` | Connector mutations and every external export | Dedicated disposable credentials, target allowlist, cleanup procedure, and sanitized ledger record |

The representative cross-catalog gates are:

```text
test_sdk_io_catalog_has_70_public_methods
test_sdk_io_catalog_has_all_19_export_handlers
test_sdk_io_signatures_match_introspection
test_sdk_io_aliases_have_one_canonical_handler
test_sdk_io_commands_have_typed_requests_and_results
test_sdk_io_secret_fields_have_secure_transports
test_sdk_io_list_commands_have_pagination_policies
test_sdk_io_async_commands_have_wait_policies
test_sdk_io_mutations_have_safety_and_retry_policies
test_sdk_io_live_policies_have_fixtures_or_blockers
test_export_destination_union_matches_handler_type
test_external_exports_require_confirmation_when_run_immediately
test_webhook_send_get_is_mutating_and_not_retried
test_csv_file_handler_is_not_aliased_to_managed_s3_download
```

Do not mark this appendix implemented because contract tests pass. Mark an
operation accepted only after its unit, subprocess, guarded live or reviewed
live-exemption evidence, redaction, and cleanup requirements pass.
