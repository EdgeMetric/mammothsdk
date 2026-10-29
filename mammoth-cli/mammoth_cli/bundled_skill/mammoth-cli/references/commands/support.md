# `support` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `support.billing.cancel-subscription`

Run: `mammoth support billing cancel-subscription`. Exact input fields: `mammoth schema get support.billing.cancel-subscription`.

Example: `mammoth support billing cancel-subscription 123 --input '{"when": "period_end"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportBillingCancelSubscriptionResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.billing.change-plan`

Run: `mammoth support billing change-plan`. Exact input fields: `mammoth schema get support.billing.change-plan`.

Example: `mammoth support billing change-plan 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportBillingChangePlanResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.billing.end-trial`

Run: `mammoth support billing end-trial`. Exact input fields: `mammoth schema get support.billing.end-trial`.

Example: `mammoth support billing end-trial 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportBillingEndTrialResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.billing.refund`

Run: `mammoth support billing refund`. Exact input fields: `mammoth schema get support.billing.refund`.

Example: `mammoth support billing refund 123 --input '{"amount": 500}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportBillingRefundResult`; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.billing.retry-payment`

Run: `mammoth support billing retry-payment`. Exact input fields: `mammoth schema get support.billing.retry-payment`.

Example: `mammoth support billing retry-payment 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportBillingRetryPaymentResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.billing.start-trial`

Run: `mammoth support billing start-trial`. Exact input fields: `mammoth schema get support.billing.start-trial`.

Example: `mammoth support billing start-trial 123 --input '{"days": 14}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportBillingStartTrialResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.add-connector`

Run: `mammoth support connector-profile add-connector`. Exact input fields: `mammoth schema get support.connector-profile.add-connector`.

Example: `mammoth support connector-profile add-connector 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileAddConnectorResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.create`

Run: `mammoth support connector-profile create`. Exact input fields: `mammoth schema get support.connector-profile.create`.

Example: `mammoth support connector-profile create 'Revenue report' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.delete`

Run: `mammoth support connector-profile delete`. Exact input fields: `mammoth schema get support.connector-profile.delete`.

Example: `mammoth support connector-profile delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector-profile.list`

Run: `mammoth support connector-profile list`. Exact input fields: `mammoth schema get support.connector-profile.list`.

Example: `mammoth support connector-profile list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportConnectorProfileListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.connector_profiles Single invocation only.

### `support.connector-profile.update`

Run: `mammoth support connector-profile update`. Exact input fields: `mammoth schema get support.connector-profile.update`.

Example: `mammoth support connector-profile update 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorProfileUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.bucket-impact`

Run: `mammoth support connector bucket-impact`. Exact input fields: `mammoth schema get support.connector.bucket-impact`.

Example: `mammoth support connector bucket-impact 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportConnectorBucketImpactResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.create`

Run: `mammoth support connector create`. Exact input fields: `mammoth schema get support.connector.create`.

Example: `mammoth support connector create 'Revenue report' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.delete`

Run: `mammoth support connector delete`. Exact input fields: `mammoth schema get support.connector.delete`.

Example: `mammoth support connector delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.connector.list`

Run: `mammoth support connector list`. Exact input fields: `mammoth schema get support.connector.list`.

Example: `mammoth support connector list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportConnectorListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.connectors Single invocation only.

### `support.connector.update`

Run: `mammoth support connector update`. Exact input fields: `mammoth schema get support.connector.update`.

Example: `mammoth support connector update 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportConnectorUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.activity`

Run: `mammoth support deal activity`. Exact input fields: `mammoth schema get support.deal.activity`.

Example: `mammoth support deal activity 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportDealActivityResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.cancel-move-to-partner`

Run: `mammoth support deal cancel-move-to-partner`. Exact input fields: `mammoth schema get support.deal.cancel-move-to-partner`.

Example: `mammoth support deal cancel-move-to-partner 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportDealCancelMoveToPartnerResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.create`

Run: `mammoth support deal create`. Exact input fields: `mammoth schema get support.deal.create`.

Example: `mammoth support deal create 123 --input '{"base_plan_id": 3, "price": 1200.0}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportDealCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.get`

