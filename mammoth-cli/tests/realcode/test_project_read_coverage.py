"""`project get` and `resource-status` say what they cover, so empty is not "no resources"."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.testing import make_runner
from tests.realcode.test_end_to_end_cli import _bind_real_service

ServiceFactory = Callable[..., Any]


def _data(*argv: str) -> dict[str, Any]:
    import json

    result = make_runner().invoke([*argv, "--project", "41", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"]


def test_resource_status_with_nothing_in_flight_says_in_flight(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service, project_id=41)
    api.on("GET", r"/projects/41/resource-status$", body={"status": {}})

    data = _data("project", "resource-status")

    assert data["in_flight"] == {}
    assert "covers" in data


def test_resource_status_keeps_the_tasks_it_found_under_in_flight(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service, project_id=41)
    api.on("GET", r"/projects/41/resource-status$", body={"status": {"view_7": "running"}})

    assert _data("project", "resource-status")["in_flight"] == {"view_7": "running"}


def test_project_get_names_what_it_does_not_cover(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service, project_id=41)
    api.on("GET", r"/workspaces/4/projects$", body={"projects": [{"id": 41, "name": "Gifts"}]})

    data = _data("project", "get", "41")

    assert (data["id"], data["name"]) == (41, "Gifts")
    assert "datasets" in data["covers"]
