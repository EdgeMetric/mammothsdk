"""Dashboard data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import ConfigDict, Field, StrictInt, computed_field, model_validator

# ── Read/response models (existing, kept as-is) ──────────────────────────────
from ._base import MammothModel


class DashboardInfo(MammothModel):
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


class ContextExtractParams(MammothModel):
    """Release-only parameters for extracting a context file."""

    model_config = ConfigDict(extra="forbid")
    name: str
    size: StrictInt = 0
    type: str | None = None
    text: str | None = None


class ContextExtractSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ContextExtractParams


class ContextExtractResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    file: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    shape: dict[str, Any] | None = None
    figureHeavy: list[str] = Field(default_factory=list)  # noqa: N815 - release field name
    suggestions: dict[str, str] = Field(default_factory=dict)
    condensed: dict[str, bool] = Field(default_factory=dict)
    skipped: dict[str, Any] | None = None


class ExemplarExtractParams(MammothModel):
    """Release parameters for extracting an example report."""

    model_config = ConfigDict(extra="forbid")
    name: str
    size: StrictInt = 0
    type: str | None = None
    content: str | None = None
    text: str | None = None
    dataview_id: StrictInt | None = None
    table_item_id: StrictInt | None = None


class ExemplarExtractSpec(MammothModel):
    """Request envelope for extracting an example report."""

    model_config = ConfigDict(extra="forbid")
    params: ExemplarExtractParams


class ExemplarExtractResponse(MammothModel):
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


class SwapDataParams(MammothModel):
    """Parameters for re-pointing a dashboard at a dataset."""

    model_config = ConfigDict(extra="forbid")
    dataview_id: StrictInt = Field(ge=1)
    mapping: dict[str, Any] | None = None
    overrides: dict[str, str | None] | None = None


class SwapDataSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: SwapDataParams


class PendingTemplateResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    slug: str | None = None


class UseTemplateParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    project_id: StrictInt = Field(ge=1)
    request_token: str | None = Field(default=None, max_length=64)
    style_id: str = Field(default="", max_length=128)
    mode: Literal["light", "dark"] | None = None
    show_summary: bool | None = None
    show_filters: bool | None = None
    kpi_style: Literal["cards", "accent", "tinted", "strip"] | None = None
    insight_style: Literal["list", "tinted", "cards", "numbered", "banner"] | None = None


class UseTemplateSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: UseTemplateParams


class TwbAssessResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    assessment: dict[str, Any] | None = None
    brief: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)


class PbixAssessResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    assessment: dict[str, Any] | None = None
    brief: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    model_available: bool = False


class ImportDatasetResponse(MammothModel):
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


class DashboardBiRefusal(MammothModel):
    """One figure the BI export/preflight route could not carry over."""

    model_config = ConfigDict(extra="allow")
    title: str
    reason: str


class DashboardBiPreflightResponse(MammothModel):
    """What a Power BI or Tableau export of a dashboard would carry (release route)."""

    model_config = ConfigDict(extra="allow")
    exportable: bool
    blocked_reason: str | None = None
    # Only ``exportable`` is required; the rest carry the backend's defaults.
    figures_total: int = 0
    figures_exported: int = 0
    figures_refused: int = 0
    degraded: bool = False
    refusals: list[DashboardBiRefusal] = Field(default_factory=list)
    row_count: int = 0
    column_count: int = 0


# Same body as the Tableau pre-flight, deliberately: the backend answers both
# with one response class (dashboards_v3/schema.py: ``TableauPreflightResponse
# = PowerBiPreflightResponse``), since the dialog asks one question -- "what
# will I actually get" -- with the same shape for either recipient tool.
PowerBiPreflightResponse = DashboardBiPreflightResponse

# Alias, not a subclass -- see the note by ``PowerBiPreflightResponse``.
TableauPreflightResponse = DashboardBiPreflightResponse


class DashboardSource(MammothModel):
    """Dashboard data source information."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    type: str | None = None


class DashboardAnalytics(MammothModel):
    """Dashboard analytics information."""

    model_config = ConfigDict(extra="allow")

    views: int | None = None
    unique_users: int | None = None
    last_viewed: str | None = None


class CreateBlankParams(MammothModel):
    """Parameters for a blank v3 dashboard seeded from a dataview."""

    model_config = ConfigDict(extra="forbid")

    dataview_id: int
    style: str = "dashboard"
    title: str = ""


