# ruff: noqa: F401, I001
"""Generated public dashboard API wrappers. Do not edit by hand."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from mammoth.models.dashboard_generated import (
    AdhocQueryParams,
    AdhocQueryResponse,
    AdhocQuerySpec,
    ApplyTemplateParams,
    ApplyTemplateSpec,
    AskParams,
    AskSpec,
    BulkWidgetDataParams,
    BulkWidgetDataSpec,
    CanvasMeta,
    CanvasResponse,
    ChatEditParams,
    ChatEditSpec,
    CommentParams,
    CommentSpec,
    ContextListResponse,
    ContextParams,
    ContextResponse,
    ContextSpec,
    CreateSessionParams,
    CreateSessionSpec,
    CreatorDashboardHtmlType,
    CustomStyleParams,
    CustomStyleSpec,
    DashboardAction,
    DashboardActionParams,
    DashboardActionSpec,
    DashboardAnalyticsResponse,
    DashboardAuth,
    DashboardEditParams,
    DashboardEditSpec,
    DashboardGenerationParams,
    DashboardGenerationSpec,
    DashboardListSchema,
    DashboardModelType,
    DashboardShareParams,
    DashboardShareSpec,
    DashboardSource,
    DashboardSourcesType,
    DashboardStatus,
    DashboardSuggestion,
    DashboardSuggestionsResponse,
    DashboardViewConfigType,
    DefaultStyleParams,
    DefaultStyleResponse,
    DefaultStyleSpec,
    DeriveStyleParams,
    DeriveStyleResponse,
    DeriveStyleSpec,
    DescriptorDataParams,
    DescriptorDataSpec,
    DuplicateDashboardResponse,
    ExtractBrandParams,
    ExtractBrandSpec,
    FeedbackParams,
    FeedbackSpec,
    FigureIntentParams,
    FigureIntentResponse,
    FigureIntentSpec,
    GenerateDashboardV3Params,
    GenerateDashboardV3Spec,
    JobResponse,
    JobSchema,
    ObjectJobSchema,
    OkResponse,
    PdfExportParams,
    PdfExportSpec,
    PlanPageParams,
    PlanPageResponse,
    PlanPageSpec,
    PreviewTemplateParams,
    PreviewTemplateResponse,
    PreviewTemplateSpec,
    QaSettingsParams,
    QaSettingsResponse,
    QaSettingsSpec,
    RenameSessionParams,
    RenameSessionSpec,
    RenameTemplateParams,
    RenameTemplateSpec,
    ResolveTemplateMappingParams,
    ResolveTemplateMappingResponse,
    ResolveTemplateMappingSpec,
    RestoreCanvasParams,
    RestoreCanvasSpec,
    RlsAssignmentEntry,
    RlsAssignmentView,
    RlsAssignmentsParams,
    RlsAssignmentsResponse,
    RlsAssignmentsSpec,
    RlsColumnsResponse,
    RlsDistinctValuesResponse,
    SaveCanvasParams,
    SaveCanvasResponse,
    SaveCanvasSpec,
    SaveTemplateParams,
    SaveTemplateSpec,
    SessionListResponse,
    SessionResponse,
    ShareDashboardHtmlType,
    SignatureListResponse,
    SignatureParams,
    SignatureResponse,
    SignatureSpec,
    SqlQueryDataResponse,
    StyleListResponse,
    StylePresetsResponse,
    StyleResponse,
    StyleTokensResponse,
    TemplateDetailResponse,
    TemplateFitResponse,
    TemplateListResponse,
    TrackHeartbeatSpec,
    TrackViewResponse,
    V3DashboardMetaType,
    VisibilityParams,
    VisibilitySpec,
    WidgetDataParams,
    WidgetDataResponse,
    WidgetDataSpec,
    mmai_dashboard_schema_OpValues,
    mmai_dashboard_schema_PathValues,
    mmai_dashboards_v3_schema_ChatHistoryResponse,
)


def _json_body(body: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", by_alias=True, exclude_none=True)
    return body


def _typed_response(
    response: Any,
    models: tuple[type[BaseModel], ...],
    *,
    allow_untyped: bool = False,
) -> Any:
    """Coerce ``response`` into the best-matching model.

    Response models tolerate additive server fields, so more than one may
    validate a payload. The best match is the model that populates the most
    declared fields (ties broken toward the model with more fields). When the
    operation also documents an untyped branch (``allow_untyped``) and no model
    is a positive match, the raw response is returned instead of raising -- so a
    valid arbitrary-object response is never rejected.
    """
    ranked = sorted(models, key=lambda model: len(model.model_fields), reverse=True)
    best: Any = None
    best_score = -1
    last_error: ValidationError | None = None
    for model in ranked:
        try:
            validated = model.model_validate(response)
        except ValidationError as error:
            last_error = error
            continue
        if isinstance(response, dict):
            score = sum(
                1
                for name, field in model.model_fields.items()
                if (field.alias or name) in response or name in response
            )
        else:
            score = 0
        if score > best_score:
            best, best_score = validated, score
    if best is not None and (best_score > 0 or not allow_untyped):
        return best
    if allow_untyped:
        return response
    if last_error is not None:
        raise last_error
    raise ValueError("typed response requires at least one model")


def analytics(self: Any, dashboard_id: int) -> DashboardAnalyticsResponse:
    """Get Dashboard Analytics."""
    path = "/dashboards/{dashboard_id}/analytics"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (DashboardAnalyticsResponse,), allow_untyped=False)


def source_list(self: Any) -> DashboardSourcesType:
    """Get Dashboard Sources."""
    path = "/dashboards/sources"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (DashboardSourcesType,), allow_untyped=False)


def data_draft(
    self: Any, dashboard_id: int, body: WidgetDataSpec
) -> WidgetDataResponse | ObjectJobSchema | JobResponse:
    """Get draft data from given SQL query."""
    path = "/dashboards/{dashboard_id}/getDraftData"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(
        response, (WidgetDataResponse, ObjectJobSchema, JobResponse), allow_untyped=False
    )


def data_published(
    self: Any, dashboard_id: int, body: WidgetDataSpec
) -> WidgetDataResponse | ObjectJobSchema | JobResponse:
    """Get published data from given SQL query."""
    path = "/dashboards/{dashboard_id}/getPublishData"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(
        response, (WidgetDataResponse, ObjectJobSchema, JobResponse), allow_untyped=False
    )


def rls_column_list(self: Any, dashboard_id: int) -> RlsColumnsResponse:
    """Candidate columns for the RLS filter."""
    path = "/dashboards/{dashboard_id}/rls/columns"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (RlsColumnsResponse,), allow_untyped=False)


def rls_value_list(
    self: Any, dashboard_id: int, column: str, search: str | None = None
) -> RlsDistinctValuesResponse:
    """Distinct values for an RLS filter column."""
    path = "/dashboards/{dashboard_id}/rls/values"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = {
        key: value
        for key, value in {"column": column, "search": search}.items()
        if value is not None
    }
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (RlsDistinctValuesResponse,), allow_untyped=False)


def rls_assignment_list(self: Any, dashboard_id: int) -> RlsAssignmentsResponse:
    """List RLS viewer assignments."""
    path = "/dashboards/{dashboard_id}/rls/assignments"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (RlsAssignmentsResponse,), allow_untyped=False)


def rls_assignment_set(self: Any, dashboard_id: int, body: RlsAssignmentsSpec) -> dict[str, Any]:
    """Replace RLS viewer assignments."""
    path = "/dashboards/{dashboard_id}/rls/assignments"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return response


def query(self: Any, dashboard_id: int, body: AdhocQuerySpec) -> AdhocQueryResponse:
    """Editor ad-hoc descriptor query."""
    path = "/dashboards/{dashboard_id}/query"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (AdhocQueryResponse,), allow_untyped=False)


def template_apply(self: Any, body: ApplyTemplateSpec) -> ObjectJobSchema | JobResponse:
    """Apply a template to a target dataset."""
    path = "/dashboards/v3/templates/apply"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def chat_history(
    self: Any, dashboard_id: int, sequence: int | None = None
) -> mmai_dashboards_v3_schema_ChatHistoryResponse:
    """Editor chat transcript."""
    path = "/dashboards/{dashboard_id}/chat"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = {key: value for key, value in {"sequence": sequence}.items() if value is not None}
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(
        response, (mmai_dashboards_v3_schema_ChatHistoryResponse,), allow_untyped=False
    )


def chat_edit(self: Any, dashboard_id: int, body: ChatEditSpec) -> ObjectJobSchema | JobResponse:
    """One chat-edit turn."""
    path = "/dashboards/{dashboard_id}/chat"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def suggestion_list(
    self: Any, dataview_id: int, table_item_id: int | None = None
) -> DashboardSuggestionsResponse:
    """Data-grounded starting points for the create screen."""
    path = "/dashboards/v3/suggestions"
    params = {
        key: value
        for key, value in {"dataview_id": dataview_id, "table_item_id": table_item_id}.items()
        if value is not None
    }
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (DashboardSuggestionsResponse,), allow_untyped=False)


def descriptor_data(
    self: Any, dashboard_id: int, body: DescriptorDataSpec
) -> ObjectJobSchema | JobResponse:
    """Descriptor data — future-request."""
    path = "/dashboards/{dashboard_id}/data"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def published_data(self: Any, url: str, body: DescriptorDataSpec) -> ObjectJobSchema | JobResponse:
    """Descriptor data for a published dashboard."""
    path = "/dashboards/url/{url}/data"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def duplicate(self: Any, dashboard_id: int) -> DuplicateDashboardResponse:
    """Duplicate a v3 dashboard."""
    path = "/dashboards/v3/{dashboard_id}/duplicate"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params)
    return _typed_response(response, (DuplicateDashboardResponse,), allow_untyped=False)


def pdf_export(self: Any, dashboard_id: int, body: PdfExportSpec) -> ObjectJobSchema | JobResponse:
    """Kick a draft-dashboard PDF export."""
    path = "/dashboards/{dashboard_id}/pdf"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def published_pdf_export(self: Any, url: str, body: PdfExportSpec) -> ObjectJobSchema | JobResponse:
    """Kick a published-dashboard PDF export."""
    path = "/dashboards/url/{url}/pdf"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def video_export(self: Any, dashboard_id: int) -> ObjectJobSchema | JobResponse:
    """Kick a motion-story video export."""
    path = "/dashboards/{dashboard_id}/video"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params)
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def published_video_export(self: Any, url: str) -> ObjectJobSchema | JobResponse:
    """Kick a motion-story video export (published view)."""
    path = "/dashboards/url/{url}/video"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("POST", path, params=params)
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def figure_intent(self: Any, dashboard_id: int, body: FigureIntentSpec) -> FigureIntentResponse:
    """Resolve an AI-add figure from an intent."""
    path = "/dashboards/{dashboard_id}/figure-intent"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (FigureIntentResponse,), allow_untyped=False)


def v3_generate(self: Any, body: GenerateDashboardV3Spec) -> ObjectJobSchema | JobResponse:
    """Generate a v3 dashboard."""
    path = "/dashboards/v3/generate"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def canvas_get(self: Any, dashboard_id: int, sequence: int | None = None) -> CanvasResponse:
    """Editor canvas (draft)."""
    path = "/dashboards/{dashboard_id}/canvas"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = {key: value for key, value in {"sequence": sequence}.items() if value is not None}
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (CanvasResponse,), allow_untyped=False)


def canvas_save(self: Any, dashboard_id: int, body: SaveCanvasSpec) -> SaveCanvasResponse:
    """Save the canvas (append a draft version)."""
    path = "/dashboards/{dashboard_id}/canvas"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (SaveCanvasResponse,), allow_untyped=False)


def published_canvas(self: Any, url: str) -> CanvasResponse:
    """Published viewer canvas."""
    path = "/dashboards/url/{url}/canvas"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (CanvasResponse,), allow_untyped=False)


def pdf_artifact(self: Any, dashboard_id: int, job_id: int) -> dict[str, Any]:
    """Download a completed draft PDF export."""
    path = "/dashboards/{dashboard_id}/pdf/{job_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{job_id}", str(job_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def published_pdf_artifact(self: Any, url: str, job_id: int) -> dict[str, Any]:
    """Download a completed published PDF export."""
    path = "/dashboards/url/{url}/pdf/{job_id}"
    path = path.replace("{url}", str(url))
    path = path.replace("{job_id}", str(job_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def video_state(self: Any, dashboard_id: int) -> dict[str, Any]:
    """Motion-story video export state (never kicks a render)."""
    path = "/dashboards/{dashboard_id}/video-state"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def og_card(self: Any, dashboard_id: int) -> dict[str, Any]:
    """Dashboard card thumbnail (draft or published PNG)."""
    path = "/dashboards/{dashboard_id}/og-card"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def published_og_card(self: Any, url: str) -> dict[str, Any]:
    """Published dashboard's link-unfurl OG card (baked PNG)."""
    path = "/dashboards/url/{url}/og-card"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def page_plan(self: Any, dashboard_id: int, body: PlanPageSpec) -> PlanPageResponse:
    """Compose a new page from an intent."""
    path = "/dashboards/{dashboard_id}/plan-page"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (PlanPageResponse,), allow_untyped=False)


