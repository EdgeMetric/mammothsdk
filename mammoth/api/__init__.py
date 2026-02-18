"""
API modules for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from .activity_logs import ActivityLogsAPI
from .addons import AddonsAPI
from .ai import AIAPI
from .automations import AutomationsAPI
from .batches import BatchesAPI
from .browse import BrowseAPI
from .clientapps import ClientAppsAPI
from .connectors import ConnectorsAPI
from .dashboards import DashboardsAPI
from .datasets import DatasetsAPI
from .dataviews import DataviewsAPI
from .exports import ExportsAPI
from .external_keys import ExternalKeysAPI
from .files import FilesAPI
from .folders import FoldersAPI
from .jobs import JobsAPI
from .pipeline import PipelineAPI
from .projects import ProjectsAPI
from .reports import ReportsAPI
from .schedules import SchedulesAPI
from .user_profile import UserProfileAPI
from .webhooks import WebhooksAPI
from .workspace import WorkspaceAPI

__all__ = [
    "ActivityLogsAPI",
    "AddonsAPI",
    "AIAPI",
    "BatchesAPI",
    "BrowseAPI",
    "ClientAppsAPI",
    "ConnectorsAPI",
    "DashboardsAPI",
    "DatasetsAPI",
    "DataviewsAPI",
    "ExportsAPI",
    "ExternalKeysAPI",
    "FilesAPI",
    "FoldersAPI",
    "JobsAPI",
    "PipelineAPI",
    "ProjectsAPI",
    "ReportsAPI",
    "SchedulesAPI",
    "UserProfileAPI",
    "WebhooksAPI",
    "AutomationsAPI",
    "WorkspaceAPI",
]
