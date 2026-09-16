"""Dashboard data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt

# ── Read/response models (existing, kept as-is) ──────────────────────────────


class DashboardInfo(BaseModel):
    """Information about a dashboard."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    status: str | None = None
    url: str | None = None
    config: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    created_by: str | None = None


class ContextExtractParams(BaseModel):
    """Release-only parameters for extracting a context file."""

    model_config = ConfigDict(extra="forbid")
    name: str
    size: StrictInt = 0
    type: str | None = None
    text: str | None = None


class ContextExtractSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ContextExtractParams


class ContextExtractResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    file: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    shape: dict[str, Any] | None = None
    figureHeavy: list[str] = Field(default_factory=list)  # noqa: N815 - release field name
    suggestions: dict[str, str] = Field(default_factory=dict)
    condensed: dict[str, bool] = Field(default_factory=dict)
    skipped: dict[str, Any] | None = None


class DashboardSource(BaseModel):
    """Dashboard data source information."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    type: str | None = None


class DashboardAnalytics(BaseModel):
    """Dashboard analytics information."""

    model_config = ConfigDict(extra="allow")

    views: int | None = None
    unique_users: int | None = None
    last_viewed: str | None = None


class CreateBlankParams(BaseModel):
    """Parameters for a blank v3 dashboard seeded from a dataview."""

    model_config = ConfigDict(extra="forbid")

    dataview_id: int
    style: str = "dashboard"
    title: str = ""


class CreateBlankSpec(BaseModel):
    """Request envelope for creating a blank v3 dashboard."""

    model_config = ConfigDict(extra="forbid")

    params: CreateBlankParams


class CreateBlankResponse(BaseModel):
    """Identifier and seeded sequence returned by blank dashboard creation."""

    id: int
    sequence: int


class TagRenameParams(BaseModel):
    """Release request body for renaming a workspace dashboard tag."""

    model_config = ConfigDict(extra="forbid")

    name: str


class DashboardTagsParams(BaseModel):
    """Release request body for replacing a dashboard's complete tag set."""

    model_config = ConfigDict(extra="forbid")

    tags: list[str]


class TagMergeParams(BaseModel):
    """Release request body for merging one workspace tag into another."""

    model_config = ConfigDict(extra="forbid")

    target_id: int


class AddPagesParams(BaseModel):
    """Structural page specs appended to a dashboard draft."""

    model_config = ConfigDict(extra="forbid")
    pages: list[dict[str, Any]] = Field(min_length=1)
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None


class AddPagesResponse(BaseModel):
    """Dashboard draft head and asynchronous bake job created by add-pages."""

    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    added_page_ids: list[str] | None = None
    message: str = ""


class AddPagesSpec(BaseModel):
    """Request envelope for structurally adding dashboard pages."""

    model_config = ConfigDict(extra="forbid")
    params: AddPagesParams


# ── update: JSON-patch enums + model ─────────────────────────────────────────


class DashboardPatchOp(str, Enum):
    """Allowed JSON-patch operation values for dashboard update."""

    ADD = "add"
    REPLACE = "replace"


class DashboardPatchPath(str, Enum):
    """Allowed JSON-patch path values for dashboard update."""

    INTENT = "intent"
    TITLE = "title"
    THEME = "theme"
    PAGES = "pages"
    FILTERS = "filters"


class DashboardPatchItem(BaseModel):
    """A single JSON-patch operation for :meth:`DashboardsAPI.update`.

    Attributes:
        op: The patch operation (``add`` or ``replace``).
        path: The field to patch.
        value: The new value; a string for ``intent``/``title``/``theme``, or a
            dict such as ``{"enable": True}`` for ``pages``/``filters``.
    """

    op: DashboardPatchOp
    path: DashboardPatchPath
    value: str | dict[str, Any]


# ── share: auth-type enum + nested models ────────────────────────────────────


class DashboardAuthType(str, Enum):
    """Dashboard sharing authentication type."""

    MAMMOTH = "mammoth"
    PUBLIC = "public"
    PASSWORD = "password"


class DashboardShareRole(str, Enum):
    """Role for a shared dashboard user."""

    VIEWER = "dashboard_viewer"
    EDITOR = "dashboard_editor"


class DashboardShareUser(BaseModel):
    """A single user entry for mammoth-type dashboard sharing.

    Attributes:
        email: Recipient email address (non-empty).
        role: Permission level granted to the user.
        shared: Whether sharing is enabled for this user.
    """

    email: str
    role: DashboardShareRole = DashboardShareRole.VIEWER
    shared: bool = True


# ── action: enum ─────────────────────────────────────────────────────────────


class DashboardActionType(str, Enum):
    """Action to perform on a dashboard."""

    SYNC = "sync"
    PUBLISH_DATA = "publish-data"
    PUBLISH_PRESENTATION = "publish-presentation"
    UNPUBLISH = "unpublish"
    AUTO_SYNC = "auto-sync"
    AUTO_PUBLISH = "auto-publish"
    DELETE_SOURCE = "delete-source"
