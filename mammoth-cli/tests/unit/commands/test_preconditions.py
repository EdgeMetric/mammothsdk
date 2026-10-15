"""Risky commands say what they do and what to check first; none shows a bare internal code."""

from __future__ import annotations

import re

import pytest

from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import load_commands

_RISKY = {"destructive", "high_impact", "external_effect"}
_STUB = re.compile(r"^(B\d{2}\.?|Fixture required\.?)$|\bB\d{2}\.$")


def _records() -> list[dict]:
    return [dict(r) for r in load_commands() if r.get("disposition") != "alias"]


def test_every_risky_command_has_preconditions() -> None:
    empty = [
        r["command_id"]
        for r in _records()
        if r["mutation_class"] in _RISKY and not get_schema(r["command_id"])["preconditions"]
    ]
    assert empty == []


def test_no_command_shows_a_bare_internal_code_as_its_preconditions() -> None:
    stubs = {
        r["command_id"]: get_schema(r["command_id"])["preconditions"]
        for r in _records()
        if _STUB.search(str(get_schema(r["command_id"])["preconditions"] or ""))
    }
    assert stubs == {}


def test_preconditions_name_only_commands_that_exist() -> None:
    paths = {str(r["command_path"]) for r in load_commands()}
    problems = []
    for r in _records():
        text = get_schema(r["command_id"])["preconditions"] or ""
        for quoted in re.findall(r"`([a-z][a-z -]*?)(?: [A-Z_]+)?`", text):
            words = quoted.split()
            if quoted.startswith(("mammoth ",)):
                words = words[1:]
            candidate = " ".join(words)
            if len(words) >= 2 and not any(
                p == candidate or p.startswith(candidate + " ") or candidate.startswith(p + " ")
                for p in paths
            ):
                problems.append((r["command_id"], quoted))
    assert problems == []


@pytest.mark.parametrize(
    ("command_id", "needle"),
    [
        ("user.delete-account", "WORKSPACE_ID"),
        ("workspace.reactivate", "--confirm"),
        ("billing.stripe.cancel", "billing stripe status"),
        ("schedule.create", "automation create"),
        ("client-app.list", "client apps"),
    ],
)
def test_the_reported_commands_say_something_useful(command_id: str, needle: str) -> None:
    assert needle in get_schema(command_id)["preconditions"]
