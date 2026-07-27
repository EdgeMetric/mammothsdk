"""Every usage error must actually explain itself.

This guards a defect class rather than a single bug. Click raises some usage
errors with a deliberately *empty* message -- a group invoked with no
subcommand is the common one, because Click has already printed the help text
and expects a human to read it. Piped into an agent that only sees the JSON
envelope, that arrived as ``{"code": "usage_error", "message": ""}``: a failure
with no stated reason and nothing to act on. It shipped in several releases
before anyone noticed, precisely because no test asserted the message was
non-empty.

So this sweeps the *whole* registered command tree rather than a hand-picked
sample: every group, plus the malformed invocations that reach the top-level
renderer. A new group, or a new Click version that adds another empty-message
error, is covered without anyone remembering to extend the list.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.main import get_command

from mammoth_cli.app import app
from mammoth_cli.testing import make_runner


def _group_paths() -> list[list[str]]:
    """Every command group in the tree, as an argv prefix.

    A "group" is any node that has subcommands -- exactly the nodes that can be
    invoked with nothing after them.
    """
    paths: list[list[str]] = [[]]

    def walk(command: Any, prefix: list[str]) -> None:
        children = getattr(command, "commands", None)
        if not children:
            return
        for name, child in children.items():
            child_path = [*prefix, name]
            if getattr(child, "commands", None):
                paths.append(child_path)
                walk(child, child_path)

    walk(get_command(app), [])
    return paths


_GROUP_PATHS = _group_paths()


def _envelope_error(args: list[str]) -> dict[str, Any]:
    result = make_runner().invoke(args)
    start = result.output.find("{")
    assert start != -1, f"{args}: no machine envelope in output: {result.output!r}"
    payload = json.loads(result.output[start:])
    assert "error" in payload, f"{args}: expected an error envelope, got {payload!r}"
    return dict(payload["error"])


def test_the_sweep_actually_covers_the_tree() -> None:
    """Sanity: the walk found the root plus a realistic number of groups."""
    assert [] in _GROUP_PATHS
    assert ["view"] in _GROUP_PATHS
    assert len(_GROUP_PATHS) >= 30, len(_GROUP_PATHS)


@pytest.mark.parametrize(
    "path", _GROUP_PATHS, ids=[" ".join(p) or "<root>" for p in _GROUP_PATHS]
)
def test_a_group_invoked_with_no_subcommand_explains_itself(path: list[str]) -> None:
    error = _envelope_error(path)

    assert error["code"], f"{path}: empty error code"
    assert error["message"].strip(), (
        f"'mammoth {' '.join(path)}' returned a usage error with an empty message; "
        "give it a real one in mammoth_cli.app._usage_error_report"
    )
    # An empty hint is allowed, but a whitespace-only one is a formatting bug.
    if error["hint"] is not None:
        assert error["hint"].strip(), f"{path}: whitespace-only hint"


@pytest.mark.parametrize(
    "args",
    [
        ["definitely-not-a-command"],
        ["view", "definitely-not-a-subcommand"],
        ["--profile", "prod", "doctor"],
        ["--output", "json"],
        ["view", "--profile", "prod"],
        ["project", "list", "--not-an-option"],
    ],
    ids=[
        "unknown-command",
        "unknown-subcommand",
        "global-option-before-command",
        "global-option-with-no-command",
        "global-option-after-a-group",
        "unknown-option-on-a-leaf",
    ],
)
def test_malformed_invocations_explain_themselves(args: list[str]) -> None:
    error = _envelope_error(args)

    assert error["code"]
    assert error["message"].strip(), f"{args}: usage error with an empty message"


@pytest.mark.parametrize(
    "path", _GROUP_PATHS, ids=[" ".join(p) or "<root>" for p in _GROUP_PATHS]
)
def test_a_group_error_suggests_no_unrunnable_command(path: list[str]) -> None:
    """A recovery command is replayed verbatim, so it must be real.

    Placeholder tokens are the trap: a caller (or an agent) that pastes
    ``mammoth schema find QUERY`` runs a literal search for "QUERY".
    """
    for command in _envelope_error(path)["recovery_commands"]:
        assert "..." not in command, f"{path}: placeholder recovery command: {command!r}"
        for placeholder in ("QUERY", "COMMAND_ID", "NAME"):
            assert placeholder not in command, (
                f"{path}: recovery command contains the placeholder "
                f"{placeholder!r} and is not runnable: {command!r}"
            )
