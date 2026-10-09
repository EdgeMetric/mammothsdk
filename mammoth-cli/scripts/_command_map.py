#!/usr/bin/env python3
"""Reviewed disposition and command mapping for all pinned OpenAPI operations.

The primary agent owns every decision here. The rule engine derives a proposed
command id from the operation's path and method; the explicit ``OVERRIDES`` and
``PROTOCOL_ONLY`` tables record the primary's reviewed decisions where rules are
insufficient. A test asserts every operation resolves to exactly one reviewed
disposition.

Dispositions:
- ``command``      user/admin can initiate it.
- ``alias``        another command has identical behavior.
- ``protocol_only``inbound webhook, callback, telemetry, or health probe.
- ``server_unavailable`` documented but unavailable (requires server evidence).
- ``deprecated``   deprecated by the OpenAPI document.
- ``internal_only``  web-app-only route with a reviewed reason; no terminal user.
- ``unmapped``     user-facing route with no CLI command yet (a real gap).
"""

from __future__ import annotations

import re

REVIEWER = "primary"

# --- Protocol-only operations (not meaningful CLI actions) -----------------
# Reviewed 2026-07-21 from the pinned snapshot: webhooks, OAuth/browser
# callbacks, telemetry events, and the health probe.
PROTOCOL_ONLY: dict[str, str] = {
    "HealthCheck": "Health probe, not a user command.",
    "UnsubscribeMessaging": "Email unsubscribe browser link, not an API action.",
    "HandleStripeWebhook": "Inbound Stripe provider webhook.",
    "ShopifyDataRequest": "Shopify GDPR privacy webhook.",
    "ShopifyCustomerRedact": "Shopify GDPR privacy webhook.",
    "ShopifyShopRedact": "Shopify GDPR privacy webhook.",
    "DeleteUserData": "Provider deauthorization callback.",
    "OauthCallback": "OAuth2 authorization-code browser callback.",
    "Create": "Mammoth user-event telemetry ingest (mm-ue).",
    "TrackHeartbeat": "Published-dashboard viewer telemetry.",
    "TrackView": "Published-dashboard viewer telemetry.",
}

# --- Server routes that exist for the web app, not for a CLI user ----------
# Keyed by operationId; value is the reviewed reason. Reviewed 2026-10-02 against
# the origin/master spec. A route listed here has no command by design; a route
# that a user could drive from a terminal belongs in the matrix as unmapped
# until a command binds it.
INTERNAL_ONLY: dict[str, str] = {
    "AgentNotifyJob": "Web-app callback: tells a connector agent that its async job finished.",
    "WatchAgentTurn": "Server-Sent Events stream of one agent turn; a terminal cannot hold it.",
    "ResourceEventsStream": "Server-Sent Events stream of project resource changes (web app).",
    "GetDraftHead": "Canvas editor poll that announces a colleague's draft change.",
    "PostPresence": "Canvas editor presence heartbeat (every ~15 seconds per open tab).",
    "TrackAction": "Viewer-side counter for outward actions such as a copied link.",
    "DashboardPublicGallery": "Public gallery HTML page for browsers and search engines.",
    "DashboardPublicGalleryHead": "HEAD twin of the public gallery HTML page.",
    "DashboardPublicGallerySitemap": "Public gallery sitemap.xml for search engines.",
    "DashboardPublicGallerySitemapHead": "HEAD twin of the public gallery sitemap.",
    "DashboardPublicGalleryTemplate": "Public gallery template HTML page for browsers.",
    "DashboardPublicGalleryTemplateHead": "HEAD twin of the public gallery template page.",
    "DashboardPublicTemplatesHead": "HEAD twin of the public template catalog.",
    "DashboardPublicTemplateHead": "HEAD twin of one public template read.",
    "DashboardPublicTemplateThumbnail": "Public template picture bytes served to the gallery page.",
    "MarkAgentSessionSeen": "Web app marks a chat session read when its panel opens.",
    "AuthorizeRedirect": "OAuth browser redirect into the consent page; the browser follows it.",
    "Authorize": "Form submit from the browser OAuth consent page.",
    "GetConsentInfo": "Data the browser OAuth consent page renders before approval.",
    "Deny": "Deny button on the browser OAuth consent page.",
    "ApproveDevice": "Browser page that approves a device-code login; the terminal polls instead.",
    "DenyDevice": "Browser page that denies a device-code login.",
    "GetDeviceInfo": "Browser page that shows the device-code request before approval.",
}

