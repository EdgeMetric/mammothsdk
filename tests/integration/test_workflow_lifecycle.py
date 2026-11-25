"""A workflow's whole life against a live Mammoth: CRUD, triggers, templates and runs.

Uses the ``MM_REL_*`` credentials and project (see ``conftest.py``) and skips without them.
The module leaves the project as it found it: every workflow and table it made is deleted at
the end, even when an assertion fails. The run tests need a server with
``POST .../workflows/{id}/run``.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio

from mammoth import MammothClient
from mammoth.api.workflows import save_run
from mammoth.exceptions import MammothAPIError

pytestmark = pytest.mark.asyncio(loop_scope="session")

TEMPLATE = "bank-reconciliation"
RUN_SECONDS = 300.0
SAVE_SECONDS = 300.0


async def _made(client: MammothClient, project: int) -> tuple[set[int], set[int]]:
    """The ids of the project's workflows and of its newest tables.

    Args:
        client: The live client.
        project: The project to read.

    Returns:
        The workflow ids and the dataset ids.
    """
    workflows = {int(w["id"]) for w in await client.workflows.list(project_id=project)}
    listed = await client.datasets.list(project_id=project)
    return workflows, {int(d["id"]) for d in listed["datasets"]}


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def project(client: MammothClient) -> AsyncIterator[int]:
    """The configured project; what the module made in it is deleted at the end."""
    project_id = int(client.project_id)
    workflows_before, datasets_before = await _made(client, project_id)
    try:
        yield project_id
    finally:
        workflows_after, datasets_after = await _made(client, project_id)
        for workflow_id in workflows_after - workflows_before:
            with contextlib.suppress(MammothAPIError):
                await client.workflows.delete(workflow_id, project_id=project_id)
        for dataset_id in datasets_after - datasets_before:
            with contextlib.suppress(MammothAPIError):
                await client.datasets.delete(dataset_id, project_id=project_id)


async def _matches(client: MammothClient, inputs: dict[str, int], project: int) -> dict[str, Any]:
    """Every role the template fitted to a column, as ``preview`` and ``build`` take them.

    Args:
        client: The live client.
        inputs: Input key -> dataset id.
        project: The project the tables are in.

    Returns:
        Input key -> role -> the column(s) playing it.
    """
    fitted = await client.workflow_templates.fit(TEMPLATE, inputs, project_id=project)
    matches: dict[str, Any] = {}
    for table in fitted["inputs"]:
        roles = matches.setdefault(table["key"], {})
        for role in table["roles"]:
            assert role["status"] in ("matched", "check") and role["mapping"], role
            roles[role["role"]] = role["mapping"]
    return matches


async def test_crud(client: MammothClient, project: int) -> None:
    """Create, read, list, rename and delete a workflow."""
    workflows = client.workflows
    made = await workflows.create("SDK live A", project_id=project)
    workflow_id = int(made["id"])
    assert made["name"] == "SDK live A"

    got = await workflows.get(workflow_id, project_id=project)
    assert got["id"] == workflow_id
    listed = await workflows.list(project_id=project)
    assert workflow_id in [w["id"] for w in listed]

    await workflows.update(workflow_id, name="SDK live A renamed", notes="live", project_id=project)
    got = await workflows.get(workflow_id, project_id=project)
    assert (got["name"], got.get("notes")) == ("SDK live A renamed", "live")

    await workflows.delete(workflow_id, project_id=project)
    with pytest.raises(MammothAPIError):
        await workflows.get(workflow_id, project_id=project)
    assert workflow_id not in [w["id"] for w in await workflows.list(project_id=project)]


async def test_triggers(client: MammothClient, project: int) -> None:
    """A clock (set, then replaced), an "after" with its loop guard, and the secret link."""
    workflows, triggers = client.workflows, client.workflow_triggers
    first = int((await workflows.create("SDK live first", project_id=project))["id"])
    second = int((await workflows.create("SDK live second", project_id=project))["id"])
    try:
        clock = await triggers.schedule_set(
            first, "weekly", by_week_day=["mo"], start_now=False, project_id=project
        )
        assert clock["automation_id"]
        again = await triggers.schedule_set(
            first, "daily", interval=2, start_now=False, project_id=project
        )
        assert again["automation_id"]

        after = await triggers.after_set(second, first, project_id=project)
        assert after["automation_id"]
        loops = await triggers.after_loops(first, project_id=project)
        assert second in loops["would_loop"]
        with pytest.raises(MammothAPIError):
            await triggers.after_set(first, second, project_id=project)

        link = await triggers.link_create(first, project_id=project)
        assert link["secret"] and str(first) in link["path"]
        assert await triggers.link_remove(first, project_id=project) == {}
    finally:
        for workflow_id in (second, first):
            with contextlib.suppress(MammothAPIError):
                await workflows.delete(workflow_id, project_id=project)


async def test_template_build_and_run(client: MammothClient, project: int) -> None:
    """Find, fit, preview and build a template, then run it once and once more while running."""
    templates, triggers = client.workflow_templates, client.workflow_triggers
    cards = (await templates.list(project_id=project))["templates"]
    assert TEMPLATE in [card["key"] for card in cards]
    template = await templates.get(TEMPLATE, project_id=project)
    assert {i["key"] for i in template["inputs"]} == {"a", "b"}

    inputs = {
        key: int(dataset_id)
        for key, dataset_id in (await templates.import_samples(TEMPLATE, project_id=project))[
            "inputs"
        ].items()
    }
    matches = await _matches(client, inputs, project)
    preview = await templates.preview(TEMPLATE, inputs, matches, project_id=project)
    assert preview

    built = await templates.build(TEMPLATE, inputs, matches, "SDK live rec", project_id=project)
    workflow_id = int(built["workflow"]["id"])
    saved = await client.workflows.wait_for_save(
        workflow_id, workflow=built["workflow"], timeout=SAVE_SECONDS, project_id=project
    )
    assert (save_run(saved) or {}).get("status") == "done", save_run(saved)

    started = await triggers.run(workflow_id, project_id=project)
    assert started["run_id"] and started["already_running"] is False
    twice = await triggers.run(workflow_id, project_id=project)
    if twice["already_running"]:
        assert twice["run_id"] == started["run_id"]

    row = await triggers.wait_for_run(
        workflow_id, str(started["run_id"]), timeout=RUN_SECONDS, project_id=project
    )
    assert row is not None and row["result"] == "success", row
    assert (row["trigger"], row["rows_out"] > 0) == ("manual", True)

    waited = await triggers.run(workflow_id, wait=True, timeout=RUN_SECONDS, project_id=project)
    assert waited["result"] == "success", waited
    runs = (await triggers.runs(workflow_id, project_id=project))["runs"]
    assert runs[0]["id"] == waited["run_id"]
    assert {started["run_id"], waited["run_id"]} <= {r["id"] for r in runs}
