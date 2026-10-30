"""A job that outlasts a tool call is named, and `get_job` reads it afterwards.

A tool call ends at 45 s, and some jobs run longer: a big upload, an extract, a
view copy. Without the job's id the model can only guess whether to start the
work again, and a second run makes a second copy of it.
"""

from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool

PROJECT, FILE = 3, 12
FILE_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/files/{FILE}"
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)
RUNNING = {"job": {"id": 41, "status": "processing", "response": None}}


class TestReadingAJob:
    def test_a_finished_job_gives_its_result(self) -> None:
        finished = {"job": {"id": 41, "status": "success", "response": {"dataview_id": 9}}}
        with a_fake_api() as api, as_caller():
            api.answer("GET", "/jobs/41", finished)
            job = call_tool("get_job", workspace_id=WORKSPACE, job_id=41)

        assert job == {"job_id": 41, "status": "success", "result": {"dataview_id": 9}}

    def test_a_job_still_running_says_so_and_to_read_it_again(self) -> None:
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            api.answer("GET", "/jobs/41", RUNNING)
            job = call_tool("get_job", workspace_id=WORKSPACE, job_id=41)

        assert job["job_id"] == 41
        assert job["status"] == "processing"
        assert "get_job" in job["note"]

    def test_a_failed_job_gives_the_reason(self) -> None:
        failed = {"job": {"id": 41, "status": "failure", "response": {"message": "disk full"}}}
        with a_fake_api() as api, as_caller():
            api.answer("GET", "/jobs/41", failed)
            with pytest.raises(ToolError, match="disk full"):
                call_tool("get_job", workspace_id=WORKSPACE, job_id=41)


class TestAToolCallThatEndsFirst:
    def test_the_error_names_the_job_and_says_it_keeps_running(self) -> None:
        # delete_file is one of the tools that answered with no job id.
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            api.answer("GET", FILE_PATH, {"file": {"id": FILE}})
            api.answer("DELETE", FILE_PATH, {"job": {"id": 41}})
            api.answer("GET", "/jobs/41", RUNNING)
            with pytest.raises(ToolError) as refused:
                call_tool("delete_file", workspace_id=WORKSPACE, project_id=PROJECT, file_id=FILE)

        said = str(refused.value)
        assert "job 41" in said
        assert "keeps running" in said
        assert "get_job" in said
