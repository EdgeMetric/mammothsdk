"""`check_upload` holds the call while the user is still picking a file.

Answering `waiting` at once ends the model's turn, and a turn that has ended
needs the user to start another one — which is why a user who had already said
"upload this and build me a dashboard" was left pressing enter to say the file
was in. Waiting here keeps the upload inside the turn they already asked for.
"""

import asyncio
import time
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server import model_watch
from mammoth_mcp_server.consts import (
    BUILD_WAIT_SECONDS,
    CONNECT_WAIT_SECONDS,
    TOOL_CALL_SECONDS,
    UPLOAD_WAIT_SECONDS,
    UPLOAD_WATCH_SECONDS,
    ConnectionFields,
    ModelWatchFields,
    UploadFields,
)
from mammoth_mcp_server.deadline import seconds_left
from mammoth_mcp_server.model_watch import model_is_polling, model_state, model_was_told
from mammoth_mcp_server.tools import files
from mammoth_mcp_server.tools.files import check_upload, wait_for_the_file
from mammoth_mcp_server.upload_tickets import mint_ticket, read_ticket, spend_ticket

from .helpers import GOOD_TOKEN, WORKSPACE, FakeRedis, a_fake_store, as_caller, run

PROJECT, JOB = 3, 31


def a_ticket() -> str:
    from mcp.server.auth.middleware.auth_context import get_access_token

    with as_caller(token=GOOD_TOKEN):
        caller = get_access_token()
        assert caller is not None
        return run(mint_ticket(caller, WORKSPACE, PROJECT))


@pytest.fixture(autouse=True)
def store() -> FakeRedis:
    with a_fake_store() as fake:
        yield fake


@pytest.fixture(autouse=True)
def brief_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the tests quick; the behaviour under test is the waiting itself."""
    monkeypatch.setattr(files, "UPLOAD_WAIT_SECONDS", 0.3)
    monkeypatch.setattr(files, "UPLOAD_POLL_SECONDS", 0.02)


async def arrives(ticket_id: str, after: float) -> None:
    """The user picks their file while the tool call is still waiting."""
    await asyncio.sleep(after)
    held = await read_ticket(ticket_id)
    assert held is not None
    await spend_ticket(ticket_id, held, JOB, ["sales.csv"], uploaded_at="now")


# What CloudFront allows between bytes (`OriginReadTimeout` on mcp.mammoth.io).
EDGE_READ_SECONDS = 30.0


@pytest.mark.parametrize(
    "seconds",
    [
        TOOL_CALL_SECONDS,
        UPLOAD_WAIT_SECONDS,
        BUILD_WAIT_SECONDS,
        CONNECT_WAIT_SECONDS,
        ConnectionFields.PREVIEW_SECONDS,
    ],
)
def test_no_silent_wait_reaches_the_edge_limit(seconds: float) -> None:
    """A wait as long as the edge's limit comes back to the user as a dead server."""
    assert seconds < EDGE_READ_SECONDS


class TestWaitingForTheUser:
    def test_the_hold_spends_from_the_call_deadline(self) -> None:
        """The job wait after the hold gets what is left, not a clock of its own."""
        ticket = a_ticket()

        async def hold_then_ask() -> float:
            await wait_for_the_file(ticket)
            return seconds_left()

        with patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.2):
            left = run(hold_then_ask())

        assert left < 0.1

    def test_the_file_arriving_ends_the_wait(self) -> None:
        ticket = a_ticket()

        async def wait_while_it_arrives() -> dict[str, object]:
            asyncio.ensure_future(arrives(ticket, after=0.05))
            return await wait_for_the_file(ticket)

        held = run(wait_while_it_arrives())

        assert held[UploadFields.JOB_ID] == JOB

    def test_it_does_not_answer_before_the_file_arrives(self) -> None:
        ticket = a_ticket()

        async def still_waiting_after(seconds: float) -> bool:
            waiting = asyncio.ensure_future(wait_for_the_file(ticket))
            await asyncio.sleep(seconds)
            unfinished = not waiting.done()
            waiting.cancel()
            return unfinished

        assert run(still_waiting_after(0.08)), "it answered without waiting"

    def test_it_gives_up_rather_than_hanging(self) -> None:
        # The user may never come back. The wait is bounded, and the model is
        # told to say so rather than sit silent.
        ticket = a_ticket()

        held = run(wait_for_the_file(ticket))

        assert held.get(UploadFields.JOB_ID) is None

    def test_the_tool_reports_waiting_when_the_user_never_came_back(self) -> None:
        ticket = a_ticket()

        with as_caller(token=GOOD_TOKEN):
            answer = run(check_upload(ticket))

        assert answer[UploadFields.STATUS] == UploadFields.WAITING

    def test_a_link_that_was_never_minted_is_refused_at_once(self) -> None:
        with as_caller(token=GOOD_TOKEN), pytest.raises(ToolError):
            run(check_upload("never-minted"))


class TestTheModelKeepsItsTurn:
    """A widget cannot start a turn, so the model polls until the file is in."""

    def test_waiting_says_to_call_again(self) -> None:
        report = run(check_upload(a_ticket()))

        assert report["status"] == "waiting"
        assert report["next_step"] == files.KEEP_WAITING

    def test_the_polling_stops_after_the_watch(self) -> None:
        ticket = a_ticket()
        late = time.time() + UPLOAD_WATCH_SECONDS + 1

        with patch.object(files.time, "time", return_value=late):
            report = run(check_upload(ticket))

        assert report["status"] == "waiting"
        assert report["next_step"] == files.STOP_WAITING
        assert run(model_state(ticket)) == ModelWatchFields.GONE

    def test_the_uploader_sees_a_model_that_is_still_polling(self) -> None:
        ticket = a_ticket()
        run(check_upload(ticket))

        report = run(check_upload(ticket, from_widget=True))

        assert report[ModelWatchFields.MODEL] == ModelWatchFields.WATCHING

    def test_the_uploader_alone_leaves_no_model_behind(self) -> None:
        report = run(check_upload(a_ticket(), from_widget=True))

        assert report[ModelWatchFields.MODEL] == ModelWatchFields.GONE

    def test_a_model_that_has_not_polled_for_a_while_counts_as_gone(self) -> None:
        ticket = a_ticket()
        run(model_is_polling(ticket))
        later = time.time() + ModelWatchFields.GAP_SECONDS + 1

        with patch.object(model_watch.time, "time", return_value=later):
            assert run(model_state(ticket)) == ModelWatchFields.GONE

    def test_a_model_that_has_the_result_is_told(self) -> None:
        ticket = a_ticket()
        run(model_was_told(ticket))

        assert run(model_state(ticket)) == ModelWatchFields.TOLD

    def test_a_poll_leaves_the_ticket_alone(self, store: FakeRedis) -> None:
        """A write back could undo the upload that spent the ticket mid-poll."""
        ticket = a_ticket()
        before = run(read_ticket(ticket))

        run(check_upload(ticket))

        assert run(read_ticket(ticket)) == before
