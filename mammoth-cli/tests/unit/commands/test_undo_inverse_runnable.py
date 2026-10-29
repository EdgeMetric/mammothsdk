"""Every ``inverse`` undo declaration builds a line that the inverse command accepts (#318).

The journal records the undo line when the write happens and ``history undo`` runs it later
with ``--yes``. A line the inverse command refuses (a ``confirm_target`` command without
``--confirm``, a ``--session`` that was not carried, an ``--input`` field only the original
had) leaves a write that is declared undoable and is not. This test builds the line for every
declared pair from a sample call and runs it through the real command path with a fake service.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands import history
from mammoth_cli.errors.envelope import EXIT_USAGE
from mammoth_cli.manifest.loader import command_records
from mammoth_cli.runtime import journal
from mammoth_cli.runtime.dispatch import Outcome, Request
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_SAMPLE = {"int": "7", "str": "abc"}


def _pairs() -> list[tuple[str, str]]:
    return [
        (r["command_id"], r["undo"]["command"])
        for r in command_records()
        if r.get("undo", {}).get("strategy") == "inverse"
    ]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _original(command_id: str, tmp_path: Path) -> Request:
    record = next(r for r in command_records() if r["command_id"] == command_id)
    values = {p["name"]: _SAMPLE.get(p.get("type", "str"), "abc") for p in record["positionals"]}
    document = tmp_path / "in.json"
    document.write_text('{"items": [{"kind": "view", "id": 3}]}', encoding="utf-8")
    invocation = Invocation(
        command_id=command_id,
        input_file=str(document) if command_id.startswith("trash.") else None,
        output="json",
        project=9,
        session="sess-1",
        yes=True,
        extra_args=list(values.values()),
    )
    invocation.positionals.update(values)
    return Request(command_id, "json", lambda: ({}, {}), invocation=invocation, profile=None)


@pytest.mark.parametrize(("command_id", "inverse"), _pairs())
def test_the_undo_line_of_an_inverse_pair_passes_the_inverse_commands_checks(
    command_id: str, inverse: str, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    record = next(r for r in command_records() if r["command_id"] == command_id)
    # A set-it-back inverse reads the earlier value from the write's result.
    carried = {src: "add" for src in record["undo"].get("input_from_result", {}).values()}
    lines, reason = journal.compensation(
        _original(command_id, tmp_path), Outcome(data=carried, meta={}), journal._Before()
    )
    assert lines, f"{command_id} declares {inverse} but built no line: {reason}"
    runner = Invocation(command_id="history.undo", output="json")
    exit_status, envelope = history._run(lines[0], runner)
    error = envelope.get("error") or {}
    assert exit_status != EXIT_USAGE, (
        f"{command_id} -> {inverse} is refused when undone: {error.get('code')}: "
        f"{error.get('message')} (line {lines[0]})"
    )
    assert fake_service.call_log or error.get("code") != "confirmation_target_mismatch"


def test_the_sample_pairs_are_not_empty() -> None:
    assert len(_pairs()) >= 20
