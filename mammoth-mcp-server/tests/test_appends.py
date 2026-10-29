"""What an append tells a model, and when a batch may be removed: rules on plain data.

The mode words, the matching of an upload's batches and the report itself are the SDK's and
are tested there (tests/unit/test_appends.py). What the API does with the mode, the file and
the batch is for a live run.
"""

from typing import Any

from mammoth.appends import NO_RECORD, NOT_ADDED, WOULD_EMPTY, refuse_batch_removal

from mammoth_mcp_server.appends import (
    NOTHING_TO_REMOVE,
    UNDO_WITH,
    batch_mode_key,
    present_append,
)
from mammoth_mcp_server.consts import AppendFields


def a_report(mode: str | None = "add", **fields: Any) -> dict[str, Any]:
    method: dict[str, Any] = {"mode": mode, "effect": "words"}
    if mode is None:
        method["error"] = "could not be read"
    return {
        "appended_to": 315779,
        "update_method": method,
        "rows_before": 6,
        "rows_after": 9,
        "rows_added": 3,
        "batch_ids": [7],
        **fields,
    }


class TestWhatAnAppendTellsTheModel:
    def test_an_add_offers_the_batch_to_remove(self) -> None:
        shown = present_append(a_report("add"))

        assert shown[AppendFields.BATCH_ID] == 7
        assert shown[AppendFields.BATCH_IDS] == [7]
        assert shown[AppendFields.NEXT_STEP] == UNDO_WITH

    def test_a_replace_never_offers_a_batch_to_remove(self) -> None:
        # The old rows are gone, so removing a batch would undo nothing.
        shown = present_append(a_report("replace", rows_added=-4))

        assert AppendFields.BATCH_IDS not in shown
        assert AppendFields.BATCH_ID not in shown
        assert shown[AppendFields.NEXT_STEP] == NOTHING_TO_REMOVE

    def test_a_mode_that_could_not_be_read_offers_nothing_and_says_why(self) -> None:
        shown = present_append(a_report(None))

        assert AppendFields.BATCH_IDS not in shown
        assert AppendFields.NEXT_STEP not in shown
        assert "could not be read" in shown[AppendFields.NOTES][0]

    def test_an_add_that_made_no_batch_we_can_name_offers_nothing(self) -> None:
        shown = present_append(a_report("add", batch_ids=[], unmatched_batch_ids=[8]))

        assert shown[AppendFields.BATCH_IDS] == []
        assert AppendFields.NEXT_STEP not in shown
        assert "not to be removed" in shown[AppendFields.NOTES][0]

    def test_rows_still_landing_are_said_to_be_pending(self) -> None:
        shown = present_append(a_report("add", append_pending=True))

        assert "check_upload" in shown[AppendFields.NOTES][0]

    def test_a_mode_this_upload_changed_is_said_to_stay(self) -> None:
        report = a_report("replace")
        report["update_method"]["previous_mode"] = "add"

        assert "stays" in present_append(report)[AppendFields.NOTES][0]

    def test_batches_that_could_not_be_read_are_said_not_guessed(self) -> None:
        report = a_report("add", batches_error="refused")
        del report["batch_ids"]

        shown = present_append(report)

        assert shown[AppendFields.BATCH_IDS] == []
        assert "refused" in shown[AppendFields.NOTES][0]

    def test_the_report_it_was_given_is_left_alone(self) -> None:
        report = a_report("replace")

        present_append(report)

        assert report["batch_ids"] == [7]


class TestWhenABatchMayBeRemoved:
    def test_a_batch_recorded_as_added_may_go(self) -> None:
        assert refuse_batch_removal([7], {7: "add"}, [3, 7]) is None

    def test_a_batch_with_no_record_is_refused(self) -> None:
        assert refuse_batch_removal([7], {}, [3, 7]) == NO_RECORD.format(7)
        assert refuse_batch_removal([7], {7: None}, [3, 7]) == NO_RECORD.format(7)

    def test_a_batch_added_under_replace_is_refused_whatever_the_dataset_does_now(self) -> None:
        # The dataset may have been switched to "add" since: the batch's rows are still all it
        # has. Only what was recorded at upload time counts.
        assert refuse_batch_removal([7], {7: "replace"}, [3, 7]) == NOT_ADDED.format(7, "replace")

    def test_a_mode_that_is_not_known_to_add_is_refused(self) -> None:
        assert refuse_batch_removal([7], {7: "merge"}, [3, 7]) == NOT_ADDED.format(7, "merge")

    def test_one_unrecorded_batch_among_recorded_ones_refuses_all(self) -> None:
        assert refuse_batch_removal([6, 7], {6: "add"}, [3, 6, 7]) == NO_RECORD.format(7)

    def test_removing_every_batch_the_dataset_has_is_refused(self) -> None:
        assert refuse_batch_removal([6, 7], {6: "add", 7: "add"}, [7, 6]) == WOULD_EMPTY.format(
            [6, 7]
        )

    def test_removing_the_only_batch_is_refused(self) -> None:
        assert refuse_batch_removal([7], {7: "add"}, [7]) == WOULD_EMPTY.format([7])

    def test_a_dataset_whose_batches_could_not_be_listed_is_not_emptied(self) -> None:
        # No listing is no evidence of other batches: a delete is refused rather than risked.
        assert refuse_batch_removal([7], {7: "add"}, []) == WOULD_EMPTY.format([7])


def test_a_batch_record_is_kept_per_workspace_dataset_and_batch() -> None:
    assert batch_mode_key(1, 2, 3) == "1:2:3"
    assert batch_mode_key(1, 2, 3) != batch_mode_key(1, 23, 0)
