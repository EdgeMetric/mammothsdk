# `workspace` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `workspace.accept-invite`

Run: `mammoth workspace accept-invite`. Exact input fields: `mammoth schema get workspace.accept-invite --output json --no-input`.

Example: `mammoth workspace accept-invite --input /private/path/request.json --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `WorkspaceAcceptInviteResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.app-usage`

Run: `mammoth workspace app-usage`. Exact input fields: `mammoth schema get workspace.app-usage --output json --no-input`.

Example: `mammoth workspace app-usage --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceAppUsageResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: workspace. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workspace.check-expression`

Run: `mammoth workspace check-expression`. Exact input fields: `mammoth schema get workspace.check-expression --output json --no-input`.

Example: `mammoth workspace check-expression --input '{"body": {"intent": "Summarize revenue by region"}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceCheckExpressionResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.create`

Run: `mammoth workspace create`. Exact input fields: `mammoth schema get workspace.create --output json --no-input`.

Example: `mammoth workspace create --input '{"body": {}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.delete`

Run: `mammoth workspace delete`. Exact input fields: `mammoth schema get workspace.delete --output json --no-input`.

Example: `mammoth workspace delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `WorkspaceDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.get`

Run: `mammoth workspace get`. Exact input fields: `mammoth schema get workspace.get --output json --no-input`.

Example: `mammoth workspace get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Returned workspace 4 (API Tests) profile. Single invocation only.

### `workspace.list`

Run: `mammoth workspace list`. Exact input fields: `mammoth schema get workspace.list --output json --no-input`.

Example: `mammoth workspace list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: limit, next, offset, workspaces. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workspace.llm-task`

Run: `mammoth workspace llm-task`. Exact input fields: `mammoth schema get workspace.llm-task --output json --no-input`.

Example: `mammoth workspace llm-task --input '{"task_type": "sample", "params": {"sample_key": "Status"}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceLlmTaskResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.reactivate`

Run: `mammoth workspace reactivate`. Exact input fields: `mammoth schema get workspace.reactivate --output json --no-input`.

Example: `mammoth workspace reactivate 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `WorkspaceReactivateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.segment.list`

Run: `mammoth workspace segment list`. Exact input fields: `mammoth schema get workspace.segment.list --output json --no-input`.

Example: `mammoth workspace segment list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceSegmentListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.10 — Bounded release read with published CLI 1.1.10 succeeded for workspace segments; segments collection returned. No Full claim: no non-empty segment fixture or option/error matrix.

### `workspace.segment.update`

Run: `mammoth workspace segment update`. Exact input fields: `mammoth schema get workspace.segment.update --output json --no-input`.

Example: `mammoth workspace segment update --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceSegmentUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: 200 non-object body reported as success on both op:add and the immediate op:remove for the same segment name: {"data":{"response":null,"status_code":200}} (both calls). `workspace segmen…

### `workspace.storage-breakdown`

Run: `mammoth workspace storage-breakdown`. Exact input fields: `mammoth schema get workspace.storage-breakdown --output json --no-input`.

Example: `mammoth workspace storage-breakdown --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceStorageBreakdownResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: items, limit, next, offset, total_count. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workspace.update`

Run: `mammoth workspace update`. Exact input fields: `mammoth schema get workspace.update --output json --no-input`.

Example: `mammoth workspace update 123 --input '{"patches": [{"op": "replace", "path": "name", "value": "sample"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `WorkspaceUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.user.add`

Run: `mammoth workspace user add`. Exact input fields: `mammoth schema get workspace.user.add --output json --no-input`.

Example: `mammoth workspace user add --input '{"email_ids": ["analyst@example.com"]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceUserAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.user.get`

Run: `mammoth workspace user get`. Exact input fields: `mammoth schema get workspace.user.get --output json --no-input`.

Example: `mammoth workspace user get resource-123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceUserGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.user.list`

Run: `mammoth workspace user list`. Exact input fields: `mammoth schema get workspace.user.list --output json --no-input`.

Example: `mammoth workspace user list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceUserListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 5, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workspace.user.remove`

Run: `mammoth workspace user remove`. Exact input fields: `mammoth schema get workspace.user.remove --output json --no-input`.

Example: `mammoth workspace user remove 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkspaceUserRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.user.remove-batch`

Run: `mammoth workspace user remove-batch`. Exact input fields: `mammoth schema get workspace.user.remove-batch --output json --no-input`.

Example: `mammoth workspace user remove-batch --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkspaceUserRemoveBatchResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.user.update`

Run: `mammoth workspace user update`. Exact input fields: `mammoth schema get workspace.user.update --output json --no-input`.

Example: `mammoth workspace user update resource-123 --input '{"patches": [{"op": "replace", "path": "role", "value": "workspace_member"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `WorkspaceUserUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workspace.user.update-batch`

Run: `mammoth workspace user update-batch`. Exact input fields: `mammoth schema get workspace.user.update-batch --output json --no-input`.

Example: `mammoth workspace user update-batch --input '{"patches": [{"sample_key": "Status"}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkspaceUserUpdateBatchResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
