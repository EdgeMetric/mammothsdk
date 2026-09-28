"""Contract test for D-077: every CLI write returns its new state.

See ``CONTRACT-write-state.md`` (the shared contract every family-owning
agent on ``feat/write-state-readback`` builds against) for the manifest shape
this enforces: every command whose ``mutation_class`` is not ``read``
declares exactly one of ``readback`` / ``no_readback`` in its command record.
The per-kind object shape of ``readback`` itself (``command``/``ids``/``kind``,
no extra fields) is already enforced by ``test_schema_validation.py`` against
``schema-v1.json``; this file checks the parts the schema cannot: that every
family has actually declared one, that a declared ``readback.command`` names
a real read command, and that its ``ids`` sources are well-formed.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.manifest.loader import load_commands

#: Families that have not yet declared readback/no_readback for every one of
#: their write commands. A family is removed from this set the moment its
#: declarations land (see the family-owning agents on this branch). THIS SET
#: MUST BE EMPTY BEFORE RELEASE -- it is a standing TODO list, not a
#: permanent exemption, and the "every write declares one" check below is
#: skipped (not passed) for any family still in it.
PENDING_FAMILIES: set[str] = {
    "activity",
    "annotation",
    "browse",
    "calc",
    "capability",
    "dashboard",
    "data-app",
    "doctor",
    "job",
    "log",
    "report",
    "schema",
    "snippet",
    "template",
    "version",
}

_VALID_ID_SOURCE_PREFIXES = ("result.", "input.", "positional.")


def _family(command_id: str) -> str:
    return command_id.split(".", 1)[0]


def _write_commands() -> list[dict[str, Any]]:
    return [c for c in load_commands() if c.get("mutation_class") != "read"]


def _families_with_writes() -> list[str]:
    return sorted({_family(c["command_id"]) for c in _write_commands()})


@pytest.mark.parametrize("family", _families_with_writes())
def test_every_write_declares_readback_or_no_readback(family: str) -> None:
    """Every write in a landed family declares exactly one of readback/no_readback."""
    if family in PENDING_FAMILIES:
        pytest.skip(f"{family}: readback declarations not landed yet (see PENDING_FAMILIES)")
    offenders = []
    for command in _write_commands():
        if _family(command["command_id"]) != family:
            continue
        has_readback = isinstance(command.get("readback"), dict)
        has_no_readback = bool(command.get("no_readback"))
        if has_readback == has_no_readback:  # neither declared, or both declared
            offenders.append(command["command_id"])
    assert (
        not offenders
    ), f"{family}: every write must declare exactly one of readback/no_readback: {offenders}"


def test_readback_command_is_a_real_read_command() -> None:
    """A declared ``readback.command`` must name a command that actually exists and reads."""
    read_ids = {c["command_id"] for c in load_commands() if c.get("mutation_class") == "read"}
    offenders: dict[str, object] = {}
    for command in _write_commands():
        readback = command.get("readback")
        if not isinstance(readback, dict):
            continue
        target = readback.get("command")
        if target not in read_ids:
            offenders[command["command_id"]] = target
    assert not offenders, f"readback.command must name a real read command: {offenders}"


def test_readback_ids_sources_are_well_formed() -> None:
    """Every ``ids`` value names a recognized source, and a positional one exists on the write."""
    offenders: dict[str, list[str]] = {}
    for command in _write_commands():
        readback = command.get("readback")
        if not isinstance(readback, dict):
            continue
        positionals = command.get("positionals") or []
        bad = []
        for name, source in (readback.get("ids") or {}).items():
            if not isinstance(source, str) or not source.startswith(_VALID_ID_SOURCE_PREFIXES):
                bad.append(f"{name}={source!r}: not a result./input./positional. source")
                continue
            if source.startswith("positional."):
                index = source[len("positional.") :]
                if not index.isdigit() or int(index) >= len(positionals):
                    bad.append(f"{name}={source!r}: no positional at index {index} on this write")
        if bad:
            offenders[command["command_id"]] = bad
    assert not offenders, f"readback.ids sources must be resolvable: {offenders}"
