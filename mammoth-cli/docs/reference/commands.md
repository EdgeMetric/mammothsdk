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

**Arguments**

- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_delete`
- Agent example: `mammoth agent session delete 123 --output json --no-input`

### `mammoth agent session list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_list`
- Agent example: `mammoth agent session list --output json --no-input`

### `mammoth agent session messages`

**Arguments**

- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_messages`
- Agent example: `mammoth agent session messages 123 --output json --no-input`

### `mammoth agent session set-visibility`

**Arguments**

- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_set_visibility`
- Agent example: `mammoth agent session set-visibility 123 --output json --no-input`

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

**Arguments**

- `ANNOTATION_ID` (int, required) — ID of the annotation.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.comment_add`
- Agent example: `mammoth annotation comment add 123 --output json --no-input`

### `mammoth annotation create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.create`
- Agent example: `mammoth annotation create --output json --no-input`

### `mammoth annotation delete`

**Arguments**

- `ANNOTATION_ID` (int, required) — ID of the annotation.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.delete`
- Agent example: `mammoth annotation delete 123 --output json --no-input`

### `mammoth annotation list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.list`
- Agent example: `mammoth annotation list --output json --no-input`

### `mammoth annotation update`

**Arguments**

- `ANNOTATION_ID` (int, required) — ID of the annotation.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.update`
- Agent example: `mammoth annotation update 123 --output json --no-input`

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

**Arguments**

- `AUTOMATION_ID` (int, required) — ID of the automation.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.delete`
- Agent example: `mammoth automation delete 123 --output json --no-input`

### `mammoth automation get`

**Arguments**

- `AUTOMATION_ID` (int, required) — ID of the automation.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.get`
- Agent example: `mammoth automation get 123 --output json --no-input`

### `mammoth automation list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.list`
- Agent example: `mammoth automation list --output json --no-input`

### `mammoth automation restore`

**Arguments**

- `AUTOMATION_ID` (int, required) — ID of the automation.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.restore`
- Agent example: `mammoth automation restore 123 --output json --no-input`

### `mammoth automation trash`

**Arguments**

- `AUTOMATION_ID` (int, required) — ID of the automation.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.trash`
- Agent example: `mammoth automation trash 123 --output json --no-input`

### `mammoth automation update`

**Arguments**

- `AUTOMATION_ID` (int, required) — ID of the automation.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.update`
- Agent example: `mammoth automation update 123 --output json --no-input`

## batch

### `mammoth batch bulk-delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.batches.BatchesAPI.bulk_delete`
- Agent example: `mammoth batch bulk-delete 123 --output json --no-input`

### `mammoth batch create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `SOURCE_ID` (int, required) — ID of the source.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.create`
- Agent example: `mammoth batch create 123 123 --output json --no-input`

### `mammoth batch delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `BATCH_ID` (int, required) — ID of the batch.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.batches.BatchesAPI.delete`
- Agent example: `mammoth batch delete 123 123 --output json --no-input`

### `mammoth batch get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `BATCH_ID` (int, required) — ID of the batch.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.get`
- Agent example: `mammoth batch get 123 123 --output json --no-input`

### `mammoth batch list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.list`
- Agent example: `mammoth batch list 123 --output json --no-input`

### `mammoth batch update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.batches.BatchesAPI.update`
- Agent example: `mammoth batch update 123 --output json --no-input`

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

**Arguments**

- `INVOICE_ID` (int, required) — ID of the invoice.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.invoice_get`
- Agent example: `mammoth billing invoice get 123 --output json --no-input`

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

**Arguments**

- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_create`
- Agent example: `mammoth billing stripe create 123 --output json --no-input`

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

**Arguments**

- `PAYMENT_METHOD_ID` (int, required) — ID of the payment method.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_delete`
- Agent example: `mammoth billing stripe payment-method delete 123 --output json --no-input`

### `mammoth billing stripe payment-method list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_list`
- Agent example: `mammoth billing stripe payment-method list --output json --no-input`

### `mammoth billing stripe payment-method set-default`

**Arguments**

- `PAYMENT_METHOD_ID` (int, required) — ID of the payment method.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_set_default`
- Agent example: `mammoth billing stripe payment-method set-default 123 --output json --no-input`

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

**Arguments**

- `FOLDER_ID` (int, required) — ID of the folder.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.browse.BrowseAPI.folder_resources`
- Agent example: `mammoth browse folder 123 --output json --no-input`

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

**Arguments**

- `CLIENT_KEY` (str, required) — Key identifying the client.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.delete`
- Agent example: `mammoth client-app delete example --output json --no-input`

### `mammoth client-app get`

**Arguments**

- `CLIENT_KEY` (str, required) — Key identifying the client.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.get`
- Agent example: `mammoth client-app get example --output json --no-input`

### `mammoth client-app list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.list`
- Agent example: `mammoth client-app list --output json --no-input`

### `mammoth client-app update`

**Arguments**

- `CLIENT_KEY` (str, required) — Key identifying the client.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.update`
- Agent example: `mammoth client-app update example --output json --no-input`

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

**Arguments**

- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.history`
- Agent example: `mammoth connector ai history example --output json --no-input`

### `mammoth connector ai session list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.session_list`
- Agent example: `mammoth connector ai session list --output json --no-input`

### `mammoth connector ai session messages`

**Arguments**

- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.session_messages`
- Agent example: `mammoth connector ai session messages 123 --output json --no-input`

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

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.create_connection`
- Agent example: `mammoth connector connection create example --output json --no-input`

