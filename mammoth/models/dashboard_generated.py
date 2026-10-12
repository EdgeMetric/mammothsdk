# ruff: noqa: N801, N815
"""Generated dashboard request and response models. Do not edit by hand."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class AddPagesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pages: Annotated[list[dict[str, Any]], Field(min_length=1)]
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None


class AddPagesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    added_page_ids: list[str] | None = None
    message: str | None = None


class AddPagesSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: AddPagesParams


class AdhocQueryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descriptor: dict[str, Any]


class AdhocQueryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    job_id: int
    descriptor_id: str


class AdhocQuerySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: AdhocQueryParams


class AppendFigureParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataview_id: int
    figure: dict[str, Any]
    banded: dict[str, Any] | None = None
    page: FigurePageTarget | None = None
    base_sequence: int | None = None


class AppendFigureResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    page_id: str
    figure_id: str
    layout_key: str
    page_title: str | None = None


class AppendFigureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: AppendFigureParams


class ApplyContextReviewParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keep: list[str] | None = None
    base_sequence: int | None = None


class ApplyContextReviewSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ApplyContextReviewParams


class ApplyTemplateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_id: Annotated[int, Field(ge=1.0)]
    mapping: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None


class ApplyTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ApplyTemplateParams


class AskParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, Field(min_length=1, max_length=2000)]
    ask_id: Annotated[str | None, Field(max_length=64)] = None
    filter_state: dict[str, Any] | None = None
    conversation_history: list[dict[str, Any]] | None = None


class AskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: AskParams


class AttachmentIntentForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_dataview_id: int


class AttachmentJob(BaseModel):
    model_config = ConfigDict(extra="allow")
    future_id: int


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    attachment_id: int
    filename: str
    kind: str


class AudienceAnonymous(BaseModel):
    model_config = ConfigDict(extra="allow")
    views: int
    public_views: int
    password_views: int


class AudienceCountries(BaseModel):
    model_config = ConfigDict(extra="allow")
    coverage: float
    items: list[AudienceCountry]


class AudienceCountry(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: str
    views: int


class AudienceDailyPoint(BaseModel):
    model_config = ConfigDict(extra="allow")
    date: str
    views: int
    people: int


class AudienceDevices(BaseModel):
    model_config = ConfigDict(extra="allow")
    coverage: float
    desktop: int
    mobile: int
    tablet: int


class AudienceNeverOpened(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    invited_at: str | None = None


class AudiencePage(BaseModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    views: int
    avg_seconds: int | None = None


class AudiencePrevTotals(BaseModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    avg_seconds: int | None = None


class AudienceResponse(BaseModel):
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


class AudienceSummaryItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    views_7d: int
    people_7d: int
    views_30d: int
    last_viewed_at: str | None = None
    daily_14: list[int]


class AudienceSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    items: dict[str, Any]


class AudienceTile(BaseModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    tile_id: str
    views: int


class AudienceTotals(BaseModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    named_people: int
    anonymous_views: int
    avg_seconds: int | None = None
    prev: AudiencePrevTotals


class AudienceViewer(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    last_viewed_at: str | None = None
    visits: int
    seconds: int


class AudienceViewport(BaseModel):
    model_config = ConfigDict(extra="allow")
    coverage: float
    buckets: dict[str, Any]


class BoardStatusModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    state: Literal["active", "archived", "trashed"]
    by_name: str | None = None


class BulkWidgetDataParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    widgets: Annotated[list[WidgetDataParams], Field(min_length=1, max_length=100)]
    rls_preview_value: str | None = None


class BulkWidgetDataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: BulkWidgetDataParams


class CanvasMeta(BaseModel):
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


class CanvasResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    canvas: dict[str, Any]
    plan: dict[str, Any] | None = None
    specs: dict[str, Any] | None = None
    meta: CanvasMeta
    dashboard_id: int | None = None


class ChatEditParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: Annotated[str, Field(min_length=1)]
    scope: dict[str, Any] | None = None
    selected_fig: int | None = None
    active_page_id: str | None = None
    target_tile_id: str | None = None
    conversation_history: list[dict[str, Any]] | None = None
    client_turn_id: str | None = None
    change: list[dict[str, Any]] | dict[str, Any] | None = None


class ChatEditSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ChatEditParams


class ChatRevision(BaseModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    updated_at: str | None = None
    updated_by: int | None = None
    updated_by_name: str | None = None


class ColumnRoster(BaseModel):
    model_config = ConfigDict(extra="allow")
    row_count: int | None = None
    columns: list[RosterColumn] | None = None
    signals: RosterSignals | None = None
    on_board_count: int | None = None


class CommentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: Annotated[str, Field(min_length=1, max_length=2000)]


class CommentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: CommentParams


class ContextExtractParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    size: int | None = None
    type: str | None = None
    text: str | None = None
    content: str | None = None


class ContextExtractResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    file: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    shape: dict[str, Any] | None = None
    figureHeavy: list[str] | None = None
    suggestions: dict[str, Any] | None = None
    condensed: dict[str, Any] | None = None
    skipped: dict[str, Any] | None = None


class ContextExtractSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ContextExtractParams


class ContextListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    contexts: list[dict[str, Any]] | None = None


class ContextParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    type: str | None = None
    files: list[dict[str, Any]] | None = None
    background: str | None = None
    goals: str | None = None
    definitions: str | None = None
    emphasis: str | None = None
    guardrails: str | None = None


class ContextResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    context: dict[str, Any]


class ContextSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ContextParams | None = None


class CreateBlankParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataview_id: int
    style: str | None = None
    title: str | None = None


class CreateBlankResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    sequence: int


class CreateBlankSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: CreateBlankParams


class CreateSessionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str | None, Field(max_length=200)] = None


class CreateSessionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: CreateSessionParams | None = None


class CreatorDashboardHtmlType(BaseModel):
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


class CustomStyleParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signals: dict[str, Any] | None = None
    tokens: dict[str, Any] | None = None
    name: str | None = None
    blurb: str | None = None
    source: dict[str, Any] | None = None


class CustomStyleSpec(BaseModel):
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
    pass


class DashboardActionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool | None = None
    view_id: int | None = None
    sequence: int | None = None
    notify_authors: bool | None = None
    filter_column: str | None = None


class DashboardActionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: DashboardAction
    params: DashboardActionParams | None = None


class DashboardAnalyticsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    total_views: int
    average_time_spent_seconds: float | None = None
    viewed_by: str
    current_concurrent_viewers: int


class DashboardArchiveParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    archived: bool


class DashboardAuth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type_of_auth: Literal["mammoth", "public", "password"]
    options: dict[str, Any] | None = None
    sequence: int | None = None


class DashboardAuthResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    type_of_auth: Literal["mammoth", "public", "password"]
    options: dict[str, Any] | None = None
    sequence: int | None = None


class DashboardEditParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: mmai_dashboard_schema_OpValues
    path: mmai_dashboard_schema_PathValues
    value: str | dict[str, Any]


class DashboardEditSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: list[DashboardEditParams]


class DashboardListSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    dashboards: list[DashboardModelType]


class DashboardModelType(BaseModel):
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


class DashboardShareParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auth: DashboardAuth


class DashboardShareSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: DashboardShareParams


class DashboardSource(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str
    rows: int
    columns: int
    updated_at: str
    workspace_name: str


class DashboardSourcesType(BaseModel):
    model_config = ConfigDict(extra="allow")
    sources: list[DashboardSource]


class DashboardStatus(RootModel[Literal["draft", "published", "archived", "deleted", "error"]]):
    pass


class DashboardTagsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tags: list[str] | None = None


class DashboardViewConfigType(BaseModel):
    model_config = ConfigDict(extra="allow")
    auto_sync: bool
    is_sync_pending: bool
    last_synced_at: str | None = None


class DefaultStyleParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    styleId: Annotated[str, Field(min_length=1)]


class DefaultStyleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    style_id: str


class DefaultStyleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: DefaultStyleParams


class DeriveStyleParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signals: dict[str, Any] | None = None


class DeriveStyleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    style_tokens: dict[str, Any]


class DeriveStyleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: DeriveStyleParams | None = None


class DescriptorDataParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descriptor_ids: Annotated[list[str], Field(min_length=1, max_length=200)]
    filter_state: dict[str, Any] | None = None
    rls_preview_value: str | None = None


class DescriptorDataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: DescriptorDataParams


class DigestPrefResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    enabled: bool
    explicit: bool | None = None
    default_on: bool | None = None


class DigestPrefSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool | None = None


class DraftHeadResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    head_sequence: int
    base_sequence: int | None = None
    count: int
    moves: list[DraftMove] | None = None


class DraftMove(BaseModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    user_id: int | None = None
    user_name: str | None = None
    at: str | None = None
    kind: Literal["edit", "assistant", "sync"]
    label: str | None = None


class DuplicateDashboardResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    swap_job_id: int | None = None


class EngagementActionDay(BaseModel):
    model_config = ConfigDict(extra="allow")
    pdf: int
    link_copy: int
    powerbi: int
    tableau: int
    video: int
    date: str


class EngagementActions(BaseModel):
    model_config = ConfigDict(extra="allow")
    pdf: int
    link_copy: int
    powerbi: int
    tableau: int
    video: int
    daily: list[EngagementActionDay]


class EngagementAnonymous(BaseModel):
    model_config = ConfigDict(extra="allow")
    views: int
    seconds: int


class EngagementDailyPoint(BaseModel):
    model_config = ConfigDict(extra="allow")
    date: str
    views: int
    people: int
    prev_views: int
    prev_people: int


class EngagementDevices(BaseModel):
    model_config = ConfigDict(extra="allow")
    desktop: int
    mobile: int
    tablet: int
    coverage: float


class EngagementEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    at: str
    kind: Literal["published", "edited", "refreshed", "shared"]
    count: int
    label: str


class EngagementPage(BaseModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    name: str
    reached: int
    views: int
    avg_s: int | None = None
    tiles: list[EngagementTile]


class EngagementPerson(BaseModel):
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


class EngagementPersonResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    name: str
    visits: list[EngagementVisit]


class EngagementPrevTotals(BaseModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    avg_engaged_s: int | None = None
    questions: int


class EngagementReach(BaseModel):
    model_config = ConfigDict(extra="allow")
    shared: int
    opened: int
    returned: int
    engaged: int
    prev: EngagementReachCounts


class EngagementReachCounts(BaseModel):
    model_config = ConfigDict(extra="allow")
    shared: int
    opened: int
    returned: int
    engaged: int


class EngagementRemindResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    sent: list[int]
    skipped: list[EngagementRemindSkip]


class EngagementRemindSkip(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    reason: Literal["not_shared", "opened", "no_email", "recently_reminded", "send_failed"]
    next_at: str | None = None


class EngagementRemindSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_ids: Annotated[list[int], Field(min_length=1, max_length=200)]


class EngagementResponse(BaseModel):
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


class EngagementRule(BaseModel):
    model_config = ConfigDict(extra="allow")
    seconds: int
    pages: int


class EngagementSurface(BaseModel):
    model_config = ConfigDict(extra="allow")
    app: int
    link: int
    embed: int


class EngagementTile(BaseModel):
    model_config = ConfigDict(extra="allow")
    tile_id: str
    title: str | None = None
    seen_pct: float


class EngagementTotals(BaseModel):
    model_config = ConfigDict(extra="allow")
    views: int
    people: int
    anon_views: int
    avg_engaged_s: int | None = None
    questions: int
    unanswered: int
    prev: EngagementPrevTotals


class EngagementVisit(BaseModel):
    model_config = ConfigDict(extra="allow")
    started_at: str | None = None
    seconds: int | None = None
    pages: list[EngagementVisitPage]
    device: str | None = None
    surface: Literal["app", "link", "embed"]


class EngagementVisitPage(BaseModel):
    model_config = ConfigDict(extra="allow")
    page_id: str
    name: str
    seconds: int


class ExemplarExtractParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    size: int | None = None
    type: str | None = None
    content: str | None = None
    text: str | None = None
    dataview_id: int | None = None
    table_item_id: int | None = None


class ExemplarExtractResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    spec: dict[str, Any] | None = None
    rejected: dict[str, Any] | None = None
    source: dict[str, Any] | None = None
    palette: list[str] | None = None
    measures: list[str] | None = None
    countable: list[str] | None = None
    brand: dict[str, Any] | None = None
    scopes: list[dict[str, Any]] | None = None


class ExemplarExtractSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ExemplarExtractParams


class ExtractBrandParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: Annotated[str, Field(min_length=1)]


class ExtractBrandSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ExtractBrandParams


class FeedbackParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: Literal["up", "down", None] | None = None


class FeedbackSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: FeedbackParams | None = None


class FigureIntentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    kind: str | None = None
    fields: dict[str, Any] | None = None


class FigureIntentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    kind: str
    added: dict[str, Any] | None = None
    spec: dict[str, Any] | None = None
    empty: bool | None = None
    caption: str | None = None
    caveat: str | None = None
    text: TextBlockSpec | None = None
    intent_applied: bool


class FigureIntentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: FigureIntentParams | None = None


class FigurePageTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    new_title: Annotated[str | None, Field(max_length=80)] = None


class FormatFloorApplied(BaseModel):
    model_config = ConfigDict(extra="allow")
    filters_added: int | None = None
    pages_added: list[str] | None = None
    cover_added: bool | None = None
    charts_composed: int | None = None


class FormatPreviewNotShown(BaseModel):
    model_config = ConfigDict(extra="allow")
    what: str
    count: int
    reason: str


class FormatPreviewResponse(BaseModel):
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


class GenerateDashboardV3Params(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    dataview_id: Annotated[int, Field(ge=1.0)]
    format: Literal["dashboard", "presentation", "document", "qa", None] | None = None
    contexts: list[str] | None = None
    client_turn_id: str | None = None
    title: Annotated[str | None, Field(max_length=200)] = None
    design_from: Annotated[int | None, Field(ge=1)] = None


class GenerateDashboardV3Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: GenerateDashboardV3Params


class ImportWorkbookForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file: str
    project_id: int | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    job: JobSchema


class JobSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Annotated[int, Field(ge=0.0)]
    status: Literal["success", "failure", "processing", "error"]
    response: dict[str, Any] | list[Any]
    last_updated_at: str
    created_at: str
    path: str
    operation: str


class ObjectJobSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    status_code: int | None = None
    job_id: int | None = None
    failure_reason: str | None = None


class OkResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    ok: bool


class OwnDataAcceptParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choice: Literal["proposal", "partial", "reshape"] | None = None
    exclude: Annotated[list[str] | None, Field(max_length=20)] = None


class OwnDataAcceptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: OwnDataAcceptParams


class OwnDataStartParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ingest_job_id: Annotated[int | None, Field(ge=1)] = None
    dataset_id: Annotated[int | None, Field(ge=1)] = None
    dataview_id: Annotated[int | None, Field(ge=1)] = None
    file_name: Annotated[str | None, Field(max_length=255)] = None


class OwnDataStartSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: OwnDataStartParams


class PdfExportParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any] | None = None
    paper: str | None = None
    carousel: bool | None = None
    compare: dict[str, Any] | None = None


class PdfExportSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PdfExportParams


class PendingTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    slug: str | None = None


class PlanPageParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    archetype: str | None = None
    kind: str | None = None
    fields: dict[str, Any] | None = None
    page_id: str | None = None


class PlanPageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    page: dict[str, Any]
    composed: bool
    message: str | None = None
    preview: list[dict[str, Any]] | None = None


class PlanPageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PlanPageParams | None = None


class PowerBiPreflightResponse(BaseModel):
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


class PowerBiRefusal(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str
    reason: str


class PresenceParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: Annotated[str, Field(min_length=1, max_length=64)]
    page_id: Annotated[str | None, Field(max_length=128)] = None
    tile_id: Annotated[str | None, Field(max_length=128)] = None
    busy_tile_id: Annotated[str | None, Field(max_length=128)] = None
    idle: bool | None = None
    since: int | None = None
    leave: bool | None = None


class PresenceResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    others: list[PresentEditor] | None = None
    status: BoardStatusModel
    head: DraftHeadResponse | None = None


class PresenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PresenceParams


class PresentEditor(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    user_name: str | None = None
    page_id: str | None = None
    tile_id: str | None = None
    busy_tile_id: str | None = None
    idle: bool | None = None


class PreviewTemplateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_id: Annotated[int, Field(ge=1.0)]
    table_item_id: Annotated[int | None, Field(ge=1)] = None
    mapping: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None


class PreviewTemplateResponse(BaseModel):
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


class PreviewTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PreviewTemplateParams


class PublicTemplateListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    templates: list[dict[str, Any]] | None = None
    total: int | None = None
    use_cases: list[dict[str, Any]] | None = None
    functions: list[dict[str, Any]] | None = None
    industries: list[dict[str, Any]] | None = None
    formats: list[dict[str, Any]] | None = None


class PublicTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    template: dict[str, Any]


class QaInsightsFeedback(BaseModel):
    model_config = ConfigDict(extra="allow")
    up: int
    down: int


class QaInsightsFields(BaseModel):
    model_config = ConfigDict(extra="allow")
    measure: str | None = None
    dimension: str | None = None


class QaInsightsGroup(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str
    count: int
    last_asked_at: str
    down: int
    up: int
    unanswered: int
    fields: QaInsightsFields | None = None


class QaInsightsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    range_days: int
    questions_total: int
    feedback: QaInsightsFeedback
    groups: list[QaInsightsGroup]


class QaSettingsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_viewer_qa: bool


class QaSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    allow_viewer_qa: bool
    can_manage: bool | None = None
    public_link: bool | None = None


class QaSettingsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: QaSettingsParams


class RenameSessionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, Field(min_length=1, max_length=200)]


class RenameSessionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: RenameSessionParams


class RenameTemplateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, Field(min_length=1, max_length=80)]
    description: Annotated[str | None, Field(max_length=240)] = None


class RenameTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: RenameTemplateParams


class ResolveTemplateMappingParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_id: Annotated[int, Field(ge=1.0)]


class ResolveTemplateMappingResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    mapping: dict[str, Any]
    fidelity: dict[str, Any]
    target_fields: dict[str, Any] | None = None


class ResolveTemplateMappingSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ResolveTemplateMappingParams


class RestoreCanvasParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_sequence: Annotated[int, Field(ge=1.0)]
    base_sequence: int | None = None
    history_index: int | None = None
    activity: dict[str, Any] | None = None


class RestoreCanvasSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: RestoreCanvasParams


class ReviewContextParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: str | None = None
    note: Annotated[str | None, Field(max_length=1000)] = None
    fresh: bool | None = None


class ReviewContextSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: ReviewContextParams | None = None


class RlsAssignmentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    all_access: bool | None = None
    values: list[str] | None = None


class RlsAssignmentView(BaseModel):
    model_config = ConfigDict(extra="allow")
    email: str
    all_access: bool
    values: list[str]
    value_missing: bool


class RlsAssignmentsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignments: list[RlsAssignmentEntry] | None = None


class RlsAssignmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    enabled: bool
    filter_column: str | None = None
    assignments: list[RlsAssignmentView]


class RlsAssignmentsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: RlsAssignmentsParams


class RlsColumnsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    columns: list[str]


class RlsDistinctValuesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    column: str
    total: int
    values: list[Any]


class RosterColumn(BaseModel):
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


class RosterCorrelation(BaseModel):
    model_config = ConfigDict(extra="allow")
    a: str
    b: str
    r: float


class RosterGeoDim(BaseModel):
    model_config = ConfigDict(extra="allow")
    field: str
    scope: str


class RosterHierarchy(BaseModel):
    model_config = ConfigDict(extra="allow")
    outer: str
    inner: str


class RosterSignals(BaseModel):
    model_config = ConfigDict(extra="allow")
    correlations: list[RosterCorrelation] | None = None
    hierarchy: RosterHierarchy | None = None
    ledger_field: str | None = None
    geo_dims: list[RosterGeoDim] | None = None


class SaveCanvasParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas: dict[str, Any]
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None
    prefer: Literal["mine", "theirs", None] | None = None
    base_canvas: dict[str, Any] | None = None
    loaded_sequence: int | None = None
    prefer_for_head: int | None = None
    accepts_merge: bool | None = None


class SaveCanvasResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    merged: bool | None = None
    merged_moves: DraftHeadResponse | None = None
    bake_job_id: int
    recomposed: bool | None = None
    changed_tiles: int | None = None
    seeded_pages: list[str] | None = None
    format_floor: FormatFloorApplied | None = None


class SaveCanvasSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: SaveCanvasParams


class SaveTemplateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dashboard_id: Annotated[int, Field(ge=1.0)]
    title: Annotated[str, Field(min_length=1, max_length=80)]
    description: Annotated[str | None, Field(max_length=240)] = None


class SaveTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: SaveTemplateParams


class SessionListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    mine: list[dict[str, Any]] | None = None
    shared: list[dict[str, Any]] | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    session: dict[str, Any]


class ShareDashboardHtmlType(BaseModel):
    model_config = ConfigDict(extra="allow")
    html: str
    title: str
    id: int
    auth_type: str
    was_published: bool
    project_id: int | None = None
    workspace_id: int | None = None


class SignatureListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    signatures: list[dict[str, Any]] | None = None


class SignatureParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    logo: str | None = None
    footer: str | None = None
    link: str | None = None
    align: str | None = None
    layout: str | None = None


class SignatureResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    signature: dict[str, Any]


class SignatureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: SignatureParams | None = None


class SqlQueryDataResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[dict[str, Any]]


class StyleListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    styles: list[dict[str, Any]] | None = None


class StylePresetsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    presets: list[dict[str, Any]] | None = None


class StyleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    style: dict[str, Any]


class StyleTokensResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    tokens: dict[str, Any]


class SwapDataParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataview_id: Annotated[int, Field(ge=1.0)]
    mapping: dict[str, Any] | None = None
    overrides: dict[str, Any] | None = None
    currency: Annotated[str | None, Field(max_length=8)] = None


class SwapDataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: SwapDataParams


class SwapFitParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_dashboard_id: Annotated[int, Field(ge=1.0)]
    target_dataview_ids: Annotated[list[int], Field(min_length=1, max_length=60)]
    include_over_budget: bool | None = None
    seconds_budget: Annotated[float | None, Field(le=30)] = None


class SwapFitResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    fits: list[dict[str, Any]] | None = None
    cell_budget: int
    sample_dataview_ids: list[int] | None = None
    seconds_spent: float | None = None
    seconds_budget: float | None = None


class SwapFitSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: SwapFitParams


class TagMergeParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_id: int


class TagRenameParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class TemplateDetailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    template: dict[str, Any]
    self_fit: dict[str, Any]
    source_dashboard_id: int
    explore: dict[str, Any] | None = None


class TemplateFitResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    fits: list[dict[str, Any]] | None = None
    dataview_id: int


class TemplateListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    templates: list[dict[str, Any]] | None = None
    use_cases: list[dict[str, Any]] | None = None
    functions: list[dict[str, Any]] | None = None
    industries: list[dict[str, Any]] | None = None
    formats: list[dict[str, Any]] | None = None


class TextBlockSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    kind: str
    title: str | None = None
    text: str


class TrackActionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str


class TrackHeartbeatSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    page_id: Annotated[str | None, Field(max_length=200)] = None
    visible_tiles: Annotated[list[str] | None, Field(max_length=200)] = None


class TrackViewResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    session_id: str | None = None


class TrackViewSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    viewport_w: Annotated[int | None, Field(le=100000)] = None
    surface: Annotated[str | None, Field(max_length=24)] = None
    page_id: Annotated[str | None, Field(max_length=200)] = None


class UnpublishedAuthor(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: int
    user_name: str | None = None
    count: int


class UseTemplateParams(BaseModel):
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


class UseTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: UseTemplateParams


class V3DashboardMetaType(BaseModel):
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


class VisibilityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visibility: str


class VisibilitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: VisibilityParams


class WidgetDataParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    widget_id: Annotated[
        str,
        Field(
            pattern="^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        ),
    ]
    global_filters: dict[str, Any] | None = None
    drilldown_filters: dict[str, Any] | None = None


class WidgetDataResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[dict[str, Any]]


class WidgetDataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: WidgetDataParams


class mmai_dashboard_schema_OpValues(RootModel[Literal["add", "replace"]]):
    pass


class mmai_dashboard_schema_PathValues(
    RootModel[Literal["intent", "title", "theme", "pages", "filters"]]
):
    pass


class mmai_dashboards_v3_schema_ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    messages: list[dict[str, Any]] | None = None
    sequence: int
    history_index: int | None = None
    revisions: list[ChatRevision] | None = None


_MODEL_NAMESPACE = {name: value for name, value in globals().items() if isinstance(value, type)}
for _model_name in [
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
    "BoardStatusModel",
    "BulkWidgetDataParams",
    "BulkWidgetDataSpec",
    "CanvasMeta",
    "CanvasResponse",
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
    "FigurePageTarget",
    "FormatFloorApplied",
    "FormatPreviewNotShown",
    "FormatPreviewResponse",
    "GenerateDashboardV3Params",
    "GenerateDashboardV3Spec",
    "ImportWorkbookForm",
    "JobResponse",
    "JobSchema",
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
    "RenameSessionParams",
    "RenameSessionSpec",
    "RenameTemplateParams",
    "RenameTemplateSpec",
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
]:
    globals()[_model_name].model_rebuild(_types_namespace=_MODEL_NAMESPACE)

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
    "BoardStatusModel",
    "BulkWidgetDataParams",
    "BulkWidgetDataSpec",
    "CanvasMeta",
    "CanvasResponse",
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
    "FigurePageTarget",
    "FormatFloorApplied",
    "FormatPreviewNotShown",
    "FormatPreviewResponse",
    "GenerateDashboardV3Params",
    "GenerateDashboardV3Spec",
    "ImportWorkbookForm",
    "JobResponse",
    "JobSchema",
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
    "RenameSessionParams",
    "RenameSessionSpec",
    "RenameTemplateParams",
    "RenameTemplateSpec",
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
