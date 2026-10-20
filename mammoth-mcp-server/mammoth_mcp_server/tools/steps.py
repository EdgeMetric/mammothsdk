"""Change one step of a view's pipeline: what it does, or whether it runs.

One tool does all of it, so a model has one place to go to fix a step:
`edit_transformation_step` replaces what a step does, suspends it, or
restores it. It never leaves a pipeline broken without saying so:

- In draft mode the change is staged; `manage_draft` "run" runs it.
- Otherwise it runs at once. A run that makes a step fail that did not fail
  before is undone: the step is put back as it was, and the tool says what
  failed.
- Mammoth refuses a change that removes a column a later step reads. The
  tool names the columns and says how to change the steps together.
"""

from typing import Literal

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import JobFields, ListFields, PipelineFields, StepFields, TaskFields
from ..jobs import JobStillRunning, still_running, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..shape import view_url
from ..task_params import StepPlace
from ..tool_kinds import DESTRUCTIVE
from .pipeline import read_pipeline, read_steps, view_ids
from .transformations import build_param, check_change, failing_ids, problems_of, read_operation

type StepChange = Literal["replace", "suspend", "restore"]
REPLACE = "replace"
SUSPEND = "suspend"
RESTORE = "restore"
# The command that undoes each command.
UNDO = {SUSPEND: RESTORE, RESTORE: SUSPEND}

NOT_CHANGED = "The step was not changed"
EDIT_RUNS_ON = (
    "The step was changed and the view's run is still going. Do not change it again."
    " Call get_pipeline later: it lists any step in error, with what to do."
)
CHANGED_NOTE = "Tell the user the step was changed and the view ran again without errors."
STILL_FAILING_NOTE = (
    "The step was changed and the view ran again, but `problems` lists steps in error."
    " They were in error before this change too. Tell the user which, and why."
)
STAGED_NOTE = (
    "The view is in draft mode, so the change is staged and nothing ran. Tell the"
    ' user. Call manage_draft with "run" to run the staged changes, or "drop" to'
    " throw them away."
)
STAGED_BREAKS = (
    "The steps in `problems` now read a column that is not there, and will fail"
    " when the draft runs: change them first."
)
PUT_BACK_NOTE = (
    "The change made the steps in `problems` fail, so it was undone: the step is as"
    " it was and the view runs as before. Tell the user what failed and why, and"
    " offer a change that avoids it. Try it first with preview_transformation."
)
NOT_PUT_BACK_NOTE = (
    "The change made the steps in `problems` fail, and undoing it failed too: {error}."
    " The pipeline is left in error. Tell the user now, with `mammoth_url`: they can"
    " fix the step there, or go back to an earlier version in its version history."
)


