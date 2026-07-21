# Command reference

Generated from the reviewed command manifests for mammoth-cli 0.1.0.
Do not edit by hand; run `python scripts/gen_docs.py`.

Total commands: 435.

## activity

### `mammoth activity export`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.activity_logs.ActivityLogsAPI.export`
- Agent example: `mammoth activity export --output json --no-input`

### `mammoth activity list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.activity_logs.ActivityLogsAPI.list`
- Agent example: `mammoth activity list --output json --no-input`

## addon

### `mammoth addon connector add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.add_connector`
- Agent example: `mammoth addon connector add --output json --no-input`

### `mammoth addon connector remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.remove_connector`
- Agent example: `mammoth addon connector remove --output json --no-input`

### `mammoth addon list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.addons.AddonsAPI.list`
- Agent example: `mammoth addon list --output json --no-input`

### `mammoth addon storage add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.add_storage`
- Agent example: `mammoth addon storage add --output json --no-input`

### `mammoth addon storage remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.remove_storage`
- Agent example: `mammoth addon storage remove --output json --no-input`

### `mammoth addon user add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.add_users`
- Agent example: `mammoth addon user add --output json --no-input`

### `mammoth addon user remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.remove_users`
- Agent example: `mammoth addon user remove --output json --no-input`

## agent

### `mammoth agent chat`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.chat`
- Agent example: `mammoth agent chat --output json --no-input`

### `mammoth agent session delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_delete`
- Agent example: `mammoth agent session delete --output json --no-input`

### `mammoth agent session list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_list`
- Agent example: `mammoth agent session list --output json --no-input`

### `mammoth agent session messages`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_messages`
- Agent example: `mammoth agent session messages --output json --no-input`

### `mammoth agent session set-visibility`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_set_visibility`
- Agent example: `mammoth agent session set-visibility --output json --no-input`

## ai

### `mammoth ai condition generate`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.condition_generate`
- Agent example: `mammoth ai condition generate --output json --no-input`

### `mammoth ai expression generate`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.expression_generate`
- Agent example: `mammoth ai expression generate --output json --no-input`

### `mammoth ai sql generate`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.generate_sql`
- Agent example: `mammoth ai sql generate --output json --no-input`

### `mammoth ai suggestion list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.get_suggestions`
- Agent example: `mammoth ai suggestion list --output json --no-input`

## annotation

### `mammoth annotation comment add`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.comment_add`
- Agent example: `mammoth annotation comment add --output json --no-input`

### `mammoth annotation create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.create`
- Agent example: `mammoth annotation create --output json --no-input`

### `mammoth annotation delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.delete`
- Agent example: `mammoth annotation delete --output json --no-input`

### `mammoth annotation list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.list`
- Agent example: `mammoth annotation list --output json --no-input`

### `mammoth annotation update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.update`
- Agent example: `mammoth annotation update --output json --no-input`

## auth

### `mammoth auth login`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.auth.login`
- Agent example: `mammoth auth login --output json --no-input`

### `mammoth auth logout`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.auth.logout`
- Agent example: `mammoth auth logout --output json --no-input`

### `mammoth auth status`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.auth.status`
- Agent example: `mammoth auth status --output json --no-input`

## automation

### `mammoth automation create`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.create`
- Agent example: `mammoth automation create --output json --no-input`

### `mammoth automation delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.delete`
- Agent example: `mammoth automation delete --output json --no-input`

### `mammoth automation get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.get`
- Agent example: `mammoth automation get --output json --no-input`

### `mammoth automation list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.list`
- Agent example: `mammoth automation list --output json --no-input`

### `mammoth automation restore`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.restore`
- Agent example: `mammoth automation restore --output json --no-input`

### `mammoth automation trash`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.trash`
- Agent example: `mammoth automation trash --output json --no-input`

### `mammoth automation update`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.update`
- Agent example: `mammoth automation update --output json --no-input`

## batch

### `mammoth batch bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.batches.BatchesAPI.bulk_delete`
- Agent example: `mammoth batch bulk-delete --output json --no-input`

### `mammoth batch create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.create`
- Agent example: `mammoth batch create --output json --no-input`

### `mammoth batch delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.batches.BatchesAPI.delete`
- Agent example: `mammoth batch delete --output json --no-input`

### `mammoth batch get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.get`
- Agent example: `mammoth batch get --output json --no-input`

### `mammoth batch list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.list`
- Agent example: `mammoth batch list --output json --no-input`

### `mammoth batch update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.update`
- Agent example: `mammoth batch update --output json --no-input`

## billing

### `mammoth billing chargebee-plan`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.chargebee_plan`
- Agent example: `mammoth billing chargebee-plan --output json --no-input`

### `mammoth billing hosted-page`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.hosted_page`
- Agent example: `mammoth billing hosted-page --output json --no-input`

### `mammoth billing invoice charge`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.invoice_charge`
- Agent example: `mammoth billing invoice charge --output json --no-input`

### `mammoth billing invoice get`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.invoice_get`
- Agent example: `mammoth billing invoice get --output json --no-input`

### `mammoth billing invoice list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.invoice_list`
- Agent example: `mammoth billing invoice list --output json --no-input`

### `mammoth billing stripe cancel`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_cancel`
- Agent example: `mammoth billing stripe cancel --output json --no-input`

### `mammoth billing stripe checkout-url`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_checkout_url`
- Agent example: `mammoth billing stripe checkout-url --output json --no-input`

### `mammoth billing stripe create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_create`
- Agent example: `mammoth billing stripe create --output json --no-input`

### `mammoth billing stripe end-trial`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_end_trial`
- Agent example: `mammoth billing stripe end-trial --output json --no-input`

### `mammoth billing stripe get`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_get`
- Agent example: `mammoth billing stripe get --output json --no-input`

### `mammoth billing stripe history`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_history`
- Agent example: `mammoth billing stripe history --output json --no-input`

### `mammoth billing stripe payment-method delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_delete`
- Agent example: `mammoth billing stripe payment-method delete --output json --no-input`

### `mammoth billing stripe payment-method list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_list`
- Agent example: `mammoth billing stripe payment-method list --output json --no-input`

### `mammoth billing stripe payment-method set-default`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_set_default`
- Agent example: `mammoth billing stripe payment-method set-default --output json --no-input`

