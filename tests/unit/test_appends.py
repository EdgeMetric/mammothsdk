"""Adding a file to an existing dataset: the SDK's pure rules, on plain data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mammoth.appends import (
    ADDING_MODES,
    EFFECTS,
    UnknownUpdateMethodError,
    describe_append,
    describe_update_method,
    match_batches,
    mode_word,
    rows_of,
    sent_names,
    status_of,
    stored_mode,
    unknown_update_method,
)


def a_plan(mode: str = "add", rows: int | None = 6) -> dict[str, Any]:
    return {
        "target": 315779,
        "update_method": {"mode": mode, "effect": EFFECTS[mode]},
        "mode_changed": False,
        "rows_before": rows,
        "batch_ids_before": [1],
    }


def a_batch(batch_id: int, file_name: str | None = None, **source: Any) -> dict[str, Any]:
    named = {"file_name": file_name} if file_name else {}
    return {"id": batch_id, "name": "", "source": {**named, **source}}


class TestModeWords:
    @pytest.mark.parametrize(
        ("stored", "word"),
        [("combine", "add"), ("replace", "replace"), (None, "add"), ("", "add")],
    )
    def test_a_stored_mode_reads_as_add_or_replace(self, stored: object, word: str) -> None:
        # A dataset with nothing stored adds: that is the platform's default.
        assert mode_word(stored) == word

    @pytest.mark.parametrize("stored", ["merge", "REPLACE", "add", 3, ["replace"]])
    def test_a_stored_mode_that_is_not_known_raises_rather_than_adding(
        self, stored: object
    ) -> None:
        # Guessing "add" for an unknown mode could delete rows through an undo.
        with pytest.raises(UnknownUpdateMethodError):
            mode_word(stored)

    @pytest.mark.parametrize(
        ("word", "stored"),
        [
            ("add", "combine"),
            ("replace", "replace"),
            (" Combine ", "combine"),
            ("append", "combine"),
        ],
    )
    def test_a_callers_word_has_a_stored_name(self, word: str, stored: str) -> None:
        assert stored_mode(word) == stored

    @pytest.mark.parametrize("word", ["merge", "", None, 1])
    def test_a_word_that_is_not_known_is_refused(self, word: object) -> None:
        with pytest.raises(UnknownUpdateMethodError):
            stored_mode(word)

    def test_only_add_is_an_adding_mode(self) -> None:
        assert sorted(ADDING_MODES) == ["add"]

    def test_the_effect_is_said_in_words_with_the_column_mapping(self) -> None:
        said = describe_update_method(
            {"data_addition_mode": "replace", "schema_mapping": {"Amount": ["amt"]}}
        )

        assert said["mode"] == "replace"
        assert "replaces" in said["effect"]
        assert said["schema_mapping"] == {"Amount": ["amt"]}

    def test_a_change_reports_the_mode_it_replaced(self) -> None:
        said = describe_update_method(
            {
                "data_addition_mode": "replace",
                "previous_data_addition_mode": None,
                "schema_settings": {"schema_mapping": None},
            }
        )

        assert (said["mode"], said["previous_mode"], said["changed"]) == ("replace", "add", True)

    def test_an_unknown_stored_mode_is_reported_with_why_not_guessed(self) -> None:
        said = unknown_update_method("not known")

        assert said["mode"] is None
        assert said["error"] == "not known"
        with pytest.raises(UnknownUpdateMethodError):
            describe_update_method({"data_addition_mode": "merge"})


class TestTheBatchesAnUploadAdded:
    def test_a_new_batch_whose_source_names_the_file_is_ours(self) -> None:
        after = [a_batch(1, "old.csv"), a_batch(2, "sales.csv")]

        assert match_batches([1], after, ["sales.csv"]) == ([2], [])

    def test_the_name_matches_without_case_or_extension(self) -> None:
        after = [a_batch(2, None, ds_name="Sales")]

        assert match_batches([], after, ["SALES.csv"]) == ([2], [])

    def test_names_are_compared_by_basename(self) -> None:
        assert match_batches([], [a_batch(2, "/tmp/x/A.CSV")], ["a.csv"]) == ([2], [])

    def test_a_batch_made_from_the_staging_dataset_is_ours(self) -> None:
        assert match_batches([], [a_batch(4, datasource_id=900)], ["a.csv"], [900]) == ([4], [])

    def test_a_batch_that_appeared_meanwhile_is_not_claimed(self) -> None:
        # A folder automation or another user: removing it would delete rows
        # nobody here added.
        after = [a_batch(2, "sales.csv"), a_batch(3, "other.csv"), a_batch(5), a_batch(6)]

        assert match_batches([1], after, ["sales.csv"], [900]) == ([2], [3, 5, 6])

    def test_a_batch_that_was_already_there_is_never_new(self) -> None:
        assert match_batches([2], [a_batch(2, "sales.csv")], ["sales.csv"]) == ([], [])

    def test_a_row_without_an_id_is_skipped(self) -> None:
        assert match_batches([], [{"source": {"file_name": "sales.csv"}}], ["sales.csv"]) == (
            [],
            [],
        )

    def test_sent_names_take_the_basename_of_paths(self) -> None:
        assert sent_names(["dir/a.csv", Path("b.csv")]) == ["a.csv", "b.csv"]


class TestWhatAnAppendReports:
    def test_an_add_reports_the_rows_added_and_the_batch(self) -> None:
        report = describe_append(a_plan("add", rows=6), 9, [7], [], settled=True)

        assert report["appended_to"] == 315779
        assert (report["rows_before"], report["rows_after"], report["rows_added"]) == (6, 9, 3)
        assert report["batch_ids"] == [7]
        assert report["update_method"]["mode"] == "add"
        assert "append_pending" not in report

    def test_a_replace_that_shrank_the_dataset_adds_a_negative_number(self) -> None:
        report = describe_append(a_plan("replace", rows=6), 2, [7], [], settled=True)

        assert report["rows_added"] == -4

    def test_batches_not_tied_to_the_upload_are_listed_apart(self) -> None:
        report = describe_append(a_plan("add"), 9, [], [8], settled=True)

        assert report["batch_ids"] == []
        assert report["unmatched_batch_ids"] == [8]

    def test_rows_still_landing_are_reported_as_pending(self) -> None:
        report = describe_append(a_plan("add"), 6, [7], [], settled=False)

        assert report["append_pending"] is True

    def test_rows_that_could_not_be_read_are_left_out_rather_than_guessed(self) -> None:
        report = describe_append(a_plan("add", rows=None), None, [7], [], settled=True)

        assert "rows_added" not in report

    def test_the_reported_update_method_is_a_copy_of_the_plans(self) -> None:
        plan = a_plan("add")
        report = describe_append(plan, 9, [], [], settled=True)
        report["update_method"]["mode"] = "replace"

        assert plan["update_method"]["mode"] == "add"


class TestReadingADatasetAnswer:
    def test_rows_and_status_come_from_the_dataset_under_its_key(self) -> None:
        read = {"dataset": {"status": "ready", "stats": {"row_count": 6}}}

        assert rows_of(read) == 6
        assert status_of(read) == "ready"

    def test_a_dataset_without_counts_reads_as_none(self) -> None:
        assert rows_of({"dataset": {}}) is None
        assert status_of({"dataset": {}}) is None
        assert rows_of(None) is None
