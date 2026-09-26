"""Dashboard data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

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


class ExemplarExtractParams(BaseModel):
    """Release parameters for extracting an example report."""

    model_config = ConfigDict(extra="forbid")
    name: str
    size: StrictInt = 0
    type: str | None = None
    content: str | None = None
    text: str | None = None
    dataview_id: StrictInt | None = None
    table_item_id: StrictInt | None = None


class ExemplarExtractSpec(BaseModel):
    """Request envelope for extracting an example report."""

    model_config = ConfigDict(extra="forbid")
    params: ExemplarExtractParams


class ExemplarExtractResponse(BaseModel):
    """Editable dashboard spec and extraction metadata."""

    model_config = ConfigDict(extra="allow")
    spec: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    palette: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    countable: list[str] = Field(default_factory=list)
    brand: dict[str, Any] = Field(default_factory=dict)
    scopes: list[dict[str, Any]] = Field(default_factory=list)


class SwapDataParams(BaseModel):
    """Parameters for re-pointing a dashboard at a dataset."""

    model_config = ConfigDict(extra="forbid")
    dataview_id: StrictInt = Field(ge=1)
    mapping: dict[str, Any] | None = None
    overrides: dict[str, str | None] | None = None


class SwapDataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: SwapDataParams


class PendingTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    slug: str | None = None


class UseTemplateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: StrictInt = Field(ge=1)
    request_token: str | None = Field(default=None, max_length=64)
    style_id: str = Field(default="", max_length=128)
    mode: Literal["light", "dark"] | None = None
    show_summary: bool | None = None
    show_filters: bool | None = None
    kpi_style: Literal["cards", "accent", "tinted", "strip"] | None = None
    insight_style: Literal["list", "tinted", "cards", "numbered", "banner"] | None = None


class UseTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: UseTemplateParams


class TwbAssessResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    assessment: dict[str, Any] | None = None
    brief: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)


class PbixAssessResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    assessment: dict[str, Any] | None = None
    brief: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    model_available: bool = False


class ImportDatasetResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    dataview_id: int | None = None
    dataset_name: str | None = None
    intent: str | None = None
    assessment: dict[str, Any] | None = None
    brief: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    data_source: str | None = None
    fields: list[dict[str, Any]] = Field(default_factory=list)


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


# ── embed: config / key / usage / preview-token / workspace secret ──────────


class EmbedConfigParams(BaseModel):
    """Embed settings for one board (mirrors ``EmbedConfigParams`` in apiv2).

    Attributes:
        mode: The tier a board WITHOUT a public link is on. ``key``: a page
            presents the board's embed key. ``signed``: every viewer needs a
            host-signed token.
        allow_any_origin: Any site may frame the board. Set false to restrict
            framing to ``allowed_origins``.
        allowed_origins: Sites allowed to frame the board while
            ``allow_any_origin`` is false. At most 20.
        appearance: The board's saved look, applied when the embed loads.
        snippet: How the embed snippet is shaped (``height`` etc.).
    """

    model_config = ConfigDict(extra="forbid")

    mode: Literal["key", "signed"] = "key"
    allow_any_origin: bool = True
    allowed_origins: list[str] = Field(default_factory=list, max_length=20)
    appearance: dict[str, Any] = Field(default_factory=dict)
    snippet: dict[str, Any] = Field(default_factory=dict)


class EmbedConfigResponse(BaseModel):
    """A board's embed settings plus the URLs a snippet needs."""

    model_config = ConfigDict(extra="allow")

    mode: str
    tier: str = "key"
    allow_any_origin: bool = True
    allowed_origins: list[str] = Field(default_factory=list)
    appearance: dict[str, Any] = Field(default_factory=dict)
    snippet: dict[str, Any] = Field(default_factory=dict)
    embed_url: str
    sdk_url: str
    published: bool
    public: bool
    access_key: str | None = None
    key_rotated_at: str | None = None
    has_signing_secret: bool = False
    signing_secret_rotated_at: str | None = None
    token_ttl: int = 300
    rls_enabled: bool = False
    rls_column: str | None = None


class EmbedKeyResponse(BaseModel):
    """The board's new (or current) embed key."""

    model_config = ConfigDict(extra="allow")

    key: str
    rotated_at: str | None = None


class EmbedOriginUsage(BaseModel):
    """One origin/tile row in a board's embed usage registry."""

    model_config = ConfigDict(extra="allow")

    origin: str
    tile: str
    tier: str
    first_seen_at: str
    last_seen_at: str
    renders_7d: int
    renders_30d: int
    refused_30d: int
    errors_30d: int
    active: bool
    health: str
    allowed: bool


class EmbedUsageResponse(BaseModel):
    """Where one board has been loaded from (the embed registry)."""

    model_config = ConfigDict(extra="allow")

    origins: list[EmbedOriginUsage] = Field(default_factory=list)
    active_origins: int = 0


class EmbedPreviewTokenResponse(BaseModel):
    """A short-lived token the embed simulator hands to the frame."""

    model_config = ConfigDict(extra="allow")

    token: str
    expires_at: int
    embed_url: str


class EmbedSecretResponse(BaseModel):
    """A new workspace embed signing secret, returned once (create/rotate)."""

    model_config = ConfigDict(extra="allow")

    secret: str
    token_ttl: int
    rotated_at: str | None = None


class EmbedLifetimeResponse(BaseModel):
    """The saved embed viewer session lifetime for a workspace."""

    model_config = ConfigDict(extra="allow")

    token_ttl: int
