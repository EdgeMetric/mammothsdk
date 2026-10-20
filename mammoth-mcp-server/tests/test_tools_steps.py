"""Changing one step of a pipeline, and what a model is told when the change breaks it."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import JobFields

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

PROJECT, DATASET, VIEW = 3, 5, 9
VIEW_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"
PIPELINE = f"{VIEW_PATH}/pipeline"
TASKS = f"{PIPELINE}/tasks"
DRAFT = f"{VIEW_PATH}/draft-mode"
RUN_JOB = "/jobs/21"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "view_id": VIEW}
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)

AMOUNT = {"display_name": "amount", "internal_name": "column_2", "type": "NUMERIC"}
QTY = {"display_name": "qty", "internal_name": "column_3", "type": "NUMERIC"}
TOTAL = {"display_name": "total", "internal_name": "column_total", "type": "NUMERIC"}
# Step 1 makes `total` from amount and qty; step 2 reads `total`.
MAKES_TOTAL: dict[str, Any] = {
    "id": 101,
    "sequence": 1,
    "status": "executed",
    "transform_status": "DONE",
    "reference_errors": None,
    "prev_metadata": [AMOUNT, QTY],
    "params": {
        "MATH": {
            "AS": {"TYPE": "NUMERIC", "COLUMN": "total", "INTERNAL_NAME": "column_total"},
            "EXPRESSION": [
                {"TYPE": "COLUMN", "VALUE": "column_2"},
                {"TYPE": "OPERATOR", "VALUE": "*"},
                {"TYPE": "COLUMN", "VALUE": "column_3"},
            ],
        },
        "TASK_KEY": "MATH",
        "CONDITION": None,
        "DATAVIEW_ID": VIEW,
        "TASK_NAMESPACE": "fiafw",
        "SEQUENCE_NUMBER": 1,
        "EXECUTION_TIMESTAMP": "2026-10-20 07:54:30",
    },
}
READS_TOTAL: dict[str, Any] = {
    "id": 102,
    "sequence": 2,
    "status": "executed",
    "transform_status": "DONE",
    "reference_errors": None,
    "prev_metadata": [AMOUNT, QTY, TOTAL],
    "params": {"MATH": {"AS": {"COLUMN": "total_plus"}}, "TASK_KEY": "MATH"},
}
STEP = f"{TASKS}/{MAKES_TOTAL['id']}"
OTHER_STEP = f"{TASKS}/{READS_TOTAL['id']}"
# The route answers with a job whose result is the change; the change names its run.
A_RUN = {"job": {"id": 31}}
CHANGE_JOB = "/jobs/31"
CHANGE_MADE = {
    "job": {"id": 31, "status": "success", "response": {"status": "processing", "future_id": 21}}
}
CLEAN_RUN = {"job": {"id": 21, "status": "success", "response": {"has_error": False}}}
BOOM = {"exception": "column_total is not there"}


def failing(step: dict[str, Any]) -> dict[str, Any]:
    return {**deepcopy(step), "transform_status": "ERROR", "reference_errors": BOOM}


def suspended(step: dict[str, Any]) -> dict[str, Any]:
    return {**deepcopy(step), "status": "suspended", "transform_status": "SUSPENDED"}


def a_view(
    api: FakeApi,
    *listings: list[dict[str, Any]],
    draft_mode: str = "off",
    runs: tuple[dict[str, Any], ...] = (CLEAN_RUN,),
) -> None:
    """A view whose steps list as each listing in turn, the last one from then on.

    Each run it starts ends as `runs` says, in turn.
    """
    for steps in listings:
        api.answer("GET", TASKS, {"tasks": steps})
    api.answer("GET", PIPELINE, {"draft_mode": draft_mode, "execution_state": "idle"})
    for each in runs:
        api.answer("GET", RUN_JOB, each)
    api.answer("GET", CHANGE_JOB, CHANGE_MADE)


def patches(api: FakeApi, path: str = STEP) -> list[dict[str, Any]]:
    """The one patch each request to the step's edit route carried."""
    sent = [api.body(request)["patches"] for request in api.sent("PATCH", path)]
    assert all(len(each) == 1 for each in sent)
    return [each[0] for each in sent]


def replace_total(new_column: str = "total") -> dict[str, Any]:
    return {"op": "math", "expression": "amount + qty", "new_column": new_column}


