"""What the server records about a call, so the launch can be measured.

Nothing here records what the call was about: no ids, no arguments, no rows,
no token. The questions these events answer are which tools get used, from
which client, how long they take and how often they fail.
"""

import json
import logging

import pytest

from mammoth_mcp_server.telemetry import EVENT_LOGGER, Events, Telemetry, TelemetryFields


class Recorded:
    """The events the telemetry middleware emitted during a test."""

    def __init__(self, caplog: pytest.LogCaptureFixture) -> None:
        self.caplog = caplog

    def __iter__(self):
        for record in self.caplog.records:
            if record.name == EVENT_LOGGER:
                yield json.loads(record.getMessage())

    def of(self, event: str) -> list[dict]:
        return [one for one in self if one[TelemetryFields.EVENT] == event]


@pytest.fixture
def recorded(caplog: pytest.LogCaptureFixture) -> Recorded:
    caplog.set_level(logging.INFO, logger=EVENT_LOGGER)
    return Recorded(caplog)


def a_context(method: str, params: dict | None = None) -> object:
    """Enough of a request context for the middleware to read."""

    class Ctx:
        pass

    ctx = Ctx()
    ctx.method = method
    ctx.params = params
    ctx.session = None
    return ctx


async def answers(_ctx: object) -> str:
    return "done"


async def raises(_ctx: object) -> str:
    raise ValueError("the tool broke")


class TestWhatIsRecordedForAToolCall:
    async def test_a_tool_call_is_recorded_with_the_tool_it_called(
        self, recorded: Recorded
    ) -> None:
        await Telemetry()(a_context("tools/call", {"name": "get_data"}), answers)

        [called] = recorded.of(Events.TOOL_CALLED)
        assert called[TelemetryFields.TOOL] == "get_data"

    async def test_a_call_that_worked_is_recorded_as_ok(self, recorded: Recorded) -> None:
        await Telemetry()(a_context("tools/call", {"name": "get_data"}), answers)

        [called] = recorded.of(Events.TOOL_CALLED)
        assert called[TelemetryFields.OUTCOME] == Events.OK

    async def test_a_call_that_failed_is_recorded_as_failed_and_still_raises(
        self, recorded: Recorded
    ) -> None:
        """Telemetry must never swallow the error it is measuring."""
        with pytest.raises(ValueError):
            await Telemetry()(a_context("tools/call", {"name": "get_data"}), raises)

        [called] = recorded.of(Events.TOOL_CALLED)
        assert called[TelemetryFields.OUTCOME] == Events.FAILED
        assert called[TelemetryFields.ERROR] == "ValueError"

    async def test_how_long_the_call_took_is_recorded(self, recorded: Recorded) -> None:
        await Telemetry()(a_context("tools/call", {"name": "get_data"}), answers)

        [called] = recorded.of(Events.TOOL_CALLED)
        assert called[TelemetryFields.DURATION_MS] >= 0

    async def test_the_answer_reaches_the_caller_unchanged(self) -> None:
        assert await Telemetry()(a_context("tools/call", {"name": "x"}), answers) == "done"


class TestWhatIsRecordedForAHandshake:
    async def test_a_handshake_is_recorded_with_the_client_that_connected(
        self, recorded: Recorded
    ) -> None:
        connects = a_context(
            "initialize", {"clientInfo": {"name": "claude-ai", "version": "1.2.3"}}
        )

        await Telemetry()(connects, answers)

        [started] = recorded.of(Events.INITIALIZE)
        assert started[TelemetryFields.CLIENT] == "claude-ai"
        assert started[TelemetryFields.CLIENT_VERSION] == "1.2.3"

    async def test_a_client_that_names_itself_in_no_way_is_still_recorded(
        self, recorded: Recorded
    ) -> None:
        await Telemetry()(a_context("initialize", {}), answers)

        assert recorded.of(Events.INITIALIZE)


class TestWhatIsNeverRecorded:
    async def test_the_arguments_a_tool_was_called_with_are_not_recorded(
        self, recorded: Recorded
    ) -> None:
        """Arguments carry the user's own data — column names, filter values,
        file names. The event says which tool ran, never what it ran on."""
        secret = "a-customers-column-name"
        called = a_context("tools/call", {"name": "get_data", "arguments": {"columns": [secret]}})

        await Telemetry()(called, answers)

        assert secret not in json.dumps(list(recorded))

    async def test_another_method_is_not_recorded_as_a_tool_call(self, recorded: Recorded) -> None:
        await Telemetry()(a_context("tools/list"), answers)

        assert recorded.of(Events.TOOL_CALLED) == []


class TestTheServerRecordsItsOwnCalls:
    def test_the_running_server_has_telemetry_on_it(self) -> None:
        """A middleware that is written but never registered records nothing."""
        from mammoth_mcp_server.server import mcp_server

        assert any(isinstance(one, Telemetry) for one in mcp_server.middleware)
