# Complete public SDK method inventory

This appendix is mechanically generated from the current SDK source. It
covers every non-private class method declared in `mammoth/client.py`,
`mammoth/view.py`, `mammoth/api/`, and `mammoth/_mixins/`. The reviewed SDK
and command manifests remain the normative disposition records.

- Public method count: `242`.
- Inventory order: fully qualified implementation symbol.
- Transformation mixin methods are invoked publicly through `mammoth.view.View`.

| Public/implementation symbol | Exact source signature | Source line |
|---|---|---:|
| `mammoth._mixins._advanced_ops.AdvancedOpsMixin.add_sql` | `add_sql(self, query: str) -> dict[str, Any]` | `mammoth/_mixins/_advanced_ops.py:306` |
| `mammoth._mixins._advanced_ops.AdvancedOpsMixin.gen_ai` | `gen_ai(self, prompt: str, context_columns: list[str], new_column: str='AI Result', assistant_data: list[str] \| None=None, context_columns_derivation: bool \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_advanced_ops.py:211` |
| `mammoth._mixins._advanced_ops.AdvancedOpsMixin.generate_sql` | `generate_sql(self, intent: str) -> str` | `mammoth/_mixins/_advanced_ops.py:259` |
| `mammoth._mixins._advanced_ops.AdvancedOpsMixin.join` | `join(self, foreign_view: int \| View, join_type: JoinType, on: list[JoinKeySpec], select: list[str \| JoinSelectSpec], column_prefix: str \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_advanced_ops.py:33` |
| `mammoth._mixins._advanced_ops.AdvancedOpsMixin.json_extract` | `json_extract(self, column: str, json_type: JsonType=JsonType.OBJECT, keys: list[str] \| None=None, extractions: list[JsonExtractionSpec] \| None=None, keep_source: bool=False, op_type: JsonOpType \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_advanced_ops.py:156` |
| `mammoth._mixins._advanced_ops.AdvancedOpsMixin.lookup` | `lookup(self, source: str, lookup_view_id: int, key: str, value: str, new_column: str \| None=None, existing_column: str \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_advanced_ops.py:105` |
| `mammoth._mixins._aggregate_ops.AggregateOpsMixin.crosstab` | `crosstab(self, rows: list[str], pivot_column: str, select: CrosstabSpec \| list[CrosstabSpec], *, dataset_name: str, save_as_mode: SaveAsDatasetMode=SaveAsDatasetMode.REPLACE, target_ds_id: int \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None, timeout: int \| None=None) -> int` | `mammoth/_mixins/_aggregate_ops.py:130` |
| `mammoth._mixins._aggregate_ops.AggregateOpsMixin.pivot` | `pivot(self, group_by: list[str], aggregations: list[AggregationSpec], condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_aggregate_ops.py:32` |
| `mammoth._mixins._aggregate_ops.AggregateOpsMixin.window` | `window(self, function: WindowFunction, column: str \| None=None, new_column: str \| None=None, column_type: ColumnType=ColumnType.NUMERIC, existing_column: str \| None=None, partition_by: list[str] \| None=None, order_by: list[list[str \| SortDirection]] \| None=None, range_type: WindowRange=WindowRange.UNBOUNDED) -> dict[str, Any]` | `mammoth/_mixins/_aggregate_ops.py:76` |
| `mammoth._mixins._column_ops.ColumnOpsMixin.add_column` | `add_column(self, name: str, column_type: ColumnType=ColumnType.TEXT) -> dict[str, Any]` | `mammoth/_mixins/_column_ops.py:26` |
| `mammoth._mixins._column_ops.ColumnOpsMixin.combine_columns` | `combine_columns(self, sources: list[str], new_column: str \| None=None, column_type: ColumnType=ColumnType.TEXT, existing_column: str \| None=None, separator: str=' ', condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_column_ops.py:81` |
| `mammoth._mixins._column_ops.ColumnOpsMixin.convert_type` | `convert_type(self, conversions: list[ConversionSpec]) -> dict[str, Any]` | `mammoth/_mixins/_column_ops.py:135` |
| `mammoth._mixins._column_ops.ColumnOpsMixin.copy_columns` | `copy_columns(self, copies: list[CopySpec]) -> dict[str, Any]` | `mammoth/_mixins/_column_ops.py:60` |
| `mammoth._mixins._column_ops.ColumnOpsMixin.delete_columns` | `delete_columns(self, columns: list[str]) -> dict[str, Any]` | `mammoth/_mixins/_column_ops.py:44` |
| `mammoth._mixins._date_ops.DateOpsMixin.date_diff` | `date_diff(self, component: DateDiffUnit, start: str, end: str, new_column: str \| None=None, existing_column: str \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_date_ops.py:58` |
| `mammoth._mixins._date_ops.DateOpsMixin.extract_date` | `extract_date(self, column: str, component: DateComponent, new_column: str \| None=None, existing_column: str \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_date_ops.py:24` |
| `mammoth._mixins._date_ops.DateOpsMixin.increment_date` | `increment_date(self, column: str, delta: DateDelta, new_column: str \| None=None, existing_column: str \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_date_ops.py:96` |
| `mammoth._mixins._filter_ops.FilterOpsMixin.filter_rows` | `filter_rows(self, condition: Condition \| CompoundCondition \| NotCondition, filter_type: FilterType=FilterType.SHOW, prompt: str='') -> dict[str, Any]` | `mammoth/_mixins/_filter_ops.py:20` |
| `mammoth._mixins._filter_ops.FilterOpsMixin.set_values` | `set_values(self, values: list[SetValue], new_column: str \| None=None, column_type: ColumnType=ColumnType.TEXT, existing_column: str \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_filter_ops.py:45` |
| `mammoth._mixins._host.ViewHost.list_tasks` | `list_tasks(self) -> list[dict[str, Any]]` | `mammoth/_mixins/_host.py:48` |
| `mammoth._mixins._host.ViewHost.refresh` | `refresh(self) -> View` | `mammoth/_mixins/_host.py:50` |
| `mammoth._mixins._math_ops.MathOpsMixin.math` | `math(self, expression: str, new_column: str \| None=None, column_type: ColumnType=ColumnType.NUMERIC, existing_column: str \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_math_ops.py:20` |
| `mammoth._mixins._math_ops.MathOpsMixin.small_large` | `small_large(self, function: SmallLargeFunction, columns: list[str], index: int=1, constants: list[float] \| None=None, new_column: str \| None=None, existing_column: str \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_math_ops.py:60` |
| `mammoth._mixins._row_ops.RowOpsMixin.discard_duplicates` | `discard_duplicates(self, ignore_columns: list[str] \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_row_ops.py:101` |
| `mammoth._mixins._row_ops.RowOpsMixin.fill_missing` | `fill_missing(self, column: str, direction: FillDirection, partition_by: str \| None=None, order_by: list[list[str \| SortDirection]] \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_row_ops.py:24` |
| `mammoth._mixins._row_ops.RowOpsMixin.limit_rows` | `limit_rows(self, n: int, bottom: bool=False, order_by: list[list[str \| SortDirection]] \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_row_ops.py:72` |
| `mammoth._mixins._row_ops.RowOpsMixin.unnest` | `unnest(self, columns: list[str], label_column: str='Label', value_column: str='Value') -> dict[str, Any]` | `mammoth/_mixins/_row_ops.py:123` |
| `mammoth._mixins._text_ops.TextOpsMixin.bulk_replace` | `bulk_replace(self, columns: list[str], mapping: list[BulkReplaceMapping], match_case: bool=True, match_words: bool=False, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_text_ops.py:116` |
| `mammoth._mixins._text_ops.TextOpsMixin.replace_values` | `replace_values(self, columns: list[str], find: str, replace: str, match_case: bool=False, match_words: bool=False, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_text_ops.py:72` |
| `mammoth._mixins._text_ops.TextOpsMixin.split_column` | `split_column(self, column: str, delimiter: str, new_columns: list[SplitColumnSpec]) -> dict[str, Any]` | `mammoth/_mixins/_text_ops.py:163` |
| `mammoth._mixins._text_ops.TextOpsMixin.substring` | `substring(self, column: str, direction: SubstringDirection \| None=None, num_char: int \| None=None, char_position: int \| None=None, regex_pattern: str \| None=None, regex_invert: bool=False, new_column: str \| None=None, existing_column: str \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_text_ops.py:204` |
| `mammoth._mixins._text_ops.TextOpsMixin.text_transform` | `text_transform(self, columns: list[str], case: TextCase \| None=None, trim: bool=False, condition: Condition \| CompoundCondition \| NotCondition \| None=None) -> dict[str, Any]` | `mammoth/_mixins/_text_ops.py:31` |
| `mammoth.api.activity_logs.ActivityLogsAPI.export` | `export(self, format: str='csv', **filters: Any) -> dict[str, Any]` | `mammoth/api/activity_logs.py:51` |
| `mammoth.api.activity_logs.ActivityLogsAPI.list` | `list(self, limit: int=50, offset: int=0, sort: str \| None=None, **filters: Any) -> dict[str, Any]` | `mammoth/api/activity_logs.py:26` |
| `mammoth.api.addons.AddonsAPI.add_connector` | `add_connector(self, connector_id: int \| None=None, connector_ids: _list[int] \| None=None) -> dict[str, Any]` | `mammoth/api/addons.py:68` |
| `mammoth.api.addons.AddonsAPI.add_storage` | `add_storage(self, additional_storage_gb: int) -> dict[str, Any]` | `mammoth/api/addons.py:118` |
| `mammoth.api.addons.AddonsAPI.add_users` | `add_users(self, user_count: int=1) -> dict[str, Any]` | `mammoth/api/addons.py:166` |
| `mammoth.api.addons.AddonsAPI.list` | `list(self) -> dict[str, Any]` | `mammoth/api/addons.py:59` |
| `mammoth.api.addons.AddonsAPI.remove_connector` | `remove_connector(self, connector_id: int \| None=None, connector_ids: _list[int] \| None=None) -> dict[str, Any]` | `mammoth/api/addons.py:92` |
| `mammoth.api.addons.AddonsAPI.remove_storage` | `remove_storage(self, removal_storage_gb: int) -> dict[str, Any]` | `mammoth/api/addons.py:143` |
| `mammoth.api.addons.AddonsAPI.remove_users` | `remove_users(self, user_count: int) -> dict[str, Any]` | `mammoth/api/addons.py:185` |
| `mammoth.api.ai.AIAPI.generate_data` | `generate_data(self, dataview_id: int, prompt: str, no_of_rows: int=10, columns: list[str] \| None=None, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/ai.py:68` |
| `mammoth.api.ai.AIAPI.generate_profile` | `generate_profile(self, dataview_id: int, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/ai.py:45` |
| `mammoth.api.ai.AIAPI.generate_sql` | `generate_sql(self, intent: str, sequence_number: int=0) -> dict[str, Any]` | `mammoth/api/ai.py:134` |
| `mammoth.api.ai.AIAPI.get_data_gen_info` | `get_data_gen_info(self, dataview_id: int, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/ai.py:112` |
| `mammoth.api.ai.AIAPI.get_suggestions` | `get_suggestions(self) -> dict[str, Any]` | `mammoth/api/ai.py:159` |
| `mammoth.api.ai.AIAPI.query_gen` | `query_gen(self, connector_key: str, connection_key: str, prompt: str, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/ai.py:173` |
| `mammoth.api.automations.AutomationsAPI.create` | `create(self, name: str, description: str, tasks: _list[AutomationTaskSpec], conditions: _list[AutomationConditionSpec] \| None=None, condition_mode: AutomationConditionMode=AutomationConditionMode.AND) -> dict[str, Any]` | `mammoth/api/automations.py:314` |
| `mammoth.api.automations.AutomationsAPI.create_schedule` | `create_schedule(self, spec: ScheduleCreateSpec) -> dict[str, Any]` | `mammoth/api/automations.py:455` |
| `mammoth.api.automations.AutomationsAPI.delete` | `delete(self, automation_id: int) -> dict[str, Any]` | `mammoth/api/automations.py:428` |
| `mammoth.api.automations.AutomationsAPI.delete_schedule` | `delete_schedule(self, schedule_id: int) -> dict[str, Any]` | `mammoth/api/automations.py:513` |
| `mammoth.api.automations.AutomationsAPI.get` | `get(self, automation_id: int) -> dict[str, Any]` | `mammoth/api/automations.py:362` |
| `mammoth.api.automations.AutomationsAPI.list` | `list(self) -> _list[dict[str, Any]]` | `mammoth/api/automations.py:303` |
| `mammoth.api.automations.AutomationsAPI.list_schedules` | `list_schedules(self) -> _list[dict[str, Any]]` | `mammoth/api/automations.py:444` |
| `mammoth.api.automations.AutomationsAPI.update` | `update(self, automation_id: int, patch: _list[AutomationPatchItem]) -> dict[str, Any]` | `mammoth/api/automations.py:375` |
| `mammoth.api.automations.AutomationsAPI.update_schedule` | `update_schedule(self, schedule_id: int, patch: _list[SchedulePatchItem]) -> dict[str, Any]` | `mammoth/api/automations.py:474` |
| `mammoth.api.batches.BatchesAPI.create` | `create(self, dataset_id: int, source_id: int, mapping: dict[str, str], project_id: int \| None=None, new_ds_params: dict[str, Any] \| None=None, is_validation_required: bool \| None=None, change_map: dict[str, Any] \| None=None, delete_source_ds: bool=False) -> dict[str, Any]` | `mammoth/api/batches.py:101` |
| `mammoth.api.batches.BatchesAPI.delete` | `delete(self, dataset_id: int, batch_id: int, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/batches.py:201` |
| `mammoth.api.batches.BatchesAPI.get` | `get(self, dataset_id: int, batch_id: int, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/batches.py:78` |
| `mammoth.api.batches.BatchesAPI.list` | `list(self, dataset_id: int, project_id: int \| None=None, limit: int=50, offset: int=0) -> dict[str, Any]` | `mammoth/api/batches.py:47` |
| `mammoth.api.batches.BatchesAPI.update` | `update(self, dataset_id: int, patch: _list[dict[str, Any]], project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/batches.py:160` |
| `mammoth.api.browse.BrowseAPI.datasets` | `datasets(self, project_id: int \| None=None, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/browse.py:55` |
| `mammoth.api.browse.BrowseAPI.dataviews` | `dataviews(self, dataset_id: int, project_id: int \| None=None, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/browse.py:73` |
| `mammoth.api.browse.BrowseAPI.folder_resources` | `folder_resources(self, folder_id: int, project_id: int \| None=None, workspace_id: int \| None=None, level: int=2, fields: str='__min') -> dict[str, Any]` | `mammoth/api/browse.py:118` |
| `mammoth.api.browse.BrowseAPI.projects` | `projects(self, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/browse.py:43` |
| `mammoth.api.browse.BrowseAPI.workspace_resources` | `workspace_resources(self, workspace_id: int \| None=None, level: int=2, fields: str='__min', limit: int=100) -> dict[str, Any]` | `mammoth/api/browse.py:96` |
| `mammoth.api.browse.BrowseAPI.workspaces` | `workspaces(self) -> dict[str, Any]` | `mammoth/api/browse.py:35` |
| `mammoth.api.clientapps.ClientAppsAPI.create` | `create(self, app_name: str, description: str \| None=None, workspace_id: int \| None=None) -> ClientAppPostResponse` | `mammoth/api/clientapps.py:72` |
| `mammoth.api.clientapps.ClientAppsAPI.delete` | `delete(self, client_key: str, workspace_id: int \| None=None) -> None` | `mammoth/api/clientapps.py:142` |
| `mammoth.api.clientapps.ClientAppsAPI.get` | `get(self, client_key: str, workspace_id: int \| None=None, fields: str \| None=None) -> ClientAppSchema` | `mammoth/api/clientapps.py:95` |
| `mammoth.api.clientapps.ClientAppsAPI.list` | `list(self, workspace_id: int \| None=None, limit: int=10, offset: int=0, fields: str \| None=None, sort: str \| None=None) -> ClientAppsListResponse` | `mammoth/api/clientapps.py:35` |
| `mammoth.api.clientapps.ClientAppsAPI.update` | `update(self, client_key: str, patch_request: PatchRequest, workspace_id: int \| None=None) -> ClientAppSchema` | `mammoth/api/clientapps.py:120` |
| `mammoth.api.connectors.ConnectorsAPI.active_connectors` | `active_connectors(self) -> _list[dict[str, Any]]` | `mammoth/api/connectors.py:419` |
| `mammoth.api.connectors.ConnectorsAPI.create_connection` | `create_connection(self, connector_key: str, config: dict[str, Any], project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:114` |
| `mammoth.api.connectors.ConnectorsAPI.create_ds_config` | `create_ds_config(self, connector_key: str, connection_key: str, *, query: str \| None=None, file_source: str \| None=None, table: str \| None=None, profile: str \| None=None, validate: bool=True, data_sample: bool=False, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:256` |
| `mammoth.api.connectors.ConnectorsAPI.delete_connection` | `delete_connection(self, connector_key: str, connection_key: str, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:213` |
| `mammoth.api.connectors.ConnectorsAPI.delete_ds_config` | `delete_ds_config(self, connector_key: str, connection_key: str, ds_config_key: str, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:394` |
| `mammoth.api.connectors.ConnectorsAPI.get` | `get(self, connector_key: str) -> dict[str, Any]` | `mammoth/api/connectors.py:79` |
| `mammoth.api.connectors.ConnectorsAPI.get_connection` | `get_connection(self, connector_key: str, connection_key: str, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:156` |
| `mammoth.api.connectors.ConnectorsAPI.get_ds_config` | `get_ds_config(self, connector_key: str, connection_key: str, ds_config_key: str, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:318` |
| `mammoth.api.connectors.ConnectorsAPI.list` | `list(self) -> _list[dict[str, Any]]` | `mammoth/api/connectors.py:68` |
| `mammoth.api.connectors.ConnectorsAPI.list_connections` | `list_connections(self, connector_key: str, project_id: int \| None=None) -> _list[dict[str, Any]]` | `mammoth/api/connectors.py:92` |
| `mammoth.api.connectors.ConnectorsAPI.list_ds_configs` | `list_ds_configs(self, connector_key: str, connection_key: str, project_id: int \| None=None) -> _list[dict[str, Any]]` | `mammoth/api/connectors.py:233` |
| `mammoth.api.connectors.ConnectorsAPI.update_connection` | `update_connection(self, connector_key: str, connection_key: str, credentials: dict[str, Any], project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:176` |
| `mammoth.api.connectors.ConnectorsAPI.update_ds_config` | `update_ds_config(self, connector_key: str, connection_key: str, ds_config_key: str, patch: _list[DsConfigPatchOp], project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/connectors.py:343` |
| `mammoth.api.dashboards.DashboardsAPI.action` | `action(self, dashboard_id: int, action: DashboardActionType, params_enabled: bool \| None=None, params_view_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dashboards.py:243` |
| `mammoth.api.dashboards.DashboardsAPI.create` | `create(self, intent: str, source: _list[int], enable_filters: bool=True, enable_pages: bool=False) -> dict[str, Any]` | `mammoth/api/dashboards.py:70` |
| `mammoth.api.dashboards.DashboardsAPI.delete` | `delete(self, dashboard_id: int) -> dict[str, Any]` | `mammoth/api/dashboards.py:166` |
| `mammoth.api.dashboards.DashboardsAPI.get` | `get(self, dashboard_id: int) -> dict[str, Any]` | `mammoth/api/dashboards.py:114` |
| `mammoth.api.dashboards.DashboardsAPI.get_analytics` | `get_analytics(self, dashboard_id: int) -> dict[str, Any]` | `mammoth/api/dashboards.py:190` |
| `mammoth.api.dashboards.DashboardsAPI.get_by_url` | `get_by_url(self, url: str) -> dict[str, Any]` | `mammoth/api/dashboards.py:293` |
| `mammoth.api.dashboards.DashboardsAPI.get_draft_data` | `get_draft_data(self, dashboard_id: int, sql: str) -> dict[str, Any]` | `mammoth/api/dashboards.py:304` |
| `mammoth.api.dashboards.DashboardsAPI.get_publish_data` | `get_publish_data(self, dashboard_id: int, sql: str) -> dict[str, Any]` | `mammoth/api/dashboards.py:320` |
| `mammoth.api.dashboards.DashboardsAPI.get_sources` | `get_sources(self) -> _list[dict[str, Any]]` | `mammoth/api/dashboards.py:177` |
| `mammoth.api.dashboards.DashboardsAPI.list` | `list(self) -> _list[dict[str, Any]]` | `mammoth/api/dashboards.py:61` |
| `mammoth.api.dashboards.DashboardsAPI.share` | `share(self, dashboard_id: int, type_of_auth: DashboardAuthType, users: _list[DashboardShareUser] \| None=None) -> dict[str, Any]` | `mammoth/api/dashboards.py:201` |
| `mammoth.api.dashboards.DashboardsAPI.update` | `update(self, dashboard_id: int, patch: _list[DashboardPatchItem]) -> dict[str, Any]` | `mammoth/api/dashboards.py:125` |
| `mammoth.api.datasets.DatasetsAPI.bulk_delete` | `bulk_delete(self, workspace_id: int \| None=None, project_id: int \| None=None) -> None` | `mammoth/api/datasets.py:254` |
| `mammoth.api.datasets.DatasetsAPI.bulk_update` | `bulk_update(self, patch_data: dict[str, Any], workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:232` |
| `mammoth.api.datasets.DatasetsAPI.create` | `create(self, dataset_spec: dict[str, Any], ds_creation_type: str, folder_resource_id: str \| None=None, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:113` |
| `mammoth.api.datasets.DatasetsAPI.delete` | `delete(self, dataset_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> None` | `mammoth/api/datasets.py:213` |
| `mammoth.api.datasets.DatasetsAPI.get` | `get(self, dataset_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:63` |
| `mammoth.api.datasets.DatasetsAPI.get_batch` | `get_batch(self, dataset_id: int, batch_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:292` |
| `mammoth.api.datasets.DatasetsAPI.get_data` | `get_data(self, dataset_id: int, workspace_id: int \| None=None, project_id: int \| None=None, timeout: int=300, poll_interval: int=2) -> dict[str, Any]` | `mammoth/api/datasets.py:85` |
| `mammoth.api.datasets.DatasetsAPI.get_file_settings` | `get_file_settings(self, dataset_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:316` |
| `mammoth.api.datasets.DatasetsAPI.list` | `list(self, workspace_id: int \| None=None, project_id: int \| None=None, limit: int=100, sort: str='(created_at:desc)') -> dict[str, Any]` | `mammoth/api/datasets.py:38` |
| `mammoth.api.datasets.DatasetsAPI.list_batches` | `list_batches(self, dataset_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> _list[dict[str, Any]]` | `mammoth/api/datasets.py:269` |
| `mammoth.api.datasets.DatasetsAPI.rename` | `rename(self, dataset_id: int, name: str, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:186` |
| `mammoth.api.datasets.DatasetsAPI.update` | `update(self, patch_data: _list[dict[str, Any]], workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/datasets.py:147` |
| `mammoth.api.dataviews.DataviewsAPI.active_users` | `active_users(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:292` |
| `mammoth.api.dataviews.DataviewsAPI.bulk_delete` | `bulk_delete(self, dataset_id: int, dataview_ids: _list[int] \| str, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:186` |
| `mammoth.api.dataviews.DataviewsAPI.conditional_format_create` | `conditional_format_create(self, dataset_id: int, dataview_id: int, rule: dict[str, Any], workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:368` |
| `mammoth.api.dataviews.DataviewsAPI.conditional_format_delete` | `conditional_format_delete(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:424` |
| `mammoth.api.dataviews.DataviewsAPI.conditional_format_list` | `conditional_format_list(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> _list[dict[str, Any]]` | `mammoth/api/dataviews.py:342` |
| `mammoth.api.dataviews.DataviewsAPI.conditional_format_update` | `conditional_format_update(self, dataset_id: int, dataview_id: int, rule: dict[str, Any], workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:396` |
| `mammoth.api.dataviews.DataviewsAPI.create` | `create(self, dataset_id: int, name: str \| None='View', clone_config_from: int \| None=None, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:91` |
| `mammoth.api.dataviews.DataviewsAPI.delete` | `delete(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:161` |
| `mammoth.api.dataviews.DataviewsAPI.draft_mode` | `draft_mode(self, dataset_id: int, dataview_id: int, command: str, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:449` |
| `mammoth.api.dataviews.DataviewsAPI.get` | `get(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:67` |
| `mammoth.api.dataviews.DataviewsAPI.get_data` | `get_data(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None, timeout: int \| None=None, poll_interval: int=2) -> dict[str, Any]` | `mammoth/api/dataviews.py:216` |
| `mammoth.api.dataviews.DataviewsAPI.list` | `list(self, dataset_id: int, workspace_id: int \| None=None, project_id: int \| None=None, limit: int=100, sort: str='(created_at:desc)') -> dict[str, Any]` | `mammoth/api/dataviews.py:38` |
| `mammoth.api.dataviews.DataviewsAPI.mark_active` | `mark_active(self, dataset_id: int, dataview_id: int, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:317` |
| `mammoth.api.dataviews.DataviewsAPI.query_data` | `query_data(self, dataset_id: int, dataview_id: int, sequence: int=0, offset: int=1, limit: int=400, columns: _list[str] \| None=None, condition: dict[str, Any] \| None=None, sort: str \| None=None, workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:246` |
| `mammoth.api.dataviews.DataviewsAPI.update` | `update(self, dataset_id: int, dataview_id: int, patch_data: _list[dict[str, Any]], workspace_id: int \| None=None, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/dataviews.py:123` |
| `mammoth.api.exports.ExportsAPI.create` | `create(self, dataview_id: int, export_spec: AddExportSpec, dataset_id: int \| None=None, project_id: int \| None=None) -> PipelineExportsModificationResp \| JobResponse` | `mammoth/api/exports.py:116` |
| `mammoth.api.exports.ExportsAPI.list` | `list(self, dataview_id: int, fields: str \| None=None, limit: int=50, offset: int=0, sort: str \| None=None, sequence: int \| None=None, status: ExportStatus \| None=None, reordered: bool \| None=None, handler_type: HandlerType \| None=None, end_of_pipeline: bool \| None=None, runnable: bool \| None=None) -> PipelineExportsPaginated` | `mammoth/api/exports.py:48` |
| `mammoth.api.exports.ExportsAPI.to_csv` | `to_csv(self, dataview_id: int, output_path: str \| Path \| None=None, timeout: int=300, dataset_id: int \| None=None) -> Path` | `mammoth/api/exports.py:303` |
| `mammoth.api.exports.ExportsAPI.to_dataset` | `to_dataset(self, dataview_id: int, dataset_name: str, column_mapping: dict[str, Any] \| None=None, sequence: int \| None=None, trigger_id: int \| None=None, end_of_pipeline: bool=True, trigger_type: TriggerType=TriggerType.PIPELINE, condition: dict[str, Any] \| None=None, run_immediately: bool=True, validate_only: bool=False, additional_properties: dict[str, Any] \| None=None) -> PipelineExportsModificationResp \| JobResponse` | `mammoth/api/exports.py:245` |
| `mammoth.api.exports.ExportsAPI.to_s3` | `to_s3(self, dataview_id: int, file: str \| None=None, file_type: str='csv', include_hidden: bool=False, is_format_set: bool=True, use_format: bool=True, sequence: int \| None=None, trigger_id: int \| None=None, end_of_pipeline: bool=True, trigger_type: TriggerType=TriggerType.PIPELINE, condition: dict[str, Any] \| None=None, run_immediately: bool=True, validate_only: bool=False, additional_properties: dict[str, Any] \| None=None, dataset_id: int \| None=None) -> PipelineExportsModificationResp \| JobResponse \| dict[str, Any]` | `mammoth/api/exports.py:155` |
| `mammoth.api.external_keys.ExternalKeysAPI.create` | `create(self, key_type: ExternalKeyType, key_name: str, secure_key: str, description: str \| None=None, model_id: str \| None=None, model_settings: ModelConfigSpec \| None=None) -> dict[str, Any]` | `mammoth/api/external_keys.py:58` |
| `mammoth.api.external_keys.ExternalKeysAPI.delete` | `delete(self, key_id: int) -> dict[str, Any]` | `mammoth/api/external_keys.py:117` |
| `mammoth.api.external_keys.ExternalKeysAPI.get` | `get(self, key_id: int) -> dict[str, Any]` | `mammoth/api/external_keys.py:46` |
| `mammoth.api.external_keys.ExternalKeysAPI.list` | `list(self) -> dict[str, Any]` | `mammoth/api/external_keys.py:37` |
| `mammoth.api.files.FilesAPI.bulk_delete` | `bulk_delete(self, file_ids: _list[int]) -> None` | `mammoth/api/files.py:276` |
| `mammoth.api.files.FilesAPI.delete` | `delete(self, file_id: int) -> None` | `mammoth/api/files.py:266` |
| `mammoth.api.files.FilesAPI.extract_sheets` | `extract_sheets(self, file_id: int, sheets: _list[str], delete_file_after_extract: bool=True, combine_after_extract: bool=False) -> ObjectJobSchema` | `mammoth/api/files.py:329` |
| `mammoth.api.files.FilesAPI.get` | `get(self, file_id: int, fields: str \| None=None) -> FileSchema` | `mammoth/api/files.py:105` |
| `mammoth.api.files.FilesAPI.list` | `list(self, fields: str \| None=None, file_ids: _list[int] \| None=None, names: _list[str] \| None=None, statuses: _list[str] \| None=None, created_at: str \| None=None, updated_at: str \| None=None, limit: int=50, offset: int=0, sort: str \| None=None) -> FilesList` | `mammoth/api/files.py:50` |
| `mammoth.api.files.FilesAPI.set_password` | `set_password(self, file_id: int, password: str) -> ObjectJobSchema` | `mammoth/api/files.py:311` |
| `mammoth.api.files.FilesAPI.update` | `update(self, file_id: int, patch_request: FilePatchRequest) -> ObjectJobSchema` | `mammoth/api/files.py:289` |
| `mammoth.api.files.FilesAPI.upload` | `upload(self, files: _list[str \| Path \| BinaryIO] \| str \| Path \| BinaryIO \| None=None, folder_resource_id: str \| int \| None=None, append_to_ds_id: int \| None=None, override_target_schema: bool \| None=None, wait_for_completion: bool=True, timeout: int=300) -> _list[int] \| int \| None` | `mammoth/api/files.py:130` |
| `mammoth.api.files.FilesAPI.upload_folder` | `upload_folder(self, folder_path: str \| Path, folder_resource_id: str \| None=None, wait_for_completion: bool=True, timeout: int=300) -> _list[int] \| int \| None` | `mammoth/api/files.py:233` |
| `mammoth.api.folders.FoldersAPI.create` | `create(self, name: str, parent_resource_id: str \| None=None, workspace_id: int \| None=None, project_id: int \| None=None) -> FolderSchema` | `mammoth/api/folders.py:140` |
| `mammoth.api.folders.FoldersAPI.delete` | `delete(self, folder_ids: _list[int], workspace_id: int \| None=None, project_id: int \| None=None, check_dependency: bool=True, remove_contents: bool=True) -> None` | `mammoth/api/folders.py:168` |
| `mammoth.api.folders.FoldersAPI.get_project_root` | `get_project_root(self, workspace_id: int \| None=None, project_id: int \| None=None) -> FolderSchema` | `mammoth/api/folders.py:42` |
| `mammoth.api.folders.FoldersAPI.list` | `list(self, workspace_id: int \| None=None, project_id: int \| None=None, fields: str \| None=None, folder_ids: _list[int] \| None=None, names: _list[str] \| None=None, statuses: _list[str] \| None=None, created_at: str \| None=None, updated_at: str \| None=None, created_by: _list[str] \| None=None, limit: int=50, offset: int=0, sort: str \| None=None) -> FoldersList` | `mammoth/api/folders.py:76` |
| `mammoth.api.folders.FoldersAPI.move` | `move(self, resource_ids: _list[str], target_folder_resource_id: str \| None=None, source_folder_resource_id: str \| None=None, workspace_id: int \| None=None, project_id: int \| None=None) -> ObjectJobSchema` | `mammoth/api/folders.py:196` |
| `mammoth.api.jobs.JobsAPI.get_job` | `get_job(self, job_id: int, timeout: int=300) -> dict[str, Any]` | `mammoth/api/jobs.py:22` |
| `mammoth.api.jobs.JobsAPI.get_jobs` | `get_jobs(self, job_ids: list[int] \| str) -> dict[str, Any]` | `mammoth/api/jobs.py:43` |
| `mammoth.api.jobs.JobsAPI.wait_for_job` | `wait_for_job(self, job_id: int, timeout: int \| None=None, poll_interval: int=2) -> dict[str, Any]` | `mammoth/api/jobs.py:71` |
| `mammoth.api.jobs.JobsAPI.wait_for_jobs` | `wait_for_jobs(self, job_ids: list[int] \| str, timeout: int \| None=None, poll_interval: int=2) -> dict[str, Any]` | `mammoth/api/jobs.py:128` |
| `mammoth.api.pipeline.PipelineAPI.add_task` | `add_task(self, dataview_id: int, task_spec: dict[str, Any], dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:196` |
| `mammoth.api.pipeline.PipelineAPI.delete_task` | `delete_task(self, dataview_id: int, task_id: int, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:258` |
| `mammoth.api.pipeline.PipelineAPI.draft_mode` | `draft_mode(self, dataview_id: int, command: str, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:296` |
| `mammoth.api.pipeline.PipelineAPI.edit_pipeline` | `edit_pipeline(self, dataview_id: int, patches: _list[dict[str, Any]], dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:317` |
| `mammoth.api.pipeline.PipelineAPI.get_pipeline` | `get_pipeline(self, dataview_id: int, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:170` |
| `mammoth.api.pipeline.PipelineAPI.get_task` | `get_task(self, dataview_id: int, task_id: int, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:216` |
| `mammoth.api.pipeline.PipelineAPI.list_tasks` | `list_tasks(self, dataview_id: int, dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:183` |
| `mammoth.api.pipeline.PipelineAPI.preview_task` | `preview_task(self, dataview_id: int, task_spec: dict[str, Any], dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:277` |
| `mammoth.api.pipeline.PipelineAPI.update_task` | `update_task(self, dataview_id: int, task_id: int, task_spec: dict[str, Any], dataset_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/pipeline.py:234` |
| `mammoth.api.pipeline.PipelineAPI.wait_for_pipeline` | `wait_for_pipeline(self, dataview_id: int, dataset_id: int \| None=None, timeout: int \| None=None, poll_interval: int=3) -> dict[str, Any]` | `mammoth/api/pipeline.py:338` |
| `mammoth.api.projects.ProjectsAPI.add_users` | `add_users(self, project_id: int, user_ids: _list[str], role: str \| None=None, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:226` |
| `mammoth.api.projects.ProjectsAPI.browse` | `browse(self, project_id: int, workspace_id: int \| None=None, fields: str \| None=None, name: str \| None=None, browse_type: str \| None=None, sort: str \| None=None, offset: int \| None=None, limit: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:274` |
| `mammoth.api.projects.ProjectsAPI.bulk_delete` | `bulk_delete(self, project_ids: _list[int], workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:206` |
| `mammoth.api.projects.ProjectsAPI.bulk_update` | `bulk_update(self, patch_data: dict[str, Any], workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:189` |
| `mammoth.api.projects.ProjectsAPI.create` | `create(self, name: str, color: str \| None=None, project_access: str \| None=None, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:109` |
| `mammoth.api.projects.ProjectsAPI.delete` | `delete(self, project_id: int, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:170` |
| `mammoth.api.projects.ProjectsAPI.get` | `get(self, project: int \| str \| None=None, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:50` |
| `mammoth.api.projects.ProjectsAPI.list` | `list(self, workspace_id: int \| None=None, limit: int=100) -> dict[str, Any]` | `mammoth/api/projects.py:32` |
| `mammoth.api.projects.ProjectsAPI.remove_users` | `remove_users(self, project_id: int, user_ids: _list[str], workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:252` |
| `mammoth.api.projects.ProjectsAPI.update` | `update(self, project_id: int, name: str \| None=None, color: str \| None=None, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/projects.py:137` |
| `mammoth.api.reports.ReportsAPI.list` | `list(self, limit: int=50, offset: int=0) -> dict[str, Any]` | `mammoth/api/reports.py:22` |
| `mammoth.api.schedules.SchedulesAPI.create` | `create(self, spec: ScheduleCreateSpec, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/schedules.py:104` |
| `mammoth.api.schedules.SchedulesAPI.delete` | `delete(self, schedule_id: int, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/schedules.py:182` |
| `mammoth.api.schedules.SchedulesAPI.get` | `get(self, schedule_id: int, project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/schedules.py:88` |
| `mammoth.api.schedules.SchedulesAPI.list` | `list(self, project_id: int \| None=None, limit: int=50, offset: int=0) -> dict[str, Any]` | `mammoth/api/schedules.py:54` |
| `mammoth.api.schedules.SchedulesAPI.update` | `update(self, schedule_id: int, patch: _list[SchedulePatchItem], project_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/schedules.py:135` |
| `mammoth.api.user_profile.UserProfileAPI.change_password` | `change_password(self, current_password: str, new_password: str) -> dict[str, Any]` | `mammoth/api/user_profile.py:42` |
| `mammoth.api.user_profile.UserProfileAPI.get` | `get(self) -> dict[str, Any]` | `mammoth/api/user_profile.py:23` |
| `mammoth.api.user_profile.UserProfileAPI.get_preferences` | `get_preferences(self) -> dict[str, Any]` | `mammoth/api/user_profile.py:63` |
| `mammoth.api.user_profile.UserProfileAPI.update` | `update(self, **fields: Any) -> dict[str, Any]` | `mammoth/api/user_profile.py:31` |
| `mammoth.api.user_profile.UserProfileAPI.update_preferences` | `update_preferences(self, **prefs: Any) -> dict[str, Any]` | `mammoth/api/user_profile.py:71` |
| `mammoth.api.webhooks.WebhooksAPI.create` | `create(self, name: str='Generic Webhook', mode: str \| WebhookMode='replace', folder_resource_id: str \| None=None, origins: str='*', is_secure: bool=False) -> dict[str, Any]` | `mammoth/api/webhooks.py:64` |
| `mammoth.api.webhooks.WebhooksAPI.delete` | `delete(self, webhook_id: int) -> dict[str, Any]` | `mammoth/api/webhooks.py:145` |
| `mammoth.api.webhooks.WebhooksAPI.get` | `get(self, webhook_id: int) -> dict[str, Any]` | `mammoth/api/webhooks.py:99` |
| `mammoth.api.webhooks.WebhooksAPI.list` | `list(self, limit: int=50, offset: int=0) -> _list[dict[str, Any]]` | `mammoth/api/webhooks.py:42` |
| `mammoth.api.webhooks.WebhooksAPI.send_data` | `send_data(self, webhook_uri: str, data: dict[str, Any]) -> dict[str, Any]` | `mammoth/api/webhooks.py:159` |
| `mammoth.api.webhooks.WebhooksAPI.send_data_get` | `send_data_get(self, webhook_uri: str, params: dict[str, Any] \| None=None) -> dict[str, Any]` | `mammoth/api/webhooks.py:175` |
| `mammoth.api.webhooks.WebhooksAPI.update` | `update(self, webhook_id: int, mode: str \| WebhookMode \| None=None, origins: str \| None=None, is_secure: bool \| None=None) -> dict[str, Any]` | `mammoth/api/webhooks.py:113` |
| `mammoth.api.workspace.WorkspaceAPI.delete` | `delete(self, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/workspace.py:96` |
| `mammoth.api.workspace.WorkspaceAPI.get` | `get(self, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/workspace.py:49` |
| `mammoth.api.workspace.WorkspaceAPI.get_user` | `get_user(self, user_id: str, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/workspace.py:133` |
| `mammoth.api.workspace.WorkspaceAPI.list` | `list(self, limit: int=100) -> dict[str, Any]` | `mammoth/api/workspace.py:37` |
| `mammoth.api.workspace.WorkspaceAPI.list_users` | `list_users(self, workspace_id: int \| None=None) -> _list[dict[str, Any]]` | `mammoth/api/workspace.py:120` |
| `mammoth.api.workspace.WorkspaceAPI.reactivate` | `reactivate(self, workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/workspace.py:108` |
| `mammoth.api.workspace.WorkspaceAPI.update` | `update(self, patches: _list[WorkspacePatchOp], workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/workspace.py:61` |
| `mammoth.api.workspace.WorkspaceAPI.update_user` | `update_user(self, user_id: str, patches: _list[UserRolePatchOp], workspace_id: int \| None=None) -> dict[str, Any]` | `mammoth/api/workspace.py:151` |
| `mammoth.client.MammothClient.branch_out` | `branch_out(self, view_id: int, dataset_name: str, *, target_ds_id: int \| None=None, column_mapping: dict[str, str] \| None=None, **kwargs: Any) -> int` | `mammoth/client.py:542` |
| `mammoth.client.MammothClient.find_dataset_for_dataview` | `find_dataset_for_dataview(self, dataview_id: int) -> int` | `mammoth/client.py:278` |
| `mammoth.client.MammothClient.get_view` | `get_view(self, view_id: int) -> View` | `mammoth/client.py:522` |
| `mammoth.client.MammothClient.set_project_id` | `set_project_id(self, project_id: int) -> None` | `mammoth/client.py:478` |
| `mammoth.client.MammothClient.test_connection` | `test_connection(self) -> bool` | `mammoth/client.py:493` |
| `mammoth.client.ViewsResource.bulk_delete` | `bulk_delete(self, view_ids: _list[int]) -> dict[str, Any]` | `mammoth/client.py:171` |
| `mammoth.client.ViewsResource.create` | `create(self, dataset_id: int, name: str='View', clone_from: int \| None=None) -> View` | `mammoth/client.py:127` |
| `mammoth.client.ViewsResource.delete` | `delete(self, view_id: int) -> dict[str, Any]` | `mammoth/client.py:159` |
| `mammoth.client.ViewsResource.get` | `get(self, view_id: int) -> View` | `mammoth/client.py:91` |
| `mammoth.client.ViewsResource.list` | `list(self, dataset_id: int) -> _list[View]` | `mammoth/client.py:110` |
| `mammoth.view.View.branch_out` | `branch_out(self, dataset_name: str, *, target_ds_id: int \| None=None, save_as_mode: SaveAsDatasetMode=SaveAsDatasetMode.REPLACE, column_mapping: dict[str, str] \| None=None, label_ids: list[int] \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None, timeout: int \| None=None) -> int` | `mammoth/view.py:630` |
| `mammoth.view.View.data` | `data(self, limit: int=400, offset: int=1, columns: list[str] \| None=None, condition: Condition \| CompoundCondition \| None=None, sort: str \| None=None) -> dict[str, Any]` | `mammoth/view.py:370` |
| `mammoth.view.View.delete_task` | `delete_task(self, task_id: int) -> dict[str, Any]` | `mammoth/view.py:490` |
| `mammoth.view.View.discard_draft` | `discard_draft(self) -> dict[str, Any]` | `mammoth/view.py:567` |
| `mammoth.view.View.draft` | `draft(self) -> _DraftContext` | `mammoth/view.py:603` |
| `mammoth.view.View.enter_draft_mode` | `enter_draft_mode(self) -> dict[str, Any]` | `mammoth/view.py:535` |
| `mammoth.view.View.get_column_mapping` | `get_column_mapping(self) -> dict[str, str]` | `mammoth/view.py:616` |
| `mammoth.view.View.get_metadata` | `get_metadata(self) -> list[dict[str, Any]]` | `mammoth/view.py:448` |
| `mammoth.view.View.is_draft_mode` | `is_draft_mode(self) -> bool` | `mammoth/view.py:531` |
| `mammoth.view.View.list_tasks` | `list_tasks(self) -> list[dict[str, Any]]` | `mammoth/view.py:474` |
| `mammoth.view.View.preview_task` | `preview_task(self, task_spec: dict[str, Any]) -> dict[str, Any]` | `mammoth/view.py:512` |
| `mammoth.view.View.refresh` | `refresh(self) -> View` | `mammoth/view.py:413` |
| `mammoth.view.View.set_auto_run` | `set_auto_run(self, enabled: bool) -> dict[str, Any]` | `mammoth/view.py:582` |
| `mammoth.view.View.submit_draft` | `submit_draft(self) -> dict[str, Any]` | `mammoth/view.py:551` |
| `mammoth.view.ViewExport.delete` | `delete(self, export_id: int) -> dict[str, Any]` | `mammoth/view.py:1573` |
| `mammoth.view.ViewExport.list` | `list(self) -> _list[dict[str, Any]]` | `mammoth/view.py:1555` |
| `mammoth.view.ViewExport.publish_to_db` | `publish_to_db(self, table: str, odbc_type: OdbcType=OdbcType.POSTGRES) -> dict[str, Any]` | `mammoth/view.py:1523` |
| `mammoth.view.ViewExport.to_azure_blob` | `to_azure_blob(self, storage_account_name: str, tenant_id: str, client_id: str, client_secret: str, container_name: str, folder_path: str='', file_name: str='', **kwargs: Any) -> ExportResult` | `mammoth/view.py:1241` |
| `mammoth.view.ViewExport.to_bigquery` | `to_bigquery(self, selected_profile: dict[str, Any], selected_identity: dict[str, Any], table: str, export_type: BigQueryExportType=BigQueryExportType.REPLACE, upsert_keys: list[dict[str, Any]] \| None=None, partition: dict[str, Any] \| None=None, **kwargs: Any) -> ExportResult` | `mammoth/view.py:1143` |
| `mammoth.view.ViewExport.to_csv` | `to_csv(self, output_path: str \| None=None, timeout: int=300) -> Path` | `mammoth/view.py:887` |
| `mammoth.view.ViewExport.to_dataset` | `to_dataset(self, dataset_name: str, *, target_ds_id: int \| None=None, save_as_mode: SaveAsDatasetMode=SaveAsDatasetMode.REPLACE, column_mapping: dict[str, str] \| None=None, label_ids: list[int] \| None=None, condition: Condition \| CompoundCondition \| NotCondition \| None=None, timeout: int \| None=None) -> int` | `mammoth/view.py:844` |
| `mammoth.view.ViewExport.to_elasticsearch` | `to_elasticsearch(self, host: str, username: str, password: str, index: str, port: int=9243, connection: str='https', chunksize: int=200, **kwargs: Any) -> ExportResult` | `mammoth/view.py:1198` |
| `mammoth.view.ViewExport.to_email` | `to_email(self, emails: list[str], subject: str='', message: str='', resource: str='', **kwargs: Any) -> ExportResult` | `mammoth/view.py:1019` |
| `mammoth.view.ViewExport.to_ftp` | `to_ftp(self, domain: str, directory: str, file: str, username: str, password: str, port: int=21, **kwargs: Any) -> ExportResult` | `mammoth/view.py:910` |
| `mammoth.view.ViewExport.to_mssql` | `to_mssql(self, host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `mammoth/view.py:1060` |
| `mammoth.view.ViewExport.to_mysql` | `to_mysql(self, host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `mammoth/view.py:763` |
| `mammoth.view.ViewExport.to_onedrive` | `to_onedrive(self, tenant_id: str, client_id: str, client_secret: str, user_id: str, folder_path: str='', file_name: str='', **kwargs: Any) -> ExportResult` | `mammoth/view.py:1325` |
| `mammoth.view.ViewExport.to_postgres` | `to_postgres(self, host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `mammoth/view.py:714` |
| `mammoth.view.ViewExport.to_powerbi` | `to_powerbi(self, username: str, password: str, client_id: str, dataset: str, table: str, **kwargs: Any) -> ExportResult` | `mammoth/view.py:1408` |
| `mammoth.view.ViewExport.to_redshift` | `to_redshift(self, host: str, port: int, database: str, table: str, username: str, password: str, **kwargs: Any) -> ExportResult` | `mammoth/view.py:1100` |
| `mammoth.view.ViewExport.to_rest_api` | `to_rest_api(self, base_url: str, endpoint_path: str, auth_type: RestAuthType=RestAuthType.NONE, http_method: HttpMethod=HttpMethod.POST, wrap_path: str='records', batch_size: int=1000, timeout_seconds: int=30, ssl_verify: bool=True, auth: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, query_params: dict[str, str] \| None=None, extra_body_fields: dict[str, Any] \| None=None, **kwargs: Any) -> ExportResult` | `mammoth/view.py:1446` |
| `mammoth.view.ViewExport.to_s3` | `to_s3(self, file_name: str \| None=None, file_type: ExportFileType=ExportFileType.CSV, include_hidden: bool=False, **kwargs: Any) -> ExportResult` | `mammoth/view.py:803` |
| `mammoth.view.ViewExport.to_sftp` | `to_sftp(self, host: str, username: str, password: str='', directory: str='', file_name: str='', port: int=22, randomize_file_name: bool=False, ssh_key_authentication: bool=False, private_key: str='', passphrase: str='', **kwargs: Any) -> ExportResult` | `mammoth/view.py:957` |
| `mammoth.view.ViewExport.to_sharepoint` | `to_sharepoint(self, tenant_id: str, client_id: str, client_secret: str, site_url: str, document_library: str='Documents', folder_path: str='', file_name: str='', **kwargs: Any) -> ExportResult` | `mammoth/view.py:1283` |
| `mammoth.view.ViewExport.to_tableau` | `to_tableau(self, server_url: str, token_name: str, token_secret: str, site_name: str='', project_name: str='Default', datasource_name: str='mammoth_export', ca_bundle_path: str='', **kwargs: Any) -> ExportResult` | `mammoth/view.py:1364` |
