"""Every recipe passes positionals in the order its command takes them (#309).

The live sweep of 2026-10-26 found ``revert-view-version`` passing ``VIEW_ID DATASET_ID
VERSION_ID`` to ``view version get``/``apply``, which take ``VIEW_ID VERSION_ID
DATASET_ID``: the server read the version id as the dataset id and answered 404.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

import pytest

from mammoth_cli.discovery import load_recipes, runnable_recipes
from mammoth_cli.manifest.loader import command_by_id

_BINDING = re.compile(r"^\{\{\s*([^}]+?)\s*\}\}$")


def _positionals(command_id: str) -> list[dict[str, Any]]:
    """The positionals *command_id* takes, in order.

    Args:
        command_id: A dotted command id.

    Returns:
        Its manifest positionals.
    """
    record = command_by_id(command_id)
    assert record is not None, f"unknown command {command_id}"
    return list(record.get("positionals") or [])


def _bound_name(arg: Any) -> str | None:
    """The field a ``{{...}}`` binding names: its last path segment.

    Args:
        arg: One positional argument of a run line.

    Returns:
        ``view_id`` for ``{{inputs.view_id}}`` or ``{{steps.up.data.datasets[0].view.view_id}}``;
        None when *arg* is not a whole-value binding.
    """
    match = _BINDING.match(arg) if isinstance(arg, str) else None
    return match.group(1).rsplit(".", 1)[-1] if match else None


def _misplaced(names: list[str | None], positionals: list[dict[str, Any]], key: str) -> list[str]:
    """Each argument that names a positional but sits in another one's slot.

    Args:
        names: The positional name each argument stands for, or None when unknown.
        positionals: The command's positionals, in order.
        key: The positional field *names* uses (``name`` or ``metavar``).

    Returns:
        One message per misplaced argument.
    """
    order = [p[key] for p in positionals]
    return [
        f"argument {index + 1} is {name}, but that slot takes {order[index]}"
        for index, name in enumerate(names)
        if name in order and index < len(order) and order[index] != name
    ]


@pytest.mark.parametrize("recipe", runnable_recipes(), ids=lambda r: r["id"])
def test_run_lines_pass_positionals_in_order(recipe: dict[str, Any]) -> None:
    problems = []
    for line in recipe["run"]:
        command_id = line["cmd"].replace(" ", ".")
        names = [_bound_name(arg) for arg in line.get("args") or []]
        for problem in _misplaced(names, _positionals(command_id), "name"):
            problems.append(f"{line.get('name') or line['cmd']}: {problem}")
    assert not problems, problems


@pytest.mark.parametrize("recipe", load_recipes(), ids=lambda r: r["id"])
def test_step_examples_pass_positionals_in_order(recipe: dict[str, Any]) -> None:
    problems = []
    for step in recipe["steps"]:
        words = shlex.split(step["example"].split(" --", 1)[0])
        command_words = step["command_id"].split(".")
        if words[1 : 1 + len(command_words)] != command_words:
            continue
        names = words[1 + len(command_words) :]
        for problem in _misplaced(list(names), _positionals(step["command_id"]), "metavar"):
            problems.append(f"{step['command_id']}: {problem}")
    assert not problems, problems
