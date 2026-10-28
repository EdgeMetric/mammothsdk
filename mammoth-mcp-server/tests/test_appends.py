"""Adding a file to an existing dataset: the rules that decide what is reported and offered.

These run on plain data. What the API does with the mode, the file and the
batch is for a live run (see the cases listed in the change notes).
"""

import pytest

from mammoth_mcp_server.appends import (
    NOTHING_TO_REMOVE,
    UNDO_WITH,
    describe_append,
    describe_update_method,
    find_new_batches,
    rows_of,
    status_of,
    word_of,
)
from mammoth_mcp_server.consts import AppendFields


def a_plan(mode: str = "add", rows: int | None = 6, changed: bool = False) -> dict:
    return {
        AppendFields.TARGET: 315779,
        AppendFields.UPDATE_METHOD: mode,
        AppendFields.MODE_CHANGED: changed,
        AppendFields.PREVIOUS_MODE: "add" if mode == "replace" else "replace",
        AppendFields.ROWS_BEFORE: rows,
        AppendFields.BATCH_IDS_BEFORE: [1],
    }


def a_batch(batch_id: int, file_name: str | None = None, **source: object) -> dict:
    return {"id": batch_id, "source": {"file_name": file_name, **source}}


class TestTheUpdateMethodIsReadAsTheCallerWordsIt:
    @pytest.mark.parametrize(
        ("stored", "word"),
        [("combine", "add"), ("replace", "replace"), (None, "add"), ("", "add")],
    )
    def test_a_stored_mode_reads_as_add_or_replace(self, stored: object, word: str) -> None:
        # A dataset with nothing stored adds: that is the platform's default.
        assert word_of(stored) == word

    def test_the_effect_is_said_in_words_with_the_column_mapping(self) -> None:
        said = describe_update_method(
            {"data_addition_mode": "replace", "schema_mapping": {"Amount": ["amt"]}}
        )

        assert said["mode"] == "replace"
        assert "replaces" in said["effect"]
        assert said["schema_mapping"] == {"Amount": ["amt"]}


class TestTheBatchesAnUploadAdded:
    def test_a_new_batch_whose_source_names_the_file_is_ours(self) -> None:
        after = [a_batch(1, "old.csv"), a_batch(2, "sales.csv")]

        assert find_new_batches([1], after, ["sales.csv"]) == ([2], [])

    def test_the_name_matches_without_case_or_extension(self) -> None:
        after = [a_batch(2, None, ds_name="Sales")]

        assert find_new_batches([], after, ["SALES.csv"]) == ([2], [])

    def test_a_batch_that_appeared_meanwhile_is_not_offered_for_removal(self) -> None:
        # A folder automation or another user: removing it would delete rows
        # nobody here added.
        after = [a_batch(2, "sales.csv"), a_batch(3, "other.csv")]

        assert find_new_batches([1], after, ["sales.csv"]) == ([2], [3])

    def test_a_batch_that_was_already_there_is_never_new(self) -> None:
        assert find_new_batches([2], [a_batch(2, "sales.csv")], ["sales.csv"]) == ([], [])

    def test_a_row_without_an_id_is_skipped(self) -> None:
        assert find_new_batches([], [{"source": {"file_name": "sales.csv"}}], ["sales.csv"]) == (
            [],
            [],
        )


class TestWhatAnAppendReports:
    def test_an_add_reports_the_rows_added_and_the_batch_to_remove(self) -> None:
        report = describe_append(a_plan("add", rows=6), 9, [7], [], settled=True)

        assert report[AppendFields.APPENDED_TO] == 315779
        assert report[AppendFields.ROWS_ADDED] == 3
        assert report[AppendFields.BATCH_ID] == 7
        assert report[AppendFields.BATCH_IDS] == [7]
        assert report[AppendFields.NEXT_STEP] == UNDO_WITH

    def test_a_replace_never_offers_a_batch_to_remove(self) -> None:
        # The old rows are gone, so removing a batch would undo nothing.
        report = describe_append(a_plan("replace", rows=6), 2, [7], [], settled=True)

        assert report[AppendFields.ROWS_ADDED] == -4
        assert AppendFields.BATCH_IDS not in report
        assert AppendFields.BATCH_ID not in report
        assert report[AppendFields.NEXT_STEP] == NOTHING_TO_REMOVE

    def test_an_add_that_made_no_batch_we_can_name_offers_nothing(self) -> None:
        report = describe_append(a_plan("add"), 9, [], [8], settled=True)

        assert report[AppendFields.BATCH_IDS] == []
        assert AppendFields.NEXT_STEP not in report
        assert report[AppendFields.UNMATCHED_BATCH_IDS] == [8]
        assert "not to be removed" in report[AppendFields.NOTES][0]

    def test_rows_still_landing_are_reported_as_pending(self) -> None:
        report = describe_append(a_plan("add"), 6, [7], [], settled=False)

        assert report[AppendFields.APPEND_PENDING] is True

    def test_a_mode_this_upload_changed_is_said_to_stay(self) -> None:
        report = describe_append(a_plan("replace", changed=True), 2, [], [], settled=True)

        assert "stays" in report[AppendFields.NOTES][0]

    def test_rows_that_could_not_be_read_are_left_out_rather_than_guessed(self) -> None:
        report = describe_append(a_plan("add", rows=None), None, [7], [], settled=True)

        assert AppendFields.ROWS_ADDED not in report


class TestReadingADatasetAnswer:
    def test_rows_and_status_come_from_the_dataset_under_its_key(self) -> None:
        read = {"dataset": {"status": "ready", "stats": {"row_count": 6}}}

        assert rows_of(read) == 6
        assert status_of(read) == "ready"

    def test_a_dataset_without_counts_reads_as_none(self) -> None:
        assert rows_of({"dataset": {}}) is None
        assert status_of({"dataset": {}}) is None
