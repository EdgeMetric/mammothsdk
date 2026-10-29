"""A join or a lookup reports how well it matched, so a poor match is not taken for success."""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.join_check import count_unmatched, join_check, measure
from mammoth_mcp_server.sdk import build_client

from .helpers import WORKSPACE, a_fake_api, as_caller, run

PROJECT, DATASET, VIEW = 3, 5, 9
VIEW_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"
QUERY = f"{VIEW_PATH}/data/query"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "dataview_id": VIEW}
ORDERS = [{"display_name": "Region", "internal_name": "column_1", "type": "TEXT"}]
MANAGER = {"display_name": "Manager", "internal_name": "column_2", "type": "TEXT"}
BUDGET = {"display_name": "Budget", "internal_name": "column_3", "type": "NUMERIC"}


def a_view(rows: int, *added: dict[str, Any]) -> dict[str, Any]:
    return {"id": VIEW, "row_count": rows, "metadata": [*ORDERS, *added]}


class TestTheCheck:
    def test_a_left_join_reports_its_match_rate_over_the_whole_view(self) -> None:
        check = join_check(a_view(40), a_view(40, MANAGER, BUDGET), unmatched=1)

        assert check["rows_before"] == 40
        assert check["rows_after"] == 40
        assert check["columns_added"] == ["Manager", "Budget"]
        assert check["unmatched_rows"] == 1
        assert check["match_rate"] == 0.975
        assert check["notes"] == [
            "1 of 40 rows found no match: every column the step brought in is empty."
            " If that is more than a few, compare the key columns of both views (type,"
            " case, spaces) before building on this, or tell the user."
        ]

    def test_a_full_match_has_no_notes(self) -> None:
        check = join_check(a_view(40), a_view(40, MANAGER), unmatched=0)

        assert check["match_rate"] == 1.0
        assert "notes" not in check

    def test_more_rows_after_the_join_says_a_key_repeats(self) -> None:
        check = join_check(a_view(40), a_view(43, MANAGER), unmatched=0)

        [note] = check["notes"]
        assert note.startswith("The join added 3 rows: a key repeats")

    def test_fewer_rows_after_the_join_says_rows_were_dropped(self) -> None:
        check = join_check(a_view(40), a_view(31, MANAGER), unmatched=0)

        [note] = check["notes"]
        assert note.startswith("9 rows found no match and were dropped")

    def test_a_lookup_into_an_existing_column_cannot_count_matches(self) -> None:
        check = join_check(a_view(40), a_view(40), unmatched=None)

        assert check["columns_added"] == []
        assert "match_rate" not in check
        assert "unmatched_rows" not in check
        assert "added no column" in check["notes"][0]

    def test_an_empty_view_has_no_match_rate(self) -> None:
        check = join_check(a_view(0), a_view(0, MANAGER), unmatched=0)

        assert "match_rate" not in check


class TestMeasuringTheView:
    def test_the_rows_with_every_added_column_empty_are_counted_by_mammoth(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEW_PATH, a_view(40, MANAGER, BUDGET))
            api.answer("POST", QUERY, {"data": [{"agg_0": 4}]})
            check = run(measure(IDS, a_view(40)))

        (sent,) = api.sent("POST", QUERY)
        assert api.body(sent)["param"]["CONDITION"] == {
            "AND": [{"column_2": {"IS_EMPTY": True}}, {"column_3": {"IS_EMPTY": True}}]
        }
        assert check["unmatched_rows"] == 4
        assert check["match_rate"] == 0.9

    def test_a_step_that_adds_no_column_sends_no_count(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEW_PATH, a_view(40))
            check = run(measure(IDS, a_view(40)))

        assert api.sent("POST", QUERY) == []
        assert "match_rate" not in check

    @pytest.mark.parametrize(
        "answer",
        [{}, {"data": []}, {"data": [{}]}, {"data": [{"agg_0": ""}]}, {"data": [{"agg_0": "abc"}]}],
    )
    def test_an_answer_with_no_count_is_not_read_as_zero(self, answer: dict[str, Any]) -> None:
        async def count() -> int:
            async with build_client(WORKSPACE, PROJECT) as client:
                return await count_unmatched(client, IDS, ["column_2"])

        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="no count"):
            api.answer("POST", QUERY, answer)
            run(count())

    def test_a_join_that_could_not_be_counted_is_not_reported_as_a_full_match(self) -> None:
        # The step is in: an error here would read as a failed add, and a retry adds it twice.
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEW_PATH, a_view(40, MANAGER))
            api.answer("POST", QUERY, {"data": []})
            check = run(measure(IDS, a_view(40)))

        assert "match_rate" not in check
        assert "unmatched_rows" not in check
        [note] = check["notes"]
        assert "could not count" in note
        assert "get_data" in note
