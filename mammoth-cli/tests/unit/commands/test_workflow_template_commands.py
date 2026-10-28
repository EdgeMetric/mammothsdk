"""The `workflow template` commands (the project workflow-template catalog, #337).

Each dry run goes through the real CLI parser and handler and stops before the request leaves;
the discovery tests read the shipped manifests, so they fail when a command is not found by the
words a person uses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app.help_text import live_command_summary
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.schema.find import find_schemas
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_API = "mammoth.api.workflow_templates.WorkflowTemplatesAPI"
_KEY = "bank-reconciliation"
_MATCHES = {"main": {"amount": {"column": "Amount"}}}

# (argv, sdk method, expected SDK arguments)
_DRY_RUNS: list[tuple[list[str], str, dict[str, Any]]] = [
    (["workflow", "template", "list"], "list", {}),
    (["workflow", "template", "get", _KEY], "get", {"key": _KEY}),
    (["workflow", "template", "sample-result", _KEY], "sample_result", {"key": _KEY}),
    (
        ["workflow", "template", "rank", _KEY, "--input", '{"input": "main", "dataset_ids": [4]}'],
        "rank",
        {"key": _KEY, "input": "main", "dataset_ids": [4]},
    ),
    (
        ["workflow", "template", "fit", _KEY, "--input", '{"inputs": {"main": 4}}'],
        "fit",
        {"key": _KEY, "inputs": {"main": 4}},
    ),
    (
        [
            *("workflow", "template", "preview", _KEY),
            *("--input", json.dumps({"inputs": {"main": 4}, "matches": _MATCHES})),
        ],
        "preview",
        {"key": _KEY, "inputs": {"main": 4}, "matches": _MATCHES},
    ),
    (["workflow", "template", "samples", _KEY], "import_samples", {"key": _KEY}),
    (
        [
            *("workflow", "template", "build", _KEY),
            *(
                "--input",
                json.dumps(
                    {"inputs": {"main": 4}, "matches": _MATCHES, "destination_name": "Result"}
                ),
            ),
        ],
        "build",
        {"key": _KEY, "destination_name": "Result"},
    ),
]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture(autouse=True)
def _offline(fake_service: FakeMammothService, block_real_network: None) -> FakeMammothService:
    return fake_service


@pytest.mark.parametrize(("argv", "method", "arguments"), _DRY_RUNS, ids=lambda v: str(v)[:40])
def test_the_dry_run_sends_the_expected_catalog_sdk_call(
    argv: list[str], method: str, arguments: dict[str, Any]
) -> None:
    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])

    assert result.exit_code == 0, result.output
    call = json.loads(result.output)["data"]["would_call"]
    assert call["sdk_symbol"] == f"{_API}.{method}"
    assert {k: v for k, v in call["arguments"].items() if k in arguments} == arguments


def test_every_catalog_operation_has_a_command_backed_by_the_catalog_client() -> None:
    commands = {f"workflow.template.{verb}" for verb in (a[0][2] for a in _DRY_RUNS)}
    assert commands <= set(HANDLERS)
    assert {command_by_id(c)["sdk_symbol"] for c in commands} == {  # type: ignore[index]
        f"{_API}.{method}" for _, method, _ in _DRY_RUNS
    }


@pytest.mark.parametrize("query", ["workflow template", "workflow templates"])
def test_schema_find_finds_the_catalog_not_the_legacy_commands(query: str) -> None:
    found = [m["command_id"] for m in find_schemas(query)["matches"]]

    assert found[0].startswith("workflow.template."), found
    assert "workflow.template.list" in found


def test_the_legacy_list_says_which_catalog_it_reads() -> None:
    summary = live_command_summary("template.list") or ""

    assert "legacy" in summary
    assert "workflow template catalog" in summary


def test_the_catalog_commands_are_not_the_legacy_group() -> None:
    assert command_by_id("template.list")["sdk_symbol"] == (  # type: ignore[index]
        "mammoth.api.templates.TemplatesAPI.list"
    )
    assert command_by_id("workflow.template.list")["sdk_symbol"] == f"{_API}.list"  # type: ignore[index]
