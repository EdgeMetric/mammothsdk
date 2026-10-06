"""Wait for the job an async API route started, read through the SDK.

Most routes that change something answer at once with a job and do the work
afterwards. A tool waits for that job, so what it returns is the finished
change and not a promise of one.
"""

import asyncio
import time

from mcp.server.mcpserver.exceptions import ToolError

from .consts import (
    JOB_POLL_MAX_SECONDS,
    JOB_POLL_SECONDS,
    JOB_TIMEOUT_SECONDS,
    ErrorFields,
    JobFields,
)
from .deadline import seconds_left
from .sdk import (
    API_ERROR_PREFIX,
    UNREADABLE_API_ERROR,
    JsonValue,
    build_client,
    read_sdk_errors,
)


class JobStillRunning(ToolError):
    """A job had not finished when the wait ran out. It keeps running."""

    def __init__(self, job: dict[str, JsonValue], seconds: float) -> None:
        super().__init__(f"{API_ERROR_PREFIX}: the job did not finish in {seconds:.0f} seconds")
        self.job = job


async def wait_for_job(
    workspace_id: int,
    started: dict[str, JsonValue],
    seconds: float = JOB_TIMEOUT_SECONDS,
) -> dict[str, JsonValue]:
    """Wait for the job an async API route started, and return its result.

    Args:
        workspace_id: The workspace the tool call acts in.
        started: The payload of the route that started the job. Every async the API
            route answers `202` with the job under the key `job`.
        seconds: How long to wait before giving up on the job, at most. The
            tool call's own deadline can cut it shorter.

    Returns:
        The job's result.

    Raises:
        JobStillRunning: If the job does not finish in time. It carries the job,
            for a tool that can report a build still going.
        ToolError: If the job fails, or returns something other than an object.
    """
    job_id = find_job_id(started)
    seconds = min(seconds, seconds_left())
    deadline = time.monotonic() + seconds
    gap = JOB_POLL_SECONDS
    async with build_client(workspace_id) as client:
        while True:
            job = read_job(await read_sdk_errors(client.jobs.get_job(job_id)))
            if job[JobFields.STATUS] != JobFields.PROCESSING:
                break
            if time.monotonic() > deadline:
                raise JobStillRunning(job, seconds)
            await asyncio.sleep(gap)
            gap = min(gap * 2, JOB_POLL_MAX_SECONDS)
    if job[JobFields.STATUS] != JobFields.SUCCESS:
        raise ToolError(f"{API_ERROR_PREFIX}: {describe_job_failure(job)}")
    result = job[JobFields.RESPONSE]
    if not isinstance(result, dict):
        raise ToolError(f"{API_ERROR_PREFIX}: the job returned no object to read")
    return result


def still_running(running: JobStillRunning, note: str) -> dict[str, JsonValue]:
    """Answer for a job that outlasted the tool call: it is going, and what to do.

    Args:
        running: The wait that ran out.
        note: What the model should do now, so it does not start the job again.
    """
    return {
        JobFields.JOB_ID: running.job[JobFields.ID],
        JobFields.STATUS: JobFields.PROCESSING,
        JobFields.NOTE: note,
    }


def find_job_id(payload: dict[str, JsonValue]) -> int:
    """Find the job id in the payload of a route that answers asynchronously.

    the API has three shapes for it: the job under `job`, the job itself, and
    `job_id` alone.
    """
    job = payload.get(JobFields.JOB, payload)
    if isinstance(job, dict) and JobFields.ID in job:
        return int(str(job[JobFields.ID]))
    job_id = payload.get(JobFields.JOB_ID)
    if job_id is None:
        raise ToolError(f"{API_ERROR_PREFIX}: the route started no job")
    return int(str(job_id))


def read_job(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Take the job out of what the job route returns."""
    job = payload.get(JobFields.JOB)
    if not isinstance(job, dict) or JobFields.STATUS not in job:
        raise ToolError(f"{API_ERROR_PREFIX}: the job route returned no job")
    return job


def describe_job_failure(job: dict[str, JsonValue]) -> str:
    """Pull the reason a job failed out of its response, for the model to read."""
    response = job.get(JobFields.RESPONSE)
    if isinstance(response, dict):
        return str(response.get(ErrorFields.MESSAGE) or response.get(ErrorFields.NAME) or response)
    return UNREADABLE_API_ERROR
