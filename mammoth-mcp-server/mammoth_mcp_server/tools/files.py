"""Bring data into Mammoth as a file, and manage the files a project holds.

There are two ways in, and the size of the file picks between them. A tool
argument carries text, never binary, so `upload_file` takes the content the
model has — a CSV it wrote, or one the user pasted — and every row of it costs
tokens twice. Anything larger, or binary, goes through `request_upload`
(`upload_app`): the user drops the file on an uploader in the chat, or opens a
link, and the browser sends it, so the bytes never enter the conversation.
"""

import asyncio
import time
from pathlib import PurePosixPath
from typing import Literal

from mammoth.client import MammothClient
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import (
    DISCARD_READS,
    LIST_LIMIT_DEFAULT,
    PREVIEW_ROWS_DEFAULT,
    UPLOAD_MEDIA_TYPES,
    UPLOAD_POLL_SECONDS,
    UPLOAD_WAIT_SECONDS,
    ApiFields,
    ApiPaths,
    ColumnFields,
    FilePatchFields,
    FileSettingsFields,
    InterpretationFields,
    JobFields,
    UnstructuredFields,
    UploadFields,
)
from ..jobs import find_job_id, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors, request_api
from ..server import mcp_server
from ..store import Record
from ..tool_kinds import CHANGES, DESTRUCTIVE, READS
from ..upload_report import report_upload
from ..upload_tickets import read_ticket

type DateFormat = Literal["US", "UK"]


@mcp_server.tool(title="Upload file", annotations=CHANGES)
async def upload_file(
    workspace_id: int, project_id: int, file_name: str, content: str
) -> dict[str, JsonValue]:
    """Create a dataset in a project from text you have.

    Use this to bring a table into Mammoth: write the rows as CSV and upload
    them. Waits for Mammoth to read the file, so the dataset exists when this
    returns. To read an existing dataset instead, use `list_datasets`.

    Only for text you already hold, and only up to a few megabytes of it: the
    content travels through this conversation, so every row costs tokens twice.
    For a file on the user's own machine — a spreadsheet, a large CSV, anything
    binary — use `request_upload` instead.

    Args:
        workspace_id: Which workspace to upload into.
        project_id: Which project to upload into.
        file_name: Name of the file, ending in .csv, .tsv, .json or .txt.
        content: The file's content, for example "name,amount\\nfoo,1\\n".

    Returns:
        What Mammoth made of the file, including the dataset it created.
    """
    async with build_client(workspace_id, project_id) as client:
        started = await request_api(
            client,
            "POST",
            ApiPaths.FILES.format(workspace_id=workspace_id, project_id=project_id),
            upload=[(file_name, content.encode(), find_media_type(file_name))],
        )
    return await wait_for_job(workspace_id, started)


async def wait_for_the_file(upload_id: str) -> Record:
    """The upload's ticket, once the user's file has reached Mammoth.

    Holds the call while they are still choosing, because answering at once
    ends the model's turn and only the user can start another one. The wait is
    bounded: a user who never comes back gets a ticket with no job on it, and
    the tool says `waiting` rather than hanging.

    Args:
        upload_id: What `request_upload` returned.

    Returns:
        The ticket, with a job on it if the file arrived in time.

    Raises:
        ToolError: If the link was never minted, or has expired.
    """
    give_up_at = time.monotonic() + UPLOAD_WAIT_SECONDS
    while True:
        ticket = await read_ticket(upload_id)
        if ticket is None:
            raise ToolError("That upload link has expired. Call request_upload for a new one.")
        if ticket.get(UploadFields.JOB_ID) is not None or time.monotonic() >= give_up_at:
            return ticket
        await asyncio.sleep(UPLOAD_POLL_SECONDS)


