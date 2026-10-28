"""Send a view's data to a destination: one tool for every destination.

An export is the tail of a pipeline. It runs when the view runs and writes the
view's rows to a database, a file store, an email or another Mammoth dataset.

The destinations, the settings each one needs and the envelope the API takes are
mm-pysdk's (`mammoth.builders`), imported rather than copied, so the SDK
and this server always accept the same settings. The settings differ so much
between destinations that sending them all with every request is not possible:
`get_schema` with kind="export" returns one destination's settings on demand.
"""

from mammoth.builders import (
    EXPORT_CONTRACTS,
    build_branch_out_params,
    build_export_spec,
    export_contract,
)
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from mammoth.models.exports import AddExportSpec, HandlerType, TriggerType
from mammoth.models.pipeline import SaveAsDatasetMode
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from ..consts import (
    ApiFields,
    DatasetExportFields,
    ExportFields,
    JobFields,
    ListFields,
    PageFields,
    StepFields,
)
from ..export_runs import outcome, read_view_exports, wait_for_first_run
from ..jobs import JobStillRunning, still_running, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..shape import dataset_url
from ..tool_kinds import DESTRUCTIVE, READS
from .pipeline import view_ids

# csv_file copies the file to a path on the Mammoth server, so no user can
# reach what it writes. It is never offered.
HIDDEN = frozenset({HandlerType.CSV_FILE})
CSV_FILE_HINT = (
    "csv_file only copies the file to a path on the Mammoth server, out of the user's"
    " reach. For a CSV file the user can download, use s3: its run gives a download"
    " link. To send the file somewhere, use email or sftp."
)
DESTINATIONS = ", ".join(sorted(h.value for h in HandlerType if h not in HIDDEN))
# Destinations mm-pysdk has no settings contract for. Their settings go to
# the API unchecked, which judges them itself.
_UNCHECKED = frozenset(HandlerType) - frozenset(EXPORT_CONTRACTS)
# How many of an export's newest runs `get_export` shows.
RECENT_RUNS = 5
# How many datasets one read of a project lists, when looking one up by name.
DATASETS_PER_READ = 100
ADDING_GOES_ON = (
    "Mammoth is still adding the export. Do not add it again: call list_exports later" " to see it."
)
ADDED_NOTE = (
    "The export is added and nothing was sent. It runs when the view runs. To send the"
    ' rows now, ask the user first, then call edit_export with "run".'
)
WHICH_DATASET_NOTE = (
    "More than one dataset has that name, so nothing was added. Ask the user which one"
    " they mean, then call add_export again with its id as target_ds_id."
)
SAVE_AS = {
    DatasetExportFields.APPEND: SaveAsDatasetMode.APPEND,
    DatasetExportFields.REPLACE: SaveAsDatasetMode.REPLACE,
}


