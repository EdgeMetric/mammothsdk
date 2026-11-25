"""Live: a workflow's whole life through the CLI: CRUD, triggers, a template, and runs.

Runs the real CLI in-process against a real tenant (no doubles) in the configured project
(``MAMMOTH_PROJECT_ID``), and leaves it as it found it: every workflow and table made is
deleted at the end, even when an assertion fails. The run test needs a server with
``POST .../workflows/{id}/run``.

    pytest tests/live/test_workflow_lifecycle.py -m live -v
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest
from live_harness import LiveCli, wait_for
from mammoth.api.workflows import save_is_running, save_run

pytestmark = pytest.mark.live

TEMPLATE = "bank-reconciliation"
_RUN = json.dumps({"wait": True, "timeout": 300})


def _ids(listed: Any) -> list[int]:
    """Read the workflow ids out of ``workflow list`` data.

    Args:
        listed: The command's ``data``.

    Returns:
        The workflow ids.
    """
    rows = listed if isinstance(listed, list) else listed["workflows"]
    return [int(w["id"]) for w in rows]


def _made(cli: LiveCli, project: int) -> tuple[set[int], set[int]]:
    """Read the ids of the project's workflows and of its newest tables.

    Args:
        cli: The live CLI.
        project: The project to read.

    Returns:
        The workflow ids and the dataset ids.
    """
    workflows = set(_ids(cli.ok("workflow", "list", project=project)[0]))
    listed, _ = cli.ok("dataset", "list", project=project)
    return workflows, {int(d["id"]) for d in listed["datasets"]}


@pytest.fixture(scope="module")
def project(live_cli: LiveCli, live_project: str) -> Iterator[int]:
    """Yield the configured project; delete what the module made in it at the end.

    Args:
        live_cli: The live CLI.
        live_project: The configured project id.

    Yields:
        The project id.
    """
    p = int(live_project)
    workflows, datasets = _made(live_cli, p)
    try:
        yield p
    finally:
        workflows_now, datasets_now = _made(live_cli, p)
        for workflow in workflows_now - workflows:
            live_cli.run("workflow", "delete", str(workflow), "--yes", project=p)
        for dataset in map(str, datasets_now - datasets):
            live_cli.run("dataset", "delete", dataset, "--yes", "--confirm", dataset, project=p)


def test_crud(live_cli: LiveCli, project: int) -> None:
    """Create, read, list, rename and delete a workflow."""
    p = project
    made, _ = live_cli.ok("workflow", "create", "CLI live A", project=p)
    workflow = str(made["id"])
    assert made["name"] == "CLI live A"
    assert int(workflow) in _ids(live_cli.ok("workflow", "list", project=p)[0])

    update = json.dumps({"name": "CLI live A renamed", "notes": "live"})
    live_cli.ok("workflow", "update", workflow, "--input", update, project=p)
    got, _ = live_cli.ok("workflow", "get", workflow, project=p)
    assert (got["name"], got.get("notes")) == ("CLI live A renamed", "live")

    live_cli.ok("workflow", "delete", workflow, "--yes", project=p)
    live_cli.err("workflow", "get", workflow, project=p)
    assert int(workflow) not in _ids(live_cli.ok("workflow", "list", project=p)[0])


def test_triggers(live_cli: LiveCli, project: int) -> None:
    """A clock (set, then replaced), an "after" with its loop guard, and the secret link."""
    p = project
    first = str(live_cli.ok("workflow", "create", "CLI live first", project=p)[0]["id"])
    second = str(live_cli.ok("workflow", "create", "CLI live second", project=p)[0]["id"])

    weekly = json.dumps({"frequency": "weekly", "by_week_day": ["mo"], "start_now": False})
    assert live_cli.ok("workflow", "schedule", "set", first, "--input", weekly, project=p)[0][
        "automation_id"
    ]
    daily = json.dumps({"frequency": "daily", "interval": 2, "start_now": False})
    assert live_cli.ok("workflow", "schedule", "set", first, "--input", daily, project=p)[0][
        "automation_id"
    ]

    assert live_cli.ok("workflow", "after", "set", second, first, project=p)[0]["automation_id"]
    loops, _ = live_cli.ok("workflow", "after", "loops", first, project=p)
    assert int(second) in loops["would_loop"]
    live_cli.err("workflow", "after", "set", first, second, project=p)

    link, _ = live_cli.ok("workflow", "link", "create", first, project=p)
    assert link["secret"] and first in link["path"]
    live_cli.ok("workflow", "link", "remove", first, "--yes", project=p)

    for workflow in (second, first):
        live_cli.ok("workflow", "delete", workflow, "--yes", project=p)


def test_template_build_and_run(live_cli: LiveCli, project: int) -> None:
    """Import a template's samples, fit, preview and build it, then run it and list the runs."""
    p = project
    cards, _ = live_cli.ok("workflow", "template", "list", project=p)
    rows = cards if isinstance(cards, list) else cards["templates"]
    assert TEMPLATE in [c["key"] for c in rows]
    live_cli.ok("workflow", "template", "get", TEMPLATE, project=p)

    samples, _ = live_cli.ok("workflow", "template", "samples", TEMPLATE, project=p)
    inputs = {key: int(dataset) for key, dataset in samples["inputs"].items()}
    fitted, _ = live_cli.ok(
        "workflow",
        "template",
        "fit",
        TEMPLATE,
        "--input",
        json.dumps({"inputs": inputs}),
        project=p,
    )
    matches: dict[str, dict[str, Any]] = {}
    for table in fitted["inputs"]:
        for role in table["roles"]:
            assert role["status"] in ("matched", "check") and role["mapping"], role
            matches.setdefault(table["key"], {})[role["role"]] = role["mapping"]

    use = {"inputs": inputs, "matches": matches}
    assert live_cli.ok(
        "workflow", "template", "preview", TEMPLATE, "--input", json.dumps(use), project=p
    )[0]
    build = json.dumps({**use, "destination_name": "CLI live rec"})
    built, _ = live_cli.ok("workflow", "template", "build", TEMPLATE, "--input", build, project=p)
    workflow = str(built["workflow"]["id"])
    saved = wait_for(
        lambda: live_cli.ok("workflow", "get", workflow, project=p)[0],
        lambda record: not save_is_running(record),
        timeout=300,
        interval=3,
    )
    assert (save_run(saved) or {}).get("status") == "done", save_run(saved)

    ran, _ = live_cli.ok("workflow", "run", "start", workflow, "--input", _RUN, project=p)
    assert (ran["result"], ran["run"]["trigger"]) == ("success", "manual"), ran
    assert ran["run"]["rows_out"] > 0

    runs, _ = live_cli.ok("workflow", "run", "list", workflow, project=p)
    assert runs["runs"][0]["id"] == ran["run_id"]
    waited, _ = live_cli.ok(
        "workflow", "run", "wait", workflow, ran["run_id"], "--input", '{"timeout": 0}', project=p
    )
    assert waited["result"] == "success"
