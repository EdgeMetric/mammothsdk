"""Real-code test that ``view draft status`` reads server-backed draft state.

Finding #6 was that draft status returned the rich ``View``'s process-local
``is_draft_mode`` flag, which a freshly resolved view always reports as
``False`` regardless of the server. The command now dispatches to
``PipelineAPI.get_draft_status``, which reads the live pipeline. This exercises
that whole path with only the HTTP socket faked and asserts the reported state
follows the server, not a local default.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.services.dispatch import resolve_sdk_method

PROJECT_ID = 180
DATASET_ID = 55
VIEW_ID = 1039
DRAFT_STATUS_SYMBOL = "mammoth.api.pipeline.PipelineAPI.get_draft_status"

ServiceFactory = Callable[..., Any]


def _wire_resolution(api: Any) -> None:
    """Register the browse + dataview probes the view resolution performs."""
    api.on(
        "GET",
        r"/browse",
        body={
            "resources": [
                {"id": PROJECT_ID, "children": [{"type": "datasource", "id": DATASET_ID}]}
            ]
        },
    )
    api.on("GET", rf"/datasets/{DATASET_ID}/dataviews/{VIEW_ID}$", body={"id": VIEW_ID})


def test_draft_status_reports_server_state(real_service: ServiceFactory) -> None:
    """A server pipeline flagged in draft is reported as draft."""
    service, api = real_service(project_id=PROJECT_ID)
    _wire_resolution(api)
    api.on("GET", r"/pipeline$", body={"state": "ready", "in_draft_mode": True})

    result = service.call(DRAFT_STATUS_SYMBOL, dataview_id=VIEW_ID)

    assert result["is_draft"] is True
    assert result["dataview_id"] == VIEW_ID
    assert any(r.path.endswith("/pipeline") for r in api.requests)


def test_draft_status_reports_not_draft(real_service: ServiceFactory) -> None:
    """A server pipeline not in draft is reported as not draft."""
    service, api = real_service(project_id=PROJECT_ID)
    _wire_resolution(api)
    api.on("GET", r"/pipeline$", body={"state": "ready"})

    result = service.call(DRAFT_STATUS_SYMBOL, dataview_id=VIEW_ID)

    assert result["is_draft"] is False


def test_draft_status_symbol_resolves_to_pipeline_api(real_service: ServiceFactory) -> None:
    """The manifest symbol resolves to the real server-backed pipeline method."""
    service, _ = real_service(project_id=PROJECT_ID)
    method = resolve_sdk_method(service._client, DRAFT_STATUS_SYMBOL)
    assert method.__name__ == "get_draft_status"
