"""Reading what an upload made, and what each item waits on, off the resources.

These drive the pure part of `upload_report` on items shaped like the resources
API's: when an upload counts as over, which items are its own, and what the
model is told to do about each action Mammoth can wait on. The round trip
through a real upload is in `test_upload_handoff.py`.
"""

from datetime import UTC, datetime

import pytest

from mammoth_mcp_server.consts import (
    DatasetStatus,
    FileStatus,
    InterpretationFields,
    ResourceTypes,
    UploadFields,
    UploadReportFields,
    UserActions,
)
from mammoth_mcp_server.upload_report import (
    ASK_FIRST,
    CARRY_ON,
    IN_MAMMOTH,
    NEXT_STEP,
    READ_IT_DIFFERENTLY,
    STOPPED,
    UNREADABLE_ROWS,
    find_made_since,
    read_time,
    summarize,
)

TICKET = {UploadFields.WORKSPACE_ID: 7, UploadFields.PROJECT_ID: 9}
SENT = datetime(2026, 9, 22, 10, 0, 0, tzinfo=UTC)
SHEETS = [{"sheet_name": "North", "num_rows": 3, "num_cols": 2}]
SUMMARY = "This file has more than one plausible way to be read: two header rows"
SUGGESTIONS = ["The header is on row 4", "Skip the three title lines"]


def a_file(status: str, action: dict | None = None, **item: object) -> dict:
    return {
        "resource_type": ResourceTypes.FILE,
        "object_id": 11,
        "name": "book.xlsx",
        "status": status,
        "created_at": "2026-09-22T10:00:05.000001Z",
        "object_properties": {UploadReportFields.USER_ACTION_REQUIRED: action},
        **item,
    }


def an_ambiguous_dataset() -> dict:
    """A dataset Mammoth read more than one way, as the resources API has it."""
    item = a_dataset(
        DatasetStatus.HAS_UNSTRUCTURED_DATA,
        {UserActions.TYPE: UserActions.UNSTRUCTURED_ROWS},
    )
    item["object_properties"][InterpretationFields.ADDITIONAL_INFO] = {
        InterpretationFields.INTERPRETATION: {
            InterpretationFields.SUMMARY: SUMMARY,
            InterpretationFields.SUGGESTIONS: SUGGESTIONS,
            # The rows the web app's modal draws. They are not the model's to
            # read: `interpret_file` answers with the rows an instruction makes.
            InterpretationFields.SAMPLE_ROWS: [["a"], ["b"]],
        }
    }
    return item


def a_dataset(status: str, action: dict | None = None) -> dict:
    return {
        **a_file(status, action),
        "resource_type": ResourceTypes.DATASET,
        "object_id": 21,
        "name": "sales",
    }


def needs_of(item: dict) -> dict:
    [described] = summarize([item], TICKET)[UploadFields.FILES]
    return described[UploadReportFields.NEEDS]


class TestWhenAnUploadIsOver:
    @pytest.mark.parametrize(
        "item",
        [
            a_file(FileStatus.PROCESSING),
            a_file(FileStatus.EXTRACTING),
            a_dataset(DatasetStatus.UNPROCESSED),
            a_dataset(DatasetStatus.PROCESSING),
        ],
        ids=["file-read", "sheets-extracted", "dataset-queued", "dataset-read"],
    )
    def test_an_item_still_being_read_keeps_the_upload_going(self, item: dict) -> None:
        done = a_dataset(DatasetStatus.READY)

        report = summarize([done, item], TICKET)

        assert report[UploadFields.STATUS] == UploadFields.PROCESSING

    @pytest.mark.parametrize(
        "item",
        [
            a_file(FileStatus.PROCESSED),
            a_file(FileStatus.ACTION_NEEDED),
            a_file(FileStatus.ERROR),
            a_dataset(DatasetStatus.READY),
            a_dataset(DatasetStatus.ACTION_NEEDED),
        ],
        ids=["read", "file-waits", "file-failed", "ready", "dataset-waits"],
    )
    def test_an_item_waiting_on_the_user_or_finished_ends_it(self, item: dict) -> None:
        # Waiting on the user is an end: polling longer would never settle it.
        report = summarize([item], TICKET)

        assert report[UploadFields.STATUS] == UploadFields.DONE

    def test_the_upload_is_what_was_made_once_it_was_sent(self) -> None:
        before = a_file(FileStatus.PROCESSED, created_at="2026-09-22T09:59:59Z")
        after = a_file(FileStatus.PROCESSED)
        at = a_file(FileStatus.PROCESSED, created_at="2026-09-22T10:00:00Z")

        assert find_made_since([before, after, at], SENT) == [after, at]

    def test_a_timestamp_with_its_own_offset_is_read_as_given(self) -> None:
        assert read_time("2026-09-22T15:30:00+05:30") == SENT


