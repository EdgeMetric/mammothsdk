"""Create, copy and delete the views of a dataset.

A view is where transformations run, so a second view is the safe place to
experiment: copy the view, change the copy, delete the copy.
"""

from collections.abc import Awaitable

from mammoth.client import MammothClient
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import LIST_LIMIT_DEFAULT, ListFields, ViewFields
from ..jobs import wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..shape import view_url
from ..tool_kinds import CHANGES, DESTRUCTIVE

IN_THE_TRASH = (
    'They are in the trash. To bring one back, call undo with what="trash";'
    " list_trash shows them, with how long the trash keeps them."
)
ASK = (
    "Nothing was deleted yet. Tell the user what goes with them, under goes_with_them;"
    " when they agree, call again with confirmed=true. A view other views or"
    " automations depend on cannot go to the trash until those are removed."
)
LAST_VIEW = (
    "These are all the views of dataset {dataset_id}, and Mammoth moves a dataset to the"
    " trash with its last view. To delete the dataset, ask the user, then call again"
    " with whole_dataset=true."
)


@mcp_server.tool(title="Create view", annotations=CHANGES)
async def create_view(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    name: str,
    copy_from_view_id: int | None = None,
) -> dict[str, JsonValue]:
    """Create a view of a dataset, empty or as a copy of another view.

    Copy a view before experimenting with its transformations: the original
    stays as it is.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: Which dataset the new view belongs to.
        name: Name of the new view. Mammoth may add a number to it, e.g.
            "Scratch" becomes "Scratch 1"; read the name back with `list_views`.
        copy_from_view_id: A view of the same dataset whose transformations the
            new view starts with. Omit for a view with no transformations.

    Returns:
        The new view's id, under the key `dataview_id`, and `mammoth_url`, the
        page in Mammoth it opens on. `next_step` when a copied step failed.
    """
    # The SDK waits for the creation job itself, so the new view's id is
    # what comes back.
    async with build_client(workspace_id) as client:
        created = await read_sdk_errors(
            client.dataviews.create(
                dataset_id,
                name=name,
                clone_config_from=copy_from_view_id,
                project_id=project_id,
            )
        )
    # The answer is the run that built the view, down to the machine it ran
    # on; the model needs the view.
    view_id = created.get(ListFields.VIEW_ID)
    view: dict[str, JsonValue] = {
        ListFields.VIEW_ID: view_id,
        ListFields.MAMMOTH_URL: view_url(workspace_id, project_id, view_id),
    }
    if created.get(ViewFields.HAS_ERROR):
        view[ViewFields.NEXT_STEP] = ViewFields.COPY_FAILED
    return view


@mcp_server.tool(title="Delete views", annotations=DESTRUCTIVE)
async def delete_views(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_ids: list[int] | None = None,
    whole_dataset: bool = False,
    confirmed: bool = False,
) -> dict[str, JsonValue]:
    """Move views of a dataset, or the whole dataset, to the trash.

    Ask the user before calling this. `undo` with what="trash" brings a view or
    a dataset back, with its transformations, until Mammoth empties the trash.
    Mammoth moves a dataset to the trash with its last view, so deleting every
    view of a dataset is refused: pass `whole_dataset` to delete the dataset.

    The first call deletes nothing when something else goes too: the exports,
    dashboards, views and automations built on the views, or the dataset. It
    lists them under `goes_with_them`. Tell the user; when they agree, call
    again with `confirmed` true.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: Which dataset the views belong to.
        view_ids: The views to delete. Omit with `whole_dataset`.
        whole_dataset: Delete the dataset, with all its views.
        confirmed: The user agreed to what `goes_with_them` listed.

    Returns:
        `deleted`: the view ids moved to the trash, or `trashed_dataset`. `failed`:
        each view that was not, with the reason; one failure does not stop the
        others. `goes_with_them`, when nothing was deleted yet. `next_step`.
    """
    async with build_client(workspace_id) as client:
        ids = {"workspace_id": workspace_id, "project_id": project_id, "dataset_id": dataset_id}
        targets = await _views_to_delete(client, ids, view_ids, whole_dataset)
        goes = await _what_goes_with(client, ids, targets)
        if whole_dataset:
            goes = {ViewFields.DATASET: dataset_id, ViewFields.VIEWS: list(targets), **goes}
        if goes and not confirmed:
            return {ViewFields.DELETED: [], ViewFields.GOES_WITH: goes, ViewFields.NEXT_STEP: ASK}
        if whole_dataset:
            await _trash(workspace_id, client.datasets.trash(dataset_id, project_id=project_id))
            return {ViewFields.TRASHED_DATASET: dataset_id, ViewFields.NEXT_STEP: IN_THE_TRASH}
        return await _trash_views(client, ids, targets)