def template_preview(self: Any, body: PreviewTemplateSpec) -> PreviewTemplateResponse:
    """Preview a template mapping applied to a target dataset."""
    path = "/dashboards/v3/templates/preview"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (PreviewTemplateResponse,), allow_untyped=False)


def template_resolve_mapping(
    self: Any, body: ResolveTemplateMappingSpec
) -> ResolveTemplateMappingResponse:
    """Propose a template mapping onto a target dataset."""
    path = "/dashboards/v3/templates/resolve-mapping"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ResolveTemplateMappingResponse,), allow_untyped=False)


def canvas_restore(
    self: Any, dashboard_id: int, body: RestoreCanvasSpec
) -> ObjectJobSchema | JobResponse:
    """Undo / redo / revert the canvas to a target version."""
    path = "/dashboards/{dashboard_id}/canvas/restore"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def published_share_page(self: Any, url: str) -> dict[str, Any]:
    """Published dashboard's link-unfurl share page (crawler-facing HTML)."""
    path = "/dashboards/url/{url}/share"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def published_video_artifact(self: Any, url: str) -> dict[str, Any]:
    """Stream a published motion-story video (Range-enabled)."""
    path = "/dashboards/url/{url}/video.mp4"
    path = path.replace("{url}", str(url))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return response


def qa_comment_create(
    self: Any, dashboard_id: int, session_id: int, body: CommentSpec
) -> SessionResponse:
    """Comment on a shared Q&A session."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/comments"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_ask(
    self: Any, dashboard_id: int, session_id: int, body: AskSpec
) -> ObjectJobSchema | JobResponse:
    """One Q&A ask turn (async)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/ask"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def qa_session_list(self: Any, dashboard_id: int) -> SessionListResponse:
    """List Q&A sessions."""
    path = "/dashboards/{dashboard_id}/qa/sessions"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (SessionListResponse,), allow_untyped=False)