class TestWhatTheModelIsTold:
    def test_a_workbook_offers_its_sheets_and_the_tool_that_takes_them(
        self,
    ) -> None:
        action = {
            UserActions.TYPE: UserActions.SHEET_SELECTION_REQUIRED,
            UserActions.SHEET_INFO: SHEETS,
        }

        needs = needs_of(a_file(FileStatus.ACTION_NEEDED, action))

        assert needs[UploadReportFields.ACTION] == (UserActions.SHEET_SELECTION_REQUIRED)
        assert needs[UploadReportFields.SHEETS] == SHEETS
        assert "extract_sheets" in needs[UploadReportFields.NEXT_STEP]

    def test_dates_that_read_either_way_name_the_tool_that_settles_them(
        self,
    ) -> None:
        action = {UserActions.TYPE: UserActions.AMBIGUOUS_DATE_FORMAT}

        needs = needs_of(a_dataset(DatasetStatus.ACTION_NEEDED, action))

        assert "set_date_format" in needs[UploadReportFields.NEXT_STEP]
        assert UploadReportFields.SHEETS not in needs

    def test_a_password_is_asked_for_with_somewhere_else_to_put_it(self) -> None:
        # A password typed here is stored with the chat and read back by a
        # model. That is the user's call to make, not ours to make for them, so
        # both ways are offered and neither is pressed.
        action = {UserActions.TYPE: UserActions.PASSWORD_REQUIRED}

        needs = needs_of(a_file(FileStatus.ACTION_NEEDED, action))

        assert "unlock_file" in needs[UploadReportFields.NEXT_STEP]
        assert "mammoth_url" in needs[UploadReportFields.NEXT_STEP]
        assert needs[UploadReportFields.MAMMOTH_URL].endswith("/#/workspaces/7/projects/9")

    def test_a_file_that_reads_more_than_one_way_is_settled_in_the_chat(self) -> None:
        # The case the web app puts a "Review & Fix" button on. Mammoth says
        # what it could not decide and how it might be answered, so the model
        # can put the choice to the user without sending them to the web app.
        needs = needs_of(an_ambiguous_dataset())

        assert "interpret_file" in needs[UploadReportFields.NEXT_STEP]
        assert needs[UploadReportFields.SUMMARY] == SUMMARY
        assert needs[UploadReportFields.SUGGESTIONS] == SUGGESTIONS

    def test_rows_that_do_not_fit_are_settled_in_the_chat_too(self) -> None:
        # The same action, without an interpretation to answer: here the rows
        # themselves are the problem, which is a different question to put to
        # the user and a different tool to put it with.
        action = {UserActions.TYPE: UserActions.UNSTRUCTURED_ROWS}

        needs = needs_of(a_dataset(DatasetStatus.HAS_UNSTRUCTURED_DATA, action))

        assert "review_unreadable_rows" in needs[UploadReportFields.NEXT_STEP]
        assert UploadReportFields.SUMMARY not in needs

    def test_rows_that_do_not_fit_are_not_discarded_for_the_user(self) -> None:
        # Discarding is not undoable, and the rows are the user's data. The
        # step has to say both that and where a row can be kept instead.
        action = {UserActions.TYPE: UserActions.UNSTRUCTURED_ROWS}

        step = needs_of(a_dataset(DatasetStatus.HAS_UNSTRUCTURED_DATA, action))[
            UploadReportFields.NEXT_STEP
        ]

        assert "do not come back" in step
        assert "mammoth_url" in step

    def test_anything_no_tool_settles_is_sent_to_mammoth(self) -> None:
        action = {UserActions.TYPE: "schema_mismatch"}

        needs = needs_of(a_dataset(DatasetStatus.ACTION_NEEDED, action))

        assert needs[UploadReportFields.NEXT_STEP].startswith(IN_MAMMOTH)

    @pytest.mark.parametrize(
        "next_step",
        [*NEXT_STEP.values(), READ_IT_DIFFERENTLY, UNREADABLE_ROWS, IN_MAMMOTH],
    )
    def test_every_action_tells_the_model_to_ask_and_not_to_choose(self, next_step: str) -> None:
        # The choice is the user's: which sheets are theirs to name, and reading
        # 01/02 the wrong way round silently changes every date in the dataset.
        # Not necessarily the first thing in the step — a step may read
        # something first to have a question worth asking — but always there,
        # and always before anything is chosen.
        assert "Ask the user" in next_step
        assert ASK_FIRST in next_step

    def test_an_item_that_waits_on_nothing_carries_no_needs(self) -> None:
        [described] = summarize([a_dataset(DatasetStatus.READY)], TICKET)[UploadFields.FILES]

        assert described == {
            UploadReportFields.KIND: "dataset",
            UploadReportFields.DATASET_ID: 21,
            UploadReportFields.NAME: "sales",
            UploadFields.STATUS: DatasetStatus.READY,
        }

    def test_a_file_is_reported_by_its_file_id(self) -> None:
        [described] = summarize([a_file(FileStatus.PROCESSED)], TICKET)[UploadFields.FILES]

        assert described[UploadReportFields.KIND] == "file"
        assert described[UploadReportFields.FILE_ID] == 11