Run: `mammoth support deal get`. Exact input fields: `mammoth schema get support.deal.get`.

Example: `mammoth support deal get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportDealGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.list`

Run: `mammoth support deal list`. Exact input fields: `mammoth schema get support.deal.list`.

Example: `mammoth support deal list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportDealListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.move-to-partner`

Run: `mammoth support deal move-to-partner`. Exact input fields: `mammoth schema get support.deal.move-to-partner`.

Example: `mammoth support deal move-to-partner 123 456 --input '{"price": 900.0, "billing_interval": "monthly"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportDealMoveToPartnerResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.opt-in`

Run: `mammoth support deal opt-in`. Exact input fields: `mammoth schema get support.deal.opt-in`.

Example: `mammoth support deal opt-in 123 --input '{"everything": true}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportDealOptInResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.preview-entitlement`

Run: `mammoth support deal preview-entitlement`. Exact input fields: `mammoth schema get support.deal.preview-entitlement`.

Example: `mammoth support deal preview-entitlement 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportDealPreviewEntitlementResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.deal.update`

Run: `mammoth support deal update`. Exact input fields: `mammoth schema get support.deal.update`.

Example: `mammoth support deal update 123 --input '{"notes": "Renewal agreed"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportDealUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.entitlement.registry`

Run: `mammoth support entitlement registry`. Exact input fields: `mammoth schema get support.entitlement.registry`.

Example: `mammoth support entitlement registry`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportEntitlementRegistryResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.add-feature`

Run: `mammoth support feature-profile add-feature`. Exact input fields: `mammoth schema get support.feature-profile.add-feature`.

Example: `mammoth support feature-profile add-feature 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileAddFeatureResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.create`

Run: `mammoth support feature-profile create`. Exact input fields: `mammoth schema get support.feature-profile.create`.

Example: `mammoth support feature-profile create 'Revenue report' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.delete`

Run: `mammoth support feature-profile delete`. Exact input fields: `mammoth schema get support.feature-profile.delete`.

Example: `mammoth support feature-profile delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature-profile.list`

Run: `mammoth support feature-profile list`. Exact input fields: `mammoth schema get support.feature-profile.list`.

Example: `mammoth support feature-profile list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportFeatureProfileListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.feature_profiles Single invocation only.

### `support.feature-profile.update`

Run: `mammoth support feature-profile update`. Exact input fields: `mammoth schema get support.feature-profile.update`.

Example: `mammoth support feature-profile update 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureProfileUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature.create`

Run: `mammoth support feature create`. Exact input fields: `mammoth schema get support.feature.create`.

Example: `mammoth support feature create 'Revenue report' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature.delete`

Run: `mammoth support feature delete`. Exact input fields: `mammoth schema get support.feature.delete`.

Example: `mammoth support feature delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.feature.list`

Run: `mammoth support feature list`. Exact input fields: `mammoth schema get support.feature.list`.

Example: `mammoth support feature list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportFeatureListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.features Single invocation only.

### `support.feature.update`

Run: `mammoth support feature update`. Exact input fields: `mammoth schema get support.feature.update`.

Example: `mammoth support feature update 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportFeatureUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.identity.get`

Run: `mammoth support identity get`. Exact input fields: `mammoth schema get support.identity.get`.

Example: `mammoth support identity get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportIdentityGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.identity.list`

Run: `mammoth support identity list`. Exact input fields: `mammoth schema get support.identity.list`.

Example: `mammoth support identity list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportIdentityListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.ownership.transfer`

Run: `mammoth support ownership transfer`. Exact input fields: `mammoth schema get support.ownership.transfer`.

Example: `mammoth support ownership transfer 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportOwnershipTransferResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.activity`

Run: `mammoth support partner activity`. Exact input fields: `mammoth schema get support.partner.activity`.

Example: `mammoth support partner activity 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPartnerActivityResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.billing`

Run: `mammoth support partner billing`. Exact input fields: `mammoth schema get support.partner.billing`.

Example: `mammoth support partner billing 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPartnerBillingResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.charge-invoices`

Run: `mammoth support partner charge-invoices`. Exact input fields: `mammoth schema get support.partner.charge-invoices`.

Example: `mammoth support partner charge-invoices 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerChargeInvoicesResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.client.cancel-detach`

Run: `mammoth support partner client cancel-detach`. Exact input fields: `mammoth schema get support.partner.client.cancel-detach`.

Example: `mammoth support partner client cancel-detach 123 456 --yes --confirm 456`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerClientCancelDetachResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.client.delete`

