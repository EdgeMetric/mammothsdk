"""What a transformation is, and how one becomes a step of a view's pipeline.

`add_transformations` in `pipeline.py` is the tool that adds them; everything
it needs to read, validate, build and run one step lives here.

The operations and their argument shapes are in `transform_operations.py`; the
code that turns one into a pipeline task is in `task_params.py`.

All shapes together are far too large to send with every request, so
`add_transformations` takes each operation as an object and
`get_transformation_schema` returns one operation's shape on demand.
"""

import typing
from typing import cast

from mammoth.client import MammothClient
from mammoth.exceptions import MammothColumnError, MammothValidationError
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, TypeAdapter, ValidationError

from ..consts import JobFields, TaskFields
from ..jobs import wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..task_params import build_task_param
from ..transform_operations import TransformOperation

_OPERATION_ADAPTER: TypeAdapter[TransformOperation] = TypeAdapter(TransformOperation)
_OPERATIONS: dict[str, type[BaseModel]] = {
    model.model_fields["op"].default: model
    for model in typing.get_args(typing.get_args(TransformOperation)[0])
}
OPERATION_NAMES = ", ".join(sorted(_OPERATIONS))


@mcp_server.tool()
async def get_transformation_schema(operation: str) -> dict[str, JsonValue]:
    """Get the arguments one transformation takes, as a JSON schema.

    Args:
        operation: The operation's name, e.g. "limit" or "math".
    """
    model = _OPERATIONS.get(operation)
    if model is None:
        raise ToolError(f"No operation '{operation}'. Operations: {OPERATION_NAMES}")
    return cast(dict[str, JsonValue], model.model_json_schema())


def read_operation(operation: dict[str, JsonValue]) -> TransformOperation:
    """Validate an operation against its shape, or explain what is wrong."""
    try:
        return _OPERATION_ADAPTER.validate_python(operation)
    except ValidationError as error:
        raise ToolError(f"Invalid operation: {error}") from error


async def add_step(ids: dict[str, int], operation: TransformOperation) -> dict[str, JsonValue]:
    """Add one step to a view, and wait for the change.

    Args:
        ids: The view's path ids: `workspace_id`, `project_id`, `dataset_id`
            and `dataview_id`.
        operation: The validated transformation.
    """
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        param = await build_param(client, operation, ids)
        answer = await read_sdk_errors(
            client.pipeline.add_task(ids["dataview_id"], param, dataset_id=ids["dataset_id"])
        )
    return await wait_for_change(ids["workspace_id"], answer)


async def build_param(
    client: MammothClient, operation: TransformOperation, ids: dict[str, int]
) -> dict[str, JsonValue]:
    """Turn a validated operation into the task the add-task route takes.

    The view's columns are read through the API as the caller, so a caller who
    may not see the view is refused before any column name can reach them.

    Raises:
        ToolError: The operation does not fit the view, in the builder's own
            words, or the API refused a read.
    """
    return await read_sdk_errors(explain_build_errors(client, operation, ids))


async def explain_build_errors(
    client: MammothClient, operation: TransformOperation, ids: dict[str, int]
) -> dict[str, JsonValue]:
    """Build the task, and say what is wrong with the operation in plain words."""
    try:
        return await build_task_param(client, operation, ids["dataset_id"], ids["dataview_id"])
    except (MammothColumnError, MammothValidationError) as error:
        raise ToolError(error.message) from error


async def wait_for_change(workspace_id: int, answer: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Wait for a pipeline change and the run it started, and return the change.

    In draft mode the change is staged and starts no run.
    """
    if TaskFields.STATUS not in answer:
        answer = await wait_for_job(workspace_id, answer)
    change = check_change(answer)
    run_id = change.get(TaskFields.RUN_ID)
    if run_id is None:
        return change
    run = await wait_for_job(workspace_id, {JobFields.JOB_ID: run_id})
    check_run(run, "The transformation was added but the pipeline")
    # The change was reported while its run was still going; the run is over.
    return {**change, TaskFields.STATUS: TaskFields.DONE}


def check_change(change: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Return a pipeline change that was made, or explain why it was not."""
    status = change[TaskFields.STATUS]
    running = status == TaskFields.PROCESSING and change.get(TaskFields.RUN_ID)
    if (status != TaskFields.DONE and not running) or change.get(TaskFields.HAS_ERROR):
        raise ToolError(f"The transformation was not added: {change.get(TaskFields.ERROR_INFO)}")
    return change


def check_run(run: dict[str, JsonValue], lead: str) -> None:
    """Explain why a pipeline run failed, if it did.

    Args:
        run: The run job's result.
        lead: How to open the message, e.g. "The pipeline".
    """
    if not run.get(TaskFields.HAS_ERROR):
        return
    results = run.get(TaskFields.TASK_RESULTS)
    tasks = results.values() if isinstance(results, dict) else []
    errors = [
        task[TaskFields.ERROR_DETAILS]
        for task in tasks
        if isinstance(task, dict) and task.get(TaskFields.ERROR_DETAILS)
    ]
    raise ToolError(f"{lead} failed to run: {errors}")
