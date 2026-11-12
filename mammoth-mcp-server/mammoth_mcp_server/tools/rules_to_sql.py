"""Replace several consecutive rules of a view with one SQL rule, in one save.

Three tools, in the order a model uses them:

1. `plan_convert_to_sql` asks Mammoth where the rules can be merged. Code on
   the server decides the cuts; the model never picks groups itself.
2. `generate_convert_sql` writes the SQL of each group from a text the model
   wrote, and previews its result. It changes nothing.
3. `convert_to_sql` saves every group at once: one pipeline version, one run.

Rules are numbered as the user sees them: rule 3 is the step whose `sequence`
is 3. Deleting the rules one by one and adding a SQL rule would make one
version per change and lose the text, so it is never the way.
"""

from mammoth.exceptions import MammothJobTimeoutError
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, ConfigDict

from ..consts import (
    PREVIEW_ROWS_DEFAULT,
    PREVIEW_ROWS_MAX,
    ConvertFields,
    ListFields,
    PipelineFields,
    SqlGenerationFields,
    StepFields,
)
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..shape import view_url
from ..tool_kinds import DESTRUCTIVE_OUTSIDE, READS
from .pipeline import read_pipeline, read_steps, view_ids

NOT_SUPPORTED = (
    "this server does not support convert-to-sql yet, or one of the rules is not in this"
    " view. Nothing was changed. Do not delete the rules one by one and add a SQL rule"
    " instead: tell the user the server cannot do it yet."
)
CONVERT_RUNS_ON = (
    "The rules were converted and the view's run is still going. Do not convert again."
    " Call get_pipeline later to see the run end."
)
PLAN_NEXT = (
    "Show the user this plan in rule numbers. If it has no groups, say why (see"
    " `kept_as_is` and `boundaries`) and stop. Otherwise write a text for each group"
    " that says what its rules do, call generate_convert_sql with each group's"
    " `task_ids` and text, and show the user the SQL and the preview. Convert only"
    " after the user approves. If the user asked for one rule and the plan has cuts, say why."
)
GENERATE_NEXT = (
    "Show the user each group's text, SQL and preview. If the user approves, call"
    " convert_to_sql with each group's `task_ids`, `text` and `query`. If a preview"
    " looks wrong, change the text and call generate_convert_sql again. Nothing was saved."
)
CONVERTED_NOTE = (
    "The rules were replaced by SQL rules in one change and the view ran again. Tell"
    " the user which rules were replaced."
)
STAGED_NOTE = (
    "The view is in draft mode, so the change joined the draft and nothing ran. Tell the"
    ' user. Call manage_draft with "run" to run it, or "drop" to throw it away.'
)


class RuleGroup(BaseModel):
    """One group to turn into SQL: the rules, and the text that says what they do."""

    model_config = ConfigDict(extra="forbid")

    task_ids: list[int]
    text: str


class ConvertGroup(RuleGroup):
    """One group to save: the rules, their text and the SQL that replaces them."""

    query: str


@mcp_server.tool(title="Plan rules to SQL conversion", annotations=READS)
async def plan_convert_to_sql(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    rules: list[int] | None = None,
) -> dict[str, JsonValue]:
    """Plan how to replace a view's rules with fewer SQL rules. Changes nothing.

    Use it when the user says "clean up my rules", "replace rules 1 to 8 with
    one rule" or "put these into fewer rules". The flow: call this tool, show
    the plan, write a text for each group that says what its rules do, call
    `generate_convert_sql`, show the SQL and the preview, get the user's
    approval, then call `convert_to_sql`. Never delete rules one by one to
    replace them: that makes many versions and loses the text. Never choose
    the groups yourself: Mammoth decides where to cut.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        rules: The rule numbers to consider, as the user sees them (rule 1 is
            the first). Leave it out for the whole pipeline.

    Returns:
        `groups`: each run of rules that can become one SQL rule, with
        `rules` in words ("1 to 3"), `first_rule`, `last_rule` and `task_ids`.
        `kept_as_is`: each rule left alone, with `rule` and `why`.
        `boundaries`: each place no rule can cross, with `after_rule` and
        `why`. `summary` and `next_step`: what to tell the user and do.
    """
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    steps = await read_steps(ids)
    task_ids = task_ids_of(steps, rules) if rules is not None else None
    async with build_client(workspace_id, project_id) as client:
        plan = await read_sdk_errors(
            client.pipeline.plan_sql_conversion(view_id, task_ids=task_ids, dataset_id=dataset_id),
            not_found=NOT_SUPPORTED,
        )
    return {
        **describe_plan(plan),
        ListFields.MAMMOTH_URL: view_url(workspace_id, project_id, view_id),
    }


