# Command reference

Generated from the reviewed command manifests for mammoth-cli 1.0.6.
Do not edit by hand; run `python scripts/gen_docs.py`.

Total commands: 505.

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
- Agent example: `mammoth addon connector add --input '{"connector_id": 42}' --output json --no-input`

### `mammoth addon connector remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.remove_connector`
- Agent example: `mammoth addon connector remove --input '{"connector_id": 42}' --output json --no-input`

### `mammoth addon list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.addons.AddonsAPI.list`
- Agent example: `mammoth addon list --output json --no-input`

### `mammoth addon storage add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.add_storage`
- Agent example: `mammoth addon storage add --input '{"additional_storage_gb": 1}' --output json --no-input`

### `mammoth addon storage remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.remove_storage`
- Agent example: `mammoth addon storage remove --input '{"removal_storage_gb": 1}' --output json --no-input`

### `mammoth addon user add`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.add_users`
- Agent example: `mammoth addon user add --output json --no-input`

### `mammoth addon user remove`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.addons.AddonsAPI.remove_users`
- Agent example: `mammoth addon user remove --input '{"user_count": 1}' --output json --no-input`

## agent

### `mammoth agent chat`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.chat`
- Agent example: `mammoth agent chat --input '{"message": "example", "scope": {"example": "example"}}' --output json --no-input`

### `mammoth agent session delete`

**Arguments**

- `SESSION_ID` (str, required) — ID of the session.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_delete`
- Agent example: `mammoth agent session delete example --output json --no-input`

### `mammoth agent session list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_list`
- Agent example: `mammoth agent session list --output json --no-input`

### `mammoth agent session messages`

**Arguments**

- `SESSION_ID` (str, required) — ID of the session.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_messages`
- Agent example: `mammoth agent session messages example --output json --no-input`

### `mammoth agent session set-visibility`

**Arguments**

