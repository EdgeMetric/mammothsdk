"""What came of an upload: the files and datasets it made, and what each waits on.

Mammoth reads an upload in steps that end at different times, and some end
waiting for the user: a workbook asks which sheets to bring in, a column of
dates that reads either way asks whether it is US or UK, a sheet with a title
above the table asks where the table starts, a locked file asks for its
password. The upload's job resolves before most of that — the Excel path
resolves it before it has even read the sheets — so the job cannot say when
the upload is over. The items can: an upload is done once every file and
dataset made since it was sent has settled.

What each item waits on is Mammoth's own `user_action_required`, the field the
web app draws its "action needed" badge from, read through the resources API
as the polling user. What it does not name is read off the status instead: an
item that is neither still being read nor finished has stopped, and saying so
is the difference between a user who knows and one who finds out later.
"""

from datetime import UTC, datetime

from .consts import (
    MAMMOTH_PROJECT_URL,
    ApiPaths,
    DatasetStatus,
    FileStatus,
    InterpretationFields,
    ResourceTypes,
    UploadFields,
    UploadReportFields,
    UserActions,
)
from .sdk import JsonValue, build_client, request_api
from .store import Record

type Item = dict[str, JsonValue]

# An item in one of these is still being read; any other status is where it
# stays until someone acts.
BUSY = {
    ResourceTypes.FILE: {
        FileStatus.PROCESSING,
        FileStatus.EXTRACTING,
    },
    ResourceTypes.DATASET: {
        DatasetStatus.UNPROCESSED,
        DatasetStatus.PROCESSING,
        DatasetStatus.DUPLICATING,
        DatasetStatus.APPENDING,
        DatasetStatus.MERGING,
    },
}
# And in one of these it arrived: Mammoth read it, and the user has their data.
# Anything else has stopped somewhere, whether or not Mammoth named what it
# waits on — which is listed rather than assumed, so a status no one here has
# seen is reported instead of passing for one that worked.
FINISHED = {
    ResourceTypes.FILE: {
        FileStatus.PROCESSED,
        FileStatus.EXTRACTED,
    },
    ResourceTypes.DATASET: {
        DatasetStatus.READY,
        DatasetStatus.PROCESSED,
    },
}
# Every action ends here: the choice is the user's, and a model that guesses it
# is wrong silently — the wrong sheets, or every date in the file read the wrong
# way round. So each step says to ask, and to stop until the answer comes.
ASK_FIRST = "Ask them before you do anything else, and do not choose for them."
# What the model does about each action Mammoth can wait on. The first two are
# settled with a tool; the rest need the web app.
NEXT_STEP = {
    UserActions.SHEET_SELECTION_REQUIRED: (
        "Ask the user which of these sheets to bring in, then call"
        f" extract_sheets with this file_id. {ASK_FIRST}"
    ),
    UserActions.AMBIGUOUS_DATE_FORMAT: (
        "Call set_date_format with this dataset_id and no format, which changes"
        " nothing and names the columns waiting to be told. Ask the user"
        " whether those are US (MM/DD/YYYY) or UK (DD/MM/YYYY) — naming them,"
        " because a file can hold one of each — and call it again with the"
        f" answer. {ASK_FIRST}"
    ),
    UserActions.PASSWORD_REQUIRED: (
        "Ask the user for the file's password and call unlock_file with it —"
        " offering, in the same message, to enter it at mammoth_url instead,"
        " because a password typed here is stored with the conversation and a"
        f" password typed in Mammoth is not. {ASK_FIRST}"
    ),
}
# The same action covers two different problems, told apart by whether Mammoth
# left an interpretation to answer: it could not decide how to READ the file,
# or it read it and some rows did not fit. Only the first is settled here.
READ_IT_DIFFERENTLY = (
    "Ask the user how the file should be read. `summary` is what Mammoth could"
    " not decide and `suggested_instructions` are its own ways of answering it;"
    " quote them. Then call interpret_file with this dataset_id, show the user"
    f" the rows it returns, and call it again with apply. {ASK_FIRST}"
)
UNREADABLE_ROWS = (
    "Call review_unreadable_rows with this dataset_id, which changes nothing"
    " and answers with the lines that would not go in and the reason for each."
    " Show them all. Ask the user whether to discard them and finish the"
    " dataset with the rows that did fit, and call it again with discard only"
    " if they say so — discarded lines do not come back. A line they want to"
    " keep instead has to be corrected in Mammoth at mammoth_url: say so"
    f" rather than discarding it for them. {ASK_FIRST}"
)
IN_MAMMOTH = (
    "Ask the user to review this in Mammoth at mammoth_url, because no tool"
    f" here settles it. {ASK_FIRST}"
)
# An upload is a step of something larger — a dataset to clean, a dashboard to
# build — and a model that reports the upload and stops leaves the user to ask
# for the rest again. So every step ends by pointing back at what they wanted.
CARRY_ON = (
    "Then carry on with what the user originally asked for, and with the other"
    " files: only a file nobody can rescue ends the work on that file."
)
# What to say about an item that stopped without Mammoth naming a wait. Nobody
# can settle these, so they are told plainly rather than asked about. Keyed by
# the status alone: a file and a dataset both call it "error", and both are put
# right the same way, by deleting the file and uploading it again.
NOTHING_TO_DO = {
    FileStatus.ERROR: (
        "Mammoth could not read this file at all. No tool and no amount of"
        " waiting changes that: tell the user, and offer to delete it with"
        " delete_file so they can fix it and upload it again."
    ),
    DatasetStatus.EMPTY: ("This file held no rows to read. Tell the user; it is theirs to fix."),
}
STOPPED = (
    "This stopped before it was ready, and Mammoth did not say what it waits"
    " on. Read it with get_file or get_dataset, tell the user what it says,"
    " and offer them mammoth_url."
)
# One page of the newest items is plenty: an upload makes a handful.
NEWEST_ITEMS = 50