# --- Routes the SDK calls that the server on master does not serve yet ------
# Keyed by ``METHOD /normalised/path`` (placeholders as ``{}``); value names the
# unmerged server branch that adds the route. An entry stops mattering once the
# route is on master and the SDK call matches a real operation.
PENDING_SERVER_RELEASE: dict[str, str] = {
    f"{method} {path}": "origin/feat/agent-cli-surface@7e2bf189c4"
    for method, path in (
        ("GET", "/agents/sessions/{}/actions"),
        ("DELETE", "/agents/sessions/{}/actions/{}"),
        ("GET", "/agents/sessions/{}/run"),
        ("GET", "/agents/sessions/{}/runs"),
        ("GET", "/agents/sessions/{}/runs/{}/units"),
        ("POST", "/agents/sessions/{}/runs/{}/units"),
        ("POST", "/agents/sessions/{}/runs/{}/extend"),
        ("POST", "/agents/sessions/{}/runs/{}/pause"),
        ("POST", "/agents/sessions/{}/runs/{}/resume"),
        ("POST", "/agents/sessions/{}/runs/{}/retry"),
        ("POST", "/agents/sessions/{}/runs/{}/stop"),
        ("GET", "/workspaces/current"),
        ("PATCH", "/workspaces/{}/projects/{}/datasets/{}/unstructured_rows"),
    )
}
PENDING_SERVER_RELEASE.update(
    {
        f"{method} {path}": "origin/feat/agent-cli-surface-w5@0a52995994"
        for method, path in (
            ("POST", "/dashboards/v3/attachments/{}/assess"),
            ("POST", "/dashboards/v3/attachments/{}/intent"),
            ("POST", "/workspaces/{}/dataviews/compare"),
            ("POST", "/workspaces/{}/projects/{}/copy"),
            ("GET", "/workspaces/{}/projects/{}/datasets/{}/dataviews/{}/analysis"),
            ("POST", "/workspaces/{}/projects/{}/datasets/{}/dataviews/{}/optimize"),
        )
    }
)
PENDING_SERVER_RELEASE["POST /dashboards/{}/figures"] = "origin/feat/agent-cli-surface-w8@15c7fe863f"
# On server master since the pinned master snapshot (master-20261002) was exported.
PENDING_SERVER_RELEASE.update(
    {
        f"{method} {path}": "origin/master@7a57c1b70f"
        for method, path in (
            ("GET", "/collections"),
            ("POST", "/collections"),
            ("GET", "/collections/{}"),
            ("PATCH", "/collections/{}"),
            ("DELETE", "/collections/{}"),
            ("GET", "/collections/url/{}"),
            ("GET", "/collections/for-dashboard/{}"),
            ("GET", "/collections/{}/activity"),
            ("GET", "/collections/{}/pipeline-changes"),
            ("POST", "/collections/{}/dashboards"),
            ("DELETE", "/collections/{}/dashboards/{}"),
            ("POST", "/collections/{}/share"),
            ("DELETE", "/collections/{}/members"),
            ("POST", "/collections/{}/files"),
            ("GET", "/dashboards/{}/engagement"),
            ("GET", "/dashboards/{}/engagement/people/{}"),
            ("POST", "/dashboards/{}/engagement/remind"),
            ("GET", "/dashboards/v3/{}/own-data"),
            ("POST", "/dashboards/v3/{}/own-data"),
            ("GET", "/dashboards/v3/{}/own-data/preview"),
            ("POST", "/dashboards/v3/{}/own-data/accept"),
            ("POST", "/dashboards/v3/{}/own-data/dismiss"),
        )
    }
)
# The SDK posts every run verb through one helper whose path ends in a variable.
PENDING_SERVER_RELEASE["POST /agents/sessions/{}/runs/{}/{}"] = PENDING_SERVER_RELEASE[
    "POST /agents/sessions/{}/runs/{}/stop"
]

# --- Operations that alias another command (identical behavior) ------------
OP_ALIAS: dict[str, str] = {
    # Chargebee-only invoice reads; the Stripe billing-history endpoint replaces them.
    "ListInvoices": "billing.stripe.history",
    "GetInvoice": "billing.stripe.history",
}

_CHARGEBEE_INVOICE = (
    "Chargebee-only invoice read that returns nothing for Stripe workspaces; the Stripe "
    "billing-history endpoint replaces it."
)
#: Reviewed reasons for aliases that are not identical behavior.
ALIAS_REASON: dict[str, str] = {
    "ListInvoices": _CHARGEBEE_INVOICE,
    "GetInvoice": _CHARGEBEE_INVOICE,
}

# --- Operations the pinned spec documents but the server cannot serve --------
# No command, no SDK symbol. Keyed by operationId; value is the reviewed reason.
SERVER_UNAVAILABLE: dict[str, str] = {
    "GenerateDashboard": (
        "No POST handler for this route exists in current apiv2 "
        "(apiv2/apiv2/mmai/dashboard/controller.py has no bare POST); every call 404s. "
        "Historically returned a structured 409 (4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED) "
        "per dated evidence in docs/capability-evidence/dashboard-sweep-20260918/. "
        "Use dashboard create-blank or dashboard v3 generate instead."
    ),
}

