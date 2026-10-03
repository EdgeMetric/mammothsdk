# API Sub-Clients Reference

All sub-clients are accessible as attributes of `MammothClient`. Most methods accept optional `workspace_id` and `project_id` parameters that default to the client's configured values.

---

## ViewsResource (`client.views`)

Returns rich **View** objects (not raw dicts).

```python
view = await client.views.get(view_id)                           # View object
views = await client.views.list(dataset_id=123)                  # list of View objects
view = await client.views.create(dataset_id, name="My View")      # new View
await client.views.delete(view_id)                                # delete
await client.views.bulk_delete([view_id1, view_id2])              # bulk delete
```

`views.list()` requires the parent `dataset_id`. `views.get()`, `views.delete()`, and
`views.bulk_delete()` accept an optional `dataset_id`; when omitted, the SDK discovers
the parent through the pipeline API. `views.create()` always requires `dataset_id`.

### View metadata attributes

After any transformation, `view.display_names`, `view.columns`, and `view.column_types` are automatically refreshed and include pipeline-added columns:

```python
await view.math(expression="Price * 1.1", new_column="adj_price")
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
await view.refresh()
```

**Implementation note:** After a transformation the API populates `taskwise_info[last_seq]["metadata"]` with the complete post-pipeline column list. The SDK reads from there so new columns are always visible. For fresh views with no tasks yet, `taskwise_info` is null and the SDK falls back to the top-level `metadata` field.

---

## ProjectsAPI (`client.projects`)

Returns **raw dicts**, not rich objects. `list()` returns a response envelope — unwrap with `["projects"]`.

```python
resp = await client.projects.list()                               # {"projects": [...], "offset": 0, ...}
projects = resp["projects"]                                 # plain list of dicts (one page, max 100)
everything = await client.projects.list_all()                     # all pages; limit>100 is a backend error
for p in projects:
    print(p["id"], p["name"])                               # dict access, NOT p.id / p.name

project = await client.projects.get(10)                           # {"id": 10, "name": "..."}
project = await client.projects.create(name="My Project")         # raw dict response
await client.projects.update(project_id=10, name="New Name")
await client.projects.delete(project_id=10)
```

---

## DatasetsAPI (`client.datasets`)

```python
datasets = await client.datasets.list()                            # list all
dataset = await client.datasets.get(dataset_id=123)                # get one
await client.datasets.delete(dataset_id=123)                       # delete
batches = await client.datasets.list_batches(dataset_id=123)       # list data batches
hits = await client.datasets.search("New Year Sale")              # name, column or sampled value
```

---

## FilesAPI (`client.files`)

```python
# Upload a file (returns dataset_id)
ds_id = await client.files.upload("path/to/data.csv")

# Upload with folder
ds_id = await client.files.upload("data.csv", folder_resource_id="folder-abc-123")

# List files
files = await client.files.list()

# Delete
await client.files.delete(file_id=42)
```

---

## DataviewsAPI (`client.dataviews`)

Low-level dataview operations (prefer `client.views` for rich View objects).

```python
# List dataviews in a dataset
dataviews = await client.dataviews.list(dataset_id=123)

# Get dataview with full metadata
dv = await client.dataviews.get(dataset_id=123, dataview_id=456)

# Query data with filters
data = await client.dataviews.query_data(
    dataset_id=123, dataview_id=456,
    limit=100, offset=1,
    columns=["column_1", "column_2"],  # internal names
)

# Create a new dataview
dv = await client.dataviews.create(dataset_id=123, name="New View")

# Delete
await client.dataviews.delete(dataset_id=123, dataview_id=456)

# Draft mode (low-level — prefer view.draft() context manager)
await client.dataviews.draft_mode(dataset_id=123, dataview_id=456, command="enter")
```

---

## PipelineAPI (`client.pipeline`)

Low-level pipeline task management (prefer View transformation methods for high-level use).

