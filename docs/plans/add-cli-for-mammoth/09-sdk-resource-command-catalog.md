# Normative SDK resource command catalog

This appendix is the reviewed command disposition for the 105 public methods in
the resource APIs named below. It is normative for command manifests, handlers,
and tests. A handler MUST NOT invent a different command path, default, input
shape, pagination rule, wait rule, safety class, or live-test class. A method
marked `BLOCKED` reserves its command name but MUST NOT be registered until the
referenced blocker is fixed in the public SDK and its contract tests pass.

The inventory was read from the current branch on 2026-07-21. Signatures omit
the implicit `self` parameter and otherwise preserve source annotation spelling;
`_list` is the module alias for the built-in `list`. `workspace_id=None` means
the workspace stored in the selected authentication profile; it is not a local
option. `project_id=None` means client context and maps to global `--project`.

## Reading each record

- The first backticked value is the exact public SDK symbol and signature.
- `CLI` is the canonical path. `ALIAS ->` means the SDK method is covered by the
  named canonical handler and gets only an alias/parity test. `BLOCKED[Bnn]`
  reserves a path without registering it.
- Primary immutable resource IDs are positionals in the order shown by the
  command path. Other scalar arguments use `--kebab-case`; `bool=True` uses
  `--foo/--no-foo`, `bool=False` uses `--foo/--no-foo` with the negative default,
  and simple lists are repeatable options. Complex dictionaries, patch lists,
  conditions, `**kwargs`, and nested Pydantic models are document-only through
  `--input FILE|-`. Explicit scalar flags override document fields.
- `R` is the normalized SDK result type. Raw `dict[str, Any]` remains a strict
  command result adapter requirement; it is not permission to return sessions,
  clients, or secrets.
- `P` is `none`, `offset`, or `single_page`. `--all` is allowed only for
  `offset`. `P=single_page` MUST emit `meta.pagination.complete=false` unless the
  returned envelope proves completion.
- `W` is `not_async`, `always_wait`, or `returns_job`. `always_wait` has no
  `--no-wait`; `returns_job` MUST expose the submitted result and MUST NOT poll.
- `S` is the mutation class from the parity plan. `L` is its acceptance evidence
  class. The current release/workspace-4 permission failure still marks dataset,
  view, folder, and dependent dashboard live IDs `blocked_external`; it does not
  change their `L` value.
- `T=NAME` requires at least `UT-NAME`, `CT-NAME-HUMAN`,
  `CT-NAME-JSON`, and `CT-NAME-ERROR`. Add `CT-NAME-WAIT` and
  `CT-NAME-TIMEOUT` for `always_wait`; add `CT-NAME-NOWAIT` for
  `returns_job`; add `LT-NAME` only when `L` is a live class and
  preflight/fixtures pass. Aliases require
  `UT-ALIAS-NAME`. Destructive/high-impact commands also require
  `CT-NAME-CONFIRM`.

## WorkspaceAPI (`client.workspaces`)

- `mammoth.api.workspace.WorkspaceAPI.list(limit: int = 100) -> dict[str, Any]`
  - CLI `workspace list`; `--limit 100`; R raw workspace envelope; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `WORKSPACE-LIST`; B01.
