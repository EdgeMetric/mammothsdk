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
        # The edit's own report is in its job: a later call can pick it up.
        assert answer["job_id"] == 41
        assert "job_id=41" in answer["next_step"]
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


# A two-part ask, as prague answered it: the chart was replaced, so `changed`
# is true, but the count it was asked for did not land. Mammoth's job reports
# each ask's status and what it could not do as fields.
COUNT_ASK = "count customers in each month, not add up a number column"
PARTLY: dict[str, Any] = {
    "asks": [
        {"ask": COUNT_ASK, "status": "not on the board — no chart was added"},
        {"ask": "order the months by calendar", "status": "applied"},
    ],
}


def edited(changed: bool = True, **response: Any) -> dict[str, Any]:
    return {
        "job": {
            "id": 41,
            "status": "success",
            "response": {"message": "Rebuilt the chart.", "changed": changed, **response},
        }
    }


class TestAnEditThatOnlyPartlyLanded:
    def test_an_ask_mammoth_says_did_not_land_is_named(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, job=edited(**PARTLY))
            answer = edit(change="Count customers per month, in calendar order")

        assert answer["changed"] is True
        assert answer["partial"] is True
        assert answer["not_done"] == [f"{COUNT_ASK}: not on the board — no chart was added"]
        assert "not_done" in answer["next_step"]

    def test_what_mammoth_could_not_do_is_named(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, job=edited(could_not_do=["a revenue chart", "a map by planet"]))
            answer = edit(change="Add a customers card, a revenue chart and a map")

        assert answer["not_done"] == ["a revenue chart", "a map by planet"]
        assert answer["partial"] is True

    def test_an_edit_whose_asks_all_landed_is_not_partial(self) -> None:
        asks = [
            {"ask": "add a card", "status": "applied"},
            {"ask": "sort by month", "status": "applied"},
        ]
        with a_fake_api() as api, as_caller():
            a_board(api, job=edited(asks=asks, could_not_do=[]))
            answer = edit(change="Add a card and sort by month")

        assert "partial" not in answer
        assert "not_done" not in answer
        assert "next_step" not in answer

    def test_an_edit_that_changed_nothing_is_not_partial(self) -> None:
        # Nothing landed, so the note is "nothing changed", not "part of it".
        with a_fake_api() as api, as_caller():
            a_board(api, job=edited(changed=False, **PARTLY))
            answer = edit(change="Count customers per month, in calendar order")

        assert "partial" not in answer
        assert "Nothing on the dashboard changed" in answer["next_step"]

    def test_the_reply_text_is_not_read_for_what_missed(self) -> None:
        # The fields are Mammoth's check; the prose is the AI's, whatever it lists.
        message = "Done:\n- Revenue by region — not attempted\n_Couldn’t do: a map._"
        with a_fake_api() as api, as_caller():
            a_board(api, job=edited(message=message))
            answer = edit(change="Add revenue by region")

        assert "partial" not in answer
        assert "not_done" not in answer


class TestPickingUpAnEditThatOutlastedTheCall:
    def test_the_job_is_waited_for_again_and_reported(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, job=edited(**PARTLY))
            answer = edit(job_id=41)

        # Nothing new is sent to the dashboard's chat.
        assert not api.sent("POST", CHAT)
        assert api.sent("GET", JOB)
        assert answer["changed"] is True
        assert answer["partial"] is True
        assert answer["id"] == DASHBOARD_ID

    @pytest.mark.parametrize(
        "more",
        [{"change": "Add a card"}, {"title": "Sales"}, {"any_site": True}, {"tags": ["sales"]}],
    )
    def test_a_job_id_with_anything_new_is_refused(self, more: dict[str, Any]) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            with pytest.raises(ToolError, match="job_id"):
                edit(job_id=41, **more)

        assert not api.requests


class TestTags:
    def test_a_dashboards_tags_are_replaced_at_once(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, board={**BOARD, "was_published": True})
            api.answer("PUT", f"{DASHBOARD}/tags", {"tags": ["sales", "weekly"]})
            answer = edit(tags=["sales", "weekly"])

        [sent] = api.sent("PUT", f"{DASHBOARD}/tags")
        assert api.body(sent)["tags"] == ["sales", "weekly"]
        assert answer["tags"] == ["sales", "weekly"]
        # Tags are not part of the draft: there is nothing to publish again.
        assert "next_step" not in answer
        assert not api.sent("POST", CHAT)

    def test_an_empty_list_clears_them(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            api.answer("PUT", f"{DASHBOARD}/tags", {"tags": []})
            edit(tags=[])

        [sent] = api.sent("PUT", f"{DASHBOARD}/tags")
        assert api.body(sent)["tags"] == []

    def test_the_workspaces_tags_come_with_the_dashboards_when_asked_for(self) -> None:
        listed = {"tags": [{"id": 1, "name": "sales", "count": 2}]}
        with a_fake_api() as api, as_caller():
            api.answer("GET", "/dashboards", {"dashboards": [BOARD]})
            api.answer("GET", "/dashboards/tags", listed)
            answer = call_tool("list_dashboards", workspace_id=WORKSPACE, include_tags=True)
            plain = call_tool("list_dashboards", workspace_id=WORKSPACE)

        assert answer["tags"] == listed["tags"]
        assert "tags" not in plain
        assert len(api.sent("GET", "/dashboards/tags")) == 1


class TestAChangeThatFailsPartWay:
    def test_too_many_sites_are_refused_before_anything_is_sent(self) -> None:
        sites = [f"https://site{n}.example.com" for n in range(21)]
        with a_fake_api() as api, as_caller():
            a_board(api)
            with pytest.raises(ToolError, match="20"):
                edit(title="Q3", allowed_sites=sites)

        assert not api.requests

    def test_what_changed_before_a_refusal_is_named(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", CHAT, {"message": "The AI dashboard allowance is used up"}, 403)
            api.answer("PUT", f"{DASHBOARD}/tags", {"tags": ["sales"]})
            a_board(api)
            with pytest.raises(ToolError, match="allowance") as refused:
                edit(title="Q3", tags=["sales"], change="Add a card")

        assert api.sent("PATCH", DASHBOARD)
        assert "title" in str(refused.value)
        assert "tags" in str(refused.value)

    def test_a_refusal_before_any_change_names_none(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("PATCH", DASHBOARD, {"message": "Title is too long"}, 400)
            a_board(api)
            with pytest.raises(ToolError) as refused:
                edit(title="Q3")

        assert "already" not in str(refused.value)


def test_a_change_off_the_draft_reads_the_board_once() -> None:
    with a_fake_api() as api, as_caller():
        api.answer("PUT", f"{DASHBOARD}/tags", {"tags": ["sales"]})
        a_board(api)
        answer = edit(tags=["sales"])

    assert len(api.sent("GET", DASHBOARD)) == 1
    assert answer["tags"] == ["sales"]
    assert answer["id"] == DASHBOARD_ID
