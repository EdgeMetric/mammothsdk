"""Mammoth Analytics Python SDK.

A Python client for the Mammoth Analytics platform API. Provides
resource-based CRUD, rich View objects with 25+ transformation methods,
a condition builder with operator overloading, and export helpers.

Quick start::

    from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

    client = MammothClient(api_token="mm_...")
    client.set_project_id(10)

    # Resource-based CRUD
    projects = await client.projects.list()
    datasets = await client.datasets.list()

    # Rich View objects with transformations
    view = await client.views.get(1039)
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.set_values(
        new_column="Category",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ],
    )
    await view.export.to_csv("output.csv")

Key modules:
    - ``mammoth.client``: MammothClient — main entry point.
    - ``mammoth.view``: View, ViewExport — data transformations and exports.
    - ``mammoth.condition``: Condition, CompoundCondition — filter builder.
    - ``mammoth.models.pipeline``: Enums (Operator, ColumnType, JoinType, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mammoth.api.automations import SchedulePatchItem
    from mammoth.client import (
        DEFAULT_JOB_POLL_SECONDS,
        DEFAULT_JOB_TIMEOUT,
        DEFAULT_PIPELINE_TIMEOUT,
        DEFAULT_TIMEOUT,
        MammothClient,
    )
    from mammoth.condition import CompoundCondition, Condition, NotCondition
    from mammoth.exceptions import (
        MammothAPIError,
        MammothAuthError,
        MammothColumnError,
        MammothError,
        MammothExportError,
        MammothJobFailedError,
        MammothJobTimeoutError,
        MammothPipelineTimeoutError,
        MammothTransformError,
        MammothValidationError,
    )
    from mammoth.helpers import parse_path
    from mammoth.models.automations import (
        AlertType,
        AutomationConditionMode,
        AutomationConditionSpec,
        AutomationConditionType,
        AutomationPatchItem,
        AutomationPatchOp,
        AutomationPatchPath,
        AutomationStatus,
        AutomationTaskSpec,
        AutomationTaskType,
        ConditionDetailsSpec,
        DataRefreshConfig,
        FirstPullAt,
        OnRefreshAction,
        PatchAutomationDetails,
        PullDataExecutionParams,
        RruleFrequency,
        RruleSpec,
        ScheduleCreateSpec,
        SchedulePatchPath,
        SchedulePatchValue,
        ScheduleStatus,
        ScheduleType,
        TaskDetailsSpec,
        WorkItemName,
        WorkItemSpec,
    )
    from mammoth.models.connectors import DsConfigPatchOp, DsConfigPatchPath
    from mammoth.models.dashboards import (
        DashboardActionType,
        DashboardAuthType,
        DashboardPatchItem,
        DashboardPatchOp,
        DashboardPatchPath,
        DashboardShareRole,
        DashboardShareUser,
    )
    from mammoth.models.exports import (
        BigQueryExportType,
        HandlerType,
        HttpMethod,
        OdbcType,
        RestAuthType,
        TriggerType,
    )
    from mammoth.models.external_keys import ExternalKeyType, ModelConfigSpec
    from mammoth.models.pipeline import (
        AggregateFunction,
        AggregationSpec,
        BulkReplaceMapping,
        ColumnType,
        ConversionSpec,
        CopySpec,
        CrosstabSpec,
        DateComponent,
        DateDelta,
        DateDiffUnit,
        DateFunction,
        DraftCommand,
        ExportFileType,
        FillDirection,
        FilterType,
        JoinKeySpec,
        JoinSelectSpec,
        JoinType,
        JsonExtractionSpec,
        JsonOpType,
        JsonType,
        MathOperator,
        Operator,
        ProviderType,
        SaveAsDatasetMode,
        SetValue,
        SmallLargeFunction,
        SortDirection,
        SplitColumnSpec,
        SubstringDirection,
        TaskType,
        TextCase,
        ValueType,
        WindowFunction,
        WindowRange,
    )
    from mammoth.models.webhooks import WebhookMode
    from mammoth.models.workspaces import (
        BillingCycle,
        UserRolePatchOp,
        WorkspacePatchOp,
        WorkspacePatchPath,
        WorkspaceRoleType,
    )
    from mammoth.view import View, ViewExport

_LAZY: dict[str, tuple[str, str]] = {
    "SchedulePatchItem": ("mammoth.api.automations", "SchedulePatchItem"),
    "DEFAULT_JOB_POLL_SECONDS": ("mammoth.client", "DEFAULT_JOB_POLL_SECONDS"),
    "DEFAULT_JOB_TIMEOUT": ("mammoth.client", "DEFAULT_JOB_TIMEOUT"),
    "DEFAULT_PIPELINE_TIMEOUT": ("mammoth.client", "DEFAULT_PIPELINE_TIMEOUT"),
    "DEFAULT_TIMEOUT": ("mammoth.client", "DEFAULT_TIMEOUT"),
    "MammothClient": ("mammoth.client", "MammothClient"),
    "CompoundCondition": ("mammoth.condition", "CompoundCondition"),
    "Condition": ("mammoth.condition", "Condition"),
    "NotCondition": ("mammoth.condition", "NotCondition"),
    "MammothAPIError": ("mammoth.exceptions", "MammothAPIError"),
    "MammothAuthError": ("mammoth.exceptions", "MammothAuthError"),
    "MammothColumnError": ("mammoth.exceptions", "MammothColumnError"),
    "MammothError": ("mammoth.exceptions", "MammothError"),
    "MammothExportError": ("mammoth.exceptions", "MammothExportError"),
    "MammothJobFailedError": ("mammoth.exceptions", "MammothJobFailedError"),
    "MammothJobTimeoutError": ("mammoth.exceptions", "MammothJobTimeoutError"),
    "MammothPipelineTimeoutError": ("mammoth.exceptions", "MammothPipelineTimeoutError"),
    "MammothTransformError": ("mammoth.exceptions", "MammothTransformError"),
    "MammothValidationError": ("mammoth.exceptions", "MammothValidationError"),
    "parse_path": ("mammoth.helpers", "parse_path"),
    "AlertType": ("mammoth.models.automations", "AlertType"),
    "AutomationConditionMode": ("mammoth.models.automations", "AutomationConditionMode"),
    "AutomationConditionSpec": ("mammoth.models.automations", "AutomationConditionSpec"),
    "AutomationConditionType": ("mammoth.models.automations", "AutomationConditionType"),
    "AutomationPatchItem": ("mammoth.models.automations", "AutomationPatchItem"),
    "AutomationPatchOp": ("mammoth.models.automations", "AutomationPatchOp"),
    "AutomationPatchPath": ("mammoth.models.automations", "AutomationPatchPath"),
    "AutomationStatus": ("mammoth.models.automations", "AutomationStatus"),
    "AutomationTaskSpec": ("mammoth.models.automations", "AutomationTaskSpec"),
    "AutomationTaskType": ("mammoth.models.automations", "AutomationTaskType"),
    "ConditionDetailsSpec": ("mammoth.models.automations", "ConditionDetailsSpec"),
    "DataRefreshConfig": ("mammoth.models.automations", "DataRefreshConfig"),
    "FirstPullAt": ("mammoth.models.automations", "FirstPullAt"),
    "OnRefreshAction": ("mammoth.models.automations", "OnRefreshAction"),
    "PatchAutomationDetails": ("mammoth.models.automations", "PatchAutomationDetails"),
    "PullDataExecutionParams": ("mammoth.models.automations", "PullDataExecutionParams"),
    "RruleFrequency": ("mammoth.models.automations", "RruleFrequency"),
    "RruleSpec": ("mammoth.models.automations", "RruleSpec"),
    "ScheduleCreateSpec": ("mammoth.models.automations", "ScheduleCreateSpec"),
    "SchedulePatchPath": ("mammoth.models.automations", "SchedulePatchPath"),
    "SchedulePatchValue": ("mammoth.models.automations", "SchedulePatchValue"),
    "ScheduleStatus": ("mammoth.models.automations", "ScheduleStatus"),
    "ScheduleType": ("mammoth.models.automations", "ScheduleType"),
    "TaskDetailsSpec": ("mammoth.models.automations", "TaskDetailsSpec"),
    "WorkItemName": ("mammoth.models.automations", "WorkItemName"),
    "WorkItemSpec": ("mammoth.models.automations", "WorkItemSpec"),
    "DsConfigPatchOp": ("mammoth.models.connectors", "DsConfigPatchOp"),
    "DsConfigPatchPath": ("mammoth.models.connectors", "DsConfigPatchPath"),
    "DashboardActionType": ("mammoth.models.dashboards", "DashboardActionType"),
    "DashboardAuthType": ("mammoth.models.dashboards", "DashboardAuthType"),
    "DashboardPatchItem": ("mammoth.models.dashboards", "DashboardPatchItem"),
    "DashboardPatchOp": ("mammoth.models.dashboards", "DashboardPatchOp"),
    "DashboardPatchPath": ("mammoth.models.dashboards", "DashboardPatchPath"),
    "DashboardShareRole": ("mammoth.models.dashboards", "DashboardShareRole"),
    "DashboardShareUser": ("mammoth.models.dashboards", "DashboardShareUser"),
    "BigQueryExportType": ("mammoth.models.exports", "BigQueryExportType"),
    "HandlerType": ("mammoth.models.exports", "HandlerType"),
    "HttpMethod": ("mammoth.models.exports", "HttpMethod"),
    "OdbcType": ("mammoth.models.exports", "OdbcType"),
    "RestAuthType": ("mammoth.models.exports", "RestAuthType"),
    "TriggerType": ("mammoth.models.exports", "TriggerType"),
    "ExternalKeyType": ("mammoth.models.external_keys", "ExternalKeyType"),
    "ModelConfigSpec": ("mammoth.models.external_keys", "ModelConfigSpec"),
    "AggregateFunction": ("mammoth.models.pipeline", "AggregateFunction"),
    "AggregationSpec": ("mammoth.models.pipeline", "AggregationSpec"),
    "BulkReplaceMapping": ("mammoth.models.pipeline", "BulkReplaceMapping"),
    "ColumnType": ("mammoth.models.pipeline", "ColumnType"),
    "ConversionSpec": ("mammoth.models.pipeline", "ConversionSpec"),
    "CopySpec": ("mammoth.models.pipeline", "CopySpec"),
    "CrosstabSpec": ("mammoth.models.pipeline", "CrosstabSpec"),
    "DateComponent": ("mammoth.models.pipeline", "DateComponent"),
    "DateDelta": ("mammoth.models.pipeline", "DateDelta"),
    "DateDiffUnit": ("mammoth.models.pipeline", "DateDiffUnit"),
    "DateFunction": ("mammoth.models.pipeline", "DateFunction"),
    "DraftCommand": ("mammoth.models.pipeline", "DraftCommand"),
    "ExportFileType": ("mammoth.models.pipeline", "ExportFileType"),
    "FillDirection": ("mammoth.models.pipeline", "FillDirection"),
    "FilterType": ("mammoth.models.pipeline", "FilterType"),
    "JoinKeySpec": ("mammoth.models.pipeline", "JoinKeySpec"),
    "JoinSelectSpec": ("mammoth.models.pipeline", "JoinSelectSpec"),
    "JoinType": ("mammoth.models.pipeline", "JoinType"),
    "JsonExtractionSpec": ("mammoth.models.pipeline", "JsonExtractionSpec"),
    "JsonOpType": ("mammoth.models.pipeline", "JsonOpType"),
    "JsonType": ("mammoth.models.pipeline", "JsonType"),
    "MathOperator": ("mammoth.models.pipeline", "MathOperator"),
    "Operator": ("mammoth.models.pipeline", "Operator"),
    "ProviderType": ("mammoth.models.pipeline", "ProviderType"),
    "SaveAsDatasetMode": ("mammoth.models.pipeline", "SaveAsDatasetMode"),
    "SetValue": ("mammoth.models.pipeline", "SetValue"),
    "SmallLargeFunction": ("mammoth.models.pipeline", "SmallLargeFunction"),
    "SortDirection": ("mammoth.models.pipeline", "SortDirection"),
    "SplitColumnSpec": ("mammoth.models.pipeline", "SplitColumnSpec"),
    "SubstringDirection": ("mammoth.models.pipeline", "SubstringDirection"),
    "TaskType": ("mammoth.models.pipeline", "TaskType"),
    "TextCase": ("mammoth.models.pipeline", "TextCase"),
    "ValueType": ("mammoth.models.pipeline", "ValueType"),
    "WindowFunction": ("mammoth.models.pipeline", "WindowFunction"),
    "WindowRange": ("mammoth.models.pipeline", "WindowRange"),
    "WebhookMode": ("mammoth.models.webhooks", "WebhookMode"),
    "BillingCycle": ("mammoth.models.workspaces", "BillingCycle"),
    "UserRolePatchOp": ("mammoth.models.workspaces", "UserRolePatchOp"),
    "WorkspacePatchOp": ("mammoth.models.workspaces", "WorkspacePatchOp"),
    "WorkspacePatchPath": ("mammoth.models.workspaces", "WorkspacePatchPath"),
    "WorkspaceRoleType": ("mammoth.models.workspaces", "WorkspaceRoleType"),
    "View": ("mammoth.view", "View"),
    "ViewExport": ("mammoth.view", "ViewExport"),
}


def __getattr__(name: str) -> Any:
    """Import a re-exported name from its module on first access (PEP 562)."""
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    value = getattr(import_module(target[0]), target[1])
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *_LAZY})


__version__ = "0.8.38"
__all__ = [
    # Client
    "MammothClient",
    "DEFAULT_TIMEOUT",
    "DEFAULT_JOB_POLL_SECONDS",
    "DEFAULT_JOB_TIMEOUT",
    "DEFAULT_PIPELINE_TIMEOUT",
    # Condition builder
    "Condition",
    "CompoundCondition",
    "NotCondition",
    # View
    "View",
    "ViewExport",
    # Enums
    "Operator",
    "ColumnType",
    "JoinType",
    "TextCase",
    "DateComponent",
    "DateDiffUnit",
    "DateFunction",
    "WindowFunction",
    "WindowRange",
    "FillDirection",
    "AggregateFunction",
    "FilterType",
    "SortDirection",
    "SubstringDirection",
    "JsonType",
    "JsonOpType",
    "ExportFileType",
    "MathOperator",
    "ProviderType",
    "SaveAsDatasetMode",
    "SmallLargeFunction",
    "TaskType",
    "DraftCommand",
    "ValueType",
    # Parameter spec dataclasses
    "SetValue",
    "CopySpec",
    "ConversionSpec",
    "AggregationSpec",
    "JoinKeySpec",
    "JoinSelectSpec",
    "JsonExtractionSpec",
    "CrosstabSpec",
    "SplitColumnSpec",
    "BulkReplaceMapping",
    "DateDelta",
    # Export enums
    "HandlerType",
    "TriggerType",
    "BigQueryExportType",
    "OdbcType",
    "RestAuthType",
    "HttpMethod",
    # Dashboard enums / models
    "DashboardActionType",
    "DashboardAuthType",
    "DashboardPatchItem",
    "DashboardPatchOp",
    "DashboardPatchPath",
    "DashboardShareRole",
    "DashboardShareUser",
    # Automation enums / models
    "AutomationTaskType",
    "AutomationConditionType",
    "AutomationConditionMode",
    "AutomationPatchOp",
    "AutomationPatchPath",
    "AutomationStatus",
    "AlertType",
    "AutomationTaskSpec",
    "TaskDetailsSpec",
    "DataRefreshConfig",
    "AutomationConditionSpec",
    "ConditionDetailsSpec",
    "AutomationPatchItem",
    "PatchAutomationDetails",
    # Schedule enums / models (shared by AutomationsAPI + SchedulesAPI)
    "RruleFrequency",
    "ScheduleStatus",
    "SchedulePatchPath",
    "WorkItemName",
    "ScheduleType",
    "FirstPullAt",
    "OnRefreshAction",
    "RruleSpec",
    "PullDataExecutionParams",
    "WorkItemSpec",
    "ScheduleCreateSpec",
    "SchedulePatchValue",
    "SchedulePatchItem",
    # Connector patch models
    "DsConfigPatchPath",
    "DsConfigPatchOp",
    # Workspace patch models
    "BillingCycle",
    "WorkspacePatchPath",
    "WorkspacePatchOp",
    "WorkspaceRoleType",
    "UserRolePatchOp",
    # External keys
    "ExternalKeyType",
    "ModelConfigSpec",
    # Exceptions
    "MammothError",
    "MammothAPIError",
    "MammothAuthError",
    "MammothTransformError",
    "MammothColumnError",
    "MammothJobTimeoutError",
    "MammothPipelineTimeoutError",
    "MammothJobFailedError",
    "MammothValidationError",
    "MammothExportError",
    # Webhooks
    "WebhookMode",
    # Helpers
    "parse_path",
]
