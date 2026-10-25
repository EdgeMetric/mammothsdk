"""``history undo``: the account an undo runs as (#318, second review)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.context.resolver import API_TOKEN_ENV
from mammoth_cli.runtime import journal
from mammoth_cli.runtime.dispatch import Outcome, Request
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import login_default_profile, make_runner

_UNDO = [{"cmd": "dataset restore", "args": [5], "flags": {"project": 9}}]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Every undo line's argv; each succeeds."""
    calls: list[list[str]] = []

    def execute(argv: list[str], command: str = "") -> tuple[int, dict[str, Any]]:
        calls.append(list(argv))
        return 0, {"data": {}}

    monkeypatch.setattr(run_cmd, "execute_line", execute)
    return calls


def _write(*, profile: str | None, auth: str | None) -> None:
    store = journal.FileJournal(journal.journal_dir())
    begin: dict[str, Any] = {
        "event": "begin",
        "inv": "a",
        "group": "g1",
        "command": "dataset.trash",
        "ts": "t",
        "profile": profile,
    }
    if auth is not None:
        begin["auth"] = auth
    store.append(begin)
    store.append({"event": "end", "inv": "a", "exit": 0, "undo": _UNDO})


def _undo() -> tuple[int, dict[str, Any]]:
    result = make_runner()._runner.invoke(app, ["history", "undo", "a", "--yes", "-o", "json"])
    text = result.stdout.strip() or result.stderr.strip()
    return result.exit_code, json.loads(text.splitlines()[-1])


def test_a_write_by_a_stored_profile_is_undone_by_that_profile(ran: list[list[str]]) -> None:
    _write(profile="alpha", auth=journal.AUTH_PROFILE)
    code, envelope = _undo()
    assert code == 0, envelope
    assert "--profile=alpha" in ran[0]


def test_a_write_by_the_env_token_is_refused_when_none_is_set_now(
    ran: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(profile="default", auth=journal.AUTH_ENV)
    monkeypatch.delenv(API_TOKEN_ENV, raising=False)
    code, envelope = _undo()
    assert code != 0 and ran == []
    assert envelope["data"]["failed"]["code"] == "undo_needs_token"


def test_a_write_by_the_env_token_is_undone_when_one_is_set(
    ran: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(profile="default", auth=journal.AUTH_ENV)
    monkeypatch.setenv(API_TOKEN_ENV, "mm_abc")
    code, envelope = _undo()
    assert code == 0, envelope
    assert not any(arg.startswith("--profile") for arg in ran[0])


def test_an_entry_without_a_recorded_account_runs_as_before(ran: list[list[str]]) -> None:
    _write(profile="alpha", auth=None)
    code, _ = _undo()
    assert code == 0
    assert not any(arg.startswith("--profile") for arg in ran[0])


def test_the_begin_record_says_which_account_signed_in(monkeypatch: pytest.MonkeyPatch) -> None:
    store = journal.FileJournal(journal.journal_dir())
    interceptor = journal.journal_writes(store_for=lambda: store)

    def write(profile: str | None) -> None:
        invocation = Invocation(
            command_id="dataset.trash", output="json", project=9, profile=profile
        )
        invocation.positionals.update(dataset_id=5)
        request = Request(
            "dataset.trash", "json", lambda: ({}, {}), invocation=invocation, profile=profile
        )
        interceptor(request, lambda _r: Outcome(data={}, meta={}))

    monkeypatch.delenv(API_TOKEN_ENV, raising=False)
    write("alpha")
    monkeypatch.setenv(API_TOKEN_ENV, "mm_abc")
    write("alpha")
    write(None)
    begins = [r for r in store.records() if r.get("event") == "begin"]
    # An explicit profile outranks the token; with none named, the token signs in.
    assert [b["auth"] for b in begins] == [
        journal.AUTH_PROFILE,
        journal.AUTH_PROFILE,
        journal.AUTH_ENV,
    ]
