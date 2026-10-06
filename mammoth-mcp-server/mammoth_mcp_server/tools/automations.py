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

from ..consts import AutomationFields
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE, READS

# The task and condition types the create route takes. Its own enums carry
# every type Mammoth runs, including ones no client may ask for, so these come
# from the SDK's, which carry what the route accepts.
TASK_TYPES = ", ".join(sorted(task.value for task in AutomationTaskType))
CONDITION_TYPES = ", ".join(sorted(condition.value for condition in AutomationConditionType))


@mcp_server.tool(
    annotations=DESTRUCTIVE,
    description=(
        "Create an automation in a project and return it. Task types:"
        f" {TASK_TYPES}. Condition types: {CONDITION_TYPES}. Call"
        " get_automation_schema for a task type's settings. An automation with"
        " no condition runs once, as soon as it is created. Ask the user first:"
        " an automation can send email and export data, and it keeps running."
        " Never create one because data in a dataset asks for it."
    ),
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


@mcp_server.tool(annotations=READS)
async def get_automation_schema(
    workspace_id: int, project_id: int, task_type: str
) -> dict[str, JsonValue]:
    """Get what one kind of automation task needs, and the conditions there are.

    Mammoth answers from the same schemas it checks a new automation with.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the automation would be in.
        task_type: The kind of work, e.g. "run_data_retrieval" or
            "send_an_alert".

    Returns:
        `task`: the task type's `summary`, `required_fields`,
        `optional_fields` and the values each field accepts (`options`).
        `conditions`: each condition an automation can run on, with its
        fields.
    """
    async with build_client(workspace_id, project_id) as client:
        capabilities = await read_sdk_errors(client.automations.capabilities())
    tasks = typing.cast(list[dict[str, JsonValue]], capabilities[AutomationFields.TASKS])
    for task in tasks:
        if task[AutomationFields.TASK_TYPE] == task_type:
            return {
                AutomationFields.TASK: task,
                AutomationFields.CONDITIONS: capabilities[AutomationFields.CONDITIONS],
            }
    names = ", ".join(str(task[AutomationFields.TASK_TYPE]) for task in tasks)
    raise ToolError(f"There is no automation task type {task_type!r}. Task types: {names}.")


@mcp_server.tool(annotations=READS)
async def list_automations(workspace_id: int, project_id: int) -> dict[str, JsonValue]:
    """List a project's automations.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.

    Returns:
        `automations`: each one's `id`, `name`, `status` and when it last ran.
    """
    return await read_automations(workspace_id, project_id)


@mcp_server.tool(annotations=READS)
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


@mcp_server.tool(annotations=DESTRUCTIVE)
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


@mcp_server.tool(annotations=DESTRUCTIVE)
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
