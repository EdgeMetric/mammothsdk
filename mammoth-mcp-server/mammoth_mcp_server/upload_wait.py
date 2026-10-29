"""Wait for an upload to be read, and report it: one path for `upload_file` and `check_upload`.

The upload route starts one job, which starts one job per file. The first is
over at once; Mammoth reads the file in the second, and makes the dataset after.
"""

import asyncio

from mcp.server.mcpserver.exceptions import ToolError

from .consts import UPLOAD_POLL_SECONDS, UploadFields
from .deadline import seconds_left
from .jobs import JobStillRunning, job_id_of, still_running, wait_for_job
from .sdk import API_ERROR_PREFIX, JsonValue
from .store import Record
from .upload_report import report_upload

STILL_READING = (
    "Mammoth is still reading the file. Do not upload it again: read each job in"
    " job_ids with get_job, then list_datasets shows the dataset it made."
)
UPLOAD_GOES_ON = (
    "Mammoth has not finished taking the upload in. Do not upload it again: read"
    " the job with get_job, then list_datasets shows what it made."
)
SOME_FAILED = (
    "Mammoth could not read the files in `failed`: tell the user why. The other"
    " files landed, so do not upload them again; send only the failed ones once fixed."
)


async def finish_upload(ticket: Record, started: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """What the upload made, once each file is read or the call's time is up.

    Args:
        ticket: Where the files went and when: `workspace_id`, `project_id`,
            `uploaded_at`, and `folder_resource_id` when they went to a folder.
        started: What the upload route answered: the job it started.
    """
    workspace_id = int(str(ticket[UploadFields.WORKSPACE_ID]))
    try:
        upload = await wait_for_job(workspace_id, started)
    except JobStillRunning as outlasted:
        return still_running(outlasted, UPLOAD_GOES_ON)
    jobs = _file_jobs(upload)
    running, failed = await _wait_for_each_file(workspace_id, jobs)
    report = await (report_upload(ticket) if running or not jobs else _report_once_read(ticket))
    if report is None:
        running, report = [int(str(job[UploadFields.JOB_ID])) for job in jobs], await report_upload(
            ticket
        )
    if running:
        report[UploadFields.STATUS] = UploadFields.PROCESSING
        report[UploadFields.JOB_IDS] = list[JsonValue](running)
        report[UploadFields.NEXT_STEP] = STILL_READING
    if failed:
        report[UploadFields.FAILED] = list[JsonValue](failed)
        report.setdefault(UploadFields.NEXT_STEP, SOME_FAILED)
    if upload.get(UploadFields.ERRORS):
        report[UploadFields.REJECTED] = upload[UploadFields.ERRORS]
    return report


def _file_jobs(started: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """The job of each file the upload took, with its file. None when Mammoth refused them all."""
    jobs = started.get(UploadFields.JOB_IDS)
    found = [job for job in jobs if isinstance(job, dict)] if isinstance(jobs, list) else []
    return [
        {
            UploadFields.JOB_ID: job_id,
            UploadFields.FILE_OBJECT_ID: job.get(UploadFields.FILE_OBJECT_ID),
        }
        for job in found
        if (job_id := job_id_of(job)) is not None
    ]


async def _wait_for_each_file(
    workspace_id: int, jobs: list[dict[str, JsonValue]]
) -> tuple[list[int], list[dict[str, JsonValue]]]:
    """Wait for each file's job: the ones still running when time ran out, and the ones that failed.

    One file that fails does not end the wait for the others: they land anyway,
    and a report that leaves them out gets them uploaded twice.
    """
    running: list[int] = []
    failed: list[dict[str, JsonValue]] = []
    for job in jobs:
        try:
            await wait_for_job(workspace_id, job)
        except JobStillRunning:
            running.append(int(str(job[UploadFields.JOB_ID])))
        except ToolError as why:
            reason = str(why).removeprefix(f"{API_ERROR_PREFIX}: ")
            failed.append({**job, UploadFields.ERROR: reason})
    return running, failed


async def _report_once_read(ticket: Record) -> dict[str, JsonValue] | None:
    """The report once Mammoth has made what the files hold; None when time ran out first."""
    while True:
        report = await report_upload(ticket)
        if report[UploadFields.STATUS] == UploadFields.DONE and report[UploadFields.FILES]:
            return report
        if seconds_left() <= UPLOAD_POLL_SECONDS:
            return None
        await asyncio.sleep(UPLOAD_POLL_SECONDS)