class GenerateV3Params(MammothModel):
    """What the generate route builds a v3 dashboard from.

    The generated wrapper's own params model is pinned to an OpenAPI snapshot
    older than the route, and carries none of this: it has no title, no "qa"
    format, and an intent it will not let go empty.
    """

    model_config = ConfigDict(extra="forbid")

    dataview_id: int = Field(ge=1)
    # Empty only for "qa", where the reader asks the questions and the author
    # writes no brief at all.
    intent: str = ""
    format: Literal["dashboard", "presentation", "document", "qa"] | None = None
    contexts: list[str] | None = None
    client_turn_id: str | None = None
    title: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def _a_brief_unless_it_is_a_notebook(self) -> GenerateV3Params:
        if self.format != "qa" and not self.intent.strip():
            raise ValueError("intent must not be empty unless format is 'qa'")
        return self


class GenerateV3Spec(MammothModel):
    """Request envelope for generating a v3 dashboard."""

    model_config = ConfigDict(extra="forbid")

    params: GenerateV3Params


class CreateBlankSpec(MammothModel):
    """Request envelope for creating a blank v3 dashboard."""

    model_config = ConfigDict(extra="forbid")

    params: CreateBlankParams


class CreateBlankResponse(MammothModel):
    """Identifier and seeded sequence returned by blank dashboard creation."""

    id: int
    sequence: int


class TagRenameParams(MammothModel):
    """Release request body for renaming a workspace dashboard tag."""

    model_config = ConfigDict(extra="forbid")

    name: str


class DashboardTagsParams(MammothModel):
    """Release request body for replacing a dashboard's complete tag set."""

    model_config = ConfigDict(extra="forbid")

    # The route takes an absent list as "carry no tags", so this does too.
    tags: list[str] = Field(default_factory=list)


class TagMergeParams(MammothModel):
    """Release request body for merging one workspace tag into another."""

    model_config = ConfigDict(extra="forbid")

    target_id: int


class AddPagesParams(MammothModel):
    """Structural page specs appended to a dashboard draft."""

    model_config = ConfigDict(extra="forbid")
    pages: list[dict[str, Any]] = Field(min_length=1)
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None


class AddPagesResponse(MammothModel):
    """Dashboard draft head and asynchronous bake job created by add-pages."""

    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    added_page_ids: list[str] | None = None
    message: str = ""


class AddPagesSpec(MammothModel):
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


class DashboardPatchItem(MammothModel):
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


class DashboardShareUser(MammothModel):
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
    RESTORE = "restore"
    SET_RLS_CONFIG = "set-rls-config"


# ── embed: config / key / usage / preview-token / workspace secret ──────────


class EmbedConfigParams(MammothModel):
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


class EmbedConfigResponse(MammothModel):
    """A board's embed settings plus the URLs a snippet needs."""

    model_config = ConfigDict(extra="allow")

    mode: str
    tier: str = "key"
    allow_any_origin: bool = True
    allowed_origins: list[str] = Field(default_factory=list)
    appearance: dict[str, Any] = Field(default_factory=dict)
    snippet: dict[str, Any] = Field(default_factory=dict, repr=False)
    embed_url: str
    sdk_url: str
    published: bool
    public: bool
    access_key: str | None = Field(default=None, repr=False)
    key_rotated_at: str | None = None
    has_signing_secret: bool = False
    signing_secret_rotated_at: str | None = None
    token_ttl: int = 300
    rls_enabled: bool = False
    rls_column: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mode_reason(self) -> str:
        """Why the board embeds the way it does, and which tier is settable.

        ``mode`` is the EFFECTIVE mode and reads ``public`` whenever the board's
        share link is public, whatever tier is saved; ``tier`` is what
        ``embed config set`` changes.
        """
        if self.public:
            return (
                "public because the board's share link is public: it embeds with no"
                f" key or token. Saved tier for when the link is removed: {self.tier}"
                " (embed config set mode=key|signed)."
            )
        return f"{self.tier}: the board's saved tier (embed config set mode=key|signed)."


class EmbedKeyResponse(MammothModel):
    """The board's new (or current) embed key."""

    model_config = ConfigDict(extra="allow")

    key: str = Field(repr=False)
    rotated_at: str | None = None


class EmbedOriginUsage(MammothModel):
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


class EmbedUsageResponse(MammothModel):
    """Where one board has been loaded from (the embed registry)."""

    model_config = ConfigDict(extra="allow")

    origins: list[EmbedOriginUsage] = Field(default_factory=list)
    active_origins: int = 0


class EmbedPreviewTokenResponse(MammothModel):
    """A short-lived token the embed simulator hands to the frame."""

    model_config = ConfigDict(extra="allow")

    token: str = Field(repr=False)
    expires_at: int
    embed_url: str


class EmbedSecretResponse(MammothModel):
    """A new workspace embed signing secret, returned once (create/rotate)."""

    model_config = ConfigDict(extra="allow")

    secret: str = Field(repr=False)
    token_ttl: int
    rotated_at: str | None = None


class EmbedLifetimeResponse(MammothModel):
    """The saved embed viewer session lifetime for a workspace."""

    model_config = ConfigDict(extra="allow")

    token_ttl: int
