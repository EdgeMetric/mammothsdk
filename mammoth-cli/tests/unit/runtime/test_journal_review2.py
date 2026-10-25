"""Defects a second independent review found in the journal and its undo lines (#318)."""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.output.normalize import REDACTED, normalize
from mammoth_cli.runtime import journal
from mammoth_cli.runtime.dispatch import Outcome, Request
from mammoth_cli.runtime.invocation import Invocation


def _request(command_id: str, *, session: str | None = None, **positionals: Any) -> Request:
    invocation = Invocation(command_id=command_id, output="json", project=9, session=session)
    invocation.positionals.update(positionals)
    return Request(command_id, "json", lambda: ({}, {}), invocation=invocation, profile="p")


def _success(**meta: Any) -> Outcome:
    return Outcome(data={}, meta=meta)


def test_a_confirm_target_inverse_carries_the_id_it_will_confirm() -> None:
    lines, _ = journal.compensation(
        _request("support.partner.client.detach", partner_id=4, workspace_id=8),
        _success(),
        journal._Before(),
    )
    assert lines[0]["cmd"] == "support partner client cancel-detach"
    assert lines[0]["args"] == [4, 8] and lines[0]["flags"]["confirm"] == "8"


def test_an_inverse_carries_the_session_the_write_was_made_with() -> None:
    lines, _ = journal.compensation(
        _request("agent.run.pause", session="sess-1", run_id="r1"), _success(), journal._Before()
    )
    assert lines[0]["flags"]["session"] == "sess-1"


def test_the_fingerprint_is_the_same_for_the_raw_tasks_and_the_redacted_envelope() -> None:
    raw = [
        {
            "id": 1,
            "type": "REST_FILL",
            "params": {"url": "https://x", "auth": {"token": "t0p"}, "api_token": "abc"},
        }
    ]
    shown = json.loads(json.dumps(normalize(raw)))
    assert shown[0]["params"]["auth"] == REDACTED
    assert journal.fingerprint(raw) == journal.fingerprint(shown)


def test_an_inverse_that_needs_input_the_write_did_not_have_is_manual() -> None:
    lines, reason = journal.compensation(
        _request("support.partner.client.cancel-detach", partner_id=4, workspace_id=8),
        _success(),
        journal._Before(),
    )
    assert lines == []
    assert reason is not None and "price" in reason and "support partner client detach" in reason
