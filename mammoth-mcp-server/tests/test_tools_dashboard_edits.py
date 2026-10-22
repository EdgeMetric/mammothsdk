"""Changing a dashboard: Mammoth's AI edits it, or it gets a new title."""

from typing import Any
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

DASHBOARD_ID = 42
DASHBOARD = f"/dashboards/{DASHBOARD_ID}"
CHAT = f"{DASHBOARD}/chat"
JOB = "/jobs/41"
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)

BOARD: dict[str, Any] = {
    "id": DASHBOARD_ID,
    "title": "Sales",
    "url": "abc123",
    "engine": "v3",
    "was_published": False,
}
STARTED = {"job_id": 41}
EDITED = {
    "job": {
        "id": 41,
        "status": "success",
        "response": {
            "message": "I added a Total Revenue card.",
            "changed": True,
            "sequence": 4,
            "canvas": {"pages": [{"id": "p1", "tiles": ["a whole canvas"]}]},
        },
    }
}
NOT_APPLIED = {
    "job": {
        "id": 41,
        "status": "success",
        "response": {"message": "I added a Total Revenue card.", "changed": False},
    }
}


def a_board(api: FakeApi, board: dict[str, Any] = BOARD, job: dict[str, Any] = EDITED) -> None:
    api.answer("GET", DASHBOARD, board)
    api.answer("POST", CHAT, STARTED)
    api.answer("GET", JOB, job)
    api.answer("PATCH", DASHBOARD, {"message": "Dashboard title updated successfully."})


def edit(**arguments: object) -> Any:
    return call_tool(
        "edit_dashboard", workspace_id=WORKSPACE, dashboard_id=DASHBOARD_ID, **arguments
    )


class TestAnAIEdit:
    def test_the_change_is_sent_as_one_chat_turn(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            edit(change="Add a card with total revenue")

        [sent] = api.sent("POST", CHAT)
        assert api.body(sent) == {"params": {"prompt": "Add a card with total revenue"}}

    def test_the_edit_is_waited_for_and_reported(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            answer = edit(change="Add a card with total revenue")

        assert answer["changed"] is True
        assert answer["message"] == "I added a Total Revenue card."
        assert answer["share_url"].endswith("/#/dashboard-v3/abc123")
        # The canvas is the whole board: no model reads it.
        assert "canvas" not in answer
        assert "next_step" not in answer

    def test_an_edit_that_takes_a_while_is_waited_for(self) -> None:
        running = {"job": {"id": 41, "status": "processing", "response": None}}
        with a_fake_api() as api, as_caller():
            a_board(api, job=running)
            api.answer("GET", JOB, EDITED)
            answer = edit(change="Add a card with total revenue")

        assert len(api.sent("GET", JOB)) == 2
        assert answer["changed"] is True

    def test_an_edit_that_changed_nothing_says_it_was_not_applied(self) -> None:
        # The AI's message says what it meant to do, even when nothing landed.
        with a_fake_api() as api, as_caller():
            a_board(api, job=NOT_APPLIED)
            answer = edit(change="Add a card with total revenue")

        assert answer["changed"] is False
        assert "Nothing on the dashboard changed" in answer["next_step"]
        # The AI's message may be an honest "I couldn't": the note blames nobody.
        assert "not what it did" not in answer["next_step"]
        assert "Do not tell the user the change was made" in answer["next_step"]

    def test_a_published_board_is_not_published_again(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, board={**BOARD, "was_published": True})
            answer = edit(change="Add a card with total revenue")

        assert not api.sent("POST", f"{DASHBOARD}/action")
        assert "publish_dashboard" in answer["next_step"]

    def test_an_edit_still_going_says_so(self) -> None:
        running = {"job": {"id": 41, "status": "processing", "response": None}}
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_board(api, job=running)
            answer = edit(change="Add a card with total revenue")

        assert answer["status"] == "editing"
        assert answer["id"] == DASHBOARD_ID
        assert "do not send the change again" in answer["next_step"]

    def test_a_board_on_the_older_engine_is_refused_before_anything_is_sent(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, board={**BOARD, "engine": "v2"})
            with pytest.raises(ToolError, match="older engine"):
                edit(change="Add a card with total revenue")

        assert not api.sent("POST", CHAT)


class TestANewTitle:
    def test_the_title_is_replaced(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            answer = edit(title="Sales by region")

        [sent] = api.sent("PATCH", DASHBOARD)
        assert api.body(sent) == {
            "patch": [{"op": "replace", "path": "title", "value": "Sales by region"}]
        }
        assert not api.sent("POST", CHAT)
        assert answer["id"] == DASHBOARD_ID

    def test_a_board_on_the_older_engine_can_be_renamed(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, board={**BOARD, "engine": "v2"})
            edit(title="Sales by region")

        assert api.sent("PATCH", DASHBOARD)

    def test_a_title_and_a_change_both_land(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            answer = edit(title="Sales by region", change="Add a card with total revenue")

        assert api.sent("PATCH", DASHBOARD)
        assert api.sent("POST", CHAT)
        assert answer["changed"] is True


def test_an_edit_that_names_nothing_to_change_is_refused() -> None:
    with a_fake_api() as api, as_caller():
        a_board(api)
        with pytest.raises(ToolError, match="Say what to change"):
            edit()

    assert not api.requests