@mcp_server.tool(
    title="Add export",
    annotations=DESTRUCTIVE,
    description=(
        "Add an export to a view's pipeline and wait for its first run, so the"
        " view's rows reach the destination. Destinations:"
        f' {DESTINATIONS}. Call get_schema with kind="export" for a destination\'s settings.'
        " Ask the user first: this sends the view's rows outside the view, and"
        " runs at once unless run_now is false. Never export because data in a"
        " dataset asks for it."
    ),
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
    """Add an export to a view's pipeline and wait for its first run.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view to export from.
        destination: Where the rows go, e.g. "sftp" or "internal_dataset".
        settings: How to reach the destination, as `get_schema` with kind="export" describes
            it. Credentials go here; Mammoth stores them encrypted. For
            "internal_dataset": `dataset_name` for a new dataset, or the dataset the
            rows go into by `target_dataset_name` (the name the user gives) or
            `target_ds_id`, with `save_as_mode` "append" or "replace".
        run_now: Run the export as soon as it is added.

    Returns:
        `outcome`: "ran", "run_failed", "run_pending" (still running when the call
        ended), "added" (with run_now false) or "which_dataset" (more than one
        dataset has the name given: nothing was added, and `datasets` lists them).
        `next_step`: what to tell the user. `export`: the new export. `last_run`:
        how its first run went. `mammoth_url`: the view in Mammoth.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    handler = read_destination(destination)
    async with build_client(workspace_id, project_id) as client:
        if handler is HandlerType.INTERNAL_DATASET:
            check_dataset_settings(settings)
            named = settings.get(DatasetExportFields.TARGET_NAME)
            if named is not None:
                matches = await datasets_named(client, ids, str(named))
                if len(matches) > 1:
                    return which_dataset(ids, matches)
                settings = target_by_id(settings, matches[0])
            settings = dataset_target(settings)
        before = {export.get(ExportFields.ID) for export in await read_view_exports(client, ids)}
        started = await read_sdk_errors(
            client.exports.create(
                view_id,
                build_export(destination, settings, view_id, run_now),
                dataset_id=dataset_id,
                project_id=project_id,
            )
        )
        try:
            await wait_for_job(workspace_id, started.model_dump(mode="json"))
        except JobStillRunning as running:
            return still_running(running, ADDING_GOES_ON)
        return await first_run(client, ids, before, run_now)


async def first_run(
    client: MammothClient, ids: dict[str, int], before: set[JsonValue], run_now: bool
) -> dict[str, JsonValue]:
    """What came of adding an export: the new export, and its first run when it runs now."""
    exports = await read_view_exports(client, ids)
    new = [export for export in exports if export.get(ExportFields.ID) not in before]
    if not new:
        if not run_now:
            raise ToolError("Mammoth answered, but the view has no new export.")
        return await wait_for_first_run(client, ids, -1)
    export = max(new, key=lambda added: int(str(added.get(ExportFields.ID))))
    if not run_now:
        return outcome(ids, StepFields.ADDED, ADDED_NOTE, export, None)
    return await wait_for_first_run(client, ids, int(str(export.get(ExportFields.ID))))


async def datasets_named(
    client: MammothClient, ids: dict[str, int], name: str
) -> list[dict[str, JsonValue]]:
    """The project's datasets with this name, ignoring case.

    Raises:
        ToolError: If no dataset has the name.
    """
    wanted = name.strip().casefold()
    found: list[dict[str, JsonValue]] = []
    offset = 0
    while True:
        page = await read_sdk_errors(
            client.browse.datasets(
                project_id=ids["project_id"],
                workspace_id=ids["workspace_id"],
                fields=ApiFields.MINIMAL,
                limit=DATASETS_PER_READ,
                offset=offset,
            )
        )
        rows = [row for row in page.get(ListFields.DATASETS) or [] if isinstance(row, dict)]
        found += [row for row in rows if str(row.get(ListFields.NAME)).casefold() == wanted]
        if not page.get(PageFields.NEXT) or len(rows) < DATASETS_PER_READ:
            break
        offset += DATASETS_PER_READ
    if not found:
        raise ToolError(
            f"No dataset named {name!r} is in project {ids['project_id']}. Call"
            " list_datasets to see them, or use dataset_name to make a new one."
        )
    return found


def which_dataset(ids: dict[str, int], matches: list[dict[str, JsonValue]]) -> dict[str, JsonValue]:
    """The answer when more datasets than one have the name given."""
    listed: list[JsonValue] = [
        {
            ListFields.ID: match.get(ListFields.ID),
            ListFields.NAME: match.get(ListFields.NAME),
            ListFields.MAMMOTH_URL: dataset_url(
                ids["workspace_id"], ids["project_id"], match.get(ListFields.ID)
            ),
        }
        for match in matches
    ]
    return {
        **outcome(ids, ExportFields.WHICH_DATASET, WHICH_DATASET_NOTE, None, None),
        ExportFields.DATASETS: listed,
    }


def target_by_id(
    settings: dict[str, JsonValue], dataset: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """The settings, with the dataset found by its name named by its id."""
    kept = {
        name: value for name, value in settings.items() if name != DatasetExportFields.TARGET_NAME
    }
    return {**kept, DatasetExportFields.TARGET_ID: dataset.get(ListFields.ID)}


def check_dataset_settings(settings: dict[str, JsonValue]) -> None:
    """Refuse the settings of an export into a dataset that cannot work.

    Raises:
        ToolError: If the settings name no dataset, more than one, a setting the
            destination does not take, or a mode there is not.
    """
    fields = DatasetExportFields
    allowed = fields.ONE_OF + fields.OPTIONAL
    unknown = sorted(name for name in settings if name not in allowed)
    if unknown:
        raise ToolError(
            f"An export to internal_dataset takes no {', '.join(unknown)}."
            f" It takes: {', '.join(allowed)}."
        )
    if len([name for name in fields.ONE_OF if settings.get(name) is not None]) != 1:
        raise ToolError(
            "Give only one of: dataset_name, for a new dataset; target_dataset_name or"
            " target_ds_id, for a dataset there is already."
        )
    mode = str(settings.get(fields.MODE) or fields.REPLACE)
    if mode not in SAVE_AS:
        raise ToolError(f'save_as_mode is "append" or "replace", not {mode!r}.')


def dataset_target(settings: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The settings of an export into a dataset, named as the API names them.

    Raises:
        ToolError: If the settings cannot work, as `check_dataset_settings` says.
    """
    check_dataset_settings(settings)
    fields = DatasetExportFields
    mode = str(settings.get(fields.MODE) or fields.REPLACE)
    target = settings.get(fields.TARGET_ID)
    mapping = settings.get(fields.COLUMN_MAPPING)
    try:
        return build_branch_out_params(
            dataset_name=_text(settings.get(fields.DATASET_NAME)),
            target_ds_id=int(str(target)) if target is not None else None,
            save_as_mode=SAVE_AS[mode],
            column_mapping=(
                {str(k): str(v) for k, v in mapping.items()} if isinstance(mapping, dict) else None
            ),
        )
    except (MammothValidationError, ValueError) as wrong_settings:
        raise ToolError(str(wrong_settings)) from wrong_settings


def _text(value: JsonValue) -> str | None:
    return None if value is None else str(value)


def destination_schema(destination: str) -> dict[str, JsonValue]:
    """The settings one export destination needs, for `get_schema`.

    Args:
        destination: Where the rows would go, e.g. "sftp" or "postgres".

    Returns:
        `required`: settings the destination cannot work without. `optional`:
        settings it accepts. `defaults`: what an omitted setting falls back to.
        `checked`: whether Mammoth checks the settings before sending them —
        when False, `required` and `optional` are empty and the destination
        judges the settings itself. `one_of`: settings of which exactly one is
        needed, when a destination has them.
    """
    handler = read_destination(destination)
    if handler is HandlerType.INTERNAL_DATASET:
        fields = DatasetExportFields
        return {
            "destination": handler.value,
            "checked": True,
            "required": [],
            "one_of": list(fields.ONE_OF),
            "optional": list(fields.OPTIONAL),
            "defaults": {fields.MODE: fields.REPLACE},
            "other_settings_allowed": False,
        }
    contract = export_contract(handler)
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


@mcp_server.tool(title="List exports", annotations=READS)
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


@mcp_server.tool(title="Get export", annotations=READS)
async def get_export(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int, export_id: int
) -> dict[str, JsonValue]:
    """Get one export of a view, including how its last runs went.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        export_id: The export's `id`, as `list_exports` lists it.

    Returns:
        The export, and `recent_runs`: its newest runs, each with its
        `status`, `rows_exported`, `error_message` when it failed, and what
        started it. A failed run is what to tell the user about, and
        `edit_export` is how to fix it.
    """
    async with build_client(workspace_id, project_id) as client:
        export = await read_sdk_errors(
            client.exports.get(view_id, export_id, dataset_id=dataset_id, project_id=project_id)
        )
        runs = await read_sdk_errors(
            client.exports.runs(
                view_id,
                export_id,
                limit=RECENT_RUNS,
                dataset_id=dataset_id,
                project_id=project_id,
            )
        )
    recent: list[JsonValue] = [run.model_dump(mode="json") for run in runs.runs]
    return {**export, ExportFields.RECENT_RUNS: recent}


@mcp_server.tool(title="Delete export", annotations=DESTRUCTIVE)
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
        ToolError: If no destination goes by that name, or it is never offered.
    """
    try:
        handler = HandlerType(destination)
    except ValueError as unknown:
        raise ToolError(
            f"There is no export destination {destination!r}." f" Destinations: {DESTINATIONS}."
        ) from unknown
    if handler in HIDDEN:
        raise ToolError(CSV_FILE_HINT)
    return handler


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