# --- Explicit reviewed command ids by operationId --------------------------
# Only operations whose command id the rule engine cannot derive correctly.
OVERRIDES: dict[str, str] = {
    # Invitations and self / user account.
    "AcceptInvite": "workspace.accept-invite",
    "GetUserDetails": "user.get",
    "UpdateUser": "user.update",
    "DeleteSelf": "user.delete-account",
    "DeleteAvatar": "user.avatar.delete",
    "UploadProfilePic": "user.avatar.upload",
    "GetUserPreferences": "user.preference.get",
    "UpdateUserPreferences": "user.preference.update",
    # Agents (AI chat).
    "AgentChat": "agent.chat",
    # Automation capabilities and dataset interpretation (bound in 2.2.x).
    "GetAutomationCapabilities": "automation.capabilities",
    "PreviewDatasetInterpretation": "dataset.interpretation.preview",
    "ConfirmDatasetInterpretation": "dataset.interpretation.confirm",
    "ListAgentSessions": "agent.session.list",
    "DeleteAgentSession": "agent.session.delete",
    "SetAgentSessionVisibility": "agent.session.set-visibility",
    "GetAgentSessionMessages": "agent.session.messages",
    # Browse scopes.
    "BrowseResources": "browse.root",
    "BrowseWorkspaceWorkspaces": "browse.workspace",
    "BrowseProjectProjects": "browse.project",
    "BrowseFolderFolders": "browse.folder",
    # Jobs.
    "GetJobs": "job.get-many",
    "GetJob": "job.get",
    # Notifications.
    "GetAllNotifications": "notification.list",
    "EditNotifications": "notification.update-batch",
    "DeleteNotifications": "notification.delete-batch",
    "EditNotification": "notification.update",
    "DeleteNotification": "notification.delete",
    # Reports and usage.
    "GetReports": "report.list",
    "GetAppUsage": "workspace.app-usage",
    "GetStorageBreakdown": "workspace.storage-breakdown",
    "GetSegments": "workspace.segment.list",
    "UpdateSegments": "workspace.segment.update",
    "RunLlmTask": "workspace.llm-task",
    "GenerateCheckExpression": "workspace.check-expression",
    # Workspaces + users.
    "GetWorkspaces": "workspace.list",
    "CreateWorkspace": "workspace.create",
    "GetWorkspace": "workspace.get",
    "UpdateWorkspace": "workspace.update",
    "DeleteUserWorkspace": "workspace.delete",
    "ReactivateWorkspace": "workspace.reactivate",
    "GetUsersInWorkspace": "workspace.user.list",
    "AddUserInWorkspace": "workspace.user.add",
    "UpdateUserToWorkspace": "workspace.user.update-batch",
    "RemoveUserFromWorkspace": "workspace.user.remove-batch",
    "UpdateUserInWorkspace": "workspace.user.update",
    "RemoveUser": "workspace.user.remove",
    "GetActiveConnectors": "connector.active",
    "GetConnector": "connector.get",
    "ListWorkspaceConnectors": "connector.list",
    # Addons.
    "AddConnectorAddon": "addon.connector.add",
    "RemoveConnectorAddon": "addon.connector.remove",
    "AddStorageAddon": "addon.storage.add",
    "RemoveStorageAddon": "addon.storage.remove",
    "AddUserSeatsAddon": "addon.user.add",
    "RemoveUserSeatsAddon": "addon.user.remove",
    # Client apps + external keys.
    "ListApps": "client-app.list",
    "CreateApp": "client-app.create",
    "AppDetails": "client-app.get",
    "UpdateApp": "client-app.update",
    "DeleteApp": "client-app.delete",
    "GetKeysByWorkspaceId": "external-key.list",
    "AddExternalKey": "external-key.create",
    "GetExternalKey": "external-key.get",
    "DeleteExternalKey": "external-key.delete",
    # Activity logs.
    "GetActivityLogs": "activity.list",
    "ExportActivityLogs": "activity.export",
    # Chargebee / billing v1 + invoices + Stripe subscription.
    "GetChargebeePlan": "billing.chargebee-plan",
    "GetWkspSubscriptionDetail": "billing.subscription.get",
    "UpdateSubscriptionDetail": "billing.subscription.update",
    "FetchHostedPage": "billing.hosted-page",
    "ChargeWorkspaceInvoices": "billing.invoice.charge",
    "GetWorkspaceSubscription": "billing.stripe.get",
    "CreateWorkspaceSubscription": "billing.stripe.create",
    "GetWorkspaceBillingHistory": "billing.stripe.history",
    "CancelWorkspaceSubscription": "billing.stripe.cancel",
    "CreateCheckoutUrl": "billing.stripe.checkout-url",
    "CreateCustomerPortalUrl": "billing.stripe.portal-url",
    "EndTrialAndStartSubscription": "billing.stripe.end-trial",
    "GetPaymentMethods": "billing.stripe.payment-method.list",
    "SetDefaultPaymentMethod": "billing.stripe.payment-method.set-default",
    "DeletePaymentMethod": "billing.stripe.payment-method.delete",
    "PreviewInvoice": "billing.stripe.preview-invoice",
    "RetryPayment": "billing.stripe.retry-payment",
    "GetWorkspaceSubscriptionStatus": "billing.stripe.status",
    "SyncSubscription": "billing.stripe.sync",
    "GetUpcomingInvoice": "billing.stripe.upcoming-invoice",
    "GetWorkspaceUsage": "billing.stripe.usage",
    # Support (support/* administration).
    "GetPlans": "support.plan.chargebee-list",
    "UpdateUserVerification": "support.user.update",
    "RegisterUser": "support.user.register",
    "ListWorkspaces": "support.workspace.list",
    "CreateWorkspaces": "support.workspace.create",
    "DeleteWorkspace": "support.workspace.delete",
    "GetWorkspaceDetail": "support.workspace.get",
    "UpdateWorkspaceDetail": "support.workspace.update",
    "RestoreWorkspaceAccess": "support.workspace.restore-access",
    "SuspendWorkspaceAccess": "support.workspace.suspend-access",
    "GetSubscriptionDetail": "support.subscription.get",
    "UpdateSubscription": "support.subscription.update",
    "RegisterSubscription": "support.subscription.create",
    "GetUserList": "support.workspace.user.list",
    "TransferUserRoles": "support.workspace.user.transfer",
    "AddUserToWorkspace": "support.workspace.user.add",
    "RemoveWorkspaceUser": "support.workspace.user.remove",
    "ListUsersOfWorkspaces": "support.user.list-all",
    "TransferOwnerships": "support.ownership.transfer",
    # Subscription admin (connector/feature profiles, plans).
    "ListConnectorProfiles": "support.connector-profile.list",
    "CreateConnectorProfile": "support.connector-profile.create",
    "DeleteConnectorProfile": "support.connector-profile.delete",
    "UpdateConnectorProfile": "support.connector-profile.update",
    "AddConnectorToProfile": "support.connector-profile.add-connector",
    "ListSubscriptionConnectors": "support.connector.list",
    "CreateConnector": "support.connector.create",
    "DeleteConnector": "support.connector.delete",
    "UpdateConnector": "support.connector.update",
    "ListFeatureProfiles": "support.feature-profile.list",
    "CreateFeatureProfile": "support.feature-profile.create",
    "DeleteFeatureProfile": "support.feature-profile.delete",
    "UpdateFeatureProfile": "support.feature-profile.update",
    "AddFeatureToProfile": "support.feature-profile.add-feature",
    "ListFeatures": "support.feature.list",
    "CreateFeature": "support.feature.create",
    "DeleteFeature": "support.feature.delete",
    "UpdateFeature": "support.feature.update",
    "ListSubscriptionPlans": "support.plan.list",
    "CreatePlan": "support.plan.create",
    "DeletePlan": "support.plan.delete",
    "GetPlan": "support.plan.get",
    "UpdatePlan": "support.plan.update",
    "ArchivePlan": "support.plan.archive",
    "UpdateStorageTiers": "support.plan.update-storage-tiers",
    "ListSelfServePlans": "support.plan.self-serve-list",
    # Dashboards.
    "ListDashboard": "dashboard.list",
    # GenerateDashboard (POST /dashboards) has no handler in current apiv2 and
    # always 404s; retired as server_unavailable directly in
    # spec/manifests/openapi-operations.yaml (no command, no SDK symbol). Not
    # mapped here so a future `build_manifests.py` run does not regenerate a
    # dead `dashboard.create` command or `DashboardsAPI.create` wrapper.
    "GetDashboardSources": "dashboard.source.list",
    "GetDashboardByUrl": "dashboard.get-by-url",
    "GetPublishDataFromSqlByUrl": "dashboard.published-data-by-url",
    "GetDashboardJob": "dashboard.job-by-url",
    "BulkWidgetDataByUrl": "dashboard.widget-data-by-url",
    "DeleteDashboard": "dashboard.delete",
    "GetDashboard": "dashboard.get",
    "EditDashboard": "dashboard.update",
    "DashboardAction": "dashboard.action",
    "GetDashboardAnalytics": "dashboard.analytics",
    "CancelDashboardGeneration": "dashboard.cancel-generation",
    "GetDraftDataFromSql": "dashboard.data.draft",
    "GetPublishDataFromSql": "dashboard.data.published",
    "RestoreDashboard": "dashboard.restore",
    "ShareDashboard": "dashboard.share",
    "TrashDashboard": "dashboard.trash",
    "BulkWidgetData": "dashboard.widget-data",
    "ListDashboardTags": "dashboard.tags.list",
    "RenameDashboardTag": "dashboard.tags.rename",
    "SetDashboardTags": "dashboard.tags.set",
    "DeleteDashboardTag": "dashboard.tags.delete",
    "MergeDashboardTags": "dashboard.tags.merge",
    # Data apps.
    "ListDataApps": "data-app.list",
    "CreateDataApp": "data-app.create",
    "DeleteDataAppEndpoint": "data-app.delete",
    "GetDataAppDetails": "data-app.get",
    "GetDataAppActiveJob": "data-app.active-job",
    "UploadToDataApp": "data-app.upload",
    "GetDataAppJob": "data-app.job",
    "GetPipelineChanges": "data-app.pipeline-changes",
    "UpdateDataApp": "data-app.update",
    "ShareDataApp": "data-app.share",
    "RemoveSharedUser": "data-app.user.remove",
    "ListSharedUsers": "data-app.user.list",
    # Projects.
    "GetProject": "project.list",
    "CreateProject": "project.create",
    "DeleteProjects": "project.bulk-delete",
    "UpdateProjects": "project.bulk-update",
    "DeleteProject": "project.delete",
    "UpdateProject": "project.update",
    "AddUserProject": "project.user.add",
    "RemoveUserProject": "project.user.remove",
    "UpdateUserProject": "project.user.update",
    "GetPendingChanges": "project.pending-changes",
    "GetResourceDependencies": "project.resource-dependencies",
    "GetResourceStatus": "project.resource-status",
    "CreateSampleFlow": "project.sample-flow",
    "GetProjectCheckpoints": "project.checkpoint.list",
    "GetProjectDataChecks": "project.data-check.list",
    "GetPublishCredentials": "project.publish-credentials",
    # AI connector chat.
    "Chat": "connector.ai.chat",
    "SubmitColumnSelection": "connector.ai.submit-column-selection",
    "SubmitCredentials": "connector.ai.submit-credentials",
    "GetChatHistory": "connector.ai.history",
    "ListSessions": "connector.ai.session.list",
    "GetSessionMessages": "connector.ai.session.messages",
    # Annotations.
    "ListAnnotations": "annotation.list",
    "CreateAnnotation": "annotation.create",
    "DeleteAnnotation": "annotation.delete",
    "PatchAnnotation": "annotation.update",
    "AddComment": "annotation.comment.add",
    # Automations + schedules.
    "GetList": "automation.list",
    "CreateAutomation": "automation.create",
    "DeleteAutomation": "automation.delete",
    "GetAutomation": "automation.get",
    "UpdateAutomation": "automation.update",
    "RestoreAutomation": "automation.restore",
    "TrashAutomation": "automation.trash",
    "ListSchedules": "schedule.list",
    "CreateSchedule": "schedule.create",
    "DeleteSchedule": "schedule.delete",
    "GetSchedule": "schedule.get",
    "PatchSchedule": "schedule.update",
    # Connections + ds-config + query-gen.
    "ListConnections": "connector.connection.list",
    "SaveConnection": "connector.connection.create",
    "DeleteConnection": "connector.connection.delete",
    "GetConnection": "connector.connection.get",
    "UpdateConnection": "connector.connection.update",
    "GetChatStatus": "connector.query.status",
    "GetQuerySuggestion": "connector.query.generate",
    "DeleteDsConfigs": "connector.ds-config.delete-all",
    "ListDsConfigs": "connector.ds-config.list",
    "ValidateAndGetDsConfig": "connector.ds-config.create",
    "DeleteDsConfig": "connector.ds-config.delete",
    "GetDsConfig": "connector.ds-config.get",
    "UpdateDsConfigs": "connector.ds-config.update",
    # Datasets.
    "GetDatasets": "dataset.list",
    "CreateDatasets": "dataset.create",
    "DeleteDatasets": "dataset.bulk-delete",
    "UpdateDatasets": "dataset.bulk-update",
    "CreateDatasetFromPdf": "dataset.create-from-pdf",
    "DeleteDataset": "dataset.delete",
    "GetDataset": "dataset.get",
    "UpdateDataset": "dataset.update",
    "GetDatasetData": "dataset.data",
    "RestoreDataset": "dataset.restore",
    "TrashDataset": "dataset.trash",
    "GetFileSettings": "dataset.file-settings.get",
    "UpdateFileSettings": "dataset.file-settings.update",
    "UndoFileSettings": "dataset.file-settings.undo",
    # Batches.
    "GetBatches": "batch.list",
    "CreateBatch": "batch.create",
    "DeleteBatches": "batch.bulk-delete",
    "UpdateBatches": "batch.update",
    "DeleteBatch": "batch.delete",
    "GetBatch": "batch.get",
    # Dataviews / views.
    "ListDataviews": "view.list",
    "AddDataview": "view.create",
    "DeleteMultipleDataviews": "view.bulk-delete",
    "DeleteDataview": "view.delete",
    "GetDataviewInformationIndividual": "view.get",
    "Patch": "view.update",
    "GetActiveUsers": "view.active-user.list",
    "MarkActiveUser": "view.active-user.mark",
    "GetConditionalFormat": "view.conditional-format.list",
    "CreateConditionalFormat": "view.conditional-format.create",
    "UpdateConditionalFormat": "view.conditional-format.update",
    "DeleteConditionalFormat": "view.conditional-format.delete-all",
    "GetDataviewData": "view.data.get",
    "GetDataviewDataPost": "view.data.query",
    "ExecuteVolatileQuery": "view.data.aggregate",
    "GetValidationInfo": "view.ai.generation-info",
    "Preview": "view.ai.generate-data",
    "GenerateProfile": "view.ai.profile",
    "ListDerivatives": "view.derivative.list",
    "CreateDerivative": "view.derivative.create",
    "DeleteDerivative": "view.derivative.delete",
    "EditDerivative": "view.derivative.update",
    "FetchDerivativeData": "view.derivative.data",
    "ExecutePipelineDraftCommand": "view.draft.command",
    "GetParameterContext": "view.parameter-context",
    "GetDataviewPreview": "view.preview",
    "RestoreDataview": "view.restore",
    "TrashDataview": "view.trash",
    "UpdatePublishToDb": "view.export.publish-db-update",
    "CreatePublishToDb": "view.export.publish-db",
    # Pipeline.
    "GetPipeline": "view.pipeline.get",
    "EditPipeline": "view.pipeline.edit",
    "GetPipelineItems": "view.pipeline.items",
    "RerunFromSequence": "view.pipeline.rerun",
    "GetPipelineTasks": "view.task.list",
    "AddTask": "view.task.add",
    "DeleteTask": "view.task.delete",
    "GetPipelineTask": "view.task.get",
    "EditTask": "view.task.update",
    "GetTaskPreview": "view.task.preview",
    "GetPipelineCheckpoints": "view.checkpoint.list",
    "AddCheckpoint": "view.checkpoint.create",
    "DeleteCheckpoint": "view.checkpoint.delete",
    "GetPipelineCheckpoint": "view.checkpoint.get",
    "EditPatches": "view.checkpoint.update",
    "GetPipelineDataChecks": "view.data-check.list",
    "AddDataCheck": "view.data-check.create",
    "DeleteDataCheck": "view.data-check.delete",
    "GetPipelineDataCheck": "view.data-check.get",
    "EditDatacheck": "view.data-check.update",
    "GetPipelineExports": "view.export.list",
    "AddExport": "view.export.create",
    "DeleteExport": "view.export.delete",
    "GetPipelineExport": "view.export.get",
    "EditExport": "view.export.update",
    "GetPipelineVersions": "view.version.list",
    "DeletePipelineVersion": "view.version.delete",
    "GetPipelineVersion": "view.version.get",
    "EditPipelineVersion": "view.version.update",
    "ApplyPipelineVersion": "view.version.apply",
    # SQL generation (AI).
    "GenerateSql": "ai.sql.generate",
    "GenerateCondition": "ai.condition.generate",
    "GenerateExpression": "ai.expression.generate",
    "AiSuggestions": "ai.suggestion.list",
    # Files.
    "ListFiles": "file.list",
    "CreateFileDataset": "file.upload",
    "DeleteFiles": "file.bulk-delete",
    "DeleteFile": "file.delete",
    "GetFileDetails": "file.get",
    "UpdateFileConfigs": "file.update",
    # Folders.
    "ListFolders": "folder.list",
    "CreateFolder": "folder.create",
    "DeleteFolders": "folder.bulk-delete",
    "UpdateFolderResources": "folder.move",
    "DeleteFolder": "folder.delete",
    "GetFolder": "folder.get",
    "UpdateFolderDetails": "folder.update",
    "TrashFolder": "folder.trash",
    # Trash.
    "ListTrash": "trash.list",
    "BulkTrash": "trash.add",
    "BulkRestore": "trash.restore",
    # Webhooks.
    "ListWebhooks": "webhook.list",
    "CreateAWebhook": "webhook.create",
    "DeleteWebhook": "webhook.delete",
    "GetWebhookDetails": "webhook.get",
    "UpdateWebhookConfigurations": "webhook.update",
    "AddDataToWebhook": "webhook.send",
    "AddDataToWebhookUsingGetMethod": "webhook.send-get",
    # Workflows + blocks + templates.
    "ListWorkflows": "workflow.list",
    "CreateWorkflow": "workflow.create",
    "CleanupGhostWorkflows": "workflow.cleanup",
    "InstantiateFromTemplate": "workflow.from-template",
    "GetProjectWorkflowGraph": "workflow.graph",
    "ListWorkspaceDatasets": "workflow.workspace-datasets",
    "ListWorkspaceExports": "workflow.workspace-exports",
    "ListWorkspaceSources": "workflow.workspace-sources",
    "DeleteWorkflow": "workflow.delete",
    "GetWorkflow": "workflow.get",
    "UpdateWorkflow": "workflow.update",
    "AddSkeletonBlock": "workflow.block.add",
    "PatchBlockAuth": "workflow.block.auth",
    "PromoteSkeletonBlock": "workflow.block.config",
    "PatchBlockType": "workflow.block.type",
    "UpdateCanvasState": "workflow.canvas",
    "ListTemplates": "template.list",
    "CreateTemplate": "template.create",
    "DeleteTemplate": "template.delete",
    "GetTemplate": "template.get",
    "UpdateTemplate": "template.update",
    # Parameters + groups.
    "ListParameters": "parameter.list",
    "CreateParameter": "parameter.create",
    "ListGroups": "parameter.group.list",
    "CreateGroup": "parameter.group.create",
    "ReorderGroups": "parameter.group.reorder",
    "DeleteGroup": "parameter.group.delete",
    "UpdateGroup": "parameter.group.update",
    "RerunAllStale": "parameter.rerun-all-stale",
    "DeleteParameter": "parameter.delete",
    "GetParameterDetail": "parameter.get",
    "UpdateParameter": "parameter.update",
    "GetParameterDependencies": "parameter.dependencies",
    "DuplicateParameter": "parameter.duplicate",
    "RerunParameter": "parameter.rerun",
    # Snippets.
    "ListSnippets": "snippet.list",
    "CreateSnippet": "snippet.create",
    "DeleteSnippet": "snippet.delete",
    "GetSnippetDetail": "snippet.get",
    "UpdateSnippet": "snippet.update",
    "GetSnippetDependencies": "snippet.dependencies",
    "DuplicateSnippet": "snippet.duplicate",
    "RerunSnippet": "snippet.rerun",
    # Dashboard v3 authoring, publishing, QA, style, and RLS APIs.
    "DeleteContext": "dashboard.context.delete",
    "DeleteSignature": "dashboard.signature.delete",
    "DeleteCustomStyle": "dashboard.style.custom.delete",
    "DashboardV3DeleteTemplate": "dashboard.template.delete",
    "DashboardV3DeleteSession": "dashboard.qa.session.delete",
    "DeleteComment": "dashboard.qa.comment.delete",
    "GetCanvasPublished": "dashboard.published.canvas",
    "OgCardByUrl": "dashboard.published.og-card",
    "GetPdfArtifactByUrl": "dashboard.published.pdf-artifact",
    "SharePageByUrl": "dashboard.published.share-page",
    "VideoByUrl": "dashboard.published.video-artifact",
    "ListContexts": "dashboard.context.list",
    "ListSignatures": "dashboard.signature.list",
    "ListCustomStyles": "dashboard.style.custom.list",
    "GetDefaultStyle": "dashboard.style.default.get",
    "ListStylePresets": "dashboard.style.preset.list",
    "GetStyleTokens": "dashboard.style.token.list",
    "DashboardSuggestions": "dashboard.suggestion.list",
    "DashboardV3ListTemplates": "dashboard.template.list",
    "FitTemplates": "dashboard.template.fit",
    "DashboardV3GetTemplate": "dashboard.template.get",
    "GetCanvasDraft": "dashboard.canvas.get",
    "DashboardV3ChatHistory": "dashboard.chat.history",
    "OgCard": "dashboard.og-card",
    "GetPdfArtifact": "dashboard.pdf-artifact",
    "DashboardV3ListSessions": "dashboard.qa.session.list",
    "GetSession": "dashboard.qa.session.get",
    "DashboardV3GetQaSettings": "dashboard.qa.settings.get",
    "ListRlsAssignments": "dashboard.rls.assignment.list",
    "GetRlsColumns": "dashboard.rls.column.list",
    "GetRlsDistinctValues": "dashboard.rls.value.list",
    "GetVideoState": "dashboard.video-state",
    "RenameTemplate": "dashboard.template.rename",
    "DescriptorDataByUrl": "dashboard.published.data",
    "ExportPdfByUrl": "dashboard.published.pdf.export",
    "ExportVideoByUrl": "dashboard.published.video.export",
    "CreateContext": "dashboard.context.create",
    "GenerateDashboardV3": "dashboard.v3.generate",
    "CreateSignature": "dashboard.signature.create",
    "CreateCustomStyle": "dashboard.style.custom.create",
    "DeriveStyle": "dashboard.style.derive",
    "ExtractBrand": "dashboard.style.extract-brand",
    "SaveTemplate": "dashboard.template.create",
    "ApplyTemplate": "dashboard.template.apply",
    "PreviewTemplate": "dashboard.template.preview",
    "ResolveTemplateMapping": "dashboard.template.resolve-mapping",
    "DuplicateDashboard": "dashboard.duplicate",
    "RestoreCanvas": "dashboard.canvas.restore",
    "ChatEdit": "dashboard.chat.edit",
    "DescriptorData": "dashboard.descriptor-data",
    "FigureIntent": "dashboard.figure-intent",
    "ExportPdf": "dashboard.pdf.export",
    "PlanPage": "dashboard.page.plan",
    "CreateSession": "dashboard.qa.session.create",
    "Ask": "dashboard.qa.ask",
    "DashboardV3AddComment": "dashboard.qa.comment.create",
    "ForkSession": "dashboard.qa.session.fork",
    "DashboardV3QaFeedback": "dashboard.qa.feedback",
    "AdhocQuery": "dashboard.query",
    "ExportVideo": "dashboard.video.export",
    "UpdateContext": "dashboard.context.update",
    "UpdateSignature": "dashboard.signature.update",
    "UpdateCustomStyle": "dashboard.style.custom.update",
    "SetDefaultStyle": "dashboard.style.default.set",
    "SaveCanvas": "dashboard.canvas.save",
    "RenameSession": "dashboard.qa.session.rename",
    "DashboardV3SetVisibility": "dashboard.qa.session.set-visibility",
    "DashboardV3SetQaSettings": "dashboard.qa.settings.set",
    "SetRlsAssignments": "dashboard.rls.assignment.set",
    # Bound 2026-10-09 from the prod snapshot: the route is called by this SDK method,
    # and the command calls that method (SDK call sites read, not inferred from names).
    "AcceptOwnData": "dashboard.own-data.accept",
    "AddDashboards": "collection.dashboards.add",
    "AddPages": "dashboard.pages.add",
    "AppendFigure": "dashboard.figure.add",
    "ApplyContextReview": "dashboard.context.apply",
    "ApplyExportableConfig": "view.exportable-config.apply",
    "ArchiveDashboard": "dashboard.archive",
    "ArchiveStorageOption": "support.plan.storage-option.archive",
    "AssessPbix": "dashboard.assess-pbix",
    "AssessTwb": "dashboard.assess-twb",
    "AttachmentAssess": "dashboard.pbix-assess",
    "AttachmentIntent": "dashboard.pbix-intent",
    "CreateAttachment": "dashboard.attachment-create",
    "AudienceSummary": "dashboard.audience.summary",
    "BulkGetResources": "browse.resources.bulk",
    "BulkModify": "project.resource-dependencies.update",
    "CancelAgentTurn": "agent.turn.cancel",
    "CollectionActivity": "collection.activity",
    "ActiveJob": "collection.active-job",
    "GetRefreshJob": "collection.job",
    "CollectionsForDashboard": "collection.for-dashboard",
    "CompareDataviews": "view.compare",
    "CopyProject": "project.copy",
    "CreateBlankDashboard": "dashboard.create-blank",
    "CreateCollection": "collection.create",
    "CreateStorageOption": "support.plan.storage-option.create",
    "DashboardPublicTemplate": "dashboard.gallery.get",
    "DashboardPublicTemplates": "dashboard.gallery.list",
    "DashboardV3AdminAudit": "support.template.audit",
    "DashboardV3AdminCatalog": "support.template.list",
    "DashboardV3AdminDataPreview": "support.template.data-preview",
    "DashboardV3AdminDeleteThumbnail": "support.template.thumbnail.clear",
    "DashboardV3AdminDiscardImport": "support.template.discard",
    "DashboardV3AdminEditRow": "support.template.edit",
    "DashboardV3AdminExportBundle": "support.template.export",
    "DashboardV3AdminExportDashboard": "support.template.export-dashboard",
    "DashboardV3AdminImportBundle": "support.template.import",
    "DashboardV3AdminInspectBundle": "support.template.inspect",
    "DashboardV3AdminPublish": "support.template.publish",
    "DashboardV3AdminPutThumbnail": "support.template.thumbnail.set",
    "DashboardV3AdminRetire": "support.template.retire",
    "DashboardV3AdminRowCanvas": "support.template.canvas",
    "DashboardV3AdminSnapshots": "support.template.snapshots",
    "DashboardV3AdminUnpublish": "support.template.unpublish",
    "DashboardV3DeleteTemplateThumbnail": "dashboard.template.thumbnail.clear",
    "DashboardV3PutTemplateThumbnail": "dashboard.template.thumbnail.set",
    "DashboardV3QaInsights": "dashboard.qa.insights",
    "DashboardV3TakePendingTemplate": "dashboard.templates.pending",
    "DashboardV3TemplateThumbnail": "dashboard.template.thumbnail.get",
    "DeleteAgentSessionAction": "agent.action.delete",
    "DeleteCollection": "collection.delete",
    "DismissOwnData": "dashboard.own-data.dismiss",
    "EmbedUsageSummary": "dashboard.embed.usage.summary",
    "ExtendAgentRun": "agent.run.extend",
    "ExtractContext": "dashboard.context.extract",
    "ExtractExemplar": "dashboard.exemplar.extract",
    "FormatPreview": "dashboard.format-preview",
    "GetAgentSessionRun": "agent.run.status",
    "GetAnalysis": "view.analyze",
    "GetAudienceDigest": "dashboard.audience.digest.get",
    "GetBatchData": "dataset.batch-data",
    "GetCollection": "collection.get",
    "GetCollectionByUrl": "collection.get-by-url",
    "GetColumnRoster": "dashboard.columns",
    "GetDashboardAudience": "dashboard.audience.get",
    "GetDashboardEngagement": "dashboard.engagement.get",
    "GetDashboardEngagementPerson": "dashboard.engagement.person",
    "GetDataviewDeleteImpact": "view.impact",
    "GetEmbedConfig": "dashboard.embed.config.get",
    "GetEmbedUsage": "dashboard.embed.usage.get",
    "GetExportableConfig": "view.exportable-config.get",
    "GetHomeSummary": "workspace.home",
    "GetOwnData": "dashboard.own-data.status",
    "GetResource": "browse.resource",
    "GetResourceAncestors": "browse.ancestors",
    "GetUnstructuredRows": "dataset.broken-rows.list",
    "ImportWorkbookDataset": "dashboard.import-workbook",
    "ListAgentSessionActions": "agent.action.list",
    "ListAgentSessionRuns": "agent.run.list",
    "ListCollections": "collection.list",
    "ListResources": "browse.resources",
    "ListStorageOptions": "support.plan.storage-option.list",
    "OptimizePipeline": "view.optimize",
    "PatchUnstructuredRows": "dataset.broken-rows.resolve",
    "PauseAgentRun": "agent.run.pause",
    "PipelineChanges": "collection.pipeline-changes",
    "PostDashboardEngagementRemind": "dashboard.engagement.remind",
    "PowerbiPreflight": "dashboard.bi-preflight",
    "PreviewOwnData": "dashboard.own-data.preview",
    "PreviewToken": "dashboard.embed.preview-token.create",
    "PutEmbedConfig": "dashboard.embed.config.set",
    "RecheckWorkspaceLimits": "billing.stripe.recheck-limits",
    "RegisterAgentRunUnits": "agent.run.units.set",
    "RemoveDashboard": "collection.dashboards.remove",
    "RemoveMember": "collection.members.remove",
    "ResumeAgentRun": "agent.run.resume",
    "ResumeWorkspaceSubscription": "billing.stripe.resume",
    "RetentionCondition": "ai.retention.condition",
    "ReviewContext": "dashboard.context.review",
    "RevokeOrigin": "dashboard.embed.origin.revoke",
    "RotateEmbedKey": "dashboard.embed.key.rotate",
    "RotateEmbedSecret": "dashboard.embed.secret.rotate",
    "SearchResources": "browse.search",
    "SetAudienceDigest": "dashboard.audience.digest.set",
    "SetEmbedLifetime": "dashboard.embed.lifetime.set",
    "ShareCollection": "collection.share",
    "StartOwnData": "dashboard.own-data.start",
    "StopAgentRun": "agent.run.stop",
    "SwapDashboardData": "dashboard.swap-data",
    "SwapFit": "dashboard.swap-fit",
    "UnarchivePlan": "support.plan.unarchive",
    "UpdateCollection": "collection.update",
    "UpdateStorageOption": "support.plan.storage-option.update",
    "UpdateSubscriptionStorage": "billing.stripe.storage.set",
    "UploadFile": "collection.files.upload",
    "UseTemplate": "dashboard.templates.use",
}


