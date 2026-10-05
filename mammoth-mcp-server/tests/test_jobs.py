"""Waiting for the job an async route started."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import JobFields
from mammoth_mcp_server.jobs import (
    JobStillRunning,
    describe_job_failure,
    find_job_id,
    read_job,
    wait_for_job,
)

from .helpers import WORKSPACE, a_fake_api, as_caller, run

JOB = "/jobs/11"


def a_job(status: str, response: object = None) -> dict:
    return {"job": {"id": 11, "status": status, "response": response}}


class TestWaitingForAJob:
    def test_a_finished_job_hands_back_its_result(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", JOB, a_job("processing"))
            api.answer("GET", JOB, a_job("success", {"rows": 3}))
            result = run(wait_for_job(WORKSPACE, {"job": {"id": 11}}))

        assert result == {"rows": 3}
        assert len(api.sent("GET", JOB)) == 2

    def test_a_failed_job_is_reported_with_its_reason(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", JOB, a_job("error", {"message": "the file is empty"}))
            with pytest.raises(ToolError, match="the file is empty"):
                run(wait_for_job(WORKSPACE, {"job_id": 11}))

    def test_a_job_still_running_when_the_wait_ends_is_handed_back(self) -> None:
        # A tool whose job outlasts the wait reports it as still going, so the
        # model can check back instead of starting it again.
        with a_fake_api() as api, as_caller():
            api.answer("GET", JOB, a_job("processing", {"id": 42}))
            with pytest.raises(JobStillRunning) as error:
                run(wait_for_job(WORKSPACE, {"job_id": 11}, seconds=0.05))

        assert error.value.job[JobFields.ID] == 11
        assert error.value.job[JobFields.STATUS] == JobFields.PROCESSING

    def test_a_job_that_returns_no_object_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", JOB, a_job("success", None))
            with pytest.raises(ToolError, match="no object"):
                run(wait_for_job(WORKSPACE, {"job_id": 11}))


class TestReadingWhatARouteStarted:
    @pytest.mark.parametrize(
        "payload",
        [{"job": {"id": 11}}, {"id": 11, "status": "processing"}, {"job_id": 11}],
        ids=["under-job", "the-job-itself", "job-id-alone"],
    )
    def test_the_job_id_is_found_in_each_shape_the_api_uses(self, payload: dict) -> None:
        assert find_job_id(payload) == 11

    def test_a_payload_that_started_no_job_is_refused(self) -> None:
        with pytest.raises(ToolError, match="started no job"):
            find_job_id({"workspaces": []})

    def test_a_job_route_payload_without_a_status_is_refused(self) -> None:
        # A job with no status cannot be waited on: fail loudly rather than
        # treat it as finished.
        with pytest.raises(ToolError):
            read_job({JobFields.JOB: {}})

    def test_a_failure_with_no_message_names_what_the_job_did_say(self) -> None:
        assert describe_job_failure({"response": {"name": "NOT_FOUND"}}) == "NOT_FOUND"