async def report_upload(ticket: Record) -> dict[str, JsonValue]:
    """Say whether Mammoth has finished reading an upload, and what it made."""
    since = read_time(ticket[UploadFields.UPLOADED_AT])
    listed = await list_newest(
        int(ticket[UploadFields.WORKSPACE_ID]), int(ticket[UploadFields.PROJECT_ID])
    )
    return summarize(find_made_since(listed, since), ticket)


async def list_newest(workspace_id: int, project_id: int) -> list[Item]:
    """List the project's newest files and datasets, with what each waits on."""
    async with build_client(workspace_id, project_id) as client:
        listed = await request_api(
            client,
            "GET",
            ApiPaths.RESOURCES.format(workspace_id=workspace_id, project_id=project_id),
            query={
                "type": f"{ResourceTypes.FILE},{ResourceTypes.DATASET}",
                "sort": "created_at:desc",
                "limit": NEWEST_ITEMS,
                "fields": "full",
            },
        )
    resources = listed.get("resources")
    if not isinstance(resources, list):
        return []
    return [item for item in resources if isinstance(item, dict)]


def find_made_since(listed: list[Item], since: datetime) -> list[Item]:
    """Keep the items the upload made: those created once it was sent."""
    return [item for item in listed if read_time(item["created_at"]) >= since]


def read_time(stamp: JsonValue) -> datetime:
    """Read a timestamp as UTC. Mammoth writes a naive UTC time with a `Z`."""
    read = datetime.fromisoformat(str(stamp).removesuffix("Z"))
    return read if read.tzinfo else read.replace(tzinfo=UTC)


def summarize(items: list[Item], ticket: Record) -> dict[str, JsonValue]:
    """`processing` while any item is still being read, else `done`."""
    return {
        UploadFields.STATUS: (
            UploadFields.PROCESSING if any(is_busy(item) for item in items) else UploadFields.DONE
        ),
        UploadFields.FILES: [describe(item, ticket) for item in items],
    }


def is_busy(item: Item) -> bool:
    """Still being read, and so not waiting on anybody yet."""
    return item[UploadFields.STATUS] in BUSY.get(str(item["resource_type"]), set()) or is_replaying(
        read_properties(item)
    )


def is_replaying(properties: Item) -> bool:
    """True for a batch about to be read the way its dataset was read before.

    Mammoth gives it the same status as a file whose rows do not fit, and tells
    the two apart by a marker of its own — `BatchManager.datasource_needs_review`
    in `api.ds.batch` is where that rule lives. A replay needs nobody: asking
    the user about it interrupts them over a file that was finishing anyway.
    """
    unread = properties.get(InterpretationFields.ADDITIONAL_INFO)
    if not isinstance(unread, dict):
        return False
    return bool(unread.get(InterpretationFields.REPLAYING)) and not unread.get(
        InterpretationFields.INTERPRETATION
    )


