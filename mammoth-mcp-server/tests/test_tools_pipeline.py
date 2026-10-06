"""A pipeline tool whose run outlasts the tool call answers that it is still running."""

from unittest.mock import patch

import pytest

from mammoth_mcp_server.consts import JobFields
from mammoth_mcp_server.jobs import JobStillRunning
from mammoth_mcp_server.tools.pipeline import run_in_one_draft, view_ids

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool, run

PROJECT, DATASET, VIEW = 3, 5, 9
VIEW_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"
PIPELINE = f"{VIEW_PATH}/pipeline"
DRAFT = f"{VIEW_PATH}/draft-mode"
JOB = "/jobs/11"
RUNNING = {"job": {"id": 11, "status": "processing", "response": {}}}
# A budget no test waits out, so a job that is still going outlasts the call.
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "view_id": VIEW}


def draft_operations(api: object) -> list[str]:
    return [api.body(sent)["draft_operation"] for sent in api.sent("POST", DRAFT)]  # type: ignore[attr-defined]


def a_view_whose_run_never_ends(api: object, draft_mode: str = "off") -> None:
    api.answer("GET", PIPELINE, {"draft_mode": draft_mode})  # type: ignore[attr-defined]
    api.answer("POST", DRAFT, {"draft_mode": "clean"})  # type: ignore[attr-defined]
    api.answer("POST", DRAFT, {"draft_mode": "dirty", "job": {"id": 11}})  # type: ignore[attr-defined]
    api.answer("PATCH", PIPELINE, {"job": {"id": 11}})  # type: ignore[attr-defined]
    api.answer("GET", JOB, RUNNING)  # type: ignore[attr-defined]


class TestARunThatOutlastsTheToolCall:
    def test_the_draft_is_left_alone_while_its_run_goes_on(self) -> None:
        # Leaving draft mode now would land under the run.
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_view_whose_run_never_ends(api)
            with pytest.raises(JobStillRunning):
                run(run_in_one_draft(view_ids(WORKSPACE, PROJECT, DATASET, VIEW), []))

        assert draft_operations(api) == ["enter", "submit"]

    def test_adding_steps_answers_that_they_are_added_and_still_running(self) -> None:
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_view_whose_run_never_ends(api)
            answer = call_tool("add_transformations", operations=[], **IDS)

        assert answer[JobFields.JOB_ID] == 11
        assert answer[JobFields.STATUS] == JobFields.PROCESSING
        assert "Do not add them again" in answer[JobFields.NOTE]
        assert draft_operations(api) == ["enter", "submit"]

    def test_running_the_pipeline_answers_that_the_run_is_still_going(self) -> None:
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_view_whose_run_never_ends(api)
            answer = call_tool("run_pipeline", **IDS)

        assert answer[JobFields.JOB_ID] == 11
        assert answer[JobFields.STATUS] == JobFields.PROCESSING
        assert "Do not run it again" in answer[JobFields.NOTE]

    def test_running_a_draft_answers_that_the_run_is_still_going(self) -> None:
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            api.answer("POST", DRAFT, {"draft_mode": "dirty", "job": {"id": 11}})
            api.answer("GET", JOB, RUNNING)
            answer = call_tool("manage_draft", action="run", **IDS)

        assert answer[JobFields.JOB_ID] == 11
        assert "Do not run it again" in answer[JobFields.NOTE]
        assert draft_operations(api) == ["submit"]