### `mammoth connector connection delete`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.delete_connection`
- Agent example: `mammoth connector connection delete example example --output json --no-input`

### `mammoth connector connection get`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.get_connection`
- Agent example: `mammoth connector connection get example example --output json --no-input`

### `mammoth connector connection list`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.list_connections`
- Agent example: `mammoth connector connection list example --output json --no-input`

### `mammoth connector connection update`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.update_connection`
- Agent example: `mammoth connector connection update example example --output json --no-input`

### `mammoth connector ds-config create`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.create_ds_config`
- Agent example: `mammoth connector ds-config create example example --output json --no-input`

### `mammoth connector ds-config delete`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.
- `DS_CONFIG_KEY` (str, required) — Key identifying the ds config.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.delete_ds_config`
- Agent example: `mammoth connector ds-config delete example example example --output json --no-input`

### `mammoth connector ds-config delete-all`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.ds_config_delete_all`
- Agent example: `mammoth connector ds-config delete-all example example --output json --no-input`

### `mammoth connector ds-config get`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.
- `DS_CONFIG_KEY` (str, required) — Key identifying the ds config.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.get_ds_config`
- Agent example: `mammoth connector ds-config get example example example --output json --no-input`

### `mammoth connector ds-config list`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.list_ds_configs`
- Agent example: `mammoth connector ds-config list example example --output json --no-input`

### `mammoth connector ds-config update`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.
- `DS_CONFIG_KEY` (str, required) — Key identifying the ds config.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.update_ds_config`
- Agent example: `mammoth connector ds-config update example example example --output json --no-input`

### `mammoth connector get`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.get`
- Agent example: `mammoth connector get example --output json --no-input`

### `mammoth connector list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.list`
- Agent example: `mammoth connector list --output json --no-input`

### `mammoth connector query generate`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.query_gen`
- Agent example: `mammoth connector query generate example example --output json --no-input`

### `mammoth connector query status`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.
- `CONNECTION_KEY` (str, required) — Key identifying the connection.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.status`
- Agent example: `mammoth connector query status example example --output json --no-input`

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

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.action`
- Agent example: `mammoth dashboard action 123 --output json --no-input`

### `mammoth dashboard analytics`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_analytics`
- Agent example: `mammoth dashboard analytics 123 --output json --no-input`

### `mammoth dashboard cancel-generation`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.cancel_generation`
- Agent example: `mammoth dashboard cancel-generation 123 --output json --no-input`

### `mammoth dashboard create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.create`
- Agent example: `mammoth dashboard create --output json --no-input`

### `mammoth dashboard data draft`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_draft_data`
- Agent example: `mammoth dashboard data draft 123 --output json --no-input`

### `mammoth dashboard data published`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_publish_data`
- Agent example: `mammoth dashboard data published 123 --output json --no-input`

### `mammoth dashboard delete`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.delete`
- Agent example: `mammoth dashboard delete 123 --output json --no-input`

### `mammoth dashboard get`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get`
- Agent example: `mammoth dashboard get 123 --output json --no-input`

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

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.restore`
- Agent example: `mammoth dashboard restore 123 --output json --no-input`

### `mammoth dashboard share`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.share`
- Agent example: `mammoth dashboard share 123 --output json --no-input`

### `mammoth dashboard source list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_sources`
- Agent example: `mammoth dashboard source list --output json --no-input`

### `mammoth dashboard trash`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.trash`
- Agent example: `mammoth dashboard trash 123 --output json --no-input`

### `mammoth dashboard update`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.update`
- Agent example: `mammoth dashboard update 123 --output json --no-input`

### `mammoth dashboard widget-data`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.widget_data`
- Agent example: `mammoth dashboard widget-data 123 --output json --no-input`

### `mammoth dashboard widget-data-by-url`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.widget_data_by_url`
- Agent example: `mammoth dashboard widget-data-by-url --output json --no-input`

## data-app

### `mammoth data-app active-job`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.active_job`
- Agent example: `mammoth data-app active-job 123 --output json --no-input`

### `mammoth data-app create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.create`
- Agent example: `mammoth data-app create --output json --no-input`

### `mammoth data-app delete`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.delete`
- Agent example: `mammoth data-app delete 123 --output json --no-input`

### `mammoth data-app get`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.get`
- Agent example: `mammoth data-app get 123 --output json --no-input`

### `mammoth data-app job`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.
- `JOB_ID` (int, required) — ID of the job.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.job`
- Agent example: `mammoth data-app job 123 123 --output json --no-input`

### `mammoth data-app list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.list`
- Agent example: `mammoth data-app list --output json --no-input`

### `mammoth data-app pipeline-changes`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.pipeline_changes`
- Agent example: `mammoth data-app pipeline-changes 123 --output json --no-input`

### `mammoth data-app share`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.share`
- Agent example: `mammoth data-app share 123 --output json --no-input`

### `mammoth data-app update`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.update`
- Agent example: `mammoth data-app update 123 --output json --no-input`

### `mammoth data-app upload`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.upload`
- Agent example: `mammoth data-app upload 123 --output json --no-input`

### `mammoth data-app user list`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.user_list`
- Agent example: `mammoth data-app user list 123 --output json --no-input`

### `mammoth data-app user remove`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.user_remove`
- Agent example: `mammoth data-app user remove 123 --output json --no-input`

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

**Arguments**

