"""Mammoth Analytics Python SDK.

A Python client for the Mammoth Analytics platform API. Provides
resource-based CRUD, rich View objects with 25+ transformation methods,
a condition builder with operator overloading, and export helpers.

Quick start::

    from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

    client = MammothClient(
        api_key="your-api-key",
        api_secret="your-api-secret",
        workspace_id=11,
    )
    client.set_project_id(10)

    # Resource-based CRUD
    projects = client.projects.list()
    datasets = client.datasets.list()

    # Rich View objects with transformations
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.set_values(
        new_column="Category",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ],
    )
    view.export.to_csv("output.csv")

Key modules:
    - ``mammoth.client``: MammothClient — main entry point.
    - ``mammoth.view``: View, ViewExport — data transformations and exports.
    - ``mammoth.condition``: Condition, CompoundCondition — filter builder.
    - ``mammoth.models.pipeline``: Enums (Operator, ColumnType, JoinType, etc.).
"""

from __future__ import annotations

from mammoth.api.automations import SchedulePatchItem
from mammoth.client import (
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

__version__ = "0.6.2"
__all__ = [
    # Client
    "MammothClient",
    "DEFAULT_TIMEOUT",
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
    "MammothJobFailedError",
    "MammothValidationError",
    "MammothExportError",
    # Webhooks
    "WebhookMode",
    # Helpers
    "parse_path",
]
