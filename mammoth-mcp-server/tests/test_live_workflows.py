"""The workflow tools against a real Mammoth, called through the MCP server as a client calls them.

No doubles: the module imports a template's sample tables into the configured project with
the SDK, then drives every workflow tool: find, draft, build, list, get, trigger and run. It
leaves the project as it found it: every workflow and table made is deleted at the end, even
when an assertion fails. Run it with `pytest -m live`; it skips itself when the environment is not set. The run
test needs a server with `POST .../workflows/{id}/run`.

Required env vars: MCP_LIVE_API_TOKEN (an `mm_` bearer), MCP_LIVE_API_URL,
MCP_LIVE_WORKSPACE_ID, MCP_LIVE_PROJECT_ID. Redis is not needed: no workflow tool keeps state.
"""

import contextlib
import os
import time
from collections.abc import Generator, Iterator
from typing import Any

import pytest
from mammoth import MammothClient
from mammoth.exceptions import MammothAPIError
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.sdk import set_api_url

from .helpers import API_URL, as_caller, call_tool, run

_REQUIRED_ENV = (
    "MCP_LIVE_API_TOKEN",
    "MCP_LIVE_API_URL",
    "MCP_LIVE_WORKSPACE_ID",
    "MCP_LIVE_PROJECT_ID",
)
_missing = [name for name in _REQUIRED_ENV if not os.environ.get(name)]
if _missing:
    pytest.skip(f"Missing env vars: {', '.join(_missing)}", allow_module_level=True)

pytestmark = pytest.mark.live

TEMPLATE = "bank-reconciliation"
_RUN_SECONDS = 300
_POLL_SECONDS = 3


class Live:
    """The live project the tools act in, and the sample tables in it."""

    def __init__(self, workspace_id: int, project_id: int, inputs: dict[str, int]) -> None:
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.inputs = inputs

    def tool(self, name: str, **arguments: object) -> Any:
        """Call one tool in this project, as the live caller."""
        return call_tool(
            name, workspace_id=self.workspace_id, project_id=self.project_id, **arguments
        )


async def _made(client: MammothClient) -> tuple[set[int], set[int]]:
    """Read the ids of the project's workflows and of its newest tables.

    Args:
        client: An SDK client set to the project.

    Returns:
        The workflow ids and the dataset ids.
    """
    workflows = {int(w["id"]) for w in await client.workflows.list()}
    return workflows, {int(d["id"]) for d in (await client.datasets.list())["datasets"]}


async def _delete_new(client: MammothClient, before: tuple[set[int], set[int]]) -> None:
    """Delete every workflow and table made since `before` was read.

    Args:
        client: An SDK client set to the project.
        before: What `_made` read at the start.
    """
    workflows, datasets = await _made(client)
    for workflow_id in workflows - before[0]:
        with contextlib.suppress(MammothAPIError):
            await client.workflows.delete(workflow_id)
    for dataset_id in datasets - before[1]:
        with contextlib.suppress(MammothAPIError):
            await client.datasets.delete(dataset_id)


@pytest.fixture(scope="module")
def live() -> Iterator[Live]:
    """The template's samples in the project, the server pointed at it; cleaned up at the end."""
    workspace_id = int(os.environ["MCP_LIVE_WORKSPACE_ID"])
    project_id = int(os.environ["MCP_LIVE_PROJECT_ID"])
    client = MammothClient(
        api_token=os.environ["MCP_LIVE_API_TOKEN"], base_url=os.environ["MCP_LIVE_API_URL"]
    )
    client.set_workspace_id(workspace_id)
    client.set_project_id(project_id)
    before = run(_made(client))
    set_api_url(os.environ["MCP_LIVE_API_URL"])
    try:
        samples = run(client.workflow_templates.import_samples(TEMPLATE, project_id=project_id))
        inputs = {key: int(dataset_id) for key, dataset_id in samples["inputs"].items()}
        with as_caller(os.environ["MCP_LIVE_API_TOKEN"], workspace_id, project_id):
            yield Live(workspace_id, project_id, inputs)
    finally:
        set_api_url(API_URL)
        run(_delete_new(client, before))


@pytest.fixture(scope="module")
def built(live: Live) -> Generator[int]:
    """The template drafted with the fitted columns and built; its workflow id."""
    found = live.tool(
        "find_workflow_template", words="reconcile bank", dataset_ids=list(live.inputs.values())
    )
    card = next(c for c in found["templates"] if c["key"] == TEMPLATE)
    assert card["fits"]["tables"] == live.inputs

    draft = live.tool("draft_workflow", template_key=TEMPLATE, inputs=live.inputs)
    assert {q["status"] for q in draft["questions"]} <= {"check"}, draft["questions"]
    assert draft["preview"]

    made = live.tool(
        "build_workflow",
        destination_name="MCP live rec",
        template_key=TEMPLATE,
        inputs=live.inputs,
        matches=draft["matches"],
    )
    workflow_id = int(made["workflow"]["id"])
    deadline = time.monotonic() + _RUN_SECONDS
    while made["saved"] == "running" and time.monotonic() < deadline:
        time.sleep(_POLL_SECONDS)
        made = live.tool("get_workflow", workflow_id=workflow_id)
    assert made["saved"] == "done", made["saved"]
    yield workflow_id


def test_built_workflow_is_listed_and_read(live: Live, built: int) -> None:
    listed = live.tool("list_workflows")
    assert built in [w["id"] for w in listed["workflows"]]
    got = live.tool("get_workflow", workflow_id=built)
    assert (got["workflow"]["id"], got["saved"]) == (built, "done")


def test_triggers(live: Live, built: int) -> None:
    clock = live.tool(
        "set_workflow_trigger",
        workflow_id=built,
        kind="schedule",
        frequency="weekly",
        by_week_day=["mo"],
    )
    assert clock["automation_id"]
    link = live.tool("set_workflow_trigger", workflow_id=built, kind="link")
    assert link["secret"] and str(built) in link["path"]
    assert live.tool("set_workflow_trigger", workflow_id=built, kind="unlink") == {"unlinked": True}
    with pytest.raises(ToolError):
        live.tool("set_workflow_trigger", workflow_id=built, kind="after")


def test_run_once_and_not_twice(live: Live, built: int) -> None:
    first = live.tool("run_workflow", workflow_id=built)
    assert first["run_id"]
    if first["result"] == "running":
        second = live.tool("run_workflow", workflow_id=built)
        assert (second["run_id"], second["already_running"]) == (first["run_id"], True)

    deadline = time.monotonic() + _RUN_SECONDS
    row = first["run"]
    while (row is None or row["result"] == "running") and time.monotonic() < deadline:
        time.sleep(_POLL_SECONDS)
        runs = live.tool("get_workflow", workflow_id=built)["runs"]
        row = next((r for r in runs if r["id"] == first["run_id"]), None)
    assert row is not None and row["result"] == "success", row
    assert (row["trigger"], row["rows_out"] > 0) == ("manual", True)