Run: `mammoth support partner client delete`. Exact input fields: `mammoth schema get support.partner.client.delete`.

Example: `mammoth support partner client delete 123 456 --yes --confirm 456`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerClientDeleteResult`; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.client.detach`

Run: `mammoth support partner client detach`. Exact input fields: `mammoth schema get support.partner.client.detach`.

Example: `mammoth support partner client detach 123 456 --input '{"price": 900.0, "contact_email": "owner@example.com"}' --yes --confirm 456`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerClientDetachResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.client.list`

Run: `mammoth support partner client list`. Exact input fields: `mammoth schema get support.partner.client.list`.

Example: `mammoth support partner client list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPartnerClientListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.create`

Run: `mammoth support partner create`. Exact input fields: `mammoth schema get support.partner.create`.

Example: `mammoth support partner create 'Revenue report' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.get`

Run: `mammoth support partner get`. Exact input fields: `mammoth schema get support.partner.get`.

Example: `mammoth support partner get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPartnerGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.invoices`

Run: `mammoth support partner invoices`. Exact input fields: `mammoth schema get support.partner.invoices`.

Example: `mammoth support partner invoices 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPartnerInvoicesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.list`

Run: `mammoth support partner list`. Exact input fields: `mammoth schema get support.partner.list`.

Example: `mammoth support partner list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPartnerListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.send-payment-link`

Run: `mammoth support partner send-payment-link`. Exact input fields: `mammoth schema get support.partner.send-payment-link`.

Example: `mammoth support partner send-payment-link 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerSendPaymentLinkResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.partner.update`

Run: `mammoth support partner update`. Exact input fields: `mammoth schema get support.partner.update`.

Example: `mammoth support partner update 123 --input '{"notes": "Prefers invoices"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPartnerUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.archive`

Run: `mammoth support plan archive`. Exact input fields: `mammoth schema get support.plan.archive`.

Example: `mammoth support plan archive 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanArchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.catalog`

Run: `mammoth support plan catalog`. Exact input fields: `mammoth schema get support.plan.catalog`.

Example: `mammoth support plan catalog`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPlanCatalogResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.chargebee-list`

Run: `mammoth support plan chargebee-list`. Exact input fields: `mammoth schema get support.plan.chargebee-list`.

Example: `mammoth support plan chargebee-list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPlanChargebeeListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.available_plans Single invocation only.

### `support.plan.create`

Run: `mammoth support plan create`. Exact input fields: `mammoth schema get support.plan.create`.

Example: `mammoth support plan create 'Revenue report' --input '{"monthly_price": 1.0, "is_self_serve": true}' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.delete`

Run: `mammoth support plan delete`. Exact input fields: `mammoth schema get support.plan.delete`.

Example: `mammoth support plan delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.get`

Run: `mammoth support plan get`. Exact input fields: `mammoth schema get support.plan.get`.

Example: `mammoth support plan get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPlanGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.list`

Run: `mammoth support plan list`. Exact input fields: `mammoth schema get support.plan.list`.

Example: `mammoth support plan list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPlanListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.plans (5 plans, ids 4-8) Single invocation only.

### `support.plan.self-serve-list`

Run: `mammoth support plan self-serve-list`. Exact input fields: `mammoth schema get support.plan.self-serve-list`.

Example: `mammoth support plan self-serve-list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPlanSelfServeListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data.plans Single invocation only.

### `support.plan.storage-option.archive`

Run: `mammoth support plan storage-option archive`. Exact input fields: `mammoth schema get support.plan.storage-option.archive`.

