"""The ``capabilities`` command: what the CLI cannot do yet, and what to do instead.

An agent that hits a gap (a file dataset that will not refresh, a token for
two projects) otherwise tries command after command, or tells the user it is
impossible when a workaround exists. The list lives in
``mammoth_cli/discovery/limitations.json``; each entry names the area, the
limitation, what to do instead, the workaround commands and the skill doc.
``schema find --unsupported [WORDS]`` returns the same list, narrowed by words.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.runtime.invocation import Invocation

_HINT = (
    "Each entry's workarounds are ready to run once the upper-case ids are filled in. "
    "Run 'mammoth how \"GOAL\"' for a whole recipe."
)


@cache
def load_limitations() -> tuple[dict[str, Any], ...]:
    """The known limitations shipped in the package, in file order."""
    text = resources.files("mammoth_cli.discovery").joinpath("limitations.json").read_text("utf-8")
    return tuple(json.loads(text)["limitations"])


def _command_path(command_id: str) -> str:
    from mammoth_cli.manifest.loader import command_by_id

    record = command_by_id(command_id)
    return "mammoth " + (str(record["command_path"]) if record else command_id.replace(".", " "))


def _entry(limitation: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": limitation["id"],
        "area": limitation["area"],
        "limitation": limitation["limitation"],
        "instead": limitation["instead"],
        "workarounds": [
            {
                "command": _command_path(item["command_id"]),
                "command_id": item["command_id"],
                "example": item["example"],
            }
            for item in limitation["workarounds"]
        ],
        "doc": limitation["doc"],
    }


def _matches(limitation: dict[str, Any], terms: tuple[str, ...]) -> bool:
    from mammoth_cli.commands.schema.find import _token_aliases, _tokens

    vocabulary = _tokens(
        " ".join(
            [
                limitation["id"],
                limitation["area"],
                limitation["limitation"],
                *limitation.get("keywords", []),
            ]
        )
    )
    return any(_token_aliases(term) & vocabulary for term in terms)


def unsupported(words: str = "") -> dict[str, Any]:
    """Every known limitation, or those that match ``words`` when any match."""
    from mammoth_cli.commands.schema.find import _query_tokens

    entries = list(load_limitations())
    terms = _query_tokens(words) if words.strip() else ()
    result: dict[str, Any] = {}
    if terms:
        picked = [entry for entry in entries if _matches(entry, terms)]
        result["query"] = words
        if picked:
            entries = picked
        else:
            result["note"] = (
                f"No known limitation matched '{words}'; every limitation is listed. "
                "The CLI may simply support it: run 'mammoth how \"GOAL\"' or "
                "'mammoth schema find \"WORDS\"'."
            )
    result["limitations"] = [_entry(entry) for entry in entries]
    result["count"] = len(entries)
    result["hint"] = _HINT
    return result


def capabilities(invocation: Invocation) -> HandlerResult:
    """List what the CLI cannot do yet, and what to do instead."""
    return unsupported(), {}
