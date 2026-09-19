# `project` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `project.bulk-delete`

Run: `mammoth project bulk-delete`. Exact input fields: `mammoth schema get project.bulk-delete --output json --no-input`.

Example: `mammoth project bulk-delete --input '{"project_ids": [1]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ProjectBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Created throwaway project 22 (cli-write-sweep-throwaway-20260918), then bulk-deleted it. Without --yes: confirmation_required. With --yes: data:{}. Verified via project list: only project 3 (protected…

### `project.bulk-update`

Run: `mammoth project bulk-update`. Exact input fields: `mammoth schema get project.bulk-update --output json --no-input`.

Example: `mammoth project bulk-update --input '{"patch_data": {"patches": [{"op": "add", "path": "role", "value": [{"project_id": 456, "user_roles": [{"user_id": 123, "role": "project_analyst"}]}]}]}}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ProjectBulkUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: body accepted as ProjectsPatch naming project_id in every value item; confirmation named the workspace scope (message: 'bulk-update roles in projects 23 of workspace 4', hint 'Pass --con…

### `project.checkpoint.list`

Run: `mammoth project checkpoint list`. Exact input fields: `mammoth schema get project.checkpoint.list --output json --no-input`.

Example: `mammoth project checkpoint list 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectCheckpointListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Bounded release read in project 3 succeeded; empty checkpoint list observed. No Full claim: no non-empty fixture.

### `project.create`

Run: `mammoth project create`. Exact input fields: `mammoth schema get project.create --output json --no-input`.

Example: `mammoth project create 'Revenue report' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `project.data-check.list`

Run: `mammoth project data-check list`. Exact input fields: `mammoth schema get project.data-check.list --output json --no-input`.

Example: `mammoth project data-check list 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectDataCheckListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Bounded release read in project 3 succeeded; empty data-check list observed. No Full claim: no non-empty fixture.

### `project.delete`

Run: `mammoth project delete`. Exact input fields: `mammoth schema get project.delete --output json --no-input`.

Example: `mammoth project delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ProjectDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19 (CLI 2.0.18): owned project deleted with --yes --confirm PROJECT_ID after its datasets were deleted one by one; project list read back without it. Single invocation only.

### `project.get`

Run: `mammoth project get`. Exact input fields: `mammoth schema get project.get --output json --no-input`.

Example: `mammoth project get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `project.list`

Run: `mammoth project list`. Exact input fields: `mammoth schema get project.list --output json --no-input`.

Example: `mammoth project list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `project.pending-changes`

Run: `mammoth project pending-changes`. Exact input fields: `mammoth schema get project.pending-changes --output json --no-input`.

Example: `mammoth project pending-changes 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectPendingChangesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Bounded release read in project 3 succeeded; pending-items envelope was empty. No Full claim: no non-empty pending fixture.

### `project.publish-credentials`

Run: `mammoth project publish-credentials`. Exact input fields: `mammoth schema get project.publish-credentials --output json --no-input`.

Example: `mammoth project publish-credentials 123 --input '{"odbc_type": "postgres"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectPublishCredentialsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. First attempt (before any publish-db existed on project 21) -> HTTP 400 4PUBL002 PUBLISH_CREDENTIALS_NOT_FOUND, a clear/correct backend response given no dataview was published-to-db yet. After view.e…

### `project.resource-dependencies`

Run: `mammoth project resource-dependencies`. Exact input fields: `mammoth schema get project.resource-dependencies --output json --no-input`.

Example: `mammoth project resource-dependencies 123 --input '{"resource_ids": [456]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectResourceDependenciesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Returned data:{} (no dependencies found for view 68, which has no dependents). Prior capability note said resource_ids had no CLI flag; that appears fixed in 2.0.14 since…

### `project.resource-dependencies.update`

Run: `mammoth project resource-dependencies update`. Exact input fields: `mammoth schema get project.resource-dependencies.update --output json --no-input`.

Example: `mammoth project resource-dependencies update 123 --input '{"patches": [{"op": "replace", "path": "data_sync", "value": {"context_type": "dataview", "context_id": 1}}]}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ProjectResourceDependenciesUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Attempt 1 missing data_pass_through/run_pending_update -> HTTP 400 4GENR007 clear message: 'At least one of data_pass_through or run_pending_update is required'. Attempt 2 added data_pass_through:true…

### `project.resource-status`

Run: `mammoth project resource-status`. Exact input fields: `mammoth schema get project.resource-status --output json --no-input`.

Example: `mammoth project resource-status 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectResourceStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Bounded release read in project 3 succeeded; empty resource status observed. No Full claim: no non-empty resource fixture.

### `project.sample-flow`

Run: `mammoth project sample-flow`. Exact input fields: `mammoth schema get project.sample-flow --output json --no-input`.

Example: `mammoth project sample-flow 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectSampleFlowResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Attempt 1 with no input -> HTTP 400 4GENR007 extra=[{key:data,message:(quote)data(quote),source:body}] (CLI sends empty POST body; accepted_fields=[label_resource_id] optional so the CLI never sends a…

### `project.update`

Run: `mammoth project update`. Exact input fields: `mammoth schema get project.update --output json --no-input`.

Example: `mammoth project update 123 --input '{"name": "Renamed project"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ProjectUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: CLI sent the release ProjectPatch shape internally; command returned the full updated project object with unchanged name (no-op rename) and a fresh updated_at timestamp, confirming the P…

### `project.user.add`

Run: `mammoth project user add`. Exact input fields: `mammoth schema get project.user.add --output json --no-input`.

Example: `mammoth project user add 123 --input '{"user_ids": [123], "role": "project_analyst"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ProjectUserAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: {users:[{user_id,role}]} with numeric user id accepted. First attempt (immediately after we had inadvertently self-demoted via project.bulk-update) got HTTP 403 4PERM002 'User lacks perm…

### `project.user.remove`

Run: `mammoth project user remove`. Exact input fields: `mammoth schema get project.user.remove --output json --no-input`.

Example: `mammoth project user remove 123 --input '{"user_ids": ["resource-123"]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ProjectUserRemoveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `project.user.update`

Run: `mammoth project user update`. Exact input fields: `mammoth schema get project.user.update --output json --no-input`.

Example: `mammoth project user update 123 --input '{"role": "project_admin", "user_id": 123}' --output json --no-input --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ProjectUserUpdateResult`; mutation `high_impact`, confirmation `yes_always`, wait policy `not_async`.

Status on release: observed blocker — backend_error: HTTP 400 4PROJ010 ROLE_ALREADY_ASSIGNED: "Role already assigned to the user" -- targeted our own user (id 5, already project_admin as project owner). Re-check before relying on it.
