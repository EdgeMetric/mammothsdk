"""The real service answers a caller that is already inside a running event loop."""

from __future__ import annotations

import asyncio
from typing import Any

PROJECTS = {"projects": [{"id": 7, "name": "Sales"}], "next": ""}


def test_a_call_from_inside_a_running_loop_returns_the_data(real_service: Any) -> None:
    service, api = real_service()
    api.on("GET", r"/workspaces/4/projects$", body=PROJECTS)

    async def async_caller() -> Any:
        return service.list_all_projects()

    assert asyncio.run(async_caller()) == PROJECTS["projects"]


def test_a_call_after_an_in_loop_call_still_uses_the_same_service(real_service: Any) -> None:
    service, api = real_service()
    api.on("GET", r"/workspaces/4/projects$", body=PROJECTS)

    async def async_caller() -> Any:
        return service.list_all_projects()

    asyncio.run(async_caller())
    assert service.list_all_projects() == PROJECTS["projects"]
