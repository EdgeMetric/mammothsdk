"""Print the real Typer/Click command tree as JSON (run as a subprocess).

The fuzz harness never keeps a hand list of commands: it asks the same ``app``
that ``mammoth`` runs for every node, so a command added tomorrow is fuzzed
tomorrow. Run in a child process so the parent's import path cannot change
which ``mammoth_cli`` is walked.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import typer

from mammoth_cli.app import app


def _param(param: Any) -> dict[str, Any]:
    type_name = getattr(param.type, "name", "text")
    choices = list(getattr(param.type, "choices", None) or [])
    return {
        "name": param.name,
        "kind": "argument" if param.param_type_name == "argument" else "option",
        "opts": list(getattr(param, "opts", []) or []),
        "secondary_opts": list(getattr(param, "secondary_opts", []) or []),
        "is_flag": bool(getattr(param, "is_flag", False)),
        "required": bool(param.required),
        "type": type_name,
        "choices": choices,
        "multiple": bool(getattr(param, "multiple", False)),
        "nargs": int(getattr(param, "nargs", 1) or 1),
        "hidden": bool(getattr(param, "hidden", False)),
    }


def _walk(node: Any, path: list[str]) -> list[dict[str, Any]]:
    children = getattr(node, "commands", None) or {}
    rows = [
        {
            "path": path,
            "is_group": bool(children),
            "params": [_param(p) for p in node.params if p.name != "help"],
        }
    ]
    for name, child in sorted(children.items()):
        rows.extend(_walk(child, [*path, name]))
    return rows


if __name__ == "__main__":
    json.dump(_walk(typer.main.get_command(app), []), sys.stdout)
