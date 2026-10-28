"""Wait for text sent with `upload_file` to be read, and report it as `check_upload` does.

The upload route starts one job, which starts one job per file. The first is
over at once; Mammoth reads the file in the second, and makes the dataset after.
"""

import asyncio

from .consts import UPLOAD_POLL_SECONDS, UploadFields
from .deadline import seconds_left
from .jobs import JobStillRunning, job_id_of, wait_for_job
from .sdk import JsonValue
from .upload_report import report_upload

STILL_READING = (
    "Mammoth is still reading the file. Do not upload it again: read each job in"
    " job_ids with get_job, then list_datasets shows the dataset it made."
)


async def finish_upload(
    workspace_id: int, project_id: int, since: str, started: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """What the upload made, once each file is read or the call's time is up.

    Args:
        workspace_id: The workspace the files went to.
        project_id: The project the files went to.
        since: When the files were sent: what the upload made is what the
            project gained since.
        started: What the upload job returned: its `job_ids` and `errors`.
    """
    ticket: dict[str, JsonValue] = {
        UploadFields.UPLOADED_AT: since,
        UploadFields.WORKSPACE_ID: workspace_id,
        UploadFields.PROJECT_ID: project_id,
    }
    running = await _wait_for_each_file(workspace_id, started)
    report = await report_upload(ticket) if running else await _report_once_read(ticket)
    if running:
        report[UploadFields.STATUS] = UploadFields.PROCESSING
        report[UploadFields.JOB_IDS] = list[JsonValue](running)
        report[UploadFields.NEXT_STEP] = STILL_READING
    if started.get(UploadFields.ERRORS):
        report[UploadFields.REJECTED] = started[UploadFields.ERRORS]
    return report


async def _wait_for_each_file(workspace_id: int, started: dict[str, JsonValue]) -> list[int]:
    """Wait for each file's job, and return the ones still running when time ran out."""
    jobs = started.get(UploadFields.JOB_IDS)
    running: list[int] = []
    for job in jobs if isinstance(jobs, list) else []:
        job_id = job_id_of(job) if isinstance(job, dict) else None
        if job_id is None:
            continue
        try:
            await wait_for_job(workspace_id, {UploadFields.JOB_ID: job_id})
        except JobStillRunning:
            running.append(job_id)
    return running


async def _report_once_read(ticket: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The report, polled until Mammoth has made what the files hold or time is up."""
    while True:
        report = await report_upload(ticket)
        over = report[UploadFields.STATUS] == UploadFields.DONE and report[UploadFields.FILES]
        if over or seconds_left() <= UPLOAD_POLL_SECONDS:
            return report
        await asyncio.sleep(UPLOAD_POLL_SECONDS)