Example: `mammoth support plan storage-option archive 123 456 --yes --confirm 456`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanStorageOptionArchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.storage-option.create`

Run: `mammoth support plan storage-option create`. Exact input fields: `mammoth schema get support.plan.storage-option.create`.

Example: `mammoth support plan storage-option create 123 --input '{"storage_gb": 1, "monthly_price": 1.0, "annual_price": 1.0}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanStorageOptionCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.storage-option.list`

Run: `mammoth support plan storage-option list`. Exact input fields: `mammoth schema get support.plan.storage-option.list`.

Example: `mammoth support plan storage-option list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportPlanStorageOptionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.storage-option.update`

Run: `mammoth support plan storage-option update`. Exact input fields: `mammoth schema get support.plan.storage-option.update`.

Example: `mammoth support plan storage-option update 123 456 --yes --confirm 456`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanStorageOptionUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.unarchive`

Run: `mammoth support plan unarchive`. Exact input fields: `mammoth schema get support.plan.unarchive`.

Example: `mammoth support plan unarchive 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanUnarchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.update`

Run: `mammoth support plan update`. Exact input fields: `mammoth schema get support.plan.update`.

Example: `mammoth support plan update 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.update-entitlements`

Run: `mammoth support plan update-entitlements`. Exact input fields: `mammoth schema get support.plan.update-entitlements`.

Example: `mammoth support plan update-entitlements 123 --input '{"values": {"dashboardBranding": "no_branding"}}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanUpdateEntitlementsResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.plan.update-storage-tiers`

Run: `mammoth support plan update-storage-tiers`. Exact input fields: `mammoth schema get support.plan.update-storage-tiers`.

Example: `mammoth support plan update-storage-tiers 123 --input '{"storage_tiers": [{"name": "Status"}]}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportPlanUpdateStorageTiersResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.project-move.get`

Run: `mammoth support project-move get`. Exact input fields: `mammoth schema get support.project-move.get`.

Example: `mammoth support project-move get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportProjectMoveGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.project-move.purge`

Run: `mammoth support project-move purge`. Exact input fields: `mammoth schema get support.project-move.purge`.

Example: `mammoth support project-move purge 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportProjectMovePurgeResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.search`

Run: `mammoth support search`. Exact input fields: `mammoth schema get support.search`.

Example: `mammoth support search acme`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportSearchResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.subscription.create`

Run: `mammoth support subscription create`. Exact input fields: `mammoth schema get support.subscription.create`.

Example: `mammoth support subscription create 123 resource-123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportSubscriptionCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.subscription.get`

Run: `mammoth support subscription get`. Exact input fields: `mammoth schema get support.subscription.get`.

Example: `mammoth support subscription get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportSubscriptionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.subscription.update`

Run: `mammoth support subscription update`. Exact input fields: `mammoth schema get support.subscription.update`.

Example: `mammoth support subscription update 123 resource-123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportSubscriptionUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.audit`

Run: `mammoth support template audit`. Exact input fields: `mammoth schema get support.template.audit`.

Example: `mammoth support template audit`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateAuditResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.canvas`

Run: `mammoth support template canvas`. Exact input fields: `mammoth schema get support.template.canvas`.

Example: `mammoth support template canvas revenue-overview`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateCanvasResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.data-preview`

Run: `mammoth support template data-preview`. Exact input fields: `mammoth schema get support.template.data-preview`.

Example: `mammoth support template data-preview revenue-overview`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateDataPreviewResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.discard`

Run: `mammoth support template discard`. Exact input fields: `mammoth schema get support.template.discard`.

Example: `mammoth support template discard revenue-overview --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplateDiscardResult`; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.edit`

Run: `mammoth support template edit`. Exact input fields: `mammoth schema get support.template.edit`.

Example: `mammoth support template edit revenue-overview --input '{"changes": {"name": "Status"}}' --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplateEditResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.export`

Run: `mammoth support template export`. Exact input fields: `mammoth schema get support.template.export`.

Example: `mammoth support template export revenue-overview`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateExportResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.export-dashboard`

Run: `mammoth support template export-dashboard`. Exact input fields: `mammoth schema get support.template.export-dashboard`.

Example: `mammoth support template export-dashboard 123 --input '{"slug": "revenue-overview"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateExportDashboardResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.import`