@mcp_server.tool(title="Check upload", annotations=READS)
async def check_upload(upload_id: str) -> dict[str, JsonValue]:
    """Wait for the user to upload their files, and report what came of them.

    Call this straight after `request_upload`. It waits while they find the
    file, so do not end your turn asking them to tell you when they are done —
    they already asked you to get on with it. The uploader in the chat calls it
    too, before it tells you.

    `waiting` means they had not picked a file by the time the wait ran out.
    Call again if you have reason to think they are still coming; after a
    couple of rounds say you are waiting, rather than polling in silence.

    Args:
        upload_id: What `request_upload` returned.

    Returns:
        `status`: `waiting` (nothing uploaded yet), `processing` (Mammoth is
        still reading them) or `done`. With the last two, `files`: every file
        and dataset the upload made. A dataset that is ready carries `view_id`:
        read, transform and build dashboards on that view. An item Mammoth cannot finish without the
        user carries `needs`: the `action`, the `next_step` to take, and
        whatever that step needs — the `sheets` to choose from, or the
        `summary` of what could not be decided and the `suggested_instructions`
        that would answer it. Follow `next_step`: each one is settled from here
        without the user opening Mammoth. Put every one of them to the user in
        one message and wait for their answer — the choice is theirs, and
        guessing it spoils the data quietly. Several files can wait on
        different things. `rejected`: files Mammoth refused.
    """
    ticket = await wait_for_the_file(upload_id)
    job_id = ticket.get(UploadFields.JOB_ID)
    if job_id is None:
        return {
            UploadFields.STATUS: UploadFields.WAITING,
            UploadFields.FILE_NAMES: ticket.get(UploadFields.FILE_NAMES),
        }
    # Read the job as the polling user, so Mammoth refuses an upload that is
    # not theirs exactly as it would refuse any other job of a stranger's.
    started = await wait_for_job(int(ticket[UploadFields.WORKSPACE_ID]), {JobFields.JOB_ID: job_id})
    report = await report_upload(ticket)
    if started.get(UploadFields.ERRORS):
        report[UploadFields.REJECTED] = started[UploadFields.ERRORS]
    return report


@mcp_server.tool(title="Extract sheets", annotations=CHANGES)
async def extract_sheets(
    workspace_id: int, project_id: int, file_id: int, sheets: list[str]
) -> dict[str, JsonValue]:
    """Bring the chosen sheets of an uploaded workbook in, one dataset each.

    Only for a file `check_upload` reports as needing `sheet_selection_required`.
    Ask the user which of its `sheets` they want first. Then call `check_upload`
    again with the same `upload_id` to see the datasets the sheets became.

    Args:
        workspace_id: Which workspace the file is in.
        project_id: Which project the file is in.
        file_id: The workbook, as `check_upload` reported it.
        sheets: The names of the sheets to bring in.
    """
    named: list[JsonValue] = list(sheets)
    return await patch_file(
        FilePatchFields.EXTRACT_SHEETS,
        {FilePatchFields.SHEETS: named},
        workspace_id=workspace_id,
        project_id=project_id,
        file_id=file_id,
    )


@mcp_server.tool(title="Unlock file", annotations=CHANGES)
async def unlock_file(
    workspace_id: int, project_id: int, file_id: int, password: str
) -> dict[str, JsonValue]:
    """Open a file that is password protected, so Mammoth can read it.

    Only for a file `check_upload` reports as needing `password_required`.

    Give the user the choice first, in as many words: tell you the password
    here, or open `mammoth_url` and enter it in Mammoth. Whatever they type
    into this conversation is stored with it and read back by a model; what
    they type into Mammoth is not. Never guess a password, never repeat one
    back, and do not press them to use this rather than the web app.

    A wrong password is refused and nothing changes, so it can be tried again.

    Args:
        workspace_id: Which workspace the file is in.
        project_id: Which project the file is in.
        file_id: The locked file, as `check_upload` reported it.
        password: The password, exactly as the user gave it.
    """
    return await patch_file(
        FilePatchFields.PASSWORD,
        password,
        workspace_id=workspace_id,
        project_id=project_id,
        file_id=file_id,
    )


async def patch_file(
    path: str,
    value: JsonValue,
    *,
    workspace_id: int,
    project_id: int,
    file_id: int,
) -> dict[str, JsonValue]:
    """Change one thing about an uploaded file, and wait for Mammoth to reread it.

    Every one of these settles something the file stopped on, so each starts a
    job and the answer is that job's — never the patch's.
    """
    async with build_client(workspace_id, project_id) as client:
        started = await request_api(
            client,
            "PATCH",
            ApiPaths.FILE.format(workspace_id=workspace_id, project_id=project_id, file_id=file_id),
            body={
                FilePatchFields.PATCH: [
                    {
                        FilePatchFields.OP: FilePatchFields.REPLACE,
                        FilePatchFields.PATH: path,
                        FilePatchFields.VALUE: value,
                    }
                ]
            },
        )
    return await wait_for_job(workspace_id, started)


