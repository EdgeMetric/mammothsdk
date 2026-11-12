"""Workflows: work the user describes once and Mammoth then does on its own.

A workflow reads the user's tables, runs its steps and writes a result, which can
be emailed after each run. It starts on demand, on a clock, after another
workflow, or when someone opens its secret link.

There are two ways to make one, and both end in the same build:

- from a template in Mammoth's catalog ("reconcile my bank statement"):
  `find_workflow_template`, then `draft_workflow` with the template's key and the
  tables, then `build_workflow`;
- from the user's own words: `draft_workflow` with a description, then
  `build_workflow` with the spec the draft returns.

Nothing is built until `build_workflow`; a draft only reads.

A workflow is also made, copied and deleted directly (`create_workflow`,
`delete_workflow`), and changed the way a person changes it on its canvas: proposed
changes join its unsaved changes (`propose_workflow_changes`), and `save_workflow`
builds them, undoes the last Save, or cancels a step of a running one.
"""

import asyncio
import re
import typing
from typing import Literal

from mammoth.api.workflows import save_run
from mammoth.client import MammothClient
from mammoth.exceptions import MammothJobTimeoutError
from mcp.server.mcpserver.exceptions import ToolError

from ..deadline import seconds_left
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import CHANGES, DESTRUCTIVE, DESTRUCTIVE_OUTSIDE, READS

# What a draft or a Save keeps back of the call's deadline, to answer in.
ANSWER_SECONDS = 3.0
TEMPLATES_SHOWN = 10
RUNS_SHOWN = 10
RUNNING = "running"
_WORD = re.compile(r"[a-z0-9]+")
# What a template card is searched by.
_CARD_TEXT = ("key", "name", "family", "sentence", "needs", "gives", "output", "words")

ERR_ONE_WAY = (
    "Give either `template_key` with `inputs`, or `description` (or `draft` to read a"
    " draft again), not both and not neither."
)
ERR_BUILD_WAY = "Give either `template_key` with `inputs` and `matches`, or `spec`, not both."
ERR_SCHEDULE_ON_TEMPLATE = (
    "A template build takes no `schedule`: build it, then call set_workflow_trigger."
)
ERR_TRIGGER_FIELDS = "`{kind}` needs `{field}`."
ERR_COPY_NEEDS_TABLES = "A copy needs `dataset_ids`: the workflow's tables to copy."
ERR_TABLES_ONLY_FOR_COPY = "`dataset_ids` is only for a copy: give `copy_of_workflow_id` too."
ERR_NO_CHANGES = "Give at least one change in `changes`."
ERR_SAVE_FIELDS = "`{action}` needs `{field}`."
ERR_NO_SAVE_RUN = "This workflow has no Save run to cancel a step of."
SAVE_ACTIONS = Literal["save", "undo", "cancel_step"]


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _card_words(card: dict[str, JsonValue]) -> set[str]:
    return _words(" ".join(str(card.get(field) or "") for field in _CARD_TEXT))


def _wait_seconds() -> float:
    """How long a wait in this call may last and still leave time to answer."""
    return max(0.0, seconds_left() - ANSWER_SECONDS)