- `WorkspaceAPI.get(workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `workspace get [WORKSPACE_ID]`; context ID is the default; R raw workspace; P `none`; W `not_async`; S `read`; L `live_read_only`; T `WORKSPACE-GET`.
- `WorkspaceAPI.update(patches: _list[WorkspacePatchOp], workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `workspace update [WORKSPACE_ID]`; `patches` is document-only `list[WorkspacePatchOp]`: `op="replace"`, path `name|metadata|plan_id|billing_cycle`, path-dependent value; R raw workspace; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `WORKSPACE-UPDATE`.
- `WorkspaceAPI.delete(workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `workspace delete [WORKSPACE_ID]`; exact immutable workspace-ID confirmation, not `--yes` alone; R raw deletion result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `WORKSPACE-DELETE`.
- `WorkspaceAPI.reactivate(workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `workspace reactivate [WORKSPACE_ID]`; R raw workspace; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `WORKSPACE-REACTIVATE`.
- `WorkspaceAPI.list_users(workspace_id: int | None = None) -> _list[dict[str, Any]]`
  - CLI `workspace user list [WORKSPACE_ID]`; R list extracted from `users`; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `WORKSPACE-USER-LIST`.
- `WorkspaceAPI.get_user(user_id: str, workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `workspace user get USER_ID`; admin permission may be required; R raw user; P `none`; W `not_async`; S `read`; L `live_read_only`; T `WORKSPACE-USER-GET`.
- `WorkspaceAPI.update_user(user_id: str, patches: _list[UserRolePatchOp], workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `workspace user update USER_ID`; document-only nonempty patches, `op="replace"`, `path="role"`, value `workspace_member|workspace_admin|workspace_owner|workspace_guest`; exact user-ID confirmation for owner/admin changes; R raw user; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `WORKSPACE-USER-UPDATE`.

## ProjectsAPI (`client.projects`)

- `mammoth.api.projects.ProjectsAPI.list(workspace_id: int | None = None, limit: int = 100) -> dict[str, Any]`
  - CLI `project list`; `--limit 100`; R raw `projects` envelope; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `PROJECT-LIST`; B01.
- `ProjectsAPI.get(project: int | str | None = None, workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project get [PROJECT]`; `PROJECT` is ID or exact name, omission only succeeds for one result; R `{id,name}`; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `PROJECT-GET`; B01.
- `ProjectsAPI.create(name: str, color: str | None = None, project_access: str | None = None, workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project create NAME`; `--color`, `--project-access only_me|some_members_of_workspace|all_members_of_workspace`; omitted values are server defaults; R raw project; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `PROJECT-CREATE`.
- `ProjectsAPI.update(project_id: int, name: str | None = None, color: str | None = None, workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project update PROJECT_ID`; optional `--name`, `--color`; R raw project; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `PROJECT-UPDATE`.
- `ProjectsAPI.delete(project_id: int, workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project delete PROJECT_ID`; immutable project-ID confirmation; R raw deletion result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `PROJECT-DELETE`.
- `ProjectsAPI.bulk_update(patch_data: dict[str, Any], workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project bulk-update`; document-only `patch_data`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `PROJECT-BULK-UPDATE`; `BLOCKED[B02]`.
- `ProjectsAPI.bulk_delete(project_ids: _list[int], workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project bulk-delete PROJECT_ID...`; sorted comma-separated ID-set confirmation; R raw deletion result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `PROJECT-BULK-DELETE`.
- `ProjectsAPI.add_users(project_id: int, user_ids: _list[str], role: str | None = None, workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project user add PROJECT_ID`; repeatable `--user USER_ID_OR_EMAIL`, optional `--role`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `PROJECT-USER-ADD`; B03.
- `ProjectsAPI.remove_users(project_id: int, user_ids: _list[str], workspace_id: int | None = None) -> dict[str, Any]`
  - CLI `project user remove PROJECT_ID`; repeatable `--user USER_ID`, sorted target-set confirmation; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `PROJECT-USER-REMOVE`; B03.
- `ProjectsAPI.browse(project_id: int, workspace_id: int | None = None, fields: str | None = None, name: str | None = None, browse_type: str | None = None, sort: str | None = None, offset: int | None = None, limit: int | None = None) -> dict[str, Any]`
  - CLI `project browse PROJECT_ID`; `--fields`, `--name`, `--browse-type`, `--sort`, `--offset`, `--limit`, all default omitted; R raw browse envelope; P `offset`; W `not_async`; S `read`; L `live_read_only`; T `PROJECT-BROWSE`; B04.

## FoldersAPI (`client.folders`)

- `mammoth.api.folders.FoldersAPI.get_project_root(workspace_id: int | None = None, project_id: int | None = None) -> FolderSchema`
  - CLI `folder root`; R local synthetic `FolderSchema(id=0,name="Project Root",resource_id=None)` after project-context validation; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `FOLDER-ROOT`.
- `FoldersAPI.list(workspace_id: int | None = None, project_id: int | None = None, fields: str | None = None, folder_ids: _list[int] | None = None, names: _list[str] | None = None, statuses: _list[str] | None = None, created_at: str | None = None, updated_at: str | None = None, created_by: _list[str] | None = None, limit: int = 50, offset: int = 0, sort: str | None = None) -> FoldersList`
  - CLI `folder list`; `--fields`; repeatable `--folder-id`, `--name`, `--status`, `--created-by`; `--created-at`, `--updated-at`, `--limit 50`, `--offset 0`, `--sort`; R `FoldersList`; P `offset`; W `not_async`; S `read`; L `live_disposable_project`; T `FOLDER-LIST`.
- `FoldersAPI.create(name: str, parent_resource_id: str | None = None, workspace_id: int | None = None, project_id: int | None = None) -> FolderSchema`
  - CLI `folder create NAME`; `--parent-resource-id`, default project root; input model `CreateFolder`; R `FolderSchema`; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `FOLDER-CREATE`.
- `FoldersAPI.delete(folder_ids: _list[int], workspace_id: int | None = None, project_id: int | None = None, check_dependency: bool = True, remove_contents: bool = True) -> None`
  - CLI `folder delete FOLDER_ID...`; `--check-dependency/--no-check-dependency` default true, `--remove-contents/--no-remove-contents` default true; sorted ID-set confirmation, and exact project ID plus phrase `DELETE FOLDER CONTENTS` when removing contents; R null; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `FOLDER-DELETE`.
- `FoldersAPI.move(resource_ids: _list[str], target_folder_resource_id: str | None = None, source_folder_resource_id: str | None = None, workspace_id: int | None = None, project_id: int | None = None) -> ObjectJobSchema`
  - CLI `folder move`; repeatable `--resource-id`; `--target-folder-resource-id` default root, optional `--source-folder-resource-id`; input model `BulkFolderPatchRequest(operation="move")`; R `ObjectJobSchema`; P `none`; W `returns_job`; S `benign_mutation`; L `live_disposable_project`; T `FOLDER-MOVE`; B05.

## DatasetsAPI (`client.datasets`)

- `mammoth.api.datasets.DatasetsAPI.list(workspace_id: int | None = None, project_id: int | None = None, limit: int = 100, sort: str = "(created_at:desc)") -> dict[str, Any]`
  - CLI `dataset list`; `--limit 100`, `--sort "(created_at:desc)"`; R raw datasets envelope; P `single_page`; W `not_async`; S `read`; L `live_disposable_project`; T `DATASET-LIST`; B01.
- `DatasetsAPI.get(dataset_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `dataset get DATASET_ID`; R raw dataset; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `DATASET-GET`.
- `DatasetsAPI.get_data(dataset_id: int, workspace_id: int | None = None, project_id: int | None = None, timeout: int = 300, poll_interval: int = 2) -> dict[str, Any]`
  - CLI `dataset data DATASET_ID`; global `--job-timeout` supplies `timeout`; do not expose `poll_interval` in v1; R completed response body; P `none`; W `always_wait`; S `read`; L `live_disposable_project`; T `DATASET-DATA`.
- `DatasetsAPI.create(dataset_spec: dict[str, Any], ds_creation_type: str, folder_resource_id: str | None = None, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `dataset create`; document-only `dataset_spec`, required `--ds-creation-type clone|cloud|sketch|weburl`, optional `--folder-resource-id`; R raw dataset/job-shaped body; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `DATASET-CREATE`; `BLOCKED[B06]`.
- `DatasetsAPI.update(patch_data: _list[dict[str, Any]], workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `dataset update`; document-only patch list; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `DATASET-UPDATE`; `BLOCKED[B07]`.
- `DatasetsAPI.rename(dataset_id: int, name: str, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `dataset rename DATASET_ID NAME`; convenience alias implemented through `update`; R raw result; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `DATASET-RENAME`.
- `DatasetsAPI.delete(dataset_id: int, workspace_id: int | None = None, project_id: int | None = None) -> None`
  - CLI `dataset delete DATASET_ID`; immutable dataset-ID confirmation; R null; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `DATASET-DELETE`.
- `DatasetsAPI.bulk_update(patch_data: dict[str, Any], workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `dataset bulk-update`; document-only `patch_data`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `DATASET-BULK-UPDATE`; `BLOCKED[B07]`.
- `DatasetsAPI.bulk_delete(workspace_id: int | None = None, project_id: int | None = None) -> None`
  - CLI `dataset bulk-delete`; R null; P `none`; W `not_async`; S `destructive`; L `contract_only_high_impact`; T `DATASET-BULK-DELETE`; `BLOCKED[B08]` and MUST NOT be exposed.
- `DatasetsAPI.list_batches(dataset_id: int, workspace_id: int | None = None, project_id: int | None = None) -> _list[dict[str, Any]]`
  - `ALIAS -> batch list DATASET_ID` (`BatchesAPI.list`); R list extracted from `batches`; P `single_page`; W `not_async`; S `read`; L `live_disposable_project`; T `DATASET-BATCH-LIST`.
- `DatasetsAPI.get_batch(dataset_id: int, batch_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - `ALIAS -> batch get DATASET_ID BATCH_ID` (`BatchesAPI.get`); R raw batch; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `DATASET-BATCH-GET`.
- `DatasetsAPI.get_file_settings(dataset_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `dataset file-settings DATASET_ID`; R raw file settings; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `DATASET-FILE-SETTINGS`.

## DataviewsAPI (`client.dataviews`)

- `mammoth.api.dataviews.DataviewsAPI.list(dataset_id: int, workspace_id: int | None = None, project_id: int | None = None, limit: int = 100, sort: str = "(created_at:desc)") -> dict[str, Any]`
  - CLI `view list DATASET_ID`; `--limit 100`, `--sort "(created_at:desc)"`; R raw envelope; P `single_page`; W `not_async`; S `read`; L `live_disposable_project`; T `VIEW-LIST`; B01.
- `DataviewsAPI.get(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - `ALIAS -> view get DATAVIEW_ID` (`ViewsResource.get`); low-level conversion additionally requires `dataset_id`; R raw dataview; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `DATAVIEW-GET`.
- `DataviewsAPI.create(dataset_id: int, name: str | None = "View", clone_config_from: int | None = None, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - `ALIAS -> view create DATASET_ID`; `--name View`, `--clone-from`; R completed dataview response; P `none`; W `always_wait`; S `benign_mutation`; L `live_disposable_project`; T `DATAVIEW-CREATE`.
- `DataviewsAPI.update(dataset_id: int, dataview_id: int, patch_data: _list[dict[str, Any]], workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view update DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; document-only JSON patch list; R raw result; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `VIEW-UPDATE`; `BLOCKED[B09]`.
- `DataviewsAPI.delete(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - `ALIAS -> view delete DATAVIEW_ID` (`ViewsResource.delete`); immutable view-ID confirmation; R raw deletion result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `DATAVIEW-DELETE`.
- `DataviewsAPI.bulk_delete(dataset_id: int, dataview_ids: _list[int] | str, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - `ALIAS -> view delete DATAVIEW_ID...` (`ViewsResource.bulk_delete`); CLI accepts typed repeated integers, never comma-separated raw text; sorted ID-set confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `DATAVIEW-BULK-DELETE`; B10.
- `DataviewsAPI.get_data(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None, timeout: int | None = None, poll_interval: int = 2) -> dict[str, Any]`
  - CLI `view data get DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; global `--job-timeout` supplies `timeout`; do not expose `poll_interval` in v1; R completed response; P `none`; W `always_wait`; S `read`; L `live_disposable_project`; T `VIEW-DATA-GET`.
- `DataviewsAPI.query_data(dataset_id: int, dataview_id: int, sequence: int = 0, offset: int = 1, limit: int = 400, columns: _list[str] | None = None, condition: dict[str, Any] | None = None, sort: str | None = None, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view data query DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; `--sequence 0`, `--offset 1`, `--limit 400`, repeatable `--column`, `--sort`; `condition` is the shared document-only condition model; R completed data response; P `offset`; W `always_wait`; S `read`; L `live_disposable_project`; T `VIEW-DATA-QUERY`; B11.
- `DataviewsAPI.active_users(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view active-user list DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; R raw activity envelope; P `single_page`; W `not_async`; S `read`; L `live_disposable_project`; T `VIEW-ACTIVE-USER-LIST`.
- `DataviewsAPI.mark_active(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view active-user mark DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; R raw activity state; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `VIEW-ACTIVE-USER-MARK`.
- `DataviewsAPI.conditional_format_list(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None) -> _list[dict[str, Any]]`
  - CLI `view conditional-format list DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; R extracted rule list; P `single_page`; W `not_async`; S `read`; L `live_disposable_project`; T `VIEW-CONDITIONAL-FORMAT-LIST`.
- `DataviewsAPI.conditional_format_create(dataset_id: int, dataview_id: int, rule: dict[str, Any], workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view conditional-format create DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; document-only `rule`; R raw rule; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `VIEW-CONDITIONAL-FORMAT-CREATE`; `BLOCKED[B09]`.
- `DataviewsAPI.conditional_format_update(dataset_id: int, dataview_id: int, rule: dict[str, Any], workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view conditional-format update DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; document-only `rule`; R raw rule; P `none`; W `not_async`; S `benign_mutation`; L `live_disposable_project`; T `VIEW-CONDITIONAL-FORMAT-UPDATE`; `BLOCKED[B09]`.
- `DataviewsAPI.conditional_format_delete(dataset_id: int, dataview_id: int, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - CLI `view conditional-format delete-all DATAVIEW_ID`; resolve `dataset_id` through the public typed view resolver; exact phrase `DELETE ALL CONDITIONAL FORMATS`; R raw deletion result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `VIEW-CONDITIONAL-FORMAT-DELETE-ALL`.
- `DataviewsAPI.draft_mode(dataset_id: int, dataview_id: int, command: str, workspace_id: int | None = None, project_id: int | None = None) -> dict[str, Any]`
  - `ALIAS -> view draft enter|submit|discard`; command is document-discriminated, never a free-form CLI argument; R raw draft state; P `none`; W `not_async`; S `reversible_pipeline`; L `live_disposable_project`; T `VIEW-DRAFT-COMMAND`; `BLOCKED[B12]`.

## ViewsResource (`client.views`)

- `mammoth.client.ViewsResource.get(view_id: int) -> View`
  - CLI `view get VIEW_ID`; R normalized `View` metadata, never its client/export helper; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `VIEW-GET`; `BLOCKED[B10]`.
- `ViewsResource.list(dataset_id: int) -> _list[View]`
  - `ALIAS -> view list DATASET_ID` (`DataviewsAPI.list`); R normalized list of `View` metadata; P `single_page`; W `not_async`; S `read`; L `live_disposable_project`; T `VIEWS-RESOURCE-LIST`; B01.
- `ViewsResource.create(dataset_id: int, name: str = "View", clone_from: int | None = None) -> View`
  - CLI `view create DATASET_ID`; `--name View`, `--clone-from`; R normalized `View`; P `none`; W `always_wait`; S `benign_mutation`; L `live_disposable_project`; T `VIEW-CREATE`.
- `ViewsResource.delete(view_id: int) -> dict[str, Any]`
  - CLI `view delete VIEW_ID`; immutable view-ID confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `VIEW-DELETE`; `BLOCKED[B10]`.
- `ViewsResource.bulk_delete(view_ids: _list[int]) -> dict[str, Any]`
  - `ALIAS -> view delete VIEW_ID...`; require at least two unique IDs; all IDs MUST resolve to the same dataset before mutation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `VIEW-BULK-DELETE`; `BLOCKED[B10]`.

## DashboardsAPI (`client.dashboards`)

- `mammoth.api.dashboards.DashboardsAPI.list() -> _list[dict[str, Any]]`
  - CLI `dashboard list`; R extracted dashboard list; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `DASHBOARD-LIST`.
- `DashboardsAPI.create(intent: str, source: _list[int], enable_filters: bool = True, enable_pages: bool = False) -> dict[str, Any]`
  - CLI `dashboard create`; required `--intent` (minimum 10 chars), repeatable positive `--source`, `--enable-filters/--no-enable-filters` default true, `--enable-pages/--no-enable-pages` default false; R raw dashboard/job body; P `none`; W `returns_job`; S `benign_mutation`; L `live_disposable_project`; T `DASHBOARD-CREATE`; B13.
- `DashboardsAPI.get(dashboard_id: int) -> dict[str, Any]`
  - CLI `dashboard get DASHBOARD_ID`; R raw dashboard; P `none`; W `not_async`; S `read`; L `live_read_only`; T `DASHBOARD-GET`.
- `DashboardsAPI.update(dashboard_id: int, patch: _list[DashboardPatchItem]) -> dict[str, Any]`
  - CLI `dashboard update DASHBOARD_ID`; document-only nonempty `DashboardPatchItem` list (`op add|replace`, path `intent|title|theme|pages|filters`, typed value); R raw dashboard/job body; P `none`; W `returns_job`; S `benign_mutation`; L `live_disposable_project`; T `DASHBOARD-UPDATE`; B13.
- `DashboardsAPI.delete(dashboard_id: int) -> dict[str, Any]`
  - CLI `dashboard delete DASHBOARD_ID`; immutable dashboard-ID confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_disposable_project`; T `DASHBOARD-DELETE`.
- `DashboardsAPI.get_sources() -> _list[dict[str, Any]]`
  - CLI `dashboard source list`; R extracted source list; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `DASHBOARD-SOURCE-LIST`; B04.
- `DashboardsAPI.get_analytics(dashboard_id: int) -> dict[str, Any]`
  - CLI `dashboard analytics DASHBOARD_ID`; R raw analytics; P `none`; W `not_async`; S `read`; L `live_read_only`; T `DASHBOARD-ANALYTICS`.
- `DashboardsAPI.share(dashboard_id: int, type_of_auth: DashboardAuthType, users: _list[DashboardShareUser] | None = None) -> dict[str, Any]`
  - CLI `dashboard share DASHBOARD_ID`; required `--type-of-auth mammoth|public|password`; `users` document-only with defaults `role=dashboard_viewer`, `shared=true`; exact ID confirmation; R raw share result; P `none`; W `not_async`; S `external_effect`; L `contract_only_high_impact`; T `DASHBOARD-SHARE`; B14.
- `DashboardsAPI.action(dashboard_id: int, action: DashboardActionType, params_enabled: bool | None = None, params_view_id: int | None = None) -> dict[str, Any]`
  - CLI `dashboard action DASHBOARD_ID`; `--action sync|publish-data|publish-presentation|unpublish|auto-sync|auto-publish|delete-source`, optional `--enabled/--no-enabled`, `--view-id`; publish/unpublish/delete-source require exact target confirmation; R raw result; P `none`; W `returns_job`; S `external_effect`; L `contract_only_high_impact`; T `DASHBOARD-ACTION`; B13.
- `DashboardsAPI.get_by_url(url: str) -> dict[str, Any]`
  - CLI `dashboard get-by-url URL`; URL is a slug, not an arbitrary request URL; R raw dashboard; P `none`; W `not_async`; S `read`; L `live_read_only`; T `DASHBOARD-GET-BY-URL`.
- `DashboardsAPI.get_draft_data(dashboard_id: int, sql: str) -> dict[str, Any]`
  - CLI `dashboard data draft DASHBOARD_ID`; required `--sql`; R raw query result; P `none`; W `not_async`; S `read`; L `live_disposable_project`; T `DASHBOARD-DATA-DRAFT`.
- `DashboardsAPI.get_publish_data(dashboard_id: int, sql: str) -> dict[str, Any]`
  - CLI `dashboard data published DASHBOARD_ID`; required `--sql`; R raw query result; P `none`; W `not_async`; S `read`; L `live_read_only`; T `DASHBOARD-DATA-PUBLISHED`.

## AutomationsAPI (`client.automations`)

- `mammoth.api.automations.AutomationsAPI.list() -> _list[dict[str, Any]]`
  - CLI `automation list`; R extracted automation list; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `AUTOMATION-LIST`.
- `AutomationsAPI.create(name: str, description: str, tasks: _list[AutomationTaskSpec], conditions: _list[AutomationConditionSpec] | None = None, condition_mode: AutomationConditionMode = AutomationConditionMode.AND) -> dict[str, Any]`
  - CLI `automation create`; `--name`, `--description`; tasks/conditions document-only typed models; `--condition-mode and|or` default `and`; R raw automation; P `none`; W `not_async`; S `external_effect`; L `live_dedicated_external_fixture`; T `AUTOMATION-CREATE`; B15.
- `AutomationsAPI.get(automation_id: int) -> dict[str, Any]`
  - CLI `automation get AUTOMATION_ID`; R raw automation; P `none`; W `not_async`; S `read`; L `live_read_only`; T `AUTOMATION-GET`.
- `AutomationsAPI.update(automation_id: int, patch: _list[AutomationPatchItem]) -> dict[str, Any]`
  - CLI `automation update AUTOMATION_ID`; document-only nonempty typed patch: command/run, replace/status (`suspend|resume`), or replace/details (`PatchAutomationDetails`); run/status require exact ID confirmation; R raw result; P `none`; W `not_async`; S `external_effect`; L `live_dedicated_external_fixture`; T `AUTOMATION-UPDATE`; B15.
- `AutomationsAPI.delete(automation_id: int) -> dict[str, Any]`
  - CLI `automation delete AUTOMATION_ID`; immutable ID confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_dedicated_external_fixture`; T `AUTOMATION-DELETE`.
- `AutomationsAPI.list_schedules() -> _list[dict[str, Any]]`
  - `ALIAS -> schedule list` (`SchedulesAPI.list`); R extracted list; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `AUTOMATION-SCHEDULE-LIST`; B16.
- `AutomationsAPI.create_schedule(spec: ScheduleCreateSpec) -> dict[str, Any]`
  - `ALIAS -> schedule create` (`SchedulesAPI.create`); document-only `ScheduleCreateSpec`; R raw schedule; P `none`; W `not_async`; S `external_effect`; L `live_dedicated_external_fixture`; T `AUTOMATION-SCHEDULE-CREATE`.
- `AutomationsAPI.update_schedule(schedule_id: int, patch: _list[SchedulePatchItem]) -> dict[str, Any]`
  - `ALIAS -> schedule update SCHEDULE_ID` (`SchedulesAPI.update`); document-only patch; R raw schedule; P `none`; W `not_async`; S `external_effect`; L `live_dedicated_external_fixture`; T `AUTOMATION-SCHEDULE-UPDATE`.
- `AutomationsAPI.delete_schedule(schedule_id: int) -> dict[str, Any]`
  - `ALIAS -> schedule delete SCHEDULE_ID` (`SchedulesAPI.delete`); immutable ID confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_dedicated_external_fixture`; T `AUTOMATION-SCHEDULE-DELETE`.

`AutomationTaskSpec` is discriminated by `task_type`:
`run_data_retrieval|append_data|send_an_alert|pull_cloud_files` with
`TaskDetailsSpec`; `AutomationConditionSpec` is discriminated by
`condition_type`: `at_specific_time|new_data_addition_in_folder|run_config|cloud_source_name_pattern`.
Email recipients, connector/connection identifiers, and cloud paths are fixture
guard fields; outbound email is never authorized by a disposable project.

## SchedulesAPI (`client.schedules`)

- `mammoth.api.schedules.SchedulesAPI.list(project_id: int | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]`
  - CLI `schedule list`; `--limit 50`, `--offset 0`; R raw schedule envelope; P `offset`; W `not_async`; S `read`; L `live_read_only`; T `SCHEDULE-LIST`; B04.
- `SchedulesAPI.get(schedule_id: int, project_id: int | None = None) -> dict[str, Any]`
  - CLI `schedule get SCHEDULE_ID`; R raw schedule; P `none`; W `not_async`; S `read`; L `live_read_only`; T `SCHEDULE-GET`.
- `SchedulesAPI.create(spec: ScheduleCreateSpec, project_id: int | None = None) -> dict[str, Any]`
  - CLI `schedule create`; document-only `ScheduleCreateSpec`: required `rrule.frequency`, `rrule.start`; optional positive `interval`, weekdays/month-days and work items; R raw schedule; P `none`; W `not_async`; S `external_effect`; L `live_dedicated_external_fixture`; T `SCHEDULE-CREATE`.
- `SchedulesAPI.update(schedule_id: int, patch: _list[SchedulePatchItem], project_id: int | None = None) -> dict[str, Any]`
  - CLI `schedule update SCHEDULE_ID`; document-only nonempty patch, `op="replace"`, path `rrule|status`; status `pause|resume`; exact ID confirmation for resume; R raw schedule; P `none`; W `not_async`; S `external_effect`; L `live_dedicated_external_fixture`; T `SCHEDULE-UPDATE`.
- `SchedulesAPI.delete(schedule_id: int, project_id: int | None = None) -> dict[str, Any]`
  - CLI `schedule delete SCHEDULE_ID`; immutable ID confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_dedicated_external_fixture`; T `SCHEDULE-DELETE`.

## UserProfileAPI (`client.user_profile`)

- `mammoth.api.user_profile.UserProfileAPI.get() -> dict[str, Any]`
  - CLI `user get`; R raw current profile with recursive redaction; P `none`; W `not_async`; S `read`; L `live_read_only`; T `USER-GET`.
- `UserProfileAPI.update(**fields: Any) -> dict[str, Any]`
  - CLI `user update`; document-only strict profile fields; R raw profile; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `USER-UPDATE`; `BLOCKED[B17]`.
- `UserProfileAPI.change_password(current_password: str, new_password: str) -> dict[str, Any]`
  - CLI `user change-password`; both secrets use hidden prompt, permission-checked input, or dedicated stdin secret transport—never normal flags; R redacted raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `USER-CHANGE-PASSWORD`; `BLOCKED[B18]`.
- `UserProfileAPI.get_preferences() -> dict[str, Any]`
  - CLI `user preference get`; R raw preferences; P `none`; W `not_async`; S `read`; L `live_read_only`; T `USER-PREFERENCE-GET`.
- `UserProfileAPI.update_preferences(**prefs: Any) -> dict[str, Any]`
  - CLI `user preference update`; document-only strict preference fields; R raw preferences; P `none`; W `not_async`; S `benign_mutation`; L `contract_only_high_impact`; T `USER-PREFERENCE-UPDATE`; `BLOCKED[B17]`.

## AddonsAPI (`client.addons`)

Every addon mutation can alter entitlement or billing and therefore requires
exact workspace-ID confirmation plus `contract_only_high_impact`; `--yes` alone
is insufficient.

- `mammoth.api.addons.AddonsAPI.list() -> dict[str, Any]`
  - CLI `addon list`; R raw addon envelope; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `ADDON-LIST`.
- `AddonsAPI.add_connector(connector_id: int | None = None, connector_ids: _list[int] | None = None) -> dict[str, Any]`
  - CLI `addon connector add`; exactly one of `--connector-id` or repeatable `--connector-ids`, all positive; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `ADDON-CONNECTOR-ADD`.
- `AddonsAPI.remove_connector(connector_id: int | None = None, connector_ids: _list[int] | None = None) -> dict[str, Any]`
  - CLI `addon connector remove`; same exclusive inputs; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `ADDON-CONNECTOR-REMOVE`.
- `AddonsAPI.add_storage(additional_storage_gb: int) -> dict[str, Any]`
  - CLI `addon storage add`; required positive `--additional-storage-gb`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `ADDON-STORAGE-ADD`.
- `AddonsAPI.remove_storage(removal_storage_gb: int) -> dict[str, Any]`
  - CLI `addon storage remove`; required positive `--removal-storage-gb`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `ADDON-STORAGE-REMOVE`.
- `AddonsAPI.add_users(user_count: int = 1) -> dict[str, Any]`
  - CLI `addon user add`; positive `--user-count 1`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `ADDON-USER-ADD`.
- `AddonsAPI.remove_users(user_count: int) -> dict[str, Any]`
  - CLI `addon user remove`; required positive `--user-count`; R raw result; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `ADDON-USER-REMOVE`.

## ReportsAPI (`client.reports`)

- `mammoth.api.reports.ReportsAPI.list(limit: int = 50, offset: int = 0) -> dict[str, Any]`
  - CLI `report list`; `--limit 50`, `--offset 0`; R raw report envelope; P `offset`; W `not_async`; S `read`; L `live_read_only`; T `REPORT-LIST`.

## ActivityLogsAPI (`client.activity_logs`)

- `mammoth.api.activity_logs.ActivityLogsAPI.list(limit: int = 50, offset: int = 0, sort: str | None = None, **filters: Any) -> dict[str, Any]`
  - CLI `activity list`; `--limit 50`, `--offset 0`, optional `--sort`; filters document-only; R raw activity envelope; P `offset`; W `not_async`; S `read`; L `live_read_only`; T `ACTIVITY-LIST`; `BLOCKED[B17]`.
- `ActivityLogsAPI.export(format: str = "csv", **filters: Any) -> dict[str, Any]`
  - CLI `activity export`; `--format csv`; filters document-only; R raw download/job-shaped result; P `none`; W `returns_job`; S `read`; L `live_read_only`; T `ACTIVITY-EXPORT`; `BLOCKED[B19]`.

## ExternalKeysAPI (`client.external_keys`)

- `mammoth.api.external_keys.ExternalKeysAPI.list() -> dict[str, Any]`
  - CLI `external-key list`; R raw key envelope with recursive secret redaction; P `single_page`; W `not_async`; S `read`; L `live_read_only`; T `EXTERNAL-KEY-LIST`.
- `ExternalKeysAPI.get(key_id: int) -> dict[str, Any]`
  - CLI `external-key get KEY_ID`; R redacted raw key metadata; P `none`; W `not_async`; S `read`; L `live_read_only`; T `EXTERNAL-KEY-GET`.
- `ExternalKeysAPI.create(key_type: ExternalKeyType, key_name: str, secure_key: str, description: str | None = None, model_id: str | None = None, model_settings: ModelConfigSpec | None = None) -> dict[str, Any]`
  - CLI `external-key create`; `--key-type open_ai|anthropic|gemini|grok`, `--key-name`, optional `--description`, `--model-id`; `secure_key` is secret prompt/input/stdin only; `ModelConfigSpec` is document-only and requires model ID; R recursively redacted raw key; P `none`; W `not_async`; S `high_impact`; L `live_dedicated_external_fixture`; T `EXTERNAL-KEY-CREATE`.
- `ExternalKeysAPI.delete(key_id: int) -> dict[str, Any]`
  - CLI `external-key delete KEY_ID`; immutable ID confirmation; R raw result; P `none`; W `not_async`; S `destructive`; L `live_dedicated_external_fixture`; T `EXTERNAL-KEY-DELETE`.

`ModelConfigSpec` defaults every field to null: `thinking_budget >= -1`,
`thinking_level`, `reasoning_effort`, `web_search`, `cached_input`, `batch_api`.
The CLI redaction key set MUST include `secure_key`, provider-token variants, and
any server-returned secret material.

## ClientAppsAPI (`client.client_apps`)

- `mammoth.api.clientapps.ClientAppsAPI.list(workspace_id: int | None = None, limit: int = 10, offset: int = 0, fields: str | None = None, sort: str | None = None) -> ClientAppsListResponse`
  - CLI `client-app list`; `--limit 10`, `--offset 0`, optional `--fields`, `--sort`; R `ClientAppsListResponse`; P `offset`; W `not_async`; S `read`; L `live_read_only`; T `CLIENT-APP-LIST`; B20.
- `ClientAppsAPI.create(app_name: str, description: str | None = None, workspace_id: int | None = None) -> ClientAppPostResponse`
  - CLI `client-app create APP_NAME`; optional `--description`; R `ClientAppPostResponse`, with any app key/token emitted only once through approved secret output and redacted from diagnostics; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `CLIENT-APP-CREATE`; B20.
- `ClientAppsAPI.get(client_key: str, workspace_id: int | None = None, fields: str | None = None) -> ClientAppSchema`
  - CLI `client-app get CLIENT_KEY`; optional `--fields`; client key is a secret-bearing identifier and is redacted in diagnostics; R `ClientAppSchema`; P `none`; W `not_async`; S `read`; L `live_read_only`; T `CLIENT-APP-GET`; B20.
- `ClientAppsAPI.update(client_key: str, patch_request: PatchRequest, workspace_id: int | None = None) -> ClientAppSchema`
  - CLI `client-app update CLIENT_KEY`; document-only `PatchRequest(patch=list[PatchOperation])`, op/path/value currently strings; exact client-key confirmation; R `ClientAppSchema`; P `none`; W `not_async`; S `high_impact`; L `contract_only_high_impact`; T `CLIENT-APP-UPDATE`; `BLOCKED[B21]`.
- `ClientAppsAPI.delete(client_key: str, workspace_id: int | None = None) -> None`
  - CLI `client-app delete CLIENT_KEY`; exact client-key confirmation; R null; P `none`; W `not_async`; S `destructive`; L `contract_only_high_impact`; T `CLIENT-APP-DELETE`; B20.

## SDK blocker register

- `B01 FIRST_PAGE_ONLY`: workspace/project/dataset/dataview list methods have no
  offset/cursor. `ProjectsAPI.get`, `ViewsResource.list`, and private dataview
  discovery can miss resources beyond the first page. Add a public proven
  continuation contract before `--all` or completeness claims.
- `B02 PROJECT_BULK_PATCH_UNTYPED`: `ProjectsAPI.bulk_update` accepts an
  unconstrained dictionary. Add a strict public request model and target set.
- `B03 PROJECT_USER_ID_ROLE_UNTYPED`: add/remove accept strings and an arbitrary
  role; OpenAPI-backed user identifier and role models are required.
- `B04 SERVER_VARIANCE`: project browse and dashboard sources are documented as
  returning HTTP 500 on some servers; schedule list may return 405. A permission
  or 5xx response is not `server_unavailable`; retain the live exemption evidence.
- `B05 FOLDER_MOVE_NO_WAIT`: the SDK returns `ObjectJobSchema` but exposes no
  public operation-specific wait method. Do not advertise `--wait`/`--no-wait`.
- `B06 DATASET_CREATE_UNTYPED_ASYNC`: creation type is a free string,
  `dataset_spec` is arbitrary, and a job-shaped server response would be returned
  without waiting. Add a discriminated create request and stable
  submitted/completed result union before assigning an asynchronous wait policy.
- `B07 DATASET_PATCH_UNTYPED`: update accepts raw operations that include rename,
  refresh, column changes, reattach, and deletion. Split typed commands or add a
  discriminated patch union; do not let a benign command smuggle deletion.
- `B08 DATASET_BULK_DELETE_TARGETLESS`: the SDK sends collection DELETE without
  target IDs. The command is forbidden until OpenAPI proves exact targets and a
  typed SDK request carries them.
- `B09 DATAVIEW_INPUT_UNTYPED`: dataview patch and conditional-format rule bodies
  are arbitrary dictionaries. Add strict public request models before handlers.
- `B10 VIEW_DATASET_RESOLUTION`: `ViewsResource.get/delete/bulk_delete` calls the
  private pipeline discovery helper; bulk delete resolves only the first ID and
  assumes every view shares its dataset. Add public, paginated resolution and
  validate every target before mutation.
- `B11 QUERY_OFFSET_SEMANTICS`: dataview query is one-indexed (`offset=1`) and
  has no response model/continuation proof. `--all` is blocked even though the
  request exposes offset and limit.
- `B12 DRAFT_COMMAND_DRIFT`: `DataviewsAPI` docstrings say
  `enter|commit|discard`, `DraftCommand` uses `enter|submit|discard|exit`, and
  this API takes free text. Replace it with the shared enum and typed server
  state; cross-process status/auto-run still require public SDK methods.
- `B13 DASHBOARD_ASYNC_UNTYPED`: create/update/action may return job-shaped raw
  dictionaries but do not expose a stable typed job or waiter. Keep
  `returns_job`; do not claim completion.
- `B14 DASHBOARD_PASSWORD_MISSING`: password sharing is an enum value but the SDK
  signature has no password input. Contract-test or repair this auth variant
  before allowing `type_of_auth=password`.
- `B15 AUTOMATION_EXTERNAL_EFFECTS`: task models can pull cloud files and send
  email. Live tests require connector/email allowlists and dedicated fixtures;
  project isolation alone is insufficient.
- `B16 DUPLICATE_SCHEDULE_SURFACE`: `AutomationsAPI` and `SchedulesAPI` expose the
  same project schedule routes with different list envelopes/pagination.
  `SchedulesAPI` owns canonical handlers; automation schedule methods are
  aliases only.
- `B17 VARIADIC_INPUT_UNTYPED`: user/profile preference fields and activity
  filters are `**Any`. Generate strict OpenAPI-backed request models; unrecognized
  fields must fail before transport.
- `B18 PASSWORD_ENDPOINT_UNSPECIFIED`: change-password is absent from the public
  OpenAPI. It remains reserved and contract-only until a pinned contract and
  secret/redaction metadata exist.
- `B19 ACTIVITY_EXPORT_UNTYPED_ASYNC`: export format, filters, and download/job
  response are raw. Add format enum, filter model, and typed result union before
  registering the command.
- `B20 CLIENT_APP_SECRET_SHAPE`: response wrappers can contain app keys/tokens
  but have no field-level secret metadata, and list pagination has no total/next
  field. Add redaction metadata and a proven completion rule.
- `B21 CLIENT_APP_PATCH_UNCONSTRAINED`: `PatchOperation.op`, `path`, and `value`
  are arbitrary strings. Add enums/path-dependent values before update is
  exposed.

## Cross-cutting acceptance rules

1. A canonical handler calls exactly the public method named here. Alias records
   do not duplicate handlers and aliases never form chains.
2. All list commands test empty, first, middle, and final pages where `P=offset`;
   `single_page` tests assert the incompleteness metadata. Repeated offset/token
   protection is mandatory before `--all`.
3. `always_wait` tests cover success, server failure, timeout, unrecognized state,
   and interruption. `returns_job` tests prove that no hidden polling occurs.
4. Destructive commands resolve immutable targets with reads before prompting.
   High-impact/external-effect commands enforce their fixture and confirmation
   policy before the SDK call.
5. `live_disposable_project` tests use the crash-safe ledger and reverse-order
   cleanup. `live_dedicated_external_fixture` tests additionally verify the
   connector, recipient, provider, or credential allowlist. Contract-only
   records have `live_test: null`, an exemption reason, sanitized fixture, guard,
   and reviewer.
6. Test IDs derived from every `T` stem are representative minimums, not a cap.
   For example, `T=FOLDER-MOVE` yields `UT-FOLDER-MOVE`,
   `CT-FOLDER-MOVE-JSON`, `CT-FOLDER-MOVE-NOWAIT`, and guarded
   `LT-FOLDER-MOVE`; the blocked release
   environment records the last ID as `blocked_external`.