def qa_session_create(self: Any, dashboard_id: int, body: CreateSessionSpec) -> SessionResponse:
    """Create a Q&A session."""
    path = "/dashboards/{dashboard_id}/qa/sessions"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_comment_delete(
    self: Any, dashboard_id: int, session_id: int, comment_id: int
) -> SessionResponse:
    """Delete a comment (author or session owner)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/comments/{comment_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    path = path.replace("{comment_id}", str(comment_id))
    params = None
    response = self._client._request_json("DELETE", path, params=params)
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_session_get(self: Any, dashboard_id: int, session_id: int) -> SessionResponse:
    """Read a Q&A session (replayable — carries baked answers)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_session_delete(self: Any, dashboard_id: int, session_id: int) -> dict[str, Any]:
    """Delete a Q&A session (owner only)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("DELETE", path, params=params)
    return response


def qa_session_fork(self: Any, dashboard_id: int, session_id: int) -> SessionResponse:
    """Fork a shared Q&A session into a private copy."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/fork"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("POST", path, params=params)
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_settings_get(self: Any, dashboard_id: int) -> QaSettingsResponse:
    """This dashboard's Q&A settings."""
    path = "/dashboards/{dashboard_id}/qa/settings"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (QaSettingsResponse,), allow_untyped=False)


