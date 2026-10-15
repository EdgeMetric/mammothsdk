"""``meta.next_commands``: the next one to three commands after a main-flow command.

An agent that just uploaded a file, ran a transform or made a dashboard almost
always reads the result next. The suggestions are templates in
``mammoth_cli/discovery/next_commands.json``, filled in with the ids of this
result, so the agent runs them as they are instead of composing a command.
A write that did not verify gets none: its own error or ``verify`` block says
what to do.
"""

from __future__ import annotations

import json
import re
from functools import cache
from importlib import resources
from typing import Any

_MAX = 3
_PLACEHOLDER = re.compile(r"\{(\?)?([a-z_][\w.|-]*)\}")
_NOT_DONE = frozenset({"failed", "partial", "error"})


@cache
def load_map() -> dict[str, tuple[str, ...]]:
    """Command id (or ``prefix.*``) to its next-command templates."""
    text = (
        resources.files("mammoth_cli.discovery").joinpath("next_commands.json").read_text("utf-8")
    )
    raw = json.loads(text)["next_commands"]
    return {key: tuple(templates) for key, templates in raw.items()}


def _templates(command_id: str) -> tuple[str, ...]:
    table = load_map()
    if command_id in table:
        return table[command_id]
    for key, templates in table.items():
        if key.endswith(".*") and command_id.startswith(key[:-1]):
            return templates
    return ()


def _lookup(path: str, data: Any, positionals: dict[str, Any], known: dict[str, Any]) -> Any:
    if path.startswith("arg."):
        return positionals.get(path[4:])
    if path.startswith("inv."):
        return known.get(path[4:])
    value = data
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def _usable(value: Any) -> bool:
    return isinstance(value, (int, str)) and not isinstance(value, bool) and str(value) != ""


def _fill(
    template: str, data: Any, positionals: dict[str, Any], known: dict[str, Any]
) -> str | None:
    missing = False

    def replace(match: re.Match[str]) -> str:
        nonlocal missing
        optional, choices = match.group(1), match.group(2).split("|")
        for path in choices:
            value = _lookup(path, data, positionals, known)
            if _usable(value):
                return str(value)
        if not optional:
            missing = True
        return ""

    filled = _PLACEHOLDER.sub(replace, template)
    return None if missing else " ".join(filled.split())


def _did_not_finish(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    verify = data.get("verify")
    if isinstance(verify, dict) and (
        verify.get("outcome") in _NOT_DONE or verify.get("verified") is False
    ):
        return True
    return data.get("status") in _NOT_DONE


def next_commands(
    command_id: str,
    data: Any,
    positionals: dict[str, Any],
    *,
    known_dataset_id: int | None = None,
) -> list[str]:
    """The filled-in next commands for one successful result, best first."""
    templates = _templates(command_id)
    if not templates or _did_not_finish(data):
        return []
    known = {"known_dataset_id": known_dataset_id}
    found: list[str] = []
    for template in templates:
        filled = _fill(template, data, positionals, known)
        if filled and filled.startswith("mammoth ") and filled not in found:
            found.append(filled)
    return found[:_MAX]


def with_next_commands(invocation: Any, data: Any, meta: dict[str, Any]) -> dict[str, Any]:
    """*meta* with ``next_commands`` added when this command has any."""
    found = next_commands(
        invocation.command_id,
        data,
        dict(invocation.positionals or {}),
        known_dataset_id=invocation.known_dataset_id,
    )
    return {**meta, "next_commands": found} if found else meta
