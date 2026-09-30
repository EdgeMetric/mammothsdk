"""The project methods of the real service return the SDK's data, not a coroutine."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.sdk_service import SdkMammothService

PROJECTS = {"projects": [{"id": 7, "name": "Sales"}], "next": ""}


def _service(real_service: Any) -> tuple[SdkMammothService, Any]:
    service, api = real_service()
    api.on("GET", r"/workspaces/4/projects$", body=PROJECTS)
    api.on("POST", r"/workspaces/4/projects$", body={"id": 8, "name": "New"})
    return service, api


def test_check_connection_reads_the_project_list(real_service: Any) -> None:
    service, api = _service(real_service)
    assert service.check_connection() == PROJECTS
    assert api.last().method == "GET"


def test_list_projects_returns_the_page(real_service: Any) -> None:
    service, _ = _service(real_service)
    assert service.list_projects(limit=10)["projects"] == PROJECTS["projects"]


def test_list_projects_past_one_page_walks_the_listing(real_service: Any) -> None:
    service, _ = _service(real_service)
    assert service.list_projects(limit=500)["projects"] == PROJECTS["projects"]


def test_list_all_projects_returns_every_project(real_service: Any) -> None:
    service, _ = _service(real_service)
    assert service.list_all_projects() == PROJECTS["projects"]


def test_get_project_returns_the_project(real_service: Any) -> None:
    service, _ = _service(real_service)
    assert service.get_project(7)["id"] == 7


def test_create_project_sends_the_create(real_service: Any) -> None:
    service, api = _service(real_service)
    assert service.create_project("New") == {"id": 8, "name": "New"}
    assert (api.last().method, api.last().json_body["name"]) == ("POST", "New")
