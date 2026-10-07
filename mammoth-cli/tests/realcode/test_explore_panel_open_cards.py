"""``view explore-panel set`` writes the cards the web app reads (``{height, cards}``).

Real-code: the genuine CLI, service and SDK client, with only the HTTP socket faked by a small
in-memory view that stores the panel a PATCH writes and serves it, with the view's columns, on GET.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.testing import make_runner
from tests.conftest import FakeApi, RecordedRequest
from tests.realcode.test_end_to_end_cli import _bind_real_service

ServiceFactory = Callable[..., Any]
PROJECT, DATASET, VIEW = 180, 9, 7
COLUMNS = [
    {"display_name": "Region", "internal_name": "column_1", "type": "TEXT"},
    {"display_name": "Amount", "internal_name": "column_2", "type": "NUMERIC"},
]


def _mount(api: FakeApi) -> list[dict[str, Any]]:
    saved: dict[str, Any] = {}
    written: list[dict[str, Any]] = []

    def patch(request: RecordedRequest) -> tuple[int, Any]:
        panel = request.json_body["patch"][0]["value"]
        saved.clear()
        saved.update(panel)
        written.append(panel)
        return 200, {"status": "ok"}

    def get(_request: RecordedRequest) -> tuple[int, Any]:
        properties = {"EXPLORE_PANEL": saved} if saved else {}
        return 200, {"id": VIEW, "metadata": COLUMNS, "user_display_properties": properties}

    api.on("GET", rf"/resources/dataview/{VIEW}$", body={"resource": {"dataset": {"id": DATASET}}})
    api.on("PATCH", rf"/datasets/{DATASET}/dataviews/{VIEW}$", handler=patch)
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", handler=get)
    return written


def _set(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path, panel: Any
) -> tuple[int, dict[str, Any], list[dict[str, Any]]]:
    api = _bind_real_service(monkeypatch, real_service, project_id=PROJECT)
    written = _mount(api)
    document = tmp_path / "panel.json"
    document.write_text(json.dumps({"panel": panel}), encoding="utf-8")
    result = make_runner().invoke(
        ["view", "explore-panel", "set", str(VIEW), "--input", str(document), "--output", "json"]
        + ["--project", str(PROJECT), "--no-input"]
    )
    return result.exit_code, json.loads(result.output), written


def test_columns_all_opens_a_card_per_column_in_the_shape_the_web_app_reads(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    code, envelope, written = _set(monkeypatch, real_service, tmp_path, {"columns": "all"})

    assert code == 0, envelope
    [panel] = written
    assert [card["colId"] for card in panel["cards"]] == ["column_1", "column_2"]
    assert [card["renderType"] for card in panel["cards"]] == ["list", "chart"]
    assert [card["colId"] for card in envelope["data"]["panel"]["cards"]] == [
        "column_1",
        "column_2",
    ]


def test_the_old_open_items_panel_is_refused_and_nothing_is_written(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    code, envelope, written = _set(
        monkeypatch, real_service, tmp_path, {"open": True, "items": [{"column": "column_1"}]}
    )

    assert code != 0
    assert "No cards yet" in envelope["error"]["message"]
    assert written == []