@mcp_server.tool(title="Generate SQL for rules", annotations=READS)
async def generate_convert_sql(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    groups: list[RuleGroup],
    rows: int = PREVIEW_ROWS_DEFAULT,
) -> dict[str, JsonValue]:
    """Write the SQL that would replace each group of rules, and preview its result.

    Changes nothing: it saves no rule. Call it after `plan_convert_to_sql`,
    with a text for each group that says what its rules do, in your own words
    from the rules you read with `get_pipeline`. Mammoth reads the rules'
    exact settings and result columns, so the SQL reproduces them. Show the
    user each text, SQL and preview, and ask for approval before
    `convert_to_sql`.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        groups: Each group is `task_ids` (one group of `plan_convert_to_sql`,
            as it gave them) and `text` (what the rules do, not blank).
        rows: How many rows the preview runs on (at most 100).

    Returns:
        `groups`: for each group `task_ids`, `text`, `query` (the SQL) and
        `preview` (`data` and `metadata`, the result's rows and columns).
        `next_step`: what to tell the user and do.
    """
    check_groups([group.task_ids for group in groups], [group.text for group in groups])
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    steps = await read_steps(ids)
    made: list[JsonValue] = []
    async with build_client(workspace_id, project_id) as client:
        for group in groups:
            first = first_sequence(steps, group.task_ids)
            answer = await read_sdk_errors(
                client.ai.generate_sql(
                    group.text,
                    first,
                    dataset_id=dataset_id,
                    dataview_id=view_id,
                    task_ids=group.task_ids,
                )
            )
            query = read_query(answer)
            preview = await read_sdk_errors(
                client.pipeline.preview_task(
                    view_id,
                    {
                        ConvertFields.SQL: {
                            ConvertFields.USER_QUERY: query,
                            ConvertFields.INTENT: group.text,
                        },
                        ConvertFields.SEQUENCE_NUMBER: first,
                    },
                    dataset_id=dataset_id,
                    sample_size=min(rows, PREVIEW_ROWS_MAX),
                )
            )
            made.append(
                {
                    ConvertFields.TASK_IDS: list[JsonValue](group.task_ids),
                    "text": group.text,
                    "query": query,
                    "preview": preview,
                }
            )
    return {ConvertFields.GROUPS: made, StepFields.NEXT_STEP: GENERATE_NEXT}


@mcp_server.tool(title="Convert rules to SQL", annotations=DESTRUCTIVE_OUTSIDE)
async def convert_to_sql(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    groups: list[ConvertGroup],
) -> dict[str, JsonValue]:
    """Replace each group of rules by one SQL rule, in one save, and wait for the run.

    Save only what the user approved after `plan_convert_to_sql` and
    `generate_convert_sql`. All groups change together: one pipeline version
    and one run, so the user can go back with `undo`. The text of each group is
    kept in the SQL rule. This replaces the rules: never delete rules one by one
    to do it. A server that cannot convert answers that it cannot: then tell the
    user, and do not fall back to deleting rules.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view.
        groups: Each group is `task_ids`, `text` (what the rules do, not
            blank) and `query` (the SQL `generate_convert_sql` wrote).

    Returns:
        `outcome`: "converted" or "staged" (the view is in draft mode, so
        nothing ran). `next_step`: what to tell the user. `pipeline` and
        `mammoth_url`.
    """
    check_groups([group.task_ids for group in groups], [group.text for group in groups])
    if any(not group.query.strip() for group in groups):
        raise ToolError("Each group needs `query`: the SQL from generate_convert_sql.")
    ids = view_ids(workspace_id, project_id, dataset_id, view_id)
    body: list[dict[str, JsonValue]] = [
        {
            ConvertFields.TASK_IDS: list[JsonValue](group.task_ids),
            ConvertFields.SQL: {
                ConvertFields.USER_QUERY: group.query,
                ConvertFields.INTENT: group.text,
            },
        }
        for group in groups
    ]
    async with build_client(workspace_id, project_id) as client:
        try:
            await read_sdk_errors(
                client.pipeline.convert_to_sql(view_id, body, dataset_id=dataset_id),
                not_found=NOT_SUPPORTED,
            )
        except MammothJobTimeoutError:
            return {StepFields.OUTCOME: "running", StepFields.NEXT_STEP: CONVERT_RUNS_ON}
    state = await read_pipeline(ids)
    staged = state[PipelineFields.DRAFT_MODE] != PipelineFields.NOT_DRAFTING
    url = state.pop(ListFields.MAMMOTH_URL)
    return {
        StepFields.OUTCOME: "staged" if staged else "converted",
        StepFields.NEXT_STEP: STAGED_NOTE if staged else CONVERTED_NOTE,
        PipelineFields.PIPELINE: state,
        ListFields.MAMMOTH_URL: url,
    }


