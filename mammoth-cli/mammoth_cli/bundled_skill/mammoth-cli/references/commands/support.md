# `support` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `support.connector-profile.add-connector`

Run: `mammoth support connector-profile add-connector`. Exact input fields: `mammoth schema get support.connector-profile.add-connector --output json --no-input`.

Example: `mammoth support connector-profile add-connector 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileAddConnectorResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.create`

Run: `mammoth support connector-profile create`. Exact input fields: `mammoth schema get support.connector-profile.create --output json --no-input`.

Example: `mammoth support connector-profile create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.delete`

Run: `mammoth support connector-profile delete`. Exact input fields: `mammoth schema get support.connector-profile.delete --output json --no-input`.

Example: `mammoth support connector-profile delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.list`

Run: `mammoth support connector-profile list`. Exact input fields: `mammoth schema get support.connector-profile.list --output json --no-input`.

Example: `mammoth support connector-profile list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.connector_profiles Single invocation only.

### `support.connector-profile.update`

Run: `mammoth support connector-profile update`. Exact input fields: `mammoth schema get support.connector-profile.update --output json --no-input`.

Example: `mammoth support connector-profile update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.create`

Run: `mammoth support connector create`. Exact input fields: `mammoth schema get support.connector.create --output json --no-input`.

Example: `mammoth support connector create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.delete`

Run: `mammoth support connector delete`. Exact input fields: `mammoth schema get support.connector.delete --output json --no-input`.

Example: `mammoth support connector delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.list`

Run: `mammoth support connector list`. Exact input fields: `mammoth schema get support.connector.list --output json --no-input`.

Example: `mammoth support connector list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.connectors Single invocation only.

### `support.connector.update`

Run: `mammoth support connector update`. Exact input fields: `mammoth schema get support.connector.update --output json --no-input`.

Example: `mammoth support connector update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.add-feature`

Run: `mammoth support feature-profile add-feature`. Exact input fields: `mammoth schema get support.feature-profile.add-feature --output json --no-input`.

Example: `mammoth support feature-profile add-feature 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileAddFeatureResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.create`

Run: `mammoth support feature-profile create`. Exact input fields: `mammoth schema get support.feature-profile.create --output json --no-input`.

Example: `mammoth support feature-profile create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.delete`

Run: `mammoth support feature-profile delete`. Exact input fields: `mammoth schema get support.feature-profile.delete --output json --no-input`.

Example: `mammoth support feature-profile delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.list`

Run: `mammoth support feature-profile list`. Exact input fields: `mammoth schema get support.feature-profile.list --output json --no-input`.

Example: `mammoth support feature-profile list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.feature_profiles Single invocation only.

### `support.feature-profile.update`

Run: `mammoth support feature-profile update`. Exact input fields: `mammoth schema get support.feature-profile.update --output json --no-input`.

Example: `mammoth support feature-profile update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature.create`

Run: `mammoth support feature create`. Exact input fields: `mammoth schema get support.feature.create --output json --no-input`.

Example: `mammoth support feature create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature.delete`

Run: `mammoth support feature delete`. Exact input fields: `mammoth schema get support.feature.delete --output json --no-input`.

Example: `mammoth support feature delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature.list`

Run: `mammoth support feature list`. Exact input fields: `mammoth schema get support.feature.list --output json --no-input`.

Example: `mammoth support feature list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.features Single invocation only.

### `support.feature.update`

Run: `mammoth support feature update`. Exact input fields: `mammoth schema get support.feature.update --output json --no-input`.

Example: `mammoth support feature update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.ownership.transfer`

Run: `mammoth support ownership transfer`. Exact input fields: `mammoth schema get support.ownership.transfer --output json --no-input`.

Example: `mammoth support ownership transfer 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportOwnershipTransferResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.archive`

Run: `mammoth support plan archive`. Exact input fields: `mammoth schema get support.plan.archive --output json --no-input`.

Example: `mammoth support plan archive 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanArchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.chargebee-list`

Run: `mammoth support plan chargebee-list`. Exact input fields: `mammoth schema get support.plan.chargebee-list --output json --no-input`.

Example: `mammoth support plan chargebee-list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanChargebeeListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.available_plans Single invocation only.

### `support.plan.create`

Run: `mammoth support plan create`. Exact input fields: `mammoth schema get support.plan.create --output json --no-input`.

Example: `mammoth support plan create 'Revenue report' --input '{"monthly_price": 1.0, "is_self_serve": true}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.delete`

Run: `mammoth support plan delete`. Exact input fields: `mammoth schema get support.plan.delete --output json --no-input`.

Example: `mammoth support plan delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.get`

Run: `mammoth support plan get`. Exact input fields: `mammoth schema get support.plan.get --output json --no-input`.

