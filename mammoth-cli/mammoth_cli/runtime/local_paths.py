"""Which commands read a path on the machine running the CLI.

The manifest marks such a positional with ``kind: local_path``
(:data:`mammoth_cli.services.positionals.LOCAL_PATH`), and an input field the same
way in ``schema get``. A host that embeds the CLI (:mod:`mammoth_cli.embed`) has
no user machine to read from, so :func:`local_path_commands` is the set it
refuses; a new command with a marked path is covered without another edit.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache
from typing import Any

from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.services.positional_spec import LOCAL_PATH, LOCAL_PATH_INPUT_FIELDS


def local_path_fields(command_id: str, positionals: Iterable[dict[str, Any]]) -> frozenset[str]:
    """The ``--input`` fields of ``command_id`` that take a host path.

    A local-path positional that falls back to a field marks that field; the
    rest come from :data:`LOCAL_PATH_INPUT_FIELDS`.
    """
    fields = set(LOCAL_PATH_INPUT_FIELDS.get(command_id, ()))
    for item in positionals:
        if item.get("kind") == LOCAL_PATH and item.get("falls_back_to_field"):
            fields.add(str(item["falls_back_to_field"]))
    return frozenset(fields)


@cache
def local_path_commands() -> frozenset[str]:
    """Every command with a local-path positional or input field."""
    found = {
        str(record["command_id"])
        for record in load_commands()
        if any(item.get("kind") == LOCAL_PATH for item in record.get("positionals", []))
    }
    return frozenset(found | LOCAL_PATH_INPUT_FIELDS.keys())