### `mammoth billing stripe portal-url`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_portal_url`
- Agent example: `mammoth billing stripe portal-url --output json --no-input`

### `mammoth billing stripe preview-invoice`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_preview_invoice`
- Agent example: `mammoth billing stripe preview-invoice --output json --no-input`

### `mammoth billing stripe retry-payment`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_retry_payment`
- Agent example: `mammoth billing stripe retry-payment --output json --no-input`

### `mammoth billing stripe status`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_status`
- Agent example: `mammoth billing stripe status --output json --no-input`

### `mammoth billing stripe sync`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_sync`
- Agent example: `mammoth billing stripe sync --output json --no-input`

### `mammoth billing stripe upcoming-invoice`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_upcoming_invoice`
- Agent example: `mammoth billing stripe upcoming-invoice --output json --no-input`

### `mammoth billing stripe usage`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_usage`
- Agent example: `mammoth billing stripe usage --output json --no-input`

### `mammoth billing subscription get`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.subscription_get`
- Agent example: `mammoth billing subscription get --output json --no-input`

### `mammoth billing subscription update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.subscription_update`
- Agent example: `mammoth billing subscription update --output json --no-input`

## browse

### `mammoth browse folder`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.browse.BrowseAPI.folder_resources`
- Agent example: `mammoth browse folder --output json --no-input`

### `mammoth browse project`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.browse`
- Agent example: `mammoth browse project --output json --no-input`

### `mammoth browse root`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.browse.BrowseAPI.root`
- Agent example: `mammoth browse root --output json --no-input`

### `mammoth browse workspace`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.browse.BrowseAPI.workspace_resources`
- Agent example: `mammoth browse workspace --output json --no-input`

## capability

### `mammoth capability get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.capability.get`
- Agent example: `mammoth capability get --output json --no-input`

### `mammoth capability list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.capability.list_`
- Agent example: `mammoth capability list --output json --no-input`

## client-app

### `mammoth client-app create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.create`
- Agent example: `mammoth client-app create --output json --no-input`

### `mammoth client-app delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.delete`
- Agent example: `mammoth client-app delete --output json --no-input`

### `mammoth client-app get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.get`
- Agent example: `mammoth client-app get --output json --no-input`

### `mammoth client-app list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.list`
- Agent example: `mammoth client-app list --output json --no-input`

### `mammoth client-app update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.update`
- Agent example: `mammoth client-app update --output json --no-input`

## completion

### `mammoth completion install`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.completion.install`
- Agent example: `mammoth completion install --output json --no-input`

### `mammoth completion show`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.completion.show`
- Agent example: `mammoth completion show --output json --no-input`

## config

### `mammoth config get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.config.get`
- Agent example: `mammoth config get --output json --no-input`

### `mammoth config list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.config.list`
- Agent example: `mammoth config list --output json --no-input`

### `mammoth config path`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.config.path`
- Agent example: `mammoth config path --output json --no-input`

### `mammoth config set`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.config.set`
- Agent example: `mammoth config set --output json --no-input`

## connector

### `mammoth connector active`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.active_connectors`
- Agent example: `mammoth connector active --output json --no-input`

### `mammoth connector ai chat`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.chat`
- Agent example: `mammoth connector ai chat --output json --no-input`

### `mammoth connector ai history`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.history`
- Agent example: `mammoth connector ai history --output json --no-input`

### `mammoth connector ai session list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.session_list`
- Agent example: `mammoth connector ai session list --output json --no-input`

### `mammoth connector ai session messages`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.session_messages`
- Agent example: `mammoth connector ai session messages --output json --no-input`

### `mammoth connector ai submit-column-selection`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.submit_column_selection`
- Agent example: `mammoth connector ai submit-column-selection --output json --no-input`

### `mammoth connector ai submit-credentials`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.submit_credentials`
- Agent example: `mammoth connector ai submit-credentials --output json --no-input`

### `mammoth connector connection create`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.create_connection`
- Agent example: `mammoth connector connection create --output json --no-input`

### `mammoth connector connection delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.delete_connection`
- Agent example: `mammoth connector connection delete --output json --no-input`

### `mammoth connector connection get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.get_connection`
- Agent example: `mammoth connector connection get --output json --no-input`

### `mammoth connector connection list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.list_connections`
- Agent example: `mammoth connector connection list --output json --no-input`

### `mammoth connector connection update`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.update_connection`
- Agent example: `mammoth connector connection update --output json --no-input`

### `mammoth connector ds-config create`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.create_ds_config`
- Agent example: `mammoth connector ds-config create --output json --no-input`

### `mammoth connector ds-config delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.delete_ds_config`
- Agent example: `mammoth connector ds-config delete --output json --no-input`

### `mammoth connector ds-config delete-all`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.ds_config_delete_all`
- Agent example: `mammoth connector ds-config delete-all --output json --no-input`

### `mammoth connector ds-config get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.get_ds_config`
- Agent example: `mammoth connector ds-config get --output json --no-input`

### `mammoth connector ds-config list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.list_ds_configs`
- Agent example: `mammoth connector ds-config list --output json --no-input`

### `mammoth connector ds-config update`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.update_ds_config`
- Agent example: `mammoth connector ds-config update --output json --no-input`

### `mammoth connector get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.get`
- Agent example: `mammoth connector get --output json --no-input`

### `mammoth connector list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.list`
- Agent example: `mammoth connector list --output json --no-input`

### `mammoth connector query generate`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.query_gen`
- Agent example: `mammoth connector query generate --output json --no-input`

### `mammoth connector query status`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.status`
- Agent example: `mammoth connector query status --output json --no-input`

## context

### `mammoth context project clear`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.project.clear`
- Agent example: `mammoth context project clear --output json --no-input`

### `mammoth context project status`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.project.status`
- Agent example: `mammoth context project status --output json --no-input`

### `mammoth context project use`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.project.use`
- Agent example: `mammoth context project use --output json --no-input`

## dashboard

### `mammoth dashboard action`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.action`
- Agent example: `mammoth dashboard action --output json --no-input`

### `mammoth dashboard analytics`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_analytics`
- Agent example: `mammoth dashboard analytics --output json --no-input`

