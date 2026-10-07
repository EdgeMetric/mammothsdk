"""``view explore-panel set`` returns the panel the backend saved, read back after the write.

Real-code: the real CLI, service and SDK client, with only the HTTP socket faked by a small
in-memory view that stores the panel a PATCH writes and serves it on the next GET.
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
PANEL = {
    "open": True,
    "items": [{"column": "column_1", "renderType": "chart"}, {"column": "column_2"}],
}


def _mount_view(api: FakeApi) -> list[dict[str, Any]]:
    """Serve one view whose saved panel starts empty; return the panels PATCHed onto it."""
    saved: dict[str, Any] = {}
    written: list[dict[str, Any]] = []

    def patch(request: RecordedRequest) -> tuple[int, Any]:
        panel = request.json_body["patch"][0]["value"]
        saved.update(panel)
        written.append(panel)
        return 200, {"status": "ok"}

    def get(_request: RecordedRequest) -> tuple[int, Any]:
        properties = {"EXPLORE_PANEL": saved} if saved else {}
        return 200, {"id": VIEW, "user_display_properties": properties}

    api.on("GET", rf"/resources/dataview/{VIEW}$", body={"resource": {"dataset": {"id": DATASET}}})
    api.on("PATCH", rf"/datasets/{DATASET}/dataviews/{VIEW}$", handler=patch)
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", handler=get)
    return written


def test_set_result_carries_the_panel_read_back_after_the_write(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    api = _bind_real_service(monkeypatch, real_service, project_id=PROJECT)
    written = _mount_view(api)
    document = tmp_path / "panel.json"
    document.write_text(json.dumps({"panel": PANEL}), encoding="utf-8")

    result = make_runner().invoke(
        ["view", "explore-panel", "set", str(VIEW), "--input", str(document), "--output", "json"]
        + ["--project", str(PROJECT), "--no-input"]
    )

    assert result.exit_code == 0, result.output
    assert written == [PANEL]
    assert json.loads(result.output)["data"]["panel"] == PANEL
    methods = [request.method for request in api.requests]
    assert methods.index("PATCH") < len(methods) - 1 - methods[::-1].index("GET")