def qa_settings_set(self: Any, dashboard_id: int, body: QaSettingsSpec) -> QaSettingsResponse:
    """Update this dashboard's Q&A settings (editors only)."""
    path = "/dashboards/{dashboard_id}/qa/settings"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (QaSettingsResponse,), allow_untyped=False)


def qa_session_rename(
    self: Any, dashboard_id: int, session_id: int, body: RenameSessionSpec
) -> SessionResponse:
    """Rename a Q&A session (owner only)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/title"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_feedback(
    self: Any, dashboard_id: int, session_id: int, message_id: int, body: FeedbackSpec
) -> SessionResponse:
    """Rate an assistant answer (up/down; null clears)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/messages/{message_id}/feedback"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    path = path.replace("{message_id}", str(message_id))
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def qa_session_set_visibility(
    self: Any, dashboard_id: int, session_id: int, body: VisibilitySpec
) -> SessionResponse:
    """Share/unshare a Q&A session (owner only)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/visibility"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (SessionResponse,), allow_untyped=False)


def context_list(self: Any) -> ContextListResponse:
    """The workspace's contexts."""
    path = "/dashboards/v3/contexts"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (ContextListResponse,), allow_untyped=False)


def context_create(self: Any, body: ContextSpec) -> ContextResponse:
    """Create a context."""
    path = "/dashboards/v3/contexts"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ContextResponse,), allow_untyped=False)