Example: `mammoth support plan get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanGetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.list`

Run: `mammoth support plan list`. Exact input fields: `mammoth schema get support.plan.list --output json --no-input`.

Example: `mammoth support plan list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.plans (5 plans, ids 4-8) Single invocation only.

### `support.plan.self-serve-list`

Run: `mammoth support plan self-serve-list`. Exact input fields: `mammoth schema get support.plan.self-serve-list --output json --no-input`.

Example: `mammoth support plan self-serve-list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanSelfServeListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.plans Single invocation only.

### `support.plan.update`

Run: `mammoth support plan update`. Exact input fields: `mammoth schema get support.plan.update --output json --no-input`.

Example: `mammoth support plan update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.update-storage-tiers`

Run: `mammoth support plan update-storage-tiers`. Exact input fields: `mammoth schema get support.plan.update-storage-tiers --output json --no-input`.

Example: `mammoth support plan update-storage-tiers 123 --input '{"storage_tiers": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanUpdateStorageTiersResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.subscription.create`

Run: `mammoth support subscription create`. Exact input fields: `mammoth schema get support.subscription.create --output json --no-input`.

Example: `mammoth support subscription create 123 resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportSubscriptionCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.subscription.get`

Run: `mammoth support subscription get`. Exact input fields: `mammoth schema get support.subscription.get --output json --no-input`.

Example: `mammoth support subscription get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportSubscriptionGetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.subscription.update`

Run: `mammoth support subscription update`. Exact input fields: `mammoth schema get support.subscription.update --output json --no-input`.

Example: `mammoth support subscription update 123 resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportSubscriptionUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.user.list-all`

Run: `mammoth support user list-all`. Exact input fields: `mammoth schema get support.user.list-all --output json --no-input`.

Example: `mammoth support user list-all --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportUserListAllResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data keyed by workspace id ('4') listing users Single invocation only.

### `support.user.register`

Run: `mammoth support user register`. Exact input fields: `mammoth schema get support.user.register --output json --no-input`.

Example: `mammoth support user register analyst@example.com --input '{"first_name": "Revenue report", "last_name": "Revenue report", "verified": true}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportUserRegisterResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.user.update`

Run: `mammoth support user update`. Exact input fields: `mammoth schema get support.user.update --output json --no-input`.

Example: `mammoth support user update analyst@example.com --input '{"verified": true}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportUserUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.create`

Run: `mammoth support workspace create`. Exact input fields: `mammoth schema get support.workspace.create --output json --no-input`.

Example: `mammoth support workspace create 'Revenue report' --input '{"user_email": "analyst@example.com", "payment_frequency": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.delete`

Run: `mammoth support workspace delete`. Exact input fields: `mammoth schema get support.workspace.delete --output json --no-input`.

Example: `mammoth support workspace delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.get`

Run: `mammoth support workspace get`. Exact input fields: `mammoth schema get support.workspace.get --output json --no-input`.

Example: `mammoth support workspace get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceGetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.list`

Run: `mammoth support workspace list`. Exact input fields: `mammoth schema get support.workspace.list --output json --no-input`.

Example: `mammoth support workspace list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; route returns a bare array so the SDK wraps it as {status_code:200, response:[...]}…

### `support.workspace.restore-access`

Run: `mammoth support workspace restore-access`. Exact input fields: `mammoth schema get support.workspace.restore-access --output json --no-input`.

Example: `mammoth support workspace restore-access 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceRestoreAccessResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.suspend-access`

Run: `mammoth support workspace suspend-access`. Exact input fields: `mammoth schema get support.workspace.suspend-access --output json --no-input`.

Example: `mammoth support workspace suspend-access 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceSuspendAccessResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.update`

Run: `mammoth support workspace update`. Exact input fields: `mammoth schema get support.workspace.update --output json --no-input`.

Example: `mammoth support workspace update 123 --input '{"name": "Revenue report", "payment_frequency": "sample", "plan_id": 1}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.add`

Run: `mammoth support workspace user add`. Exact input fields: `mammoth schema get support.workspace.user.add --output json --no-input`.

Example: `mammoth support workspace user add 123 --input '{"email": "analyst@example.com", "role": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.list`

Run: `mammoth support workspace user list`. Exact input fields: `mammoth schema get support.workspace.user.list --output json --no-input`.

Example: `mammoth support workspace user list 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.remove`

Run: `mammoth support workspace user remove`. Exact input fields: `mammoth schema get support.workspace.user.remove --output json --no-input`.

Example: `mammoth support workspace user remove 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserRemoveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.transfer`

Run: `mammoth support workspace user transfer`. Exact input fields: `mammoth schema get support.workspace.user.transfer --output json --no-input`.

Example: `mammoth support workspace user transfer 123 123 --input '{"role": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserTransferResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.
