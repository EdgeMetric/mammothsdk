"""Read a job that outlasted the tool call that started it.

A tool call ends at 45 s, and a big upload, an extract or a view copy can run
longer. The tool names the job; this reads it, so the work is not started twice.
"""

from ..consts import JobFields
from ..jobs import JobStillRunning, still_running, wait_for_job
from ..sdk import JsonValue
from ..server import mcp_server
from ..tool_kinds import READS

STILL_GOING = (
    "Mammoth is still running it. Do not start the same work again: call get_job"
    " again in a while, and tell the user it is taking a while."
)


@mcp_server.tool(title="Get job", annotations=READS)
async def get_job(workspace_id: int, job_id: int) -> dict[str, JsonValue]:
    """Read a job a tool named when its call ended before the job did.

    Waits a while for the job to finish before answering.

    Args:
        workspace_id: Which workspace the job runs in.
        job_id: The job, as the tool named it.

    Returns:
        `job_id` and `status`. A finished job has `result`: what the tool
        would have returned. One still running has `note`: what to do now.
        A failed job is an error naming the reason.
    """
    try:
        result = await wait_for_job(workspace_id, {JobFields.JOB_ID: job_id})
    except JobStillRunning as running:
        return still_running(running, STILL_GOING)
    return {JobFields.JOB_ID: job_id, JobFields.STATUS: JobFields.SUCCESS, JobFields.RESULT: result}