@mcp_server.tool(title="Edit transformation step", annotations=DESTRUCTIVE)
async def edit_transformation_step(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    step_id: int,
    change: StepChange,
    operation: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Change one step of a view's pipeline, and wait for the view to run again.

    `change` says what to do:
    - "replace": the step does `operation` instead, in its own place. Name
      columns as they are at that step, before it runs.
    - "suspend": the step stays in the pipeline but stops running.
    - "restore": a suspended step runs again.

    Run now or draft: in draft mode the change is staged, and nothing runs
    until `manage_draft` "run". Otherwise it runs at once. Start draft mode
    first for changes that need each other, e.g. a step renames a column
    that later steps read: "start", change each step, "run", then "stop".

    When the run makes a step fail that did not fail before, the change is
    undone and `problems` says what failed. Mammoth refuses a change that
    removes a column a later step reads, and says which.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        step_id: The step's `id`, as `get_pipeline` lists it.
        change: "replace", "suspend" or "restore".
        operation: With "replace" only: what the step does instead, shaped as
            `add_transformations` takes each operation.

    Returns:
        `outcome`: "changed", "staged", "put_back" (the change failed and was
        undone) or "not_put_back" (it failed and is still in place).
        `next_step`: what to tell the user. `problems`: each step in error,
        with why. `step`: the step afterwards. `pipeline` and `mammoth_url`.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    before = await read_steps(ids)
    step = find_step(before, step_id)
    patch = await build_patch(ids, step, change, operation)
    drafting = (await read_pipeline(ids))[PipelineFields.DRAFT_MODE] != PipelineFields.NOT_DRAFTING
    try:
        run = await send_change(ids, step, patch)
    except JobStillRunning as running:
        return still_running(running, EDIT_RUNS_ON)
    after = await read_steps(ids)
    if drafting:
        staged = problems_of(after)
        note = f"{STAGED_NOTE} {STAGED_BREAKS}" if staged else STAGED_NOTE
        return await report(ids, step_id, StepFields.STAGED, note, staged)
    failing_before = failing_ids(before)
    if failing_ids(after, run) <= failing_before:
        note = STILL_FAILING_NOTE if failing_ids(after, run) else CHANGED_NOTE
        return await report(ids, step_id, StepFields.CHANGED, note, problems_of(after, run))
    return await put_back(ids, step, change, problems_of(after, run), failing_before)


def find_step(steps: list[dict[str, JsonValue]], step_id: int) -> dict[str, JsonValue]:
    """The step with this id, or why there is none.

    The edit route finds a step by its id alone, in any view, and then edits
    the step at that place in this one. So a step of another view is refused
    here, before anything is sent.
    """
    for step in steps:
        if step.get(StepFields.ID) == step_id:
            return step
    listed = [step.get(StepFields.ID) for step in steps]
    raise ToolError(
        f"This view has no step {step_id}. Its steps: {listed}. Call get_pipeline to see them."
    )


async def build_patch(
    ids: dict[str, int],
    step: dict[str, JsonValue],
    change: str,
    operation: dict[str, JsonValue] | None,
) -> dict[str, JsonValue]:
    """The edit route's patch for one change, or why the change cannot be made."""
    if change != REPLACE:
        if operation is not None:
            raise ToolError(f'Pass `operation` only with "replace", not with "{change}".')
        check_command(step, change)
        return command_patch(change)
    if operation is None:
        raise ToolError('"replace" needs `operation`: what the step does instead.')
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        param = await build_param(client, read_operation(operation), ids, place_of(step))
    keep_new_column_names(param, step.get(StepFields.PARAMS))
    return params_patch(ids, param)


def check_command(step: dict[str, JsonValue], change: str) -> None:
    """Refuse to suspend a suspended step, or to restore one that runs."""
    suspended = step.get(StepFields.STATUS) == StepFields.SUSPENDED
    if change == SUSPEND and suspended:
        raise ToolError(f"Step {step.get(StepFields.ID)} is suspended already.")
    if change == RESTORE and not suspended:
        raise ToolError(f"Step {step.get(StepFields.ID)} is not suspended: it runs already.")


def place_of(step: dict[str, JsonValue]) -> StepPlace:
    """Where a step stands: its sequence, and the columns it reads."""
    columns = step.get(StepFields.COLUMNS_READ)
    return StepPlace(
        sequence=int(str(step.get(StepFields.SEQUENCE))),
        columns=(
            [column for column in columns if isinstance(column, dict)]
            if isinstance(columns, list)
            else []
        ),
    )


def keep_new_column_names(new: JsonValue, old: JsonValue) -> None:
    """Give each column the new step makes the internal name the old step gave it.

    Later steps read a column by its internal name. A replaced step that makes
    a column of the same name keeps its internal name, so those steps still
    find it, in place of the fresh one the builder gave it. A column with a
    new name keeps the fresh one.
    """
    names = new_column_names(old)
    for spec in new_column_specs(new):
        name = spec.get(StepFields.NEW_COLUMN)
        if isinstance(name, str) and name in names:
            spec[StepFields.INTERNAL_NAME] = names[name]


def new_column_names(params: JsonValue) -> dict[str, str]:
    """Each column a stored step makes, by name, with its internal name."""
    return {
        str(spec[StepFields.NEW_COLUMN]): str(spec[StepFields.INTERNAL_NAME])
        for spec in new_column_specs(params)
        if StepFields.INTERNAL_NAME in spec
    }


def new_column_specs(params: JsonValue) -> list[dict[str, JsonValue]]:
    """Every object in a step's params that names a column the step makes."""
    if isinstance(params, list):
        return [spec for item in params for spec in new_column_specs(item)]
    if not isinstance(params, dict):
        return []
    found = [params] if isinstance(params.get(StepFields.NEW_COLUMN), str) else []
    return found + [spec for value in params.values() for spec in new_column_specs(value)]


def params_patch(ids: dict[str, int], param: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """A patch that has the step do `param` instead.

    The route reads the value as a task only when it names the view: without
    `DATAVIEW_ID` it takes the value as a plain object and changes nothing.
    """
    value = {**param, TaskFields.DATAVIEW_ID: ids["dataview_id"]}
    return {
        StepFields.OP: StepFields.REPLACE,
        StepFields.PATH: StepFields.REPLACE_PARAMS,
        StepFields.VALUE: value,
    }


def command_patch(change: str) -> dict[str, JsonValue]:
    """A patch that suspends or restores the step."""
    return {StepFields.OP: StepFields.COMMAND, StepFields.PATH: change, StepFields.VALUE: None}


async def send_change(
    ids: dict[str, int], step: dict[str, JsonValue], patch: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """Send one change to a step, and wait for the run it starts.

    Returns:
        The run's result, or nothing when no run started (in draft mode). A
        run that fails as a whole reports the failure as its own.

    Raises:
        JobStillRunning: If the run outlasts the tool call.
        ToolError: If Mammoth refused the change.
    """
    step_id = int(str(step[StepFields.ID]))
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        answer = await read_sdk_errors(
            client.pipeline.update_task(
                ids["dataview_id"], step_id, patches=[patch], dataset_id=ids["dataset_id"]
            )
        )
    refuse_a_broken_dependency(answer, step, ids["dataview_id"])
    if answer.get(TaskFields.STATUS) == TaskFields.DONE and answer.get(TaskFields.HAS_ERROR):
        # Made, but later steps now read a column that is not there. Mammoth
        # says so only in draft mode; the steps' own errors name them.
        return {}
    run_id = check_change(answer, NOT_CHANGED).get(TaskFields.RUN_ID)
    if run_id is None:
        return {}
    try:
        return await wait_for_job(ids["workspace_id"], {JobFields.JOB_ID: run_id})
    except JobStillRunning:
        raise
    except ToolError as failed:
        return {
            TaskFields.HAS_ERROR: True,
            StepFields.STEP_ID: step_id,
            StepFields.ERROR: str(failed),
        }


def refuse_a_broken_dependency(
    answer: dict[str, JsonValue], step: dict[str, JsonValue], view_id: int
) -> None:
    """Explain a change Mammoth refused because later steps read what it removes."""
    info = answer.get(TaskFields.ERROR_INFO)
    dependents = info.get(StepFields.DEPENDENTS) if isinstance(info, dict) else None
    if not isinstance(dependents, dict) or not dependents:
        return
    made = new_column_names(step.get(StepFields.PARAMS))
    names = {internal: name for name, internal in made.items()}
    read = "; ".join(
        f"{names.get(column, column)!r} is read by {readers_of(readers, view_id)}"
        for column, readers in dependents.items()
    )
    raise ToolError(
        f"{NOT_CHANGED}: it removes columns that are still read. {read}. Nothing"
        ' changed. To change them together, call manage_draft with "start", change'
        ' or delete the steps that read them, change this one, then "run".'
    )


def readers_of(readers: JsonValue, view_id: int) -> str:
    """What reads a column, as Mammoth lists it: steps by place, anything else by count."""
    if not isinstance(readers, dict):
        return str(readers)
    found: list[str] = []
    for kind, items in readers.items():
        listed = items if isinstance(items, list) else [items]
        if kind == StepFields.TASKS:
            found += [step_at(item, view_id) for item in listed if isinstance(item, dict)]
        else:
            found.append(f"{len(listed)} {kind}")
    return ", ".join(found)


def step_at(reader: dict[str, JsonValue], view_id: int) -> str:
    """A step that reads a column, by its place, and its view when it is another."""
    where = reader.get(StepFields.VIEW_ID)
    place = f"step {reader.get(StepFields.SEQUENCE)}"
    return place if where in (None, view_id) else f"{place} of view {where}"


async def put_back(
    ids: dict[str, int],
    step: dict[str, JsonValue],
    change: str,
    problems: list[dict[str, JsonValue]],
    failing_before: set[int],
) -> dict[str, JsonValue]:
    """Undo a change that made steps fail, and report what failed.

    Args:
        ids: The view's path ids.
        step: The step as it was before the change.
        change: The change to undo.
        problems: The steps in error after the change.
        failing_before: The steps that were in error before it.
    """
    step_id = int(str(step[StepFields.ID]))
    try:
        run = await send_change(ids, step, undo_patch(ids, step, change))
    except JobStillRunning as running:
        return still_running(running, EDIT_RUNS_ON)
    except ToolError as error:
        note = NOT_PUT_BACK_NOTE.format(error=error)
        return await report(ids, step_id, StepFields.NOT_PUT_BACK, note, problems)
    if failing_ids(await read_steps(ids), run) <= failing_before:
        return await report(ids, step_id, StepFields.PUT_BACK, PUT_BACK_NOTE, problems)
    note = NOT_PUT_BACK_NOTE.format(error="the view still fails after the step was put back")
    return await report(ids, step_id, StepFields.NOT_PUT_BACK, note, problems)


def undo_patch(
    ids: dict[str, int], step: dict[str, JsonValue], change: str
) -> dict[str, JsonValue]:
    """The patch that puts a step back as the tasks route listed it."""
    if change != REPLACE:
        return command_patch(UNDO[change])
    params = step.get(StepFields.PARAMS)
    params = params if isinstance(params, dict) else {}
    key = params.get(StepFields.TASK_KEY)
    if not isinstance(key, str) or key not in params:
        raise ToolError("the step's old operation could not be read back")
    # A stored step carries keys of Mammoth's own that the route refuses back.
    kept = {name: params[name] for name in StepFields.KEPT_ON_PUT_BACK if name in params}
    return params_patch(ids, {key: params[key], **kept})


async def report(
    ids: dict[str, int],
    step_id: int,
    outcome: str,
    note: str,
    problems: list[dict[str, JsonValue]] | None = None,
) -> dict[str, JsonValue]:
    """What a change came to: the step now, the steps in error, and what to do."""
    steps = await read_steps(ids)
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        state = await read_sdk_errors(
            client.pipeline.get_pipeline(ids["dataview_id"], dataset_id=ids["dataset_id"])
        )
    now = [step for step in steps if step.get(StepFields.ID) == step_id]
    return {
        StepFields.OUTCOME: outcome,
        StepFields.NEXT_STEP: note,
        StepFields.PROBLEMS: list[JsonValue](problems or []),
        StepFields.STEP: now[0] if now else None,
        PipelineFields.PIPELINE: state,
        ListFields.MAMMOTH_URL: view_url(
            ids["workspace_id"], ids["project_id"], ids["dataview_id"]
        ),
    }
