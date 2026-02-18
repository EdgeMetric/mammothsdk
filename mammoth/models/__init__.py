"""
Data models for the Mammoth Analytics SDK.
"""

from .files import *
from .jobs import *
from .exports import *
from .datasets import *
from .dataviews import *
from .workspaces import *
from .projects import *
from .clientapps import *
from .folders import *
from .pipeline import *
from .connectors import *
from .dashboards import *
from .webhooks import *
from .automations import *

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
    # Pipeline models
    "Operator",
    "ColumnType",
    "ValueType",
    "JoinType",
    "TextCase",
    "DateComponent",
    "WindowFunction",
    "FillDirection",
    "AggregateFunction",
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
    # Automations models
    "AutomationInfo",
    "ScheduleInfo",
]
