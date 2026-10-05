"""Schedule work in a project: refresh data, consolidate a folder, send an alert.

An automation is a list of tasks and the conditions that set them off. The
conditions decide when: at a time, on a recurrence, or when a file lands in a
folder. With no condition at all, the automation runs once, immediately.

Every task type takes its own `details`, and all of them together are far too
large to send with every request, so `get_automation_schema` returns one task
type's shape on demand — the same split `add_transformations` and `add_export`
use.
"""

import typing

from mammoth.models.automations import (
    AutomationConditionSpec,
    AutomationConditionType,
    AutomationPatchItem,
    AutomationPatchOp,
    AutomationPatchPath,
    AutomationTaskSpec,
    AutomationTaskType,
    PatchAutomationDetails,
)
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from ..automation_examples import AUTOMATION_EXAMPLES
from ..consts import AutomationFields
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server

# The task and condition types the create route takes. Its own enums carry
# every type Mammoth runs, including ones no client may ask for, so these come
# from the SDK's, which carry what the route accepts.
TASK_TYPES = ", ".join(sorted(task.value for task in AutomationTaskType))
CONDITION_TYPES = ", ".join(sorted(condition.value for condition in AutomationConditionType))
DOCUMENTED_EXAMPLES = AUTOMATION_EXAMPLES


@mcp_server.tool(
    description=(
        "Create an automation in a project and return it. Task types:"
        f" {TASK_TYPES}. Condition types: {CONDITION_TYPES}. Call"
        " get_automation_schema for a task type's settings. An automation with"
        " no condition runs once, as soon as it is created."
    )
)
async def create_automation(
    workspace_id: int,
    project_id: int,
    name: str,
    tasks: list[dict[str, JsonValue]],
    conditions: list[dict[str, JsonValue]] | None = None,
    description: str = "",
) -> dict[str, JsonValue]:
    """Create an automation in a project and return it.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the automation belongs to.
        name: What to call it.
        tasks: What it does. Each task is `{"task_type": ..., "details": {...}}`,
            as `get_automation_schema` describes it.
        conditions: When it runs. Each is `{"condition_type": ..., "details":
            {...}}`. **Leave this out and the automation runs once, straight
            away** — give it a condition to schedule it instead.
        description: What it is for, for whoever reads the list later.

    Returns:
        The automation that was created.
    """
    async with build_client(workspace_id, project_id) as client:
        return await read_sdk_errors(
            client.automations.create(
                name,
                description,
                read_tasks(tasks),
                conditions=read_conditions(conditions or []),
            )
        )


@mcp_server.tool()
async def get_automation_schema(task_type: str) -> dict[str, JsonValue]:
    """Get what one kind of automation task needs, with a worked example.

    Args:
        task_type: The kind of work, e.g. "run_data_retrieval" or
            "send_an_alert".

    Returns:
        `example`: a whole `create_automation` body that uses this task type,
        if one is written down. `condition_types`: the conditions an automation
        can run on.
    """
    task = read_task_type(task_type)
    return {
        AutomationFields.TASK_TYPE: task.value,
        "example": find_example(task, DOCUMENTED_EXAMPLES),
        "condition_types": sorted(condition.value for condition in AutomationConditionType),
    }


@mcp_server.tool()
async def list_automations(workspace_id: int, project_id: int) -> dict[str, JsonValue]:
    """List a project's automations.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.

    Returns:
        `automations`: each one's `id`, `name`, `status` and when it last ran.
    """
    return await read_automations(workspace_id, project_id)


@mcp_server.tool()
async def get_automation(
    workspace_id: int, project_id: int, automation_id: int
) -> dict[str, JsonValue]:
    """Get one automation: what it does, when it runs, and how it last went.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        automation_id: Which automation, as `list_automations` lists it.
    """
    async with build_client(workspace_id, project_id) as client:
        found = await read_sdk_errors(client.automations.get(automation_id))
    # The route wraps the automation in a one-key object; a tool that returned
    # the wrapper would make every caller unwrap it.
    return typing.cast(dict[str, JsonValue], found[AutomationFields.AUTOMATION])


