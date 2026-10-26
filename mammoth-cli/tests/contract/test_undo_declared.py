"""Every write command declares how the journal undoes it, or why it cannot (#311)."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.manifest.loader import command_records, load_commands

_STRATEGIES = {"inverse", "pipeline_version", "trash_created", "manual", "irreversible"}
#: The generic phrases an irreversible reason must not shrink back to.
_GENERIC = {"no command reverses it.", "cannot be undone.", "irreversible."}


def _writes() -> list[dict[str, Any]]:
    return [r for r in command_records() if r["mutation_class"] != "read"]


def _ids() -> set[str]:
    return {r["command_id"] for r in command_records()}


def test_every_write_declares_undo() -> None:
    missing = [r["command_id"] for r in _writes() if "undo" not in r]
    assert not missing, f"declare `undo` (or set it in commands/<group>.yaml): {missing[:10]}"


def test_a_read_declares_no_undo() -> None:
    declared = [
        r["command_id"] for r in command_records() if r["mutation_class"] == "read" and "undo" in r
    ]
    assert not declared, declared


def test_every_strategy_is_in_the_vocabulary() -> None:
    bad = [r["command_id"] for r in _writes() if r["undo"]["strategy"] not in _STRATEGIES]
    assert not bad, bad


def test_an_irreversible_write_says_why() -> None:
    bad = [
        r["command_id"]
        for r in _writes()
        if r["undo"]["strategy"] == "irreversible"
        and (
            len(str(r["undo"].get("reason", "")).split()) < 4
            or str(r["undo"]["reason"]).lower() in _GENERIC
        )
    ]
    assert not bad, bad


def test_irreversible_reasons_are_not_one_string() -> None:
    reasons = [r["undo"]["reason"] for r in _writes() if r["undo"]["strategy"] == "irreversible"]
    assert len(set(reasons)) > len(reasons) // 4


def test_a_named_command_exists_and_is_not_the_write_itself() -> None:
    ids = _ids()
    bad = [
        r["command_id"]
        for r in _writes()
        if r["undo"]["strategy"] in {"inverse", "manual"}
        and (r["undo"]["command"] not in ids or r["undo"]["command"] == r["command_id"])
    ]
    assert not bad, bad


def test_an_inverse_takes_the_arguments_of_the_write() -> None:
    """The journal runs an ``inverse`` with the write's own positionals, so they must match."""
    by_id = {r["command_id"]: r for r in command_records()}
    bad = []
    for record in _writes():
        undo = record["undo"]
        if undo["strategy"] != "inverse":
            continue
        names = [p["name"] for p in record["positionals"]]
        target = [p["name"] for p in by_id[undo["command"]]["positionals"]]
        if names != target:
            bad.append((record["command_id"], names, undo["command"], target))
    assert not bad, bad


def test_an_irreversible_reason_does_not_deny_a_delete_that_exists() -> None:
    """``no delete command exists for it`` is false when ``<object> delete`` is a command."""
    ids = _ids()
    bad = []
    for record in _writes():
        undo = record["undo"]
        if undo["strategy"] != "irreversible" or "no delete command" not in undo["reason"]:
            continue
        prefix = record["command_id"].rpartition(".")[0]
        siblings = [f"{prefix}.{verb}" for verb in ("delete", "remove", "trash")]
        bad.extend((record["command_id"], name) for name in siblings if name in ids)
    assert not bad, f"declare the delete as the undo, or trash_created: {bad}"


def test_a_manual_undo_that_takes_the_same_arguments_says_why_it_is_not_run() -> None:
    """Without a note the message says the undo needs an id the write made: false for these."""
    by_id = {r["command_id"]: r for r in command_records()}
    bad = []
    for record in _writes():
        undo = record["undo"]
        if undo["strategy"] != "manual" or undo.get("note"):
            continue
        own = {p["name"] for p in record["positionals"]}
        target = [p["name"] for p in by_id[undo["command"]]["positionals"]]
        if not set(target) - own:
            bad.append((record["command_id"], undo["command"]))
    assert not bad, f"add an `undo.note` that states the real reason: {bad}"


def test_a_pipeline_version_undo_is_for_a_pipeline_edit() -> None:
    declared = {r["command_id"] for r in _writes() if r["undo"]["strategy"] == "pipeline_version"}
    edits = {r["command_id"] for r in _writes() if r["mutation_class"] == "reversible_pipeline"}
    assert declared == edits


def test_the_compiled_manifest_carries_undo() -> None:
    compiled = {r["command_id"]: r.get("undo") for r in load_commands()}
    stale = [r["command_id"] for r in _writes() if compiled[r["command_id"]] != r["undo"]]
    assert not stale, f"run scripts/build_manifests.py: {stale[:10]}"


@pytest.mark.parametrize(
    ("command_id", "strategy"),
    [
        ("dataset.trash", "inverse"),
        ("dataset.restore", "inverse"),
        ("file.upload", "trash_created"),
        ("view.transform.filter", "pipeline_version"),
        ("dataset.delete", "irreversible"),
        ("view.export.postgres", "irreversible"),
        ("dataset.file-settings.update", "inverse"),
        ("workspace.user.add", "manual"),
    ],
)
def test_known_writes_declare_the_expected_strategy(command_id: str, strategy: str) -> None:
    record = next(r for r in command_records() if r["command_id"] == command_id)
    assert record["undo"]["strategy"] == strategy
