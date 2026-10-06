"""``SdkMammothService.call_many``: independent reads that wait together, not in turn.

The real service and SDK client run; only the HTTP socket is faked, and it answers
after a pause so that waiting in turn and waiting together differ by a wide margin.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.sdk_service import SdkMammothService
from tests.conftest import FakeApi

ServiceFactory = Callable[..., Any]
_PAUSE = 0.2
_VIEW = "mammoth.api.dataviews.DataviewsAPI.get"


class _SlowApi(FakeApi):
    """A fake API whose every answer takes ``_PAUSE`` seconds."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(_PAUSE)
        return await super().handle_async_request(request)


def _service(real_service: ServiceFactory) -> tuple[SdkMammothService, FakeApi]:
    return real_service(project_id=180, api=_SlowApi())


def _read(view_id: int) -> tuple[str, dict[str, Any]]:
    return _VIEW, {"dataset_id": 9, "dataview_id": view_id, "project_id": 180}


def test_call_many_waits_for_all_reads_together(real_service: ServiceFactory) -> None:
    service, api = _service(real_service)
    for view_id in range(1, 7):
        api.on("GET", rf"/dataviews/{view_id}$", body={"id": view_id})

    started = time.monotonic()
    results = service.call_many([_read(view_id) for view_id in range(1, 7)])
    elapsed = time.monotonic() - started

    assert [r["id"] for r in results] == [1, 2, 3, 4, 5, 6]
    assert elapsed < _PAUSE * 6 * 0.6, f"six reads took {elapsed:.2f}s: they ran in turn"


def test_call_many_returns_a_failed_read_as_the_error_call_raises(
    real_service: ServiceFactory,
) -> None:
    service, api = _service(real_service)
    api.on("GET", r"/dataviews/1$", body={"id": 1})
    api.on("GET", r"/dataviews/2$", status=404, body={"message": "no such view"})

    results = service.call_many([_read(1), _read(2), ("mammoth.api.nope.Nothing.at_all", {})])

    assert results[0] == {"id": 1}
    assert isinstance(results[1], CliError) and isinstance(results[2], CliError)
    with pytest.raises(CliError) as raised:
        service.call(*_read(2)[:1], **_read(2)[1])
    assert results[1].code == raised.value.code
    assert results[2].code == "sdk_symbol_unresolved"


def test_call_many_of_nothing_is_empty(real_service: ServiceFactory) -> None:
    service, _api = _service(real_service)

    assert service.call_many([]) == []