@mcp_server.tool()
async def update_automation(
    workspace_id: int,
    project_id: int,
    automation_id: int,
    name: str | None = None,
    description: str | None = None,
    active: bool | None = None,
) -> dict[str, JsonValue]:
    """Rename an automation, or stop and start it. Returns it afterwards.

    A suspended automation keeps its tasks and its schedule and does not run.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        automation_id: Which automation.
        name: A new name. Leave out to keep the one it has.
        description: A new description. Leave out to keep the one it has.
        active: False to suspend it, True to start it running again. Leave out
            to leave it as it is.

    Returns:
        The automation afterwards, as `get_automation` reports it.
    """
    async with build_client(workspace_id, project_id) as client:
        for patch in build_patches(name, description, active):
            await read_sdk_errors(client.automations.update(automation_id, [patch]))
    return await get_automation(workspace_id, project_id, automation_id)


@mcp_server.tool()
async def delete_automation(
    workspace_id: int, project_id: int, automation_id: int
) -> dict[str, JsonValue]:
    """Move an automation to the trash, where it can still be restored.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        automation_id: Which automation.

    Returns:
        The project's automations afterwards, as `list_automations` reports them.
    """
    async with build_client(workspace_id, project_id) as client:
        await read_sdk_errors(client.automations.trash(automation_id))
    return await read_automations(workspace_id, project_id)


def read_task_type(task_type: str) -> AutomationTaskType:
    """Read a task type's name, or name the ones there are.

    Raises:
        ToolError: If no task type goes by that name.
    """
    try:
        return AutomationTaskType(task_type)
    except ValueError as unknown:
        raise ToolError(
            f"There is no automation task type {task_type!r}." f" Task types: {TASK_TYPES}."
        ) from unknown


def find_example(
    task: AutomationTaskType, examples: list[dict[str, JsonValue]]
) -> dict[str, JsonValue] | None:
    """Find a worked example that uses a task type.

    Two of the create route's examples once carried a name no enum has, which
    the route itself would have rejected. So an example is offered only when
    every task type in it is real — a stale one is skipped rather than taught.

    Args:
        task: The task type the example has to use.
        examples: Whole `create_automation` bodies to choose from.
    """
    real = {member.value for member in AutomationTaskType}
    for body in examples:
        tasks = typing.cast(list[dict[str, JsonValue]], body[AutomationFields.TASKS])
        types = {task_spec[AutomationFields.TASK_TYPE] for task_spec in tasks}
        if task.value in types and types <= real:
            return body
    return None


def build_patches(
    name: str | None, description: str | None, active: bool | None
) -> list[AutomationPatchItem]:
    """Build one patch per thing the caller asked to change."""
    patches: list[AutomationPatchItem] = []
    # Only the fields the caller named: a patch carries what changes, and an
    # unset field is left as it is rather than blanked.
    changed = {
        field: value
        for field, value in (
            (AutomationFields.NAME, name),
            (AutomationFields.DESCRIPTION, description),
        )
        if value is not None
    }
    if changed:
        patches.append(
            AutomationPatchItem(
                op=AutomationPatchOp.REPLACE,
                path=AutomationPatchPath.DETAILS,
                value=PatchAutomationDetails.model_validate(changed),
            )
        )
    if active is not None:
        patches.append(
            AutomationPatchItem(
                op=AutomationPatchOp.REPLACE,
                path=AutomationPatchPath.STATUS,
                value=(AutomationFields.RESTORE if active else AutomationFields.SUSPEND),
            )
        )
    return patches


async def read_automations(workspace_id: int, project_id: int) -> dict[str, JsonValue]:
    """Read a project's automations."""
    async with build_client(workspace_id, project_id) as client:
        listed = await read_sdk_errors(client.automations.list())
    # The SDK unwraps the route's one-key object; the tool's callers read it.
    return {AutomationFields.AUTOMATIONS: list[JsonValue](listed)}


def read_tasks(tasks: list[dict[str, JsonValue]]) -> list[AutomationTaskSpec]:
    """Check each task against what the create route takes.

    Raises:
        ToolError: If a task is not one the route would run, with the reason.
    """
    try:
        return [AutomationTaskSpec.model_validate(task) for task in tasks]
    except ValidationError as error:
        raise ToolError(f"Invalid task: {error}") from error


def read_conditions(
    conditions: list[dict[str, JsonValue]],
) -> list[AutomationConditionSpec]:
    """Check each condition against what the create route takes.

    Raises:
        ToolError: If a condition is not one the route would run.
    """
    try:
        return [AutomationConditionSpec.model_validate(each) for each in conditions]
    except ValidationError as error:
        raise ToolError(f"Invalid condition: {error}") from error
