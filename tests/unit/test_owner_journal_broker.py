"""Offline fault tests for the owner-side durable broker journal."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "owner_journal_broker.py"


@pytest.fixture()
def broker_module():
    spec = importlib.util.spec_from_file_location("owner_journal_broker", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _inv(module, intent_id: str = "intent-1"):
    return module.Invocation(
        intent_id=intent_id,
        operation="dataset.create",
        workspace_id=7,
        project_id=9,
        payload_sha256="a" * 64,
    )


def _broker(module, path: Path):
    return module.OwnerJournalBroker(
        path,
        module.OwnerPolicy(
            workspace_id=7,
            project_id=9,
            allowlist=frozenset({"dataset.create"}),
        ),
    )


def test_journal_receipt_is_atomic_and_repeat_does_not_redispatch(
    broker_module, tmp_path: Path
) -> None:
    broker = _broker(broker_module, tmp_path / "owner-only")
    calls: list[str] = []

    def sender(invocation):
        calls.append(invocation.intent_id)
        return {"outcome": "succeeded", "handle": "job-44"}

    receipt = broker.submit(_inv(broker_module), sender)
    repeated = broker.submit(_inv(broker_module), sender)

    assert receipt == repeated
    assert calls == ["intent-1"]
    events = [
        json.loads(line)
        for line in (tmp_path / "owner-only" / "journal.jsonl").read_text().splitlines()
    ]
    assert [event["event"] for event in events] == ["intent", "receipt"]
    assert set(events[0]).isdisjoint({"payload", "credentials", "authorization", "api_key"})
    assert events[0]["payload_sha256"] == "a" * 64


@pytest.mark.parametrize("fault", ["after_intent_before_send", "after_commit_before_receipt"])
def test_crash_boundaries_never_automatically_replay(
    broker_module, tmp_path: Path, fault: str
) -> None:
    broker = _broker(broker_module, tmp_path / fault)
    calls: list[str] = []

    def sender(invocation):
        calls.append(invocation.intent_id)
        return {"outcome": "succeeded", "handle": "job-44"}

    with pytest.raises(broker_module.InjectedCrashError):
        broker.submit(_inv(broker_module), sender, fault=fault)
    assert calls == ([] if fault == "after_intent_before_send" else ["intent-1"])
    with pytest.raises(broker_module.ReconciliationRequiredError):
        broker.submit(_inv(broker_module), sender)
    assert calls == ([] if fault == "after_intent_before_send" else ["intent-1"])


def test_scope_allowlist_and_policy_replacement_fail_closed(broker_module, tmp_path: Path) -> None:
    root = tmp_path / "owner-only"
    broker = _broker(broker_module, root)
    bad_scope = broker_module.Invocation("intent-2", "dataset.create", 7, 10, "b" * 64)
    forbidden = broker_module.Invocation("intent-3", "project.delete", 7, 9, "b" * 64)

    with pytest.raises(broker_module.BrokerPolicyError):
        broker.submit(bad_scope, lambda _: {"outcome": "succeeded"})
    with pytest.raises(broker_module.BrokerPolicyError):
        broker.submit(forbidden, lambda _: {"outcome": "succeeded"})
    with pytest.raises(broker_module.BrokerPolicyError):
        broker_module.OwnerJournalBroker(
            root,
            broker_module.OwnerPolicy(
                workspace_id=7,
                project_id=10,
                allowlist=frozenset({"dataset.create"}),
            ),
        )