- `SESSION_ID` (str, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.agents.AgentsAPI.session_set_visibility`
- Agent example: `mammoth agent session set-visibility example --input '{"visibility": "example"}' --output json --no-input`

## ai

### `mammoth ai condition generate`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset to generate a condition for.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.condition_generate`
- Agent example: `mammoth ai condition generate 123 --input '{"intent": "example"}' --output json --no-input`

### `mammoth ai expression generate`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset to generate an expression for.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.expression_generate`
- Agent example: `mammoth ai expression generate 123 --input '{"intent": "example", "mode": "example"}' --output json --no-input`

### `mammoth ai sql generate`

**Arguments**

- `INTENT` (str, optional) — Generation intent for the SQL query; or pass it via the 'intent' input field.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.ai.AIAPI.generate_sql`
- Agent example: `mammoth ai sql generate example --output json --no-input`

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
- Agent example: `mammoth annotation comment add 123 --input '{"body": "example"}' --output json --no-input`

### `mammoth annotation create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.annotations.AnnotationsAPI.create`
- Agent example: `mammoth annotation create --input '{"target_type": "example", "target_id": 1, "body": "example"}' --output json --no-input`

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
- Agent example: `mammoth annotation update 123 --input '{"status": "example"}' --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new automation; or pass it via the 'name' input field.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.automations.AutomationsAPI.create`
- Agent example: `mammoth automation create example --input '{"description": "example", "tasks": [{"task_type": "run_data_retrieval"}]}' --output json --no-input`

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
- Agent example: `mammoth automation update 123 --input '{"patch": [{"op": "replace", "path": "details", "value": "example"}]}' --output json --no-input`

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
- Agent example: `mammoth batch create 123 123 --input '{"mapping": {"example": "example"}}' --output json --no-input`

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
- Agent example: `mammoth batch update 123 --input '{"patch": [{"example": "example"}]}' --output json --no-input`

## billing

### `mammoth billing chargebee-plan`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.chargebee_plan`
- Agent example: `mammoth billing chargebee-plan --output json --no-input`

### `mammoth billing hosted-page`

**Arguments**

- `OBJECT_TYPE` (str, optional) — Type of hosted page to generate; or pass it via the 'object_type' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.hosted_page`
- Agent example: `mammoth billing hosted-page example --output json --no-input`

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
- Agent example: `mammoth billing stripe checkout-url --input '{"success_url": "example", "cancel_url": "example"}' --output json --no-input`

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

- `PAYMENT_METHOD_ID` (str, required) — ID of the payment method.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_delete`
- Agent example: `mammoth billing stripe payment-method delete example --output json --no-input`

### `mammoth billing stripe payment-method list`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_list`
- Agent example: `mammoth billing stripe payment-method list --output json --no-input`

### `mammoth billing stripe payment-method set-default`

**Arguments**

- `PAYMENT_METHOD_ID` (str, required) — ID of the payment method.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.billing.BillingAPI.stripe_payment_method_set_default`
- Agent example: `mammoth billing stripe payment-method set-default example --output json --no-input`

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
- Agent example: `mammoth billing subscription update --input '{"patch": [{"example": "example"}]}' --output json --no-input`

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

**Arguments**

- `OPERATION_ID` (str, required) — Operation id to fetch the capability record for (e.g. AddTask).

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.capability.get`
- Agent example: `mammoth capability get AddTask --output json --no-input`

### `mammoth capability list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.capability.list_`
- Agent example: `mammoth capability list --output json --no-input`

## client-app

### `mammoth client-app create`

**Arguments**

- `APP_NAME` (str, optional) — Name of the new client app; or pass it via the 'app_name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.clientapps.ClientAppsAPI.create`
- Agent example: `mammoth client-app create example --output json --no-input`

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
- Agent example: `mammoth client-app update example --input '{"patch_request": {"patch": [{"op": "replace", "path": "role"}]}}' --output json --no-input`

## completion

### `mammoth completion install`

**Arguments**

- `SHELL` (str, optional) — Shell to target (bash/zsh/fish); or pass it via the 'shell' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.completion.install`
- Agent example: `mammoth completion install example --output json --no-input`

### `mammoth completion show`

**Arguments**

- `SHELL` (str, optional) — Shell to target (bash/zsh/fish); or pass it via the 'shell' input field.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.completion.show`
- Agent example: `mammoth completion show example --output json --no-input`

## config

### `mammoth config get`

**Arguments**

- `KEY` (str, required) — Configuration key to read (e.g. output, timeout).

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.config.get`
- Agent example: `mammoth config get output --output json --no-input`

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

**Arguments**

- `KEY` (str, required) — Configuration key to set (e.g. output, timeout).
- `VALUE` (str, required) — New value for the configuration key.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.config.set`
- Agent example: `mammoth config set output text --output json --no-input`

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
- Agent example: `mammoth connector ai chat --input '{"body": {"messages": [{"content": "example", "role": "user"}]}}' --output json --no-input`

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
- Agent example: `mammoth connector ai submit-column-selection --input '{"body": {"selected_columns": ["example"], "session_id": "example"}}' --output json --no-input`

### `mammoth connector ai submit-credentials`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.connector_ai.ConnectorAIAPI.submit_credentials`
- Agent example: `mammoth connector ai submit-credentials --input '{"body": {"credentials": {}, "session_id": "example"}}' --output json --no-input`

### `mammoth connector connection create`

**Arguments**

- `CONNECTOR_KEY` (str, required) — Key identifying the connector.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.connectors.ConnectorsAPI.create_connection`
- Agent example: `mammoth connector connection create example --input '{"config": {"example": "example"}}' --output json --no-input`

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
- Agent example: `mammoth connector connection update example example --input '{"credentials": {"example": "example"}}' --output json --no-input`

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
- Agent example: `mammoth connector ds-config delete-all example example --input '{"config_ids": ["example"]}' --output json --no-input`

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
- Agent example: `mammoth connector ds-config update example example example --input '{"patch": [{"op": "replace", "path": "query", "value": "example"}]}' --output json --no-input`

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
- Agent example: `mammoth connector query generate example example --input '{"prompt": "example"}' --output json --no-input`

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

**Arguments**

- `PROJECT_ID` (int, required) — Positive project id to make active.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.context.project.use`
- Agent example: `mammoth context project use 123 --output json --no-input`

## dashboard

### `mammoth dashboard action`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.action`
- Agent example: `mammoth dashboard action 123 --input '{"action": "sync"}' --output json --no-input`

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

### `mammoth dashboard canvas get`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.canvas_get`
- Agent example: `mammoth dashboard canvas get 123 --output json --no-input`

### `mammoth dashboard canvas restore`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.canvas_restore`
- Agent example: `mammoth dashboard canvas restore 123 --input '{"body": {"params": {"target_sequence": 1}}}' --output json --no-input`

### `mammoth dashboard canvas save`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.canvas_save`
- Agent example: `mammoth dashboard canvas save 123 --input '{"body": {"params": {"canvas": {}}}}' --output json --no-input`

### `mammoth dashboard chat edit`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.chat_edit`
- Agent example: `mammoth dashboard chat edit 123 --input '{"body": {"params": {"prompt": "example"}}}' --output json --no-input`

### `mammoth dashboard chat history`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.chat_history`
- Agent example: `mammoth dashboard chat history 123 --output json --no-input`

### `mammoth dashboard context create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.context_create`
- Agent example: `mammoth dashboard context create --input '{"body": {"params": {"name": "example"}}}' --output json --no-input`

### `mammoth dashboard context delete`

**Arguments**

- `CONTEXT_ID` (str, required) — ID of the context.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.context_delete`
- Agent example: `mammoth dashboard context delete example --output json --no-input`

### `mammoth dashboard context list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.context_list`
- Agent example: `mammoth dashboard context list --output json --no-input`

### `mammoth dashboard context update`

**Arguments**

- `CONTEXT_ID` (str, required) — ID of the context.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.context_update`
- Agent example: `mammoth dashboard context update example --input '{"body": {"params": {"name": "example"}}}' --output json --no-input`

### `mammoth dashboard create`

**Arguments**

- `INTENT` (str, optional) — Generation intent for the new dashboard; or pass it via the 'intent' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.create`
- Agent example: `mammoth dashboard create example --input '{"source": [1]}' --output json --no-input`

### `mammoth dashboard data draft`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_draft_data`
- Agent example: `mammoth dashboard data draft 123 --input '{"sql": "example"}' --output json --no-input`

### `mammoth dashboard data published`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_publish_data`
- Agent example: `mammoth dashboard data published 123 --input '{"sql": "example"}' --output json --no-input`

### `mammoth dashboard delete`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.delete`
- Agent example: `mammoth dashboard delete 123 --output json --no-input`

### `mammoth dashboard descriptor-data`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.descriptor_data`
- Agent example: `mammoth dashboard descriptor-data 123 --input '{"body": {"params": {"descriptor_ids": ["example"]}}}' --output json --no-input`

### `mammoth dashboard duplicate`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.duplicate`
- Agent example: `mammoth dashboard duplicate 123 --output json --no-input`

### `mammoth dashboard figure-intent`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.figure_intent`
- Agent example: `mammoth dashboard figure-intent 123 --input '{"body": {"params": {"intent": "example"}}}' --output json --no-input`

### `mammoth dashboard get`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get`
- Agent example: `mammoth dashboard get 123 --output json --no-input`

### `mammoth dashboard get-by-url`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_by_url`
- Agent example: `mammoth dashboard get-by-url example --output json --no-input`

### `mammoth dashboard job-by-url`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.
- `JOB_ID` (int, required) — ID of the job.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.job_by_url`
- Agent example: `mammoth dashboard job-by-url example 123 --output json --no-input`

### `mammoth dashboard list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.list`
- Agent example: `mammoth dashboard list --output json --no-input`

### `mammoth dashboard og-card`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.og_card`
- Agent example: `mammoth dashboard og-card 123 --output json --no-input`

### `mammoth dashboard page plan`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.page_plan`
- Agent example: `mammoth dashboard page plan 123 --input '{"body": {"params": {"intent": "example"}}}' --output json --no-input`

### `mammoth dashboard pdf export`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.pdf_export`
- Agent example: `mammoth dashboard pdf export 123 --input '{"body": {"params": {"data": {}}}}' --output json --no-input`

### `mammoth dashboard pdf-artifact`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `JOB_ID` (int, required) — ID of the job.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.pdf_artifact`
- Agent example: `mammoth dashboard pdf-artifact 123 123 --output json --no-input`

### `mammoth dashboard published canvas`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_canvas`
- Agent example: `mammoth dashboard published canvas example --output json --no-input`

### `mammoth dashboard published data`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_data`
- Agent example: `mammoth dashboard published data example --input '{"body": {"params": {"descriptor_ids": ["example"]}}}' --output json --no-input`

### `mammoth dashboard published og-card`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_og_card`
- Agent example: `mammoth dashboard published og-card example --output json --no-input`

### `mammoth dashboard published pdf export`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_pdf_export`
- Agent example: `mammoth dashboard published pdf export example --input '{"body": {"params": {"data": {}}}}' --output json --no-input`

### `mammoth dashboard published pdf-artifact`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.
- `JOB_ID` (int, required) — ID of the job.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_pdf_artifact`
- Agent example: `mammoth dashboard published pdf-artifact example 123 --output json --no-input`

### `mammoth dashboard published share-page`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_share_page`
- Agent example: `mammoth dashboard published share-page example --output json --no-input`

### `mammoth dashboard published video export`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_video_export`
- Agent example: `mammoth dashboard published video export example --output json --no-input`

### `mammoth dashboard published video-artifact`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_video_artifact`
- Agent example: `mammoth dashboard published video-artifact example --output json --no-input`

### `mammoth dashboard published-data-by-url`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.published_data_by_url`
- Agent example: `mammoth dashboard published-data-by-url example --input '{"body": {"params": {"widget_id": "00000000-0000-4000-8000-000000000001"}}}' --output json --no-input`

### `mammoth dashboard qa ask`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_ask`
- Agent example: `mammoth dashboard qa ask 123 123 --input '{"body": {"params": {"question": "example"}}}' --output json --no-input`

### `mammoth dashboard qa comment create`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_comment_create`
- Agent example: `mammoth dashboard qa comment create 123 123 --input '{"body": {"params": {"body": "example"}}}' --output json --no-input`

### `mammoth dashboard qa comment delete`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.
- `COMMENT_ID` (int, required) — ID of the comment.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_comment_delete`
- Agent example: `mammoth dashboard qa comment delete 123 123 123 --output json --no-input`

### `mammoth dashboard qa feedback`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.
- `MESSAGE_ID` (int, required) — ID of the message.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_feedback`
- Agent example: `mammoth dashboard qa feedback 123 123 123 --input '{"body": {"params": {"rating": "up"}}}' --output json --no-input`

### `mammoth dashboard qa session create`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_create`
- Agent example: `mammoth dashboard qa session create 123 --input '{"body": {"params": {"title": "example"}}}' --output json --no-input`

### `mammoth dashboard qa session delete`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_delete`
- Agent example: `mammoth dashboard qa session delete 123 123 --output json --no-input`

### `mammoth dashboard qa session fork`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_fork`
- Agent example: `mammoth dashboard qa session fork 123 123 --output json --no-input`

### `mammoth dashboard qa session get`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_get`
- Agent example: `mammoth dashboard qa session get 123 123 --output json --no-input`

### `mammoth dashboard qa session list`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_list`
- Agent example: `mammoth dashboard qa session list 123 --output json --no-input`

### `mammoth dashboard qa session rename`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_rename`
- Agent example: `mammoth dashboard qa session rename 123 123 --input '{"body": {"params": {"title": "example"}}}' --output json --no-input`

### `mammoth dashboard qa session set-visibility`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.
- `SESSION_ID` (int, required) — ID of the session.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_session_set_visibility`
- Agent example: `mammoth dashboard qa session set-visibility 123 123 --input '{"body": {"params": {"visibility": "example"}}}' --output json --no-input`

### `mammoth dashboard qa settings get`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_settings_get`
- Agent example: `mammoth dashboard qa settings get 123 --output json --no-input`

### `mammoth dashboard qa settings set`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.qa_settings_set`
- Agent example: `mammoth dashboard qa settings set 123 --input '{"body": {"params": {"allow_viewer_qa": true}}}' --output json --no-input`

### `mammoth dashboard query`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.query`
- Agent example: `mammoth dashboard query 123 --input '{"body": {"params": {"descriptor": {}}}}' --output json --no-input`

### `mammoth dashboard restore`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.restore`
- Agent example: `mammoth dashboard restore 123 --output json --no-input`

### `mammoth dashboard rls assignment list`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.rls_assignment_list`
- Agent example: `mammoth dashboard rls assignment list 123 --output json --no-input`

### `mammoth dashboard rls assignment set`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.rls_assignment_set`
- Agent example: `mammoth dashboard rls assignment set 123 --input '{"body": {"params": {"assignments": [{"email": "example"}]}}}' --output json --no-input`

### `mammoth dashboard rls column list`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.rls_column_list`
- Agent example: `mammoth dashboard rls column list 123 --output json --no-input`

### `mammoth dashboard rls value list`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.rls_value_list`
- Agent example: `mammoth dashboard rls value list 123 --input '{"column": "example"}' --output json --no-input`

### `mammoth dashboard share`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.share`
- Agent example: `mammoth dashboard share 123 --input '{"type_of_auth": "mammoth"}' --output json --no-input`

### `mammoth dashboard signature create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.signature_create`
- Agent example: `mammoth dashboard signature create --input '{"body": {"params": {"name": "example"}}}' --output json --no-input`

### `mammoth dashboard signature delete`

**Arguments**

- `SIGNATURE_ID` (str, required) — ID of the signature.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.signature_delete`
- Agent example: `mammoth dashboard signature delete example --output json --no-input`

### `mammoth dashboard signature list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.signature_list`
- Agent example: `mammoth dashboard signature list --output json --no-input`

### `mammoth dashboard signature update`

**Arguments**

- `SIGNATURE_ID` (str, required) — ID of the signature.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.signature_update`
- Agent example: `mammoth dashboard signature update example --input '{"body": {"params": {"name": "example"}}}' --output json --no-input`

### `mammoth dashboard source list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.get_sources`
- Agent example: `mammoth dashboard source list --output json --no-input`

### `mammoth dashboard style custom create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_custom_create`
- Agent example: `mammoth dashboard style custom create --input '{"body": {"params": {"signals": {}}}}' --output json --no-input`

### `mammoth dashboard style custom delete`

**Arguments**

- `STYLE_ID` (str, required) — ID of the style.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_custom_delete`
- Agent example: `mammoth dashboard style custom delete example --output json --no-input`

### `mammoth dashboard style custom list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_custom_list`
- Agent example: `mammoth dashboard style custom list --output json --no-input`

### `mammoth dashboard style custom update`

**Arguments**

- `STYLE_ID` (str, required) — ID of the style.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_custom_update`
- Agent example: `mammoth dashboard style custom update example --input '{"body": {"params": {"signals": {}}}}' --output json --no-input`

### `mammoth dashboard style default get`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_default_get`
- Agent example: `mammoth dashboard style default get --output json --no-input`

### `mammoth dashboard style default set`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_default_set`
- Agent example: `mammoth dashboard style default set --input '{"body": {"params": {"styleId": "example"}}}' --output json --no-input`

### `mammoth dashboard style derive`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_derive`
- Agent example: `mammoth dashboard style derive --input '{"body": {"params": {"signals": {}}}}' --output json --no-input`

### `mammoth dashboard style extract-brand`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_extract_brand`
- Agent example: `mammoth dashboard style extract-brand --input '{"body": {"params": {"url": "example"}}}' --output json --no-input`

### `mammoth dashboard style preset list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_preset_list`
- Agent example: `mammoth dashboard style preset list --output json --no-input`

### `mammoth dashboard style token list`

**Arguments**

- `ID` (str, required) — Identifier of the resource.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.style_token_list`
- Agent example: `mammoth dashboard style token list example --output json --no-input`

### `mammoth dashboard suggestion list`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.suggestion_list`
- Agent example: `mammoth dashboard suggestion list 123 --output json --no-input`

### `mammoth dashboard template apply`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_apply`
- Agent example: `mammoth dashboard template apply --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}' --output json --no-input`

### `mammoth dashboard template create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_create`
- Agent example: `mammoth dashboard template create --input '{"body": {"params": {"dashboard_id": 1, "title": "example"}}}' --output json --no-input`

### `mammoth dashboard template delete`

**Arguments**

- `TEMPLATE_ID` (str, required) — ID of the template.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_delete`
- Agent example: `mammoth dashboard template delete example --output json --no-input`

### `mammoth dashboard template fit`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_fit`
- Agent example: `mammoth dashboard template fit 123 --output json --no-input`

### `mammoth dashboard template get`

**Arguments**

- `TEMPLATE_ID` (str, required) — ID of the template.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_get`
- Agent example: `mammoth dashboard template get example --output json --no-input`

### `mammoth dashboard template list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_list`
- Agent example: `mammoth dashboard template list --output json --no-input`

### `mammoth dashboard template preview`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_preview`
- Agent example: `mammoth dashboard template preview --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}' --output json --no-input`

### `mammoth dashboard template rename`

**Arguments**

- `TEMPLATE_ID` (str, required) — ID of the template.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_rename`
- Agent example: `mammoth dashboard template rename example --input '{"body": {"params": {"title": "example"}}}' --output json --no-input`

### `mammoth dashboard template resolve-mapping`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.template_resolve_mapping`
- Agent example: `mammoth dashboard template resolve-mapping --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}' --output json --no-input`

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
- Agent example: `mammoth dashboard update 123 --input '{"patch": [{"op": "add", "path": "intent", "value": "example"}]}' --output json --no-input`

### `mammoth dashboard v3 generate`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.v3_generate`
- Agent example: `mammoth dashboard v3 generate --input '{"body": {"params": {"intent": "example", "dataview_id": 1}}}' --output json --no-input`

### `mammoth dashboard video export`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.video_export`
- Agent example: `mammoth dashboard video export 123 --output json --no-input`

### `mammoth dashboard video-state`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.video_state`
- Agent example: `mammoth dashboard video-state 123 --output json --no-input`

### `mammoth dashboard widget-data`

**Arguments**

- `DASHBOARD_ID` (int, required) — ID of the dashboard.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.widget_data`
- Agent example: `mammoth dashboard widget-data 123 --input '{"body": {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}}' --output json --no-input`

### `mammoth dashboard widget-data-by-url`

**Arguments**

- `URL` (str, required) — URL slug identifying the resource.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dashboards.DashboardsAPI.widget_data_by_url`
- Agent example: `mammoth dashboard widget-data-by-url example --input '{"body": {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}}' --output json --no-input`

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
- Agent example: `mammoth data-app create --input '{"body": {"automation_id": 1, "dashboard_ids": [1], "name": "example", "project_id": 1}}' --output json --no-input`

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
- Agent example: `mammoth data-app share 123 --input '{"body": {"params": {"auth": {"type_of_auth": "mammoth"}}}}' --output json --no-input`

### `mammoth data-app update`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.update`
- Agent example: `mammoth data-app update 123 --input '{"body": {"params": {"name": "example"}}}' --output json --no-input`

### `mammoth data-app upload`

**Arguments**

- `DATA_APP_ID` (int, required) — ID of the data app to upload into.
- `FILE` (str, optional) — Path to a local file to upload; or pass it via the 'file' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.upload`
- Agent example: `mammoth data-app upload 123 example --output json --no-input`

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
- `EMAIL` (str, required) — Email address of the shared user to remove.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_apps.DataAppsAPI.user_remove`
- Agent example: `mammoth data-app user remove 123 example --output json --no-input`

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
- Agent example: `mammoth dataset bulk-update --input '{"patch_data": {"example": "example"}}' --output json --no-input`

### `mammoth dataset create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.create`
- Agent example: `mammoth dataset create --input '{"dataset_spec": {"example": "example"}, "ds_creation_type": "example"}' --output json --no-input`

### `mammoth dataset create-from-pdf`

**Arguments**

- `FILE_OBJECT_ID` (int, required) — ID of the file object.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.create_from_pdf`
- Agent example: `mammoth dataset create-from-pdf 123 --input '{"file_name": "example"}' --output json --no-input`

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

### `mammoth dataset file-settings get`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.datasets.DatasetsAPI.get_file_settings`
- Agent example: `mammoth dataset file-settings get 123 --output json --no-input`

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
- Agent example: `mammoth dataset file-settings update 123 --input '{"delimiter": "example", "has_header": true, "initial_skip_count": 1, "quotechar": "example"}' --output json --no-input`

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
- Agent example: `mammoth dataset rename 123 --input '{"name": "example"}' --output json --no-input`

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
- Agent example: `mammoth dataset update --input '{"patch_data": [{"example": "example"}]}' --output json --no-input`

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
- Agent example: `mammoth external-key create --input '{"key_type": "open_ai", "key_name": "example", "secure_key": "example"}' --output json --no-input`

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
- Agent example: `mammoth file bulk-delete --input '{"file_ids": [1]}' --output json --no-input`

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
- Agent example: `mammoth file extract-sheets 123 --input '{"sheets": ["example"]}' --output json --no-input`

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
- Agent example: `mammoth file set-password 123 --input '{"password": "example"}' --output json --no-input`

### `mammoth file update`

**Arguments**

- `FILE_ID` (int, required) — ID of the file.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.update`
- Agent example: `mammoth file update 123 --input '{"patch_request": {"patch": [{"op": "replace", "path": "extract_sheets", "value": "example"}]}}' --output json --no-input`

### `mammoth file upload`

**Arguments**

- `FILES` (str, optional) — Path to a local file to upload; or pass one or more via the 'files' field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.upload`
- Agent example: `mammoth file upload example --output json --no-input`

### `mammoth file upload-folder`

**Arguments**

- `FOLDER_PATH` (str, optional) — Path to a local folder to upload; or pass it via the 'folder_path' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.files.FilesAPI.upload_folder`
- Agent example: `mammoth file upload-folder example --output json --no-input`

## folder

### `mammoth folder bulk-delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.folders.FoldersAPI.bulk_delete`
- Agent example: `mammoth folder bulk-delete --output json --no-input`

### `mammoth folder create`

**Arguments**

- `NAME` (str, optional) — Name of the new folder; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.folders.FoldersAPI.create`
- Agent example: `mammoth folder create example --output json --no-input`

### `mammoth folder delete`

**Arguments**

- `FOLDER_ID` (int, required) — ID of the folder to delete.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.folders.FoldersAPI.delete`
- Agent example: `mammoth folder delete 123 --output json --no-input`

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
- Agent example: `mammoth folder move --input '{"resource_ids": ["example"]}' --output json --no-input`

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
- Agent example: `mammoth folder update 123 --input '{"name": "example"}' --output json --no-input`

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
- Agent example: `mammoth job get-many --input '{"job_ids": [1]}' --output json --no-input`

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
- Agent example: `mammoth job wait-many --input '{"job_ids": [1]}' --output json --no-input`

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
- Agent example: `mammoth notification update 123 --input '{"patch": [{"example": "example"}]}' --output json --no-input`

### `mammoth notification update-batch`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.notifications.NotificationsAPI.update_batch`
- Agent example: `mammoth notification update-batch --input '{"patch": [{"example": "example"}]}' --output json --no-input`

## parameter

### `mammoth parameter create`

**Arguments**

- `NAME` (str, optional) — Name of the new parameter; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.create`
- Agent example: `mammoth parameter create example --input '{"param_type": "example", "value": "example"}' --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new parameter group; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.parameters.ParametersAPI.group_create`
- Agent example: `mammoth parameter group create example --output json --no-input`

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
- Agent example: `mammoth parameter group reorder --input '{"order": [1]}' --output json --no-input`

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
- Agent example: `mammoth project bulk-delete --input '{"project_ids": [1]}' --output json --no-input`

### `mammoth project bulk-update`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.bulk_update`
- Agent example: `mammoth project bulk-update --input '{"patch_data": {"example": "example"}}' --output json --no-input`

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
- Agent example: `mammoth project publish-credentials 123 --input '{"odbc_type": "postgres"}' --output json --no-input`

### `mammoth project resource-dependencies`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.resource_dependencies`
- Agent example: `mammoth project resource-dependencies 123 --input '{"resource_ids": ["example"]}' --output json --no-input`

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
- Agent example: `mammoth project user add 123 --input '{"user_ids": ["example"]}' --output json --no-input`

### `mammoth project user remove`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.remove_users`
- Agent example: `mammoth project user remove 123 --input '{"user_ids": ["example"]}' --output json --no-input`

### `mammoth project user update`

**Arguments**

- `PROJECT_ID` (int, optional) — ID of the project to act on; defaults to the active project.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.projects.ProjectsAPI.user_update`
- Agent example: `mammoth project user update 123 --input '{"role": "project_admin", "user_id": 123}' --output json --no-input`

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
- Agent example: `mammoth schedule create --input '{"spec": {"rrule": {"frequency": "minutely", "start": "2026-01-01T00:00:00Z"}}}' --output json --no-input`

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
- Agent example: `mammoth schedule update 123 --input '{"patch": [{"op": "replace", "path": "rrule", "value": {"rrule": {"frequency": "minutely", "start": "2026-01-01T00:00:00Z"}, "work_items": [{"name": "pull_cloud_data", "execution_params": {"schedule_type": "moment", "first_pull_at": "now", "on_refresh_action": "replace"}, "args": [1]}]}}]}' --output json --no-input`

## schema

### `mammoth schema get`

**Arguments**

- `COMMAND_ID` (str, required) — Command id to fetch the schema for (e.g. view.transform.bulk-replace).

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth_cli.commands.schema.get`
- Agent example: `mammoth schema get view.transform.bulk-replace --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new snippet; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.snippets.SnippetsAPI.create`
- Agent example: `mammoth snippet create example --input '{"code": "example", "language": "example"}' --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new connector; or pass it via the 'name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_create`
- Agent example: `mammoth support connector create example --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new connector profile; or pass it via the 'name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.connector_profile_create`
- Agent example: `mammoth support connector-profile create example --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new feature; or pass it via the 'name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_create`
- Agent example: `mammoth support feature create example --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new feature profile; or pass it via the 'name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.feature_profile_create`
- Agent example: `mammoth support feature-profile create example --output json --no-input`

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

**Arguments**

- `NAME` (str, optional) — Name of the new plan; or pass it via the 'name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.plan_create`
- Agent example: `mammoth support plan create example --input '{"monthly_price": 1.0, "is_self_serve": true}' --output json --no-input`

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
- Agent example: `mammoth support plan update-storage-tiers 123 --input '{"storage_tiers": [{"example": "example"}]}' --output json --no-input`

### `mammoth support subscription create`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.
- `PLAN_ID` (str, required) — ID of the plan.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_create`
- Agent example: `mammoth support subscription create 123 example --output json --no-input`

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
- `SUBSCRIPTION_ID` (str, required) — ID of the subscription.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.subscription_update`
- Agent example: `mammoth support subscription update 123 example --output json --no-input`

### `mammoth support user list-all`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.user_list_all`
- Agent example: `mammoth support user list-all --output json --no-input`

### `mammoth support user register`

**Arguments**

- `EMAIL` (str, optional) — Email of the user to register; or pass it via the 'email' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.user_register`
- Agent example: `mammoth support user register example --input '{"first_name": "example", "last_name": "example", "verified": true}' --output json --no-input`

### `mammoth support user update`

**Arguments**

- `EMAIL` (str, optional) — Email of the user to update; or pass it via the 'email' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.user_update`
- Agent example: `mammoth support user update example --input '{"verified": true}' --output json --no-input`

### `mammoth support workspace create`

**Arguments**

- `NAME` (str, optional) — Name of the new workspace; or pass it via the 'name' input field.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_create`
- Agent example: `mammoth support workspace create example --input '{"user_email": "example", "payment_frequency": "example"}' --output json --no-input`

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
- Agent example: `mammoth support workspace update 123 --input '{"name": "example", "payment_frequency": "example", "plan_id": 1}' --output json --no-input`

### `mammoth support workspace user add`

**Arguments**

- `WORKSPACE_ID` (int, required) — ID of the workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.support.SupportAPI.workspace_user_add`
- Agent example: `mammoth support workspace user add 123 --input '{"email": "example", "role": "example"}' --output json --no-input`

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
- Agent example: `mammoth support workspace user transfer 123 123 --input '{"role": "example"}' --output json --no-input`

## template

### `mammoth template create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.templates.TemplatesAPI.create`
- Agent example: `mammoth template create --input '{"body": {"name": "example"}}' --output json --no-input`

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
- Agent example: `mammoth template update 123 --input '{"body": {"name": "example"}}' --output json --no-input`

## trash

### `mammoth trash add`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.trash.TrashAPI.add`
- Agent example: `mammoth trash add --input '{"items": [{"example": "example"}]}' --output json --no-input`

### `mammoth trash list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.trash.TrashAPI.list`
- Agent example: `mammoth trash list --output json --no-input`

### `mammoth trash restore`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.trash.TrashAPI.restore`
- Agent example: `mammoth trash restore --input '{"items": [{"example": "example"}]}' --output json --no-input`

## upgrade

### `mammoth upgrade`

- Mutation class: `external_effect`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth_cli.commands.upgrade.run`
- Agent example: `mammoth upgrade --output json --no-input`

## user

### `mammoth user avatar delete`

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.users.UsersAPI.avatar_delete`
- Agent example: `mammoth user avatar delete --output json --no-input`

### `mammoth user avatar upload`

**Arguments**

- `FILE` (str, optional) — Path to a local image to upload; or pass it via the 'file' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.users.UsersAPI.avatar_upload`
- Agent example: `mammoth user avatar upload example --output json --no-input`

### `mammoth user change-password`

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.user_profile.UserProfileAPI.change_password`
- Agent example: `mammoth user change-password --input '{"current_password": "example", "new_password": "example"}' --output json --no-input`

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

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.active_users`
- Agent example: `mammoth view active-user list 123 123 --output json --no-input`

### `mammoth view active-user mark`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

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
- Agent example: `mammoth view ai generate-data 123 --input '{"prompt": "example"}' --output json --no-input`

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
- Agent example: `mammoth view bulk-delete 123 --input '{"dataview_ids": [1]}' --output json --no-input`

### `mammoth view checkpoint create`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.create`
- Agent example: `mammoth view checkpoint create 123 123 --input '{"body": {"checkpoint_name": "example", "checkpoint_type": "alert"}}' --output json --no-input`

### `mammoth view checkpoint delete`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `CHECKPOINT_ID` (int, required) — ID of the checkpoint.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.delete`
- Agent example: `mammoth view checkpoint delete 123 123 123 --output json --no-input`

### `mammoth view checkpoint get`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `CHECKPOINT_ID` (int, required) — ID of the checkpoint.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.get`
- Agent example: `mammoth view checkpoint get 123 123 123 --output json --no-input`

### `mammoth view checkpoint list`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.list`
- Agent example: `mammoth view checkpoint list 123 123 --output json --no-input`

### `mammoth view checkpoint update`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `CHECKPOINT_ID` (int, required) — ID of the checkpoint.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.checkpoints.CheckpointsAPI.update`
- Agent example: `mammoth view checkpoint update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "approve"}]}}' --output json --no-input`

### `mammoth view conditional-format create`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_create`
- Agent example: `mammoth view conditional-format create 123 123 --input '{"rule": {"example": "example"}}' --output json --no-input`

### `mammoth view conditional-format delete-all`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_delete`
- Agent example: `mammoth view conditional-format delete-all 123 123 --output json --no-input`

### `mammoth view conditional-format list`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_list`
- Agent example: `mammoth view conditional-format list 123 123 --output json --no-input`

### `mammoth view conditional-format update`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.conditional_format_update`
- Agent example: `mammoth view conditional-format update 123 123 --input '{"rule": {"example": "example"}}' --output json --no-input`

### `mammoth view create`

**Arguments**

- `DATASET_ID` (int, required) — ID of the dataset.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.client.ViewsResource.create`
- Agent example: `mammoth view create 123 --output json --no-input`

### `mammoth view data get`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.get_data`
- Agent example: `mammoth view data get 123 123 --output json --no-input`

### `mammoth view data query`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.query_data`
- Agent example: `mammoth view data query 123 123 --output json --no-input`

### `mammoth view data-check create`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.create`
- Agent example: `mammoth view data-check create 123 123 --input '{"body": {"checks": [{"check_type": "null_percentage", "config": {"column": "example", "condition": "lt"}}], "name": "example"}}' --output json --no-input`

### `mammoth view data-check delete`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATA_CHECK_ID` (int, required) — ID of the data check.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.delete`
- Agent example: `mammoth view data-check delete 123 123 123 --output json --no-input`

### `mammoth view data-check get`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATA_CHECK_ID` (int, required) — ID of the data check.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.get`
- Agent example: `mammoth view data-check get 123 123 123 --output json --no-input`

### `mammoth view data-check list`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.list`
- Agent example: `mammoth view data-check list 123 123 --output json --no-input`

### `mammoth view data-check update`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATA_CHECK_ID` (int, required) — ID of the data check.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.data_checks.DataChecksAPI.update`
- Agent example: `mammoth view data-check update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "enable"}]}}' --output json --no-input`

### `mammoth view delete`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.client.ViewsResource.delete`
- Agent example: `mammoth view delete 123 --output json --no-input`

### `mammoth view derivative create`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.create`
- Agent example: `mammoth view derivative create 123 123 --input '{"body": {"param": {"METRIC": {"AS": "example", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "example", "FUNCTION": "SUM"}}]}}}}' --output json --no-input`

### `mammoth view derivative data`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DERIVATIVE_ID` (int, required) — ID of the derivative.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.data`
- Agent example: `mammoth view derivative data 123 123 123 --input '{"body": {"condition": {"FILTER_TYPE": "SHOW"}}}' --output json --no-input`

### `mammoth view derivative delete`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DERIVATIVE_ID` (int, required) — ID of the derivative.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.delete`
- Agent example: `mammoth view derivative delete 123 123 123 --output json --no-input`

### `mammoth view derivative list`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.list`
- Agent example: `mammoth view derivative list 123 123 --output json --no-input`

### `mammoth view derivative update`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DERIVATIVE_ID` (int, required) — ID of the derivative.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.derivatives.DerivativesAPI.update`
- Agent example: `mammoth view derivative update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "param", "value": {"METRIC": {"AS": "example", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "example", "FUNCTION": "SUM"}}]}}}]}}' --output json --no-input`

### `mammoth view draft auto-run`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.view.View.set_auto_run`
- Agent example: `mammoth view draft auto-run 123 --input '{"enabled": true}' --output json --no-input`

### `mammoth view draft command`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.command`
- Agent example: `mammoth view draft command 123 --input '{"command": "example"}' --output json --no-input`

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
- Agent example: `mammoth view export create 123 --input '{"export_spec": {"DATAVIEW_ID": 1, "handler_type": "postgres", "trigger_type": "none", "target_properties": {"file": "example", "file_type": "example", "include_hidden": true, "is_format_set": true, "use_format": true}, "additional_properties": {}, "run_immediately": true}}' --output json --no-input`

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
- Agent example: `mammoth view export publish-db 123 --input '{"odbc_type": "postgres", "target_properties": {"example": "example"}}' --output json --no-input`

### `mammoth view export publish-db-update`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.publish_db_update`
- Agent example: `mammoth view export publish-db-update 123 --input '{"patch": [{"example": "example"}]}' --output json --no-input`

### `mammoth view export update`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `EXPORT_ID` (int, required) — ID of the export.

- Mutation class: `external_effect`
- Confirmation: `yes_always`
- Backing SDK: `mammoth.api.exports.ExportsAPI.update`
- Agent example: `mammoth view export update 123 123 --input '{"patches": [{"example": "example"}]}' --output json --no-input`

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

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

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
- Agent example: `mammoth view pipeline edit 123 --input '{"patches": [{"example": "example"}]}' --output json --no-input`

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

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.preview`
- Agent example: `mammoth view preview 123 123 --output json --no-input`

### `mammoth view restore`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

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
- Agent example: `mammoth view task add 123 --input '{"task_spec": {"example": "example"}}' --output json --no-input`

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
- Agent example: `mammoth view task preview 123 --input '{"task_spec": {"example": "example"}}' --output json --no-input`

### `mammoth view task update`

**Arguments**

- `DATAVIEW_ID` (int, required) — ID of the dataview.
- `TASK_ID` (int, required) — ID of the task.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline.PipelineAPI.update_task`
- Agent example: `mammoth view task update 123 123 --input '{"task_spec": {"example": "example"}}' --output json --no-input`

### `mammoth view transform add-column`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.add_column`
- Agent example: `mammoth view transform add-column 123 --input '{"name": "example"}' --output json --no-input`

### `mammoth view transform add-sql`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.add_sql`
- Agent example: `mammoth view transform add-sql 123 --input '{"query": "example"}' --output json --no-input`

### `mammoth view transform ai`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.gen_ai`
- Agent example: `mammoth view transform ai 123 --input '{"prompt": "example", "context_columns": ["example"]}' --output json --no-input`

### `mammoth view transform bulk-replace`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.bulk_replace`
- Agent example: `mammoth view transform bulk-replace 123 --input '{"columns": ["example"], "mapping": [{"search": ["example"], "replace": "example"}]}' --output json --no-input`

### `mammoth view transform combine-columns`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.combine_columns`
- Agent example: `mammoth view transform combine-columns 123 --input '{"sources": ["example"]}' --output json --no-input`

### `mammoth view transform convert-type`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.convert_type`
- Agent example: `mammoth view transform convert-type 123 --input '{"conversions": [{"column": "example", "to": "TEXT"}]}' --output json --no-input`

### `mammoth view transform copy-columns`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.copy_columns`
- Agent example: `mammoth view transform copy-columns 123 --input '{"copies": [{"source": "example"}]}' --output json --no-input`

### `mammoth view transform crosstab`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.crosstab`
- Agent example: `mammoth view transform crosstab 123 --input '{"rows": ["example"], "pivot_column": "example", "select": {"function": "SUM"}, "dataset_name": "example"}' --output json --no-input`

### `mammoth view transform date-diff`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.date_diff`
- Agent example: `mammoth view transform date-diff 123 --input '{"component": "YEAR", "start": "example", "end": "example"}' --output json --no-input`

### `mammoth view transform delete-columns`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.delete_columns`
- Agent example: `mammoth view transform delete-columns 123 --input '{"columns": ["example"]}' --output json --no-input`

### `mammoth view transform discard-duplicates`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.discard_duplicates`
- Agent example: `mammoth view transform discard-duplicates 123 --output json --no-input`

### `mammoth view transform extract-date`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.extract_date`
- Agent example: `mammoth view transform extract-date 123 --input '{"column": "example", "component": "year"}' --output json --no-input`

### `mammoth view transform fill-missing`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.fill_missing`
- Agent example: `mammoth view transform fill-missing 123 --input '{"column": "example", "direction": "FIRST_VALUE"}' --output json --no-input`

### `mammoth view transform filter`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.filter_rows`
- Agent example: `mammoth view transform filter 123 --input '{"condition": {"column": "Status", "operator": "EQ", "value": "Active"}}' --output json --no-input`

### `mammoth view transform generate-sql`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.generate_sql`
- Agent example: `mammoth view transform generate-sql 123 --input '{"intent": "example"}' --output json --no-input`

### `mammoth view transform increment-date`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.increment_date`
- Agent example: `mammoth view transform increment-date 123 --input '{"column": "example", "delta": {}}' --output json --no-input`

### `mammoth view transform join`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.join`
- Agent example: `mammoth view transform join 123 --input '{"foreign_view": 1, "join_type": "INNER", "on": [{"left": "example", "right": "example"}], "select": ["example"]}' --output json --no-input`

### `mammoth view transform json-extract`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.json_extract`
- Agent example: `mammoth view transform json-extract 123 --input '{"column": "example"}' --output json --no-input`

### `mammoth view transform limit-rows`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.limit_rows`
- Agent example: `mammoth view transform limit-rows 123 --input '{"n": 1}' --output json --no-input`

### `mammoth view transform lookup`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.lookup`
- Agent example: `mammoth view transform lookup 123 --input '{"source": "example", "lookup_view_id": 1, "key": "example", "value": "example"}' --output json --no-input`

### `mammoth view transform math`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.math`
- Agent example: `mammoth view transform math 123 --input '{"expression": "example"}' --output json --no-input`

### `mammoth view transform pivot`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.pivot`
- Agent example: `mammoth view transform pivot 123 --input '{"group_by": ["example"], "aggregations": [{"column": "example", "function": "SUM"}]}' --output json --no-input`

### `mammoth view transform replace`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.replace_values`
- Agent example: `mammoth view transform replace 123 --input '{"columns": ["example"], "find": "example", "replace": "example"}' --output json --no-input`

### `mammoth view transform set-values`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.set_values`
- Agent example: `mammoth view transform set-values 123 --input '{"values": [{"value": "example"}]}' --output json --no-input`

### `mammoth view transform small-large`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.small_large`
- Agent example: `mammoth view transform small-large 123 --input '{"function": "SMALL", "columns": ["example"]}' --output json --no-input`

### `mammoth view transform split`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.split_column`
- Agent example: `mammoth view transform split 123 --input '{"column": "example", "delimiter": "example", "new_columns": [{"name": "example"}]}' --output json --no-input`

### `mammoth view transform substring`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.substring`
- Agent example: `mammoth view transform substring 123 --input '{"column": "example"}' --output json --no-input`

### `mammoth view transform text`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.text_transform`
- Agent example: `mammoth view transform text 123 --input '{"columns": ["example"]}' --output json --no-input`

### `mammoth view transform unnest`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.unnest`
- Agent example: `mammoth view transform unnest 123 --input '{"columns": ["example"]}' --output json --no-input`

### `mammoth view transform window`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.

- Mutation class: `reversible_pipeline`
- Confirmation: `none`
- Backing SDK: `mammoth.View.window`
- Agent example: `mammoth view transform window 123 --input '{"function": "ROW_NUMBER"}' --output json --no-input`

### `mammoth view trash`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.trash`
- Agent example: `mammoth view trash 123 123 --output json --no-input`

### `mammoth view update`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.dataviews.DataviewsAPI.update`
- Agent example: `mammoth view update 123 123 --input '{"patch_data": [{"example": "example"}]}' --output json --no-input`

### `mammoth view version apply`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `VERSION_ID` (int, required) — ID of the pipeline version.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.apply`
- Agent example: `mammoth view version apply 123 123 123 --output json --no-input`

### `mammoth view version delete`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `VERSION_ID` (int, required) — ID of the pipeline version.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `destructive`
- Confirmation: `prompt_or_yes`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.delete`
- Agent example: `mammoth view version delete 123 123 123 --output json --no-input`

### `mammoth view version get`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `VERSION_ID` (int, required) — ID of the pipeline version.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.get`
- Agent example: `mammoth view version get 123 123 123 --output json --no-input`

### `mammoth view version list`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.list`
- Agent example: `mammoth view version list 123 123 --output json --no-input`

### `mammoth view version update`

**Arguments**

- `VIEW_ID` (int, required) — ID of the view to act on.
- `VERSION_ID` (int, required) — ID of the pipeline version.
- `DATASET_ID` (int, optional) — ID of the dataset the view belongs to; resolved from the view when omitted.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.pipeline_versions.PipelineVersionsAPI.update`
- Agent example: `mammoth view version update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "name"}]}}' --output json --no-input`

