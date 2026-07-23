# ruff: noqa: N801, N815
"""Generated dashboard request and response models. Do not edit by hand."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


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
    conversation_history: list[dict[str, Any]] | None = None


class AskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: AskParams


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
    artifact_version: str | None = None
    filters: dict[str, Any] | None = None
    figures: dict[str, Any] | None = None
    stale_bake: bool | None = None


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


class CommentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: Annotated[str, Field(min_length=1, max_length=2000)]


class CommentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: CommentParams


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
    theme: str
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


class DashboardGenerationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Annotated[str, Field(min_length=1)]
    source: list[int]
    enable_filters: bool | None = None
    enable_pages: bool | None = None


class DashboardGenerationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: DashboardGenerationParams


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


class DashboardSuggestion(BaseModel):
    model_config = ConfigDict(extra="allow")
    format: Literal["dashboard", "presentation", "document"]
    title: str
    intent: str


class DashboardSuggestionsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    suggestions: list[DashboardSuggestion] | None = None


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


class DuplicateDashboardResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int


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
    intent_applied: bool


class FigureIntentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: FigureIntentParams | None = None


class GenerateDashboardV3Params(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Annotated[str, Field(min_length=1)]
    dataview_id: Annotated[int, Field(ge=1.0)]
    format: Literal["dashboard", "presentation", "document", None] | None = None
    contexts: list[str] | None = None
    client_turn_id: str | None = None


class GenerateDashboardV3Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: GenerateDashboardV3Params


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


class PdfExportParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any] | None = None
    paper: str | None = None
    compare: dict[str, Any] | None = None


class PdfExportSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PdfExportParams


class PlanPageParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str | None = None
    archetype: str | None = None
    kind: str | None = None
    fields: dict[str, Any] | None = None


class PlanPageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    page: dict[str, Any]
    composed: bool
    message: str | None = None


class PlanPageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PlanPageParams | None = None


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


class PreviewTemplateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: PreviewTemplateParams


class QaSettingsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_viewer_qa: bool


class QaSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    allow_viewer_qa: bool
    can_manage: bool | None = None


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


class SaveCanvasParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas: dict[str, Any]
    base_sequence: int | None = None
    activity: dict[str, Any] | None = None


class SaveCanvasResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    sequence: int
    bake_job_id: int
    recomposed: bool | None = None
    changed_tiles: int | None = None


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


class TemplateDetailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    template: dict[str, Any]
    self_fit: dict[str, Any]
    sample: dict[str, Any]
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
    industries: list[dict[str, Any]] | None = None
    formats: list[dict[str, Any]] | None = None


class TrackHeartbeatSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str


class TrackViewResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    session_id: str | None = None


class V3DashboardMetaType(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    title: str
    share: DashboardAuthResponse | None = None
    url: str
    was_published: bool
    sources: list[int] | None = None
    auto_sync: dict[str, Any] | None = None
    auto_publish: bool | None = None
    is_sync_pending: bool | None = None
    is_publish_pending: bool | None = None
    is_publish_presentation_pending: bool | None = None


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


_MODEL_NAMESPACE = {name: value for name, value in globals().items() if isinstance(value, type)}
for _model_name in [
    "AdhocQueryParams",
    "AdhocQueryResponse",
    "AdhocQuerySpec",
    "ApplyTemplateParams",
    "ApplyTemplateSpec",
    "AskParams",
    "AskSpec",
    "BulkWidgetDataParams",
    "BulkWidgetDataSpec",
    "CanvasMeta",
    "CanvasResponse",
    "ChatEditParams",
    "ChatEditSpec",
    "CommentParams",
    "CommentSpec",
    "ContextListResponse",
    "ContextParams",
    "ContextResponse",
    "ContextSpec",
    "CreateSessionParams",
    "CreateSessionSpec",
    "CreatorDashboardHtmlType",
    "CustomStyleParams",
    "CustomStyleSpec",
    "DashboardAction",
    "DashboardActionParams",
    "DashboardActionSpec",
    "DashboardAnalyticsResponse",
    "DashboardAuth",
    "DashboardAuthResponse",
    "DashboardEditParams",
    "DashboardEditSpec",
    "DashboardGenerationParams",
    "DashboardGenerationSpec",
    "DashboardListSchema",
    "DashboardModelType",
    "DashboardShareParams",
    "DashboardShareSpec",
    "DashboardSource",
    "DashboardSourcesType",
    "DashboardStatus",
    "DashboardSuggestion",
    "DashboardSuggestionsResponse",
    "DashboardViewConfigType",
    "DefaultStyleParams",
    "DefaultStyleResponse",
    "DefaultStyleSpec",
    "DeriveStyleParams",
    "DeriveStyleResponse",
    "DeriveStyleSpec",
    "DescriptorDataParams",
    "DescriptorDataSpec",
    "DuplicateDashboardResponse",
    "ExtractBrandParams",
    "ExtractBrandSpec",
    "FeedbackParams",
    "FeedbackSpec",
    "FigureIntentParams",
    "FigureIntentResponse",
    "FigureIntentSpec",
    "GenerateDashboardV3Params",
    "GenerateDashboardV3Spec",
    "JobResponse",
    "JobSchema",
    "ObjectJobSchema",
    "OkResponse",
    "PdfExportParams",
    "PdfExportSpec",
    "PlanPageParams",
    "PlanPageResponse",
    "PlanPageSpec",
    "PreviewTemplateParams",
    "PreviewTemplateResponse",
    "PreviewTemplateSpec",
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
    "RlsAssignmentEntry",
    "RlsAssignmentView",
    "RlsAssignmentsParams",
    "RlsAssignmentsResponse",
    "RlsAssignmentsSpec",
    "RlsColumnsResponse",
    "RlsDistinctValuesResponse",
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
    "TemplateDetailResponse",
    "TemplateFitResponse",
    "TemplateListResponse",
    "TrackHeartbeatSpec",
    "TrackViewResponse",
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
    "AdhocQueryParams",
    "AdhocQueryResponse",
    "AdhocQuerySpec",
    "ApplyTemplateParams",
    "ApplyTemplateSpec",
    "AskParams",
    "AskSpec",
    "BulkWidgetDataParams",
    "BulkWidgetDataSpec",
    "CanvasMeta",
    "CanvasResponse",
    "ChatEditParams",
    "ChatEditSpec",
    "CommentParams",
    "CommentSpec",
    "ContextListResponse",
    "ContextParams",
    "ContextResponse",
    "ContextSpec",
    "CreateSessionParams",
    "CreateSessionSpec",
    "CreatorDashboardHtmlType",
    "CustomStyleParams",
    "CustomStyleSpec",
    "DashboardAction",
    "DashboardActionParams",
    "DashboardActionSpec",
    "DashboardAnalyticsResponse",
    "DashboardAuth",
    "DashboardAuthResponse",
    "DashboardEditParams",
    "DashboardEditSpec",
    "DashboardGenerationParams",
    "DashboardGenerationSpec",
    "DashboardListSchema",
    "DashboardModelType",
    "DashboardShareParams",
    "DashboardShareSpec",
    "DashboardSource",
    "DashboardSourcesType",
    "DashboardStatus",
    "DashboardSuggestion",
    "DashboardSuggestionsResponse",
    "DashboardViewConfigType",
    "DefaultStyleParams",
    "DefaultStyleResponse",
    "DefaultStyleSpec",
    "DeriveStyleParams",
    "DeriveStyleResponse",
    "DeriveStyleSpec",
    "DescriptorDataParams",
    "DescriptorDataSpec",
    "DuplicateDashboardResponse",
    "ExtractBrandParams",
    "ExtractBrandSpec",
    "FeedbackParams",
    "FeedbackSpec",
    "FigureIntentParams",
    "FigureIntentResponse",
    "FigureIntentSpec",
    "GenerateDashboardV3Params",
    "GenerateDashboardV3Spec",
    "JobResponse",
    "JobSchema",
    "ObjectJobSchema",
    "OkResponse",
    "PdfExportParams",
    "PdfExportSpec",
    "PlanPageParams",
    "PlanPageResponse",
    "PlanPageSpec",
    "PreviewTemplateParams",
    "PreviewTemplateResponse",
    "PreviewTemplateSpec",
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
    "RlsAssignmentEntry",
    "RlsAssignmentView",
    "RlsAssignmentsParams",
    "RlsAssignmentsResponse",
    "RlsAssignmentsSpec",
    "RlsColumnsResponse",
    "RlsDistinctValuesResponse",
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
    "TemplateDetailResponse",
    "TemplateFitResponse",
    "TemplateListResponse",
    "TrackHeartbeatSpec",
    "TrackViewResponse",
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
