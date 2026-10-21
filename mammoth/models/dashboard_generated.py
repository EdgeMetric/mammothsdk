# ruff: noqa: N801, N815
"""Generated dashboard request and response models. Do not edit by hand."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import ConfigDict, Field, RootModel

from ._base import MammothModel


class AddPagesParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    pages: Annotated[list[dict[str, Any]], Field(min_length=1)]
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None


class AddPagesResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    added_page_ids: list[str] | None = None
    message: str | None = None


class AddPagesSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: AddPagesParams


class AdhocQueryParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    descriptor: dict[str, Any]


class AdhocQueryResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    job_id: int
    descriptor_id: str


class AdhocQuerySpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: AdhocQueryParams


class AppendFigureParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    dataview_id: int
    figure: dict[str, Any]
    banded: dict[str, Any] | None = None
    page: FigurePageTarget | None = None
    base_sequence: int | None = None
    on_duplicate: Literal["add", "refuse", "replace"] | None = None


class AppendFigureResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    page_id: str
    figure_id: str
    layout_key: str
    page_title: str | None = None


class AppendFigureSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: AppendFigureParams


class ApplyContextReviewParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    keep: list[str] | None = None
    base_sequence: int | None = None


class ApplyContextReviewSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ApplyContextReviewParams


class ApplyTemplateParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_id: Annotated[int, Field(ge=1.0)]
    mapping: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None


class ApplyTemplateSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ApplyTemplateParams


class AskParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, Field(min_length=1, max_length=2000)]
    ask_id: Annotated[str | None, Field(max_length=64)] = None
    filter_state: dict[str, Any] | None = None
    conversation_history: list[dict[str, Any]] | None = None


class AskSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: AskParams


class AttachmentIntentForm(MammothModel):
    model_config = ConfigDict(extra="forbid")
    target_dataview_id: int


class AttachmentJob(MammothModel):
    model_config = ConfigDict(extra="allow")
    future_id: int


class AttachmentResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    attachment_id: int
    filename: str
    kind: str


class AudienceAnonymous(MammothModel):
    model_config = ConfigDict(extra="allow")
    views: int
    public_views: int
    password_views: int


class AudienceCountries(MammothModel):
    model_config = ConfigDict(extra="allow")
    coverage: float
    items: list[AudienceCountry]


class AudienceCountry(MammothModel):
    model_config = ConfigDict(extra="allow")
    code: str
    views: int


class AudienceDailyPoint(MammothModel):
    model_config = ConfigDict(extra="allow")
    date: str
    views: int
    people: int


class AudienceDevices(MammothModel):
    model_config = ConfigDict(extra="allow")
    coverage: float
    desktop: int
    mobile: int
    tablet: int


class AudienceNeverOpened(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    invited_at: str | None = None


class AudiencePage(MammothModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    views: int
    avg_seconds: int | None = None


class AudiencePrevTotals(MammothModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    avg_seconds: int | None = None


class AudienceResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    range_days: int
    as_of: str
    published: bool
    published_at: str | None = None
    totals: AudienceTotals
    concurrent_now: int
    daily: list[AudienceDailyPoint]
    daily_prev: list[AudienceDailyPoint]
    viewers: list[AudienceViewer]
    viewers_total: int
    anonymous: AudienceAnonymous
    countries: AudienceCountries
    devices: AudienceDevices
    viewport: AudienceViewport
    never_opened: list[AudienceNeverOpened]
    pages: list[AudiencePage]
    tiles: list[AudienceTile]
    actions: dict[str, Any]
    last_viewed_at: str | None = None


class AudienceSummaryItem(MammothModel):
    model_config = ConfigDict(extra="allow")
    views_7d: int
    people_7d: int
    views_30d: int
    last_viewed_at: str | None = None
    daily_14: list[int]


class AudienceSummaryResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    items: dict[str, Any]


class AudienceTile(MammothModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    tile_id: str
    views: int


class AudienceTotals(MammothModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    named_people: int
    anonymous_views: int
    avg_seconds: int | None = None
    prev: AudiencePrevTotals


class AudienceViewer(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    last_viewed_at: str | None = None
    visits: int
    seconds: int


class AudienceViewport(MammothModel):
    model_config = ConfigDict(extra="allow")
    coverage: float
    buckets: dict[str, Any]


class BoardPreviewOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    dashboard_id: int
    title: str
    published: bool
    rls: bool
    figures: list[FigureOut]
    choices: list[FigureOut]


class BoardStatusModel(MammothModel):
    model_config = ConfigDict(extra="allow")
    state: Literal["active", "archived", "trashed"]
    by_name: str | None = None


class BulkWidgetDataParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    widgets: Annotated[list[WidgetDataParams], Field(min_length=1, max_length=100)]
    rls_preview_value: str | None = None


class BulkWidgetDataSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: BulkWidgetDataParams


class CanvasMeta(MammothModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    signature_token: str | None = None
    signature_locked: bool | None = None
    artifact_version: str | None = None
    filters: dict[str, Any] | None = None
    figures: dict[str, Any] | None = None
    stale_bake: bool | None = None
    bake_error: dict[str, Any] | str | None = None
    heal_notes: list[str] | None = None
    unbuilt_notes: list[str] | None = None
    fanout_notes: list[str] | None = None
    unweighted_means: list[str] | None = None
    broken_bindings: list[dict[str, Any]] | None = None
    receipts: dict[str, Any] | None = None
    context_drift: list[dict[str, Any]] | None = None
    published_context_drift: list[dict[str, Any]] | None = None
    context_baseline: bool | None = None
    currency: dict[str, Any] | None = None
    on_sample_data: bool | None = None
    sanctioned_demo_publish: bool | None = None
    rls_scoped: bool | None = None


class CanvasResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    canvas: dict[str, Any]
    plan: dict[str, Any] | None = None
    specs: dict[str, Any] | None = None
    meta: CanvasMeta
    dashboard_id: int | None = None


class ChangeAudienceParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    audience: Literal["workspace", "public", "sites"]
    allowed_origins: list[str] | None = None


class ChangeAudienceSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ChangeAudienceParams


class ChatEditParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    prompt: Annotated[str, Field(min_length=1)]
    scope: dict[str, Any] | None = None
    selected_fig: int | None = None
    active_page_id: str | None = None
    target_tile_id: str | None = None
    conversation_history: list[dict[str, Any]] | None = None
    client_turn_id: str | None = None
    change: list[dict[str, Any]] | dict[str, Any] | None = None


class ChatEditSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ChatEditParams


class ChatRevision(MammothModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    updated_at: str | None = None
    updated_by: int | None = None
    updated_by_name: str | None = None


class ColumnRoster(MammothModel):
    model_config = ConfigDict(extra="allow")
    row_count: int | None = None
    columns: list[RosterColumn] | None = None
    signals: RosterSignals | None = None
    on_board_count: int | None = None


class CommentParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    body: Annotated[str, Field(min_length=1, max_length=2000)]


class CommentSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: CommentParams


class ContextExtractParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    size: int | None = None
    type: str | None = None
    text: str | None = None
    content: str | None = None


class ContextExtractResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    file: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    shape: dict[str, Any] | None = None
    figureHeavy: list[str] | None = None
    suggestions: dict[str, Any] | None = None
    condensed: dict[str, Any] | None = None
    skipped: dict[str, Any] | None = None


class ContextExtractSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ContextExtractParams


class ContextListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    contexts: list[dict[str, Any]] | None = None


class ContextParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    type: str | None = None
    files: list[dict[str, Any]] | None = None
    background: str | None = None
    goals: str | None = None
    definitions: str | None = None
    emphasis: str | None = None
    guardrails: str | None = None


class ContextResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    context: dict[str, Any]


class ContextSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ContextParams | None = None


class CreateBlankParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    dataview_id: int
    style: str | None = None
    title: str | None = None


class CreateBlankResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: int
    sequence: int


class CreateBlankSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: CreateBlankParams


class CreateLiveChartParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    view_id: Annotated[int, Field(ge=1.0)]
    figure: dict[str, Any]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    audience: Literal["workspace", "public", "sites"] | None = None
    allowed_origins: list[str] | None = None
    origin: LiveChartOrigin | None = None


class CreateLiveChartResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    dashboard_id: int
    job_id: int | None = None


class CreateLiveChartSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: CreateLiveChartParams


class CreateSessionParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str | None, Field(max_length=200)] = None


class CreateSessionSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: CreateSessionParams | None = None


class CreatorDashboardHtmlType(MammothModel):
    model_config = ConfigDict(extra="allow")
    html: str
    sources: list[int]
    messages: list[dict[str, Any]]
    title: str
    share: DashboardAuthResponse | None = None
    url: str
    engine: str | None = None
    theme: str
    role: str
    id: int
    was_published: bool
    auto_sync: dict[str, Any]
    auto_publish: bool
    is_sync_pending: bool
    is_publish_pending: bool
    is_publish_presentation_pending: bool
    project_id: int | None = None
    workspace_id: int | None = None


class CustomStyleParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    signals: dict[str, Any] | None = None
    tokens: dict[str, Any] | None = None
    name: str | None = None
    blurb: str | None = None
    source: dict[str, Any] | None = None


class CustomStyleSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: CustomStyleParams | None = None


class DashboardAction(
    RootModel[
        Literal[
            "sync",
            "publish-data",
            "publish-presentation",
            "unpublish",
            "auto-sync",
            "auto-publish",
            "delete-source",
            "restore",
            "set-rls-config",
        ]
    ]
):
    model_config = ConfigDict(defer_build=True)


class DashboardActionParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool | None = None
    view_id: int | None = None
    sequence: int | None = None
    notify_authors: bool | None = None
    filter_column: str | None = None


class DashboardActionSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    action: DashboardAction
    params: DashboardActionParams | None = None


class DashboardAnalyticsResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    total_views: int
    average_time_spent_seconds: float | None = None
    viewed_by: str
    current_concurrent_viewers: int


class DashboardArchiveParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    archived: bool


class DashboardAuth(MammothModel):
    model_config = ConfigDict(extra="forbid")
    type_of_auth: Literal["mammoth", "public", "password"]
    options: dict[str, Any] | None = None
    sequence: int | None = None


class DashboardAuthResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    type_of_auth: Literal["mammoth", "public", "password"]
    options: dict[str, Any] | None = None
    sequence: int | None = None


class DashboardEditParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    op: mmai_dashboard_schema_OpValues
    path: mmai_dashboard_schema_PathValues
    value: str | dict[str, Any]


class DashboardEditSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    patch: list[DashboardEditParams]


class DashboardListSchema(MammothModel):
    model_config = ConfigDict(extra="allow")
    dashboards: list[DashboardModelType]


class DashboardModelType(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: int
    updated_at: str
    created_at: str
    status: DashboardStatus
    role: str
    sources: list[int]
    share: Any
    url: str
    updated_by: int
    title: str
    theme: str
    auto_sync: dict[str, Any]
    auto_publish: bool
    is_sync_pending: bool
    is_publish_pending: bool
    is_publish_presentation_pending: bool
    was_published: bool
    sequence: int | None = None
    sub_sequence: int | None = None
    engine: str | None = None
    project_id: int | None = None
    workspace_id: int | None = None
    format: str | None = None
    archived: bool | None = None
    tags: list[str] | None = None
    page_count: int | None = None
    shared_by_name: str | None = None
    collection_ids: list[int] | None = None


class DashboardPlaceResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    dashboard_id: int
    title: str
    figure_id: str


class DashboardShareParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    auth: DashboardAuth


class DashboardShareSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: DashboardShareParams


class DashboardSource(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str
    rows: int
    columns: int
    updated_at: str
    workspace_name: str


class DashboardSourcesType(MammothModel):
    model_config = ConfigDict(extra="allow")
    sources: list[DashboardSource]


class DashboardStatus(RootModel[Literal["draft", "published", "archived", "deleted", "error"]]):
    model_config = ConfigDict(defer_build=True)


class DashboardTagsParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    tags: list[str] | None = None


class DashboardViewConfigType(MammothModel):
    model_config = ConfigDict(extra="allow")
    auto_sync: bool
    is_sync_pending: bool
    last_synced_at: str | None = None


class DefaultStyleParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    styleId: Annotated[str, Field(min_length=1)]


class DefaultStyleResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    style_id: str


class DefaultStyleSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: DefaultStyleParams


class DeriveStyleParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    signals: dict[str, Any] | None = None


class DeriveStyleResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    style_tokens: dict[str, Any]


class DeriveStyleSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: DeriveStyleParams | None = None


class DescriptorDataParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    descriptor_ids: Annotated[list[str], Field(min_length=1, max_length=200)]
    filter_state: dict[str, Any] | None = None
    rls_preview_value: str | None = None


class DescriptorDataSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: DescriptorDataParams


class DigestPrefResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    enabled: bool
    explicit: bool | None = None
    default_on: bool | None = None


class DigestPrefSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool | None = None


class DraftHeadResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    head_sequence: int
    base_sequence: int | None = None
    count: int
    moves: list[DraftMove] | None = None


class DraftMove(MammothModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    user_id: int | None = None
    user_name: str | None = None
    at: str | None = None
    kind: Literal["edit", "assistant", "sync"]
    label: str | None = None


class DuplicateDashboardResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: int
    swap_job_id: int | None = None


class EmailUpdateOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: int
    enabled: bool
    trigger: Trigger
    frequency: Frequency
    weekday: int | None = None
    monthday: int | None = None
    time_of_day: str
    timezone: str
    numbers: dict[str, Any]
    next_run_at: str | None = None
    last_run_at: str | None = None
    last_status: str | None = None
    last_detail: str | None = None
    last_delivered: int | None = None
    left_out: dict[str, Any] | None = None


class EmailUpdateSettingsBody(MammothModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    trigger: Trigger | None = None
    timezone: Annotated[str, Field(min_length=1, max_length=64)]
    frequency: Frequency | None = None
    weekday: Annotated[int | None, Field(le=6)] = None
    monthday: Annotated[int | None, Field(ge=1, le=28)] = None
    time_of_day: str | None = None
    numbers: dict[str, Any] | None = None


class EmailUpdateSubscriptionBody(MammothModel):
    model_config = ConfigDict(extra="forbid")
    subscribed: bool


class EmailUpdateSubscriptionOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    available: bool
    subscribed: bool


class EmailUpdateSummaryList(MammothModel):
    model_config = ConfigDict(extra="allow")
    updates: list[EmailUpdateSummaryOut]


class EmailUpdateSummaryOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    collection_id: int | None = None
    dashboard_id: int | None = None
    enabled: bool
    trigger: Trigger
    frequency: Frequency
    last_run_at: str | None = None
    last_status: str | None = None
    last_detail: str | None = None
    last_delivered: int | None = None
    left_out: list[int] | None = None
    unsubscribed: list[str] | None = None


class EmailUpdateTestOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    sent: int


class EmailUpdatesOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    update: EmailUpdateOut | None = None
    people: int
    unsubscribed: list[str]
    boards: list[BoardPreviewOut]
    covered_by: list[str] | None = None


class EmbedPlaceResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    origin: str
    renders_30d: int
    last_seen_at: str | None = None


class EngagementActionDay(MammothModel):
    model_config = ConfigDict(extra="allow")
    pdf: int
    link_copy: int
    powerbi: int
    tableau: int
    video: int
    date: str


class EngagementActions(MammothModel):
    model_config = ConfigDict(extra="allow")
    pdf: int
    link_copy: int
    powerbi: int
    tableau: int
    video: int
    daily: list[EngagementActionDay]


class EngagementAnonymous(MammothModel):
    model_config = ConfigDict(extra="allow")
    views: int
    seconds: int


class EngagementDailyPoint(MammothModel):
    model_config = ConfigDict(extra="allow")
    date: str
    views: int
    people: int
    prev_views: int
    prev_people: int


class EngagementDevices(MammothModel):
    model_config = ConfigDict(extra="allow")
    desktop: int
    mobile: int
    tablet: int
    coverage: float


class EngagementEvent(MammothModel):
    model_config = ConfigDict(extra="allow")
    at: str
    kind: Literal["published", "edited", "refreshed", "shared"]
    count: int
    label: str


class EngagementPage(MammothModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    name: str
    reached: int
    views: int
    avg_s: int | None = None
    tiles: list[EngagementTile]


class EngagementPerson(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    email: str | None = None
    visits: int
    seconds: int
    pages_read: int
    last_seen: str | None = None
    status: Literal["engaged", "active", "drifting", "never"]
    daily: list[int]
    shared: bool
    reminded_at: str | None = None
    can_remind: bool


class EngagementPersonResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    visits: list[EngagementVisit]


class EngagementPrevTotals(MammothModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    avg_engaged_s: int | None = None
    questions: int


class EngagementReach(MammothModel):
    model_config = ConfigDict(extra="allow")
    shared: int
    opened: int
    returned: int
    engaged: int
    prev: EngagementReachCounts


class EngagementReachCounts(MammothModel):
    model_config = ConfigDict(extra="allow")
    shared: int
    opened: int
    returned: int
    engaged: int


class EngagementRemindResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    sent: list[int]
    skipped: list[EngagementRemindSkip]


class EngagementRemindSkip(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    reason: Literal["not_shared", "opened", "no_email", "recently_reminded", "send_failed"]
    next_at: str | None = None


class EngagementRemindSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    user_ids: Annotated[list[int], Field(min_length=1, max_length=200)]


class EngagementResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    range_days: int
    as_of: str
    published: bool
    published_at: str | None = None
    tz: str
    engaged_rule: EngagementRule
    reach: EngagementReach
    totals: EngagementTotals
    daily: list[EngagementDailyPoint]
    pages: list[EngagementPage]
    people: list[EngagementPerson]
    anonymous: EngagementAnonymous
    hours: list[list[int]]
    surface: EngagementSurface
    devices: EngagementDevices
    actions: EngagementActions
    events: list[EngagementEvent]


class EngagementRule(MammothModel):
    model_config = ConfigDict(extra="allow")
    seconds: int
    pages: int


class EngagementSurface(MammothModel):
    model_config = ConfigDict(extra="allow")
    app: int
    link: int
    embed: int


class EngagementTile(MammothModel):
    model_config = ConfigDict(extra="allow")
    tile_id: str
    title: str | None = None
    seen_pct: float


class EngagementTotals(MammothModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    anon_views: int
    avg_engaged_s: int | None = None
    questions: int
    unanswered: int
    prev: EngagementPrevTotals


class EngagementVisit(MammothModel):
    model_config = ConfigDict(extra="allow")
    started_at: str | None = None
    seconds: int | None = None
    pages: list[EngagementVisitPage]
    device: str | None = None
    surface: Literal["app", "link", "embed"]


class EngagementVisitPage(MammothModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    name: str
    seconds: int


class ExemplarExtractParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    size: int | None = None
    type: str | None = None
    content: str | None = None
    text: str | None = None
    dataview_id: int | None = None
    table_item_id: int | None = None


class ExemplarExtractResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    spec: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] | None = None
    palette: list[str] | None = None
    measures: list[str] | None = None
    countable: list[str] | None = None
    brand: dict[str, Any] | None = None
    scopes: list[dict[str, Any]] | None = None


class ExemplarExtractSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ExemplarExtractParams


class ExtractBrandParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    url: Annotated[str, Field(min_length=1)]


class ExtractBrandSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ExtractBrandParams


class FeedbackParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    rating: Literal["up", "down", None] | None = None


class FeedbackSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: FeedbackParams | None = None


class FigureIntentParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    kind: str | None = None
    fields: dict[str, Any] | None = None


class FigureIntentResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    kind: str
    added: dict[str, Any] | None = None
    spec: dict[str, Any] | None = None
    empty: bool | None = None
    caption: str | None = None
    caveat: str | None = None
    text: TextBlockSpec | None = None
    intent_applied: bool


class FigureIntentSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: FigureIntentParams | None = None


class FigureOut(MammothModel):
    model_config = ConfigDict(extra="allow")
    key: str
    label: str
    value: str | None = None


class FigurePageTarget(MammothModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    new_title: Annotated[str | None, Field(max_length=80)] = None


class FormatFloorApplied(MammothModel):
    model_config = ConfigDict(extra="allow")
    filters_added: int | None = None
    pages_added: list[str] | None = None
    cover_added: bool | None = None
    charts_composed: int | None = None


class FormatPreviewNotShown(MammothModel):
    model_config = ConfigDict(extra="allow")
    what: str
    count: int
    reason: str


class FormatPreviewResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    style: str
    charts_carried: int | None = None
    kpis_carried: int | None = None
    filters_carried: int | None = None
    pages_after: int | None = None
    filters_added: int | None = None
    pages_added: list[str] | None = None
    cover_added: bool | None = None
    qa_added: bool | None = None
    not_shown: list[FormatPreviewNotShown] | None = None


class Frequency(RootModel[Literal["daily", "weekdays", "weekly", "monthly"]]):
    model_config = ConfigDict(defer_build=True)


class GenerateDashboardV3Params(MammothModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    dataview_id: Annotated[int, Field(ge=1.0)]
    format: Literal["dashboard", "presentation", "document", "qa", None] | None = None
    contexts: list[str] | None = None
    client_turn_id: str | None = None
    title: Annotated[str | None, Field(max_length=200)] = None
    structure: Annotated[str | None, Field(max_length=40)] = None
    design_from: Annotated[int | None, Field(ge=1)] = None


class GenerateDashboardV3Spec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: GenerateDashboardV3Params


class ImportWorkbookForm(MammothModel):
    model_config = ConfigDict(extra="forbid")
    file: str
    project_id: int | None = None


class JobResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    job: JobSchema


class JobSchema(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: Annotated[int, Field(ge=0.0)]
    status: Literal["success", "failure", "processing", "error"]
    response: dict[str, Any] | list[Any]
    last_updated_at: str
    created_at: str
    path: str
    operation: str


class LiveChartBroken(MammothModel):
    model_config = ConfigDict(extra="allow")
    reasons: list[str]
    since: str


class LiveChartListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    items: list[LiveChartRef]


class LiveChartOrigin(MammothModel):
    model_config = ConfigDict(extra="forbid")
    session_id: Annotated[str, Field(min_length=1, max_length=64)]
    message_id: Annotated[str, Field(min_length=1, max_length=64)]
    chart_index: Annotated[int, Field(ge=0.0, le=99.0)]


class LiveChartRef(MammothModel):
    model_config = ConfigDict(extra="allow")
    dashboard_id: int
    message_id: str
    chart_index: int
    state: Literal["pending", "live", "failed", "broken"]
    audience: Literal["workspace", "public", "sites"]
    view_name: str | None = None


class LiveChartResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    dashboard_id: int
    title: str
    token: str
    state: Literal["pending", "live", "failed", "broken"]
    audience: Literal["workspace", "public", "sites"]
    allowed_origins: list[str]
    view_id: int
    view_name: str | None = None
    figure: dict[str, Any] | None = None
    data_updated_at: int | None = None
    broken: LiveChartBroken | None = None
    created_at: str
    embed_url: str
    share_url: str
    embed_snippet: str | None = None
    oembed: bool


class LiveChartUsageResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    embeds: list[EmbedPlaceResponse]
    dashboards: list[DashboardPlaceResponse]
    link_views_30d: int


class ObjectJobSchema(MammothModel):
    model_config = ConfigDict(extra="allow")
    status_code: int | None = None
    job_id: int | None = None
    failure_reason: str | None = None


class OkResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    ok: bool


class OwnDataAcceptParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    choice: Literal["proposal", "partial", "reshape"] | None = None
    exclude: Annotated[list[str] | None, Field(max_length=20)] = None


class OwnDataAcceptSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: OwnDataAcceptParams


class OwnDataStartParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    ingest_job_id: Annotated[int | None, Field(ge=1)] = None
    dataset_id: Annotated[int | None, Field(ge=1)] = None
    dataview_id: Annotated[int | None, Field(ge=1)] = None
    file_name: Annotated[str | None, Field(max_length=255)] = None


class OwnDataStartSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: OwnDataStartParams


class PdfExportParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any] | None = None
    paper: str | None = None
    carousel: bool | None = None
    compare: dict[str, Any] | None = None


class PdfExportSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: PdfExportParams


class PendingTemplateResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    slug: str | None = None


class PlanPageParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    archetype: str | None = None
    kind: str | None = None
    fields: dict[str, Any] | None = None
    page_id: str | None = None


class PlanPageResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    page: dict[str, Any]
    composed: bool
    message: str | None = None
    preview: list[dict[str, Any]] | None = None


class PlanPageSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: PlanPageParams | None = None


class PowerBiPreflightResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    exportable: bool
    blocked_reason: str | None = None
    figures_total: int | None = None
    figures_exported: int | None = None
    figures_refused: int | None = None
    degraded: bool | None = None
    refusals: list[PowerBiRefusal] | None = None
    row_count: int | None = None
    column_count: int | None = None


class PowerBiRefusal(MammothModel):
    model_config = ConfigDict(extra="allow")
    title: str
    reason: str


class PresenceParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    client_id: Annotated[str, Field(min_length=1, max_length=64)]
    page_id: Annotated[str | None, Field(max_length=128)] = None
    tile_id: Annotated[str | None, Field(max_length=128)] = None
    busy_tile_id: Annotated[str | None, Field(max_length=128)] = None
    idle: bool | None = None
    since: int | None = None
    leave: bool | None = None


class PresenceResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    others: list[PresentEditor] | None = None
    status: BoardStatusModel
    head: DraftHeadResponse | None = None


class PresenceSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: PresenceParams


class PresentEditor(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    user_name: str | None = None
    page_id: str | None = None
    tile_id: str | None = None
    busy_tile_id: str | None = None
    idle: bool | None = None


class PreviewTemplateParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_id: Annotated[int, Field(ge=1.0)]
    table_item_id: Annotated[int | None, Field(ge=1)] = None
    mapping: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None


class PreviewTemplateResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    canvas: dict[str, Any]
    plan: dict[str, Any] | None = None
    specs: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
    mapping: dict[str, Any]
    fidelity: dict[str, Any]
    target_fields: dict[str, Any] | None = None
    results: dict[str, Any] | None = None
    coverage: dict[str, Any] | None = None


class PreviewTemplateSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: PreviewTemplateParams


class PublicTemplateListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    templates: list[dict[str, Any]] | None = None
    total: int | None = None
    use_cases: list[dict[str, Any]] | None = None
    functions: list[dict[str, Any]] | None = None
    industries: list[dict[str, Any]] | None = None
    formats: list[dict[str, Any]] | None = None


class PublicTemplateResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    template: dict[str, Any]


class QaInsightsFeedback(MammothModel):
    model_config = ConfigDict(extra="allow")
    up: int
    down: int


class QaInsightsFields(MammothModel):
    model_config = ConfigDict(extra="allow")
    measure: str | None = None
    dimension: str | None = None


class QaInsightsGroup(MammothModel):
    model_config = ConfigDict(extra="allow")
    text: str
    count: int
    last_asked_at: str
    down: int
    up: int
    unanswered: int
    fields: QaInsightsFields | None = None


class QaInsightsResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    range_days: int
    questions_total: int
    feedback: QaInsightsFeedback
    groups: list[QaInsightsGroup]


class QaSettingsParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    allow_viewer_qa: bool


class QaSettingsResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    allow_viewer_qa: bool
    can_manage: bool | None = None
    public_link: bool | None = None


class QaSettingsSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: QaSettingsParams


class RecordPlacementParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    dashboard_id: Annotated[int, Field(ge=1.0)]
    figure_id: Annotated[str, Field(min_length=1, max_length=64)]


class RecordPlacementSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: RecordPlacementParams


class RenameSessionParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, Field(min_length=1, max_length=200)]


class RenameSessionSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: RenameSessionParams


class RenameTemplateParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, Field(min_length=1, max_length=80)]
    description: Annotated[str | None, Field(max_length=240)] = None


class RenameTemplateSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: RenameTemplateParams


class RenderFigureSvgResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    svg: str


class RenderFigureSvgSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    spec: dict[str, Any]
    style_id: str | None = None


class ResolveTemplateMappingParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_id: Annotated[int, Field(ge=1.0)]


class ResolveTemplateMappingResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    mapping: dict[str, Any]
    fidelity: dict[str, Any]
    target_fields: dict[str, Any] | None = None


class ResolveTemplateMappingSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ResolveTemplateMappingParams


class RestoreCanvasParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    target_sequence: Annotated[int, Field(ge=1.0)]
    base_sequence: int | None = None
    history_index: int | None = None
    activity: dict[str, Any] | None = None


class RestoreCanvasSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: RestoreCanvasParams


class ReviewContextParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    scope: str | None = None
    note: Annotated[str | None, Field(max_length=1000)] = None
    fresh: bool | None = None


class ReviewContextSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: ReviewContextParams | None = None


class RlsAssignmentEntry(MammothModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    all_access: bool | None = None
    values: list[str] | None = None


class RlsAssignmentView(MammothModel):
    model_config = ConfigDict(extra="allow")
    email: str
    all_access: bool
    values: list[str]
    value_missing: bool


class RlsAssignmentsParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    assignments: list[RlsAssignmentEntry] | None = None


class RlsAssignmentsResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    enabled: bool
    filter_column: str | None = None
    assignments: list[RlsAssignmentView]


class RlsAssignmentsSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: RlsAssignmentsParams


class RlsColumnsResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    columns: list[str]


class RlsDistinctValuesResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    column: str
    total: int
    values: list[Any]


class RosterColumn(MammothModel):
    model_config = ConfigDict(extra="allow")
    name: str
    label: str
    type: str
    cardinality: int | None = None
    non_empty: int | None = None
    min: float | None = None
    max: float | None = None
    null_rate: float | None = None
    distinct_count: int | None = None
    semantic: str | None = None
    agg: str | None = None
    per_unit: bool | None = None
    currency: str | None = None
    currency_assumed: bool | None = None
    samples: list[str] | None = None
    top_share: float | None = None
    has_empty: bool | None = None
    identifier: bool | None = None
    sensitive: bool | None = None
    min_date: str | None = None
    max_date: str | None = None
    span_months: int | None = None
    as_of_like: bool | None = None
    on_board: bool | None = None


class RosterCorrelation(MammothModel):
    model_config = ConfigDict(extra="allow")
    a: str
    b: str
    r: float


class RosterGeoDim(MammothModel):
    model_config = ConfigDict(extra="allow")
    field: str
    scope: str


class RosterHierarchy(MammothModel):
    model_config = ConfigDict(extra="allow")
    outer: str
    inner: str


class RosterSignals(MammothModel):
    model_config = ConfigDict(extra="allow")
    correlations: list[RosterCorrelation] | None = None
    hierarchy: RosterHierarchy | None = None
    ledger_field: str | None = None
    geo_dims: list[RosterGeoDim] | None = None


class SaveCanvasParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    canvas: dict[str, Any]
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None
    prefer: Literal["mine", "theirs", None] | None = None
    base_canvas: dict[str, Any] | None = None
    loaded_sequence: int | None = None
    prefer_for_head: int | None = None
    accepts_merge: bool | None = None


class SaveCanvasResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    merged: bool | None = None
    merged_moves: DraftHeadResponse | None = None
    bake_job_id: int
    recomposed: bool | None = None
    changed_tiles: int | None = None
    seeded_pages: list[str] | None = None
    format_floor: FormatFloorApplied | None = None


class SaveCanvasSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: SaveCanvasParams


class SaveTemplateParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    dashboard_id: Annotated[int, Field(ge=1.0)]
    title: Annotated[str, Field(min_length=1, max_length=80)]
    description: Annotated[str | None, Field(max_length=240)] = None


class SaveTemplateSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: SaveTemplateParams


class SessionListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    mine: list[dict[str, Any]] | None = None
    shared: list[dict[str, Any]] | None = None


class SessionResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    session: dict[str, Any]


class ShareDashboardHtmlType(MammothModel):
    model_config = ConfigDict(extra="allow")
    html: str
    title: str
    id: int
    auth_type: str
    was_published: bool
    project_id: int | None = None
    workspace_id: int | None = None


class SignatureListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    signatures: list[dict[str, Any]] | None = None


class SignatureParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    logo: str | None = None
    footer: str | None = None
    link: str | None = None
    align: str | None = None
    layout: str | None = None


class SignatureResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    signature: dict[str, Any]


class SignatureSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: SignatureParams | None = None


class SqlQueryDataResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    data: list[dict[str, Any]]


class StyleListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    styles: list[dict[str, Any]] | None = None


class StylePresetsResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    presets: list[dict[str, Any]] | None = None


class StyleResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    style: dict[str, Any]


class StyleTokensResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    tokens: dict[str, Any]


class SwapDataParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    dataview_id: Annotated[int, Field(ge=1.0)]
    mapping: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None
    currency: Annotated[str | None, Field(max_length=8)] = None


class SwapDataSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: SwapDataParams


class SwapFitParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_ids: Annotated[list[int], Field(min_length=1, max_length=60)]
    include_over_budget: bool | None = None
    seconds_budget: Annotated[float | None, Field(le=30)] = None


class SwapFitResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    fits: list[dict[str, Any]] | None = None
    cell_budget: int
    sample_dataview_ids: list[int] | None = None
    seconds_spent: float | None = None
    seconds_budget: float | None = None


class SwapFitSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: SwapFitParams


class TagMergeParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    target_id: int


class TagRenameParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class TemplateDetailResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    template: dict[str, Any]
    self_fit: dict[str, Any]
    source_dashboard_id: int
    explore: dict[str, Any] | None = None


class TemplateFitResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    fits: list[dict[str, Any]] | None = None
    dataview_id: int


class TemplateListResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    templates: list[dict[str, Any]] | None = None
    use_cases: list[dict[str, Any]] | None = None
    functions: list[dict[str, Any]] | None = None
    industries: list[dict[str, Any]] | None = None
    formats: list[dict[str, Any]] | None = None


class TextBlockSpec(MammothModel):
    model_config = ConfigDict(extra="allow")
    kind: str
    title: str | None = None
    text: str


class TrackActionSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    action: str


class TrackHeartbeatSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    page_id: Annotated[str | None, Field(max_length=200)] = None
    visible_tiles: Annotated[list[str] | None, Field(max_length=200)] = None


class TrackViewResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    session_id: str | None = None


class TrackViewSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    viewport_w: Annotated[int | None, Field(le=100000)] = None
    surface: Annotated[str | None, Field(max_length=24)] = None
    page_id: Annotated[str | None, Field(max_length=200)] = None


class Trigger(RootModel[Literal["new_data", "schedule"]]):
    model_config = ConfigDict(defer_build=True)


class UnpublishedAuthor(MammothModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    user_name: str | None = None
    count: int


class UseTemplateParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    project_id: Annotated[int, Field(ge=1.0)]
    request_token: Annotated[str | None, Field(max_length=64)] = None
    style_id: Annotated[str | None, Field(max_length=128)] = None
    mode: Literal["light", "dark", None] | None = None
    show_summary: bool | None = None
    show_filters: bool | None = None
    kpi_style: Literal["cards", "accent", "tinted", "strip", None] | None = None
    insight_style: Literal["list", "tinted", "cards", "numbered", "banner", None] | None = None
    header_treatment: Literal["photo", "pattern", "gradient", "plain", None] | None = None


class UseTemplateSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: UseTemplateParams


class V3DashboardMetaType(MammothModel):
    model_config = ConfigDict(extra="allow")
    id: int
    title: str
    share: DashboardAuthResponse | None = None
    url: str
    engine: str | None = None
    was_published: bool
    sources: list[int] | None = None
    auto_sync: dict[str, Any] | None = None
    auto_publish: bool | None = None
    is_sync_pending: bool | None = None
    is_publish_pending: bool | None = None
    is_publish_presentation_pending: bool | None = None
    unpublished_authors: list[UnpublishedAuthor] | None = None
    role: str | None = None
    project_id: int | None = None


class VisibilityParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    visibility: str


class VisibilitySpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: VisibilityParams


class WidgetDataParams(MammothModel):
    model_config = ConfigDict(extra="forbid")
    widget_id: Annotated[
        str,
        Field(
            pattern="^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        ),
    ]
    global_filters: dict[str, Any] | None = None
    drilldown_filters: dict[str, Any] | None = None


class WidgetDataResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    data: list[dict[str, Any]]


class WidgetDataSpec(MammothModel):
    model_config = ConfigDict(extra="forbid")
    params: WidgetDataParams


class mmai_dashboard_schema_OpValues(RootModel[Literal["add", "replace"]]):
    model_config = ConfigDict(defer_build=True)


class mmai_dashboard_schema_PathValues(
    RootModel[Literal["intent", "title", "theme", "pages", "filters"]]
):
    model_config = ConfigDict(defer_build=True)


class mmai_dashboards_v3_schema_ChatHistoryResponse(MammothModel):
    model_config = ConfigDict(extra="allow")
    messages: list[dict[str, Any]] | None = None
    sequence: int
    history_index: int | None = None
    revisions: list[ChatRevision] | None = None


__all__ = [
    "AddPagesParams",
    "AddPagesResponse",
    "AddPagesSpec",
    "AdhocQueryParams",
    "AdhocQueryResponse",
    "AdhocQuerySpec",
    "AppendFigureParams",
    "AppendFigureResponse",
    "AppendFigureSpec",
    "ApplyContextReviewParams",
    "ApplyContextReviewSpec",
    "ApplyTemplateParams",
    "ApplyTemplateSpec",
    "AskParams",
    "AskSpec",
    "AttachmentIntentForm",
    "AttachmentJob",
    "AttachmentResponse",
    "AudienceAnonymous",
    "AudienceCountries",
    "AudienceCountry",
    "AudienceDailyPoint",
    "AudienceDevices",
    "AudienceNeverOpened",
    "AudiencePage",
    "AudiencePrevTotals",
    "AudienceResponse",
    "AudienceSummaryItem",
    "AudienceSummaryResponse",
    "AudienceTile",
    "AudienceTotals",
    "AudienceViewer",
    "AudienceViewport",
    "BoardPreviewOut",
    "BoardStatusModel",
    "BulkWidgetDataParams",
    "BulkWidgetDataSpec",
    "CanvasMeta",
    "CanvasResponse",
    "ChangeAudienceParams",
    "ChangeAudienceSpec",
    "ChatEditParams",
    "ChatEditSpec",
    "ChatRevision",
    "ColumnRoster",
    "CommentParams",
    "CommentSpec",
    "ContextExtractParams",
    "ContextExtractResponse",
    "ContextExtractSpec",
    "ContextListResponse",
    "ContextParams",
    "ContextResponse",
    "ContextSpec",
    "CreateBlankParams",
    "CreateBlankResponse",
    "CreateBlankSpec",
    "CreateLiveChartParams",
    "CreateLiveChartResponse",
    "CreateLiveChartSpec",
    "CreateSessionParams",
    "CreateSessionSpec",
    "CreatorDashboardHtmlType",
    "CustomStyleParams",
    "CustomStyleSpec",
    "DashboardAction",
    "DashboardActionParams",
    "DashboardActionSpec",
    "DashboardAnalyticsResponse",
    "DashboardArchiveParams",
    "DashboardAuth",
    "DashboardAuthResponse",
    "DashboardEditParams",
    "DashboardEditSpec",
    "DashboardListSchema",
    "DashboardModelType",
    "DashboardPlaceResponse",
    "DashboardShareParams",
    "DashboardShareSpec",
    "DashboardSource",
    "DashboardSourcesType",
    "DashboardStatus",
    "DashboardTagsParams",
    "DashboardViewConfigType",
    "DefaultStyleParams",
    "DefaultStyleResponse",
    "DefaultStyleSpec",
    "DeriveStyleParams",
    "DeriveStyleResponse",
    "DeriveStyleSpec",
    "DescriptorDataParams",
    "DescriptorDataSpec",
    "DigestPrefResponse",
    "DigestPrefSpec",
    "DraftHeadResponse",
    "DraftMove",
    "DuplicateDashboardResponse",
    "EmailUpdateOut",
    "EmailUpdateSettingsBody",
    "EmailUpdateSubscriptionBody",
    "EmailUpdateSubscriptionOut",
    "EmailUpdateSummaryList",
    "EmailUpdateSummaryOut",
    "EmailUpdateTestOut",
    "EmailUpdatesOut",
    "EmbedPlaceResponse",
    "EngagementActionDay",
    "EngagementActions",
    "EngagementAnonymous",
    "EngagementDailyPoint",
    "EngagementDevices",
    "EngagementEvent",
    "EngagementPage",
    "EngagementPerson",
    "EngagementPersonResponse",
    "EngagementPrevTotals",
    "EngagementReach",
    "EngagementReachCounts",
    "EngagementRemindResponse",
    "EngagementRemindSkip",
    "EngagementRemindSpec",
    "EngagementResponse",
    "EngagementRule",
    "EngagementSurface",
    "EngagementTile",
    "EngagementTotals",
    "EngagementVisit",
    "EngagementVisitPage",
    "ExemplarExtractParams",
    "ExemplarExtractResponse",
    "ExemplarExtractSpec",
    "ExtractBrandParams",
    "ExtractBrandSpec",
    "FeedbackParams",
    "FeedbackSpec",
    "FigureIntentParams",
    "FigureIntentResponse",
    "FigureIntentSpec",
    "FigureOut",
    "FigurePageTarget",
    "FormatFloorApplied",
    "FormatPreviewNotShown",
    "FormatPreviewResponse",
    "Frequency",
    "GenerateDashboardV3Params",
    "GenerateDashboardV3Spec",
    "ImportWorkbookForm",
    "JobResponse",
    "JobSchema",
    "LiveChartBroken",
    "LiveChartListResponse",
    "LiveChartOrigin",
    "LiveChartRef",
    "LiveChartResponse",
    "LiveChartUsageResponse",
    "ObjectJobSchema",
    "OkResponse",
    "OwnDataAcceptParams",
    "OwnDataAcceptSpec",
    "OwnDataStartParams",
    "OwnDataStartSpec",
    "PdfExportParams",
    "PdfExportSpec",
    "PendingTemplateResponse",
    "PlanPageParams",
    "PlanPageResponse",
    "PlanPageSpec",
    "PowerBiPreflightResponse",
    "PowerBiRefusal",
    "PresenceParams",
    "PresenceResponse",
    "PresenceSpec",
    "PresentEditor",
    "PreviewTemplateParams",
    "PreviewTemplateResponse",
    "PreviewTemplateSpec",
    "PublicTemplateListResponse",
    "PublicTemplateResponse",
    "QaInsightsFeedback",
    "QaInsightsFields",
    "QaInsightsGroup",
    "QaInsightsResponse",
    "QaSettingsParams",
    "QaSettingsResponse",
    "QaSettingsSpec",
    "RecordPlacementParams",
    "RecordPlacementSpec",
    "RenameSessionParams",
    "RenameSessionSpec",
    "RenameTemplateParams",
    "RenameTemplateSpec",
    "RenderFigureSvgResponse",
    "RenderFigureSvgSpec",
    "ResolveTemplateMappingParams",
    "ResolveTemplateMappingResponse",
    "ResolveTemplateMappingSpec",
    "RestoreCanvasParams",
    "RestoreCanvasSpec",
    "ReviewContextParams",
    "ReviewContextSpec",
    "RlsAssignmentEntry",
    "RlsAssignmentView",
    "RlsAssignmentsParams",
    "RlsAssignmentsResponse",
    "RlsAssignmentsSpec",
    "RlsColumnsResponse",
    "RlsDistinctValuesResponse",
    "RosterColumn",
    "RosterCorrelation",
    "RosterGeoDim",
    "RosterHierarchy",
    "RosterSignals",
    "SaveCanvasParams",
    "SaveCanvasResponse",
    "SaveCanvasSpec",
    "SaveTemplateParams",
    "SaveTemplateSpec",
    "SessionListResponse",
    "SessionResponse",
    "ShareDashboardHtmlType",
    "SignatureListResponse",
    "SignatureParams",
    "SignatureResponse",
    "SignatureSpec",
    "SqlQueryDataResponse",
    "StyleListResponse",
    "StylePresetsResponse",
    "StyleResponse",
    "StyleTokensResponse",
    "SwapDataParams",
    "SwapDataSpec",
    "SwapFitParams",
    "SwapFitResponse",
    "SwapFitSpec",
    "TagMergeParams",
    "TagRenameParams",
    "TemplateDetailResponse",
    "TemplateFitResponse",
    "TemplateListResponse",
    "TextBlockSpec",
    "TrackActionSpec",
    "TrackHeartbeatSpec",
    "TrackViewResponse",
    "TrackViewSpec",
    "Trigger",
    "UnpublishedAuthor",
    "UseTemplateParams",
    "UseTemplateSpec",
    "V3DashboardMetaType",
    "VisibilityParams",
    "VisibilitySpec",
    "WidgetDataParams",
    "WidgetDataResponse",
    "WidgetDataSpec",
    "mmai_dashboard_schema_OpValues",
    "mmai_dashboard_schema_PathValues",
    "mmai_dashboards_v3_schema_ChatHistoryResponse",
]