## webhook

### `mammoth webhook create`

**Arguments**

- `NAME` (str, optional) — Name of the new webhook; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.create`
- Agent example: `mammoth webhook create example --output json --no-input`

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
- Agent example: `mammoth webhook send --input '{"webhook_uri": "example", "data": {"example": "example"}}' --output json --no-input`

### `mammoth webhook send-get`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.webhooks.WebhooksAPI.send_data_get`
- Agent example: `mammoth webhook send-get --input '{"webhook_uri": "example"}' --output json --no-input`

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
- Agent example: `mammoth workflow block add 123 --input '{"block_type": "example"}' --output json --no-input`

### `mammoth workflow block auth`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.
- `BLOCK_ID` (int, required) — ID of the block.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.block_auth`
- Agent example: `mammoth workflow block auth 123 123 --input '{"auth_data": {"example": "example"}}' --output json --no-input`

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
- Agent example: `mammoth workflow block type 123 123 --input '{"connection_type": "example"}' --output json --no-input`

### `mammoth workflow canvas`

**Arguments**

- `WORKFLOW_ID` (int, required) — ID of the workflow.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.canvas`
- Agent example: `mammoth workflow canvas 123 --input '{"canvas_state": {"example": "example"}}' --output json --no-input`

### `mammoth workflow cleanup`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.cleanup`
- Agent example: `mammoth workflow cleanup --output json --no-input`

