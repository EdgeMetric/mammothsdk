"""Add a file to an existing dataset, see what was added, and take it back.

A dataset has an update method (`data_addition_mode`, "Update Method" in the web
app): "add" puts a new file's rows under the rows it holds, "replace" throws the
old rows away and keeps the new ones. Every upload into the dataset follows it,
so an upload that names a target also names the mode, and the mode is set
before the files are sent: the backend reads it when the file lands.

Adding a file makes a batch, which is what can be removed again. Replacing makes
none worth removing: the old rows are gone. So this module keeps three things
apart and reports them: the mode the upload ran under, the rows before and
after, and the batches the upload added — told apart from batches that merely
appeared meanwhile (a folder automation, another user) by their source naming
the file that was sent.

The upload tools and `check_upload` share it. `request_upload` sends the file
later, from the browser, so what is read before the send travels in the ticket
as plain data (`prepare_append` returns it).
"""

import asyncio
import time
from pathlib import PurePosixPath
from typing import Literal

from mammoth.client import MammothClient
from mcp.server.mcpserver.exceptions import ToolError

from .consts import (
    APPEND_POLL_SECONDS,
    APPEND_WAIT_SECONDS,
    BATCH_PAGE,
    ApiFields,
    AppendFields,
    DatasetStatus,
    ListFields,
    PageFields,
)
from .deadline import seconds_left
from .sdk import JsonValue, build_client, read_sdk_errors

type Mode = Literal["add", "replace"]
type Plan = dict[str, JsonValue]

# The words a caller uses, and the names the platform stores them under.
STORED_MODE: dict[str, str] = {"add": "combine", "replace": "replace"}
EFFECTS: dict[str, str] = {
    "add": "Each new file adds its rows to the rows the dataset holds.",
    "replace": "Each new file replaces the rows the dataset holds.",
}
# A status in which the dataset is no longer taking rows in.
SETTLED = {DatasetStatus.READY, DatasetStatus.PROCESSED, DatasetStatus.EMPTY}
NOT_AN_APPEND = (
    "`mode` only applies together with `append_to_dataset_id`: it sets the update method"
    " of the dataset the file goes into."
)
UNDO_WITH = (
    'To take this back, ask the user, then call undo with what="batch", this dataset_id'
    " and these batch_ids."
)
NOTHING_TO_REMOVE = (
    "The dataset replaces its rows, so the old rows are gone and there is no batch to remove."
    " To get them back, upload the old file again."
)
NO_BATCH_TO_REMOVE = "The update method is replace: no batch of this dataset can be removed."


def word_of(stored: JsonValue) -> Mode:
    """The caller's word for a stored mode; a dataset with none stored adds, as the platform does."""
    return "replace" if stored == STORED_MODE["replace"] else "add"


