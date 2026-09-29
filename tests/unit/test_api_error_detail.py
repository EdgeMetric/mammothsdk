"""The sentence the API sent with a refusal has to survive into the exception.

A caller — the CLI, a script, or an agent relaying to a person — can act on
"Invalid column names found" and can act on nothing at all when it is handed
"HTTP 404". Mammoth carries that sentence in `message`, and sends `detail:
null` beside it on a 404, which is exactly the shape that used to read as "no
detail" and collapse to the status code.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError


class _Refuses(httpx.AsyncBaseTransport):
    """Answer every request with one status and one body."""

    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        self._status_code = status_code
        self._body = body

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(self._status_code, json=self._body, request=request)


def _client(status_code: int, body: dict[str, Any]) -> MammothClient:
    client = MammothClient(api_key="k", api_secret="s", workspace_id=1)
    client.session = httpx.AsyncClient(
        transport=_Refuses(status_code, body),
        headers=client.session.headers,
        follow_redirects=False,
    )
    return client


async def _refusal(status_code: int, body: dict[str, Any]) -> str:
    client = _client(status_code, body)
    try:
        with pytest.raises(MammothAPIError) as refused:
            await client._request_json("GET", "/workspaces/1/projects")
        return str(refused.value)
    finally:
        await client.close()


async def test_a_404_says_what_was_not_found() -> None:
    # Exactly what apiv2's 404 handler sends: the whole exception's __dict__,
    # `detail` included and set to null.
    said = await _refusal(
        404,
        {
            "name": "INVALID_COLUMNS_FOUND",
            "message": "Invalid column names found. Please check the column names provided",
            "details": None,
            "error_code": "4DTVW006",
            "headers": None,
            "extra": None,
            "detail": None,
        },
    )

    assert "Invalid column names found" in said


async def test_a_refusal_that_carries_an_object_of_details_still_speaks() -> None:
    # A business error serialises `detail` as an object beside `message`.
    said = await _refusal(
        400,
        {
            "error_code": "4DTVW001",
            "name": "INVALID_PARAMS",
            "message": "The pipeline step cannot run",
            "detail": {"message": "column_9 does not exist"},
        },
    )

    assert "The pipeline step cannot run" in said


async def test_an_api_that_speaks_only_in_detail_is_still_heard() -> None:
    # Not every server names the field `message`; the older shape still works.
    said = await _refusal(502, {"detail": "gateway failure"})

    assert "gateway failure" in said


async def test_a_refusal_with_nothing_to_say_falls_back_to_the_status() -> None:
    said = await _refusal(500, {"name": "BOOM", "message": "", "detail": None})

    assert "HTTP 500" in said
