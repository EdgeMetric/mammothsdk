"""Change one export of a view: its settings, whether it runs, or run it now.

One tool does all of it, as `edit_transformation_step` does for a step, so a
model has one place to go to fix an export. An export sends rows out of
Mammoth, so nothing here sends them unless the model asks for "run":

- "replace" changes the settings and sends nothing. The new settings apply
  from the next run.
- "suspend" and "restore" stop and start the export running with the view.
- "run" sends the rows now, and reports how the run went.
"""

from typing import Literal

from mammoth.client import MammothClient
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import ExportFields, StepFields
from ..export_runs import (
    RUN_FAILED_NOTE,
    RUN_GOES_ON,
    last_run,
    read_view_exports,
    report,
    report_run,
    run_since,
)
from ..jobs import JobStillRunning, job_id_of, still_running, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE
from .exports import build_export
from .pipeline import view_ids

type ExportChange = Literal["replace", "suspend", "restore", "run"]
REPLACE = "replace"
SUSPEND = "suspend"
RESTORE = "restore"
RUN = "run"
# What an export's status reads while it does not run with its view.
NOT_RUNNING = frozenset({ExportFields.SUSPENDED, ExportFields.SUSPENDING})

NOT_CHANGED = "The export was not changed"
REPLACED_NOTE = (
    "The settings are saved and nothing was sent. They apply from the export's next"
    " run. Tell the user. To send the rows now, ask them first, then call edit_export"
    ' with "run".'
)
SUSPENDED_NOTE = "The export no longer runs when the view runs. Tell the user."
RESTORED_NOTE = "The export runs again when the view runs. Tell the user."