def read_properties(item: Item) -> Item:
    """What the core list holds about an item, which it may hold nothing of."""
    properties = item.get("object_properties")
    return properties if isinstance(properties, dict) else {}


def describe(item: Item, ticket: Record) -> Item:
    """One item, and — when it waits on the user — what to do about it."""
    is_file = item["resource_type"] == ResourceTypes.FILE
    id_field = UploadReportFields.FILE_ID if is_file else UploadReportFields.DATASET_ID
    described: Item = {
        UploadReportFields.KIND: "file" if is_file else "dataset",
        id_field: item["object_id"],
        UploadReportFields.NAME: item["name"],
        UploadFields.STATUS: item["status"],
    }
    needs = describe_wait(item, read_properties(item), ticket)
    if needs:
        described[UploadReportFields.NEEDS] = needs
    return described


def describe_wait(item: Item, properties: Item, ticket: Record) -> Item:
    """What stands between this item and data the user can work with.

    Either Mammoth named what it waits on, or the item stopped somewhere it
    cannot leave by itself. The second is reported too: an item the report says
    nothing about reads as one that worked, and the user finds out later that
    half their upload is missing.
    """
    if is_replaying(properties):
        return {}
    action = properties.get(UploadReportFields.USER_ACTION_REQUIRED)
    if isinstance(action, dict):
        return describe_action(action, properties, ticket)
    if has_stopped(item):
        return describe_stop(item, ticket)
    return {}


def has_stopped(item: Item) -> bool:
    """True when an item is neither still being read nor finished."""
    kind = str(item["resource_type"])
    # Still coming or already arrived: either way nobody has to do anything.
    under_way = BUSY.get(kind, set()) | FINISHED.get(kind, set())
    return item[UploadFields.STATUS] not in under_way


def describe_stop(item: Item, ticket: Record) -> Item:
    """An item that went no further, and what — if anything — is left to try."""
    status = str(item[UploadFields.STATUS])
    return {
        UploadReportFields.ACTION: status,
        UploadReportFields.NEXT_STEP: (f"{NOTHING_TO_DO.get(status, STOPPED)} {CARRY_ON}"),
        UploadReportFields.MAMMOTH_URL: project_url(ticket),
    }


def describe_action(action: Item, properties: Item, ticket: Record) -> Item:
    """What the item waits on, what to do, and what the user has to be told."""
    kind = str(action.get(UserActions.TYPE))
    unread = read_interpretation(properties)
    needs: Item = {
        UploadReportFields.ACTION: kind,
        UploadReportFields.NEXT_STEP: f"{find_next_step(kind, unread)} {CARRY_ON}",
        UploadReportFields.MAMMOTH_URL: project_url(ticket),
        **unread,
    }
    sheets = action.get(UserActions.SHEET_INFO)
    if sheets:
        needs[UploadReportFields.SHEETS] = sheets
    return needs


def project_url(ticket: Record) -> str:
    """Where the user looks at this upload in the web app."""
    return MAMMOTH_PROJECT_URL.format(
        workspace_id=ticket[UploadFields.WORKSPACE_ID],
        project_id=ticket[UploadFields.PROJECT_ID],
    )


def find_next_step(kind: str, unread: Item) -> str:
    """What the model does about this action.

    `unstructured_rows` is two problems under one name. With an interpretation,
    Mammoth could not decide how to read the file and is waiting to be told —
    which `interpret_file` does. Without one, it read the file and some rows
    did not fit it, which `review_unreadable_rows` shows and discards.
    """
    if kind == UserActions.UNSTRUCTURED_ROWS:
        return READ_IT_DIFFERENTLY if unread else UNREADABLE_ROWS
    return NEXT_STEP.get(kind, IN_MAMMOTH)


def read_interpretation(properties: Item) -> Item:
    """What Mammoth could not decide about a file's layout, if that is the wait.

    Its sample rows are left behind: the model shows the user the rows an
    instruction actually makes, which `interpret_file` answers with.
    """
    info = properties.get(InterpretationFields.ADDITIONAL_INFO)
    unread = info.get(InterpretationFields.INTERPRETATION) if isinstance(info, dict) else None
    if not isinstance(unread, dict):
        return {}
    return {
        UploadReportFields.SUMMARY: unread.get(InterpretationFields.SUMMARY),
        UploadReportFields.SUGGESTIONS: unread.get(InterpretationFields.SUGGESTIONS),
    }