### `mammoth dashboard cancel-generation`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.cancel_generation`
- Agent example: `mammoth dashboard cancel-generation --output json --no-input`

### `mammoth dashboard create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.create`
- Agent example: `mammoth dashboard create --output json --no-input`

### `mammoth dashboard data draft`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_draft_data`
- Agent example: `mammoth dashboard data draft --output json --no-input`

### `mammoth dashboard data published`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_publish_data`
- Agent example: `mammoth dashboard data published --output json --no-input`

### `mammoth dashboard delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.delete`
- Agent example: `mammoth dashboard delete --output json --no-input`

### `mammoth dashboard get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get`
- Agent example: `mammoth dashboard get --output json --no-input`

### `mammoth dashboard get-by-url`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_by_url`
- Agent example: `mammoth dashboard get-by-url --output json --no-input`

### `mammoth dashboard job-by-url`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.job_by_url`
- Agent example: `mammoth dashboard job-by-url --output json --no-input`

### `mammoth dashboard list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.list`
- Agent example: `mammoth dashboard list --output json --no-input`

### `mammoth dashboard published-data-by-url`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_data_by_url`
- Agent example: `mammoth dashboard published-data-by-url --output json --no-input`

### `mammoth dashboard restore`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.restore`
- Agent example: `mammoth dashboard restore --output json --no-input`

### `mammoth dashboard share`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.share`
- Agent example: `mammoth dashboard share --output json --no-input`

### `mammoth dashboard source list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_sources`
- Agent example: `mammoth dashboard source list --output json --no-input`

### `mammoth dashboard trash`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.trash`
- Agent example: `mammoth dashboard trash --output json --no-input`

### `mammoth dashboard update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.update`
- Agent example: `mammoth dashboard update --output json --no-input`

### `mammoth dashboard widget-data`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.widget_data`
- Agent example: `mammoth dashboard widget-data --output json --no-input`

### `mammoth dashboard widget-data-by-url`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.widget_data_by_url`
- Agent example: `mammoth dashboard widget-data-by-url --output json --no-input`

## data-app

### `mammoth data-app active-job`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.active_job`
- Agent example: `mammoth data-app active-job --output json --no-input`

### `mammoth data-app create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.create`
- Agent example: `mammoth data-app create --output json --no-input`

### `mammoth data-app delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.delete`
- Agent example: `mammoth data-app delete --output json --no-input`

### `mammoth data-app get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.get`
- Agent example: `mammoth data-app get --output json --no-input`

### `mammoth data-app job`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.job`
- Agent example: `mammoth data-app job --output json --no-input`

### `mammoth data-app list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.list`
- Agent example: `mammoth data-app list --output json --no-input`

### `mammoth data-app pipeline-changes`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.pipeline_changes`
- Agent example: `mammoth data-app pipeline-changes --output json --no-input`

### `mammoth data-app share`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.share`
- Agent example: `mammoth data-app share --output json --no-input`

### `mammoth data-app update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.update`
- Agent example: `mammoth data-app update --output json --no-input`

### `mammoth data-app upload`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.upload`
- Agent example: `mammoth data-app upload --output json --no-input`

### `mammoth data-app user list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.user_list`
- Agent example: `mammoth data-app user list --output json --no-input`

### `mammoth data-app user remove`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.user_remove`
- Agent example: `mammoth data-app user remove --output json --no-input`

## dataset

### `mammoth dataset bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.bulk_delete`
- Agent example: `mammoth dataset bulk-delete --output json --no-input`

### `mammoth dataset bulk-update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.bulk_update`
- Agent example: `mammoth dataset bulk-update --output json --no-input`

### `mammoth dataset create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.create`
- Agent example: `mammoth dataset create --output json --no-input`

### `mammoth dataset create-from-pdf`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.create_from_pdf`
- Agent example: `mammoth dataset create-from-pdf --output json --no-input`

### `mammoth dataset data`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get_data`
- Agent example: `mammoth dataset data --output json --no-input`

### `mammoth dataset delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.delete`
- Agent example: `mammoth dataset delete --output json --no-input`

### `mammoth dataset file-settings`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get_file_settings`
- Agent example: `mammoth dataset file-settings --output json --no-input`

### `mammoth dataset file-settings undo`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.file_settings_undo`
- Agent example: `mammoth dataset file-settings undo --output json --no-input`

### `mammoth dataset file-settings update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.file_settings_update`
- Agent example: `mammoth dataset file-settings update --output json --no-input`

### `mammoth dataset get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get`
- Agent example: `mammoth dataset get --output json --no-input`

### `mammoth dataset list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.list`
- Agent example: `mammoth dataset list --output json --no-input`

### `mammoth dataset rename`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.rename`
- Agent example: `mammoth dataset rename --output json --no-input`

### `mammoth dataset restore`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.restore`
- Agent example: `mammoth dataset restore --output json --no-input`

### `mammoth dataset trash`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.trash`
- Agent example: `mammoth dataset trash --output json --no-input`

### `mammoth dataset update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.update`
- Agent example: `mammoth dataset update --output json --no-input`

## doctor

### `mammoth doctor`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.doctor.run`
- Agent example: `mammoth doctor --output json --no-input`

## external-key

### `mammoth external-key create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.external_keys.ExternalKeysAPI.create`
- Agent example: `mammoth external-key create --output json --no-input`

### `mammoth external-key delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.external_keys.ExternalKeysAPI.delete`
- Agent example: `mammoth external-key delete --output json --no-input`

### `mammoth external-key get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.external_keys.ExternalKeysAPI.get`
- Agent example: `mammoth external-key get --output json --no-input`

### `mammoth external-key list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.external_keys.ExternalKeysAPI.list`
- Agent example: `mammoth external-key list --output json --no-input`

## file

### `mammoth file bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.files.FilesAPI.bulk_delete`
- Agent example: `mammoth file bulk-delete --output json --no-input`

### `mammoth file delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.files.FilesAPI.delete`
- Agent example: `mammoth file delete --output json --no-input`

### `mammoth file extract-sheets`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.extract_sheets`
- Agent example: `mammoth file extract-sheets --output json --no-input`

### `mammoth file get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.get`
- Agent example: `mammoth file get --output json --no-input`

### `mammoth file list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.list`
- Agent example: `mammoth file list --output json --no-input`

