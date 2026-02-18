"""
API modules for the Mammoth Analytics SDK.
"""

from .files import FilesAPI
from .jobs import JobsAPI
from .exports import ExportsAPI
from .workspace import WorkspaceAPI
from .clientapps import ClientAppsAPI
from .projects import ProjectsAPI
from .folders import FoldersAPI
from .datasets import DatasetsAPI
from .dataviews import DataviewsAPI
from .pipeline import PipelineAPI
from .connectors import ConnectorsAPI
from .dashboards import DashboardsAPI
from .webhooks import WebhooksAPI
from .automations import AutomationsAPI
from .ai import AIAPI

__all__ = [
    "FilesAPI",
    "JobsAPI",
    "ExportsAPI",
    "WorkspaceAPI",
    "ClientAppsAPI",
    "ProjectsAPI",
    "FoldersAPI",
    "DatasetsAPI",
    "DataviewsAPI",
    "PipelineAPI",
    "ConnectorsAPI",
    "DashboardsAPI",
    "WebhooksAPI",
    "AutomationsAPI",
    "AIAPI",
]