- `FILE_OBJECT_ID` (int, required) — ID of the file object.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.create_from_pdf`
- Agent example: `mammoth dataset create-from-pdf 123 --output json --no-input`

### `mammoth dataset data`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get_data`
- Agent example: `mammoth dataset data 123 --output json --no-input`

### `mammoth dataset delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.delete`
- Agent example: `mammoth dataset delete 123 --output json --no-input`

### `mammoth dataset file-settings`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get_file_settings`
- Agent example: `mammoth dataset file-settings 123 --output json --no-input`

### `mammoth dataset file-settings undo`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.file_settings_undo`
- Agent example: `mammoth dataset file-settings undo 123 --output json --no-input`

### `mammoth dataset file-settings update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.file_settings_update`
- Agent example: `mammoth dataset file-settings update 123 --output json --no-input`

### `mammoth dataset get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get`
- Agent example: `mammoth dataset get 123 --output json --no-input`

### `mammoth dataset list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.list`
- Agent example: `mammoth dataset list --output json --no-input`

### `mammoth dataset rename`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.rename`
- Agent example: `mammoth dataset rename 123 --output json --no-input`

### `mammoth dataset restore`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.restore`
- Agent example: `mammoth dataset restore 123 --output json --no-input`

### `mammoth dataset trash`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.trash`
- Agent example: `mammoth dataset trash 123 --output json --no-input`

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

**Arguments**

- `KEY_ID` (int, required) — ID of the key.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.external_keys.ExternalKeysAPI.delete`
- Agent example: `mammoth external-key delete 123 --output json --no-input`

### `mammoth external-key get`

**Arguments**

- `KEY_ID` (int, required) — ID of the key.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.external_keys.ExternalKeysAPI.get`
- Agent example: `mammoth external-key get 123 --output json --no-input`

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

**Arguments**

- `FILE_ID` (int, required) — ID of the file.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.files.FilesAPI.delete`
- Agent example: `mammoth file delete 123 --output json --no-input`

### `mammoth file extract-sheets`

**Arguments**

- `FILE_ID` (int, required) — ID of the file.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.extract_sheets`
- Agent example: `mammoth file extract-sheets 123 --output json --no-input`

### `mammoth file get`

**Arguments**

- `FILE_ID` (int, required) — ID of the file.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.get`
- Agent example: `mammoth file get 123 --output json --no-input`

### `mammoth file list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.list`
- Agent example: `mammoth file list --output json --no-input`

### `mammoth file set-password`

**Arguments**

- `FILE_ID` (int, required) — ID of the file.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.files.FilesAPI.set_password`
- Agent example: `mammoth file set-password 123 --output json --no-input`

### `mammoth file update`

**Arguments**

- `FILE_ID` (int, required) — ID of the file.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.update`
- Agent example: `mammoth file update 123 --output json --no-input`

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

**Arguments**

- `FOLDER_ID` (int, required) — ID of the folder.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.get`
- Agent example: `mammoth folder get 123 --output json --no-input`

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

**Arguments**

- `FOLDER_ID` (int, required) — ID of the folder.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.trash`
- Agent example: `mammoth folder trash 123 --output json --no-input`

### `mammoth folder update`

**Arguments**

- `FOLDER_ID` (int, required) — ID of the folder.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.update`
- Agent example: `mammoth folder update 123 --output json --no-input`

## job

### `mammoth job get`

**Arguments**

- `JOB_ID` (int, required) — ID of the job.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.get_job`
- Agent example: `mammoth job get 123 --output json --no-input`

### `mammoth job get-many`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.get_jobs`
- Agent example: `mammoth job get-many --output json --no-input`

### `mammoth job wait`

**Arguments**

- `JOB_ID` (int, required) — ID of the job.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.wait_for_job`
- Agent example: `mammoth job wait 123 --output json --no-input`

### `mammoth job wait-many`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.jobs.JobsAPI.wait_for_jobs`
- Agent example: `mammoth job wait-many --output json --no-input`

## notification

### `mammoth notification delete`

**Arguments**

- `NOTIFICATION_ID` (int, required) — ID of the notification.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.delete`
- Agent example: `mammoth notification delete 123 --output json --no-input`

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

**Arguments**

- `NOTIFICATION_ID` (int, required) — ID of the notification.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.update`
- Agent example: `mammoth notification update 123 --output json --no-input`

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

**Arguments**

- `PARAMETER_ID` (int, required) — ID of the parameter.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.delete`
- Agent example: `mammoth parameter delete 123 --output json --no-input`

### `mammoth parameter dependencies`

**Arguments**

- `PARAMETER_ID` (int, required) — ID of the parameter.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.dependencies`
- Agent example: `mammoth parameter dependencies 123 --output json --no-input`

### `mammoth parameter duplicate`

**Arguments**

- `PARAMETER_ID` (int, required) — ID of the parameter.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.duplicate`
- Agent example: `mammoth parameter duplicate 123 --output json --no-input`

### `mammoth parameter get`

**Arguments**

- `PARAMETER_ID` (int, required) — ID of the parameter.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.get`
- Agent example: `mammoth parameter get 123 --output json --no-input`

### `mammoth parameter group create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_create`
- Agent example: `mammoth parameter group create --output json --no-input`

### `mammoth parameter group delete`

**Arguments**

- `GROUP_ID` (int, required) — ID of the group.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_delete`
- Agent example: `mammoth parameter group delete 123 --output json --no-input`

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

**Arguments**

- `GROUP_ID` (int, required) — ID of the group.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_update`
- Agent example: `mammoth parameter group update 123 --output json --no-input`

