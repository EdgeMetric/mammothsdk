"""
Data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from .automations import (
    AutomationInfo,
    ScheduleInfo,
)
from .clientapps import (
    ClientAppCreate,
    ClientAppPostResponse,
    ClientAppSchema,
    ClientAppsListResponse,
    ValueWrapper,
)
from .connectors import (
    ConnectionInfo,
    ConnectorInfo,
    DsConfigInfo,
)
from .dashboards import (
    DashboardAnalytics,
    DashboardInfo,
    DashboardSource,
)
from .datasets import (
    DatasetCreateSpec,
    DatasetDataResponse,
    DatasetPatchData,
    DatasetPatchRequest,
    DatasetProperties,
    DatasetSchema,
    DatasetsList,
)
from .dataviews import (
    ActiveUser,
    ActiveUsersList,
    DataviewColumn,
    DataviewCreateRequest,
    DataviewDataRequest,
    DataviewDataResponse,
    DataviewPatchData,
    DataviewPatchRequest,
    DataviewProperties,
    DataviewSchema,
    DataviewsList,
)
from .exports import (
    AddExportSpec,
    ExportStatus,
    HandlerType,
    ItemExportInfo,
    PipelineExportsModificationResp,
    PipelineExportsPaginated,
    S3TargetProperties,
    TriggerType,
)
from .files import (
    AdditionalInfo,
    ExtractSheetsPatch,
    FileDetails,
    FilePatchData,
    FilePatchOperation,
    FilePatchPath,
    FilePatchRequest,
    FileSchema,
    FilesList,
    SheetInfo,
    StatusInfo,
)
from .folders import (
    BulkFolderPatchRequest,
    CreateFolder,
    FolderDetails,
    FolderSchema,
    FoldersList,
)
from .jobs import (
    JobResponse,
    JobSchema,
    JobsGetResponse,
    JobStatus,
    ObjectJobSchema,
)
from .pipeline import (
    AggregateFunction,
    ColumnType,
    DateComponent,
    DateDiffUnit,
    FillDirection,
    FilterType,
    JoinType,
    JsonType,
    MathOperator,
    Operator,
    PipelineInfo,
    PipelineTaskInfo,
    PipelineTasksList,
    ProviderType,
    SetValue,
    SmallLargeFunction,
    SortDirection,
    SubstringDirection,
    TaskType,
    TextCase,
    ValueType,
    WindowFunction,
    WindowRange,
)
from .projects import (
    AddUsersToProject,
    PatchOperation,
    ProjectCreate,
    ProjectList,
    ProjectPatch,
    ProjectProperties,
    ProjectSchema,
    ProjectsPatch,
    ProjectUserPatch,
)
from .webhooks import (
    WebhookCreate,
    WebhookInfo,
    WebhookMode,
)
from .workspaces import (
    WorkspaceSchema,
    WorkspacesSchema,
)

__all__ = [
    # Files models
    "FileSchema",
    "FileDetails",
    "FilesList",
    "AdditionalInfo",
    "StatusInfo",
    "SheetInfo",
    "FilePatchRequest",
    "FilePatchData",
    "ExtractSheetsPatch",
    "FilePatchOperation",
    "FilePatchPath",
    # Jobs models
    "JobSchema",
    "JobResponse",
    "JobsGetResponse",
    "ObjectJobSchema",
    "JobStatus",
    # Exports models
    "HandlerType",
    "TriggerType",
    "ExportStatus",
    "S3TargetProperties",
    "AddExportSpec",
    "ItemExportInfo",
    "PipelineExportsPaginated",
    "PipelineExportsModificationResp",
    # Datasets models
    "DatasetSchema",
    "DatasetsList",
    "DatasetProperties",
    "DatasetCreateSpec",
    "DatasetPatchData",
    "DatasetPatchRequest",
    "DatasetDataResponse",
    # Dataviews models
    "DataviewSchema",
    "DataviewsList",
    "DataviewColumn",
    "DataviewProperties",
    "DataviewCreateRequest",
    "DataviewPatchData",
    "DataviewPatchRequest",
    "DataviewDataRequest",
    "DataviewDataResponse",
    "ActiveUser",
    "ActiveUsersList",
    # Workspaces models
    "WorkspaceSchema",
    "WorkspacesSchema",
    # Projects models
    "ProjectSchema",
    "ProjectList",
    "ProjectProperties",
    "ProjectCreate",
    "PatchOperation",
    "ProjectPatch",
    "AddUsersToProject",
    "ProjectUserPatch",
    "ProjectsPatch",
    # Client Apps models
    "ValueWrapper",
    "ClientAppSchema",
    "ClientAppsListResponse",
    "ClientAppCreate",
    "ClientAppPostResponse",
    # Folders models
    "FolderSchema",
    "FoldersList",
    "CreateFolder",
    "FolderDetails",
    "BulkFolderPatchRequest",
    # Pipeline models
    "Operator",
    "ColumnType",
    "ValueType",
    "JoinType",
    "TextCase",
    "DateComponent",
    "DateDiffUnit",
    "WindowFunction",
    "WindowRange",
    "FillDirection",
    "AggregateFunction",
    "SmallLargeFunction",
    "ProviderType",
    "FilterType",
    "SortDirection",
    "MathOperator",
    "SubstringDirection",
    "JsonType",
    "TaskType",
    "SetValue",
    "PipelineTaskInfo",
    "PipelineTasksList",
    "PipelineInfo",
    # Connectors models
    "ConnectorInfo",
    "ConnectionInfo",
    "DsConfigInfo",
    # Dashboards models
    "DashboardInfo",
    "DashboardSource",
    "DashboardAnalytics",
    # Webhooks models
    "WebhookInfo",
    "WebhookCreate",
    "WebhookMode",
    # Automations models
    "AutomationInfo",
    "ScheduleInfo",
]