Run: `mammoth support template import`. Exact input fields: `mammoth schema get support.template.import`.

Example: `mammoth support template import template.zip --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `SupportTemplateImportResult`; mutation `high_impact`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.inspect`

Run: `mammoth support template inspect`. Exact input fields: `mammoth schema get support.template.inspect`.

Example: `mammoth support template inspect template.zip`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateInspectResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.list`

Run: `mammoth support template list`. Exact input fields: `mammoth schema get support.template.list`.

Example: `mammoth support template list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.publish`

Run: `mammoth support template publish`. Exact input fields: `mammoth schema get support.template.publish`.

Example: `mammoth support template publish revenue-overview --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplatePublishResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.retire`

Run: `mammoth support template retire`. Exact input fields: `mammoth schema get support.template.retire`.

Example: `mammoth support template retire revenue-overview --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplateRetireResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.snapshots`

Run: `mammoth support template snapshots`. Exact input fields: `mammoth schema get support.template.snapshots`.

Example: `mammoth support template snapshots`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTemplateSnapshotsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.thumbnail.clear`

Run: `mammoth support template thumbnail clear`. Exact input fields: `mammoth schema get support.template.thumbnail.clear`.

Example: `mammoth support template thumbnail clear revenue-overview --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplateThumbnailClearResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.thumbnail.set`

Run: `mammoth support template thumbnail set`. Exact input fields: `mammoth schema get support.template.thumbnail.set`.

Example: `mammoth support template thumbnail set revenue-overview card.png --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplateThumbnailSetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.template.unpublish`

Run: `mammoth support template unpublish`. Exact input fields: `mammoth schema get support.template.unpublish`.

Example: `mammoth support template unpublish revenue-overview --yes --confirm revenue-overview`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportTemplateUnpublishResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.triage`

Run: `mammoth support triage`. Exact input fields: `mammoth schema get support.triage`.

Example: `mammoth support triage`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportTriageResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.usage-tiles`

Run: `mammoth support usage-tiles`. Exact input fields: `mammoth schema get support.usage-tiles`.

Example: `mammoth support usage-tiles`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportUsageTilesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.user.list-all`

Run: `mammoth support user list-all`. Exact input fields: `mammoth schema get support.user.list-all`.

Example: `mammoth support user list-all`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportUserListAllResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; data keyed by workspace id ('4') listing users Single invocation only.

### `support.user.register`

Run: `mammoth support user register`. Exact input fields: `mammoth schema get support.user.register`.

Example: `mammoth support user register analyst@example.com --input '{"first_name": "Revenue report", "last_name": "Revenue report", "verified": true}' --yes --confirm analyst@example.com`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportUserRegisterResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.user.update`

Run: `mammoth support user update`. Exact input fields: `mammoth schema get support.user.update`.

Example: `mammoth support user update analyst@example.com --input '{"verified": true}' --yes --confirm analyst@example.com`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportUserUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.activity`

Run: `mammoth support workspace activity`. Exact input fields: `mammoth schema get support.workspace.activity`.

Example: `mammoth support workspace activity 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceActivityResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.archive`

Run: `mammoth support workspace archive`. Exact input fields: `mammoth schema get support.workspace.archive`.

Example: `mammoth support workspace archive 123 --input '{"storage_class": "GLACIER_IR", "confirm_name": "Revenue report", "reason": "Customer left"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceArchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `support.workspace.archive-info`

Run: `mammoth support workspace archive-info`. Exact input fields: `mammoth schema get support.workspace.archive-info`.

Example: `mammoth support workspace archive-info 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceArchiveInfoResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.chargebee-cancelled`

Run: `mammoth support workspace chargebee-cancelled`. Exact input fields: `mammoth schema get support.workspace.chargebee-cancelled`.

Example: `mammoth support workspace chargebee-cancelled 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceChargebeeCancelledResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.create`

Run: `mammoth support workspace create`. Exact input fields: `mammoth schema get support.workspace.create`.

Example: `mammoth support workspace create 'Revenue report' --input '{"user_email": "analyst@example.com", "payment_frequency": "monthly"}' --yes --confirm 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.deal-seed`

