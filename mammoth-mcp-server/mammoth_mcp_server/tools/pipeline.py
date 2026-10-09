"""Read and change a view's pipeline: its steps, draft mode and runs.

A step is one transformation in the pipeline, and `add_transformations` adds
them. In draft mode, steps are staged without running until the draft is
submitted.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Literal

from mammoth.api.pipeline import PipelineAPI
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import (
    PREVIEW_ROWS_DEFAULT,
    PREVIEW_ROWS_MAX,
    PipelineFields,
)
from ..jobs import JobStillRunning, still_running, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import CHANGES, DESTRUCTIVE, READS
from ..transform_operations import TransformOperation
from .transformations import (
    OPERATION_NAMES,
    add_step,
    build_param,
    check_run,
    read_operation,
    wait_for_change,
)

# What a tool tells the model when the run it started outlasts the call.
RUN_GOES_ON = "The run is still going. Do not run it again: call get_pipeline later to see it end."
STEPS_RUN_ON = (
    "The steps were added and their run is still going. Do not add them again."
    " Call get_pipeline later; once the run is over, call manage_draft with"
    ' action "stop" to leave draft mode.'
)
DELETE_RUNS_ON = (
    "The step was deleted and the view's run is still going. Call get_pipeline"
    " later to see it end."
)

type DraftAction = Literal["start", "run", "drop", "stop"]
RUN_THE_DRAFT = "run"
# What each action asks the draft-mode route to do. One route, one operation.
DRAFT_ACTIONS: dict[str, str] = {
    "start": PipelineFields.DRAFT_ON,
    RUN_THE_DRAFT: PipelineFields.DRAFT_SUBMIT,
    "drop": PipelineFields.DRAFT_DISCARD,
    "stop": PipelineFields.DRAFT_OFF,
}


@mcp_server.tool(title="Get pipeline", annotations=READS)
async def get_pipeline(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int
) -> dict[str, JsonValue]:
    """Get a view's pipeline: its state and its steps, in order.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.

    Returns:
        `pipeline`: the state (`draft_mode` is off, clean or dirty; `auto_run`;
        `execution_state`). `steps`: each step's `id`, `sequence`, `status`
        and `params` (columns there are internal names).
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    # Both reads go through one client rather than one each.
    async with _pipeline(ids) as pipeline:
        tasks = await read_sdk_errors(
            pipeline.list_tasks(ids["dataview_id"], dataset_id=ids["dataset_id"])
        )
        state = await read_sdk_errors(
            pipeline.get_pipeline(ids["dataview_id"], dataset_id=ids["dataset_id"])
        )
    return {
        PipelineFields.PIPELINE: state,
        PipelineFields.STEPS: tasks[PipelineFields.TASKS],
    }


@mcp_server.tool(title="Delete transformation step", annotations=DESTRUCTIVE)
async def delete_transformation_step(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int, step_id: int
) -> dict[str, JsonValue]:
    """Delete one step of a view's pipeline and wait for the view to run again.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        step_id: The step's `id`, as `get_pipeline` lists it.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with _pipeline(ids) as pipeline:
        answer = await read_sdk_errors(
            pipeline.delete_task(ids["dataview_id"], step_id, dataset_id=ids["dataset_id"])
        )
    try:
        return await wait_for_change(workspace_id, answer)
    except JobStillRunning as running:
        return still_running(running, DELETE_RUNS_ON)


@mcp_server.tool(title="Preview transformation", annotations=READS)
async def preview_transformation(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    operation: dict[str, JsonValue],
    rows: int = PREVIEW_ROWS_DEFAULT,
) -> dict[str, JsonValue]:
    """Show what a transformation would do to a sample of a view, without adding it.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        operation: The transformation, in the shape `add_transformations`
            takes each of its own.
        rows: How many of the view's rows the preview runs on (at most 100).

    Returns:
        `data`: the sample's rows after the transformation, keyed by column
        name. `metadata`: the columns after it.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with build_client(workspace_id, project_id) as client:
        param = await build_param(client, read_operation(operation), ids)
        return await read_sdk_errors(
            client.pipeline.preview_task(
                ids["dataview_id"],
                param,
                dataset_id=ids["dataset_id"],
                sample_size=min(rows, PREVIEW_ROWS_MAX),
            )
        )