class TestAnItemThatStoppedOnItsOwn:
    """Mammoth names most waits. What it leaves unnamed is still not silence."""

    def test_a_file_mammoth_could_not_read_offers_the_only_way_out(self) -> None:
        needs = needs_of(a_file(FileStatus.ERROR))

        assert needs[UploadReportFields.ACTION] == FileStatus.ERROR
        assert "delete_file" in needs[UploadReportFields.NEXT_STEP]

    def test_a_file_with_nothing_in_it_is_the_users_own_to_fix(self) -> None:
        needs = needs_of(a_dataset(DatasetStatus.EMPTY))

        assert "no rows" in needs[UploadReportFields.NEXT_STEP]

    def test_a_status_nobody_here_has_seen_is_reported_rather_than_assumed(
        self,
    ) -> None:
        # The alternative is the worst answer of all: an upload reported as
        # done, with a file quietly missing from it.
        needs = needs_of(a_dataset("stared_into_the_middle_distance"))

        assert needs[UploadReportFields.NEXT_STEP].startswith(STOPPED)

    @pytest.mark.parametrize(
        "item",
        [
            a_file(FileStatus.PROCESSED),
            a_file(FileStatus.EXTRACTED),
            a_dataset(DatasetStatus.READY),
            a_dataset(DatasetStatus.PROCESSED),
            a_file(FileStatus.PROCESSING),
            a_dataset(DatasetStatus.MERGING),
        ],
        ids=[
            "file-read",
            "sheets-out",
            "ready",
            "processed",
            "busy-file",
            "busy-dataset",
        ],
    )
    def test_an_item_that_arrived_or_is_still_coming_needs_nothing(self, item: dict) -> None:
        [described] = summarize([item], TICKET)[UploadFields.FILES]

        assert UploadReportFields.NEEDS not in described

    @pytest.mark.parametrize(
        "item",
        [
            a_file(FileStatus.ERROR),
            a_dataset(DatasetStatus.EMPTY),
            an_ambiguous_dataset(),
            a_file(
                FileStatus.ACTION_NEEDED,
                {UserActions.TYPE: UserActions.PASSWORD_REQUIRED},
            ),
        ],
        ids=["unreadable", "empty", "ambiguous", "locked"],
    )
    def test_every_step_points_back_at_what_the_user_asked_for(self, item: dict) -> None:
        # An upload is a step of something larger. A model that reports it and
        # stops makes the user ask for the rest all over again.
        assert CARRY_ON in needs_of(item)[UploadReportFields.NEXT_STEP]


class TestABatchThatFinishesByItself:
    """A replay wears the same status as a file nobody can read. It needs nobody."""

    @staticmethod
    def a_replaying_batch(**extra: object) -> dict:
        item = a_dataset(
            DatasetStatus.HAS_UNSTRUCTURED_DATA,
            {UserActions.TYPE: UserActions.UNSTRUCTURED_ROWS},
        )
        item["object_properties"][InterpretationFields.ADDITIONAL_INFO] = {
            InterpretationFields.REPLAYING: True,
            **extra,
        }
        return item

    def test_a_replay_is_still_being_read_not_waiting_on_anyone(self) -> None:
        report = summarize([self.a_replaying_batch()], TICKET)

        assert report[UploadFields.STATUS] == UploadFields.PROCESSING

    def test_a_replay_is_not_put_to_the_user(self) -> None:
        # It finishes by itself. Asking about it interrupts them over a file
        # that needed nothing.
        [described] = summarize([self.a_replaying_batch()], TICKET)[UploadFields.FILES]

        assert UploadReportFields.NEEDS not in described

    def test_rows_that_do_not_fit_are_not_mistaken_for_a_replay(self) -> None:
        # Same status, no marker: this one really is waiting.
        needs = needs_of(
            a_dataset(
                DatasetStatus.HAS_UNSTRUCTURED_DATA,
                {UserActions.TYPE: UserActions.UNSTRUCTURED_ROWS},
            )
        )

        assert "review_unreadable_rows" in needs[UploadReportFields.NEXT_STEP]

    def test_a_marked_batch_that_turned_out_ambiguous_is_put_to_the_user(self) -> None:
        # Mammoth stamps the marker early and hopefully, then works out what
        # the file really is. An interpretation means it settled on ambiguous,
        # and the stale marker must not swallow that.
        needs = needs_of(
            self.a_replaying_batch(
                **{
                    InterpretationFields.INTERPRETATION: {
                        InterpretationFields.SUMMARY: SUMMARY,
                        InterpretationFields.SUGGESTIONS: SUGGESTIONS,
                    }
                }
            )
        )

        assert "interpret_file" in needs[UploadReportFields.NEXT_STEP]