def check_groups(task_ids: list[list[int]], texts: list[str]) -> None:
    """Refuse, before any request, no group, a group with no rules, or a blank text."""
    if not task_ids:
        raise ToolError("Pass at least one group. Call plan_convert_to_sql to get them.")
    if any(not ids for ids in task_ids):
        raise ToolError("Each group needs `task_ids`, as plan_convert_to_sql gave them.")
    if any(not text.strip() for text in texts):
        raise ToolError(
            "Each group needs a `text` that says what its rules do. Write it from the"
            " rules you read with get_pipeline. Nothing was sent."
        )


def task_ids_of(steps: list[dict[str, JsonValue]], rules: list[int]) -> list[int]:
    """The step ids of these rule numbers, or why a number names no rule."""
    by_number = {step.get(StepFields.SEQUENCE): step.get(StepFields.ID) for step in steps}
    missing = [rule for rule in rules if rule not in by_number]
    if missing:
        numbers = sorted(number for number in by_number if isinstance(number, int))
        raise ToolError(f"This view has no rule {missing}. Its rules are numbered {numbers}.")
    return [int(str(by_number[rule])) for rule in rules]


def first_sequence(steps: list[dict[str, JsonValue]], task_ids: list[int]) -> int:
    """The rule number of the first of these steps, or why a step is not in the view."""
    found = [
        int(str(step.get(StepFields.SEQUENCE)))
        for step in steps
        if step.get(StepFields.ID) in task_ids
    ]
    if len(found) != len(set(task_ids)):
        raise ToolError(
            f"A step in {task_ids} is not in this view. Use the `task_ids` of"
            " plan_convert_to_sql for this view."
        )
    return min(found)


def read_query(answer: dict[str, JsonValue]) -> str:
    """The SQL the AI wrote, or the AI's own reason it wrote none."""
    response = answer.get(SqlGenerationFields.RESPONSE)
    done = isinstance(response, dict) and response.get(SqlGenerationFields.STATUS_CODE) == (
        SqlGenerationFields.SUCCESS
    )
    if not isinstance(response, dict) or not done:
        reason = response.get(SqlGenerationFields.DETAIL) if isinstance(response, dict) else None
        raise ToolError(
            f"Mammoth could not write the SQL: {reason or 'no reason given'}."
            " Change the text, say more about what the rules do, and try again."
        )
    return str(response[SqlGenerationFields.RESULT])


def describe_plan(plan: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The plan route's answer, in rule numbers and words."""
    raw_groups = plan.get(ConvertFields.GROUPS)
    raw_cuts = plan.get(ConvertFields.CUTS)
    groups = (
        [one for one in raw_groups if isinstance(one, dict)] if isinstance(raw_groups, list) else []
    )
    cuts = [one for one in raw_cuts if isinstance(one, dict)] if isinstance(raw_cuts, list) else []
    described: list[JsonValue] = []
    for group in groups:
        first, last = group[ConvertFields.FIRST_SEQUENCE], group[ConvertFields.LAST_SEQUENCE]
        described.append(
            {
                "rules": f"{first} to {last}" if first != last else str(first),
                "first_rule": first,
                "last_rule": last,
                ConvertFields.TASK_IDS: group[ConvertFields.TASK_IDS],
            }
        )
    kept: list[JsonValue] = []
    boundaries: list[JsonValue] = []
    for cut in cuts:
        reason = str(cut.get(ConvertFields.REASON))
        why = ConvertFields.REASON_WORDS.get(reason, reason)
        if reason == ConvertFields.GATE:
            boundaries.append({"after_rule": cut[ConvertFields.SEQUENCE], "why": why})
        else:
            kept.append({"rule": cut[ConvertFields.SEQUENCE], "why": why})
    return {
        ConvertFields.GROUPS: described,
        "kept_as_is": kept,
        "boundaries": boundaries,
        "summary": summary_of(described),
        StepFields.NEXT_STEP: PLAN_NEXT,
    }


def summary_of(groups: list[JsonValue]) -> str:
    """One line: which rules can become one rule each, or that none can."""
    if not groups:
        return "No rules can be merged into a SQL rule."
    parts = [f"rules {one['rules']}" for one in groups if isinstance(one, dict)]
    return f"These can each become one SQL rule: {'; '.join(parts)}."