```python
# List pipeline tasks
tasks = await client.pipeline.list_tasks(dataview_id=456, dataset_id=123)

# Add a task (raw spec)
result = await client.pipeline.add_task(
    dataview_id=456,
    task_spec={"DELETE": ["column_1"]},
    dataset_id=123,
)

# Get/update/delete specific task
task = await client.pipeline.get_task(dataview_id=456, task_id=789, dataset_id=123)
await client.pipeline.delete_task(dataview_id=456, task_id=789, dataset_id=123)

# Preview a task without applying
preview = await client.pipeline.preview_task(dataview_id=456, task_spec={...}, dataset_id=123)

# Draft mode (low-level — prefer view.draft() context manager)
await client.pipeline.draft_mode(dataview_id=456, command=DraftCommand.ENTER, dataset_id=123)
```

---

## JobsAPI (`client.jobs`)

Track async job status.

```python
# Get job status
job = await client.jobs.get_job(job_id=12345)

# Wait for job completion (returns when the job finishes)
result = await client.jobs.wait_for_job(job_id=12345)
result = await client.jobs.wait_for_job(job_id=12345, timeout=120)

# Track multiple jobs
results = await client.jobs.wait_for_jobs([12345, 12346])
```

Job statuses: `processing`, `success`, `failure`, `error`

---

## ExportsAPI (`client.exports`)

```python
# List exports for a dataview
exports = await client.exports.list(dataview_id=456)

# Create export
result = await client.exports.create(
    dataview_id=456,
    export_spec=spec,  # AddExportSpec model
    dataset_id=123,
)

# Download as CSV
path = await client.exports.to_csv(dataview_id=456, output_path="data.csv", dataset_id=123)
```

Prefer using `view.export.to_csv()`, `view.export.to_postgres()`, etc. on View objects.

---

## FoldersAPI (`client.folders`)

```python
folders = await client.folders.list()
folder = await client.folders.create(name="Reports")
await client.folders.delete(folder_ids=[5])
```

---

## ConnectorsAPI (`client.connectors`)

Third-party data connectors (databases, APIs, cloud services).

```python
connectors = await client.connectors.list()
connector = await client.connectors.get("postgres")
connections = await client.connectors.list_connections("postgres")
conn = await client.connectors.create_connection("postgres", config={...})
```

---

## DashboardsAPI (`client.dashboards`)

AI-powered dashboards.

```python
dashboards = await client.dashboards.list()
job = await client.dashboards.generate_v3({...})   # GenerateV3Params or dict; returns the build job id
blank = await client.dashboards.create_blank(params)  # CreateBlankParams; empty v3 dashboard bound to a dataview
data = await client.dashboards.get_publish_data(dashboard_id=1, widget_id="w1")  # optional global_filters, drilldown_filters
```

---

## WebhooksAPI (`client.webhooks`)

```python
webhooks = await client.webhooks.list()
webhook = await client.webhooks.create(name="My Webhook", mode="replace")
await client.webhooks.delete(webhook_id=1)
```

---

## AutomationsAPI (`client.automations`)

Scheduled tasks and orchestration.

```python
automations = await client.automations.list()
automation = await client.automations.create(
    name="Nightly refresh", description="", tasks=[AutomationTaskSpec(...)],
    conditions=[AutomationConditionSpec(...)],  # optional; condition_mode=AutomationConditionMode.AND by default
)
schedules = await client.automations.list_schedules()
```

---

## AIAPI (`client.ai`)

AI features.

```python
# Generate data profile
profile = await client.ai.generate_profile(dataview_id=456)

# Generate synthetic data
data = await client.ai.generate_data(dataview_id=456, prompt="customers", no_of_rows=100, columns=["Name", "Age"])

# Get AI suggestions for the current project
suggestions = await client.ai.get_suggestions()
```

---

## WorkspaceAPI (`client.workspaces`)