### `mammoth parameter list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.list`
- Agent example: `mammoth parameter list --output json --no-input`

### `mammoth parameter rerun`

**Arguments**

- `PARAMETER_ID` (int, required) — ID of the parameter.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.rerun`
- Agent example: `mammoth parameter rerun 123 --output json --no-input`

### `mammoth parameter rerun-all-stale`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.rerun_all_stale`
- Agent example: `mammoth parameter rerun-all-stale --output json --no-input`

### `mammoth parameter update`

**Arguments**

- `PARAMETER_ID` (int, required) — ID of the parameter.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.update`
- Agent example: `mammoth parameter update 123 --output json --no-input`

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

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.checkpoint_list`
- Agent example: `mammoth project checkpoint list 123 --output json --no-input`

### `mammoth project create`

**Arguments**

- `NAME` (str, optional) — Name of the new project; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.create`
- Agent example: `mammoth project create example --output json --no-input`

### `mammoth project data-check list`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.data_check_list`
- Agent example: `mammoth project data-check list 123 --output json --no-input`

### `mammoth project delete`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.delete`
- Agent example: `mammoth project delete 123 --output json --no-input`

### `mammoth project get`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.get`
- Agent example: `mammoth project get 123 --output json --no-input`

### `mammoth project list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.list`
- Agent example: `mammoth project list --output json --no-input`

### `mammoth project pending-changes`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.pending_changes`
- Agent example: `mammoth project pending-changes 123 --output json --no-input`

### `mammoth project publish-credentials`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.publish_credentials`
- Agent example: `mammoth project publish-credentials 123 --output json --no-input`

### `mammoth project resource-dependencies`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.resource_dependencies`
- Agent example: `mammoth project resource-dependencies 123 --output json --no-input`

### `mammoth project resource-status`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.resource_status`
- Agent example: `mammoth project resource-status 123 --output json --no-input`

### `mammoth project sample-flow`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.sample_flow`
- Agent example: `mammoth project sample-flow 123 --output json --no-input`

### `mammoth project update`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.update`
- Agent example: `mammoth project update 123 --output json --no-input`

### `mammoth project user add`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.add_users`
- Agent example: `mammoth project user add 123 --output json --no-input`

### `mammoth project user remove`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.remove_users`
- Agent example: `mammoth project user remove 123 --output json --no-input`

### `mammoth project user update`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.user_update`
- Agent example: `mammoth project user update 123 --output json --no-input`

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

**Arguments**

- `SCHEDULE_ID` (int, required) — ID of the schedule.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.delete`
- Agent example: `mammoth schedule delete 123 --output json --no-input`

### `mammoth schedule get`

**Arguments**

- `SCHEDULE_ID` (int, required) — ID of the schedule.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.get`
- Agent example: `mammoth schedule get 123 --output json --no-input`

### `mammoth schedule list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.list`
- Agent example: `mammoth schedule list --output json --no-input`

### `mammoth schedule update`

**Arguments**

- `SCHEDULE_ID` (int, required) — ID of the schedule.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.schedules.SchedulesAPI.update`
- Agent example: `mammoth schedule update 123 --output json --no-input`

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

**Arguments**

- `SNIPPET_ID` (int, required) — ID of the snippet.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.delete`
- Agent example: `mammoth snippet delete 123 --output json --no-input`

### `mammoth snippet dependencies`

**Arguments**

- `SNIPPET_ID` (int, required) — ID of the snippet.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.dependencies`
- Agent example: `mammoth snippet dependencies 123 --output json --no-input`

### `mammoth snippet duplicate`

**Arguments**

- `SNIPPET_ID` (int, required) — ID of the snippet.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.duplicate`
- Agent example: `mammoth snippet duplicate 123 --output json --no-input`

### `mammoth snippet get`

**Arguments**

- `SNIPPET_ID` (int, required) — ID of the snippet.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.get`
- Agent example: `mammoth snippet get 123 --output json --no-input`

### `mammoth snippet list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.list`
- Agent example: `mammoth snippet list --output json --no-input`

### `mammoth snippet rerun`

**Arguments**

- `SNIPPET_ID` (int, required) — ID of the snippet.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.rerun`
- Agent example: `mammoth snippet rerun 123 --output json --no-input`

### `mammoth snippet update`

**Arguments**

- `SNIPPET_ID` (int, required) — ID of the snippet.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.update`
- Agent example: `mammoth snippet update 123 --output json --no-input`

## support

### `mammoth support connector create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_create`
- Agent example: `mammoth support connector create --output json --no-input`

### `mammoth support connector delete`

**Arguments**

- `CONNECTOR_ID` (int, required) — ID of the connector.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_delete`
- Agent example: `mammoth support connector delete 123 --output json --no-input`

### `mammoth support connector list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_list`
- Agent example: `mammoth support connector list --output json --no-input`

### `mammoth support connector update`

**Arguments**

- `CONNECTOR_ID` (int, required) — ID of the connector.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_update`
- Agent example: `mammoth support connector update 123 --output json --no-input`

### `mammoth support connector-profile add-connector`

**Arguments**

- `PROFILE_ID` (int, required) — ID of the profile.
- `CONNECTOR_ID` (int, required) — ID of the connector.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_add_connector`
- Agent example: `mammoth support connector-profile add-connector 123 123 --output json --no-input`

### `mammoth support connector-profile create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_create`
- Agent example: `mammoth support connector-profile create --output json --no-input`

### `mammoth support connector-profile delete`