def describe_update_method(settings: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Say what a dataset's stored settings mean for the next file.

    Args:
        settings: What `DatasetsAPI.get_update_method` returned; empty for a
            dataset that has none stored.

    Returns:
        The `mode` ("add" or "replace"), its `effect` in words, and the
        `schema_mapping` that matches a file's columns to the dataset's.
    """
    mode = word_of(settings.get(AppendFields.DATA_ADDITION_MODE))
    return {
        "mode": mode,
        AppendFields.EFFECT: EFFECTS[mode],
        AppendFields.SCHEMA_MAPPING: settings.get(AppendFields.SCHEMA_MAPPING),
    }


def sent_labels(file_names: list[str]) -> set[str]:
    """The lower-case names a batch's source can carry for files that were sent."""
    names = {PurePosixPath(name).name.lower() for name in file_names}
    return names | {PurePosixPath(name).stem.lower() for name in names}


def batch_labels(row: dict[str, JsonValue]) -> set[str]:
    """The lower-case names a batch row carries for its source."""
    source = row.get(AppendFields.SOURCE)
    holders = [source if isinstance(source, dict) else {}, row]
    labels = [holder.get(key) for holder in holders for key in AppendFields.SOURCE_NAMES]
    names = {PurePosixPath(label).name.lower() for label in labels if isinstance(label, str)}
    return names | {PurePosixPath(name).stem for name in names}


def find_new_batches(
    before_ids: list[int], after: list[dict[str, JsonValue]], file_names: list[str]
) -> tuple[list[int], list[int]]:
    """Tell the batches an upload added from the ones that appeared meanwhile.

    A new batch is the upload's only when its source names a file that was sent.
    Any other new batch is returned apart and never offered for removal: it may
    be another user's.

    Args:
        before_ids: The ids of the dataset's batches before the files were sent.
        after: The batch rows now.
        file_names: The names of the files that were sent.

    Returns:
        `(ids of this upload's batches, ids of new batches not tied to it)`.
    """
    known = set(before_ids)
    wanted = sent_labels(file_names)
    ours: list[int] = []
    other: list[int] = []
    for row in after:
        batch_id = row.get("id")
        if not isinstance(batch_id, int) or batch_id in known:
            continue
        (ours if batch_labels(row) & wanted else other).append(batch_id)
    return ours, other


def rows_of(response: dict[str, JsonValue]) -> int | None:
    """The row count a dataset read holds, or None when it holds none."""
    dataset = response.get(ListFields.DATASET, response)
    stats = dataset.get(AppendFields.STATS) if isinstance(dataset, dict) else None
    rows = stats.get(AppendFields.ROW_COUNT) if isinstance(stats, dict) else None
    return rows if isinstance(rows, int) else None


async def read_rows(
    client: MammothClient, workspace_id: int, project_id: int, dataset_id: int
) -> dict[str, JsonValue]:
    """Read a dataset with its status and row counts."""
    return await read_sdk_errors(
        client.datasets.get(
            dataset_id,
            workspace_id=workspace_id,
            project_id=project_id,
            fields=ApiFields.STANDARD,
        )
    )


def status_of(response: dict[str, JsonValue]) -> str | None:
    """The status a dataset read holds, or None when it holds none."""
    dataset = response.get(ListFields.DATASET, response)
    status = dataset.get("status") if isinstance(dataset, dict) else None
    return status if isinstance(status, str) else None


def describe_append(
    plan: Plan,
    rows_after: int | None,
    ours: list[int],
    other: list[int],
    settled: bool,
) -> dict[str, JsonValue]:
    """Report what an upload into a dataset did, and what can be done about it.

    Args:
        plan: What `prepare_append` read before the files were sent.
        rows_after: The dataset's rows now, or None when they could not be read.
        ours: The batches this upload added.
        other: New batches that could not be tied to this upload.
        settled: Whether the dataset had taken the rows in by the time it was read.

    Returns:
        `appended_to`, the `update_method` the upload ran under, the rows before
        and after with `rows_added` (negative when a replace shrank the dataset),
        and for an "add" the `batch_ids` to remove. A "replace" offers none.
    """
    mode = str(plan[AppendFields.UPDATE_METHOD])
    before = plan[AppendFields.ROWS_BEFORE]
    report: dict[str, JsonValue] = {
        AppendFields.APPENDED_TO: plan[AppendFields.TARGET],
        AppendFields.UPDATE_METHOD: mode,
        AppendFields.EFFECT: EFFECTS[mode],
    }
    notes: list[str] = []
    if plan.get(AppendFields.MODE_CHANGED):
        notes.append(
            f"The dataset's update method was {plan[AppendFields.PREVIOUS_MODE]} and is now"
            f" {mode}. It stays: every later upload into it follows it too."
        )
    if isinstance(before, int) and rows_after is not None:
        report[AppendFields.ROWS_BEFORE] = before
        report[AppendFields.ROWS_AFTER] = rows_after
        report[AppendFields.ROWS_ADDED] = rows_after - before
    if not settled:
        report[AppendFields.APPEND_PENDING] = True
        notes.append(
            "The dataset was still taking the rows in, so rows_added is what had landed. Call"
            " check_upload again, or get_dataset, before using it."
        )
    if mode == "replace":
        report[AppendFields.NEXT_STEP] = NOTHING_TO_REMOVE
    else:
        report[AppendFields.BATCH_IDS] = list(ours)
        if len(ours) == 1:
            report[AppendFields.BATCH_ID] = ours[0]
        report[AppendFields.NEXT_STEP] = UNDO_WITH if ours else None
    if other:
        report[AppendFields.UNMATCHED_BATCH_IDS] = list(other)
        notes.append(
            f"Batches {other} appeared in the dataset meanwhile and none names the uploaded"
            " file, so they are not listed in batch_ids and are not to be removed."
        )
    if notes:
        report[AppendFields.NOTES] = list(notes)
    return {key: value for key, value in report.items() if value is not None}


async def prepare_append(
    workspace_id: int, project_id: int, dataset_id: int, mode: Mode | None
) -> Plan:
    """Set the mode the files will run under, and read the dataset as it is before them.

    The mode is set before the files are sent, because the backend reads it when
    they land. Nothing is changed when `mode` is left out: the stored mode is
    read, so the report can say which one the upload ran under.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: The dataset the files are added to.
        mode: "add" or "replace" to set, or None to keep what the dataset holds.

    Returns:
        Plain data for `describe_append`: the target, the mode the upload runs
        under, the mode it had (when this changed it), the rows and the batch
        ids it had.

    Raises:
        ToolError: If the dataset cannot be read or its mode cannot be set.
    """
    async with build_client(workspace_id, project_id) as client:
        stored = await read_sdk_errors(
            client.datasets.get_update_method(
                dataset_id, workspace_id=workspace_id, project_id=project_id
            )
        )
        previous = word_of(stored.get(AppendFields.DATA_ADDITION_MODE))
        changed = mode is not None and mode != previous
        if mode is not None and changed:
            await read_sdk_errors(
                client.datasets.set_update_method(
                    dataset_id,
                    STORED_MODE[mode],
                    workspace_id=workspace_id,
                    project_id=project_id,
                )
            )
        read = await read_rows(client, workspace_id, project_id, dataset_id)
        batches = await list_batches(workspace_id, project_id, dataset_id)
    return {
        AppendFields.TARGET: dataset_id,
        AppendFields.UPDATE_METHOD: mode or previous,
        AppendFields.MODE_CHANGED: changed,
        AppendFields.PREVIOUS_MODE: previous,
        AppendFields.ROWS_BEFORE: rows_of(read),
        AppendFields.BATCH_IDS_BEFORE: [int(str(row["id"])) for row in batches],
    }


async def restore_mode(workspace_id: int, project_id: int, plan: Plan) -> str | None:
    """Put the dataset's mode back after the upload that needed it failed.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        plan: What `prepare_append` returned.

    Returns:
        None when nothing needed putting back or it was put back; otherwise a
        sentence saying the new mode stayed, for the error being raised.
    """
    if not plan.get(AppendFields.MODE_CHANGED):
        return None
    dataset_id = int(str(plan[AppendFields.TARGET]))
    try:
        async with build_client(workspace_id, project_id) as client:
            await read_sdk_errors(
                client.datasets.set_update_method(
                    dataset_id,
                    STORED_MODE[str(plan[AppendFields.PREVIOUS_MODE])],
                    workspace_id=workspace_id,
                    project_id=project_id,
                )
            )
    except ToolError as failed:
        return (
            f"Dataset {dataset_id} kept the update method {plan[AppendFields.UPDATE_METHOD]}"
            f" this upload gave it, because the old one could not be restored ({failed})."
        )
    return None


async def list_batches(
    workspace_id: int, project_id: int, dataset_id: int
) -> list[dict[str, JsonValue]]:
    """Every batch of a dataset, in listing order, paging through the listing."""
    found: list[dict[str, JsonValue]] = []
    offset = 0
    async with build_client(workspace_id, project_id) as client:
        while True:
            page = await read_sdk_errors(
                client.batches.list(
                    dataset_id, project_id=project_id, limit=BATCH_PAGE, offset=offset
                )
            )
            rows = page.get(AppendFields.BATCHES)
            rows = rows if isinstance(rows, list) else []
            known = {row["id"] for row in found}
            found.extend(
                row
                for row in rows
                if isinstance(row, dict)
                and isinstance(row.get("id"), int)
                and row["id"] not in known
            )
            if len(rows) < BATCH_PAGE:
                return found
            offset += BATCH_PAGE


async def read_append_history(
    workspace_id: int, project_id: int, dataset_id: int
) -> dict[str, JsonValue]:
    """A dataset's update method and the batches it was built from.

    Returns:
        `update_method` (mode, effect, schema_mapping) and `batches`: each
        file or dataset added, with its `id` (what `undo` takes) and source.
    """
    async with build_client(workspace_id, project_id) as client:
        stored = await read_sdk_errors(
            client.datasets.get_update_method(
                dataset_id, workspace_id=workspace_id, project_id=project_id
            )
        )
    rows = await list_batches(workspace_id, project_id, dataset_id)
    batches: list[JsonValue] = [
        {key: row[key] for key in AppendFields.BATCH_FIELDS if key in row} for row in rows
    ]
    return {
        AppendFields.UPDATE_METHOD: describe_update_method(stored),
        AppendFields.BATCHES: batches,
        PageFields.TOTAL: len(batches),
    }


async def finish_append(
    workspace_id: int, project_id: int, plan: Plan, file_names: list[str]
) -> dict[str, JsonValue]:
    """Wait for the rows to land in the dataset, then report what the upload did.

    The upload's job ends when its staging dataset is made; the rows reach the
    target after that, while it reads "processing". The wait is bounded by the
    tool call's own clock, so a slow append is reported as pending, not hung on.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        plan: What `prepare_append` returned before the files were sent.
        file_names: The names of the files that were sent.

    Returns:
        What `describe_append` reports.
    """
    dataset_id = int(str(plan[AppendFields.TARGET]))
    give_up_at = time.monotonic() + min(APPEND_WAIT_SECONDS, seconds_left())
    async with build_client(workspace_id, project_id) as client:
        while True:
            read = await read_rows(client, workspace_id, project_id, dataset_id)
            settled = status_of(read) in SETTLED
            if settled or time.monotonic() >= give_up_at:
                break
            await asyncio.sleep(APPEND_POLL_SECONDS)
    after = await list_batches(workspace_id, project_id, dataset_id)
    known = plan[AppendFields.BATCH_IDS_BEFORE]
    before_ids = [int(str(batch_id)) for batch_id in known] if isinstance(known, list) else []
    ours, other = find_new_batches(before_ids, after, file_names)
    return describe_append(plan, rows_of(read), ours, other, settled)
