"""Take a change back: restore what went to the trash, or put a pipeline back as it was.

What can be taken back:
- Views (`delete_views`), dashboards (`delete_dashboard`), automations
  (`delete_automation`) and datasets go to their project's trash. `undo` with
  what="trash" restores them until Mammoth empties the trash.
- Every change to a view's pipeline saves a version of it. `undo` with
  what="pipeline" puts an older version back. The version from just before
  stays in the list, so that is taken back the same way.

A deleted file or export, and rows already sent out, are not in the trash.

One tool takes back both, and one lists the trash: reads and changes cannot
share a tool, and every tool more is one more for a model to choose between.
"""

from typing import Literal, TypedDict

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import PageFields, PipelineFields, TrashFields, VersionFields
from ..jobs import JobStillRunning, still_running, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE, READS
from .pipeline import get_pipeline

type TrashKind = Literal["dataview", "dataset", "dashboard", "automation"]
type UndoWhat = Literal["trash", "pipeline"]


class TrashItem(TypedDict):
    """One item to restore, as `list_trash` lists it."""

    type: TrashKind
    id: int


NAME_THE_ITEMS = "Name the items to restore, each with its type and id, as list_trash lists them."
NAME_THE_VERSION = (
    "Name the view (dataset_id and view_id) and the version_id to put back, as"
    " get_pipeline lists them with include_versions."
)
PUT_BACK = (
    "The pipeline is back as that version had it. get_pipeline with include_versions"
    " lists the version from just before this; undo with it takes this back."
)
STILL_RUNNING = (
    "The view is running again with these steps: get_pipeline shows their results"
    " once the run is done."
)
RUN_FAILED = (
    "The pipeline is back, but the view's run after it failed: tell the user, and"
    " see `problems` for the step to blame."
)
STILL_RESTORING = (
    "Mammoth is still restoring. list_trash shows what is left once it is done:"
    " do not call undo again."
)
STILL_PUTTING_BACK = (
    "Mammoth is still putting the pipeline back. get_pipeline shows it once it is"
    " done: do not call undo again."
)

# What to tell the user of the view's run after a version is put back.
RUN_NOTES = {
    **dict.fromkeys(VersionFields.RUNNING_STATES, STILL_RUNNING),
    VersionFields.RUNTIME_ERROR: RUN_FAILED,
}


@mcp_server.tool(title="List trash", annotations=READS)
async def list_trash(
    workspace_id: int, project_id: int, kind: TrashKind | None = None, offset: int = 0
) -> dict[str, JsonValue]:
    """List what is in a project's trash and can still be restored with `undo`.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        kind: Only "dataview", "dataset", "dashboard" or "automation". Omit for
            all of them.
        offset: How many items to skip, for the next page: `next_offset`.

    Returns:
        `items`: each item's `type` and `id` (what `undo` takes), `name`, the
        `dataset_id` of a view, `trashed_at`, and `days_until_purge`, after
        which Mammoth deletes it for good. `total`, and `retention_days`: how
        long the trash keeps an item. `next_offset`, when there are more.
    """
    async with build_client(workspace_id, project_id) as client:
        listed = await read_sdk_errors(
            client.trash.list(
                project_id=project_id, type=kind, limit=TrashFields.LISTED, offset=offset
            )
        )
    items: list[JsonValue] = [
        {field: item[field] for field in TrashFields.ITEM_FIELDS if field in item}
        for item in listed[TrashFields.ITEMS]
        if not item.get(TrashFields.IS_ACTIVE_PARENT)
    ]
    total = listed.get(PageFields.TOTAL)
    after = offset + TrashFields.LISTED
    return {
        TrashFields.ITEMS: items,
        PageFields.TOTAL: total,
        TrashFields.RETENTION_DAYS: listed.get(TrashFields.RETENTION_DAYS),
        **({PageFields.NEXT_OFFSET: after} if isinstance(total, int) and after < total else {}),
    }


@mcp_server.tool(title="Undo: restore trash, roll back pipeline", annotations=DESTRUCTIVE)
async def undo(
    workspace_id: int,
    project_id: int,
    what: UndoWhat,
    items: list[TrashItem] | None = None,
    dataset_id: int | None = None,
    view_id: int | None = None,
    version_id: int | None = None,
) -> dict[str, JsonValue]:
    """Take a change back: restore items from the trash, or roll back a view's pipeline.

    Ask the user first. Putting a pipeline back replaces its steps with the
    version's, and the view runs again.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        what: "trash" restores `items`. "pipeline" puts the view's pipeline
            back as `version_id` had it.
        items: For "trash": what to restore, each as `{"type": ..., "id": ...}`
            from `list_trash`. A view comes back with the dashboards trashed
            with it; a view whose dataset is trashed needs the dataset first.
        dataset_id: For "pipeline": the view's dataset.
        view_id: For "pipeline": the view.
        version_id: For "pipeline": the version to put back, from
            `get_pipeline` with `include_versions`.

    Returns:
        For "trash": `succeeded` and `failed`, each item with why. For
        "pipeline": the pipeline afterwards, as `get_pipeline` reports it, and
        `next_step`, how to take this back too.
    """
    if what == "trash":
        return await restore_from_trash(workspace_id, project_id, items)
    if dataset_id is None or view_id is None or version_id is None:
        raise ToolError(NAME_THE_VERSION)
    return await put_pipeline_back(workspace_id, project_id, dataset_id, view_id, version_id)


async def restore_from_trash(
    workspace_id: int, project_id: int, items: list[TrashItem] | None
) -> dict[str, JsonValue]:
    """Restore the items named, and wait for Mammoth to say which came back."""
    if not items:
        raise ToolError(NAME_THE_ITEMS)
    async with build_client(workspace_id, project_id) as client:
        started = await read_sdk_errors(
            client.trash.restore([dict(item) for item in items], project_id=project_id)
        )
    try:
        restored = await wait_for_job(workspace_id, started)
    except JobStillRunning as running:
        return still_running(running, STILL_RESTORING)
    return {
        TrashFields.SUCCEEDED: restored.get(TrashFields.SUCCEEDED, []),
        TrashFields.FAILED: restored.get(TrashFields.FAILED, []),
    }


async def put_pipeline_back(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int, version_id: int
) -> dict[str, JsonValue]:
    """Apply one of a view's versions, wait for it, and read the pipeline after."""
    async with build_client(workspace_id, project_id) as client:
        started = await read_sdk_errors(
            client.pipeline_versions.apply(dataset_id, view_id, version_id)
        )
    try:
        await wait_for_job(workspace_id, started)
    except JobStillRunning as running:
        return still_running(running, STILL_PUTTING_BACK)
    pipeline = await get_pipeline(workspace_id, project_id, dataset_id, view_id)
    state = pipeline[PipelineFields.PIPELINE]
    run = state.get(VersionFields.EXECUTION_STATE) if isinstance(state, dict) else None
    told = (pipeline.get(VersionFields.NEXT_STEP), PUT_BACK, RUN_NOTES.get(str(run)))
    notes = [str(note) for note in told if note]
    return {**pipeline, VersionFields.NEXT_STEP: " ".join(notes)}
