"""Bounded independent S6 SDK transport oracles.

This batch executes the real public dashboard SDK methods against a recording
transport. Expected request literals are authored in the JSON fixture from the
pinned OpenAPI surface; the test does not use command contracts, handler
metadata, SDK introspection, or the SDK method implementation to construct
expectations. It proves only SDK transport shape, not CLI binding.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from mammoth.api.dashboards import DashboardsAPI
from pydantic import ValidationError

FIXTURE = Path(__file__).with_name("fixtures") / "C2-S6-INDEPENDENT-WIRE-001.json"


class RecordingClient:
    """Transport seam that records the request before response validation."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, path, kwargs))
        return {}

    def _request_binary(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        # Artifact routes (PNG/PDF/MP4/HTML) go through the binary seam; the
        # wire oracle only cares about method, path, and query.
        self.calls.append((method, path, kwargs))
        return {"content_type": "application/octet-stream", "size_bytes": 0, "sha256": ""}


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _invoke(client: RecordingClient, route: str) -> None:
    dashboards = DashboardsAPI(client)  # type: ignore[arg-type]
    calls: dict[str, Callable[[], Any]] = {
        "dashboard.cancel-generation": lambda: dashboards.cancel_generation(2001),
        "dashboard.canvas.restore": lambda: dashboards.canvas_restore(
            2002,
            {
                "params": {
                    "target_sequence": 7102,
                    "base_sequence": 7101,
                    "history_index": 4,
                    "activity": "C2_S6_RESTORE",
                }
            },
        ),
        "dashboard.canvas.save": lambda: dashboards.canvas_save(
            2003,
            {
                "params": {
                    "canvas": {"C2_S6": "CANVAS_2003"},
                    "base_sequence": 7103,
                    "activity": "C2_S6_SAVE",
                }
            },
        ),
        "dashboard.chat.edit": lambda: dashboards.chat_edit(
            2004,
            {
                "params": {
                    "prompt": "C2_S6_CHAT_PROMPT_2004",
                    "scope": "dashboard",
                    "selected_fig": "fig-2004",
                    "active_page_id": 204,
                    "target_tile_id": 304,
                    "conversation_history": ["C2_S6_HISTORY_2004"],
                    "client_turn_id": "turn-2004",
                    "change": "C2_S6_CHANGE_2004",
                }
            },
        ),
        "dashboard.chat.history": lambda: dashboards.chat_history(2005, sequence=7105),
        "dashboard.context.create": lambda: dashboards.context_create(
            {
                "params": {
                    "name": "C2_S6_CONTEXT_2006",
                    "type": "dashboard",
                    "files": ["C2_S6_FILE_2006"],
                    "background": "C2_S6_BACKGROUND_2006",
                    "goals": ["C2_S6_GOAL_2006"],
                    "definitions": {"C2_S6_TERM": "C2_S6_VALUE"},
                    "emphasis": ["C2_S6_EMPHASIS"],
                    "guardrails": ["C2_S6_GUARDRAIL"],
                }
            }
        ),
        "dashboard.context.list": lambda: dashboards.context_list(),
        "dashboard.context.update": lambda: dashboards.context_update(
            "C2_S6_CONTEXT_2008",
            {
                "params": {
                    "name": "C2_S6_CONTEXT_UPDATED_2008",
                    "type": "project",
                    "files": ["C2_S6_FILE_2008"],
                    "background": "C2_S6_BACKGROUND_2008",
                    "goals": ["C2_S6_GOAL_2008"],
                    "definitions": {"C2_S6_TERM_2008": "C2_S6_VALUE_2008"},
                    "emphasis": ["C2_S6_EMPHASIS_2008"],
                    "guardrails": ["C2_S6_GUARDRAIL_2008"],
                }
            },
        ),
        "dashboard.data.published": lambda: dashboards.get_publish_data(
            2009, "c2000000-0000-4000-8000-000000002009"
        ),
        "dashboard.delete": lambda: dashboards.delete(2010),
        "dashboard.descriptor-data": lambda: dashboards.descriptor_data(
            2011,
            {
                "params": {
                    "descriptor_ids": [8211, 8212],
                    "filter_state": {"C2_S6_FILTER_2011": "C2_S6_FILTER_VALUE_2011"},
                    "rls_preview_value": "C2_S6_RLS_2011",
                }
            },
        ),
        "dashboard.duplicate": lambda: dashboards.duplicate(2012),
        "dashboard.figure-intent": lambda: dashboards.figure_intent(
            2013,
            {
                "params": {
                    "intent": "C2_S6_FIGURE_INTENT_2013",
                    "kind": "bar",
                    "fields": ["C2_S6_FIELD_2013"],
                }
            },
        ),
        "dashboard.get": lambda: dashboards.get(2014),
        "dashboard.get-by-url": lambda: dashboards.get_by_url("C2_S6_URL_2015"),
        "dashboard.job-by-url": lambda: dashboards.job_by_url("C2_S6_URL_2016", 9216),
        "dashboard.og-card": lambda: dashboards.og_card(2017),
        "dashboard.page.plan": lambda: dashboards.page_plan(
            2018,
            {
                "params": {
                    "intent": "C2_S6_PAGE_INTENT_2018",
                    "archetype": "grid",
                    "kind": "summary",
                    "fields": ["C2_S6_PAGE_FIELD_2018"],
                }
            },
        ),
        "dashboard.pdf-artifact": lambda: dashboards.pdf_artifact(2019, 9219),
        "dashboard.pdf.export": lambda: dashboards.pdf_export(
            2020,
            {
                "params": {
                    "data": {"C2_S6_DATA": "DATA_2020"},
                    "paper": "C2_S6_PAPER_2020",
                    "compare": False,
                }
            },
        ),
        "dashboard.published-data-by-url": lambda: dashboards.published_data_by_url(
            "C2_S6_URL_2021",
            {
                "params": {
                    "widget_id": 9221,
                    "global_filters": {"C2_S6_GLOBAL_2021": "C2_S6_VALUE_2021"},
                    "drilldown_filters": {"C2_S6_DRILL_2021": "C2_S6_VALUE_2021"},
                }
            },
        ),
        "dashboard.published.canvas": lambda: dashboards.published_canvas("C2_S6_URL_2022"),
        "dashboard.published.data": lambda: dashboards.published_data(
            "C2_S6_URL_2023",
            {
                "params": {
                    "descriptor_ids": [9223],
                    "filter_state": {"C2_S6_FILTER_2023": "C2_S6_VALUE_2023"},
                    "rls_preview_value": "C2_S6_RLS_2023",
                }
            },
        ),
        "dashboard.published.og-card": lambda: dashboards.published_og_card("C2_S6_URL_2024"),
        "dashboard.published.pdf-artifact": lambda: dashboards.published_pdf_artifact(
            "C2_S6_URL_2025", 9225
        ),
    }
    try:
        calls[route]()
    except ValidationError:
        # Minimal offline responses are expected to fail response validation;
        # the transport request was already recorded and is the assertion.
        pass


def test_batch_is_exactly_the_first_25_uncovered_s6_routes() -> None:
    fixture = _fixture()
    assert fixture["route_count"] == 25
    assert len(fixture["routes"]) == 25
    assert [route["command_id"] for route in fixture["routes"]] == [
        "dashboard.cancel-generation",
        "dashboard.canvas.restore",
        "dashboard.canvas.save",
        "dashboard.chat.edit",
        "dashboard.chat.history",
        "dashboard.context.create",
        "dashboard.context.list",
        "dashboard.context.update",
        "dashboard.data.published",
        "dashboard.delete",
        "dashboard.descriptor-data",
        "dashboard.duplicate",
        "dashboard.figure-intent",
        "dashboard.get",
        "dashboard.get-by-url",
        "dashboard.job-by-url",
        "dashboard.og-card",
        "dashboard.page.plan",
        "dashboard.pdf-artifact",
        "dashboard.pdf.export",
        "dashboard.published-data-by-url",
        "dashboard.published.canvas",
        "dashboard.published.data",
        "dashboard.published.og-card",
        "dashboard.published.pdf-artifact",
    ]


@pytest.mark.parametrize("case", _fixture()["routes"], ids=lambda case: case["command_id"])
def test_real_sdk_method_matches_pinned_transport_oracle(case: dict[str, Any]) -> None:
    client = RecordingClient()
    _invoke(client, case["command_id"])
    assert len(client.calls) == 1, case["command_id"]
    assert client.calls[0] == (
        case["expected"]["method"],
        case["expected"]["path"],
        case["expected"]["kwargs"],
    )


def test_independent_oracle_rejects_dropped_body_field() -> None:
    case = next(
        route for route in _fixture()["routes"] if route["command_id"] == "dashboard.pdf.export"
    )
    client = RecordingClient()
    _invoke(client, case["command_id"])
    method, path, kwargs = client.calls[0]
    corrupted = dict(kwargs)
    corrupted["json"] = dict(corrupted["json"])
    corrupted["json"]["params"] = dict(corrupted["json"]["params"])
    corrupted["json"]["params"].pop("paper")
    assert (method, path, corrupted) != (
        case["expected"]["method"],
        case["expected"]["path"],
        case["expected"]["kwargs"],
    )