### `mammoth workflow create`

**Arguments**

- `NAME` (str, optional) — Name of the new workflow; or pass it via the 'name' input field.

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workflows.WorkflowsAPI.create`
- Agent example: `mammoth workflow create example --output json --no-input`

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
- Agent example: `mammoth workflow from-template 123 --input '{"workflow_name": "example"}' --output json --no-input`

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
- Agent example: `mammoth workspace accept-invite --input '{"token": "example"}' --output json --no-input`

### `mammoth workspace app-usage`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.app_usage`
- Agent example: `mammoth workspace app-usage --output json --no-input`

### `mammoth workspace check-expression`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.check_expression`
- Agent example: `mammoth workspace check-expression --input '{"body": {"intent": "example"}}' --output json --no-input`

### `mammoth workspace create`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.create`
- Agent example: `mammoth workspace create --input '{"body": {}}' --output json --no-input`

### `mammoth workspace delete`

**Arguments**

- `WORKSPACE_ID` (int, optional) — ID of the workspace to act on; defaults to the client's own workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.delete`
- Agent example: `mammoth workspace delete 123 --output json --no-input`

### `mammoth workspace get`

**Arguments**

- `WORKSPACE_ID` (int, optional) — ID of the workspace to act on; defaults to the client's own workspace.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.get`
- Agent example: `mammoth workspace get 123 --output json --no-input`

