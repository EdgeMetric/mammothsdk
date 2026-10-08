"""`check_upload` holds the call while the user is still picking a file.

Answering `waiting` at once ends the model's turn, and a turn that has ended
needs the user to start another one — which is why a user who had already said
"upload this and build me a dashboard" was left pressing enter to say the file
was in. Waiting here keeps the upload inside the turn they already asked for.
"""

import asyncio

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import UploadFields
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


class TestWaitingForTheUser:
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
