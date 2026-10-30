"""Add a file to an existing dataset, see what was added, and take it back.

The reading, the mode, the matching and the report are the SDK's (`client.appends`,
`mammoth.appends`): this module is the MCP side of them. It holds what is said to a model
(what to call next, what stays), the record of the mode each batch was added under, and the
rule that decides whether a batch may be removed.

A dataset has an update method: "add" puts a new file's rows under the rows it holds,
"replace" throws the old rows away and keeps the new ones. Adding a file makes a batch,
which is what can be removed again. Removing a batch that a replace made would delete rows
the dataset now depends on, so the mode in effect when each batch was made is recorded here
at upload time, and `undo` removes only batches recorded as added.

`request_upload` sends the file later, from the browser, so what is read before the send
travels in the ticket as plain data (`prepare_append` returns it).
"""

import io
from collections.abc import Mapping, Sequence
from typing import Literal

from mammoth.appends import ADDING_MODES, refuse_batch_removal
from mammoth.exceptions import MammothError, MammothJobTimeoutError
from mcp.server.mcpserver.exceptions import ToolError

from .consts import (
    APPEND_POLL_SECONDS,
    APPEND_WAIT_SECONDS,
    BATCH_MODE_KIND,
    BATCH_MODE_SECONDS,
    AppendFields,
    JobFields,
    PageFields,
)
from .deadline import seconds_left
from .jobs import JobStillRunning
from .sdk import JsonValue, build_client, read_sdk_errors
from .store import forget, recall, remember

type Mode = Literal["add", "replace"]
type Plan = dict[str, JsonValue]

NOT_AN_APPEND = (
    "`mode` only applies together with `append_to_dataset_id`: it sets the update method"
    " of the dataset the file goes into."
)
NOT_IN_A_FOLDER = (
    "`folder_resource_id` is for a new dataset: an upload into `append_to_dataset_id` goes into"
    " that dataset, wherever it is. Leave one of them out."
)
UNDO_WITH = (
    'To take this back, ask the user, then call undo with what="batch", this dataset_id'
    " and these batch_ids."
)
NOTHING_TO_REMOVE = (
    "The dataset replaces its rows, so the old rows are gone and there is no batch to remove."
    " To get them back, upload the old file again."
)
NO_MODE_NO_BATCH = (
    "The update method of the dataset could not be read ({0}), so no batch is offered for"
    " removal."
)