### `mammoth file set-password`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.files.FilesAPI.set_password`
- Agent example: `mammoth file set-password --output json --no-input`

### `mammoth file update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.update`
- Agent example: `mammoth file update --output json --no-input`

### `mammoth file upload`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.upload`
- Agent example: `mammoth file upload --output json --no-input`

### `mammoth file upload-folder`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.upload_folder`
- Agent example: `mammoth file upload-folder --output json --no-input`

## folder

### `mammoth folder bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.folders.FoldersAPI.bulk_delete`
- Agent example: `mammoth folder bulk-delete --output json --no-input`

### `mammoth folder create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.create`
- Agent example: `mammoth folder create --output json --no-input`

### `mammoth folder delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.folders.FoldersAPI.delete`
- Agent example: `mammoth folder delete --output json --no-input`

### `mammoth folder get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.get`
- Agent example: `mammoth folder get --output json --no-input`

### `mammoth folder list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.list`
- Agent example: `mammoth folder list --output json --no-input`

### `mammoth folder move`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.move`
- Agent example: `mammoth folder move --output json --no-input`

### `mammoth folder root`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.get_project_root`
- Agent example: `mammoth folder root --output json --no-input`

### `mammoth folder trash`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.trash`
- Agent example: `mammoth folder trash --output json --no-input`

### `mammoth folder update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.update`
- Agent example: `mammoth folder update --output json --no-input`

## job

### `mammoth job get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.get_job`
- Agent example: `mammoth job get --output json --no-input`

### `mammoth job get-many`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.get_jobs`
- Agent example: `mammoth job get-many --output json --no-input`

### `mammoth job wait`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.wait_for_job`
- Agent example: `mammoth job wait --output json --no-input`

### `mammoth job wait-many`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.wait_for_jobs`
- Agent example: `mammoth job wait-many --output json --no-input`

## notification

### `mammoth notification delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.delete`
- Agent example: `mammoth notification delete --output json --no-input`

### `mammoth notification delete-batch`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.delete_batch`
- Agent example: `mammoth notification delete-batch --output json --no-input`

### `mammoth notification list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.list`
- Agent example: `mammoth notification list --output json --no-input`

### `mammoth notification update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.update`
- Agent example: `mammoth notification update --output json --no-input`

### `mammoth notification update-batch`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.update_batch`
- Agent example: `mammoth notification update-batch --output json --no-input`

## parameter

### `mammoth parameter create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.create`
- Agent example: `mammoth parameter create --output json --no-input`

### `mammoth parameter delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.delete`
- Agent example: `mammoth parameter delete --output json --no-input`

### `mammoth parameter dependencies`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.dependencies`
- Agent example: `mammoth parameter dependencies --output json --no-input`

### `mammoth parameter duplicate`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.duplicate`
- Agent example: `mammoth parameter duplicate --output json --no-input`

### `mammoth parameter get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.get`
- Agent example: `mammoth parameter get --output json --no-input`

### `mammoth parameter group create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_create`
- Agent example: `mammoth parameter group create --output json --no-input`

### `mammoth parameter group delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_delete`
- Agent example: `mammoth parameter group delete --output json --no-input`

### `mammoth parameter group list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_list`
- Agent example: `mammoth parameter group list --output json --no-input`

### `mammoth parameter group reorder`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_reorder`
- Agent example: `mammoth parameter group reorder --output json --no-input`

### `mammoth parameter group update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_update`
- Agent example: `mammoth parameter group update --output json --no-input`

### `mammoth parameter list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.list`
- Agent example: `mammoth parameter list --output json --no-input`

### `mammoth parameter rerun`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.rerun`
- Agent example: `mammoth parameter rerun --output json --no-input`

### `mammoth parameter rerun-all-stale`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.rerun_all_stale`
- Agent example: `mammoth parameter rerun-all-stale --output json --no-input`

### `mammoth parameter update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.update`
- Agent example: `mammoth parameter update --output json --no-input`

## project

### `mammoth project bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.bulk_delete`
- Agent example: `mammoth project bulk-delete --output json --no-input`

### `mammoth project bulk-update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.bulk_update`
- Agent example: `mammoth project bulk-update --output json --no-input`

### `mammoth project checkpoint list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.checkpoint_list`
- Agent example: `mammoth project checkpoint list --output json --no-input`

### `mammoth project create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.create`
- Agent example: `mammoth project create --output json --no-input`

### `mammoth project data-check list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.data_check_list`
- Agent example: `mammoth project data-check list --output json --no-input`

### `mammoth project delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.delete`
- Agent example: `mammoth project delete --output json --no-input`

### `mammoth project get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.get`
- Agent example: `mammoth project get --output json --no-input`

### `mammoth project list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.list`
- Agent example: `mammoth project list --output json --no-input`

### `mammoth project pending-changes`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.pending_changes`
- Agent example: `mammoth project pending-changes --output json --no-input`

### `mammoth project publish-credentials`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.publish_credentials`
- Agent example: `mammoth project publish-credentials --output json --no-input`

### `mammoth project resource-dependencies`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.resource_dependencies`
- Agent example: `mammoth project resource-dependencies --output json --no-input`

### `mammoth project resource-status`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.resource_status`
- Agent example: `mammoth project resource-status --output json --no-input`

### `mammoth project sample-flow`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.sample_flow`
- Agent example: `mammoth project sample-flow --output json --no-input`

### `mammoth project update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.update`
- Agent example: `mammoth project update --output json --no-input`

### `mammoth project user add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.add_users`
- Agent example: `mammoth project user add --output json --no-input`

### `mammoth project user remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.remove_users`
- Agent example: `mammoth project user remove --output json --no-input`

### `mammoth project user update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.user_update`
- Agent example: `mammoth project user update --output json --no-input`

## report

### `mammoth report list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.reports.ReportsAPI.list`
- Agent example: `mammoth report list --output json --no-input`

## schedule

### `mammoth schedule create`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.create`
- Agent example: `mammoth schedule create --output json --no-input`

### `mammoth schedule delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.delete`
- Agent example: `mammoth schedule delete --output json --no-input`

### `mammoth schedule get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.get`
- Agent example: `mammoth schedule get --output json --no-input`