@mcp_server.tool(title="Interpret file", annotations=CHANGES)
async def interpret_file(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    instruction: str,
    apply: bool = False,
) -> dict[str, JsonValue]:
    """Say how a file is meant to be read, when Mammoth found more than one way.

    Only for a dataset `check_upload` reports as needing `unstructured_rows`
    with a `summary`. Mammoth could not tell where the table starts — a title
    sits above it, the header runs over two rows, one sheet holds several
    tables — and it will not guess, because guessing wrong quietly throws rows
    away. The instruction is plain English: "the header is on row 4", "skip the
    first three lines", "there is one table per region, stacked".

    Call it with `apply` false first and show the user the rows it returns:
    only they can say whether the file now reads the way they meant. Then call
    it again with the same instruction and `apply` true, and carry on with what
    they originally asked for.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: The dataset, as `check_upload` reported it.
        instruction: How the file is meant to be read, in the user's own
            words. `suggested_instructions` are Mammoth's own wording for it.
        apply: Read the whole file this way and finish the dataset. Leave it
            false to see the first rows first.

    Returns:
        `preview_rows`: the first rows as the dataset would hold them, the
        header first. `total_row_count`: how many rows the whole file makes
        this way. `applied`: whether the dataset was finished with it.

    Raises:
        ToolError: If Mammoth will not read the file that way, with its reason.
            Put that to the user and ask them to say it another way.
    """
    ids = {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "dataset_id": dataset_id,
    }
    async with build_client(workspace_id) as client:
        preview = await read_sdk_errors(
            client.datasets.preview_interpretation(dataset_id, instruction, project_id=project_id)
        )
    read = read_preview(preview)
    if not apply:
        return read
    await apply_interpretation(ids, instruction)
    return {**read, InterpretationFields.APPLIED: True}


