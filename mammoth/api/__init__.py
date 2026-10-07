"""
API modules for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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

_LAZY: dict[str, tuple[str, str]] = {
    "ActivityLogsAPI": ("mammoth.api.activity_logs", "ActivityLogsAPI"),
    "AddonsAPI": ("mammoth.api.addons", "AddonsAPI"),
    "AIAPI": ("mammoth.api.ai", "AIAPI"),
    "AutomationsAPI": ("mammoth.api.automations", "AutomationsAPI"),
    "BatchesAPI": ("mammoth.api.batches", "BatchesAPI"),
    "BrowseAPI": ("mammoth.api.browse", "BrowseAPI"),
    "ClientAppsAPI": ("mammoth.api.clientapps", "ClientAppsAPI"),
    "ConnectorsAPI": ("mammoth.api.connectors", "ConnectorsAPI"),
    "DashboardsAPI": ("mammoth.api.dashboards", "DashboardsAPI"),
    "DatasetsAPI": ("mammoth.api.datasets", "DatasetsAPI"),
    "DataviewsAPI": ("mammoth.api.dataviews", "DataviewsAPI"),
    "ExportsAPI": ("mammoth.api.exports", "ExportsAPI"),
    "ExternalKeysAPI": ("mammoth.api.external_keys", "ExternalKeysAPI"),
    "FilesAPI": ("mammoth.api.files", "FilesAPI"),
    "FoldersAPI": ("mammoth.api.folders", "FoldersAPI"),
    "JobsAPI": ("mammoth.api.jobs", "JobsAPI"),
    "PipelineAPI": ("mammoth.api.pipeline", "PipelineAPI"),
    "ProjectsAPI": ("mammoth.api.projects", "ProjectsAPI"),
    "ReportsAPI": ("mammoth.api.reports", "ReportsAPI"),
    "SchedulesAPI": ("mammoth.api.schedules", "SchedulesAPI"),
    "UserProfileAPI": ("mammoth.api.user_profile", "UserProfileAPI"),
    "WebhooksAPI": ("mammoth.api.webhooks", "WebhooksAPI"),
    "WorkspaceAPI": ("mammoth.api.workspace", "WorkspaceAPI"),
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
