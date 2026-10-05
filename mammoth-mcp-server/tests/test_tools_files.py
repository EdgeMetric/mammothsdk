"""The file tools, on answers shaped like the API's.

Each test stubs the SDK client or the one request helper a tool uses, and
checks what the tool sends and what it makes of the answer.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import (
    PREVIEW_ROWS_DEFAULT,
    ColumnFields,
    FilePatchFields,
    FileSettingsFields,
    InterpretationFields,
    UnstructuredFields,
)
from mammoth_mcp_server.tools.files import (
    extract_sheets,
    interpret_file,
    read_preview,
    read_unreadable_rows,
    review_unreadable_rows,
    set_date_format,
    unlock_file,
)

from .helpers import lends, run

REFUSED = "that would invent a column the file does not have"
FILES = "mammoth_mcp_server.tools.files"
INSTRUCTION = "the header is on row 4"


class TestWhatAnInterpretationPreviewSays:
    """A preview answers the same way whether or not it worked, so it is read."""

    @staticmethod
    def a_preview(**answered: object) -> dict:
        return {
            InterpretationFields.ROWS: [["name", "amount"], *([["foo", "1"]] * 40)],
            InterpretationFields.TOTAL_ROWS: 900,
            InterpretationFields.STRUCTURE_MAP: {"header_row": 3},
            **answered,
        }

    def test_the_rows_an_instruction_makes_come_back_with_the_whole_count(self) -> None:
        read = read_preview(self.a_preview())

        assert read[InterpretationFields.ROWS][0] == ["name", "amount"]
        assert read[InterpretationFields.TOTAL_ROWS] == 900
        assert read[InterpretationFields.APPLIED] is False

    def test_only_enough_rows_to_judge_the_reading_are_kept(self) -> None:
        # The user is deciding where the table starts, not reading the data,
        # and 50 rows of it would crowd out everything else in the answer.
        read = read_preview(self.a_preview())

        assert len(read[InterpretationFields.ROWS]) == 11

    def test_an_instruction_mammoth_will_not_follow_is_raised_with_its_reason(
        self,
    ) -> None:
        # It arrives as an ordinary answer with no rows. Reported as one, the
        # model would tell the user their file is empty.
        refused = self.a_preview(
            preview_rows=[],
            total_row_count=0,
            structure_map={
                InterpretationFields.IN_SCOPE: False,
                InterpretationFields.REFUSED: REFUSED,
            },
        )

        with pytest.raises(ToolError, match=REFUSED):
            read_preview(refused)

    def test_a_batch_that_no_longer_fits_its_dataset_is_raised_too(self) -> None:
        # The same refusal, worded for a file added to an existing dataset.
        refused = self.a_preview(
            structure_map={
                InterpretationFields.COMPATIBLE: False,
                InterpretationFields.REFUSED: REFUSED,
            }
        )

        with pytest.raises(ToolError, match=REFUSED):
            read_preview(refused)


class TestApplyingWhatTheUserSaw:
    """Applying reads the whole file the way the preview read its first rows."""

    @staticmethod
    def interpret(**arguments: Any) -> tuple[dict, AsyncMock]:
        """Run the tool over a preview that worked, and hand back the confirm.

        Both halves are the SDK's own methods now. What the confirm sends is
        the SDK's business; what this holds to is that the tool asks it to
        reuse the plan the preview saved rather than working one out again.
        """
        datasets = MagicMock()
        datasets.preview_interpretation = AsyncMock(
            return_value={
                InterpretationFields.ROWS: [["name"], ["foo"]],
                InterpretationFields.TOTAL_ROWS: 2,
                InterpretationFields.STRUCTURE_MAP: {"header_row": 3},
            }
        )
        datasets.confirm_interpretation = AsyncMock(return_value=None)
        client = MagicMock(datasets=datasets)
        with patch(f"{FILES}.build_client", lends(client)):
            read = run(
                interpret_file(
                    workspace_id=1,
                    project_id=2,
                    dataset_id=3,
                    instruction=INSTRUCTION,
                    **arguments,
                )
            )
        return read, datasets.confirm_interpretation

    def test_a_preview_leaves_the_dataset_as_it_was(self) -> None:
        # The user has not seen the rows yet, so nothing may be read this way.
        read, confirmed = self.interpret()

        assert read[InterpretationFields.APPLIED] is False
        confirmed.assert_not_called()

    def test_applying_reads_the_file_the_way_it_was_just_previewed(self) -> None:
        # Not the same instruction worked out again: it is worked out by a
        # model, which would not answer identically twice, and the user
        # approved the rows of one particular answer.
        read, confirmed = self.interpret(apply=True)

        assert read[InterpretationFields.APPLIED] is True
        confirmed.assert_awaited_once()
        [dataset_id, instruction] = confirmed.call_args.args
        assert dataset_id == 3
        assert instruction == INSTRUCTION


class TestTheRowsThatWouldNotGoIn:
    """The lines a file set aside, shown to the user and discarded on request."""

    RAGGED = [
        {
            UnstructuredFields.LINE: "Sales,North,2024,extra",
            UnstructuredFields.LINE_NUMBER: 7,
            UnstructuredFields.REASON: "Mismatched columns. Detected: 4. Expected: 3",
        }
    ]

    @staticmethod
    def set_aside(batch_id: int, line_number: int) -> dict:
        """One set-aside line, as the API lists it."""
        return {
            UnstructuredFields.LINE: f"line {line_number}",
            UnstructuredFields.LINE_NUMBER: line_number,
            UnstructuredFields.BATCH_ID: batch_id,
            UnstructuredFields.REASON: "Mismatched columns. Detected: 4. Expected: 3",
        }

    @staticmethod
    def review(*answers: dict, **arguments: Any) -> tuple[dict, MagicMock]:
        """Run the tool over the SDK's answers to each read, and hand back its datasets.

        The tool calls the SDK, so what is stubbed is the SDK's own methods and
        what is asserted is which one the tool chose — reading and discarding
        are different methods rather than different HTTP verbs.
        """
        datasets = MagicMock()
        datasets.get_unstructured_rows = AsyncMock(side_effect=answers)
        datasets.resolve_unstructured_rows = AsyncMock(return_value={"id": 9})
        client = MagicMock(datasets=datasets)
        client.jobs.wait_for_job = AsyncMock(return_value={})
        with patch(f"{FILES}.build_client", lends(client)):
            read = run(
                review_unreadable_rows(workspace_id=1, project_id=2, dataset_id=3, **arguments)
            )
        return read, datasets

    def test_reading_the_rows_discards_nothing(self) -> None:
        # The user has not seen them yet, and a discarded line does not come
        # back — so the reading call must not be able to throw one away.
        read, called = self.review(
            {
                UnstructuredFields.ROWS: self.RAGGED,
                UnstructuredFields.ROW_COUNT: 1,
            }
        )

        assert read[UnstructuredFields.ROWS] == self.RAGGED
        assert read[UnstructuredFields.DISCARDED] is False
        called.get_unstructured_rows.assert_awaited_once()
        called.resolve_unstructured_rows.assert_not_awaited()

    def test_how_many_rows_there_are_is_reported_even_when_few_are_shown(self) -> None:
        # A file can set thousands of lines aside. Every one of them would go
        # through the conversation, and the user is deciding about the lot.
        read, _ = self.review(
            {
                UnstructuredFields.ROWS: self.RAGGED * 60,
                UnstructuredFields.ROW_COUNT: 900,
            }
        )

        assert len(read[UnstructuredFields.ROWS]) == PREVIEW_ROWS_DEFAULT
        assert read[UnstructuredFields.ROW_COUNT] == 900

    def test_discarding_removes_the_lines_of_each_upload_and_says_how_many_went(
        self,
    ) -> None:
        rows = [self.set_aside(5, 7), self.set_aside(5, 9), self.set_aside(6, 2)]

        read, called = self.review(
            {UnstructuredFields.ROWS: rows}, {UnstructuredFields.ROWS: []}, discard=True
        )

        assert read[UnstructuredFields.DELETED] == 3
        assert read[UnstructuredFields.DISCARDED] is True
        removed = {
            call.args[2]: (call.args[1], [line["line_num"] for line in call.args[3]])
            for call in called.resolve_unstructured_rows.await_args_list
        }
        assert removed == {5: ("remove", [7, 9]), 6: ("remove", [2])}

    def test_discarding_goes_on_until_a_read_brings_no_more_lines(self) -> None:
        # One read lists the first lines only, so a file that set many aside
        # takes more than one.
        read, called = self.review(
            {UnstructuredFields.ROWS: [self.set_aside(5, 7)]},
            {UnstructuredFields.ROWS: [self.set_aside(5, 8)]},
            {UnstructuredFields.ROWS: []},
            discard=True,
        )

        assert read[UnstructuredFields.DELETED] == 2
        assert called.resolve_unstructured_rows.await_count == 2

    def test_a_line_still_listed_after_it_went_is_not_discarded_twice(self) -> None:
        # A read made straight after a discard can still show the line.
        stale = {UnstructuredFields.ROWS: [self.set_aside(5, 7)]}

        read, called = self.review(stale, stale, discard=True)

        assert read[UnstructuredFields.DELETED] == 1
        called.resolve_unstructured_rows.assert_awaited_once()

    def test_a_dataset_with_no_such_rows_reports_none(self) -> None:
        read = read_unreadable_rows({UnstructuredFields.ROWS: [], UnstructuredFields.ROW_COUNT: 0})

        assert read[UnstructuredFields.ROWS] == []
        assert read[UnstructuredFields.ROW_COUNT] == 0


class TestChangingOneThingAboutAFile:
    """Both tools that settle a stuck file patch it, and the shapes differ."""

    @staticmethod
    def sent_by(call: Any) -> dict:
        """The patch one tool puts on the wire, without a Mammoth to take it."""
        patched = AsyncMock(return_value={})
        with (
            patch(f"{FILES}.request_api", patched),
            patch(f"{FILES}.build_client", lends(MagicMock(workspace_id=1))),
            patch(f"{FILES}.wait_for_job", AsyncMock(return_value={})),
        ):
            run(call)
        [change] = patched.call_args.kwargs["body"][FilePatchFields.PATCH]
        return change

    def test_a_password_replaces_the_password_and_nothing_else(self) -> None:
        change = self.sent_by(
            unlock_file(workspace_id=1, project_id=2, file_id=3, password="let me in")
        )

        assert change[FilePatchFields.OP] == FilePatchFields.REPLACE
        assert change[FilePatchFields.PATH] == FilePatchFields.PASSWORD
        assert change[FilePatchFields.VALUE] == "let me in"

    def test_sheets_are_named_under_a_key_of_their_own(self) -> None:
        # A workbook's sheets are wrapped and a password is not: the two tools
        # share the patch, not what goes in it.
        change = self.sent_by(
            extract_sheets(workspace_id=1, project_id=2, file_id=3, sheets=["North", "South"])
        )

        assert change[FilePatchFields.PATH] == FilePatchFields.EXTRACT_SHEETS
        assert change[FilePatchFields.VALUE] == {FilePatchFields.SHEETS: ["North", "South"]}


class TestWhichWayRoundTheDatesRead:
    """A file can hold one US column and one UK column, so the answer is per column."""

    COLUMNS = [
        {
            ColumnFields.DISPLAY_NAME: "ordered on",
            ColumnFields.INTERNAL_NAME: "column_3",
            ColumnFields.FORMAT: {},
        },
        {
            ColumnFields.DISPLAY_NAME: "shipped on",
            ColumnFields.INTERNAL_NAME: "column_4",
            ColumnFields.FORMAT: {ColumnFields.DATE_FORMAT_TYPE: "UK"},
        },
    ]
    SETTINGS = {
        "info": {
            "delimiter": ",",
            "has_header": True,
            "initial_skip_count": 0,
            "quotechar": '"',
            FileSettingsFields.DATE_COLUMNS: COLUMNS,
        }
    }

    @classmethod
    def read_then(cls, **arguments: Any) -> tuple[dict, AsyncMock]:
        """Run the tool over a file with one unanswered column and one answered."""
        called = AsyncMock(side_effect=[cls.SETTINGS, {"job": {"id": 1}}])
        with (
            patch(f"{FILES}.request_api", called),
            patch(f"{FILES}.build_client", lends(MagicMock(workspace_id=1))),
            patch(f"{FILES}.wait_for_job", AsyncMock(return_value={})),
        ):
            answer = run(set_date_format(workspace_id=1, project_id=2, dataset_id=3, **arguments))
        return answer, called

    def test_asking_with_no_format_names_the_columns_and_changes_nothing(self) -> None:
        # The model cannot put a useful question to the user without them, and
        # a read that quietly rewrote the file would be a trap.
        answer, called = self.read_then()

        assert answer[FileSettingsFields.AMBIGUOUS_COLUMNS] == [
            "ordered on",
            "shipped on",
        ]
        assert answer[FileSettingsFields.APPLIED] is False
        assert called.call_count == 1

    def test_one_format_is_sent_for_the_whole_file(self) -> None:
        answer, called = self.read_then(date_format="US")

        assert called.call_args.kwargs["body"][FileSettingsFields.DATE_FORMAT] == "US"
        assert answer[FileSettingsFields.APPLIED] is True

    def test_a_column_is_named_the_way_the_route_knows_it(self) -> None:
        # The user says "ordered on"; the route only answers to "column_3".
        _, called = self.read_then(columns={"ordered on": "US"})

        sent = called.call_args.kwargs["body"][FileSettingsFields.DATE_FORMATS]
        assert sent["column_3"] == "US"

    def test_a_column_already_answered_for_is_not_undone(self) -> None:
        # The route takes the whole set every time and forgets what is left
        # out, so answering about one column would silently reopen the other.
        _, called = self.read_then(columns={"ordered on": "US"})

        sent = called.call_args.kwargs["body"][FileSettingsFields.DATE_FORMATS]
        assert sent == {"column_3": "US", "column_4": "UK"}

    def test_a_column_the_file_does_not_have_is_refused_by_name(self) -> None:
        # Otherwise the call succeeds and sets nothing, and the model reports
        # to the user that their dates are fixed.
        with pytest.raises(ToolError, match="delivered on"):
            self.read_then(columns={"delivered on": "US"})

    def test_the_project_default_is_only_set_when_it_is_asked_for(self) -> None:
        # It outlives this file: every later upload into the project stops
        # being asked. Nothing may turn that on by itself.
        _, called = self.read_then(date_format="UK")

        assert called.call_args.kwargs["body"][FileSettingsFields.PROJECT_DEFAULT] is (False)