async def _every_view(client: MammothClient, ids: dict[str, int]) -> list[int]:
    """The ids of every view of the dataset, page by page: one page is not all of them."""
    every: list[int] = []
    while True:
        page = await read_sdk_errors(
            client.browse.dataviews(
                ids["dataset_id"],
                project_id=ids["project_id"],
                limit=LIST_LIMIT_DEFAULT,
                offset=len(every),
            )
        )
        views = page.get(ListFields.VIEWS, [])
        every += [int(view[ListFields.ID]) for view in views]
        if len(views) < LIST_LIMIT_DEFAULT:
            return every


async def _views_to_delete(
    client: MammothClient, ids: dict[str, int], view_ids: list[int] | None, whole: bool
) -> list[int]:
    """The views the call deletes, refused when they would take the dataset with them."""
    if not view_ids and not whole:
        raise ToolError("Name the views to delete in view_ids, or pass whole_dataset.")
    if view_ids and whole:
        raise ToolError("Name the views in view_ids, or pass whole_dataset: not both.")
    every = await _every_view(client, ids)
    if whole:
        return every
    named = list(dict.fromkeys(view_ids or []))
    if every and set(every) <= set(named):
        raise ToolError(LAST_VIEW.format(dataset_id=ids["dataset_id"]))
    return named


async def _what_goes_with(
    client: MammothClient, ids: dict[str, int], view_ids: list[int]
) -> dict[str, JsonValue]:
    """What deleting the views takes with them, by kind, as Mammoth lists it."""
    goes: dict[str, list[JsonValue]] = {}
    for view_id in view_ids:
        impact = await read_sdk_errors(
            client.dataviews.delete_impact(
                ids["dataset_id"], view_id, ViewFields.IMPACT_SCOPE, project_id=ids["project_id"]
            )
        )
        for kind in ViewFields.IMPACT_KINDS:
            for item in impact.get(kind) or []:
                kept = {k: item[k] for k in ViewFields.IMPACT_ITEM_FIELDS if k in item}
                goes.setdefault(kind, []).append({ViewFields.VIEW_ID: view_id, **kept})
    return dict(goes)


async def _trash(workspace_id: int, started: Awaitable[dict[str, JsonValue]]) -> None:
    await wait_for_job(workspace_id, await read_sdk_errors(started))


async def _trash_views(
    client: MammothClient, ids: dict[str, int], view_ids: list[int]
) -> dict[str, JsonValue]:
    deleted: list[JsonValue] = []
    failed: list[JsonValue] = []
    for view_id in view_ids:
        try:
            await _trash(
                ids["workspace_id"],
                client.dataviews.trash(ids["dataset_id"], view_id, project_id=ids["project_id"]),
            )
        except ToolError as error:
            failed.append({ViewFields.VIEW_ID: view_id, ViewFields.ERROR: str(error)})
        else:
            deleted.append(view_id)
    return {
        ViewFields.DELETED: deleted,
        ViewFields.FAILED: failed,
        **({ViewFields.NEXT_STEP: IN_THE_TRASH} if deleted else {}),
    }
