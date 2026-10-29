"""Wait for an upload to be read, and report it: one path for `upload_file` and `check_upload`.

The upload route starts one job, which starts one job per file. The first is
over at once; Mammoth reads the file in the second, and makes the dataset after.
"""

import asyncio

from mcp.server.mcpserver.exceptions import ToolError

from .consts import UPLOAD_POLL_SECONDS, UploadFields
from .deadline import seconds_left
from .jobs import JobFailed, JobStillRunning, job_id_of, still_running, wait_for_job
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
NONE_READ = (
    "Mammoth could not read any of the files: `failed` says why for each. Tell the"
    " user; nothing landed, so send the files again only once they are fixed."
)
SOME_FAILED = (
    "Mammoth could not read the files in `failed`: tell the user why. The other"
    " files landed, so do not upload them again; send only the failed ones once fixed."
)


type Report = dict[str, JsonValue]


async def finish_upload(
    ticket: Record, started: dict[str, JsonValue], goes_on: str | None = None
) -> tuple[Report, bool]:
    """What the upload made, once each file is read or the call's time is up.

    Args:
        ticket: Where the files went and when: `workspace_id`, `project_id`,
            `uploaded_at`, and `folder_resource_id` when they went to a folder.
        started: What the upload route answered: the job it started.
        goes_on: What to tell the model while the upload is not over, in place
            of the notes for a new dataset.

    Returns:
        The report, and whether every file Mammoth took was read and none failed
        to be: only then is there anything an append can report.
    """
    workspace_id = int(str(ticket[UploadFields.WORKSPACE_ID]))
    try:
        upload = await wait_for_job(workspace_id, started)
    except JobStillRunning as outlasted:
        return still_running(outlasted, goes_on or UPLOAD_GOES_ON), False
    jobs = _file_jobs(upload)
    running, failed = await _wait_for_each_file(workspace_id, jobs)
    report, late = await _report(ticket, jobs, running, failed)
    running = running or late
    notes: list[str] = []
    if running:
        report[UploadFields.STATUS] = UploadFields.PROCESSING
        report[UploadFields.JOB_IDS] = list[JsonValue](running)
        notes.append(goes_on or STILL_READING)
    if failed:
        report[UploadFields.FAILED] = list[JsonValue](failed)
        notes.append(NONE_READ if len(failed) == len(jobs) else SOME_FAILED)
    if notes:
        report[UploadFields.NEXT_STEP] = " ".join(notes)
    if upload.get(UploadFields.ERRORS):
        report[UploadFields.REJECTED] = upload[UploadFields.ERRORS]
    return report, bool(jobs) and not running and len(failed) < len(jobs)


async def _report(
    ticket: Record,
    jobs: list[dict[str, JsonValue]],
    running: list[int],
    failed: list[dict[str, JsonValue]],
) -> tuple[Report, list[int]]:
    """The report, and the jobs of files read whose dataset was not listed in time.

    It waits for the dataset only when a file was read and makes one: an append adds
    to a dataset that exists, and a failed file makes nothing.
    """
    gone = {job[UploadFields.JOB_ID] for job in failed}
    read = [
        int(str(job[UploadFields.JOB_ID])) for job in jobs if job[UploadFields.JOB_ID] not in gone
    ]
    if read and not running and not ticket.get(UploadFields.APPEND):
        report, in_time = await _report_once_read(ticket)
        return report, [] if in_time else read
    return await report_upload(ticket), []


def _file_jobs(started: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """The job of each file the upload took, with its file; empty when it took none."""
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
    """Wait for each file's job: the ones not known to be over, and the ones that failed.

    One file that fails does not end the wait for the others: they land anyway,
    and a report that leaves them out gets them uploaded twice. A job that could
    not be read is not known to have failed, so it is reported as still going:
    calling it failed would get a file that landed sent again.
    """
    running: list[int] = []
    failed: list[dict[str, JsonValue]] = []
    for job in jobs:
        try:
            await wait_for_job(workspace_id, job)
        except JobFailed as why:
            reason = str(why).removeprefix(f"{API_ERROR_PREFIX}: ")
            failed.append({**job, UploadFields.ERROR: reason})
        except ToolError:
            running.append(int(str(job[UploadFields.JOB_ID])))
    return running, failed


async def _report_once_read(ticket: Record) -> tuple[Report, bool]:
    """The report once Mammoth has made what the files hold, and whether that was in time."""
    while True:
        report = await report_upload(ticket)
        if report[UploadFields.STATUS] == UploadFields.DONE and report[UploadFields.FILES]:
            return report, True
        if seconds_left() <= UPLOAD_POLL_SECONDS:
            return report, False
        await asyncio.sleep(UPLOAD_POLL_SECONDS)