### `mammoth workspace list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.list`
- Agent example: `mammoth workspace list --output json --no-input`

### `mammoth workspace llm-task`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.llm_task`
- Agent example: `mammoth workspace llm-task --input '{"task_type": "example", "params": {"example": "example"}}' --output json --no-input`

### `mammoth workspace reactivate`

**Arguments**

- `WORKSPACE_ID` (int, optional) — ID of the workspace to act on; defaults to the client's own workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.reactivate`
- Agent example: `mammoth workspace reactivate 123 --output json --no-input`

### `mammoth workspace segment list`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.segment_list`
- Agent example: `mammoth workspace segment list --output json --no-input`

### `mammoth workspace segment update`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.segment_update`
- Agent example: `mammoth workspace segment update --input '{"patch": [{"example": "example"}]}' --output json --no-input`

### `mammoth workspace storage-breakdown`

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.storage_breakdown`
- Agent example: `mammoth workspace storage-breakdown --output json --no-input`

### `mammoth workspace update`

**Arguments**

- `WORKSPACE_ID` (int, optional) — ID of the workspace to act on; defaults to the client's own workspace.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.update`
- Agent example: `mammoth workspace update 123 --input '{"patches": [{"op": "replace", "path": "name", "value": "example"}]}' --output json --no-input`

### `mammoth workspace user add`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_add`
- Agent example: `mammoth workspace user add --input '{"email_ids": ["example"]}' --output json --no-input`

### `mammoth workspace user get`

**Arguments**

- `USER_ID` (str, required) — ID of the user.

- Mutation class: `read`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.get_user`
- Agent example: `mammoth workspace user get example --output json --no-input`

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

- `USER_ID` (str, required) — ID of the user.

- Mutation class: `high_impact`
- Confirmation: `confirm_target`
- Backing SDK: `mammoth.api.workspace.WorkspaceAPI.update_user`
- Agent example: `mammoth workspace user update example --input '{"patches": [{"op": "replace", "path": "role", "value": "workspace_member"}]}' --output json --no-input`

### `mammoth workspace user update-batch`

- Mutation class: `benign_mutation`
- Confirmation: `none`
- Backing SDK: `mammoth.api.workspaces.WorkspacesAPI.user_update_batch`
- Agent example: `mammoth workspace user update-batch --input '{"patches": [{"example": "example"}]}' --output json --no-input`