```python
workspaces = await client.workspaces.list()
workspace = await client.workspaces.get(workspace_id=11)
users = await client.workspaces.list_users()
```

---

## ClientAppsAPI (`client.client_apps`)

```python
apps = await client.client_apps.list()
app = await client.client_apps.create(app_name="My Integration")
```

---

## Convenience Methods on MammothClient

```python
# Quick access to View object
view = await client.get_view(view_id=1039)

# Branch out (export view to another dataset)
new_id = await client.branch_out(view_id=1039, dataset_name="Q1 snapshot")   # target_ds_id=42 writes into an existing dataset
```

`branch_out` returns the id of the dataset written to. `get_view()` and `branch_out()` do not accept `dataset_id` — it's auto-detected from the view.

---

## Other sub-clients

Every public method of the sub-clients not described above, by name. All are coroutines (`await client.<attr>.<method>(...)`); read the signature with `help(client.<attr>.<method>)` or the source in `mammoth/api/`. Most take optional `workspace_id`/`project_id` defaults from the client.

- `client.agents` (AgentsAPI): `chat`, `session_delete`, `session_list`, `session_messages`, `session_set_visibility`, `action_list`, `action_delete`, `run_status`, `run_list`, `run_pause`, `run_resume`, `run_stop`, `run_extend`, `run_units_set`, `turn_cancel`
- `client.annotations` (AnnotationsAPI): `list`, `create`, `delete`, `update`, `comment_add`
- `client.billing` (BillingAPI): `chargebee_plan`, `hosted_page`, `stripe_checkout_url`, `stripe_portal_url`, `stripe_get`, `stripe_create`, `stripe_cancel`, `stripe_end_trial`, `stripe_retry_payment`, `stripe_sync`, `stripe_status`, `stripe_history`, `stripe_usage`, `stripe_preview_invoice`, `stripe_upcoming_invoice`, `stripe_resume`, `stripe_recheck_limits`, `stripe_storage_update`, `stripe_payment_method_list`, `stripe_payment_method_set_default`, `stripe_payment_method_delete`, `invoice_list`, `invoice_charge`, `subscription_get`, `subscription_update`
- `client.checkpoints` (CheckpointsAPI): `list`, `get`, `create`, `update`, `delete`
- `client.connector_ai` (ConnectorAIAPI): `chat`, `history`, `session_list`, `session_messages`, `submit_column_selection`, `submit_credentials`
- `client.data_apps` (DataAppsAPI): `list`, `get`, `create`, `update`, `delete`, `active_job`, `job`, `pipeline_changes`, `share`, `upload`, `user_list`, `user_remove`
- `client.data_checks` (DataChecksAPI): `list`, `get`, `create`, `update`, `delete`
- `client.derivatives` (DerivativesAPI): `list`, `create`, `data`, `update`, `delete`
- `client.notifications` (NotificationsAPI): `list`, `delete`, `delete_batch`, `update`, `update_batch`
- `client.parameters` (ParametersAPI): `list`, `create`, `get`, `update`, `delete`, `dependencies`, `duplicate`, `rerun`, `rerun_all_stale`, `group_list`, `group_create`, `group_update`, `group_delete`, `group_reorder`
- `client.pipeline_versions` (PipelineVersionsAPI): `list`, `get`, `apply`, `update`, `delete`
- `client.snippets` (SnippetsAPI): `list`, `create`, `get`, `update`, `delete`, `dependencies`, `duplicate`, `rerun`
- `client.support` (SupportAPI): `plan_list`, `plan_self_serve_list`, `plan_chargebee_list`, `plan_get`, `plan_create`, `plan_update`, `plan_update_storage_tiers`, `plan_delete`, `plan_archive`, `plan_unarchive`, `plan_storage_option_list`, `plan_storage_option_create`, `plan_storage_option_update`, `plan_storage_option_archive`, `feature_list`, `feature_create`, `feature_update`, `feature_delete`, `feature_profile_list`, `feature_profile_create`, `feature_profile_update`, `feature_profile_delete`, `feature_profile_add_feature`, `connector_list`, `connector_create`, `connector_update`, `connector_delete`, `connector_profile_list`, `connector_profile_create`, `connector_profile_update`, `connector_profile_delete`, `connector_profile_add_connector`, `subscription_get`, `subscription_create`, `subscription_update`, `user_register`, `user_update`, `user_list_all`, `ownership_transfer`, `workspace_list`, `workspace_get`, `workspace_create`, `workspace_update`, `workspace_delete`, `workspace_suspend_access`, `workspace_restore_access`, `workspace_user_list`, `workspace_user_add`, `workspace_user_remove`, `workspace_user_transfer`, `template_list`, `template_edit`, `template_data_preview`, `template_canvas`, `template_publish`, `template_unpublish`, `template_retire`, `template_inspect`, `template_import`, `template_thumbnail_set`, `template_thumbnail_clear`, `template_discard`, `template_snapshots`, `template_audit`, `template_export`, `template_export_dashboard`
- `client.templates` (TemplatesAPI): `list`, `get`, `create`, `update`, `delete`
- `client.trash` (TrashAPI): `list`, `add`, `restore`
- `client.users` (UsersAPI): `avatar_delete`, `avatar_upload`, `delete_account`
- `client.workflows` (WorkflowsAPI): `list`, `create`, `get`, `update`, `delete`, `graph`, `cleanup`, `from_template`, `workspace_datasets`, `workspace_exports`, `workspace_sources`, `block_add`, `block_auth`, `block_type`, `block_config`, `canvas`
- `client.workspace` (WorkspacesAPI): `accept_invite`, `create`, `check_expression`, `llm_task`, `app_usage`, `home_summary`, `storage_breakdown`, `segment_list`, `segment_update`, `user_add`, `user_remove`, `user_remove_batch`, `user_update_batch`, `invite_list`, `invite_resend`, `invite_revoke`, `invite_role_update`, `invite_delete`