def command_for(operation_id: str) -> str | None:
    """Return the reviewed command id for an operationId, or None if not command."""
    if operation_id in PROTOCOL_ONLY or operation_id in OP_ALIAS:
        return None
    return OVERRIDES.get(operation_id)


def disposition_for(operation_id: str) -> tuple[str, str | None, str | None, str]:
    """Return (disposition, canonical_command, alias_of, reason)."""
    if operation_id in PROTOCOL_ONLY:
        return "protocol_only", None, None, PROTOCOL_ONLY[operation_id]
    if operation_id in OP_ALIAS:
        reason = ALIAS_REASON.get(operation_id, "Identical behavior to the aliased command.")
        return "alias", None, OP_ALIAS[operation_id], reason
    if operation_id in INTERNAL_ONLY:
        return "internal_only", None, None, INTERNAL_ONLY[operation_id]
    if operation_id in SERVER_UNAVAILABLE:
        return "server_unavailable", None, None, SERVER_UNAVAILABLE[operation_id]
    command = OVERRIDES.get(operation_id)
    if command:
        return "command", command, None, "User-initiated production operation."
    return "unmapped", None, None, "No reviewed CLI command or SDK symbol recorded."


_WORD = re.compile(r"[^a-z0-9]+")

# Planned SDK API location per command prefix (longest match wins). Phase 2 adds
# these public typed SDK methods; until then they resolve as "unknown", which is
# the intended red-first state.
_PLANNED_PREFIX: list[tuple[str, str, str]] = [
    ("view.derivative", "derivatives", "DerivativesAPI"),
    ("view.checkpoint", "checkpoints", "CheckpointsAPI"),
    ("view.version", "pipeline_versions", "PipelineVersionsAPI"),
    ("view.data-check", "data_checks", "DataChecksAPI"),
    ("view.export", "exports", "ExportsAPI"),
    ("view.conditional-format", "conditional_formats", "ConditionalFormatsAPI"),
    ("view.task", "pipeline", "PipelineAPI"),
    ("view.pipeline", "pipeline", "PipelineAPI"),
    ("view.draft", "pipeline", "PipelineAPI"),
    ("view.ai", "ai", "AIAPI"),
    ("view.data", "dataviews", "DataviewsAPI"),
    ("view.active-user", "dataviews", "DataviewsAPI"),
    ("view", "dataviews", "DataviewsAPI"),
    ("connector.ai", "connector_ai", "ConnectorAIAPI"),
    ("connector.query", "ai", "AIAPI"),
    ("connector", "connectors", "ConnectorsAPI"),
    ("project", "projects", "ProjectsAPI"),
    ("folder", "folders", "FoldersAPI"),
    ("dataset", "datasets", "DatasetsAPI"),
    ("file", "files", "FilesAPI"),
    ("batch", "batches", "BatchesAPI"),
    ("workspace", "workspaces", "WorkspacesAPI"),
    ("user", "users", "UsersAPI"),
    ("billing", "billing", "BillingAPI"),
    ("support", "support", "SupportAPI"),
    ("schedule", "automations", "AutomationsAPI"),
    ("automation", "automations", "AutomationsAPI"),
    ("webhook", "webhooks", "WebhooksAPI"),
    ("agent", "agents", "AgentsAPI"),
    ("report", "reports", "ReportsAPI"),
    ("addon", "addons", "AddonsAPI"),
    ("external-key", "external_keys", "ExternalKeysAPI"),
    ("client-app", "clientapps", "ClientAppsAPI"),
    ("activity", "activity_logs", "ActivityLogsAPI"),
    ("annotation", "annotations", "AnnotationsAPI"),
    ("notification", "notifications", "NotificationsAPI"),
    ("parameter", "parameters", "ParametersAPI"),
    ("snippet", "snippets", "SnippetsAPI"),
    ("data-app", "data_apps", "DataAppsAPI"),
    ("dashboard", "dashboards", "DashboardsAPI"),
    ("collection", "collections", "CollectionsAPI"),
    ("template", "templates", "TemplatesAPI"),
    ("workflow", "workflows", "WorkflowsAPI"),
    ("trash", "trash", "TrashAPI"),
    ("browse", "browse", "BrowseAPI"),
    ("ai", "ai", "AIAPI"),
    ("job", "jobs", "JobsAPI"),
]


def planned_symbol(command_id: str) -> str:
    """Return the planned public SDK symbol for a not-yet-implemented command."""
    for prefix, module, cls in _PLANNED_PREFIX:
        if command_id == prefix or command_id.startswith(prefix + "."):
            rest = command_id[len(prefix) :].lstrip(".")
            method = rest.replace(".", "_").replace("-", "_") or "run"
            return f"mammoth.api.{module}.{cls}.{method}"
    method = command_id.split(".", 1)[-1].replace(".", "_").replace("-", "_")
    return f"mammoth.api._planned.PlannedAPI.{method}"


def all_operation_ids_covered(operation_ids: list[str]) -> list[str]:
    """Return operationIds with no reviewed disposition."""
    missing = []
    for oid in operation_ids:
        disp, cmd, alias, reason = disposition_for(oid)
        if disp == "unmapped":
            missing.append(oid)
    return missing
