"""The manifest's command tree: which token paths are commands and which are groups."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

from mammoth_cli.manifest.loader import load_commands

if TYPE_CHECKING:
    pass


def _command_records() -> list[dict[str, Any]]:
    return [r for r in load_commands() if r.get("disposition") != "alias"]


@cache
def _command_tree() -> tuple[dict[tuple[str, ...], str], frozenset[tuple[str, ...]]]:
    """Map every command path to its id, and name the container nodes.

    A "container command" sits at a node that also has deeper subcommands
    (e.g. ``dataset file-settings``, which also has ``... undo`` / ``... update``).
    """
    path_to_command = {
        tuple(r["command_path"].split()): r["command_id"] for r in _command_records()
    }
    prefixes: set[tuple[str, ...]] = set()
    for tokens in path_to_command:
        for depth in range(1, len(tokens)):
            prefixes.add(tokens[:depth])
    return path_to_command, frozenset(prefixes & path_to_command.keys())