def read_preview(preview: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The rows an instruction makes, or why Mammoth will not read a file so.

    A refusal arrives as an ordinary answer with the verdict where the plan
    should be and no rows, so it is read rather than passed on as an empty
    file. Only the first rows are kept: the user is deciding whether the table
    now starts in the right place, not reading the data.

    Raises:
        ToolError: If Mammoth refused the instruction.
    """
    plan = preview.get(InterpretationFields.STRUCTURE_MAP)
    plan = plan if isinstance(plan, dict) else {}
    if not plan.get(InterpretationFields.IN_SCOPE, True) or not plan.get(
        InterpretationFields.COMPATIBLE, True
    ):
        raise ToolError(
            "Mammoth will not read the file that way:" f" {plan.get(InterpretationFields.REFUSED)}"
        )
    rows = preview.get(InterpretationFields.ROWS)
    return {
        InterpretationFields.ROWS: (
            rows[: PREVIEW_ROWS_DEFAULT + 1] if isinstance(rows, list) else rows
        ),
        InterpretationFields.TOTAL_ROWS: preview.get(InterpretationFields.TOTAL_ROWS),
        InterpretationFields.APPLIED: False,
    }


async def apply_interpretation(ids: dict[str, int], instruction: str) -> None:
    """Read the whole file the way the preview just read its first rows.

    The plan itself is not sent back. The route never trusts a client's copy of
    one — it carries SQL, which would then run unchecked — so it re-reads the
    plan the preview saved, and only this field's presence chooses that over
    working the instruction out again, which would not answer identically.
    """
    async with build_client(ids["workspace_id"]) as client:
        await read_sdk_errors(
            client.datasets.confirm_interpretation(
                ids["dataset_id"], instruction, project_id=ids["project_id"]
            )
        )


@mcp_server.tool(title="Review unreadable rows", annotations=DESTRUCTIVE)
async def review_unreadable_rows(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    discard: bool = False,
) -> dict[str, JsonValue]:
    """Show the lines of a file that did not fit, and discard them on request.

    For a dataset `check_upload` reports as needing `unstructured_rows` with no
    `interpretation_summary` beside it. Mammoth read the file, and some lines
    would not go into the dataset it built: a line carrying more fields than
    the header, or a value the column's type refuses. Those lines are set
    aside rather than dropped, and the dataset waits with them.

    Call it with no `discard` first. It changes nothing and answers with the
    rows and the reason each was set aside. Show the user every row — they are
    the only one who knows whether a line matters — and ask whether to discard
    them. Call it again with `discard` only if they say so.

    A row they want to keep cannot be repaired here: correcting a line is the
    web app's, at `mammoth_url`. Say so rather than discarding it for them.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: The dataset, as `check_upload` reported it.
        discard: Throw the set-aside lines away and finish the dataset with
            the rows that did fit. This cannot be undone.

    Returns:
        Without `discard`: `unstructured_rows`, each with its `line`,
        `line_num` and the `reason` it did not fit, and `row_count`, which is
        how many there are in all — more than the rows returned, when the file
        set many aside. With `discard`: `rows_deleted`.
    """
    async with build_client(workspace_id) as client:
        if discard:
            return await discard_unreadable_rows(client, project_id, dataset_id)
        return read_unreadable_rows(
            await read_sdk_errors(
                client.datasets.get_unstructured_rows(dataset_id, project_id=project_id)
            )
        )


async def discard_unreadable_rows(
    client: MammothClient, project_id: int, dataset_id: int
) -> dict[str, JsonValue]:
    """Discard every set-aside line, and say how many went.

    A read returns the first lines only, and the API discards the lines it is
    given, so this reads and discards until a read brings nothing new.
    """
    gone: set[tuple[int, int]] = set()
    for _ in range(DISCARD_READS):
        found = await read_sdk_errors(
            client.datasets.get_unstructured_rows(dataset_id, project_id=project_id)
        )
        waiting = group_lines_by_batch(found.get(UnstructuredFields.ROWS), gone)
        if not waiting:
            break
        for batch_id, lines in waiting.items():
            started = await read_sdk_errors(
                client.datasets.resolve_unstructured_rows(
                    dataset_id, "remove", batch_id, lines, project_id=project_id
                )
            )
            await read_sdk_errors(client.jobs.wait_for_job(find_job_id(started)))
            gone.update(
                (batch_id, int(str(line[UnstructuredFields.LINE_NUMBER]))) for line in lines
            )
    return {UnstructuredFields.DELETED: len(gone), UnstructuredFields.DISCARDED: True}


def group_lines_by_batch(
    rows: JsonValue, gone: set[tuple[int, int]]
) -> dict[int, list[dict[str, JsonValue]]]:
    """The set-aside lines not discarded yet, under the upload each came from.

    A read made straight after a discard can still show the lines that went.
    """
    waiting: dict[int, list[dict[str, JsonValue]]] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        batch_id = int(str(row[UnstructuredFields.BATCH_ID]))
        line_number = int(str(row[UnstructuredFields.LINE_NUMBER]))
        if (batch_id, line_number) in gone:
            continue
        waiting.setdefault(batch_id, []).append(
            {
                UnstructuredFields.LINE_NUMBER: line_number,
                UnstructuredFields.LINE: row[UnstructuredFields.LINE],
            }
        )
    return waiting


def read_unreadable_rows(found: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The set-aside lines, capped, with what they cost still reported.

    A file can set thousands of lines aside, and every one of them would go
    through the conversation. The user is deciding whether to keep any of
    them, which the first few and the true count answer.
    """
    rows = found.get(UnstructuredFields.ROWS)
    return {
        UnstructuredFields.ROWS: (rows[:PREVIEW_ROWS_DEFAULT] if isinstance(rows, list) else rows),
        UnstructuredFields.ROW_COUNT: found.get(UnstructuredFields.ROW_COUNT),
        UnstructuredFields.DISCARDED: False,
    }


@mcp_server.tool(title="Set date format", annotations=CHANGES)
async def set_date_format(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    date_format: DateFormat | None = None,
    columns: dict[str, DateFormat] | None = None,
    for_the_whole_project: bool = False,
) -> dict[str, JsonValue]:
    """Say which way round a file's dates read, and finish the dataset.

    For a dataset waiting on this: one `check_upload` reports as needing
    `ambiguous_date_format`, or one `get_dataset` shows with the status
    `need_action`. A date column whose every value fits both orders stops the
    file: 01/02/2026 is 2 January read as `US` (MM/DD/YYYY) and 1 February read
    as `UK` (DD/MM/YYYY). Mammoth will not guess, because guessing wrong moves
    every date in the file and says nothing.

    Call it with no format first. It answers with `date_columns`, the columns
    waiting to be told, and changes nothing. Name them to the user and ask:
    only they know where the file came from, and the values cannot settle it —
    if they could, Mammoth would have read them already. Then call it again
    with their answer and carry on with what they first asked for.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: The dataset, as `check_upload` reported it.
        date_format: `US` or `UK`, for every one of the file's date columns.
        columns: A format for single columns, by the display name
            `date_columns` gives, for a file whose columns disagree — one put
            together from two systems can hold a column of each. Beats
            `date_format`, and may be given instead of it or with it.
        for_the_whole_project: Make this the project's own default too, so
            later uploads are never asked about it. Only with `date_format`,
            and only when the user says so: it outlives this file.

    Returns:
        With no format, `date_columns` and `applied` false. Otherwise the
        reread dataset, and `applied` true.
    """
    path = ApiPaths.FILE_SETTINGS.format(
        workspace_id=workspace_id, project_id=project_id, dataset_id=dataset_id
    )
    async with build_client(workspace_id, project_id) as client:
        return await change_date_format(
            client,
            path,
            dataset_id,
            date_format=date_format,
            columns=columns,
            for_the_whole_project=for_the_whole_project,
        )


async def change_date_format(
    client: MammothClient,
    path: str,
    dataset_id: int,
    *,
    date_format: DateFormat | None,
    columns: dict[str, DateFormat] | None,
    for_the_whole_project: bool,
) -> dict[str, JsonValue]:
    """Report the date columns waiting to be told, or tell them and reread the file."""
    settings = await read_file_settings(client, path, dataset_id)
    date_columns = find_date_columns(settings)
    if date_format is None and not columns:
        waiting: list[JsonValue] = [str(name) for name in sorted(date_columns)]
        return {
            FileSettingsFields.AMBIGUOUS_COLUMNS: waiting,
            FileSettingsFields.APPLIED: False,
        }
    per_column: dict[str, JsonValue] = {
        **already_set(settings),
        **name_the_columns(columns, date_columns),
    }
    body: dict[str, JsonValue] = {key: settings.get(key) for key in FileSettingsFields.KEPT}
    body[FileSettingsFields.DATE_FORMAT] = date_format
    body[FileSettingsFields.DATE_FORMATS] = per_column or None
    body[FileSettingsFields.PROJECT_DEFAULT] = for_the_whole_project
    started = await request_api(client, "POST", path, body=body)
    return {
        **await wait_for_job(client.workspace_id, started),
        FileSettingsFields.APPLIED: True,
    }


async def read_file_settings(
    client: MammothClient, path: str, dataset_id: int
) -> dict[str, JsonValue]:
    """How Mammoth read this dataset's file, as it must be sent back to change it.

    Raises:
        ToolError: If the dataset was not made from a file, so there is nothing
            to read it differently.
    """
    read = await request_api(client, "GET", path)
    settings = read.get(FileSettingsFields.INFO)
    if not isinstance(settings, dict):
        raise ToolError(f"Mammoth has no file settings for dataset {dataset_id}.")
    return settings


def list_date_columns(settings: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """The file's date columns, as the settings list them, and nothing else."""
    listed = settings.get(FileSettingsFields.DATE_COLUMNS)
    if not isinstance(listed, list):
        return []
    return [
        column
        for column in listed
        if isinstance(column, dict) and ColumnFields.INTERNAL_NAME in column
    ]


def find_date_columns(settings: dict[str, JsonValue]) -> dict[str, str]:
    """The date columns the user may set: display name to the route's own name."""
    return {
        str(column.get(ColumnFields.DISPLAY_NAME)): str(column[ColumnFields.INTERNAL_NAME])
        for column in list_date_columns(settings)
    }


def already_set(settings: dict[str, JsonValue]) -> dict[str, str]:
    """The columns somebody has already answered for, which a new call keeps.

    The route takes every per-column choice each time and forgets the ones left
    out, so an answer given in the web app would be undone by an answer given
    here about a different column.
    """
    settled: dict[str, str] = {}
    for column in list_date_columns(settings):
        chosen = column.get(ColumnFields.FORMAT)
        if isinstance(chosen, dict) and chosen.get(ColumnFields.DATE_FORMAT_TYPE):
            settled[str(column[ColumnFields.INTERNAL_NAME])] = str(
                chosen[ColumnFields.DATE_FORMAT_TYPE]
            )
    return settled


def name_the_columns(
    columns: dict[str, DateFormat] | None, date_columns: dict[str, str]
) -> dict[str, str]:
    """Put the user's column names into the names the route knows them by.

    Raises:
        ToolError: If a column named is not one of the file's date columns,
            which is how a display name the model guessed is caught rather than
            quietly setting nothing.
    """
    unknown = sorted(set(columns or {}) - set(date_columns))
    if unknown:
        raise ToolError(
            f"This file has no date column called {', '.join(unknown)}. Its date"
            f" columns are: {', '.join(sorted(date_columns)) or 'none'}."
        )
    return {date_columns[name]: chosen for name, chosen in (columns or {}).items()}


def find_media_type(file_name: str) -> str:
    """Return the media type of a file a tool may upload.

    Raises:
        ToolError: If Mammoth cannot read that kind of file from text.
    """
    media_type = UPLOAD_MEDIA_TYPES.get(PurePosixPath(file_name).suffix.lower())
    if media_type is None:
        raise ToolError(
            f"Cannot upload '{file_name}'. Upload one of:"
            f" {', '.join(UPLOAD_MEDIA_TYPES)}. Any other kind of file has to be"
            " uploaded in the Mammoth web app."
        )
    return media_type


@mcp_server.tool(title="List files", annotations=READS)
async def list_files(
    workspace_id: int,
    project_id: int,
    limit: int = LIST_LIMIT_DEFAULT,
    offset: int = 0,
) -> dict[str, JsonValue]:
    """List the files uploaded to a project.

    A file is what was uploaded; the dataset is what Mammoth made of it.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project to look in.
        limit: How many files to return.
        offset: How many files to skip, for paging.
    """
    async with build_client(workspace_id, project_id) as client:
        return await request_api(
            client,
            "GET",
            ApiPaths.FILES.format(workspace_id=workspace_id, project_id=project_id),
            query={
                ApiFields.FIELDS: ApiFields.MINIMAL,
                "limit": limit,
                "offset": offset,
            },
        )


@mcp_server.tool(title="Get file", annotations=READS)
async def get_file(workspace_id: int, project_id: int, file_id: int) -> dict[str, JsonValue]:
    """Get one file, with its status and what Mammoth read from it.

    Args:
        workspace_id: Which workspace the file is in.
        project_id: Which project the file is in.
        file_id: Which file to read.

    Returns:
        The file, under the key `file`.
    """
    async with build_client(workspace_id, project_id) as client:
        return await request_api(
            client,
            "GET",
            ApiPaths.FILE.format(workspace_id=workspace_id, project_id=project_id, file_id=file_id),
            query={ApiFields.FIELDS: ApiFields.STANDARD},
        )


@mcp_server.tool(title="Delete file", annotations=DESTRUCTIVE)
async def delete_file(workspace_id: int, project_id: int, file_id: int) -> dict[str, JsonValue]:
    """Delete a file from a project.

    The dataset Mammoth made from the file is deleted with it. Ask the user
    before calling this: it cannot be undone from here.

    Args:
        workspace_id: Which workspace the file is in.
        project_id: Which project the file is in.
        file_id: Which file to delete.
    """
    async with build_client(workspace_id, project_id) as client:
        started = await request_api(
            client,
            "DELETE",
            ApiPaths.FILE.format(workspace_id=workspace_id, project_id=project_id, file_id=file_id),
        )
    return await wait_for_job(workspace_id, started)
