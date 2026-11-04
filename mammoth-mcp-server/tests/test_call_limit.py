"""A tool call answers before CloudFront cuts it off."""

import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from mcp_types import CallToolResult, TextContent

from mammoth_mcp_server.call_limit import CallLimit, outcome_unknown
from mammoth_mcp_server.consts import CALL_HARD_STOP_SECONDS, ROUTE_TIMEOUT_SECONDS
from mammoth_mcp_server.read_only import ReadOnly
from mammoth_mcp_server.server import mcp_server
from mammoth_mcp_server.telemetry import Telemetry

from .helpers import run

SOON = 0.05
ANSWER = "answered"


def a_request(method: str = "tools/call") -> Any:
    """A request for the middleware, naming a tool."""
    return SimpleNamespace(method=method, params={"name": "add_export"})


async def slow(_ctx: Any) -> str:
    """A handler that outlasts the stop."""
    await asyncio.sleep(5)
    return ANSWER


async def quick(_ctx: Any) -> str:
    """A handler that answers at once."""
    return ANSWER


def test_a_quick_call_comes_back_untouched() -> None:
    assert run(CallLimit()(a_request(), quick)) == ANSWER


def test_a_call_that_runs_too_long_says_its_outcome_is_unknown() -> None:
    with patch("mammoth_mcp_server.call_limit.CALL_HARD_STOP_SECONDS", SOON):
        result = run(CallLimit()(a_request(), slow))

    assert isinstance(result, CallToolResult)
    assert result.is_error
    text = result.content[0]
    assert isinstance(text, TextContent)
    assert "add_export" in text.text
    assert "outcome is unknown" in text.text


def test_a_stopped_call_is_recorded_as_failed() -> None:
    # The stop sits outside Telemetry so the event sees the cut, not a tidy error result.
    assert [type(one) for one in mcp_server._lowlevel_server.middleware[-3:]] == [
        CallLimit,
        Telemetry,
        ReadOnly,
    ]


def test_other_requests_are_not_timed() -> None:
    async def lists() -> Any:
        return await CallLimit()(a_request("tools/list"), quick)

    with patch("mammoth_mcp_server.call_limit.CALL_HARD_STOP_SECONDS", 0):
        assert run(lists()) == ANSWER


def test_the_stop_comes_before_a_slow_request_and_the_edge() -> None:
    assert CALL_HARD_STOP_SECONDS < 30 < ROUTE_TIMEOUT_SECONDS


def test_the_answer_is_a_tool_result_rather_than_a_protocol_error() -> None:
    assert isinstance(outcome_unknown("undo"), CallToolResult)