### `mammoth schedule list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.list`
- Agent example: `mammoth schedule list --output json --no-input`

### `mammoth schedule update`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.update`
- Agent example: `mammoth schedule update --output json --no-input`

## schema

### `mammoth schema get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.schema.get`
- Agent example: `mammoth schema get --output json --no-input`

### `mammoth schema list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.schema.list_`
- Agent example: `mammoth schema list --output json --no-input`

## skill

### `mammoth skill install`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.skills.installer.install`
- Agent example: `mammoth skill install --output json --no-input`

### `mammoth skill list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.skills.installer.list_`
- Agent example: `mammoth skill list --output json --no-input`

### `mammoth skill path`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.skills.installer.path`
- Agent example: `mammoth skill path --output json --no-input`

### `mammoth skill uninstall`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.skills.installer.uninstall`
- Agent example: `mammoth skill uninstall --output json --no-input`

### `mammoth skill update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.skills.installer.update`
- Agent example: `mammoth skill update --output json --no-input`

## snippet

### `mammoth snippet create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.create`
- Agent example: `mammoth snippet create --output json --no-input`

### `mammoth snippet delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.delete`
- Agent example: `mammoth snippet delete --output json --no-input`

### `mammoth snippet dependencies`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.dependencies`
- Agent example: `mammoth snippet dependencies --output json --no-input`

### `mammoth snippet duplicate`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.duplicate`
- Agent example: `mammoth snippet duplicate --output json --no-input`

### `mammoth snippet get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.get`
- Agent example: `mammoth snippet get --output json --no-input`

### `mammoth snippet list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.list`
- Agent example: `mammoth snippet list --output json --no-input`

### `mammoth snippet rerun`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.rerun`
- Agent example: `mammoth snippet rerun --output json --no-input`

### `mammoth snippet update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.update`
- Agent example: `mammoth snippet update --output json --no-input`

## support

### `mammoth support connector create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_create`
- Agent example: `mammoth support connector create --output json --no-input`

### `mammoth support connector delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_delete`
- Agent example: `mammoth support connector delete --output json --no-input`

### `mammoth support connector list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_list`
- Agent example: `mammoth support connector list --output json --no-input`

### `mammoth support connector update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_update`
- Agent example: `mammoth support connector update --output json --no-input`

### `mammoth support connector-profile add-connector`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_add_connector`
- Agent example: `mammoth support connector-profile add-connector --output json --no-input`

### `mammoth support connector-profile create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_create`
- Agent example: `mammoth support connector-profile create --output json --no-input`

### `mammoth support connector-profile delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_delete`
- Agent example: `mammoth support connector-profile delete --output json --no-input`

### `mammoth support connector-profile list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_list`
- Agent example: `mammoth support connector-profile list --output json --no-input`

### `mammoth support connector-profile update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_update`
- Agent example: `mammoth support connector-profile update --output json --no-input`

### `mammoth support feature create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_create`
- Agent example: `mammoth support feature create --output json --no-input`

### `mammoth support feature delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_delete`
- Agent example: `mammoth support feature delete --output json --no-input`

### `mammoth support feature list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_list`
- Agent example: `mammoth support feature list --output json --no-input`

### `mammoth support feature update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_update`
- Agent example: `mammoth support feature update --output json --no-input`

### `mammoth support feature-profile add-feature`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_add_feature`
- Agent example: `mammoth support feature-profile add-feature --output json --no-input`

### `mammoth support feature-profile create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_create`
- Agent example: `mammoth support feature-profile create --output json --no-input`

### `mammoth support feature-profile delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_delete`
- Agent example: `mammoth support feature-profile delete --output json --no-input`

### `mammoth support feature-profile list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_list`
- Agent example: `mammoth support feature-profile list --output json --no-input`

### `mammoth support feature-profile update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_update`
- Agent example: `mammoth support feature-profile update --output json --no-input`

### `mammoth support ownership transfer`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.ownership_transfer`
- Agent example: `mammoth support ownership transfer --output json --no-input`

### `mammoth support plan archive`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_archive`
- Agent example: `mammoth support plan archive --output json --no-input`

### `mammoth support plan chargebee-list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_chargebee_list`
- Agent example: `mammoth support plan chargebee-list --output json --no-input`

### `mammoth support plan create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_create`
- Agent example: `mammoth support plan create --output json --no-input`

### `mammoth support plan delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_delete`
- Agent example: `mammoth support plan delete --output json --no-input`

### `mammoth support plan get`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_get`
- Agent example: `mammoth support plan get --output json --no-input`

### `mammoth support plan list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_list`
- Agent example: `mammoth support plan list --output json --no-input`

### `mammoth support plan self-serve-list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_self_serve_list`
- Agent example: `mammoth support plan self-serve-list --output json --no-input`

### `mammoth support plan update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_update`
- Agent example: `mammoth support plan update --output json --no-input`

### `mammoth support plan update-storage-tiers`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_update_storage_tiers`
- Agent example: `mammoth support plan update-storage-tiers --output json --no-input`

### `mammoth support subscription create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_create`
- Agent example: `mammoth support subscription create --output json --no-input`

### `mammoth support subscription get`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_get`
- Agent example: `mammoth support subscription get --output json --no-input`

### `mammoth support subscription update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_update`
- Agent example: `mammoth support subscription update --output json --no-input`

### `mammoth support user list-all`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.user_list_all`
- Agent example: `mammoth support user list-all --output json --no-input`

### `mammoth support user register`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.user_register`
- Agent example: `mammoth support user register --output json --no-input`

### `mammoth support user update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.user_update`
- Agent example: `mammoth support user update --output json --no-input`

### `mammoth support workspace create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_create`
- Agent example: `mammoth support workspace create --output json --no-input`

### `mammoth support workspace delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_delete`
- Agent example: `mammoth support workspace delete --output json --no-input`

### `mammoth support workspace get`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_get`
- Agent example: `mammoth support workspace get --output json --no-input`

### `mammoth support workspace list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_list`
- Agent example: `mammoth support workspace list --output json --no-input`

### `mammoth support workspace restore-access`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_restore_access`
- Agent example: `mammoth support workspace restore-access --output json --no-input`

### `mammoth support workspace suspend-access`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_suspend_access`
- Agent example: `mammoth support workspace suspend-access --output json --no-input`

