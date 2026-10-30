"""How an export's run went, for the tools that add, edit or run one.

Adding an export starts a job that ends before the export runs: the run comes
after it, and when a new export's first run fails, Mammoth removes the export.
So a tool that runs an export reads the export and its runs afterwards.
"""

import asyncio

from mammoth.client import MammothClient

from .consts import EXPORT_POLL_SECONDS, ExportFields, ListFields, StepFields
from .deadline import seconds_left
from .sdk import JsonValue, read_sdk_errors
from .shape import view_url

RAN_NOTE = "Tell the user the rows were sent: `last_run` says how many, and where."
RUN_PENDING_NOTE = (
    "The run's job ended, but Mammoth has not recorded the run yet, so how it went"
    " is not known. Do not run it again: call get_export in a minute, and tell the"
    " user what its newest run says."
)
RUN_FAILED_NOTE = (
    "The run failed: `last_run` says why. Tell the user. Fix the settings with"
    ' edit_export "replace" (get_schema with kind="export" lists them), then "run" again; or'
    ' "suspend" the export until it can be fixed.'
)
RUN_GOES_ON = (
    "The export is still running. Do not run it again: call get_export later to see"
    " how the run went."
)
REMOVED_NOTE = (
    "The export's first run failed, so Mammoth removed the export and sent nothing."
    ' Tell the user. Check the settings against get_schema with kind="export", then'
    " add the export again."
)
# What a new export's status reads until its first run ends.
NOT_RUN_YET = frozenset({ExportFields.ADDED, ExportFields.EXECUTING})


async def read_view_exports(
    client: MammothClient, ids: dict[str, int]
) -> list[dict[str, JsonValue]]:
    """Every export of a view, as the exports route lists them."""
    paged = await read_sdk_errors(
        client.exports.list(ids["dataview_id"], dataset_id=ids["dataset_id"])
    )
    return [dict(export.model_dump(mode="json")) for export in paged.exports]


async def wait_for_first_run(
    client: MammothClient, ids: dict[str, int], export_id: int
) -> dict[str, JsonValue]:
    """Wait for a new export's first run, and say how it went.

    Waits while the export reads "added" or "executing", as long as the tool
    call may wait.
    """
    while True:
        exports = await read_view_exports(client, ids)
        now = [export for export in exports if export.get(ExportFields.ID) == export_id]
        if not now:
            return outcome(ids, StepFields.RUN_FAILED, REMOVED_NOTE, None, None)
        if now[0].get(ExportFields.STATUS) not in NOT_RUN_YET:
            return await report_run(client, ids, export_id, None)
        if seconds_left() <= EXPORT_POLL_SECONDS:
            return outcome(ids, StepFields.RUN_PENDING, RUN_GOES_ON, now[0], None)
        await asyncio.sleep(EXPORT_POLL_SECONDS)


async def report(
    client: MammothClient,
    ids: dict[str, int],
    export_id: int,
    result: str,
    note: str,
    run: JsonValue,
) -> dict[str, JsonValue]:
    """What a change came to: the export now, its newest run, and what to do."""
    exports = await read_view_exports(client, ids)
    now = [export for export in exports if export.get(ExportFields.ID) == export_id]
    return outcome(ids, result, note, now[0] if now else None, run)


def outcome(
    ids: dict[str, int], result: str, note: str, export: JsonValue, run: JsonValue
) -> dict[str, JsonValue]:
    """The answer a tool gives about one export."""
    return {
        StepFields.OUTCOME: result,
        StepFields.NEXT_STEP: note,
        ExportFields.EXPORT: export,
        ExportFields.LAST_RUN: run,
        ListFields.MAMMOTH_URL: view_url(
            ids["workspace_id"], ids["project_id"], ids["dataview_id"]
        ),
    }


async def report_run(
    client: MammothClient, ids: dict[str, int], export_id: int, before: JsonValue
) -> dict[str, JsonValue]:
    """How a run the tool started went, from a run newer than `before`."""
    run = await run_since(client, ids, export_id, before)
    if not isinstance(run, dict):
        return await report(client, ids, export_id, StepFields.RUN_PENDING, RUN_PENDING_NOTE, None)
    if run.get(ExportFields.RUN_STATUS) == ExportFields.FAILED:
        return await report(client, ids, export_id, StepFields.RUN_FAILED, RUN_FAILED_NOTE, run)
    return await report(client, ids, export_id, StepFields.RAN, RAN_NOTE, run)


async def run_since(
    client: MammothClient, ids: dict[str, int], export_id: int, before: JsonValue
) -> JsonValue:
    """The export's newest run when it is newer than `before`, else None."""
    run = await last_run(client, ids, export_id)
    old_id = before.get(ExportFields.ID) if isinstance(before, dict) else None
    return run if isinstance(run, dict) and run.get(ExportFields.ID) != old_id else None


async def last_run(client: MammothClient, ids: dict[str, int], export_id: int) -> JsonValue:
    """The export's newest run, or None when it never ran."""
    runs = await read_sdk_errors(
        client.exports.runs(
            ids["dataview_id"],
            export_id,
            limit=1,
            dataset_id=ids["dataset_id"],
            project_id=ids["project_id"],
        )
    )
    return runs.runs[0].model_dump(mode="json") if runs.runs else None
