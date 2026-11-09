"""The workflow automation commands: run, triggers, describe, editing and template fits.

Each dry run goes through the real CLI parser and handler and stops before the request leaves;
the manifest tests read the shipped manifests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.schema.find import find_schemas
from mammoth_cli.commands.workflow import SAVE_AWAITED, await_built_workflow
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_T = "mammoth.api.workflow_triggers.WorkflowTriggersAPI"
_D = "mammoth.api.workflow_describe.WorkflowDescribeAPI"
_W = "mammoth.api.workflows.WorkflowsAPI"
_C = "mammoth.api.workflow_templates.WorkflowTemplatesAPI"
_SPEC = {"sentence": "Match payouts", "status": "ready"}

# (argv, sdk symbol, expected SDK arguments)
_DRY_RUNS: list[tuple[list[str], str, dict[str, Any]]] = [
    (["workflow", "template", "fits"], f"{_C}.fits", {}),
    (
        ["workflow", "page", "start", "stripe-payouts"],
        f"{_C}.start_page",
        {"slug": "stripe-payouts"},
    ),
    (
        ["workflow", "run", "start", "41", "--input", '{"wait": true}'],
        f"{_T}.run",
        {"workflow_id": 41, "wait": True},
    ),
    (["workflow", "run", "list", "41"], f"{_T}.runs", {"workflow_id": 41}),
    (
        ["workflow", "run", "wait", "41", "r-1"],
        f"{_T}.wait_for_run",
        {"workflow_id": 41, "run_id": "r-1"},
    ),
    (
        ["workflow", "schedule", "set", "41", "--input", '{"frequency": "daily"}'],
        f"{_T}.schedule_set",
        {"workflow_id": 41, "frequency": "daily"},
    ),
    (
        ["workflow", "after", "set", "41", "40"],
        f"{_T}.after_set",
        {"workflow_id": 41, "source_workflow_id": 40},
    ),
    (["workflow", "after", "loops", "41"], f"{_T}.after_loops", {"workflow_id": 41}),
    (["workflow", "link", "create", "41"], f"{_T}.link_create", {"workflow_id": 41}),
    (
        ["workflow", "describe", "start", "--input", '{"text": "Match payouts"}'],
        f"{_D}.start",
        {"text": "Match payouts"},
    ),
    (["workflow", "describe", "get", "d-1"], f"{_D}.draft", {"draft": "d-1"}),
    (["workflow", "describe", "wait", "d-1"], f"{_D}.wait", {"draft": "d-1"}),
    (
        ["workflow", "describe", "build", "--input"]
        + [json.dumps({"spec": _SPEC, "destination_name": "Out"})],
        f"{_D}.build",
        {"spec": _SPEC, "destination_name": "Out"},
    ),
    (["workflow", "describe", "fed-by", "77"], f"{_D}.fed_by", {"view_id": 77}),
    (
        ["workflow", "step-lines", "41", "--input", '{"view_ids": [3]}'],
        f"{_W}.step_lines",
        {"workflow_id": 41, "view_ids": [3]},
    ),
    (["workflow", "repeat-counts"], f"{_W}.repeat_counts", {}),
    (
        ["workflow", "values", "41", "3", "--input", '{"column": "Region", "text": "West"}'],
        f"{_W}.view_values",
        {"workflow_id": 41, "view_id": 3, "column": "Region", "text": "West"},
    ),
    (["workflow", "held", "check", "41"], f"{_W}.holds_check", {"workflow_id": 41}),
    (
        ["workflow", "swap", "apply", "41", "3", "9"],
        f"{_W}.swap",
        {"workflow_id": 41, "view_id": 3, "dataset_id": 9},
    ),
    (["workflow", "swap", "undo", "41"], f"{_W}.swap_undo", {"workflow_id": 41}),
]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture(autouse=True)
def _offline(fake_service: FakeMammothService, block_real_network: None) -> FakeMammothService:
    return fake_service


@pytest.mark.parametrize(("argv", "symbol", "arguments"), _DRY_RUNS, ids=lambda v: str(v)[:48])
def test_the_dry_run_sends_the_expected_sdk_call(
    argv: list[str], symbol: str, arguments: dict[str, Any]
) -> None:
    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])

    assert result.exit_code == 0, result.output
    call = json.loads(result.output)["data"]["would_call"]
    assert call["sdk_symbol"] == symbol
    assert {k: v for k, v in call["arguments"].items() if k in arguments} == arguments


def test_the_link_remove_dry_run_names_the_workflow_it_turns_the_link_off_for(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses["mammoth.api.workflows.WorkflowsAPI.get"] = {"id": 41, "name": "Bank"}

    result = make_runner().invoke(
        [*("workflow", "link", "remove", "41", "--yes", "--project", "25654"), "--dry-run"]
        + ["--output", "json"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["would_call"]["sdk_symbol"] == f"{_T}.link_remove"
    assert data["would_call"]["arguments"]["workflow_id"] == 41
    assert [(t["type"], t["id"], t["name"]) for t in data["targets"]] == [("workflow", 41, "Bank")]


@pytest.mark.parametrize(
    "argv",
    [
        ["workflow", "schedule", "set", "41", "--input", '{"frequency": "yearly"}'],
        ["workflow", "describe", "start", "--input", '{"text": "hi"}'],
        [
            *("workflow", "describe", "build", "--input"),
            json.dumps({"spec": _SPEC, "destination_name": "Out", "schedule": {"x": 1}}),
        ],
    ],
)
def test_a_dry_run_refuses_what_the_sdk_would_refuse(argv: list[str]) -> None:
    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])

    assert result.exit_code != 0
    assert json.loads(result.output)["error"]["code"] == "invalid_arguments"


_COMMANDS = (
    "workflow.template.fits",
    "workflow.page.start",
    "workflow.run.start",
    "workflow.run.wait",
    "workflow.run.list",
    "workflow.schedule.set",
    "workflow.after.set",
    "workflow.after.loops",
    "workflow.link.create",
    "workflow.link.remove",
    "workflow.describe.start",
    "workflow.describe.get",
    "workflow.describe.wait",
    "workflow.describe.check",
    "workflow.describe.build",
    "workflow.describe.sample",
    "workflow.describe.fed-by",
    "workflow.step-lines",
    "workflow.repeat-counts",
    "workflow.before-after",
    "workflow.values",
    "workflow.held.check",
    "workflow.sentence.read",
    "workflow.sentence.dismiss-ask",
    "workflow.swap.fit",
    "workflow.swap.apply",
    "workflow.swap.cancel",
    "workflow.swap.undo",
)


def test_every_new_command_is_registered_and_each_write_declares_its_undo() -> None:
    assert set(_COMMANDS) <= set(HANDLERS)
    for command_id in _COMMANDS:
        record = command_by_id(command_id)
        assert record is not None, command_id
        if record["mutation_class"] != "read":
            assert record.get("undo"), command_id


def test_the_link_removal_asks_first() -> None:
    assert command_by_id("workflow.link.remove")["confirmation"] == "prompt_or_yes"  # type: ignore[index]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("run a workflow on a schedule", "workflow.schedule.set"),
        ("which workflow templates fit my tables", "workflow.template.fits"),
        ("describe a workflow in words", "workflow.describe.start"),
    ],
)
def test_schema_find_finds_the_workflow_commands(query: str, expected: str) -> None:
    found = [m["command_id"] for m in find_schemas(query)["matches"]][:5]

    assert expected in found, found


def _workflow(status: str, steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"id": 41, "canvas_state": {"save_run": {"status": status, "steps": steps or []}}}


class _Service:
    def __init__(self, reads: list[dict[str, Any]]) -> None:
        self.reads = reads

    def call(self, symbol: str, **kwargs: Any) -> dict[str, Any]:
        return self.reads.pop(0)


class _Invocation:
    project = 25654
    job_timeout = 30.0


def test_both_builds_wait_for_their_save(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mammoth_cli.commands.workflow._SAVE_POLL_SECONDS", 0.0)
    monkeypatch.setattr("mammoth_cli.commands.workflow.require_project", lambda inv: 25654)
    service = _Service([_workflow("done")])

    data = await_built_workflow(
        _Invocation(), service, {"workflow": _workflow("running")}  # type: ignore[arg-type]
    )

    assert SAVE_AWAITED == {"workflow.template.build", "workflow.describe.build"}
    assert data["workflow"]["canvas_state"]["save_run"]["status"] == "done"


def test_a_build_whose_save_left_steps_unbuilt_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mammoth_cli.commands.workflow.require_project", lambda inv: 25654)
    partial = _workflow("partial", [{"label": "Join", "error": "column gone"}])

    with pytest.raises(CliError) as caught:
        await_built_workflow(_Invocation(), _Service([]), {"workflow": partial})  # type: ignore[arg-type]

    assert "Join: column gone" in caught.value.message