### `mammoth support workspace update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_update`
- Agent example: `mammoth support workspace update --output json --no-input`

### `mammoth support workspace user add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_add`
- Agent example: `mammoth support workspace user add --output json --no-input`

### `mammoth support workspace user list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_list`
- Agent example: `mammoth support workspace user list --output json --no-input`

### `mammoth support workspace user remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_remove`
- Agent example: `mammoth support workspace user remove --output json --no-input`

### `mammoth support workspace user transfer`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_transfer`
- Agent example: `mammoth support workspace user transfer --output json --no-input`

## template

### `mammoth template create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.create`
- Agent example: `mammoth template create --output json --no-input`

### `mammoth template delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.delete`
- Agent example: `mammoth template delete --output json --no-input`

### `mammoth template get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.get`
- Agent example: `mammoth template get --output json --no-input`

### `mammoth template list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.list`
- Agent example: `mammoth template list --output json --no-input`

### `mammoth template update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.update`
- Agent example: `mammoth template update --output json --no-input`

## trash

### `mammoth trash add`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.trash.TrashAPI.add`
- Agent example: `mammoth trash add --output json --no-input`

### `mammoth trash list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.trash.TrashAPI.list`
- Agent example: `mammoth trash list --output json --no-input`

### `mammoth trash restore`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.trash.TrashAPI.restore`
- Agent example: `mammoth trash restore --output json --no-input`

## user

### `mammoth user avatar delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.users.UsersAPI.avatar_delete`
- Agent example: `mammoth user avatar delete --output json --no-input`

### `mammoth user avatar upload`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.users.UsersAPI.avatar_upload`
- Agent example: `mammoth user avatar upload --output json --no-input`

### `mammoth user change-password`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.user_profile.UserProfileAPI.change_password`
- Agent example: `mammoth user change-password --output json --no-input`

### `mammoth user delete-account`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.users.UsersAPI.delete_account`
- Agent example: `mammoth user delete-account --output json --no-input`

### `mammoth user get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.user_profile.UserProfileAPI.get`
- Agent example: `mammoth user get --output json --no-input`

### `mammoth user preference get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.user_profile.UserProfileAPI.get_preferences`
- Agent example: `mammoth user preference get --output json --no-input`

### `mammoth user preference update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.user_profile.UserProfileAPI.update_preferences`
- Agent example: `mammoth user preference update --output json --no-input`

### `mammoth user update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.user_profile.UserProfileAPI.update`
- Agent example: `mammoth user update --output json --no-input`

## version

### `mammoth version`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.meta.version`
- Agent example: `mammoth version --output json --no-input`

## view

### `mammoth view active-user list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.active_users`
- Agent example: `mammoth view active-user list --output json --no-input`

### `mammoth view active-user mark`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.mark_active`
- Agent example: `mammoth view active-user mark --output json --no-input`

### `mammoth view ai generate-data`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.generate_data`
- Agent example: `mammoth view ai generate-data --output json --no-input`

### `mammoth view ai generation-info`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.get_data_gen_info`
- Agent example: `mammoth view ai generation-info --output json --no-input`

### `mammoth view ai profile`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.generate_profile`
- Agent example: `mammoth view ai profile --output json --no-input`

### `mammoth view bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.bulk_delete`
- Agent example: `mammoth view bulk-delete --output json --no-input`

### `mammoth view checkpoint create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.create`
- Agent example: `mammoth view checkpoint create --output json --no-input`

### `mammoth view checkpoint delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.delete`
- Agent example: `mammoth view checkpoint delete --output json --no-input`

### `mammoth view checkpoint get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.get`
- Agent example: `mammoth view checkpoint get --output json --no-input`

### `mammoth view checkpoint list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.list`
- Agent example: `mammoth view checkpoint list --output json --no-input`

### `mammoth view checkpoint update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.update`
- Agent example: `mammoth view checkpoint update --output json --no-input`

### `mammoth view conditional-format create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_create`
- Agent example: `mammoth view conditional-format create --output json --no-input`

### `mammoth view conditional-format delete-all`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_delete`
- Agent example: `mammoth view conditional-format delete-all --output json --no-input`

### `mammoth view conditional-format list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_list`
- Agent example: `mammoth view conditional-format list --output json --no-input`

### `mammoth view conditional-format update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_update`
- Agent example: `mammoth view conditional-format update --output json --no-input`

### `mammoth view create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.client.ViewsResource.create`
- Agent example: `mammoth view create --output json --no-input`

### `mammoth view data get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.get_data`
- Agent example: `mammoth view data get --output json --no-input`

### `mammoth view data query`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.query_data`
- Agent example: `mammoth view data query --output json --no-input`

### `mammoth view data-check create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.create`
- Agent example: `mammoth view data-check create --output json --no-input`

### `mammoth view data-check delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.delete`
- Agent example: `mammoth view data-check delete --output json --no-input`

### `mammoth view data-check get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.get`
- Agent example: `mammoth view data-check get --output json --no-input`

### `mammoth view data-check list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.list`
- Agent example: `mammoth view data-check list --output json --no-input`

### `mammoth view data-check update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.update`
- Agent example: `mammoth view data-check update --output json --no-input`

### `mammoth view delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.client.ViewsResource.delete`
- Agent example: `mammoth view delete --output json --no-input`

### `mammoth view derivative create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.create`
- Agent example: `mammoth view derivative create --output json --no-input`

### `mammoth view derivative data`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.data`
- Agent example: `mammoth view derivative data --output json --no-input`

### `mammoth view derivative delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.delete`
- Agent example: `mammoth view derivative delete --output json --no-input`

### `mammoth view derivative list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.list`
- Agent example: `mammoth view derivative list --output json --no-input`

### `mammoth view derivative update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.update`
- Agent example: `mammoth view derivative update --output json --no-input`

### `mammoth view draft auto-run`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.set_auto_run`
- Agent example: `mammoth view draft auto-run --output json --no-input`

### `mammoth view draft command`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.command`
- Agent example: `mammoth view draft command --output json --no-input`

### `mammoth view draft discard`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.view.View.discard_draft`
- Agent example: `mammoth view draft discard --output json --no-input`