def style_custom_list(self: Any) -> StyleListResponse:
    """The workspace's custom styles."""
    path = "/dashboards/v3/styles/custom"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (StyleListResponse,), allow_untyped=False)


def style_custom_create(self: Any, body: CustomStyleSpec) -> StyleResponse:
    """Create a custom style."""
    path = "/dashboards/v3/styles/custom"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (StyleResponse,), allow_untyped=False)


def signature_list(self: Any) -> SignatureListResponse:
    """The workspace's signatures."""
    path = "/dashboards/v3/signatures"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (SignatureListResponse,), allow_untyped=False)


def signature_create(self: Any, body: SignatureSpec) -> SignatureResponse:
    """Create a signature."""
    path = "/dashboards/v3/signatures"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (SignatureResponse,), allow_untyped=False)


def context_update(self: Any, context_id: str, body: ContextSpec) -> ContextResponse:
    """Update a context."""
    path = "/dashboards/v3/contexts/{context_id}"
    path = path.replace("{context_id}", str(context_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (ContextResponse,), allow_untyped=False)


def context_delete(self: Any, context_id: str) -> OkResponse:
    """Delete a context."""
    path = "/dashboards/v3/contexts/{context_id}"
    path = path.replace("{context_id}", str(context_id))
    params = None
    response = self._client._request_json("DELETE", path, params=params)
    return _typed_response(response, (OkResponse,), allow_untyped=False)


def style_custom_update(self: Any, style_id: str, body: CustomStyleSpec) -> StyleResponse:
    """Update a custom style."""
    path = "/dashboards/v3/styles/custom/{style_id}"
    path = path.replace("{style_id}", str(style_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (StyleResponse,), allow_untyped=False)


def style_custom_delete(self: Any, style_id: str) -> OkResponse:
    """Delete a custom style."""
    path = "/dashboards/v3/styles/custom/{style_id}"
    path = path.replace("{style_id}", str(style_id))
    params = None
    response = self._client._request_json("DELETE", path, params=params)
    return _typed_response(response, (OkResponse,), allow_untyped=False)


def signature_update(self: Any, signature_id: str, body: SignatureSpec) -> SignatureResponse:
    """Update a signature."""
    path = "/dashboards/v3/signatures/{signature_id}"
    path = path.replace("{signature_id}", str(signature_id))
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (SignatureResponse,), allow_untyped=False)


def signature_delete(self: Any, signature_id: str) -> OkResponse:
    """Delete a signature."""
    path = "/dashboards/v3/signatures/{signature_id}"
    path = path.replace("{signature_id}", str(signature_id))
    params = None
    response = self._client._request_json("DELETE", path, params=params)
    return _typed_response(response, (OkResponse,), allow_untyped=False)


def template_get(self: Any, template_id: str) -> TemplateDetailResponse:
    """One template's metadata + self-fit recipe."""
    path = "/dashboards/v3/templates/{template_id}"
    path = path.replace("{template_id}", str(template_id))
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (TemplateDetailResponse,), allow_untyped=False)


def template_delete(self: Any, template_id: str) -> OkResponse:
    """Delete a saved workspace template."""
    path = "/dashboards/v3/templates/{template_id}"
    path = path.replace("{template_id}", str(template_id))
    params = None
    response = self._client._request_json("DELETE", path, params=params)
    return _typed_response(response, (OkResponse,), allow_untyped=False)


def template_rename(
    self: Any, template_id: str, body: RenameTemplateSpec
) -> TemplateDetailResponse:
    """Rename a saved workspace template."""
    path = "/dashboards/v3/templates/{template_id}"
    path = path.replace("{template_id}", str(template_id))
    params = None
    response = self._client._request_json("PATCH", path, params=params, json=_json_body(body))
    return _typed_response(response, (TemplateDetailResponse,), allow_untyped=False)


