"""Generated public dashboard API wrappers. Do not edit by hand."""

from __future__ import annotations

from typing import Any


def analytics(self: Any, dashboard_id: int) -> Any:
    """Get Dashboard Analytics."""
    path = "/dashboards/{dashboard_id}/analytics"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def source_list(self: Any) -> Any:
    """Get Dashboard Sources."""
    path = "/dashboards/sources"
    params = None
    return self._client._request_json("GET", path, params=params)


def data_draft(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Get draft data from given SQL query."""
    path = "/dashboards/{dashboard_id}/getDraftData"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def data_published(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Get published data from given SQL query."""
    path = "/dashboards/{dashboard_id}/getPublishData"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def rls_column_list(self: Any, dashboard_id: int) -> Any:
    """Candidate columns for the RLS filter."""
    path = "/dashboards/{dashboard_id}/rls/columns"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def rls_value_list(self: Any, dashboard_id: int, column: str, search: str | None = None) -> Any:
    """Distinct values for an RLS filter column."""
    path = "/dashboards/{dashboard_id}/rls/values"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = {
        key: value
        for key, value in {"column": column, "search": search}.items()
        if value is not None
    }
    return self._client._request_json("GET", path, params=params)


def rls_assignment_list(self: Any, dashboard_id: int) -> Any:
    """List RLS viewer assignments."""
    path = "/dashboards/{dashboard_id}/rls/assignments"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def rls_assignment_set(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Replace RLS viewer assignments."""
    path = "/dashboards/{dashboard_id}/rls/assignments"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def query(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Editor ad-hoc descriptor query."""
    path = "/dashboards/{dashboard_id}/query"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def template_apply(self: Any, body: dict[str, Any]) -> Any:
    """Apply a template to a target dataset."""
    path = "/dashboards/v3/templates/apply"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def chat_history(self: Any, dashboard_id: int, sequence: int | None = None) -> Any:
    """Editor chat transcript."""
    path = "/dashboards/{dashboard_id}/chat"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = {key: value for key, value in {"sequence": sequence}.items() if value is not None}
    return self._client._request_json("GET", path, params=params)


def chat_edit(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """One chat-edit turn."""
    path = "/dashboards/{dashboard_id}/chat"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def suggestion_list(self: Any, dataview_id: int, table_item_id: int | None = None) -> Any:
    """Data-grounded starting points for the create screen."""
    path = "/dashboards/v3/suggestions"
    params = {
        key: value
        for key, value in {"dataview_id": dataview_id, "table_item_id": table_item_id}.items()
        if value is not None
    }
    return self._client._request_json("GET", path, params=params)


def descriptor_data(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Descriptor data — future-request."""
    path = "/dashboards/{dashboard_id}/data"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def published_data(self: Any, url: str, body: dict[str, Any]) -> Any:
    """Descriptor data for a published dashboard."""
    path = "/dashboards/url/{url}/data"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def duplicate(self: Any, dashboard_id: int) -> Any:
    """Duplicate a v3 dashboard."""
    path = "/dashboards/v3/{dashboard_id}/duplicate"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params)


def pdf_export(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Kick a draft-dashboard PDF export."""
    path = "/dashboards/{dashboard_id}/pdf"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def published_pdf_export(self: Any, url: str, body: dict[str, Any]) -> Any:
    """Kick a published-dashboard PDF export."""
    path = "/dashboards/url/{url}/pdf"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def video_export(self: Any, dashboard_id: int) -> Any:
    """Kick a motion-story video export."""
    path = "/dashboards/{dashboard_id}/video"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params)


def published_video_export(self: Any, url: str) -> Any:
    """Kick a motion-story video export (published view)."""
    path = "/dashboards/url/{url}/video"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("POST", path, params=params)


def figure_intent(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Resolve an AI-add figure from an intent."""
    path = "/dashboards/{dashboard_id}/figure-intent"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def v3_generate(self: Any, body: dict[str, Any]) -> Any:
    """Generate a v3 dashboard."""
    path = "/dashboards/v3/generate"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def canvas_get(self: Any, dashboard_id: int, sequence: int | None = None) -> Any:
    """Editor canvas (draft)."""
    path = "/dashboards/{dashboard_id}/canvas"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = {key: value for key, value in {"sequence": sequence}.items() if value is not None}
    return self._client._request_json("GET", path, params=params)


def canvas_save(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Save the canvas (append a draft version)."""
    path = "/dashboards/{dashboard_id}/canvas"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def published_canvas(self: Any, url: str) -> Any:
    """Published viewer canvas."""
    path = "/dashboards/url/{url}/canvas"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("GET", path, params=params)


def pdf_artifact(self: Any, dashboard_id: int, job_id: int) -> Any:
    """Download a completed draft PDF export."""
    path = "/dashboards/{dashboard_id}/pdf/{job_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{job_id}", str(job_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def published_pdf_artifact(self: Any, url: str, job_id: int) -> Any:
    """Download a completed published PDF export."""
    path = "/dashboards/url/{url}/pdf/{job_id}"
    path = path.replace("{url}", str(url))
    path = path.replace("{job_id}", str(job_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def video_state(self: Any, dashboard_id: int) -> Any:
    """Motion-story video export state (never kicks a render)."""
    path = "/dashboards/{dashboard_id}/video-state"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def og_card(self: Any, dashboard_id: int) -> Any:
    """Dashboard card thumbnail (draft or published PNG)."""
    path = "/dashboards/{dashboard_id}/og-card"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def published_og_card(self: Any, url: str) -> Any:
    """Published dashboard's link-unfurl OG card (baked PNG)."""
    path = "/dashboards/url/{url}/og-card"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("GET", path, params=params)


def page_plan(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Compose a new page from an intent."""
    path = "/dashboards/{dashboard_id}/plan-page"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def template_preview(self: Any, body: dict[str, Any]) -> Any:
    """Preview a template mapping applied to a target dataset."""
    path = "/dashboards/v3/templates/preview"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def template_resolve_mapping(self: Any, body: dict[str, Any]) -> Any:
    """Propose a template mapping onto a target dataset."""
    path = "/dashboards/v3/templates/resolve-mapping"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def canvas_restore(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Undo / redo / revert the canvas to a target version."""
    path = "/dashboards/{dashboard_id}/canvas/restore"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def published_share_page(self: Any, url: str) -> Any:
    """Published dashboard's link-unfurl share page (crawler-facing HTML)."""
    path = "/dashboards/url/{url}/share"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("GET", path, params=params)


def published_video_artifact(self: Any, url: str) -> Any:
    """Stream a published motion-story video (Range-enabled)."""
    path = "/dashboards/url/{url}/video.mp4"
    path = path.replace("{url}", str(url))
    params = None
    return self._client._request_json("GET", path, params=params)


def qa_comment_create(self: Any, dashboard_id: int, session_id: int, body: dict[str, Any]) -> Any:
    """Comment on a shared Q&A session."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/comments"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def qa_ask(self: Any, dashboard_id: int, session_id: int, body: dict[str, Any]) -> Any:
    """One Q&A ask turn (async)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/ask"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def qa_session_list(self: Any, dashboard_id: int) -> Any:
    """List Q&A sessions."""
    path = "/dashboards/{dashboard_id}/qa/sessions"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def qa_session_create(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Create a Q&A session."""
    path = "/dashboards/{dashboard_id}/qa/sessions"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def qa_comment_delete(self: Any, dashboard_id: int, session_id: int, comment_id: int) -> Any:
    """Delete a comment (author or session owner)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/comments/{comment_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    path = path.replace("{comment_id}", str(comment_id))
    params = None
    return self._client._request_json("DELETE", path, params=params)


def qa_session_get(self: Any, dashboard_id: int, session_id: int) -> Any:
    """Read a Q&A session (replayable — carries baked answers)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def qa_session_delete(self: Any, dashboard_id: int, session_id: int) -> Any:
    """Delete a Q&A session (owner only)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("DELETE", path, params=params)


def qa_session_fork(self: Any, dashboard_id: int, session_id: int) -> Any:
    """Fork a shared Q&A session into a private copy."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/fork"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("POST", path, params=params)


def qa_settings_get(self: Any, dashboard_id: int) -> Any:
    """This dashboard's Q&A settings."""
    path = "/dashboards/{dashboard_id}/qa/settings"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def qa_settings_set(self: Any, dashboard_id: int, body: dict[str, Any]) -> Any:
    """Update this dashboard's Q&A settings (editors only)."""
    path = "/dashboards/{dashboard_id}/qa/settings"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def qa_session_rename(self: Any, dashboard_id: int, session_id: int, body: dict[str, Any]) -> Any:
    """Rename a Q&A session (owner only)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/title"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def qa_feedback(
    self: Any, dashboard_id: int, session_id: int, message_id: int, body: dict[str, Any]
) -> Any:
    """Rate an assistant answer (up/down; null clears)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/messages/{message_id}/feedback"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    path = path.replace("{message_id}", str(message_id))
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def qa_session_set_visibility(
    self: Any, dashboard_id: int, session_id: int, body: dict[str, Any]
) -> Any:
    """Share/unshare a Q&A session (owner only)."""
    path = "/dashboards/{dashboard_id}/qa/sessions/{session_id}/visibility"
    path = path.replace("{dashboard_id}", str(dashboard_id))
    path = path.replace("{session_id}", str(session_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def context_list(self: Any) -> Any:
    """The workspace's contexts."""
    path = "/dashboards/v3/contexts"
    params = None
    return self._client._request_json("GET", path, params=params)


def context_create(self: Any, body: dict[str, Any]) -> Any:
    """Create a context."""
    path = "/dashboards/v3/contexts"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def style_custom_list(self: Any) -> Any:
    """The workspace's custom styles."""
    path = "/dashboards/v3/styles/custom"
    params = None
    return self._client._request_json("GET", path, params=params)


def style_custom_create(self: Any, body: dict[str, Any]) -> Any:
    """Create a custom style."""
    path = "/dashboards/v3/styles/custom"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def signature_list(self: Any) -> Any:
    """The workspace's signatures."""
    path = "/dashboards/v3/signatures"
    params = None
    return self._client._request_json("GET", path, params=params)


def signature_create(self: Any, body: dict[str, Any]) -> Any:
    """Create a signature."""
    path = "/dashboards/v3/signatures"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def context_update(self: Any, context_id: str, body: dict[str, Any]) -> Any:
    """Update a context."""
    path = "/dashboards/v3/contexts/{context_id}"
    path = path.replace("{context_id}", str(context_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def context_delete(self: Any, context_id: str) -> Any:
    """Delete a context."""
    path = "/dashboards/v3/contexts/{context_id}"
    path = path.replace("{context_id}", str(context_id))
    params = None
    return self._client._request_json("DELETE", path, params=params)


def style_custom_update(self: Any, style_id: str, body: dict[str, Any]) -> Any:
    """Update a custom style."""
    path = "/dashboards/v3/styles/custom/{style_id}"
    path = path.replace("{style_id}", str(style_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def style_custom_delete(self: Any, style_id: str) -> Any:
    """Delete a custom style."""
    path = "/dashboards/v3/styles/custom/{style_id}"
    path = path.replace("{style_id}", str(style_id))
    params = None
    return self._client._request_json("DELETE", path, params=params)


def signature_update(self: Any, signature_id: str, body: dict[str, Any]) -> Any:
    """Update a signature."""
    path = "/dashboards/v3/signatures/{signature_id}"
    path = path.replace("{signature_id}", str(signature_id))
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def signature_delete(self: Any, signature_id: str) -> Any:
    """Delete a signature."""
    path = "/dashboards/v3/signatures/{signature_id}"
    path = path.replace("{signature_id}", str(signature_id))
    params = None
    return self._client._request_json("DELETE", path, params=params)


def template_get(self: Any, template_id: str) -> Any:
    """One template's metadata + self-fit recipe."""
    path = "/dashboards/v3/templates/{template_id}"
    path = path.replace("{template_id}", str(template_id))
    params = None
    return self._client._request_json("GET", path, params=params)


def template_delete(self: Any, template_id: str) -> Any:
    """Delete a saved workspace template."""
    path = "/dashboards/v3/templates/{template_id}"
    path = path.replace("{template_id}", str(template_id))
    params = None
    return self._client._request_json("DELETE", path, params=params)


def template_rename(self: Any, template_id: str, body: dict[str, Any]) -> Any:
    """Rename a saved workspace template."""
    path = "/dashboards/v3/templates/{template_id}"
    path = path.replace("{template_id}", str(template_id))
    params = None
    return self._client._request_json("PATCH", path, params=params, json=body)


def style_derive(self: Any, body: dict[str, Any]) -> Any:
    """Derive a full Style bundle from signals."""
    path = "/dashboards/v3/styles/derive"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def style_extract_brand(self: Any, body: dict[str, Any]) -> Any:
    """Kick a brand extraction from a URL."""
    path = "/dashboards/v3/styles/extract-brand"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


def template_fit(self: Any, dataview_id: int, table_item_id: int | None = None) -> Any:
    """Fit-score the whole catalog against one dataset."""
    path = "/dashboards/v3/templates/fit"
    params = {
        key: value
        for key, value in {"dataview_id": dataview_id, "table_item_id": table_item_id}.items()
        if value is not None
    }
    return self._client._request_json("GET", path, params=params)


def style_default_get(self: Any) -> Any:
    """The workspace default style id."""
    path = "/dashboards/v3/styles/default"
    params = None
    return self._client._request_json("GET", path, params=params)


def style_default_set(self: Any, body: dict[str, Any]) -> Any:
    """Set the workspace default style id."""
    path = "/dashboards/v3/styles/default"
    params = None
    return self._client._request_json("PUT", path, params=params, json=body)


def style_token_list(self: Any, id: str) -> Any:
    """Full Style bundle by id (stock or custom)."""
    path = "/dashboards/v3/styles/tokens"
    params = {key: value for key, value in {"id": id}.items() if value is not None}
    return self._client._request_json("GET", path, params=params)


def style_preset_list(self: Any) -> Any:
    """Style presets (stock + custom)."""
    path = "/dashboards/v3/styles/presets"
    params = None
    return self._client._request_json("GET", path, params=params)


def template_list(self: Any) -> Any:
    """Curated template catalog."""
    path = "/dashboards/v3/templates"
    params = None
    return self._client._request_json("GET", path, params=params)


def template_create(self: Any, body: dict[str, Any]) -> Any:
    """Save a dashboard as a workspace template."""
    path = "/dashboards/v3/templates"
    params = None
    return self._client._request_json("POST", path, params=params, json=body)


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