@mcp_server.tool(title="Edit export", annotations=DESTRUCTIVE)
async def edit_export(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    export_id: int,
    change: ExportChange,
    settings: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Change one export of a view, or run it now.

    `change` says what to do:
    - "replace": change the export's settings. Pass only the settings that
      change, and null for one to drop; the rest stay as they are. A
      password reads back masked; leave it out to keep it. Nothing is sent.
    - "suspend": the export stops running when the view runs.
    - "restore": a suspended export runs with the view again.
    - "run": send the view's rows now. Ask the user first.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        export_id: The export's `id`, as `list_exports` lists it.
        change: "replace", "suspend", "restore" or "run".
        settings: With "replace" only: the settings that change, named as
            `get_schema` with kind="export" names them.

    Returns:
        `outcome`: "changed", "ran", "run_failed" or "run_pending" (Mammoth
        has not recorded the run yet). `next_step`: what to tell the user.
        `export`: the export afterwards. `last_run`: after "run", how it went.
        `mammoth_url`: the view in Mammoth.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with build_client(workspace_id, project_id) as client:
        export = find_export(await read_view_exports(client, ids), export_id)
        patch = export_patch(view_id, export, change, settings)
        # The newest run before this one, so an older run is not reported as this one.
        before = await last_run(client, ids, export_id)
        try:
            await send_export_change(client, ids, export_id, patch)
        except JobStillRunning as running:
            return still_running(running, RUN_GOES_ON)
        except ToolError as failed:
            if change != RUN:
                raise
            note = f"{RUN_FAILED_NOTE} Mammoth said: {failed}"
            run = await run_since(client, ids, export_id, before)
            return await report(client, ids, export_id, StepFields.RUN_FAILED, note, run)
        if change != RUN:
            note = CHANGE_NOTES[change]
            return await report(client, ids, export_id, StepFields.CHANGED, note, before)
        return await report_run(client, ids, export_id, before)


CHANGE_NOTES = {REPLACE: REPLACED_NOTE, SUSPEND: SUSPENDED_NOTE, RESTORE: RESTORED_NOTE}


def find_export(exports: list[dict[str, JsonValue]], export_id: int) -> dict[str, JsonValue]:
    """The export with this id in the view, or why there is none."""
    for export in exports:
        if export.get(ExportFields.ID) == export_id:
            return export
    listed = [export.get(ExportFields.ID) for export in exports]
    raise ToolError(
        f"This view has no export {export_id}. Its exports: {listed}."
        " Call list_exports to see them."
    )


def export_patch(
    view_id: int,
    export: dict[str, JsonValue],
    change: str,
    settings: dict[str, JsonValue] | None,
) -> dict[str, JsonValue]:
    """The export route's patch for one change, or why the change cannot be made."""
    if change != REPLACE:
        if settings is not None:
            raise ToolError(f'Pass `settings` only with "replace", not with "{change}".')
        check_command(export, change)
        return {StepFields.OP: StepFields.COMMAND, StepFields.PATH: change, StepFields.VALUE: None}
    if not settings:
        raise ToolError('"replace" needs `settings`: the settings that change.')
    return {
        StepFields.OP: StepFields.REPLACE,
        StepFields.PATH: StepFields.REPLACE_PARAMS,
        StepFields.VALUE: replaced_export(view_id, export, settings),
    }


def check_command(export: dict[str, JsonValue], change: str) -> None:
    """Refuse a command that cannot do anything to the export as it stands."""
    stopped = export.get(ExportFields.STATUS) in NOT_RUNNING
    export_id = export.get(ExportFields.ID)
    if change == SUSPEND and stopped:
        raise ToolError(f"Export {export_id} is suspended already.")
    if change == RESTORE and not stopped:
        raise ToolError(f"Export {export_id} is not suspended: it runs with the view already.")
    if change == RUN and stopped:
        raise ToolError(
            f'Export {export_id} is suspended, so it cannot run. Call edit_export with "restore"'
            " first, if the user wants it running again."
        )


def replaced_export(
    view_id: int, export: dict[str, JsonValue], settings: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """The whole export the route takes: the stored one, with the settings changed.

    The settings are checked against the destination's own contract, as when
    the export was added. Everything else keeps what the export had: when it
    runs, where it sits in the pipeline, and the condition on its rows.

    Raises:
        ToolError: If the changed settings do not fit the destination.
    """
    stored = export.get(ExportFields.SETTINGS)
    # Only a setting the caller sets to null is dropped; a stored null stays.
    dropped = {name for name, value in settings.items() if value is None}
    merged = {**(stored if isinstance(stored, dict) else {}), **settings}
    kept: dict[str, JsonValue] = {
        name: value for name, value in merged.items() if name not in dropped
    }
    spec = build_export(str(export.get(ExportFields.DESTINATION)), kept, view_id, run_now=False)
    stays = {
        name: export[name] for name in ExportFields.KEPT_ON_REPLACE if export.get(name) is not None
    }
    return {
        **spec.model_dump(mode="json", exclude_none=True),
        **stays,
        **place_of(export),
        ExportFields.TRIGGER_ID: export.get(ExportFields.ID),
        **schedule_of(export),
    }


def place_of(export: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Where the export runs: at the end of the pipeline, or after a step.

    A save that names a sequence pins the export after that step, so an
    export at the end is saved without one, as the web app saves it, and
    stays at the end when steps are added later.
    """
    if export.get(ExportFields.AT_THE_END) is False:
        return {
            ExportFields.AT_THE_END: False,
            ExportFields.SEQUENCE: export.get(ExportFields.SEQUENCE),
        }
    return {ExportFields.AT_THE_END: True, ExportFields.SEQUENCE: None}


def schedule_of(export: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The schedule a scheduled export must be saved with again, or nothing.

    Mammoth rebuilds the stored schedule from the one the save sends, and
    refuses a scheduled export saved without one.
    """
    if export.get(ExportFields.WHEN) != ExportFields.ON_A_SCHEDULE:
        return {}
    extra = export.get(ExportFields.EXTRA)
    schedule = extra.get(ExportFields.SCHEDULE) if isinstance(extra, dict) else None
    return {ExportFields.SCHEDULE: schedule} if schedule is not None else {}


async def send_export_change(
    client: MammothClient, ids: dict[str, int], export_id: int, patch: dict[str, JsonValue]
) -> None:
    """Send one change to an export, and wait for the job it starts.

    Raises:
        JobStillRunning: If the job outlasts the tool call.
        ToolError: If Mammoth refused the change, or its job failed.
    """
    answer = await read_sdk_errors(
        client.exports.update(
            ids["dataview_id"],
            export_id,
            [patch],
            dataset_id=ids["dataset_id"],
            project_id=ids["project_id"],
        )
    )
    if job_id_of(answer) is not None:
        await wait_for_job(ids["workspace_id"], answer)
