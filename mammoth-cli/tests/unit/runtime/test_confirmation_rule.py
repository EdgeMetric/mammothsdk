"""One rule decides which commands ask before they act (verb and mutation class, not taste).

A command that removes, clears, discards or deletes something the caller cannot get back with one
more command must carry a confirmation policy (``prompt_or_yes``, ``confirm_target`` or
``yes_always``).  Commands that are reversible, local-only, or state-of-a-draft are listed in
:data:`PROMPTLESS` with the reason, so the exceptions are reviewed rather than accidental.
"""

from __future__ import annotations

import pytest

from mammoth_cli.manifest.loader import load_commands

_DESTRUCTIVE_VERBS = frozenset({"remove", "clear", "discard", "delete"})

#: Promptless destructive-verb commands, each with the reason it is safe to run unasked.
PROMPTLESS: dict[str, str] = {
    "dashboard.filter.remove": "edits a filter on the working canvas; add it again to undo",
    "context.project.clear": "clears the local active-project pointer only; no server data",
}


def _records() -> list[dict]:
    return [dict(r) for r in load_commands() if r.get("disposition") != "alias"]


def test_destructive_verbs_ask_unless_listed_with_a_reason() -> None:
    offenders = [
        r["command_id"]
        for r in _records()
        if r["command_id"].split(".")[-1] in _DESTRUCTIVE_VERBS
        and r["mutation_class"] not in {"read", "reversible_pipeline"}
        and r["confirmation"] == "none"
        and r["command_id"] not in PROMPTLESS
    ]
    assert not offenders, f"destructive commands that ask nothing: {offenders}"


def test_every_promptless_exception_is_real_and_has_a_reason() -> None:
    by_id = {r["command_id"]: r for r in _records()}
    for command_id, reason in PROMPTLESS.items():
        assert reason.strip()
        assert by_id[command_id]["confirmation"] == "none", f"{command_id} now asks; drop it here"


@pytest.mark.parametrize(
    "command_id", ["project.memory.remove", "agent.projects.clear", "agent.plan.discard"]
)
def test_the_three_reported_commands_prompt_or_yes(command_id: str) -> None:
    by_id = {r["command_id"]: r for r in _records()}
    assert by_id[command_id]["confirmation"] == "prompt_or_yes"
    assert "--yes" in by_id[command_id]["agent_example"]


@pytest.mark.parametrize(
    "command_id",
    [
        "dashboard.filter.remove",
        "context.project.clear",
        "view.trash",
        "dataset.trash",
        "dashboard.trash",
        "automation.trash",
        "folder.trash",
        "workflow.archive",
        "dashboard.tags.rename",
    ],
)
def test_reversible_commands_stay_promptless(command_id: str) -> None:
    by_id = {r["command_id"]: r for r in _records()}
    assert by_id[command_id]["confirmation"] == "none"
    assert "--yes" not in by_id[command_id]["agent_example"]
