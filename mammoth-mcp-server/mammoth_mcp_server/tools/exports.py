"""Send a view's data to a destination: one tool for every destination.

An export is the tail of a pipeline. It runs when the view runs and writes the
view's rows to a database, a file store, an email or another Mammoth dataset.

The destinations, the settings each one needs and the envelope the API takes are
mm-pysdk's (`mammoth._pure.builders`), imported rather than copied, so the SDK
and this server always accept the same settings. The settings differ so much
between destinations that sending them all with every request is not possible:
`get_export_schema` returns one destination's settings on demand.
"""

from mammoth._pure.builders import _EXPORT_CONTRACTS, build_export_spec
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from mammoth.models.exports import AddExportSpec, HandlerType, TriggerType
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from ..consts import JobFields
from ..jobs import wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from .pipeline import view_ids

DESTINATIONS = ", ".join(sorted(handler.value for handler in HandlerType))
# Destinations mm-pysdk has no settings contract for. Their settings go to
# the API unchecked, which judges them itself.
_UNCHECKED = frozenset(HandlerType) - frozenset(_EXPORT_CONTRACTS)


@mcp_server.tool(
    description=(
        "Add an export to a view's pipeline and wait for it to run, so the"
        " view's rows reach the destination. Destinations:"
        f" {DESTINATIONS}. Call get_export_schema for a destination's settings."
    )
)
async def add_export(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    destination: str,
    settings: dict[str, JsonValue],
    run_now: bool = True,
) -> dict[str, JsonValue]:
    """Add an export to a view's pipeline and wait for it to run.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view to export from.
        destination: Where the rows go, e.g. "sftp" or "internal_dataset".
        settings: How to reach the destination, as `get_export_schema` describes
            it. Credentials go here; Mammoth stores them encrypted.
        run_now: Run the export as soon as it is added.

    Returns:
        The view's exports afterwards, as `list_exports` reports them.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with build_client(workspace_id, project_id) as client:
        started = await read_sdk_errors(
            client.exports.create(
                view_id,
                build_export(destination, settings, view_id, run_now),
                dataset_id=dataset_id,
                project_id=project_id,
            )
        )
        await wait_for_job(workspace_id, started.model_dump(mode="json"))
        return await read_exports(client, ids)


@mcp_server.tool()
async def get_export_schema(destination: str) -> dict[str, JsonValue]:
    """Get the settings one export destination needs.

    Args:
        destination: Where the rows would go, e.g. "sftp" or "postgres".

    Returns:
        `required`: settings the destination cannot work without. `optional`:
        settings it accepts. `defaults`: what an omitted setting falls back to.
        `checked`: whether Mammoth checks the settings before sending them —
        when False, `required` and `optional` are empty and the destination
        judges the settings itself.
    """
    handler = read_destination(destination)
    contract = _EXPORT_CONTRACTS.get(handler)
    if contract is None:
        return {"destination": handler.value, "checked": False}
    return {
        "destination": handler.value,
        "checked": True,
        "required": list(contract.required),
        "optional": list(contract.optional),
        "defaults": dict(contract.defaults),
        "other_settings_allowed": contract.allow_extra,
    }


@mcp_server.tool()
async def list_exports(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int
) -> dict[str, JsonValue]:
    """List a view's exports.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.

    Returns:
        `exports`: each export's `id`, `handler_type`, `sequence`, `status` and
        the `target_properties` it was set up with.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with build_client(workspace_id, project_id) as client:
        return await read_exports(client, ids)


@mcp_server.tool()
async def get_export(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int, export_id: int
) -> dict[str, JsonValue]:
    """Get one export of a view, including how its last run went.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        export_id: The export's `id`, as `list_exports` lists it.
    """
    async with build_client(workspace_id, project_id) as client:
        return await read_sdk_errors(
            client.exports.get(view_id, export_id, dataset_id=dataset_id, project_id=project_id)
        )


@mcp_server.tool()
async def delete_export(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int, export_id: int
) -> dict[str, JsonValue]:
    """Delete one export of a view. Rows already sent are not taken back.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        export_id: The export's `id`, as `list_exports` lists it.

    Returns:
        The view's exports afterwards, as `list_exports` reports them.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    async with build_client(workspace_id, project_id) as client:
        answer = await read_sdk_errors(
            client.exports.delete(view_id, export_id, dataset_id=dataset_id, project_id=project_id)
        )
        # The delete answers with the export when it is dropped outright, and
        # with a job when the pipeline has to run again without it.
        if JobFields.JOB in answer:
            await wait_for_job(workspace_id, answer)
        return await read_exports(client, ids)


def read_destination(destination: str) -> HandlerType:
    """Read a destination name, or name the ones there are.

    Raises:
        ToolError: If no destination goes by that name.
    """
    try:
        return HandlerType(destination)
    except ValueError as unknown:
        raise ToolError(
            f"There is no export destination {destination!r}." f" Destinations: {DESTINATIONS}."
        ) from unknown


def build_export(
    destination: str, settings: dict[str, JsonValue], view_id: int, run_now: bool
) -> AddExportSpec:
    """Build the export `POST exports` takes, checking the settings where it can.

    Raises:
        ToolError: If the destination does not exist, or its settings are wrong.
    """
    handler = read_destination(destination)
    if handler in _UNCHECKED:
        return AddExportSpec(
            DATAVIEW_ID=view_id,
            handler_type=handler,
            trigger_type=TriggerType.PIPELINE,
            target_properties=dict(settings),
            run_immediately=run_now,
        )
    try:
        return AddExportSpec.model_validate(
            build_export_spec(handler, settings, dataview_id=view_id, run_immediately=run_now)
        )
    except (MammothValidationError, ValidationError) as wrong_settings:
        raise ToolError(str(wrong_settings)) from wrong_settings


async def read_exports(client: MammothClient, ids: dict[str, int]) -> dict[str, JsonValue]:
    """Read a view's exports, through the client the caller already has.

    Args:
        client: The caller's SDK client, in the view's own project.
        ids: The view's path ids, as `view_ids` names them.
    """
    paged = await read_sdk_errors(
        client.exports.list(ids["dataview_id"], dataset_id=ids["dataset_id"])
    )
    return dict(paged.model_dump(mode="json"))