**Arguments**

- `PROFILE_ID` (int, required) — ID of the profile.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_delete`
- Agent example: `mammoth support connector-profile delete 123 --output json --no-input`

### `mammoth support connector-profile list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_list`
- Agent example: `mammoth support connector-profile list --output json --no-input`

### `mammoth support connector-profile update`

**Arguments**

- `PROFILE_ID` (int, required) — ID of the profile.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_update`
- Agent example: `mammoth support connector-profile update 123 --output json --no-input`

### `mammoth support feature create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_create`
- Agent example: `mammoth support feature create --output json --no-input`

### `mammoth support feature delete`

**Arguments**

- `FEATURE_ID` (int, required) — ID of the feature.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_delete`
- Agent example: `mammoth support feature delete 123 --output json --no-input`

### `mammoth support feature list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_list`
- Agent example: `mammoth support feature list --output json --no-input`

### `mammoth support feature update`

**Arguments**

- `FEATURE_ID` (int, required) — ID of the feature.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_update`
- Agent example: `mammoth support feature update 123 --output json --no-input`

### `mammoth support feature-profile add-feature`

**Arguments**

- `PROFILE_ID` (int, required) — ID of the profile.
- `FEATURE_ID` (int, required) — ID of the feature.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_add_feature`
- Agent example: `mammoth support feature-profile add-feature 123 123 --output json --no-input`

### `mammoth support feature-profile create`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_create`
- Agent example: `mammoth support feature-profile create --output json --no-input`

### `mammoth support feature-profile delete`

**Arguments**

- `PROFILE_ID` (int, required) — ID of the profile.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_delete`
- Agent example: `mammoth support feature-profile delete 123 --output json --no-input`

### `mammoth support feature-profile list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_list`
- Agent example: `mammoth support feature-profile list --output json --no-input`

### `mammoth support feature-profile update`

**Arguments**

- `PROFILE_ID` (int, required) — ID of the profile.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_update`
- Agent example: `mammoth support feature-profile update 123 --output json --no-input`

### `mammoth support ownership transfer`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.
- `USER_ID` (int, required) — ID of the user.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.ownership_transfer`
- Agent example: `mammoth support ownership transfer 123 123 --output json --no-input`

### `mammoth support plan archive`

**Arguments**

- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_archive`
- Agent example: `mammoth support plan archive 123 --output json --no-input`

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

**Arguments**

- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_delete`
- Agent example: `mammoth support plan delete 123 --output json --no-input`

### `mammoth support plan get`

**Arguments**

- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_get`
- Agent example: `mammoth support plan get 123 --output json --no-input`

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

**Arguments**

- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_update`
- Agent example: `mammoth support plan update 123 --output json --no-input`

### `mammoth support plan update-storage-tiers`

**Arguments**

- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_update_storage_tiers`
- Agent example: `mammoth support plan update-storage-tiers 123 --output json --no-input`