@mcp_server.tool(title="Find workflow template", annotations=READS)
async def find_workflow_template(
    workspace_id: int,
    project_id: int,
    words: str = "",
    dataset_ids: list[int] | None = None,
) -> dict[str, JsonValue]:
    """Find a ready-made workflow in Mammoth's catalog for what the user wants done.

    Use it when the user says "I want to <do something>" with their data
    (reconcile a bank statement, chase late invoices, roll up sales by month).
    Each template says what tables it needs and what it gives. A template the
    project's tables already fit names the table for each input, so
    `draft_workflow` can try it straight away.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project's tables to try.
        words: What the user wants, in their words. Leave it empty to list the
            templates the project's tables fit.
        dataset_ids: The tables to try the templates on; Mammoth picks when
            this is left out.

    Returns:
        `templates`: up to 10 cards, best match first, each with `key`, `name`,
        `sentence`, `needs`, `gives` and `inputs`, and `fits` when the project's
        tables fit it: `tables` (input key to dataset id) and `sure` (false
        when a match is a guess).
    """
    async with build_client(workspace_id, project_id) as client:
        listed, fitted = await asyncio.gather(
            read_sdk_errors(client.workflow_templates.list()),
            read_sdk_errors(client.workflow_templates.fits(dataset_ids)),
        )
    fits = {str(fit["key"]): fit for fit in fitted["fits"]}
    asked = _words(words)
    scored = []
    for order, card in enumerate(listed["templates"]):
        fit = fits.get(str(card.get("key")))
        hits = len(asked & _card_words(card))
        if asked and not hits:
            continue
        if not asked and fit is None:
            continue
        shown = dict(card)
        if fit is not None:
            shown["fits"] = {"tables": fit.get("tables"), "sure": fit.get("sure")}
        scored.append(((-hits, fit is None, order), shown))
    scored.sort(key=lambda pair: pair[0])
    return {"templates": [card for _, card in scored[:TEMPLATES_SHOWN]]}


@mcp_server.tool(
    title="Draft workflow",
    annotations=READS,
    description=(
        "Draft a workflow from a template or from the user's description, and show"
        " what it would give, without building anything.\n\n"
        "From a template: `template_key` and `inputs` (input key to dataset id, as"
        " find_workflow_template's `fits.tables` gives them). Mammoth matches each role"
        " to a column and runs the template on the tables' first rows. Show the user the"
        " `matches` and any `questions`; pass `matches` back to change one.\n\n"
        "From a description: `description` (what the workflow should do) and the"
        " `dataset_ids` it reads. Mammoth reads it back as steps and a spec. When it asks"
        " `asks`, put the user's answers in `answers` and send the same description"
        " again. A draft that is still working returns its `draft` id: call again with"
        " `draft` to read it."
    ),
)
async def draft_workflow(
    workspace_id: int,
    project_id: int,
    template_key: str | None = None,
    inputs: dict[str, int] | None = None,
    matches: dict[str, dict[str, dict[str, JsonValue]]] | None = None,
    settings: dict[str, JsonValue] | None = None,
    description: str | None = None,
    dataset_ids: list[int] | None = None,
    answers: list[dict[str, str]] | None = None,
    draft: str | None = None,
) -> dict[str, JsonValue]:
    """Draft a workflow from a template or a description, and show what it gives.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the tables are in.
        template_key: A template's `key`, from `find_workflow_template`.
        inputs: Template input key to the dataset id that fills it.
        matches: Input key to role to the column(s) playing it, e.g.
            `{"main": {"amount": {"column": "Amount"}}}`. Mammoth proposes them
            when this is left out.
        settings: Template setting key to value; the template's defaults when
            left out.
        description: What the workflow should do, in the user's words (3 to
            2000 characters).
        dataset_ids: The tables a described workflow reads (at most 10).
        answers: Answers to a draft's `asks`, `{"question", "answer"}` each.
        draft: A running draft's id, to read it again.

    Returns:
        From a template: `template_key`, `inputs`, `matches`, `questions` (roles
        Mammoth was not sure of, or could not find) and `preview` (the result on
        the first rows, and the template's checks). From a description: `draft`,
        `state` (running, done or failed), `read_back` (its `spec`, steps and the
        result on the user's rows) and `reason` when it failed.
    """
    by_template = template_key is not None
    by_words = description is not None or draft is not None
    if by_template == by_words or (by_template and not inputs):
        raise ToolError(ERR_ONE_WAY)
    async with build_client(workspace_id, project_id) as client:
        if template_key is not None and inputs is not None:
            return await _draft_from_template(client, template_key, inputs, matches, settings)
        describe = client.workflow_describe
        if draft is None:
            assert description is not None
            started = await read_sdk_errors(
                describe.start(description, dataset_ids=dataset_ids, answers=answers)
            )
            draft = str(started["draft"])
        return await read_sdk_errors(describe.wait(draft, timeout=_wait_seconds()))


