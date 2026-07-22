# Complete OpenAPI operation inventory

This appendix is mechanically generated from the authoritative production
OpenAPI document at <https://app.mammoth.io/api/v2/docs/openapi.json>. It prevents silent operation omissions.
The reviewed disposition and exact command records defined by the parity plan
remain the normative pre-code specification freeze.

- OpenAPI version: `3.1.0`.
- API version: `0.1.0`.
- Path count: `234`.
- HTTP operation count: `376`.
- Source SHA-256: `6b2c8647afa9f83c7a742e4279f0407f33bd1325f43acb1efa2cf411d64acb54`.

| Stable method/path identity | Operation ID | Tags | Summary |
|---|---|---|---|
| `POST /accept-invite` | `AcceptInvite` | Accept Invite | Accept invitation to workspace |
| `POST /agents/chat` | `AgentChat` | AI, Agents | Chat with a Mammoth agent |
| `GET /agents/sessions` | `ListAgentSessions` | AI, Agents | List current user's agent sessions |
| `DELETE /agents/sessions/{session_id}` | `DeleteAgentSession` | AI, Agents | Delete an agent chat session |
| `PATCH /agents/sessions/{session_id}` | `SetAgentSessionVisibility` | AI, Agents | Set a chat session's private/shared visibility (creator only) |
| `GET /agents/sessions/{session_id}/messages` | `GetAgentSessionMessages` | AI, Agents | Read messages for one agent session |
| `GET /browse` | `BrowseResources` | Browse | Browse and discover resources |
| `GET /dashboards` | `ListDashboard` | Dashboard | List all dashboards |
| `POST /dashboards` | `GenerateDashboard` | Dashboard | Generate Dashboard |
| `GET /dashboards/sources` | `GetDashboardSources` | Dashboard | Get Dashboard Sources |
| `GET /dashboards/url/{url}` | `GetDashboardByUrl` | Dashboard | Get Dashboard based on url |
| `POST /dashboards/url/{url}/getPublishData` | `GetPublishDataFromSqlByUrl` | Dashboard | Get published data from given SQL query |
| `GET /dashboards/url/{url}/jobs/{job_id}` | `GetDashboardJob` | Dashboard | Get dashboard job by id |
| `POST /dashboards/url/{url}/track-heartbeat` | `TrackHeartbeat` | Dashboard | Update Session Heartbeat |
| `POST /dashboards/url/{url}/track-view` | `TrackView` | Dashboard | Track Dashboard View |
| `POST /dashboards/url/{url}/widgets/data` | `BulkWidgetDataByUrl` | Dashboard | Bulk widget data for a published dashboard |
| `DELETE /dashboards/{dashboard_id}` | `DeleteDashboard` | Dashboard | Delete Dashboard |
| `GET /dashboards/{dashboard_id}` | `GetDashboard` | Dashboard | Get Dashboard |
| `PATCH /dashboards/{dashboard_id}` | `EditDashboard` | Dashboard | Edit Dashboard |
| `POST /dashboards/{dashboard_id}/action` | `DashboardAction` | Dashboard | Dashboard action |
| `GET /dashboards/{dashboard_id}/analytics` | `GetDashboardAnalytics` | Dashboard | Get Dashboard Analytics |
| `POST /dashboards/{dashboard_id}/cancel-generation` | `CancelDashboardGeneration` | Dashboard | Cancel in-flight dashboard generation |
| `POST /dashboards/{dashboard_id}/getDraftData` | `GetDraftDataFromSql` | Dashboard | Get draft data from given SQL query |
| `POST /dashboards/{dashboard_id}/getPublishData` | `GetPublishDataFromSql` | Dashboard | Get published data from given SQL query |
| `POST /dashboards/{dashboard_id}/restore` | `RestoreDashboard` | Dashboard | Restore dashboard from trash |
| `POST /dashboards/{dashboard_id}/share` | `ShareDashboard` | Dashboard | Share Dashboard |
| `POST /dashboards/{dashboard_id}/trash` | `TrashDashboard` | Dashboard | Move dashboard to trash |
| `POST /dashboards/{dashboard_id}/widgets/data` | `BulkWidgetData` | Dashboard | Bulk widget data — future-request |
| `GET /data-apps` | `ListDataApps` | Data Apps | List data apps |
| `POST /data-apps` | `CreateDataApp` | Data Apps | Create a data app |
| `DELETE /data-apps/{data_app_id}` | `DeleteDataAppEndpoint` | Data Apps | Delete a data app |
| `GET /data-apps/{data_app_id}` | `GetDataAppDetails` | Data Apps | Get data app metadata |
| `GET /data-apps/{data_app_id}/active-job` | `GetDataAppActiveJob` | Data Apps | Resume the most recent in-flight upload for this data app |
| `POST /data-apps/{data_app_id}/files` | `UploadToDataApp` | Data Apps | Upload file to data app |
| `GET /data-apps/{data_app_id}/jobs/{job_id}` | `GetDataAppJob` | Data Apps | Poll an upload job scoped to a data app |
| `GET /data-apps/{data_app_id}/pipeline-changes` | `GetPipelineChanges` | Data Apps | Get pipeline changes for data app |
| `POST /data-apps/{data_app_id}/settings` | `UpdateDataApp` | Data Apps | Update data app settings |
| `POST /data-apps/{data_app_id}/share` | `ShareDataApp` | Data Apps | Share Data App |
| `DELETE /data-apps/{data_app_id}/users` | `RemoveSharedUser` | Data Apps | Remove a user from the data app |
| `GET /data-apps/{data_app_id}/users` | `ListSharedUsers` | Data Apps | List users the data app is shared with |
| `POST /gdpr_hooks/shopify/customers/data_request` | `ShopifyDataRequest` | Shopify Privacy Webhooks | Get requested data of shopify user |
| `POST /gdpr_hooks/shopify/customers/redact` | `ShopifyCustomerRedact` | Shopify Privacy Webhooks | Delete requested shopify customer orders data from the system |
| `POST /gdpr_hooks/shopify/shop/redact` | `ShopifyShopRedact` | Shopify Privacy Webhooks | Delete requested shopify shop's data from the system |
| `POST /gdpr_hooks/{integration_name}/deauthorization` | `DeleteUserData` | Deauthorization | Delete user's data from the system |
| `GET /health` | `HealthCheck` | System | Health Check |
| `GET /jobs` | `GetJobs` | Jobs | Track multiple job ids |
| `GET /jobs/{job_id}` | `GetJob` | Jobs | Get job by id |
| `DELETE /notifications` | `DeleteNotifications` | Notifications | Delete notifications (batch) |
| `GET /notifications` | `GetAllNotifications` | Notifications | List notifications |
| `PATCH /notifications` | `EditNotifications` | Notifications | Edit notifications (batch) |
| `DELETE /notifications/{notification_id}` | `DeleteNotification` | Notifications | Delete notification |
| `PATCH /notifications/{notification_id}` | `EditNotification` | Notifications | Edit notification |
| `GET /preferences` | `GetUserPreferences` | Preferences | Fetch user preferences |
| `PATCH /preferences` | `UpdateUserPreferences` | Preferences | Update user preferences |
| `GET /reports` | `GetReports` | Reports | Get list of reports |
| `DELETE /self` | `DeleteSelf` | Self | Delete self |
| `GET /self` | `GetUserDetails` | Self | Get request user details |
| `PATCH /self` | `UpdateUser` | Self | Update user details |
| `DELETE /self/avatar` | `DeleteAvatar` | Self | Delete profile picture |
| `POST /self/avatar` | `UploadProfilePic` | Self | Add profile picture |
| `GET /settings/users` | `ListUsersOfWorkspaces` | Owner user control settings | List users of all workspaces |
| `PATCH /settings/users` | `TransferOwnerships` | Owner user control settings | Transfer ownerships of the workspaces |
| `GET /subscription/connector-profiles` | `ListConnectorProfiles` | Connector Profiles | List all connector profiles |
| `POST /subscription/connector-profiles` | `CreateConnectorProfile` | Connector Profiles | Create a new connector profile |
| `DELETE /subscription/connector-profiles/{profile_id}` | `DeleteConnectorProfile` | Connector Profiles | Delete a connector profile |
| `PUT /subscription/connector-profiles/{profile_id}` | `UpdateConnectorProfile` | Connector Profiles | Update a connector profile |
| `POST /subscription/connector-profiles/{profile_id}/connectors` | `AddConnectorToProfile` | Connector Profiles | Add connector to profile |
| `GET /subscription/connectors` | `ListSubscriptionConnectors` | Connectors | List all connectors |
| `POST /subscription/connectors` | `CreateConnector` | Connectors | Create a new connector |
| `DELETE /subscription/connectors/{connector_id}` | `DeleteConnector` | Connectors | Delete a connector |
| `PUT /subscription/connectors/{connector_id}` | `UpdateConnector` | Connectors | Update a connector |
| `GET /subscription/feature-profiles` | `ListFeatureProfiles` | Feature Profiles | List all feature profiles |
| `POST /subscription/feature-profiles` | `CreateFeatureProfile` | Feature Profiles | Create a new feature profile |
| `DELETE /subscription/feature-profiles/{profile_id}` | `DeleteFeatureProfile` | Feature Profiles | Delete a feature profile |
| `PUT /subscription/feature-profiles/{profile_id}` | `UpdateFeatureProfile` | Feature Profiles | Update a feature profile |
| `POST /subscription/feature-profiles/{profile_id}/features` | `AddFeatureToProfile` | Feature Profiles | Add feature to profile |
| `GET /subscription/features` | `ListFeatures` | Features | List all features |
| `POST /subscription/features` | `CreateFeature` | Features | Create a new feature |
| `DELETE /subscription/features/{feature_id}` | `DeleteFeature` | Features | Delete a feature |
| `PUT /subscription/features/{feature_id}` | `UpdateFeature` | Features | Update a feature |
| `GET /subscription/plans` | `ListSubscriptionPlans` | Subscription Plans | List all subscription plans |
| `POST /subscription/plans` | `CreatePlan` | Subscription Plans | Create a new subscription plan |
| `DELETE /subscription/plans/{plan_id}` | `DeletePlan` | Subscription Plans | Delete a subscription plan |
| `GET /subscription/plans/{plan_id}` | `GetPlan` | Subscription Plans | Get a specific plan |
| `PUT /subscription/plans/{plan_id}` | `UpdatePlan` | Subscription Plans | Update a subscription plan |
| `POST /subscription/plans/{plan_id}/archive` | `ArchivePlan` | Subscription Plans | Archive a subscription plan |
| `PUT /subscription/plans/{plan_id}/storage-tiers` | `UpdateStorageTiers` | Subscription Plans | Update storage tiers for a plan |
| `GET /subscription/self-serve-plans` | `ListSelfServePlans` | Self-Serve Subscription Plans | List all subscription plans for self-serve |
| `POST /subscription/stripe/webhook` | `HandleStripeWebhook` | Stripe Webhooks | Handle Stripe webhook |
| `GET /support/sms` | `GetPlans` | Subscriptions Support | Get available plans and other chargebee resources |
| `PATCH /support/users` | `UpdateUserVerification` | Registration Support | Update user details |
| `POST /support/users` | `RegisterUser` | Registration Support | Register a user |
| `GET /support/workspaces` | `ListWorkspaces` | Workspaces Support | Get workspaces list |
| `POST /support/workspaces` | `CreateWorkspaces` | Workspaces Support | Create new workspace |
| `DELETE /support/workspaces/{workspace_id}` | `DeleteWorkspace` | Workspaces Support | Delete a workspace |
| `GET /support/workspaces/{workspace_id}` | `GetWorkspaceDetail` | Workspaces Support | Get workspace details |
| `PATCH /support/workspaces/{workspace_id}` | `UpdateWorkspaceDetail` | Workspaces Support | Update workspace details |
| `POST /support/workspaces/{workspace_id}/restore-access` | `RestoreWorkspaceAccess` | Workspaces Support | Restore workspace user access (level 1) |
| `GET /support/workspaces/{workspace_id}/sms` | `GetSubscriptionDetail` | Subscriptions Support | Get subscription details |
| `PATCH /support/workspaces/{workspace_id}/sms` | `UpdateSubscription` | Subscriptions Support | Update subscription for workspace |
| `POST /support/workspaces/{workspace_id}/sms` | `RegisterSubscription` | Subscriptions Support | Create subscription for workspace |
| `POST /support/workspaces/{workspace_id}/suspend-access` | `SuspendWorkspaceAccess` | Workspaces Support | Suspend workspace user access (level 1) |
| `GET /support/workspaces/{workspace_id}/users` | `GetUserList` | Users Support | Get users list |
| `PATCH /support/workspaces/{workspace_id}/users` | `TransferUserRoles` | Users Support | Transfer workspace ownership |
| `POST /support/workspaces/{workspace_id}/users` | `AddUserToWorkspace` | Users Support | Add a user to the workspace |
| `DELETE /support/workspaces/{workspace_id}/users/{user_id}` | `RemoveWorkspaceUser` | Users Support | Remove a user in a workspace |
| `GET /unsubscribe` | `UnsubscribeMessaging` | Unsubscribe Messaging | Unsubscribe from messaging |
| `GET /webhooks/data/{webhook_uri}` | `AddDataToWebhookUsingGetMethod` | Webhooks | Add data to the webhook |
| `POST /webhooks/data/{webhook_uri}` | `AddDataToWebhook` | Webhooks | Add data to webhook |
| `GET /workspaces` | `GetWorkspaces` | Workspaces | Get workspaces |
| `POST /workspaces` | `CreateWorkspace` | Workspaces | Create workspace |
| `DELETE /workspaces/{workspace_id}` | `DeleteUserWorkspace` | Workspaces | Delete a workspace |
| `GET /workspaces/{workspace_id}` | `GetWorkspace` | Workspaces | Get workspace details |
| `PATCH /workspaces/{workspace_id}` | `UpdateWorkspace` | Workspaces | Update workspace |
| `GET /workspaces/{workspace_id}/active_connectors` | `GetActiveConnectors` | Connections | Get Active Connectors |
| `POST /workspaces/{workspace_id}/activity_log` | `GetActivityLogs` | Activity Logs | Get requested activity logs |
| `POST /workspaces/{workspace_id}/activity_log/export` | `ExportActivityLogs` | Activity Logs | Export activity logs |
| `DELETE /workspaces/{workspace_id}/addons/connectors` | `RemoveConnectorAddon` | Workspaces | Remove connector addon from workspace |
| `POST /workspaces/{workspace_id}/addons/connectors` | `AddConnectorAddon` | Workspaces | Add connector addon to workspace |
| `DELETE /workspaces/{workspace_id}/addons/storage` | `RemoveStorageAddon` | Workspaces | Remove storage addon from workspace |
| `POST /workspaces/{workspace_id}/addons/storage` | `AddStorageAddon` | Workspaces | Add storage addon to workspace |
| `DELETE /workspaces/{workspace_id}/addons/users` | `RemoveUserSeatsAddon` | Workspaces | Remove user seats addon from workspace |
| `POST /workspaces/{workspace_id}/addons/users` | `AddUserSeatsAddon` | Workspaces | Add user seats addon to workspace |
| `POST /workspaces/{workspace_id}/ai/check-expression` | `GenerateCheckExpression` | Workflow AI | Generate data check expression |
| `GET /workspaces/{workspace_id}/app-usage` | `GetAppUsage` | App Usage | Get app usage details |
| `GET /workspaces/{workspace_id}/browse` | `BrowseWorkspaceWorkspaces` | Browse | Browse and discover workspace resources |
| `GET /workspaces/{workspace_id}/chargebee-plan` | `GetChargebeePlan` | Chargebee Plan | Get Chargebee plan |
| `GET /workspaces/{workspace_id}/clientapps` | `ListApps` | Client Apps | Get list of client apps |
| `POST /workspaces/{workspace_id}/clientapps` | `CreateApp` | Client Apps | Create api tokens to access api |
| `DELETE /workspaces/{workspace_id}/clientapps/{client_key}` | `DeleteApp` | Client Apps | Delete a client app |
| `GET /workspaces/{workspace_id}/clientapps/{client_key}` | `AppDetails` | Client Apps | Get client app details |
| `PATCH /workspaces/{workspace_id}/clientapps/{client_key}` | `UpdateApp` | Client Apps | Update client app |
| `GET /workspaces/{workspace_id}/connectors` | `ListWorkspaceConnectors` | Connectors | List connectors |
| `GET /workspaces/{workspace_id}/connectors/{connector_key}` | `GetConnector` | Connectors | Get connector details |
| `GET /workspaces/{workspace_id}/external_keys` | `GetKeysByWorkspaceId` | External keys | Get external keys of the given Workspace ID |
| `POST /workspaces/{workspace_id}/external_keys` | `AddExternalKey` | External keys | Add external keys to access the intended services |
| `DELETE /workspaces/{workspace_id}/external_keys/{key_id}` | `DeleteExternalKey` | External key | Delete an external key |
| `GET /workspaces/{workspace_id}/external_keys/{key_id}` | `GetExternalKey` | External key | Get the given external key |
| `POST /workspaces/{workspace_id}/invoices/charge` | `ChargeWorkspaceInvoices` | Workspaces | Charge all open invoices for workspace |
| `POST /workspaces/{workspace_id}/llm` | `RunLlmTask` | LLM, Workspaces | Trigger an LLM-based task for a workspace |
| `POST /workspaces/{workspace_id}/mm-ue` | `Create` | Mammoth User Events | Post mammoth user event |
| `GET /workspaces/{workspace_id}/parameters` | `ListParameters` | Parameters | List parameters |
| `POST /workspaces/{workspace_id}/parameters` | `CreateParameter` | Parameters | Create parameter |
| `GET /workspaces/{workspace_id}/parameters/groups` | `ListGroups` | Parameters | List parameter groups |
| `POST /workspaces/{workspace_id}/parameters/groups` | `CreateGroup` | Parameters | Create parameter group |
| `POST /workspaces/{workspace_id}/parameters/groups/reorder` | `ReorderGroups` | Parameters | Reorder parameter groups |
| `DELETE /workspaces/{workspace_id}/parameters/groups/{group_id}` | `DeleteGroup` | Parameters | Delete parameter group |
| `PATCH /workspaces/{workspace_id}/parameters/groups/{group_id}` | `UpdateGroup` | Parameters | Update parameter group |
| `POST /workspaces/{workspace_id}/parameters/rerun-all-stale` | `RerunAllStale` | Parameters | Rerun all stale pipelines |
| `DELETE /workspaces/{workspace_id}/parameters/{parameter_id}` | `DeleteParameter` | Parameters | Delete parameter |
| `GET /workspaces/{workspace_id}/parameters/{parameter_id}` | `GetParameterDetail` | Parameters | Get parameter detail |
| `PATCH /workspaces/{workspace_id}/parameters/{parameter_id}` | `UpdateParameter` | Parameters | Update parameter |
| `GET /workspaces/{workspace_id}/parameters/{parameter_id}/dependencies` | `GetParameterDependencies` | Parameters | Get parameter dependencies |
| `POST /workspaces/{workspace_id}/parameters/{parameter_id}/duplicate` | `DuplicateParameter` | Parameters | Duplicate parameter |
| `POST /workspaces/{workspace_id}/parameters/{parameter_id}/rerun` | `RerunParameter` | Parameters | Rerun stale pipelines for parameter |
| `DELETE /workspaces/{workspace_id}/projects` | `DeleteProjects` | Projects | Delete multiple projects |
| `GET /workspaces/{workspace_id}/projects` | `GetProject` | Projects | Get list of projects |
| `PATCH /workspaces/{workspace_id}/projects` | `UpdateProjects` | Projects | Update multiple projects by adding/removing users or changing roles of the users |
| `POST /workspaces/{workspace_id}/projects` | `CreateProject` | Projects | Create a new project in given workspace |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}` | `DeleteProject` | Projects | Delete a project |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}` | `UpdateProject` | Projects | Update a project |
| `POST /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat` | `Chat` | AI, Connector Chat | Chat with AI to configure a REST API connection |
| `POST /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/column-selection` | `SubmitColumnSelection` | AI, Connector Chat | Submit column selection out-of-band for the chat session |
| `POST /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/credentials` | `SubmitCredentials` | AI, Connector Chat | Submit credentials out-of-band for the chat session |
| `GET /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/history` | `GetChatHistory` | AI, Connector Chat | Get chat history for a connection created via AI chat |
| `GET /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/oauth-callback` | `OauthCallback` | AI, Connector Chat | OAuth2 authorization code callback |
| `GET /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/sessions` | `ListSessions` | AI, Connector Chat | List recent AI chat sessions for the current user |
| `GET /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/sessions/{session_id}/messages` | `GetSessionMessages` | AI, Connector Chat | Get display messages for a chat session |
| `GET /workspaces/{workspace_id}/projects/{project_id}/annotations` | `ListAnnotations` | Annotations | List annotations |
| `POST /workspaces/{workspace_id}/projects/{project_id}/annotations` | `CreateAnnotation` | Annotations | Create annotation |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/annotations/{annotation_id}` | `DeleteAnnotation` | Annotations | Delete annotation |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/annotations/{annotation_id}` | `PatchAnnotation` | Annotations | Update annotation status |
| `POST /workspaces/{workspace_id}/projects/{project_id}/annotations/{annotation_id}/comments` | `AddComment` | Annotations | Add comment |
| `GET /workspaces/{workspace_id}/projects/{project_id}/automations` | `GetList` | Automations | Get list of automations |
| `POST /workspaces/{workspace_id}/projects/{project_id}/automations` | `CreateAutomation` | Automations | Create automation |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/automations/{automation_id}` | `DeleteAutomation` | Automations | Delete automation and its tasks |
| `GET /workspaces/{workspace_id}/projects/{project_id}/automations/{automation_id}` | `GetAutomation` | Automations | Get automation data |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/automations/{automation_id}` | `UpdateAutomation` | Automations | Update automation related data |
| `POST /workspaces/{workspace_id}/projects/{project_id}/automations/{automation_id}/restore` | `RestoreAutomation` | Automations | Restore automation from trash |
| `POST /workspaces/{workspace_id}/projects/{project_id}/automations/{automation_id}/trash` | `TrashAutomation` | Automations | Move automation to trash |
| `GET /workspaces/{workspace_id}/projects/{project_id}/browse` | `BrowseProjectProjects` | Browse | Browse and discover project resources |
| `GET /workspaces/{workspace_id}/projects/{project_id}/checkpoints` | `GetProjectCheckpoints` | Project pipeline checkpoints | Get all checkpoints across a project |
| `GET /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections` | `ListConnections` | Connections | List Connections |
| `POST /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections` | `SaveConnection` | Connections | Create Connection |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}` | `DeleteConnection` | Connections | Delete Connection |
| `GET /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}` | `GetConnection` | Connections | Get Connection |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}` | `UpdateConnection` | Connections | Update Connection |
| `GET /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/chat` | `GetChatStatus` | QueryGen | Get status |
| `POST /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/chat` | `GetQuerySuggestion` | QueryGen | Generate query |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/ds_configs` | `DeleteDsConfigs` | DsConfig | Delete ds configs |
| `GET /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/ds_configs` | `ListDsConfigs` | DsConfig | List ds configs |
| `POST /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/ds_configs` | `ValidateAndGetDsConfig` | DsConfig | Validate and get sample data |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}` | `DeleteDsConfig` | DsConfig | Delete ds config |
| `GET /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}` | `GetDsConfig` | DsConfig | Get ds config details |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}` | `UpdateDsConfigs` | DsConfig | Validate and get sample data |
| `GET /workspaces/{workspace_id}/projects/{project_id}/credentials` | `GetPublishCredentials` | Publish Credentials | Get Publish Credentials |
| `GET /workspaces/{workspace_id}/projects/{project_id}/data-checks` | `GetProjectDataChecks` | Project pipeline data checks | Get all data checks across a project |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets` | `DeleteDatasets` | Datasets | Delete multiple datasets |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets` | `GetDatasets` | Datasets | Get list of datasets |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets` | `UpdateDatasets` | Datasets | Update datasets name |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets` | `CreateDatasets` | Datasets | Create dataset |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets-from-pdf` | `CreateDatasetFromPdf` | Datasets from PDF | Create datasets from Selected Tables of PDF |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}` | `DeleteDataset` | Datasets | Delete dataset |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}` | `GetDataset` | Datasets | Get dataset details |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}` | `UpdateDataset` | Datasets | Update dataset |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches` | `DeleteBatches` | Batches | Delete multiple batches |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches` | `GetBatches` | Batches | List batches |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches` | `UpdateBatches` | Batches | Update batches |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches` | `CreateBatch` | Batches | Create batch |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches/{batch_id}` | `DeleteBatch` | Batches | Delete batch |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches/{batch_id}` | `GetBatch` | Batches | List batches |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/data` | `GetDatasetData` | Datasets | Get dataset data |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews` | `DeleteMultipleDataviews` | Dataviews | Delete multiple dataviews |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews` | `ListDataviews` | Dataviews | Get list of dataviews present in a dataset |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews` | `AddDataview` | Dataviews | Create or duplicate dataview |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}` | `DeleteDataview` | Dataviews | Delete dataview safely |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}` | `GetDataviewInformationIndividual` | Dataviews | Get dataview information |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}` | `Patch` | Dataviews | Patch dataview |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/activities` | `GetActiveUsers` | Dataviews | Get list of active users on this dataview |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/activities` | `MarkActiveUser` | Dataviews | Mark active user on this dataview |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format` | `DeleteConditionalFormat` | Conditional Format | delete conditional format |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format` | `GetConditionalFormat` | Conditional Format | get conditional format |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format` | `UpdateConditionalFormat` | Conditional Format | update conditional format |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format` | `CreateConditionalFormat` | Conditional Format | create conditional format |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data` | `GetDataviewData` | Dataviews | Get dataview data |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data` | `GetDataviewDataPost` | Dataviews | Get dataview data |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data/generate` | `GetValidationInfo` | Generate AI data | Get validation information |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data/generate` | `Preview` | Generate AI data | Generate AI preview data for a dataview for the given sequence |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data/query` | `ExecuteVolatileQuery` | Dataviews | Execute volatile query on dataview |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/derivatives` | `ListDerivatives` | Derivatives | List derivatives for a dataview |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/derivatives` | `CreateDerivative` | Derivatives | Create a derivative |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/derivatives/{derivative_id}` | `DeleteDerivative` | Derivatives | Delete a derivative |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/derivatives/{derivative_id}` | `EditDerivative` | Derivatives | Edit a derivative |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/derivatives/{derivative_id}/data` | `FetchDerivativeData` | Derivatives | Fetch derivative data |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/draft-mode` | `ExecutePipelineDraftCommand` | Dataview Draft Mode | Execute pipeline draft command |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/parameter-context` | `GetParameterContext` | Parameters | Get parameter context for pipeline |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline` | `GetPipeline` | Dataview pipeline | Get dataview pipeline information |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline` | `EditPipeline` | Dataview pipeline | Edit and perform bulk operations on a dataview pipeline |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/checkpoints` | `GetPipelineCheckpoints` | Dataview pipeline checkpoints | Get dataview pipeline checkpoints |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/checkpoints` | `AddCheckpoint` | Dataview pipeline checkpoints | Add a checkpoint |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/checkpoints/{checkpoint_id}` | `DeleteCheckpoint` | Dataview pipeline Checkpoint | Delete a pipeline checkpoint |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/checkpoints/{checkpoint_id}` | `GetPipelineCheckpoint` | Dataview pipeline Checkpoint | Get the given dataview pipeline checkpoint |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/checkpoints/{checkpoint_id}` | `EditPatches` | Dataview pipeline Checkpoint | Edit and perform operations on a pipeline checkpoint |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/data-checks` | `GetPipelineDataChecks` | Dataview pipeline data checks | Get dataview pipeline data checks |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/data-checks` | `AddDataCheck` | Dataview pipeline data checks | Add a data check |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/data-checks/{data_check_id}` | `DeleteDataCheck` | Dataview pipeline data check | Delete a pipeline data check |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/data-checks/{data_check_id}` | `GetPipelineDataCheck` | Dataview pipeline data check | Get the given dataview pipeline data check |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/data-checks/{data_check_id}` | `EditDatacheck` | Dataview pipeline data check | Edit and perform operations on a pipeline data check |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports` | `GetPipelineExports` | Dataview pipeline Exports | Get dataview pipeline exports information |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports` | `AddExport` | Dataview pipeline Exports | Add a export in the pipeline |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports/{export_id}` | `DeleteExport` | Dataview pipeline Export | Delete an export |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports/{export_id}` | `GetPipelineExport` | Dataview pipeline Export | Get dataview pipeline export information |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports/{export_id}` | `EditExport` | Dataview pipeline Export | Edit a dataview pipeline export |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/items` | `GetPipelineItems` | Dataview pipeline Items | Get dataview pipeline items |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/rerun` | `RerunFromSequence` | Dataview pipeline | Rerun pipeline from a specific step |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/task_preview` | `GetTaskPreview` | Dataview pipeline Task preview | Get task preview |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/tasks` | `GetPipelineTasks` | Dataview pipeline Tasks | Get dataview pipeline tasks information |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/tasks` | `AddTask` | Dataview pipeline Tasks | Add a task in the pipeline |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/tasks/{task_id}` | `DeleteTask` | Dataview pipeline Task | Delete a task |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/tasks/{task_id}` | `GetPipelineTask` | Dataview pipeline Task | Get dataview pipeline task information |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/tasks/{task_id}` | `EditTask` | Dataview pipeline Task | Edit a dataview pipeline task |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/versions` | `GetPipelineVersions` | Pipeline Versioning | Get pipeline versions |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/versions/{version_id}` | `DeletePipelineVersion` | Pipeline Versioning | Delete a pipeline version |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/versions/{version_id}` | `GetPipelineVersion` | Pipeline Versioning | Get a pipeline version |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/versions/{version_id}` | `EditPipelineVersion` | Pipeline Versioning | Edit a pipeline version |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/versions/{version_id}` | `ApplyPipelineVersion` | Pipeline Versioning | Apply a pipeline version |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/preview` | `GetDataviewPreview` | Dataviews | Get dataview data preview |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/profile_generation` | `GenerateProfile` | Dataviews, Generate Profile | Generate or Update Dataset Profile |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/publish-to-db` | `UpdatePublishToDb` | Publish to DB | Update Publish to DB credentials |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/publish-to-db` | `CreatePublishToDb` | Publish to DB | Publish view to external database |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/restore` | `RestoreDataview` | Dataviews | Restore dataview from trash |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/trash` | `TrashDataview` | Dataviews | Move dataview to trash |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/file_settings` | `UndoFileSettings` | FileDataSettings | Undo updates done on dataset file settings |
| `GET /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/file_settings` | `GetFileSettings` | FileDataSettings | Get File Settings |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/file_settings` | `UpdateFileSettings` | FileDataSettings | Updates dataset file settings |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/restore` | `RestoreDataset` | Datasets | Restore dataset from trash |
| `POST /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/trash` | `TrashDataset` | Datasets | Move dataset to trash |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/files` | `DeleteFiles` | Files | Delete files |
| `GET /workspaces/{workspace_id}/projects/{project_id}/files` | `ListFiles` | Files | List files |
| `POST /workspaces/{workspace_id}/projects/{project_id}/files` | `CreateFileDataset` | Files | Upload file or folder |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/files/{file_id}` | `DeleteFile` | Files | Delete file |
| `GET /workspaces/{workspace_id}/projects/{project_id}/files/{file_id}` | `GetFileDetails` | Files | Get file details |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/files/{file_id}` | `UpdateFileConfigs` | Files | Updates the file configs |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/folders` | `DeleteFolders` | Folders | Delete folders |
| `GET /workspaces/{workspace_id}/projects/{project_id}/folders` | `ListFolders` | Folders | List folders |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/folders` | `UpdateFolderResources` | Folders | Move resources from/to folder |
| `POST /workspaces/{workspace_id}/projects/{project_id}/folders` | `CreateFolder` | Folders | Create Folder |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/folders/{folder_id}` | `DeleteFolder` | Folders | Delete Folder |
| `GET /workspaces/{workspace_id}/projects/{project_id}/folders/{folder_id}` | `GetFolder` | Folders | Get Folder Details |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/folders/{folder_id}` | `UpdateFolderDetails` | Folders | Updates the folder details |
| `GET /workspaces/{workspace_id}/projects/{project_id}/folders/{folder_id}/browse` | `BrowseFolderFolders` | Browse | Browse and discover folder resources |
| `POST /workspaces/{workspace_id}/projects/{project_id}/folders/{folder_id}/trash` | `TrashFolder` | Folders | Trash a folder's contents |
| `GET /workspaces/{workspace_id}/projects/{project_id}/pending-changes` | `GetPendingChanges` | Projects | Get pending changes for a project |
| `GET /workspaces/{workspace_id}/projects/{project_id}/resource-dependencies` | `GetResourceDependencies` | Projects | Get resource dependencies |
| `GET /workspaces/{workspace_id}/projects/{project_id}/resource-status` | `GetResourceStatus` | Projects | Get resource status |
| `POST /workspaces/{workspace_id}/projects/{project_id}/sample-flow` | `CreateSampleFlow` | Sample Flow | Trigger sample-flow import |
| `GET /workspaces/{workspace_id}/projects/{project_id}/schedules` | `ListSchedules` | Schedules | Get list of schedules |
| `POST /workspaces/{workspace_id}/projects/{project_id}/schedules` | `CreateSchedule` | Schedules | Create schedule |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/schedules/{schedule_id}` | `DeleteSchedule` | Schedules | Delete schedule data |
| `GET /workspaces/{workspace_id}/projects/{project_id}/schedules/{schedule_id}` | `GetSchedule` | Schedules | Get schedule data |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/schedules/{schedule_id}` | `PatchSchedule` | Schedules | Patch schedule related data |
| `POST /workspaces/{workspace_id}/projects/{project_id}/sql_generation` | `GenerateSql` | Dataviews, SQL Generation | Generate SQL query based on intent |
| `POST /workspaces/{workspace_id}/projects/{project_id}/sql_generation/condition` | `GenerateCondition` | Dataviews, SQL Generation | Generate SQL condition based on intent |
| `POST /workspaces/{workspace_id}/projects/{project_id}/sql_generation/expression` | `GenerateExpression` | Dataviews, SQL Generation | Generate SQL expression based on intent |
| `POST /workspaces/{workspace_id}/projects/{project_id}/suggestions` | `AiSuggestions` | Dataviews, generate AI Data | Generate AI-based Suggestions for Dataview |
| `GET /workspaces/{workspace_id}/projects/{project_id}/trash` | `ListTrash` | Trash | List trashed items |
| `POST /workspaces/{workspace_id}/projects/{project_id}/trash` | `BulkTrash` | Trash | Move multiple items to Trash |
| `POST /workspaces/{workspace_id}/projects/{project_id}/trash/restore` | `BulkRestore` | Trash | Restore multiple items from Trash |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/users` | `RemoveUserProject` | Projects | Remove user from a project |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/users` | `UpdateUserProject` | Projects | Update user role on a project |
| `POST /workspaces/{workspace_id}/projects/{project_id}/users` | `AddUserProject` | Projects | Add user to a project |
| `GET /workspaces/{workspace_id}/projects/{project_id}/webhooks` | `ListWebhooks` | Webhooks | List webhooks |
| `POST /workspaces/{workspace_id}/projects/{project_id}/webhooks` | `CreateAWebhook` | Webhooks | Create a webhook |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/webhooks/{webhook_id}` | `DeleteWebhook` | Webhooks | Delete webhook |
| `GET /workspaces/{workspace_id}/projects/{project_id}/webhooks/{webhook_id}` | `GetWebhookDetails` | Webhooks | Get webhook details |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/webhooks/{webhook_id}` | `UpdateWebhookConfigurations` | Webhooks | Updates the webhook |
| `GET /workspaces/{workspace_id}/projects/{project_id}/workflows` | `ListWorkflows` | Workflows | List workflows |
| `POST /workspaces/{workspace_id}/projects/{project_id}/workflows` | `CreateWorkflow` | Workflows | Create a workflow |
| `POST /workspaces/{workspace_id}/projects/{project_id}/workflows/cleanup` | `CleanupGhostWorkflows` | Workflows | Cleanup ghost workflows |
| `POST /workspaces/{workspace_id}/projects/{project_id}/workflows/from-template` | `InstantiateFromTemplate` | Workflows | Instantiate workflow from template |
| `GET /workspaces/{workspace_id}/projects/{project_id}/workflows/graph` | `GetProjectWorkflowGraph` | Workflows | Get project workflow graph |
| `GET /workspaces/{workspace_id}/projects/{project_id}/workflows/workspace-datasets` | `ListWorkspaceDatasets` | Workflows | List workspace datasets |
| `GET /workspaces/{workspace_id}/projects/{project_id}/workflows/workspace-exports` | `ListWorkspaceExports` | Workflows | List workspace exports |
| `GET /workspaces/{workspace_id}/projects/{project_id}/workflows/workspace-sources` | `ListWorkspaceSources` | Workflows | List workspace sources |
| `DELETE /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}` | `DeleteWorkflow` | Workflows | Delete a workflow |
| `GET /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}` | `GetWorkflow` | Workflows | Get a workflow |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}` | `UpdateWorkflow` | Workflows | Update a workflow |
| `POST /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}/blocks` | `AddSkeletonBlock` | Workflows | Add skeleton block |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}/blocks/{block_id}/auth` | `PatchBlockAuth` | Workflows | Store block auth credentials |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}/blocks/{block_id}/config` | `PromoteSkeletonBlock` | Workflows | Promote skeleton block |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}/blocks/{block_id}/type` | `PatchBlockType` | Workflows | Assign block type |
| `PATCH /workspaces/{workspace_id}/projects/{project_id}/workflows/{workflow_id}/canvas` | `UpdateCanvasState` | Workflows | Update canvas state |
| `POST /workspaces/{workspace_id}/reactivate` | `ReactivateWorkspace` | Workspaces | Reactivate a workspace |
| `GET /workspaces/{workspace_id}/snippets` | `ListSnippets` | Snippets | List snippets |
| `POST /workspaces/{workspace_id}/snippets` | `CreateSnippet` | Snippets | Create snippet |
| `DELETE /workspaces/{workspace_id}/snippets/{snippet_id}` | `DeleteSnippet` | Snippets | Delete snippet |
| `GET /workspaces/{workspace_id}/snippets/{snippet_id}` | `GetSnippetDetail` | Snippets | Get snippet detail |
| `PATCH /workspaces/{workspace_id}/snippets/{snippet_id}` | `UpdateSnippet` | Snippets | Update snippet |
| `GET /workspaces/{workspace_id}/snippets/{snippet_id}/dependencies` | `GetSnippetDependencies` | Snippets | Get snippet dependencies |
| `POST /workspaces/{workspace_id}/snippets/{snippet_id}/duplicate` | `DuplicateSnippet` | Snippets | Duplicate snippet |
| `POST /workspaces/{workspace_id}/snippets/{snippet_id}/rerun` | `RerunSnippet` | Snippets | Rerun stale pipelines for snippet |
| `GET /workspaces/{workspace_id}/split-segments` | `GetSegments` | Split Segments | Get segments and features |
| `PATCH /workspaces/{workspace_id}/split-segments` | `UpdateSegments` | Split Segments | Update segments with workspace Id |
| `GET /workspaces/{workspace_id}/storage-breakdown` | `GetStorageBreakdown` | Storage | Get storage breakdown |
| `GET /workspaces/{workspace_id}/subscription` | `GetWorkspaceSubscription` | Stripe Subscriptions | Get workspace subscription from Stripe |
| `POST /workspaces/{workspace_id}/subscription` | `CreateWorkspaceSubscription` | Stripe Subscriptions | Create Stripe subscription for workspace |
| `GET /workspaces/{workspace_id}/subscription/billing-history` | `GetWorkspaceBillingHistory` | Stripe Subscriptions | Get workspace billing history from Stripe |
| `POST /workspaces/{workspace_id}/subscription/cancel` | `CancelWorkspaceSubscription` | Stripe Subscriptions | Cancel workspace subscription in Stripe |
| `POST /workspaces/{workspace_id}/subscription/create-checkout` | `CreateCheckoutUrl` | Stripe Subscriptions | Create Stripe checkout URL for workspace subscription |
| `POST /workspaces/{workspace_id}/subscription/customer-portal` | `CreateCustomerPortalUrl` | Stripe Subscriptions | Create Stripe customer portal URL |
| `POST /workspaces/{workspace_id}/subscription/end-trial` | `EndTrialAndStartSubscription` | Stripe Subscriptions | End trial immediately and start subscription |
| `GET /workspaces/{workspace_id}/subscription/payment-methods` | `GetPaymentMethods` | Stripe Subscriptions | Get workspace payment methods from Stripe |
| `POST /workspaces/{workspace_id}/subscription/payment-methods/default` | `SetDefaultPaymentMethod` | Stripe Subscriptions | Set default payment method |
| `DELETE /workspaces/{workspace_id}/subscription/payment-methods/{payment_method_id}` | `DeletePaymentMethod` | Stripe Subscriptions | Delete payment method |
| `GET /workspaces/{workspace_id}/subscription/preview-invoice` | `PreviewInvoice` | Stripe Subscriptions | Preview next invoice |
| `POST /workspaces/{workspace_id}/subscription/retry-payment` | `RetryPayment` | Stripe Subscriptions | Retry payment on open invoices |
| `GET /workspaces/{workspace_id}/subscription/status` | `GetWorkspaceSubscriptionStatus` | Stripe Subscriptions | Get workspace subscription status |
| `POST /workspaces/{workspace_id}/subscription/sync` | `SyncSubscription` | Stripe Subscriptions | Sync subscription status from Stripe |
| `GET /workspaces/{workspace_id}/subscription/upcoming-invoice` | `GetUpcomingInvoice` | Stripe Subscriptions | Get upcoming invoice from Stripe |
| `GET /workspaces/{workspace_id}/subscription/usage` | `GetWorkspaceUsage` | Stripe Subscriptions | Get workspace usage from Stripe |
| `GET /workspaces/{workspace_id}/subscription_v1` | `GetWkspSubscriptionDetail` | Subscription | Get subscription details |
| `PATCH /workspaces/{workspace_id}/subscription_v1` | `UpdateSubscriptionDetail` | Subscription | Update subscription details |
| `POST /workspaces/{workspace_id}/subscription_v1/hosted-page` | `FetchHostedPage` | Subscription | Get hosted pages |
| `GET /workspaces/{workspace_id}/subscription_v1/invoices` | `ListInvoices` | Subscription | List all invoices |
| `GET /workspaces/{workspace_id}/subscription_v1/invoices/{invoice_id}` | `GetInvoice` | Subscription | Get associated plan details |
| `GET /workspaces/{workspace_id}/templates` | `ListTemplates` | Workflow Templates | List workflow templates |
| `POST /workspaces/{workspace_id}/templates` | `CreateTemplate` | Workflow Templates | Create a workflow template |
| `DELETE /workspaces/{workspace_id}/templates/{template_id}` | `DeleteTemplate` | Workflow Templates | Delete a workflow template |
| `GET /workspaces/{workspace_id}/templates/{template_id}` | `GetTemplate` | Workflow Templates | Get a workflow template |
| `PATCH /workspaces/{workspace_id}/templates/{template_id}` | `UpdateTemplate` | Workflow Templates | Update a workflow template |
| `DELETE /workspaces/{workspace_id}/users` | `RemoveUserFromWorkspace` | Workspaces | Remove users or invites from workspace |
| `GET /workspaces/{workspace_id}/users` | `GetUsersInWorkspace` | Workspaces | Get users in workspace |
| `PATCH /workspaces/{workspace_id}/users` | `UpdateUserToWorkspace` | Workspaces | Resend invite, remove invitation, or change role in workspace |
| `POST /workspaces/{workspace_id}/users` | `AddUserInWorkspace` | Workspaces | Add user in workspace |
| `DELETE /workspaces/{workspace_id}/users/{user_id}` | `RemoveUser` | Workspaces | Remove user from workspace/Leave workspace |
| `PATCH /workspaces/{workspace_id}/users/{user_id}` | `UpdateUserInWorkspace` | Workspaces | Change user role in workspace |
