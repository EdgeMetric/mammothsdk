# `billing` commands

### `billing.chargebee-plan`

Run: `mammoth billing chargebee-plan`. Exact input fields: `mammoth schema get billing.chargebee-plan --output json --no-input`.

Example: `mammoth billing chargebee-plan --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingChargebeePlanResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.hosted-page`

Run: `mammoth billing hosted-page`. Exact input fields: `mammoth schema get billing.hosted-page --output json --no-input`.

Example: `mammoth billing hosted-page sample --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingHostedPageResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.invoice.charge`

Run: `mammoth billing invoice charge`. Exact input fields: `mammoth schema get billing.invoice.charge --output json --no-input`.

Example: `mammoth billing invoice charge --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingInvoiceChargeResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.invoice.get`

Run: `mammoth billing invoice get`. Exact input fields: `mammoth schema get billing.invoice.get --output json --no-input`.

Example: `mammoth billing invoice get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingInvoiceGetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.invoice.list`

Run: `mammoth billing invoice list`. Exact input fields: `mammoth schema get billing.invoice.list --output json --no-input`.

Example: `mammoth billing invoice list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingInvoiceListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.cancel`

Run: `mammoth billing stripe cancel`. Exact input fields: `mammoth schema get billing.stripe.cancel --output json --no-input`.

Example: `mammoth billing stripe cancel --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeCancelResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.checkout-url`

Run: `mammoth billing stripe checkout-url`. Exact input fields: `mammoth schema get billing.stripe.checkout-url --output json --no-input`.

Example: `mammoth billing stripe checkout-url --input '{"success_url": "https://example.com/data.csv", "cancel_url": "https://example.com/data.csv"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeCheckoutUrlResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.create`

Run: `mammoth billing stripe create`. Exact input fields: `mammoth schema get billing.stripe.create --output json --no-input`.

Example: `mammoth billing stripe create 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.end-trial`

Run: `mammoth billing stripe end-trial`. Exact input fields: `mammoth schema get billing.stripe.end-trial --output json --no-input`.

Example: `mammoth billing stripe end-trial --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeEndTrialResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.get`

Run: `mammoth billing stripe get`. Exact input fields: `mammoth schema get billing.stripe.get --output json --no-input`.

Example: `mammoth billing stripe get --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeGetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.history`

Run: `mammoth billing stripe history`. Exact input fields: `mammoth schema get billing.stripe.history --output json --no-input`.

Example: `mammoth billing stripe history --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeHistoryResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.payment-method.delete`

Run: `mammoth billing stripe payment-method delete`. Exact input fields: `mammoth schema get billing.stripe.payment-method.delete --output json --no-input`.

Example: `mammoth billing stripe payment-method delete resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripePaymentMethodDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.payment-method.list`

Run: `mammoth billing stripe payment-method list`. Exact input fields: `mammoth schema get billing.stripe.payment-method.list --output json --no-input`.

Example: `mammoth billing stripe payment-method list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripePaymentMethodListResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.payment-method.set-default`

Run: `mammoth billing stripe payment-method set-default`. Exact input fields: `mammoth schema get billing.stripe.payment-method.set-default --output json --no-input`.

Example: `mammoth billing stripe payment-method set-default resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripePaymentMethodSetDefaultResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.portal-url`

Run: `mammoth billing stripe portal-url`. Exact input fields: `mammoth schema get billing.stripe.portal-url --output json --no-input`.

Example: `mammoth billing stripe portal-url --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripePortalUrlResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.preview-invoice`

Run: `mammoth billing stripe preview-invoice`. Exact input fields: `mammoth schema get billing.stripe.preview-invoice --output json --no-input`.

Example: `mammoth billing stripe preview-invoice --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripePreviewInvoiceResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.retry-payment`

Run: `mammoth billing stripe retry-payment`. Exact input fields: `mammoth schema get billing.stripe.retry-payment --output json --no-input`.

Example: `mammoth billing stripe retry-payment --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeRetryPaymentResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.status`

Run: `mammoth billing stripe status`. Exact input fields: `mammoth schema get billing.stripe.status --output json --no-input`.

Example: `mammoth billing stripe status --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeStatusResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.sync`

Run: `mammoth billing stripe sync`. Exact input fields: `mammoth schema get billing.stripe.sync --output json --no-input`.

Example: `mammoth billing stripe sync --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeSyncResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.upcoming-invoice`

Run: `mammoth billing stripe upcoming-invoice`. Exact input fields: `mammoth schema get billing.stripe.upcoming-invoice --output json --no-input`.

Example: `mammoth billing stripe upcoming-invoice --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeUpcomingInvoiceResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.stripe.usage`

Run: `mammoth billing stripe usage`. Exact input fields: `mammoth schema get billing.stripe.usage --output json --no-input`.

Example: `mammoth billing stripe usage --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingStripeUsageResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.subscription.get`

Run: `mammoth billing subscription get`. Exact input fields: `mammoth schema get billing.subscription.get --output json --no-input`.

Example: `mammoth billing subscription get --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingSubscriptionGetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `billing.subscription.update`

Run: `mammoth billing subscription update`. Exact input fields: `mammoth schema get billing.subscription.update --output json --no-input`.

Example: `mammoth billing subscription update --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `BillingSubscriptionUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