async def _draft_from_template(
    client: MammothClient,
    key: str,
    inputs: dict[str, int],
    matches: dict[str, dict[str, dict[str, JsonValue]]] | None,
    settings: dict[str, JsonValue] | None,
) -> dict[str, JsonValue]:
    templates = client.workflow_templates
    questions: list[JsonValue] = []
    if matches is None:
        fitted = await read_sdk_errors(templates.fit(key, inputs))
        matches = {}
        for table in fitted.get("inputs", []):
            roles = matches.setdefault(str(table["key"]), {})
            for role in table.get("roles", []):
                if role.get("mapping"):
                    roles[str(role["role"])] = role["mapping"]
                if role.get("status") != "matched":
                    questions.append(
                        {
                            "input": table["key"],
                            "role": role.get("role"),
                            "status": role.get("status"),
                            "question": role.get("question"),
                            "candidates": role.get("candidates"),
                        }
                    )
    preview = await read_sdk_errors(
        templates.preview(key, inputs, typing.cast(typing.Any, matches), settings)
    )
    return {
        "template_key": key,
        "inputs": typing.cast(JsonValue, inputs),
        "matches": typing.cast(JsonValue, matches),
        "questions": questions,
        "preview": preview,
    }


@mcp_server.tool(
    title="Build workflow",
    annotations=DESTRUCTIVE_OUTSIDE,
    description=(
        "Build a drafted workflow: add its steps to a new workflow, write its result"
        " table, and wait for Mammoth to finish building it. Ask the user first: the"
        " result can be emailed after every run, and a `schedule` sets it to run on"
        " its own.\n\n"
        "From a template: the `template_key`, `inputs` and `matches` draft_workflow"
        " showed. From a description: the draft's `read_back.spec`, and optionally a"
        " `schedule`. Name the result table in `destination_name`."
    ),
)
async def build_workflow(
    workspace_id: int,
    project_id: int,
    destination_name: str,
    template_key: str | None = None,
    inputs: dict[str, int] | None = None,
    matches: dict[str, dict[str, dict[str, JsonValue]]] | None = None,
    settings: dict[str, JsonValue] | None = None,
    spec: dict[str, JsonValue] | None = None,
    destination_emails: list[str] | None = None,
    schedule: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Build a drafted workflow and wait for its Save.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project to build it in.
        destination_name: What to call the result table (1 to 120 characters).
        template_key: The template's `key`.
        inputs: Template input key to dataset id.
        matches: Input key to role to column(s), as `draft_workflow` returned.
        settings: Template setting key to value.
        spec: A described draft's `read_back.spec`.
        destination_emails: People to email the result to after each run.
        schedule: A clock to start with a described workflow, e.g.
            `{"frequency": "weekly", "by_week_day": ["mo"]}`.

    Returns:
        `workflow`: the workflow, with `id`. `saved`: `done` when every step was
        built, `running` when the build outlasted this call (read it with
        `get_workflow`), or how it failed.
    """
    by_template = template_key is not None
    if by_template == (spec is not None) or (by_template and not (inputs and matches)):
        raise ToolError(ERR_BUILD_WAY)
    if by_template and schedule is not None:
        raise ToolError(ERR_SCHEDULE_ON_TEMPLATE)
    async with build_client(workspace_id, project_id) as client:
        if template_key is not None and inputs is not None and matches is not None:
            built = await read_sdk_errors(
                client.workflow_templates.build(
                    template_key,
                    inputs,
                    typing.cast(typing.Any, matches),
                    destination_name,
                    settings=settings,
                    destination_emails=destination_emails,
                )
            )
        else:
            assert spec is not None
            built = await read_sdk_errors(
                client.workflow_describe.build(
                    spec,
                    destination_name,
                    destination_emails=destination_emails,
                    schedule=schedule,
                )
            )
        workflow = await _await_save(client, built["workflow"])
    return {"workflow": workflow, "saved": _save_status(workflow)}


def _save_status(workflow: dict[str, JsonValue]) -> JsonValue:
    run = save_run(workflow)
    return (run.get("status") if run else None) or "done"


async def _await_save(
    client: MammothClient, workflow: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """Read the workflow until its Save ends or the call's time runs out."""
    workflow_id = typing.cast(int, workflow["id"])
    return await read_sdk_errors(
        client.workflows.wait_for_save(
            workflow_id,
            workflow=typing.cast(dict[str, typing.Any], workflow),
            timeout=_wait_seconds(),
        )
    )


@mcp_server.tool(
    title="Run workflow",
    annotations=DESTRUCTIVE_OUTSIDE,
    description=(
        "Run a workflow now, on Mammoth's servers, and wait briefly for it to end. Ask"
        " the user first: a run rewrites the result table and sends its emails and"
        " exports. A workflow already running is not started twice. `result` is"
        " `running` when the run outlasts this call: read it later with get_workflow."
    ),
)
async def run_workflow(
    workspace_id: int, project_id: int, workflow_id: int
) -> dict[str, JsonValue]:
    """Run a workflow now and wait briefly for it to end.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the workflow is in.
        workflow_id: Which workflow to run.

    Returns:
        `run_id`, `already_running`, `run` (its Recent runs row, once it shows)
        and `result`: running, success or failure.
    """
    async with build_client(workspace_id, project_id) as client:
        triggers = client.workflow_triggers
        started = await read_sdk_errors(triggers.run(workflow_id))
        row = await read_sdk_errors(
            triggers.wait_for_run(workflow_id, str(started["run_id"]), timeout=_wait_seconds())
        )
    return {**started, "run": row, "result": row["result"] if row else RUNNING}


@mcp_server.tool(
    title="Set workflow trigger",
    annotations=DESTRUCTIVE_OUTSIDE,
    description=(
        "Set what starts a workflow on its own: a clock (`schedule`), the end of"
        " another workflow (`after`), or a secret link anyone can open (`link`;"
        " `unlink` turns it off). Ask the user first: every run sends the workflow's"
        " emails and exports. For a workflow, use this rather than create_automation."
        " A clock or an `after` is stored as an automation: pause or remove it with"
        " update_automation or delete_automation by the `automation_id` returned."
    ),
)
async def set_workflow_trigger(
    workspace_id: int,
    project_id: int,
    workflow_id: int,
    kind: Literal["schedule", "after", "link", "unlink"],
    frequency: Literal["hourly", "daily", "weekly", "monthly"] | None = None,
    interval: int = 1,
    by_week_day: list[Literal["mo", "tu", "we", "th", "fr", "sa", "su"]] | None = None,
    by_month_day: list[int] | None = None,
    start_at: str | None = None,
    start_now: bool = False,
    until: str | None = None,
    source_workflow_id: int | None = None,
    only_when_ok: bool = True,
) -> dict[str, JsonValue]:
    """Set what starts a workflow: a clock, another workflow, or a link.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the workflow is in.
        workflow_id: Which workflow.
        kind: `schedule`, `after`, `link` (make or replace the secret link) or
            `unlink`.
        frequency: For `schedule`: hourly, daily, weekly or monthly.
        interval: For `schedule`: every how many of `frequency` (1 to 366).
        by_week_day: For a weekly `schedule`: the days it runs.
        by_month_day: For a monthly `schedule`: the days of the month (1 to 31).
        start_at: For `schedule`: the first run, ISO 8601 in UTC.
        start_now: For `schedule`: run once now as well.
        until: For `schedule`: the last day it runs, ISO 8601.
        source_workflow_id: For `after`: the workflow whose end starts this one.
        only_when_ok: For `after`: start only when that run succeeded.

    Returns:
        `automation_id` for `schedule` and `after`. For `link`: `path` (the link
        under Mammoth's API) and `secret`, shown only this once.
    """
    if kind == "schedule" and frequency is None:
        raise ToolError(ERR_TRIGGER_FIELDS.format(kind=kind, field="frequency"))
    if kind == "after" and source_workflow_id is None:
        raise ToolError(ERR_TRIGGER_FIELDS.format(kind=kind, field="source_workflow_id"))
    async with build_client(workspace_id, project_id) as client:
        triggers = client.workflow_triggers
        if kind == "schedule":
            assert frequency is not None
            return await read_sdk_errors(
                triggers.schedule_set(
                    workflow_id,
                    frequency,
                    interval=interval,
                    by_week_day=typing.cast(list[str] | None, by_week_day),
                    by_month_day=by_month_day,
                    start_at=start_at,
                    start_now=start_now,
                    until=until,
                )
            )
        if kind == "after":
            assert source_workflow_id is not None
            return await read_sdk_errors(
                triggers.after_set(workflow_id, source_workflow_id, only_when_ok=only_when_ok)
            )
        if kind == "link":
            return await read_sdk_errors(triggers.link_create(workflow_id))
        await read_sdk_errors(triggers.link_remove(workflow_id))
        return {"unlinked": True}


@mcp_server.tool(title="List workflows", annotations=READS)
async def list_workflows(workspace_id: int, project_id: int) -> dict[str, JsonValue]:
    """List a project's workflows.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.

    Returns:
        `workflows`: each with `id`, `name` and what it is for.
    """
    async with build_client(workspace_id, project_id) as client:
        workflows = await read_sdk_errors(client.workflows.list())
    return {"workflows": typing.cast(JsonValue, workflows)}


@mcp_server.tool(title="Get workflow", annotations=READS)
async def get_workflow(
    workspace_id: int, project_id: int, workflow_id: int
) -> dict[str, JsonValue]:
    """Get a workflow, whether its build finished, and its recent runs.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the workflow is in.
        workflow_id: Which workflow.

    Returns:
        `workflow`, `saved` (done, running, or how the build failed) and `runs`:
        the latest 10, newest first, each with `trigger` (manual, schedule,
        file, after, called), `result` (running, success, failure), times,
        `rows_out` and `reason`.
    """
    async with build_client(workspace_id, project_id) as client:
        workflow, runs = await asyncio.gather(
            read_sdk_errors(client.workflows.get(workflow_id)),
            read_sdk_errors(client.workflow_triggers.runs(workflow_id)),
        )
    return {
        "workflow": workflow,
        "saved": _save_status(workflow),
        "runs": runs["runs"][:RUNS_SHOWN],
    }


@mcp_server.tool(
    title="Create workflow",
    annotations=CHANGES,
    description=(
        "Create an empty workflow, or copy one. A new workflow may start from a table"
        " (`seed_dataset_id`). A copy (`copy_of_workflow_id` with `dataset_ids`, the"
        " workflow's tables) copies those tables with their rows, views and steps in one"
        " job; tables it only joins are shared, and automations and exports are not"
        " copied. A copy that outlasts this call returns its `job_id`: read it with"
        " get_job. To build a workflow from a template or a description, use"
        " draft_workflow and build_workflow instead."
    ),
)
async def create_workflow(
    workspace_id: int,
    project_id: int,
    name: str,
    purpose: str | None = None,
    seed_dataset_id: int | None = None,
    copy_of_workflow_id: int | None = None,
    dataset_ids: list[int] | None = None,
) -> dict[str, JsonValue]:
    """Create an empty workflow, or copy one with its tables.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project to create it in.
        name: The new workflow's name.
        purpose: What the workflow is for, in the user's words.
        seed_dataset_id: A table the new workflow starts from.
        copy_of_workflow_id: The workflow to copy.
        dataset_ids: For a copy: the workflow's tables to copy.

    Returns:
        `workflow` for a new one. For a copy: `workflow_id` once the copy is done,
        or `job_id` and `status` `running` while it is still copying, or `copy` (the
        server's answer as is) when the server gives no job to follow.
    """
    if copy_of_workflow_id is None:
        if dataset_ids:
            raise ToolError(ERR_TABLES_ONLY_FOR_COPY)
        async with build_client(workspace_id, project_id) as client:
            made = await read_sdk_errors(
                client.workflows.create(name, purpose=purpose, seed_datasource_id=seed_dataset_id)
            )
        return {"workflow": made}
    if not dataset_ids:
        raise ToolError(ERR_COPY_NEEDS_TABLES)
    async with build_client(workspace_id, project_id) as client:
        queued = await read_sdk_errors(
            client.workflows.duplicate(
                name, dataset_ids, source_workflow_id=copy_of_workflow_id, wait=False
            )
        )
        job_id = queued.get("job_id")
        if job_id is None:
            return {"copy": queued}
        try:
            job = await read_sdk_errors(
                client.jobs.wait_for_job(int(job_id), timeout=_wait_seconds())
            )
        except ToolError as error:
            if isinstance(error.__cause__, MammothJobTimeoutError):
                return {"job_id": job_id, "status": RUNNING}
            raise
    response = job.get("response")
    copied = response.get("workflow_id") if isinstance(response, dict) else None
    return {"job_id": job_id, "status": "done", "workflow_id": copied}


@mcp_server.tool(
    title="Delete workflow",
    annotations=DESTRUCTIVE,
    description=(
        "Delete a workflow. Ask the user first. Its tables and views stay in the"
        " project; its runs, triggers and unsaved changes go with it."
    ),
)
async def delete_workflow(
    workspace_id: int, project_id: int, workflow_id: int
) -> dict[str, JsonValue]:
    """Delete a workflow.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the workflow is in.
        workflow_id: Which workflow to delete.

    Returns:
        `deleted`: the workflow id.
    """
    async with build_client(workspace_id, project_id) as client:
        await read_sdk_errors(client.workflows.delete(workflow_id))
    return {"deleted": workflow_id}


@mcp_server.tool(
    title="Propose workflow changes",
    annotations=CHANGES,
    description=(
        "Propose changes on a workflow's canvas. They join its unsaved changes, where"
        " people see them labelled as yours, and nothing is built until save_workflow."
        " Each change is an object with `op`: add_view, rename_view, trash_view,"
        " rename_dataset, trash_dataset, send_to_new_dataset, send_to_dataset, join,"
        " lookup, export, add_source, add_step, update_step or remove_step. add_step is"
        " {op, view_id, transform, params, label} where transform is a transformation"
        " kind and params its input; update_step is {op, view_id, task_id, params:"
        " {task_spec} or {patches}}; remove_step is {op, view_id, task_id}. An op that"
        " adds a view, table or step may name it with `ref`, and a later change in the"
        " same call uses `view_ref` or `dataset_ref` in place of the id. A change the"
        " server cannot use is refused with what it expects. `added` lists the keys of"
        " the changes this call made: pass them to save_workflow. `unsaved` holds"
        " everyone's unsaved changes, other people's proposals included."
    ),
)
async def propose_workflow_changes(
    workspace_id: int,
    project_id: int,
    workflow_id: int,
    changes: list[dict[str, JsonValue]],
) -> dict[str, JsonValue]:
    """Add changes to a workflow's unsaved changes, for save_workflow to build.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the workflow is in.
        workflow_id: Which workflow.
        changes: The changes, each an object with `op`.

    Returns:
        `added`: the keys of the unsaved changes this call added or changed, for
        save_workflow's `keys`; `unsaved`: every unsaved change the workflow now
        holds, anyone's, each with its `key`; and `version`.
    """
    if not changes:
        raise ToolError(ERR_NO_CHANGES)
    async with build_client(workspace_id, project_id) as client:
        before = _pending_by_key(await read_sdk_errors(client.workflows.get(workflow_id)))
        workflow = await read_sdk_errors(
            client.workflows.canvas(
                workflow_id, {"proposed_changes": typing.cast(typing.Any, changes)}
            )
        )
    after = _pending_by_key(workflow)
    state = workflow.get("canvas_state")
    state = state if isinstance(state, dict) else {}
    return {
        "added": typing.cast(JsonValue, _added_by_this_call(before, after)),
        "unsaved": typing.cast(JsonValue, state.get("pending_changes") or []),
        "version": state.get("version"),
    }


def _added_by_this_call(before: dict[str, JsonValue], after: dict[str, JsonValue]) -> list[str]:
    """The keys this call's PATCH added or changed.

    A change that differs from the read before the PATCH may also be someone else's,
    made between the two requests. The server stamps every change of one PATCH with
    the same `at`, under a row lock, so this call's changes are the ones stamped with
    the newest `at`; an earlier stamp is another proposal's.

    Args:
        before: The unsaved changes by key, read before the PATCH.
        after: The unsaved changes by key, as the PATCH returned them.

    Returns:
        The keys of the changes this call made, in the server's order.
    """
    changed = {key: change for key, change in after.items() if before.get(key) != change}
    stamps = {
        key: str(change.get("at") or "")
        for key, change in changed.items()
        if isinstance(change, dict)
    }
    newest = max(stamps.values(), default="")
    return [key for key in changed if stamps.get(key, "") == newest]


def _pending_by_key(workflow: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The workflow's unsaved changes by their key."""
    state = workflow.get("canvas_state")
    pending = state.get("pending_changes") if isinstance(state, dict) else None
    return {
        str(change["key"]): change
        for change in (pending if isinstance(pending, list) else [])
        if isinstance(change, dict) and change.get("key")
    }


@mcp_server.tool(
    title="Save workflow",
    annotations=DESTRUCTIVE_OUTSIDE,
    description=(
        "Build unsaved changes (`save` with `keys`: the `added` keys"
        " propose_workflow_changes returned; other people's proposals are built only when"
        " the user names them), undo a Save this conversation made (`undo` with the"
        " `run_id` its save returned), or cancel one step of the Save that is running"
        " (`cancel_step` with `step`, the step's index). Ask the user first: a Save"
        " changes the tables' views and runs them, and a view's exports run with it."
        " It waits for the Save to end; `saved` is `running` when it outlasts this"
        " call: read it later with get_workflow."
    ),
)
async def save_workflow(
    workspace_id: int,
    project_id: int,
    workflow_id: int,
    action: SAVE_ACTIONS = "save",
    keys: list[str] | None = None,
    run_id: str | None = None,
    step: int | None = None,
) -> dict[str, JsonValue]:
    """Save, undo the latest Save, or cancel a step of the running Save.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the workflow is in.
        workflow_id: Which workflow.
        action: `save`, `undo` or `cancel_step`.
        keys: For `save` (required): the unsaved changes to build (and what they need).
        run_id: For `undo` (required): the Save run to undo, as `save` returned it.
            For `cancel_step`: the running Save; the workflow's latest when left out.
        step: For `cancel_step`: the index of the step to cancel.

    Returns:
        `workflow`, `run_id` (the Save run, for a later `undo`), `saved` (done,
        running, or how it failed) and `steps`: each step of the Save run with its
        status.
    """
    needs = {"save": ("keys", keys), "undo": ("run_id", run_id), "cancel_step": ("step", step)}
    field, given = needs[action]
    if given is None or given == []:
        raise ToolError(ERR_SAVE_FIELDS.format(action=action, field=field))
    async with build_client(workspace_id, project_id) as client:
        workflows_api = client.workflows
        if action == "save":
            started = await read_sdk_errors(workflows_api.save(workflow_id, keys=keys))
        elif action == "undo":
            assert run_id is not None
            started = await read_sdk_errors(workflows_api.undo_save(workflow_id, run_id))
        else:
            assert step is not None
            run = run_id or await _latest_run_id(client, workflow_id)
            started = await read_sdk_errors(workflows_api.cancel_save_step(workflow_id, run, step))
        record = started if isinstance(started.get("canvas_state"), dict) else None
        workflow = await read_sdk_errors(
            workflows_api.wait_for_save(workflow_id, workflow=record, timeout=_wait_seconds())
        )
    run_now = save_run(workflow) or {}
    return {
        "workflow": workflow,
        "run_id": run_now.get("id"),
        "saved": _save_status(workflow),
        "steps": typing.cast(JsonValue, run_now.get("steps") or []),
    }


async def _latest_run_id(client: MammothClient, workflow_id: int) -> str:
    """The id of the workflow's latest Save run, for cancelling one of its steps."""
    workflow = await read_sdk_errors(client.workflows.get(workflow_id))
    run = save_run(workflow)
    if not run or not run.get("id"):
        raise ToolError(ERR_NO_SAVE_RUN)
    return str(run["id"])