### `mammoth view draft enter`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.enter_draft_mode`
- Agent example: `mammoth view draft enter --output json --no-input`

### `mammoth view draft status`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.is_draft_mode`
- Agent example: `mammoth view draft status --output json --no-input`

### `mammoth view draft submit`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.submit_draft`
- Agent example: `mammoth view draft submit --output json --no-input`

### `mammoth view export create`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.create`
- Agent example: `mammoth view export create --output json --no-input`

### `mammoth view export csv`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.exports.ExportsAPI.to_csv`
- Agent example: `mammoth view export csv --output json --no-input`

### `mammoth view export delete`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.delete`
- Agent example: `mammoth view export delete --output json --no-input`

### `mammoth view export get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.exports.ExportsAPI.get`
- Agent example: `mammoth view export get --output json --no-input`

### `mammoth view export list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.exports.ExportsAPI.list`
- Agent example: `mammoth view export list --output json --no-input`

### `mammoth view export publish-db`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.publish_db`
- Agent example: `mammoth view export publish-db --output json --no-input`

### `mammoth view export publish-db-update`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.publish_db_update`
- Agent example: `mammoth view export publish-db-update --output json --no-input`

### `mammoth view export update`

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.update`
- Agent example: `mammoth view export update --output json --no-input`

### `mammoth view get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.client.ViewsResource.get`
- Agent example: `mammoth view get --output json --no-input`

### `mammoth view list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.list`
- Agent example: `mammoth view list --output json --no-input`

### `mammoth view parameter-context`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.parameter_context`
- Agent example: `mammoth view parameter-context --output json --no-input`

### `mammoth view pipeline edit`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.edit_pipeline`
- Agent example: `mammoth view pipeline edit --output json --no-input`

### `mammoth view pipeline get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.get_pipeline`
- Agent example: `mammoth view pipeline get --output json --no-input`

### `mammoth view pipeline items`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.items`
- Agent example: `mammoth view pipeline items --output json --no-input`

### `mammoth view pipeline rerun`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.rerun`
- Agent example: `mammoth view pipeline rerun --output json --no-input`

### `mammoth view pipeline wait`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.wait_for_pipeline`
- Agent example: `mammoth view pipeline wait --output json --no-input`

### `mammoth view preview`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.preview`
- Agent example: `mammoth view preview --output json --no-input`

### `mammoth view restore`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.restore`
- Agent example: `mammoth view restore --output json --no-input`

### `mammoth view task add`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.add_task`
- Agent example: `mammoth view task add --output json --no-input`

### `mammoth view task delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.delete_task`
- Agent example: `mammoth view task delete --output json --no-input`

### `mammoth view task get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.get_task`
- Agent example: `mammoth view task get --output json --no-input`

### `mammoth view task list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.list_tasks`
- Agent example: `mammoth view task list --output json --no-input`

### `mammoth view task preview`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.preview_task`
- Agent example: `mammoth view task preview --output json --no-input`

### `mammoth view task update`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.update_task`
- Agent example: `mammoth view task update --output json --no-input`

### `mammoth view transform add-column`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.add_column`
- Agent example: `mammoth view transform add-column --output json --no-input`

### `mammoth view transform add-sql`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.add_sql`
- Agent example: `mammoth view transform add-sql --output json --no-input`

### `mammoth view transform ai`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.gen_ai`
- Agent example: `mammoth view transform ai --output json --no-input`

### `mammoth view transform bulk-replace`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.bulk_replace`
- Agent example: `mammoth view transform bulk-replace --output json --no-input`

### `mammoth view transform combine-columns`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.combine_columns`
- Agent example: `mammoth view transform combine-columns --output json --no-input`

### `mammoth view transform convert-type`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.convert_type`
- Agent example: `mammoth view transform convert-type --output json --no-input`

### `mammoth view transform copy-columns`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.copy_columns`
- Agent example: `mammoth view transform copy-columns --output json --no-input`

### `mammoth view transform crosstab`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._aggregate_ops.AggregateOpsMixin.crosstab`
- Agent example: `mammoth view transform crosstab --output json --no-input`

### `mammoth view transform date-diff`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._date_ops.DateOpsMixin.date_diff`
- Agent example: `mammoth view transform date-diff --output json --no-input`

### `mammoth view transform delete-columns`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.delete_columns`
- Agent example: `mammoth view transform delete-columns --output json --no-input`

### `mammoth view transform discard-duplicates`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.discard_duplicates`
- Agent example: `mammoth view transform discard-duplicates --output json --no-input`

### `mammoth view transform extract-date`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._date_ops.DateOpsMixin.extract_date`
- Agent example: `mammoth view transform extract-date --output json --no-input`

### `mammoth view transform fill-missing`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.fill_missing`
- Agent example: `mammoth view transform fill-missing --output json --no-input`

### `mammoth view transform filter`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._filter_ops.FilterOpsMixin.filter_rows`
- Agent example: `mammoth view transform filter --output json --no-input`

### `mammoth view transform generate-sql`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.generate_sql`
- Agent example: `mammoth view transform generate-sql --output json --no-input`

### `mammoth view transform increment-date`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._date_ops.DateOpsMixin.increment_date`
- Agent example: `mammoth view transform increment-date --output json --no-input`

### `mammoth view transform join`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.join`
- Agent example: `mammoth view transform join --output json --no-input`

### `mammoth view transform json-extract`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.json_extract`
- Agent example: `mammoth view transform json-extract --output json --no-input`

### `mammoth view transform limit-rows`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.limit_rows`
- Agent example: `mammoth view transform limit-rows --output json --no-input`

### `mammoth view transform lookup`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.lookup`
- Agent example: `mammoth view transform lookup --output json --no-input`

### `mammoth view transform math`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._math_ops.MathOpsMixin.math`
- Agent example: `mammoth view transform math --output json --no-input`

### `mammoth view transform pivot`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._aggregate_ops.AggregateOpsMixin.pivot`
- Agent example: `mammoth view transform pivot --output json --no-input`

### `mammoth view transform replace`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.replace_values`
- Agent example: `mammoth view transform replace --output json --no-input`

### `mammoth view transform set-values`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._filter_ops.FilterOpsMixin.set_values`
- Agent example: `mammoth view transform set-values --output json --no-input`