@mcp_server.tool(title="Manage pipeline draft", annotations=DESTRUCTIVE)
async def manage_draft(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    action: DraftAction,
) -> dict[str, JsonValue]:
    """Stage a view's transformations instead of running each one as it is added.

    In draft mode a new step is staged and does not run, so steps can be looked
    over with `preview_transformation` and then run together. Draft mode is the
    same as auto-run off. `add_transformations` already does all of this by
    itself; reach for this tool when the user wants to see the steps before
    they run, or to drop them.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        action: "start" to turn draft mode on, "run" to run the staged steps
            and wait for them, "drop" to throw them away, "stop" to turn draft
            mode off. The view stays in draft mode after "run" and "drop".

    Returns:
        The pipeline's state afterwards, as `get_pipeline` reports it. When
        the run outlasts the call: the run's `job_id` and what to do next.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    answer = await change_draft(ids, DRAFT_ACTIONS[action])
    if action == RUN_THE_DRAFT:
        # Only the submit starts a run; the other three answer for themselves.
        try:
            await wait_for_job(workspace_id, answer)
        except JobStillRunning as running:
            return still_running(running, RUN_GOES_ON)
    return await read_pipeline(ids)


@mcp_server.tool(
    title="Add transformation steps",
    annotations=CHANGES,
    description=(
        "Add transformations to a view's pipeline and wait for them to run."
        " Pass one operation or several: several are run together, once, after"
        f" the last. Operations: {OPERATION_NAMES}. Call"
        " get_transformation_schema for the arguments of an operation before"
        " using it, and get_view for the view's column names. Columns are named"
        " by their display name."
    ),
)
async def add_transformations(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    operations: list[dict[str, JsonValue]],
) -> dict[str, JsonValue]:
    """Add transformations to a view, and run its pipeline once.

    The steps are staged in draft mode and run together after the last one, so
    a step may use a column an earlier one adds. If a step cannot be added,
    none is kept. A step that is added and then fails when it runs IS kept:
    the view keeps it, and `get_pipeline` shows its error. If the view is
    already in draft mode, the steps stay staged for `manage_draft`.

    A step that adds a column leaves the view with columns this does not
    report. Call `get_view` again before reading rows or naming a column: the
    new column has an internal name of its own, and `get_data` takes internal
    names rather than the name a person reads.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view to transform.
        operations: The transformations, in order. Each is an object like
            `{"op": "limit", "n": 10}`, shaped as `get_transformation_schema`
            describes for its `op`.

    Returns:
        The pipeline's state afterwards, as `get_pipeline` reports it. When
        the run outlasts the call: the run's `job_id` and what to do next.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    # The API refuses to show the pipeline to a caller who may not see the view.
    pipeline = await read_pipeline(ids)
    steps = [read_operation(operation) for operation in operations]
    if pipeline[PipelineFields.DRAFT_MODE] == PipelineFields.NOT_DRAFTING:
        try:
            await run_in_one_draft(ids, steps)
        except JobStillRunning as running:
            return still_running(running, STEPS_RUN_ON)
    else:
        await stage_steps(ids, steps)
    return await read_pipeline(ids)


@mcp_server.tool(title="Run pipeline", annotations=DESTRUCTIVE)
async def run_pipeline(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int
) -> dict[str, JsonValue]:
    """Run all of a view's steps again, e.g. after its dataset got new data.

    Waits for the run and reports any step that failed.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.

    Returns:
        The pipeline's state after the run, as `get_pipeline` reports it. When
        the run outlasts the call: the run's `job_id` and what to do next.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with _pipeline(ids) as pipeline:
        started = await read_sdk_errors(
            pipeline.edit_pipeline(
                ids["dataview_id"],
                [PipelineFields.RUN],
                dataset_id=ids["dataset_id"],
            )
        )
    try:
        finished = await wait_for_job(workspace_id, started)
    except JobStillRunning as running:
        return still_running(running, RUN_GOES_ON)
    check_run(finished, "The pipeline")
    return await read_pipeline(ids)


def view_ids(workspace_id: int, project_id: int, dataset_id: int, view_id: int) -> dict[str, int]:
    """The path ids of a view, named as the API's routes name them."""
    return {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "dataset_id": dataset_id,
        "dataview_id": view_id,
    }


async def run_in_one_draft(ids: dict[str, int], steps: list[TransformOperation]) -> None:
    """Stage the steps in a draft of their own, run them once, and leave draft mode.

    A step that cannot be added drops the draft, so the view is left as it was.
    A step that is added and then fails when it RUNS is kept: the draft is
    spent, and the route refuses to discard it. Either way the caller is told
    why the step failed — the tidying up can fail too, and its own error must
    never take the place of that reason.

    A run that outlasts the tool call is left in draft mode: leaving it now
    would land under the run.

    Raises:
        JobStillRunning: If the run outlasts the tool call.
    """
    await change_draft(ids, PipelineFields.DRAFT_ON)
    try:
        await stage_steps(ids, steps)
        submitted = await change_draft(ids, PipelineFields.DRAFT_SUBMIT)
    except Exception:
        await tidy_up(ids, PipelineFields.DRAFT_DISCARD)
        await tidy_up(ids, PipelineFields.DRAFT_OFF)
        raise
    try:
        finished = await wait_for_job(ids["workspace_id"], submitted)
    except JobStillRunning:
        raise
    except Exception:
        await tidy_up(ids, PipelineFields.DRAFT_OFF)
        raise
    await tidy_up(ids, PipelineFields.DRAFT_OFF)
    check_run(finished, "The pipeline")


async def tidy_up(ids: dict[str, int], operation: str) -> None:
    """Put a view's draft mode back, without hiding why we are putting it back."""
    with suppress(ToolError):
        await change_draft(ids, operation)


async def stage_steps(ids: dict[str, int], steps: list[TransformOperation]) -> None:
    """Add the steps in order: each is built on the columns the one before left."""
    for step in steps:
        await add_step(ids, step)


@asynccontextmanager
async def _pipeline(ids: dict[str, int]) -> AsyncIterator[PipelineAPI]:
    """The SDK's pipeline client for the caller, in the view's own project.

    It reads the project off the client rather than taking it, and refuses one
    that has none. Leaving the block closes the client's connections.
    """
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        yield client.pipeline


async def read_pipeline(ids: dict[str, int]) -> dict[str, JsonValue]:
    """Read a view's pipeline state."""
    async with _pipeline(ids) as pipeline:
        return await read_sdk_errors(
            pipeline.get_pipeline(ids["dataview_id"], dataset_id=ids["dataset_id"])
        )


async def change_draft(ids: dict[str, int], operation: str) -> dict[str, JsonValue]:
    """Send one draft operation (enter, exit, submit or discard) for a view."""
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        return await read_sdk_errors(
            client.dataviews.draft_mode(
                ids["dataset_id"],
                ids["dataview_id"],
                operation,
                project_id=ids["project_id"],
            )
        )