### Further methods on the documented sub-clients

Methods added since the sections above were written (same convention):

- `client.files`: `upload_folder`, `set_password`, `extract_sheets`
- `client.jobs`: `get_jobs`
- `client.exports`: `publish_db`, `publish_db_update`, `to_s3`, `to_dataset`, `to_csv_url`
- `client.workspaces`: `reactivate`, `get_user`, `update_user`
- `client.projects`: `bulk_update`, `add_users`, `remove_users`, `browse`, `checkpoint_list`, `data_check_list`, `pending_changes`, `needs_attention`, `list_agent_memory`, `add_agent_memory`, `remove_agent_memory`, `publish_credentials`, `resource_dependencies`, `resource_dependencies_update`, `resource_status`, `sample_flow`, `user_update`
- `client.folders`: `get_project_root`, `move`, `trash`
- `client.datasets`: `get_data`, `rename`, `delete_and_verify`, `bulk_update`, `preview_interpretation`, `confirm_interpretation`, `get_unstructured_rows`, `resolve_unstructured_rows`, `get_batch`, `get_batch_data`, `get_file_settings`, `create_from_pdf`, `file_settings_update`, `file_settings_undo`, `interpretation_preview`, `interpretation_confirm`, `restore`, `trash`
- `client.dataviews`: `delete_impact`, `get_data`, `aggregate`, `explore`, `get_exportable_config`, `apply_exportable_config`, `active_users`, `mark_active`, `conditional_format_list`, `conditional_format_create`, `conditional_format_update`, `conditional_format_delete`, `parameter_context`, `restore`, `trash`
- `client.pipeline`: `find_dataset_for_dataview`, `get_pipeline`, `update_task`, `get_draft_status`, `reconcile_draft_submission`, `edit_pipeline`, `wait_for_pipeline`, `items`, `items_all`, `latest_task_sequence`, `rerun`
- `client.connectors`: `get_connection`, `update_connection`, `delete_connection`, `list_ds_configs`, `create_ds_config`, `get_ds_config`, `update_ds_config`, `delete_ds_config`, `ds_config_delete_all`, `active_connectors`
- `client.dashboards`: `list_tags`, `rename_tag`, `set_tags`, `delete_tag`, `merge_tag`, `create_blank`, `generate_v3`, `add_pages`, `extract_context`, `extract_exemplar`, `swap_data`, `take_pending_template`, `use_template`, `assess_twb`, `assess_pbix`, `import_workbook`, `powerbi_preflight`, `tableau_preflight`, `powerbi_export_artifact`, `tableau_export_artifact`, `export_powerbi`, `export_tableau`, `archive`, `get_sources`, `get_analytics`, `share`, `action`, `get_by_url`, `get_draft_data`, `cancel_generation`, `job_by_url`, `wait_for_job_by_url`, `published_data_by_url`, `restore`, `trash`, `widget_data`, `widget_data_by_url`, `embed_config_get`, `embed_config_set`, `embed_key_rotate`, `embed_usage_get`, `embed_usage_summary`, `format_preview`, `swap_fit`, `audience`, `audience_digest_get`, `audience_digest_set`, `audience_summary`, `column_roster`, `context_review`, `context_apply`, `qa_insights`, `template_thumbnail_get`, `template_thumbnail_set`, `template_thumbnail_clear`, `gallery_list`, `gallery_get`, `embed_origin_revoke`, `embed_preview_token_create`, `embed_secret_rotate`, `embed_lifetime_set`, `analytics`, `source_list`, `data_draft`, `data_published`, `rls_column_list`, `rls_value_list`, `rls_assignment_list`, `rls_assignment_set`, `query`, `template_apply`, `chat_history`, `chat_edit`, `suggestion_list`, `descriptor_data`, `published_data`, `duplicate`, `pdf_export`, `published_pdf_export`, `video_export`, `published_video_export`, `figure_intent`, `v3_generate`, `canvas_get`, `canvas_save`, `published_canvas`, `pdf_artifact`, `published_pdf_artifact`, `video_state`, `og_card`, `published_og_card`, `page_plan`, `template_preview`, `template_resolve_mapping`, `canvas_restore`, `published_share_page`, `published_video_artifact`, `qa_comment_create`, `qa_ask`, `qa_session_list`, `qa_session_create`, `qa_comment_delete`, `qa_session_get`, `qa_session_delete`, `qa_session_fork`, `qa_settings_get`, `qa_settings_set`, `qa_session_rename`, `qa_feedback`, `qa_session_set_visibility`, `context_list`, `context_create`, `style_custom_list`, `style_custom_create`, `signature_list`, `signature_create`, `context_update`, `context_delete`, `style_custom_update`, `style_custom_delete`, `signature_update`, `signature_delete`, `template_get`, `template_delete`, `template_rename`, `style_derive`, `style_extract_brand`, `template_fit`, `style_default_get`, `style_default_set`, `style_token_list`, `style_preset_list`, `template_list`, `template_create`
- `client.webhooks`: `send_data`, `send_data_get`
- `client.automations`: `capabilities`, `restore`, `trash`, `create_schedule`, `update_schedule`, `delete_schedule`
- `client.ai`: `get_data_gen_info`, `generate_sql`, `query_gen`, `condition_generate`, `expression_generate`, `retention_condition`
- `client.batches`: `create_spec`
- `client.browse`: `root`, `workspace_resources`, `folder_resources`, `resources_list`, `resource_get`, `resource_ancestors`, `resources_search`, `resources_bulk`
- `client.user_profile`: `change_password`, `get_preferences`, `update_preferences`
- `client.addons`: `add_connector`, `remove_connector`, `add_storage`, `remove_storage`, `add_users`, `remove_users`