### `mammoth view transform small-large`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._math_ops.MathOpsMixin.small_large`
- Agent example: `mammoth view transform small-large --output json --no-input`

### `mammoth view transform split`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.split_column`
- Agent example: `mammoth view transform split --output json --no-input`

### `mammoth view transform substring`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.substring`
- Agent example: `mammoth view transform substring --output json --no-input`

### `mammoth view transform text`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.text_transform`
- Agent example: `mammoth view transform text --output json --no-input`

### `mammoth view transform unnest`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.unnest`
- Agent example: `mammoth view transform unnest --output json --no-input`

### `mammoth view transform window`

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._aggregate_ops.AggregateOpsMixin.window`
- Agent example: `mammoth view transform window --output json --no-input`

### `mammoth view trash`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.trash`
- Agent example: `mammoth view trash --output json --no-input`

### `mammoth view update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.update`
- Agent example: `mammoth view update --output json --no-input`

### `mammoth view version apply`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.apply`
- Agent example: `mammoth view version apply --output json --no-input`

### `mammoth view version delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.delete`
- Agent example: `mammoth view version delete --output json --no-input`

### `mammoth view version get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.get`
- Agent example: `mammoth view version get --output json --no-input`

### `mammoth view version list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.list`
- Agent example: `mammoth view version list --output json --no-input`

### `mammoth view version update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.update`
- Agent example: `mammoth view version update --output json --no-input`

## webhook

### `mammoth webhook create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.create`
- Agent example: `mammoth webhook create --output json --no-input`

### `mammoth webhook delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.delete`
- Agent example: `mammoth webhook delete --output json --no-input`

### `mammoth webhook get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.get`
- Agent example: `mammoth webhook get --output json --no-input`

### `mammoth webhook list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.list`
- Agent example: `mammoth webhook list --output json --no-input`

### `mammoth webhook send`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.send_data`
- Agent example: `mammoth webhook send --output json --no-input`

### `mammoth webhook send-get`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.send_data_get`
- Agent example: `mammoth webhook send-get --output json --no-input`

### `mammoth webhook update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.update`
- Agent example: `mammoth webhook update --output json --no-input`

## workflow

### `mammoth workflow block add`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_add`
- Agent example: `mammoth workflow block add --output json --no-input`

### `mammoth workflow block auth`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_auth`
- Agent example: `mammoth workflow block auth --output json --no-input`

### `mammoth workflow block config`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_config`
- Agent example: `mammoth workflow block config --output json --no-input`

### `mammoth workflow block type`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_type`
- Agent example: `mammoth workflow block type --output json --no-input`

### `mammoth workflow canvas`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.canvas`
- Agent example: `mammoth workflow canvas --output json --no-input`

### `mammoth workflow cleanup`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.cleanup`
- Agent example: `mammoth workflow cleanup --output json --no-input`

### `mammoth workflow create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.create`
- Agent example: `mammoth workflow create --output json --no-input`

### `mammoth workflow delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.delete`
- Agent example: `mammoth workflow delete --output json --no-input`

### `mammoth workflow from-template`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.from_template`
- Agent example: `mammoth workflow from-template --output json --no-input`

### `mammoth workflow get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.get`
- Agent example: `mammoth workflow get --output json --no-input`

### `mammoth workflow graph`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.graph`
- Agent example: `mammoth workflow graph --output json --no-input`

### `mammoth workflow list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.list`
- Agent example: `mammoth workflow list --output json --no-input`

### `mammoth workflow update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.update`
- Agent example: `mammoth workflow update --output json --no-input`

### `mammoth workflow workspace-datasets`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.workspace_datasets`
- Agent example: `mammoth workflow workspace-datasets --output json --no-input`

### `mammoth workflow workspace-exports`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.workspace_exports`
- Agent example: `mammoth workflow workspace-exports --output json --no-input`

### `mammoth workflow workspace-sources`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.workspace_sources`
- Agent example: `mammoth workflow workspace-sources --output json --no-input`

## workspace

### `mammoth workspace accept-invite`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.accept_invite`
- Agent example: `mammoth workspace accept-invite --output json --no-input`

### `mammoth workspace app-usage`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.app_usage`
- Agent example: `mammoth workspace app-usage --output json --no-input`

### `mammoth workspace check-expression`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.check_expression`
- Agent example: `mammoth workspace check-expression --output json --no-input`

### `mammoth workspace create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.create`
- Agent example: `mammoth workspace create --output json --no-input`

### `mammoth workspace delete`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.delete`
- Agent example: `mammoth workspace delete --output json --no-input`

### `mammoth workspace get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.get`
- Agent example: `mammoth workspace get --output json --no-input`

### `mammoth workspace list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.list`
- Agent example: `mammoth workspace list --output json --no-input`

### `mammoth workspace llm-task`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.llm_task`
- Agent example: `mammoth workspace llm-task --output json --no-input`

### `mammoth workspace reactivate`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.reactivate`
- Agent example: `mammoth workspace reactivate --output json --no-input`

### `mammoth workspace segment list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.segment_list`
- Agent example: `mammoth workspace segment list --output json --no-input`

### `mammoth workspace segment update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.segment_update`
- Agent example: `mammoth workspace segment update --output json --no-input`

### `mammoth workspace storage-breakdown`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.storage_breakdown`
- Agent example: `mammoth workspace storage-breakdown --output json --no-input`

### `mammoth workspace update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.update`
- Agent example: `mammoth workspace update --output json --no-input`

### `mammoth workspace user add`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_add`
- Agent example: `mammoth workspace user add --output json --no-input`

### `mammoth workspace user get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.get_user`
- Agent example: `mammoth workspace user get --output json --no-input`

### `mammoth workspace user list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.list_users`
- Agent example: `mammoth workspace user list --output json --no-input`

### `mammoth workspace user remove`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_remove`
- Agent example: `mammoth workspace user remove --output json --no-input`

### `mammoth workspace user remove-batch`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_remove_batch`
- Agent example: `mammoth workspace user remove-batch --output json --no-input`

### `mammoth workspace user update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.update_user`
- Agent example: `mammoth workspace user update --output json --no-input`

### `mammoth workspace user update-batch`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_update_batch`
- Agent example: `mammoth workspace user update-batch --output json --no-input`