class TestReplacingAStep:
    def test_it_is_built_on_the_columns_its_step_reads(self) -> None:
        # The view's own columns are never read: no fake answers for them.
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool(
                "edit_transformation_step",
                step_id=101,
                change="replace",
                operation=replace_total(),
                **IDS,
            )

        [sent] = patches(api)
        assert (sent["op"], sent["path"]) == ("replace", "params")
        assert sent["value"]["DATAVIEW_ID"] == VIEW
        expression = sent["value"]["MATH"]["EXPRESSION"]
        assert {"TYPE": "COLUMN", "VALUE": "column_2"} in expression
        assert {"TYPE": "OPERATOR", "VALUE": "+"} in expression
        assert answer["outcome"] == "changed"
        assert answer["problems"] == []
        assert answer["step"]["id"] == 101

    def test_a_column_of_the_same_name_keeps_its_internal_name(self) -> None:
        # Step 2 reads `total` by its internal name; a new one would lose it.
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", STEP, A_RUN)
            call_tool(
                "edit_transformation_step",
                step_id=101,
                change="replace",
                operation=replace_total(),
                **IDS,
            )

        [sent] = patches(api)
        assert sent["value"]["MATH"]["AS"]["INTERNAL_NAME"] == "column_total"

    def test_a_column_with_a_new_name_gets_a_new_internal_name(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", STEP, A_RUN)
            call_tool(
                "edit_transformation_step",
                step_id=101,
                change="replace",
                operation=replace_total("sum"),
                **IDS,
            )

        [sent] = patches(api)
        assert sent["value"]["MATH"]["AS"]["INTERNAL_NAME"] != "column_total"

    def test_a_column_a_later_step_makes_is_not_there_to_use(self) -> None:
        # `total` exists only after step 1, so step 1 cannot read it.
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            with pytest.raises(ToolError, match="does not fit the view.*total"):
                call_tool(
                    "edit_transformation_step",
                    step_id=101,
                    change="replace",
                    operation={"op": "math", "expression": "total * 2", "new_column": "x"},
                    **IDS,
                )

        assert api.sent("PATCH", STEP) == []

    def test_without_an_operation_it_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL])
            with pytest.raises(ToolError, match="needs `operation`"):
                call_tool("edit_transformation_step", step_id=101, change="replace", **IDS)

        assert api.sent("PATCH", STEP) == []


class TestWhichStep:
    def test_a_step_of_another_view_is_refused_before_anything_is_sent(self) -> None:
        # The route finds a step by id in any view, then edits this view's step
        # at that place: the wrong step.
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            with pytest.raises(ToolError, match=r"no step 555\. Its steps: \[101, 102\]"):
                call_tool("edit_transformation_step", step_id=555, change="suspend", **IDS)

        assert [r for r in api.requests if r.method == "PATCH"] == []


class TestSuspendingAndRestoring:
    def test_suspending_sends_the_command_alone(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", OTHER_STEP, A_RUN)
            answer = call_tool("edit_transformation_step", step_id=102, change="suspend", **IDS)

        assert patches(api, OTHER_STEP) == [{"op": "command", "path": "suspend", "value": None}]
        assert answer["outcome"] == "changed"

    def test_restoring_a_suspended_step_sends_restore(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, suspended(READS_TOTAL)], [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", OTHER_STEP, A_RUN)
            call_tool("edit_transformation_step", step_id=102, change="restore", **IDS)

        assert patches(api, OTHER_STEP) == [{"op": "command", "path": "restore", "value": None}]

    @pytest.mark.parametrize(
        ("step", "change", "reason"),
        [
            (suspended(READS_TOTAL), "suspend", "suspended already"),
            (READS_TOTAL, "restore", "not suspended"),
        ],
        ids=["suspend-twice", "restore-a-running-step"],
    )
    def test_a_command_that_changes_nothing_is_refused(
        self, step: dict[str, Any], change: str, reason: str
    ) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, step])
            with pytest.raises(ToolError, match=reason):
                call_tool("edit_transformation_step", step_id=102, change=change, **IDS)

        assert api.sent("PATCH", OTHER_STEP) == []

    def test_an_operation_with_a_command_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            with pytest.raises(ToolError, match='only with "replace"'):
                call_tool(
                    "edit_transformation_step",
                    step_id=102,
                    change="suspend",
                    operation=replace_total(),
                    **IDS,
                )


