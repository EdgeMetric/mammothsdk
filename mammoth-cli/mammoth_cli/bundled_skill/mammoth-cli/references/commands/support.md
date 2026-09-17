# `support` commands

### `support.connector-profile.add-connector`

Run: `mammoth support connector-profile add-connector`. Exact input fields: `mammoth schema get support.connector-profile.add-connector --output json --no-input`.

Example: `mammoth support connector-profile add-connector 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorProfileAddConnectorResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector-profile.create`

Run: `mammoth support connector-profile create`. Exact input fields: `mammoth schema get support.connector-profile.create --output json --no-input`.

Example: `mammoth support connector-profile create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorProfileCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector-profile.delete`

Run: `mammoth support connector-profile delete`. Exact input fields: `mammoth schema get support.connector-profile.delete --output json --no-input`.

Example: `mammoth support connector-profile delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorProfileDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector-profile.list`

Run: `mammoth support connector-profile list`. Exact input fields: `mammoth schema get support.connector-profile.list --output json --no-input`.

Example: `mammoth support connector-profile list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorProfileListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector-profile.update`

Run: `mammoth support connector-profile update`. Exact input fields: `mammoth schema get support.connector-profile.update --output json --no-input`.

Example: `mammoth support connector-profile update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorProfileUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector.create`

Run: `mammoth support connector create`. Exact input fields: `mammoth schema get support.connector.create --output json --no-input`.

Example: `mammoth support connector create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector.delete`

Run: `mammoth support connector delete`. Exact input fields: `mammoth schema get support.connector.delete --output json --no-input`.

Example: `mammoth support connector delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector.list`

Run: `mammoth support connector list`. Exact input fields: `mammoth schema get support.connector.list --output json --no-input`.

Example: `mammoth support connector list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.connector.update`

Run: `mammoth support connector update`. Exact input fields: `mammoth schema get support.connector.update --output json --no-input`.

Example: `mammoth support connector update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportConnectorUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature-profile.add-feature`

Run: `mammoth support feature-profile add-feature`. Exact input fields: `mammoth schema get support.feature-profile.add-feature --output json --no-input`.

Example: `mammoth support feature-profile add-feature 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureProfileAddFeatureResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature-profile.create`

Run: `mammoth support feature-profile create`. Exact input fields: `mammoth schema get support.feature-profile.create --output json --no-input`.

Example: `mammoth support feature-profile create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureProfileCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature-profile.delete`

Run: `mammoth support feature-profile delete`. Exact input fields: `mammoth schema get support.feature-profile.delete --output json --no-input`.

Example: `mammoth support feature-profile delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureProfileDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature-profile.list`

Run: `mammoth support feature-profile list`. Exact input fields: `mammoth schema get support.feature-profile.list --output json --no-input`.

Example: `mammoth support feature-profile list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureProfileListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature-profile.update`

Run: `mammoth support feature-profile update`. Exact input fields: `mammoth schema get support.feature-profile.update --output json --no-input`.

Example: `mammoth support feature-profile update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureProfileUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature.create`

Run: `mammoth support feature create`. Exact input fields: `mammoth schema get support.feature.create --output json --no-input`.

Example: `mammoth support feature create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature.delete`

Run: `mammoth support feature delete`. Exact input fields: `mammoth schema get support.feature.delete --output json --no-input`.

Example: `mammoth support feature delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature.list`

Run: `mammoth support feature list`. Exact input fields: `mammoth schema get support.feature.list --output json --no-input`.

Example: `mammoth support feature list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.feature.update`

Run: `mammoth support feature update`. Exact input fields: `mammoth schema get support.feature.update --output json --no-input`.

Example: `mammoth support feature update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportFeatureUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.ownership.transfer`

Run: `mammoth support ownership transfer`. Exact input fields: `mammoth schema get support.ownership.transfer --output json --no-input`.

Example: `mammoth support ownership transfer 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportOwnershipTransferResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.archive`

Run: `mammoth support plan archive`. Exact input fields: `mammoth schema get support.plan.archive --output json --no-input`.

Example: `mammoth support plan archive 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanArchiveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.chargebee-list`

Run: `mammoth support plan chargebee-list`. Exact input fields: `mammoth schema get support.plan.chargebee-list --output json --no-input`.

Example: `mammoth support plan chargebee-list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanChargebeeListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.create`

Run: `mammoth support plan create`. Exact input fields: `mammoth schema get support.plan.create --output json --no-input`.

Example: `mammoth support plan create 'Revenue report' --input '{"monthly_price": 1.0, "is_self_serve": true}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.delete`

Run: `mammoth support plan delete`. Exact input fields: `mammoth schema get support.plan.delete --output json --no-input`.

Example: `mammoth support plan delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.get`