### `mammoth support subscription create`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.
- `PLAN_ID` (int, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_create`
- Agent example: `mammoth support subscription create 123 123 --output json --no-input`

### `mammoth support subscription get`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_get`
- Agent example: `mammoth support subscription get 123 --output json --no-input`

### `mammoth support subscription update`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.
- `SUBSCRIPTION_ID` (int, required) — ID of the subscription.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_update`
- Agent example: `mammoth support subscription update 123 123 --output json --no-input`

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

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_delete`
- Agent example: `mammoth support workspace delete 123 --output json --no-input`

### `mammoth support workspace get`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_get`
- Agent example: `mammoth support workspace get 123 --output json --no-input`

### `mammoth support workspace list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_list`
- Agent example: `mammoth support workspace list --output json --no-input`

### `mammoth support workspace restore-access`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_restore_access`
- Agent example: `mammoth support workspace restore-access 123 --output json --no-input`

### `mammoth support workspace suspend-access`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_suspend_access`
- Agent example: `mammoth support workspace suspend-access 123 --output json --no-input`

### `mammoth support workspace update`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_update`
- Agent example: `mammoth support workspace update 123 --output json --no-input`

### `mammoth support workspace user add`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_add`
- Agent example: `mammoth support workspace user add 123 --output json --no-input`

### `mammoth support workspace user list`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_list`
- Agent example: `mammoth support workspace user list 123 --output json --no-input`

### `mammoth support workspace user remove`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.
- `USER_ID` (int, required) — ID of the user.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_remove`
- Agent example: `mammoth support workspace user remove 123 123 --output json --no-input`

### `mammoth support workspace user transfer`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.
- `USER_ID` (int, required) — ID of the user.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_transfer`
- Agent example: `mammoth support workspace user transfer 123 123 --output json --no-input`

## template

### `mammoth template create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.create`
- Agent example: `mammoth template create --output json --no-input`

### `mammoth template delete`

**Arguments**

- `TEMPLATE_ID` (int, required) — ID of the template.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.delete`
- Agent example: `mammoth template delete 123 --output json --no-input`

### `mammoth template get`

**Arguments**

- `TEMPLATE_ID` (int, required) — ID of the template.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.get`
- Agent example: `mammoth template get 123 --output json --no-input`

### `mammoth template list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.list`
- Agent example: `mammoth template list --output json --no-input`

### `mammoth template update`

**Arguments**

- `TEMPLATE_ID` (int, required) — ID of the template.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.update`
- Agent example: `mammoth template update 123 --output json --no-input`

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

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.active_users`
- Agent example: `mammoth view active-user list 123 123 --output json --no-input`

### `mammoth view active-user mark`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.mark_active`
- Agent example: `mammoth view active-user mark 123 123 --output json --no-input`

### `mammoth view ai generate-data`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.generate_data`
- Agent example: `mammoth view ai generate-data 123 --output json --no-input`

### `mammoth view ai generation-info`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.get_data_gen_info`
- Agent example: `mammoth view ai generation-info 123 --output json --no-input`

### `mammoth view ai profile`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.generate_profile`
- Agent example: `mammoth view ai profile 123 --output json --no-input`

### `mammoth view bulk-delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.bulk_delete`
- Agent example: `mammoth view bulk-delete 123 --output json --no-input`

### `mammoth view checkpoint create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.create`
- Agent example: `mammoth view checkpoint create 123 123 --output json --no-input`

### `mammoth view checkpoint delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `CHECKPOINT_ID` (int, required) — ID of the checkpoint.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.delete`
- Agent example: `mammoth view checkpoint delete 123 123 123 --output json --no-input`

### `mammoth view checkpoint get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `CHECKPOINT_ID` (int, required) — ID of the checkpoint.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.get`
- Agent example: `mammoth view checkpoint get 123 123 123 --output json --no-input`

### `mammoth view checkpoint list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.list`
- Agent example: `mammoth view checkpoint list 123 123 --output json --no-input`

### `mammoth view checkpoint update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `CHECKPOINT_ID` (int, required) — ID of the checkpoint.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.update`
- Agent example: `mammoth view checkpoint update 123 123 123 --output json --no-input`

### `mammoth view conditional-format create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_create`
- Agent example: `mammoth view conditional-format create 123 123 --output json --no-input`

### `mammoth view conditional-format delete-all`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_delete`
- Agent example: `mammoth view conditional-format delete-all 123 123 --output json --no-input`

### `mammoth view conditional-format list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_list`
- Agent example: `mammoth view conditional-format list 123 123 --output json --no-input`

### `mammoth view conditional-format update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_update`
- Agent example: `mammoth view conditional-format update 123 123 --output json --no-input`

### `mammoth view create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.client.ViewsResource.create`
- Agent example: `mammoth view create 123 --output json --no-input`

### `mammoth view data get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.get_data`
- Agent example: `mammoth view data get 123 123 --output json --no-input`

### `mammoth view data query`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.query_data`
- Agent example: `mammoth view data query 123 123 --output json --no-input`

### `mammoth view data-check create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.create`
- Agent example: `mammoth view data-check create 123 123 --output json --no-input`

### `mammoth view data-check delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `DATA_CHECK_ID` (int, required) — ID of the data check.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.delete`
- Agent example: `mammoth view data-check delete 123 123 123 --output json --no-input`

### `mammoth view data-check get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `DATA_CHECK_ID` (int, required) — ID of the data check.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.get`
- Agent example: `mammoth view data-check get 123 123 123 --output json --no-input`

### `mammoth view data-check list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.list`
- Agent example: `mammoth view data-check list 123 123 --output json --no-input`

### `mammoth view data-check update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `DATA_CHECK_ID` (int, required) — ID of the data check.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.update`
- Agent example: `mammoth view data-check update 123 123 123 --output json --no-input`

### `mammoth view delete`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.client.ViewsResource.delete`
- Agent example: `mammoth view delete 123 --output json --no-input`

### `mammoth view derivative create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.create`
- Agent example: `mammoth view derivative create 123 123 --output json --no-input`

### `mammoth view derivative data`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `DERIVATIVE_ID` (int, required) — ID of the derivative.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.data`
- Agent example: `mammoth view derivative data 123 123 123 --output json --no-input`

### `mammoth view derivative delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `DERIVATIVE_ID` (int, required) — ID of the derivative.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.delete`
- Agent example: `mammoth view derivative delete 123 123 123 --output json --no-input`

### `mammoth view derivative list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.list`
- Agent example: `mammoth view derivative list 123 123 --output json --no-input`

### `mammoth view derivative update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `DERIVATIVE_ID` (int, required) — ID of the derivative.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.update`
- Agent example: `mammoth view derivative update 123 123 123 --output json --no-input`

### `mammoth view draft auto-run`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.set_auto_run`
- Agent example: `mammoth view draft auto-run 123 --output json --no-input`

### `mammoth view draft command`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.command`
- Agent example: `mammoth view draft command 123 --output json --no-input`

### `mammoth view draft discard`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.view.View.discard_draft`
- Agent example: `mammoth view draft discard 123 --output json --no-input`

### `mammoth view draft enter`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.enter_draft_mode`
- Agent example: `mammoth view draft enter 123 --output json --no-input`

### `mammoth view draft status`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.get_draft_status`
- Agent example: `mammoth view draft status 123 --output json --no-input`

### `mammoth view draft submit`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.submit_draft`
- Agent example: `mammoth view draft submit 123 --output json --no-input`

### `mammoth view export create`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.create`
- Agent example: `mammoth view export create 123 --output json --no-input`

### `mammoth view export csv`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.exports.ExportsAPI.to_csv`
- Agent example: `mammoth view export csv 123 --output json --no-input`

### `mammoth view export delete`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `EXPORT_ID` (int, required) — ID of the export.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.delete`
- Agent example: `mammoth view export delete 123 123 --output json --no-input`

### `mammoth view export get`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `EXPORT_ID` (int, required) — ID of the export.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.exports.ExportsAPI.get`
- Agent example: `mammoth view export get 123 123 --output json --no-input`

### `mammoth view export list`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.exports.ExportsAPI.list`
- Agent example: `mammoth view export list 123 --output json --no-input`

### `mammoth view export publish-db`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.publish_db`
- Agent example: `mammoth view export publish-db 123 --output json --no-input`

### `mammoth view export publish-db-update`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.publish_db_update`
- Agent example: `mammoth view export publish-db-update 123 --output json --no-input`

### `mammoth view export update`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `EXPORT_ID` (int, required) — ID of the export.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.update`
- Agent example: `mammoth view export update 123 123 --output json --no-input`

### `mammoth view get`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.client.ViewsResource.get`
- Agent example: `mammoth view get 123 --output json --no-input`

### `mammoth view list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.list`
- Agent example: `mammoth view list 123 --output json --no-input`

### `mammoth view parameter-context`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.parameter_context`
- Agent example: `mammoth view parameter-context 123 123 --output json --no-input`

### `mammoth view pipeline edit`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.edit_pipeline`
- Agent example: `mammoth view pipeline edit 123 --output json --no-input`

### `mammoth view pipeline get`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.get_pipeline`
- Agent example: `mammoth view pipeline get 123 --output json --no-input`

### `mammoth view pipeline items`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.items`
- Agent example: `mammoth view pipeline items 123 --output json --no-input`

### `mammoth view pipeline rerun`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.rerun`
- Agent example: `mammoth view pipeline rerun 123 --output json --no-input`

### `mammoth view pipeline wait`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.wait_for_pipeline`
- Agent example: `mammoth view pipeline wait 123 --output json --no-input`

### `mammoth view preview`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.preview`
- Agent example: `mammoth view preview 123 123 --output json --no-input`

### `mammoth view restore`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.restore`
- Agent example: `mammoth view restore 123 123 --output json --no-input`

### `mammoth view task add`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.add_task`
- Agent example: `mammoth view task add 123 --output json --no-input`

### `mammoth view task delete`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `TASK_ID` (int, required) — ID of the task.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.delete_task`
- Agent example: `mammoth view task delete 123 123 --output json --no-input`

### `mammoth view task get`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `TASK_ID` (int, required) — ID of the task.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.get_task`
- Agent example: `mammoth view task get 123 123 --output json --no-input`

### `mammoth view task list`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.list_tasks`
- Agent example: `mammoth view task list 123 --output json --no-input`

### `mammoth view task preview`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.preview_task`
- Agent example: `mammoth view task preview 123 --output json --no-input`

### `mammoth view task update`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `TASK_ID` (int, required) — ID of the task.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.update_task`
- Agent example: `mammoth view task update 123 123 --output json --no-input`

### `mammoth view transform add-column`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.add_column`
- Agent example: `mammoth view transform add-column 123 --output json --no-input`

### `mammoth view transform add-sql`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.add_sql`
- Agent example: `mammoth view transform add-sql 123 --output json --no-input`

### `mammoth view transform ai`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.gen_ai`
- Agent example: `mammoth view transform ai 123 --output json --no-input`

### `mammoth view transform bulk-replace`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.bulk_replace`
- Agent example: `mammoth view transform bulk-replace 123 --output json --no-input`

### `mammoth view transform combine-columns`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.combine_columns`
- Agent example: `mammoth view transform combine-columns 123 --output json --no-input`

### `mammoth view transform convert-type`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.convert_type`
- Agent example: `mammoth view transform convert-type 123 --output json --no-input`

### `mammoth view transform copy-columns`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.copy_columns`
- Agent example: `mammoth view transform copy-columns 123 --output json --no-input`

### `mammoth view transform crosstab`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._aggregate_ops.AggregateOpsMixin.crosstab`
- Agent example: `mammoth view transform crosstab 123 --output json --no-input`

### `mammoth view transform date-diff`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._date_ops.DateOpsMixin.date_diff`
- Agent example: `mammoth view transform date-diff 123 --output json --no-input`

### `mammoth view transform delete-columns`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._column_ops.ColumnOpsMixin.delete_columns`
- Agent example: `mammoth view transform delete-columns 123 --output json --no-input`

### `mammoth view transform discard-duplicates`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.discard_duplicates`
- Agent example: `mammoth view transform discard-duplicates 123 --output json --no-input`

### `mammoth view transform extract-date`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._date_ops.DateOpsMixin.extract_date`
- Agent example: `mammoth view transform extract-date 123 --output json --no-input`

### `mammoth view transform fill-missing`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.fill_missing`
- Agent example: `mammoth view transform fill-missing 123 --output json --no-input`

### `mammoth view transform filter`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._filter_ops.FilterOpsMixin.filter_rows`
- Agent example: `mammoth view transform filter 123 --output json --no-input`

### `mammoth view transform generate-sql`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.generate_sql`
- Agent example: `mammoth view transform generate-sql 123 --output json --no-input`

### `mammoth view transform increment-date`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._date_ops.DateOpsMixin.increment_date`
- Agent example: `mammoth view transform increment-date 123 --output json --no-input`

### `mammoth view transform join`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.join`
- Agent example: `mammoth view transform join 123 --output json --no-input`

### `mammoth view transform json-extract`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.json_extract`
- Agent example: `mammoth view transform json-extract 123 --output json --no-input`

### `mammoth view transform limit-rows`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.limit_rows`
- Agent example: `mammoth view transform limit-rows 123 --output json --no-input`

### `mammoth view transform lookup`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._advanced_ops.AdvancedOpsMixin.lookup`
- Agent example: `mammoth view transform lookup 123 --output json --no-input`

### `mammoth view transform math`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._math_ops.MathOpsMixin.math`
- Agent example: `mammoth view transform math 123 --output json --no-input`

### `mammoth view transform pivot`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._aggregate_ops.AggregateOpsMixin.pivot`
- Agent example: `mammoth view transform pivot 123 --output json --no-input`

### `mammoth view transform replace`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.replace_values`
- Agent example: `mammoth view transform replace 123 --output json --no-input`

### `mammoth view transform set-values`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._filter_ops.FilterOpsMixin.set_values`
- Agent example: `mammoth view transform set-values 123 --output json --no-input`

### `mammoth view transform small-large`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._math_ops.MathOpsMixin.small_large`
- Agent example: `mammoth view transform small-large 123 --output json --no-input`

### `mammoth view transform split`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.split_column`
- Agent example: `mammoth view transform split 123 --output json --no-input`

### `mammoth view transform substring`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.substring`
- Agent example: `mammoth view transform substring 123 --output json --no-input`

### `mammoth view transform text`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._text_ops.TextOpsMixin.text_transform`
- Agent example: `mammoth view transform text 123 --output json --no-input`

### `mammoth view transform unnest`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._row_ops.RowOpsMixin.unnest`
- Agent example: `mammoth view transform unnest 123 --output json --no-input`

### `mammoth view transform window`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth._mixins._aggregate_ops.AggregateOpsMixin.window`
- Agent example: `mammoth view transform window 123 --output json --no-input`

### `mammoth view trash`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.trash`
- Agent example: `mammoth view trash 123 123 --output json --no-input`

### `mammoth view update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.update`
- Agent example: `mammoth view update 123 123 --output json --no-input`

### `mammoth view version apply`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `VERSION_ID` (int, required) — ID of the version.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.apply`
- Agent example: `mammoth view version apply 123 123 123 --output json --no-input`

### `mammoth view version delete`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `VERSION_ID` (int, required) — ID of the version.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.delete`
- Agent example: `mammoth view version delete 123 123 123 --output json --no-input`

### `mammoth view version get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `VERSION_ID` (int, required) — ID of the version.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.get`
- Agent example: `mammoth view version get 123 123 123 --output json --no-input`

### `mammoth view version list`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.list`
- Agent example: `mammoth view version list 123 123 --output json --no-input`

### `mammoth view version update`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.
- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `VERSION_ID` (int, required) — ID of the version.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.update`
- Agent example: `mammoth view version update 123 123 123 --output json --no-input`

## webhook

### `mammoth webhook create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.create`
- Agent example: `mammoth webhook create --output json --no-input`

### `mammoth webhook delete`

**Arguments**

- `WEBHOOK_ID` (int, required) — ID of the webhook.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.delete`
- Agent example: `mammoth webhook delete 123 --output json --no-input`

### `mammoth webhook get`

**Arguments**

- `WEBHOOK_ID` (int, required) — ID of the webhook.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.get`
- Agent example: `mammoth webhook get 123 --output json --no-input`

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

**Arguments**

- `WEBHOOK_ID` (int, required) — ID of the webhook.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.update`
- Agent example: `mammoth webhook update 123 --output json --no-input`

## workflow

### `mammoth workflow block add`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_add`
- Agent example: `mammoth workflow block add 123 --output json --no-input`

### `mammoth workflow block auth`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.
- `BLOCK_ID` (int, required) — ID of the block.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_auth`
- Agent example: `mammoth workflow block auth 123 123 --output json --no-input`

### `mammoth workflow block config`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.
- `BLOCK_ID` (int, required) — ID of the block.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_config`
- Agent example: `mammoth workflow block config 123 123 --output json --no-input`

### `mammoth workflow block type`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.
- `BLOCK_ID` (int, required) — ID of the block.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_type`
- Agent example: `mammoth workflow block type 123 123 --output json --no-input`

### `mammoth workflow canvas`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.canvas`
- Agent example: `mammoth workflow canvas 123 --output json --no-input`

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

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.delete`
- Agent example: `mammoth workflow delete 123 --output json --no-input`

### `mammoth workflow from-template`

**Arguments**

- `TEMPLATE_ID` (int, required) — ID of the template.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.from_template`
- Agent example: `mammoth workflow from-template 123 --output json --no-input`

### `mammoth workflow get`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.get`
- Agent example: `mammoth workflow get 123 --output json --no-input`

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

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.update`
- Agent example: `mammoth workflow update 123 --output json --no-input`

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

**Arguments**

- `USER_ID` (int, required) — ID of the user.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.get_user`
- Agent example: `mammoth workspace user get 123 --output json --no-input`

### `mammoth workspace user list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.list_users`
- Agent example: `mammoth workspace user list --output json --no-input`

### `mammoth workspace user remove`

**Arguments**

- `USER_ID` (int, required) — ID of the user.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_remove`
- Agent example: `mammoth workspace user remove 123 --output json --no-input`

### `mammoth workspace user remove-batch`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_remove_batch`
- Agent example: `mammoth workspace user remove-batch --output json --no-input`

### `mammoth workspace user update`

**Arguments**

- `USER_ID` (int, required) — ID of the user.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.update_user`
- Agent example: `mammoth workspace user update 123 --output json --no-input`

### `mammoth workspace user update-batch`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_update_batch`
- Agent example: `mammoth workspace user update-batch --output json --no-input`