class TestInDraftMode:
    def test_the_change_is_staged_and_nothing_is_waited_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL], draft_mode="dirty")
            api.answer("PATCH", OTHER_STEP, {"status": "done", "future_id": None})
            answer = call_tool("edit_transformation_step", step_id=102, change="suspend", **IDS)

        assert answer["outcome"] == "staged"
        assert 'manage_draft with "run"' in answer["next_step"]
        assert api.sent("GET", RUN_JOB) == []


class TestAChangeMammothRefuses:
    def test_a_change_that_breaks_a_later_step_says_how_to_make_it(self) -> None:
        # The shape Mammoth refuses with: each column, and the steps that read it.
        reader = {"sequence": 2, "param": READS_TOTAL["params"], "dataview_id": VIEW}
        refused = {
            "status": "error",
            "error_code": 7010,
            "error_info": {"column_to_dependencies_dict": {"column_total": {"tasks": [reader]}}},
        }
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", STEP, refused)
            with pytest.raises(ToolError) as error:
                call_tool(
                    "edit_transformation_step",
                    step_id=101,
                    change="replace",
                    operation=replace_total("sum"),
                    **IDS,
                )

        message = str(error.value)
        assert "'total' is read by step 2." in message
        # The reading step's own params are not repeated to the model.
        assert "total_plus" not in message
        assert "Nothing changed" in message
        assert 'manage_draft with "start"' in message
        assert len(api.sent("PATCH", STEP)) == 1

    def test_a_step_of_another_view_that_reads_the_column_is_named_with_its_view(self) -> None:
        reader = {"sequence": 4, "dataview_id": 77}
        refused = {
            "status": "error",
            "error_info": {"column_to_dependencies_dict": {"column_total": {"tasks": [reader]}}},
        }
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL])
            api.answer("PATCH", STEP, refused)
            with pytest.raises(ToolError, match="'total' is read by step 4 of view 77"):
                call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)