Run: `mammoth support workspace deal-seed`. Exact input fields: `mammoth schema get support.workspace.deal-seed`.

Example: `mammoth support workspace deal-seed 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceDealSeedResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.delete`

Run: `mammoth support workspace delete`. Exact input fields: `mammoth schema get support.workspace.delete`.

Example: `mammoth support workspace delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceDeleteResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.entitlement`

Run: `mammoth support workspace entitlement`. Exact input fields: `mammoth schema get support.workspace.entitlement`.

Example: `mammoth support workspace entitlement 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceEntitlementResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.get`

Run: `mammoth support workspace get`. Exact input fields: `mammoth schema get support.workspace.get`.

Example: `mammoth support workspace get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.invite.cancel`

Run: `mammoth support workspace invite cancel`. Exact input fields: `mammoth schema get support.workspace.invite.cancel`.

Example: `mammoth support workspace invite cancel 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceInviteCancelResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.invite.resend`

Run: `mammoth support workspace invite resend`. Exact input fields: `mammoth schema get support.workspace.invite.resend`.

Example: `mammoth support workspace invite resend 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceInviteResendResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.list`

Run: `mammoth support workspace list`. Exact input fields: `mammoth schema get support.workspace.list`.

Example: `mammoth support workspace list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — admin read sweep 2026-09-18: exit 0 on release with CLI 2.0.15. The CLI gates this GET behind --yes --confirm WORKSPACE_ID (confirm_target policy); with confirmation: exit 0; route returns a bare array so the SDK wraps it as {status_code:200, response:[...]}…

### `support.workspace.project.list`

Run: `mammoth support workspace project list`. Exact input fields: `mammoth schema get support.workspace.project.list`.

Example: `mammoth support workspace project list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceProjectListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.project.move-check`

Run: `mammoth support workspace project move-check`. Exact input fields: `mammoth schema get support.workspace.project.move-check`.

Example: `mammoth support workspace project move-check 123 456 --input '{"target_workspace_id": 1}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceProjectMoveCheckResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.project.move-start`

Run: `mammoth support workspace project move-start`. Exact input fields: `mammoth schema get support.workspace.project.move-start`.

Example: `mammoth support workspace project move-start 123 456 --input '{"target_workspace_id": 1}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceProjectMoveStartResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.restore-access`

Run: `mammoth support workspace restore-access`. Exact input fields: `mammoth schema get support.workspace.restore-access`.

Example: `mammoth support workspace restore-access 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceRestoreAccessResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.restore-archive`

Run: `mammoth support workspace restore-archive`. Exact input fields: `mammoth schema get support.workspace.restore-archive`.

Example: `mammoth support workspace restore-archive 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceRestoreArchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `support.workspace.suspend-access`

Run: `mammoth support workspace suspend-access`. Exact input fields: `mammoth schema get support.workspace.suspend-access`.

Example: `mammoth support workspace suspend-access 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceSuspendAccessResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.update`

Run: `mammoth support workspace update`. Exact input fields: `mammoth schema get support.workspace.update`.

Example: `mammoth support workspace update 123 --input '{"name": "Revenue report", "payment_frequency": "monthly", "plan_id": 1}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUpdateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.add`

Run: `mammoth support workspace user add`. Exact input fields: `mammoth schema get support.workspace.user.add`.

Example: `mammoth support workspace user add 123 --input '{"email": "analyst@example.com", "role": "workspace_member"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.list`

Run: `mammoth support workspace user list`. Exact input fields: `mammoth schema get support.workspace.user.list`.

Example: `mammoth support workspace user list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SupportWorkspaceUserListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.remove`

Run: `mammoth support workspace user remove`. Exact input fields: `mammoth schema get support.workspace.user.remove`.

Example: `mammoth support workspace user remove 123 456 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserRemoveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `support.workspace.user.transfer`

Run: `mammoth support workspace user transfer`. Exact input fields: `mammoth schema get support.workspace.user.transfer`.

Example: `mammoth support workspace user transfer 123 456 --input '{"role": "workspace_admin"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `SupportWorkspaceUserTransferResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.
