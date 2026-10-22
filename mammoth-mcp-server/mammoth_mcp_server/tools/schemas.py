"""What a tool's argument takes: an operation, an export destination, an automation task.

One tool answers all three, so a model has one place to look before it writes
one, and the tool list a client sends with every request stays short.
"""

from typing import Literal

from mcp.server.mcpserver.exceptions import ToolError

from ..sdk import JsonValue
from ..server import mcp_server
from ..tool_kinds import READS
from .automations import task_schema
from .exports import destination_schema
from .transformations import operation_schema

type SchemaKind = Literal["transformation", "export", "automation"]

NAME_THE_PROJECT = (
    "An automation task's schema is Mammoth's to answer per project: name the"
    " workspace_id and project_id."
)


@mcp_server.tool(title="Get schema: step, export or automation", annotations=READS)
async def get_schema(
    kind: SchemaKind,
    of: str,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, JsonValue]:
    """Get what a transformation, an export destination or an automation task takes.

    Call it before writing one: `add_transformations` and
    `edit_transformation_step` take a transformation, `add_export` and
    `edit_export` an export's settings, `create_automation` a task.

    Args:
        kind: "transformation", "export" or "automation".
        of: The operation (e.g. "limit" or "math"), the destination (e.g.
            "sftp" or "postgres") or the task type (e.g. "run_data_retrieval"
            or "send_an_alert").
        workspace_id: For "automation" only: which workspace.
        project_id: For "automation" only: which project the automation
            would be in.

    Returns:
        For "transformation": the operation's arguments, as a JSON schema.
        For "export": `required` settings, `optional` ones and their
        `defaults`, and `checked`: whether Mammoth checks them before sending
        (when false, the destination judges them itself). For "automation":
        `task`, with its `required_fields`, `optional_fields` and the values
        each accepts (`options`), and every condition it can run on.
    """
    if kind == "transformation":
        return operation_schema(of)
    if kind == "export":
        return destination_schema(of)
    if workspace_id is None or project_id is None:
        raise ToolError(NAME_THE_PROJECT)
    return await task_schema(workspace_id, project_id, of)