def style_derive(self: Any, body: DeriveStyleSpec) -> dict[str, Any] | DeriveStyleResponse:
    """Derive a full Style bundle from signals."""
    path = "/dashboards/v3/styles/derive"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (DeriveStyleResponse,), allow_untyped=True)


def style_extract_brand(self: Any, body: ExtractBrandSpec) -> ObjectJobSchema | JobResponse:
    """Kick a brand extraction from a URL."""
    path = "/dashboards/v3/styles/extract-brand"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (ObjectJobSchema, JobResponse), allow_untyped=False)


def template_fit(
    self: Any, dataview_id: int, table_item_id: int | None = None
) -> TemplateFitResponse:
    """Fit-score the whole catalog against one dataset."""
    path = "/dashboards/v3/templates/fit"
    params = {
        key: value
        for key, value in {"dataview_id": dataview_id, "table_item_id": table_item_id}.items()
        if value is not None
    }
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (TemplateFitResponse,), allow_untyped=False)


def style_default_get(self: Any) -> DefaultStyleResponse:
    """The workspace default style id."""
    path = "/dashboards/v3/styles/default"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (DefaultStyleResponse,), allow_untyped=False)


def style_default_set(self: Any, body: DefaultStyleSpec) -> DefaultStyleResponse:
    """Set the workspace default style id."""
    path = "/dashboards/v3/styles/default"
    params = None
    response = self._client._request_json("PUT", path, params=params, json=_json_body(body))
    return _typed_response(response, (DefaultStyleResponse,), allow_untyped=False)


def style_token_list(self: Any, id: str) -> StyleTokensResponse:
    """Full Style bundle by id (stock or custom)."""
    path = "/dashboards/v3/styles/tokens"
    params = {key: value for key, value in {"id": id}.items() if value is not None}
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (StyleTokensResponse,), allow_untyped=False)


def style_preset_list(self: Any) -> StylePresetsResponse:
    """Style presets (stock + custom)."""
    path = "/dashboards/v3/styles/presets"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (StylePresetsResponse,), allow_untyped=False)


def template_list(self: Any) -> TemplateListResponse:
    """Curated template catalog."""
    path = "/dashboards/v3/templates"
    params = None
    response = self._client._request_json("GET", path, params=params)
    return _typed_response(response, (TemplateListResponse,), allow_untyped=False)


def template_create(self: Any, body: SaveTemplateSpec) -> TemplateDetailResponse:
    """Save a dashboard as a workspace template."""
    path = "/dashboards/v3/templates"
    params = None
    response = self._client._request_json("POST", path, params=params, json=_json_body(body))
    return _typed_response(response, (TemplateDetailResponse,), allow_untyped=False)


GENERATED_METHODS = [
    "analytics",
    "source_list",
    "data_draft",
    "data_published",
    "rls_column_list",
    "rls_value_list",
    "rls_assignment_list",
    "rls_assignment_set",
    "query",
    "template_apply",
    "chat_history",
    "chat_edit",
    "suggestion_list",
    "descriptor_data",
    "published_data",
    "duplicate",
    "pdf_export",
    "published_pdf_export",
    "video_export",
    "published_video_export",
    "figure_intent",
    "v3_generate",
    "canvas_get",
    "canvas_save",
    "published_canvas",
    "pdf_artifact",
    "published_pdf_artifact",
    "video_state",
    "og_card",
    "published_og_card",
    "page_plan",
    "template_preview",
    "template_resolve_mapping",
    "canvas_restore",
    "published_share_page",
    "published_video_artifact",
    "qa_comment_create",
    "qa_ask",
    "qa_session_list",
    "qa_session_create",
    "qa_comment_delete",
    "qa_session_get",
    "qa_session_delete",
    "qa_session_fork",
    "qa_settings_get",
    "qa_settings_set",
    "qa_session_rename",
    "qa_feedback",
    "qa_session_set_visibility",
    "context_list",
    "context_create",
    "style_custom_list",
    "style_custom_create",
    "signature_list",
    "signature_create",
    "context_update",
    "context_delete",
    "style_custom_update",
    "style_custom_delete",
    "signature_update",
    "signature_delete",
    "template_get",
    "template_delete",
    "template_rename",
    "style_derive",
    "style_extract_brand",
    "template_fit",
    "style_default_get",
    "style_default_set",
    "style_token_list",
    "style_preset_list",
    "template_list",
    "template_create",
]
