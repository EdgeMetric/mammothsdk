# `billing` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `billing.chargebee-plan`

Run: `mammoth billing chargebee-plan`. Exact input fields: `mammoth schema get billing.chargebee-plan --output json --no-input`.

Example: `mammoth billing chargebee-plan --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingChargebeePlanResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: observed blocker — backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS014 'Chargebee plan not found for the given workspace' (workspace 4 is n. Re-check before relying on it.

### `billing.hosted-page`

Run: `mammoth billing hosted-page`. Exact input fields: `mammoth schema get billing.hosted-page --output json --no-input`.

Example: `mammoth billing hosted-page sample --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingHostedPageResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.invoice.charge`

Run: `mammoth billing invoice charge`. Exact input fields: `mammoth schema get billing.invoice.charge --output json --no-input`.

Example: `mammoth billing invoice charge --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingInvoiceChargeResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.invoice.get`

Run: `mammoth billing invoice get`. Exact input fields: `mammoth schema get billing.invoice.get --output json --no-input`.

Example: `mammoth billing invoice get 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingInvoiceGetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: billing invoice list answered HTTP 500, so no invoice id was observed. Re-check before relying on it.

### `billing.invoice.list`

Run: `mammoth billing invoice list`. Exact input fields: `mammoth schema get billing.invoice.list --output json --no-input`.

Example: `mammoth billing invoice list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingInvoiceListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: observed blocker — backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 500 with empty body on GET /workspaces/4/subscription_v1/invoices. Re-check before relying on it.

### `billing.stripe.cancel`

Run: `mammoth billing stripe cancel`. Exact input fields: `mammoth schema get billing.stripe.cancel --output json --no-input`.

Example: `mammoth billing stripe cancel --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeCancelResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.checkout-url`

Run: `mammoth billing stripe checkout-url`. Exact input fields: `mammoth schema get billing.stripe.checkout-url --output json --no-input`.

Example: `mammoth billing stripe checkout-url --input '{"success_url": "https://example.com/data.csv", "cancel_url": "https://example.com/data.csv"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeCheckoutUrlResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.create`

Run: `mammoth billing stripe create`. Exact input fields: `mammoth schema get billing.stripe.create --output json --no-input`.

Example: `mammoth billing stripe create 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.end-trial`

Run: `mammoth billing stripe end-trial`. Exact input fields: `mammoth schema get billing.stripe.end-trial --output json --no-input`.

Example: `mammoth billing stripe end-trial --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeEndTrialResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.get`

Run: `mammoth billing stripe get`. Exact input fields: `mammoth schema get billing.stripe.get --output json --no-input`.

Example: `mammoth billing stripe get --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeGetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.history`

Run: `mammoth billing stripe history`. Exact input fields: `mammoth schema get billing.stripe.history --output json --no-input`.

Example: `mammoth billing stripe history --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeHistoryResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.billing_history Single invocation only.

### `billing.stripe.payment-method.delete`

Run: `mammoth billing stripe payment-method delete`. Exact input fields: `mammoth schema get billing.stripe.payment-method.delete --output json --no-input`.

Example: `mammoth billing stripe payment-method delete resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripePaymentMethodDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.payment-method.list`

Run: `mammoth billing stripe payment-method list`. Exact input fields: `mammoth schema get billing.stripe.payment-method.list --output json --no-input`.

Example: `mammoth billing stripe payment-method list --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripePaymentMethodListResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.payment_methods Single invocation only.

### `billing.stripe.payment-method.set-default`

Run: `mammoth billing stripe payment-method set-default`. Exact input fields: `mammoth schema get billing.stripe.payment-method.set-default --output json --no-input`.

Example: `mammoth billing stripe payment-method set-default resource-123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripePaymentMethodSetDefaultResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.portal-url`

Run: `mammoth billing stripe portal-url`. Exact input fields: `mammoth schema get billing.stripe.portal-url --output json --no-input`.

Example: `mammoth billing stripe portal-url --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripePortalUrlResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.preview-invoice`

Run: `mammoth billing stripe preview-invoice`. Exact input fields: `mammoth schema get billing.stripe.preview-invoice --output json --no-input`.

Example: `mammoth billing stripe preview-invoice --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripePreviewInvoiceResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: observed blocker — backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS037 'Failed to perform subscription operation'. Re-check before relying on it.

### `billing.stripe.retry-payment`

Run: `mammoth billing stripe retry-payment`. Exact input fields: `mammoth schema get billing.stripe.retry-payment --output json --no-input`.

Example: `mammoth billing stripe retry-payment --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeRetryPaymentResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.status`

Run: `mammoth billing stripe status`. Exact input fields: `mammoth schema get billing.stripe.status --output json --no-input`.

Example: `mammoth billing stripe status --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeStatusResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data with billing_cycle, has_active_subscription, is_trial_expired, ... (20 keys) Si…

### `billing.stripe.sync`

Run: `mammoth billing stripe sync`. Exact input fields: `mammoth schema get billing.stripe.sync --output json --no-input`.

Example: `mammoth billing stripe sync --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeSyncResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `billing.stripe.upcoming-invoice`

Run: `mammoth billing stripe upcoming-invoice`. Exact input fields: `mammoth schema get billing.stripe.upcoming-invoice --output json --no-input`.

Example: `mammoth billing stripe upcoming-invoice --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeUpcomingInvoiceResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: observed blocker — backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS074 'Upcoming invoice not found' (no active Stripe subscription on works. Re-check before relying on it.

### `billing.stripe.usage`

Run: `mammoth billing stripe usage`. Exact input fields: `mammoth schema get billing.stripe.usage --output json --no-input`.

Example: `mammoth billing stripe usage --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingStripeUsageResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: observed blocker — backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 5GENR010 UNKNOWN_ERROR 'Unknown error occurred. Re-check before relying on it.

### `billing.subscription.get`

Run: `mammoth billing subscription get`. Exact input fields: `mammoth schema get billing.subscription.get --output json --no-input`.

Example: `mammoth billing subscription get --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingSubscriptionGetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data with current_plan_new, next_action_info, over_limit_info, sms_details Single in…

### `billing.subscription.update`

Run: `mammoth billing subscription update`. Exact input fields: `mammoth schema get billing.subscription.update --output json --no-input`.

Example: `mammoth billing subscription update --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `BillingSubscriptionUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.