def present_append(report: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Say what an upload into a dataset did, and what can be done about it.

    Args:
        report: What the SDK's append reported (`AppendsAPI.finish`).

    Returns:
        The report, with the `batch_ids` kept (and `batch_id` when there is one) only for an
        upload that added, `next_step` saying what to call, and `notes` for what the user
        should be told: a method this upload changed and that stays, rows still landing,
        new batches that could not be tied to the upload.
    """
    entry = report[AppendFields.UPDATE_METHOD]
    method: dict[str, JsonValue] = dict(entry) if isinstance(entry, dict) else {}
    mode = method.get(AppendFields.MODE)
    shown = {key: value for key, value in report.items() if key != AppendFields.BATCH_IDS}
    ours = report.get(AppendFields.BATCH_IDS)
    batch_ids = (
        [batch for batch in ours if isinstance(batch, int)] if isinstance(ours, list) else []
    )
    notes: list[str] = []
    previous = method.get(AppendFields.PREVIOUS_MODE)
    if previous is not None:
        notes.append(
            f"The dataset's update method was {previous} and is now {mode}. It stays: every"
            " later upload into it follows it too."
        )
    failed = bool(report.get(AppendFields.APPEND_FAILED))
    if failed and report.get(AppendFields.REASON):
        notes.append(
            f"The upload FAILED: {report[AppendFields.REASON]} Tell the user it did not work;"
            " do not use the dataset as if the file were in it."
        )
    elif failed:
        notes.append(
            f"The upload FAILED: the dataset ended with the status"
            f" {report.get(AppendFields.STATUS)}, so rows_added says nothing about what is in"
            " it. Tell the user it did not work; do not use the dataset as if the file were in"
            " it. Read the reason with get_dataset."
        )
    elif report.get(AppendFields.APPEND_PENDING):
        reason = report.get(AppendFields.READ_ERROR)
        notes.append(
            "The dataset was still taking the rows in"
            + (f" (reading it failed: {reason})" if reason else "")
            + ", so rows_added is only what had landed and can read 0 while the rows are still"
            " arriving. Call check_upload again, or get_dataset,"
            " before using it."
        )
    if failed:
        # A failed upload leaves nothing to take back and nothing to say about batches.
        shown.pop(AppendFields.BATCH_ID, None)
    elif mode in ADDING_MODES:
        shown[AppendFields.BATCH_IDS] = list(batch_ids)
        if len(batch_ids) == 1:
            shown[AppendFields.BATCH_ID] = batch_ids[0]
        if batch_ids:
            shown[AppendFields.NEXT_STEP] = UNDO_WITH
    elif mode is None:
        notes.append(NO_MODE_NO_BATCH.format(method.get(AppendFields.ERROR, "no reason given")))
    else:
        shown[AppendFields.NEXT_STEP] = NOTHING_TO_REMOVE
    other = report.get(AppendFields.UNMATCHED_BATCH_IDS)
    if other:
        notes.append(
            f"Batches {other} appeared in the dataset meanwhile and none names the uploaded"
            " file, so they are not listed in batch_ids and are not to be removed."
        )
    if report.get(AppendFields.BATCHES_ERROR):
        notes.append(
            f"The batches could not be read after the upload ({report[AppendFields.BATCHES_ERROR]}),"
            " so none is offered for removal."
        )
    if notes:
        shown[AppendFields.NOTES] = list(notes)
    return shown


def batch_mode_key(workspace_id: int, dataset_id: int, batch_id: int) -> str:
    """The store key of the mode one batch was added under."""
    return f"{workspace_id}:{dataset_id}:{batch_id}"


async def record_batch_modes(
    workspace_id: int, dataset_id: int, batch_ids: Sequence[int], mode: str
) -> None:
    """Keep the mode in effect when each batch was added, for `undo` to read back."""
    for batch_id in batch_ids:
        await remember(
            BATCH_MODE_KIND,
            batch_mode_key(workspace_id, dataset_id, batch_id),
            {AppendFields.MODE: mode},
            BATCH_MODE_SECONDS,
        )


async def recall_batch_modes(
    workspace_id: int, dataset_id: int, batch_ids: Sequence[int]
) -> dict[int, str | None]:
    """The mode each batch was recorded as added under; None where there is no record."""
    modes: dict[int, str | None] = {}
    for batch_id in batch_ids:
        record = await recall(BATCH_MODE_KIND, batch_mode_key(workspace_id, dataset_id, batch_id))
        stored = record.get(AppendFields.MODE) if record else None
        modes[batch_id] = stored if isinstance(stored, str) else None
    return modes


async def forget_batch_modes(workspace_id: int, dataset_id: int, batch_ids: Sequence[int]) -> None:
    """Drop the records of batches that were removed."""
    for batch_id in batch_ids:
        await forget(BATCH_MODE_KIND, batch_mode_key(workspace_id, dataset_id, batch_id))


async def report_append(workspace_id: int, report: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Record the mode each of an upload's batches was added under, and present the report."""
    method = report.get(AppendFields.UPDATE_METHOD)
    mode = method.get(AppendFields.MODE) if isinstance(method, dict) else None
    ours = report.get(AppendFields.BATCH_IDS)
    target = report.get(AppendFields.APPENDED_TO)
    if isinstance(mode, str) and isinstance(ours, list) and isinstance(target, int):
        await record_batch_modes(
            workspace_id, target, [batch for batch in ours if isinstance(batch, int)], mode
        )
    return present_append(report)


async def prepare_append(
    workspace_id: int, project_id: int, dataset_id: int, mode: Mode | None
) -> Plan:
    """Set the mode the files will run under, and read the dataset as it is before them.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: The dataset the files are added to.
        mode: "add" or "replace" to set, or None to keep what the dataset holds.

    Returns:
        The SDK's plan: plain data for `finish_append` and `restore_mode`.

    Raises:
        ToolError: If the dataset cannot be read or its mode cannot be set.
    """
    async with build_client(workspace_id, project_id) as client:
        plan = await read_sdk_errors(client.appends.prepare(dataset_id, mode))
    return dict(plan)


async def restore_mode(workspace_id: int, project_id: int, plan: Plan) -> str | None:
    """Put the dataset's mode back after the upload that needed it failed.

    Returns:
        None when nothing needed putting back or it was put back; otherwise a sentence
        saying the new mode stayed, for the error being raised.
    """
    async with build_client(workspace_id, project_id) as client:
        return await client.appends.restore_mode(plan)


async def finish_append(
    workspace_id: int, project_id: int, plan: Plan, file_names: list[str]
) -> dict[str, JsonValue]:
    """Wait for the rows to land in the dataset, then report what the upload did.

    The wait is bounded by the tool call's own clock, so a slow append is reported as
    pending, not hung on.
    """
    async with build_client(workspace_id, project_id) as client:
        report = await read_sdk_errors(
            client.appends.finish(
                plan,
                file_names,
                wait_seconds=min(APPEND_WAIT_SECONDS, seconds_left()),
                poll_seconds=APPEND_POLL_SECONDS,
            )
        )
    return await report_append(workspace_id, report)


async def append_file(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    file_name: str,
    content: bytes,
    mode: Mode | None,
) -> dict[str, JsonValue]:
    """Add one file's content to a dataset through the SDK's append, and report it.

    Raises:
        JobStillRunning: If the upload job outlasted the tool call. It keeps running, and
            reads the mode when the file lands, so the mode is not put back.
        ToolError: If Mammoth refuses; a mode this upload set that could not be put back
            is named in the message.
    """
    upload = io.BytesIO(content)
    upload.name = file_name
    timeout = max(1, int(seconds_left()))
    try:
        async with build_client(workspace_id, project_id) as client:
            outcome = await read_sdk_errors(
                client.appends.append(
                    upload,
                    dataset_id,
                    mode,
                    timeout=timeout,
                    wait_seconds=min(APPEND_WAIT_SECONDS, seconds_left()),
                    poll_seconds=APPEND_POLL_SECONDS,
                )
            )
    except ToolError as failed:
        cause = failed.__cause__
        if isinstance(cause, MammothJobTimeoutError):
            job_id = cause.details.get("job_id")
            raise JobStillRunning({JobFields.ID: job_id}, timeout) from cause
        kept = cause.details.get("update_method_kept") if isinstance(cause, MammothError) else None
        raise ToolError(f"{failed} {kept}" if kept else str(failed)) from failed
    return await report_append(workspace_id, outcome)


async def read_append_history(
    workspace_id: int, project_id: int, dataset_id: int
) -> dict[str, JsonValue]:
    """A dataset's update method and the batches it was built from.

    Returns:
        `update_method` (mode, effect, schema_mapping; `mode` is null with an `error` when it
        could not be read) and `batches`: each file or dataset added, with its `id` (what
        `undo` takes), source, and `removable`: whether `undo` will remove it.
    """
    async with build_client(workspace_id, project_id) as client:
        method = await client.appends.read_mode(dataset_id)
        rows = await read_sdk_errors(client.appends.list_batches(dataset_id))
    ids = [int(str(row["id"])) for row in rows]
    recorded = await recall_batch_modes(workspace_id, dataset_id, ids)
    batches: list[JsonValue] = []
    for row in rows:
        batch_id = int(str(row["id"]))
        removable = refuse_batch_removal([batch_id], recorded, ids) is None
        batches.append(
            {
                **{key: row[key] for key in AppendFields.BATCH_FIELDS if key in row},
                AppendFields.REMOVABLE: removable,
            }
        )
    return {
        AppendFields.UPDATE_METHOD: method,
        AppendFields.BATCHES: batches,
        PageFields.TOTAL: len(batches),
    }