Run: `mammoth support plan get`. Exact input fields: `mammoth schema get support.plan.get --output json --no-input`.

Example: `mammoth support plan get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanGetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.list`

Run: `mammoth support plan list`. Exact input fields: `mammoth schema get support.plan.list --output json --no-input`.

Example: `mammoth support plan list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.self-serve-list`

Run: `mammoth support plan self-serve-list`. Exact input fields: `mammoth schema get support.plan.self-serve-list --output json --no-input`.

Example: `mammoth support plan self-serve-list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanSelfServeListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.update`

Run: `mammoth support plan update`. Exact input fields: `mammoth schema get support.plan.update --output json --no-input`.

Example: `mammoth support plan update 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.plan.update-storage-tiers`

Run: `mammoth support plan update-storage-tiers`. Exact input fields: `mammoth schema get support.plan.update-storage-tiers --output json --no-input`.

Example: `mammoth support plan update-storage-tiers 123 --input '{"storage_tiers": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportPlanUpdateStorageTiersResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.subscription.create`

Run: `mammoth support subscription create`. Exact input fields: `mammoth schema get support.subscription.create --output json --no-input`.

Example: `mammoth support subscription create 123 resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportSubscriptionCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.subscription.get`

Run: `mammoth support subscription get`. Exact input fields: `mammoth schema get support.subscription.get --output json --no-input`.

Example: `mammoth support subscription get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportSubscriptionGetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.subscription.update`

Run: `mammoth support subscription update`. Exact input fields: `mammoth schema get support.subscription.update --output json --no-input`.

Example: `mammoth support subscription update 123 resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportSubscriptionUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.user.list-all`

Run: `mammoth support user list-all`. Exact input fields: `mammoth schema get support.user.list-all --output json --no-input`.

Example: `mammoth support user list-all --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportUserListAllResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.user.register`

Run: `mammoth support user register`. Exact input fields: `mammoth schema get support.user.register --output json --no-input`.

Example: `mammoth support user register analyst@example.com --input '{"first_name": "Revenue report", "last_name": "Revenue report", "verified": true}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportUserRegisterResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.user.update`

Run: `mammoth support user update`. Exact input fields: `mammoth schema get support.user.update --output json --no-input`.

Example: `mammoth support user update analyst@example.com --input '{"verified": true}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportUserUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.create`

Run: `mammoth support workspace create`. Exact input fields: `mammoth schema get support.workspace.create --output json --no-input`.

Example: `mammoth support workspace create 'Revenue report' --input '{"user_email": "analyst@example.com", "payment_frequency": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.delete`

Run: `mammoth support workspace delete`. Exact input fields: `mammoth schema get support.workspace.delete --output json --no-input`.

Example: `mammoth support workspace delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.get`

Run: `mammoth support workspace get`. Exact input fields: `mammoth schema get support.workspace.get --output json --no-input`.

Example: `mammoth support workspace get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceGetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.list`

Run: `mammoth support workspace list`. Exact input fields: `mammoth schema get support.workspace.list --output json --no-input`.

Example: `mammoth support workspace list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.restore-access`

Run: `mammoth support workspace restore-access`. Exact input fields: `mammoth schema get support.workspace.restore-access --output json --no-input`.

Example: `mammoth support workspace restore-access 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceRestoreAccessResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.suspend-access`

Run: `mammoth support workspace suspend-access`. Exact input fields: `mammoth schema get support.workspace.suspend-access --output json --no-input`.

Example: `mammoth support workspace suspend-access 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceSuspendAccessResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.update`

Run: `mammoth support workspace update`. Exact input fields: `mammoth schema get support.workspace.update --output json --no-input`.

Example: `mammoth support workspace update 123 --input '{"name": "Revenue report", "payment_frequency": "sample", "plan_id": 1}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.user.add`

Run: `mammoth support workspace user add`. Exact input fields: `mammoth schema get support.workspace.user.add --output json --no-input`.

Example: `mammoth support workspace user add 123 --input '{"email": "analyst@example.com", "role": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceUserAddResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.user.list`

Run: `mammoth support workspace user list`. Exact input fields: `mammoth schema get support.workspace.user.list --output json --no-input`.

Example: `mammoth support workspace user list 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceUserListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.user.remove`

Run: `mammoth support workspace user remove`. Exact input fields: `mammoth schema get support.workspace.user.remove --output json --no-input`.

Example: `mammoth support workspace user remove 123 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceUserRemoveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `support.workspace.user.transfer`

Run: `mammoth support workspace user transfer`. Exact input fields: `mammoth schema get support.workspace.user.transfer --output json --no-input`.

Example: `mammoth support workspace user transfer 123 123 --input '{"role": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `SupportWorkspaceUserTransferResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
