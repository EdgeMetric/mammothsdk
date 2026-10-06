"""Waiting for the job an async route started."""

import time
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import JOB_POLL_MAX_SECONDS, JOB_POLL_SECONDS, JobFields
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

    def test_the_wait_between_checks_grows_and_stops_at_its_cap(self) -> None:
        # A long build is checked about once every couple of seconds, not four
        # times a second; a short job is still seen at once.
        waited: list[float] = []

        async def note(seconds: float) -> None:
            waited.append(seconds)

        with a_fake_api() as api, as_caller(), patch("mammoth_mcp_server.jobs.asyncio.sleep", note):
            for _ in range(8):
                api.answer("GET", JOB, a_job("processing"))
            api.answer("GET", JOB, a_job("success", {"rows": 3}))
            run(wait_for_job(WORKSPACE, {"job": {"id": 11}}))

        assert waited[0] == JOB_POLL_SECONDS
        assert waited == sorted(waited)
        assert waited[-1] == JOB_POLL_MAX_SECONDS
        assert max(waited) == JOB_POLL_MAX_SECONDS

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


class TestOneDeadlinePerToolCall:
    def test_every_wait_in_a_tool_call_spends_from_one_deadline(self) -> None:
        # A client gives up on a call after about a minute: two waits of a
        # minute each would answer nobody.
        async def two_waits() -> None:
            await wait_for_job(WORKSPACE, {"job_id": 11})
            await wait_for_job(WORKSPACE, {"job_id": 12})

        with (
            a_fake_api() as api,
            as_caller(),
            patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.3),
        ):
            api.answer("GET", JOB, a_job("processing"))
            api.answer("GET", JOB, a_job("success", {"rows": 3}))
            api.answer("GET", "/jobs/12", a_job("processing"))
            started = time.monotonic()
            with pytest.raises(JobStillRunning):
                run(two_waits())

        # The second wait got what the first left, not a minute of its own.
        assert time.monotonic() - started < 5