class TestAChangeMadeWithBrokenReferences:
    """Mammoth makes the change, and says later steps now read a missing column."""

    MADE_WITH_ERRORS = {"status": "done", "has_error": True, "error_info": None}

    def test_in_draft_mode_it_is_staged_with_the_steps_that_will_fail(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(
                api,
                [MAKES_TOTAL, READS_TOTAL],
                [MAKES_TOTAL, failing(READS_TOTAL)],
                draft_mode="dirty",
            )
            api.answer("PATCH", STEP, self.MADE_WITH_ERRORS)
            answer = call_tool(
                "edit_transformation_step",
                step_id=101,
                change="replace",
                operation=replace_total("sum"),
                **IDS,
            )

        assert answer["outcome"] == "staged"
        assert [problem["step_id"] for problem in answer["problems"]] == [102]
        assert "change them first" in answer["next_step"]

    def test_outside_draft_mode_it_is_put_back(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(
                api,
                [MAKES_TOTAL, READS_TOTAL],
                [MAKES_TOTAL, failing(READS_TOTAL)],
                [MAKES_TOTAL, READS_TOTAL],
            )
            api.answer("PATCH", STEP, self.MADE_WITH_ERRORS)
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)

        assert [sent["path"] for sent in patches(api)] == ["suspend", "restore"]
        assert answer["outcome"] == "put_back"


class TestAChangeThatBreaksTheView:
    def test_a_replaced_step_that_breaks_a_later_one_is_put_back(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(
                api,
                [MAKES_TOTAL, READS_TOTAL],
                [MAKES_TOTAL, failing(READS_TOTAL)],
                [MAKES_TOTAL, READS_TOTAL],
            )
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool(
                "edit_transformation_step",
                step_id=101,
                change="replace",
                operation=replace_total(),
                **IDS,
            )

        _, undo = patches(api)
        # The stored step goes back without the keys Mammoth adds to it.
        assert undo["value"] == {
            "MATH": MAKES_TOTAL["params"]["MATH"],
            "CONDITION": None,
            "DATAVIEW_ID": VIEW,
        }
        assert answer["outcome"] == "put_back"
        assert "undone" in answer["next_step"]
        [problem] = answer["problems"]
        assert problem["step_id"] == 102
        assert problem["error"] == BOOM
        assert problem["task"] == "MATH"

    def test_a_suspended_step_that_breaks_a_later_one_is_restored(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(
                api,
                [MAKES_TOTAL, READS_TOTAL],
                [suspended(MAKES_TOTAL), failing(READS_TOTAL)],
                [MAKES_TOTAL, READS_TOTAL],
            )
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)

        assert [sent["path"] for sent in patches(api)] == ["suspend", "restore"]
        assert answer["outcome"] == "put_back"

    def test_a_step_that_failed_before_the_change_is_not_a_reason_to_undo_it(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, failing(READS_TOTAL)])
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool(
                "edit_transformation_step",
                step_id=101,
                change="replace",
                operation=replace_total(),
                **IDS,
            )

        assert len(patches(api)) == 1
        assert answer["outcome"] == "changed"
        assert "in error before" in answer["next_step"]
        assert [problem["step_id"] for problem in answer["problems"]] == [102]

    def test_a_run_that_fails_as_a_whole_is_put_back_too(self) -> None:
        with a_fake_api() as api, as_caller():
            failed_run = {"job": {"id": 21, "status": "failure", "response": {}}}
            a_view(api, [MAKES_TOTAL, READS_TOTAL], runs=(failed_run, CLEAN_RUN))
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)

        assert [sent["path"] for sent in patches(api)] == ["suspend", "restore"]
        assert answer["outcome"] == "put_back"

    def test_when_undoing_fails_too_the_user_is_sent_to_the_view(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL], [MAKES_TOTAL, failing(READS_TOTAL)])
            api.answer("PATCH", STEP, A_RUN)
            api.answer("PATCH", STEP, {"status": "error", "error_info": {"reason": "locked"}})
            answer = call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)

        assert answer["outcome"] == "not_put_back"
        assert "locked" in answer["next_step"]
        assert "mammoth_url" in answer["next_step"]
        assert answer["mammoth_url"].endswith(f"/views/{VIEW}")

    def test_a_view_still_failing_after_the_undo_is_not_called_put_back(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, READS_TOTAL], [MAKES_TOTAL, failing(READS_TOTAL)])
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)

        assert [sent["path"] for sent in patches(api)] == ["suspend", "restore"]
        assert answer["outcome"] == "not_put_back"
        assert "still fails" in answer["next_step"]


class TestARunThatOutlastsTheCall:
    def test_the_model_is_told_not_to_change_it_again(self) -> None:
        running = {"job": {"id": 21, "status": "processing", "response": {}}}
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_view(api, [MAKES_TOTAL, READS_TOTAL], runs=(running,))
            api.answer("PATCH", STEP, A_RUN)
            answer = call_tool("edit_transformation_step", step_id=101, change="suspend", **IDS)

        assert answer[JobFields.JOB_ID] == 21
        assert "Do not change it again" in answer[JobFields.NOTE]


class TestTellingTheUserWhatIsWrong:
    def test_get_pipeline_lists_a_step_in_error_with_what_to_do(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, failing(READS_TOTAL)])
            answer = call_tool("get_pipeline", **IDS)

        [problem] = answer["problems"]
        assert problem["step_id"] == 102
        assert "edit_transformation_step" in answer["next_step"]

    def test_get_pipeline_says_when_changes_are_staged_and_not_run(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL], draft_mode="dirty")
            answer = call_tool("get_pipeline", **IDS)

        assert "problems" not in answer
        assert "have not run" in answer["next_step"]

    def test_a_clean_pipeline_has_nothing_to_tell(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL])
            answer = call_tool("get_pipeline", **IDS)

        assert "problems" not in answer
        assert "next_step" not in answer

    def test_running_a_draft_reports_the_steps_it_broke(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [MAKES_TOTAL, failing(READS_TOTAL)])
            api.answer("POST", DRAFT, {"draft_mode": "dirty", "job": {"id": 21}})
            answer = call_tool("manage_draft", action="run", **IDS)

        assert [problem["step_id"] for problem in answer["problems"]] == [102]
        assert "edit_transformation_step" in answer["next_step"]

    def test_the_help_explains_when_to_draft_and_what_to_do_on_an_error(self) -> None:
        with as_caller():
            text = call_tool("get_help", topic="pipeline")["help"]

        assert "Run now, or draft" in text
        assert "When a step fails" in text
