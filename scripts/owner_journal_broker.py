"""Owner-side durable invocation journal; deliberately separate from the CLI.

The broker records intent before handing an already-authorized operation to an
owner-supplied transport callback. It stores neither credentials nor request
payloads: callers provide a SHA-256 payload digest only. A journaled intent
without a receipt is an ambiguity requiring reconciliation, never an automatic
replay. This provides at-most-one broker dispatch per intent id, not exactly-
once backend execution.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OUTCOMES = frozenset({"succeeded", "failed", "outcome_unknown"})


class BrokerPolicyError(ValueError):
    """Raised when an agent-provided invocation exceeds fixed owner policy."""


class ReconciliationRequiredError(RuntimeError):
    """Raised when a prior dispatch may have happened but lacks a receipt."""


class InjectedCrashError(RuntimeError):
    """Test-only failure injected at a durable boundary."""


@dataclass(frozen=True)
class OwnerPolicy:
    """Immutable authority boundary selected by the owner, never the agent."""

    workspace_id: int
    project_id: int
    allowlist: frozenset[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "allowlist": sorted(self.allowlist),
        }


@dataclass(frozen=True)
class Invocation:
    """Secret-free intent received from an untrusted agent boundary."""

    intent_id: str
    operation: str
    workspace_id: int
    project_id: int
    payload_sha256: str

    def as_dict(self) -> dict[str, str | int]:
        return {
            "intent_id": self.intent_id,
            "operation": self.operation,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True)
class Receipt:
    intent_id: str
    outcome: str
    handle: str | None


Sender = Callable[[Invocation], Mapping[str, object]]


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


class OwnerJournalBroker:
    """Append-only, fsynced owner journal with fail-closed replay semantics."""

    def __init__(self, root: Path, policy: OwnerPolicy) -> None:
        if policy.workspace_id <= 0 or policy.project_id <= 0 or not policy.allowlist:
            raise BrokerPolicyError(
                "policy requires positive fixed scope and a non-empty allowlist"
            )
        self.root = Path(root).resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.policy = policy
        self._policy_path = self.root / "policy.json"
        self._journal_path = self.root / "journal.jsonl"
        self._lock_path = self.root / "journal.lock"
        self._policy_digest = _sha256(policy.as_dict())
        self._install_or_verify_policy()

    def _install_or_verify_policy(self) -> None:
        encoded = (
            _canonical({"policy": self.policy.as_dict(), "sha256": self._policy_digest}) + b"\n"
        )
        try:
            descriptor = os.open(self._policy_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            existing = json.loads(self._policy_path.read_text(encoding="utf-8"))
            if existing != json.loads(encoded):
                raise BrokerPolicyError(
                    "existing journal policy differs from requested owner policy"
                ) from None
            return
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())

    def _append(self, event: dict[str, object]) -> None:
        encoded = _canonical(event) + b"\n"
        descriptor = os.open(self._journal_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())

    def _events(self) -> list[dict[str, object]]:
        if not self._journal_path.exists():
            return []
        events: list[dict[str, object]] = []
        for line in self._journal_path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if not isinstance(event, dict):
                raise RuntimeError("journal contains a non-object event")
            events.append(event)
        return events

    def _validate(self, invocation: Invocation) -> None:
        if not invocation.intent_id or not invocation.operation:
            raise BrokerPolicyError("intent_id and operation are required")
        if not _HEX_SHA256.fullmatch(invocation.payload_sha256):
            raise BrokerPolicyError("payload_sha256 must be a lowercase SHA-256 digest")
        if invocation.operation not in self.policy.allowlist:
            raise BrokerPolicyError("operation is outside the immutable owner allowlist")
        if (invocation.workspace_id, invocation.project_id) != (
            self.policy.workspace_id,
            self.policy.project_id,
        ):
            raise BrokerPolicyError("invocation scope differs from immutable owner scope")

    def submit(
        self,
        invocation: Invocation,
        sender: Sender,
        *,
        fault: str | None = None,
    ) -> Receipt:
        """Journal intent, dispatch once, then append a receipt when observed.

        ``fault`` exists solely for offline boundary tests. In production no
        fault value is passed. A crash after intent is durable but before a
        receipt intentionally blocks re-dispatch pending independent recovery.
        """
        descriptor = os.open(self._lock_path, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(descriptor, "wb") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                return self._submit_locked(invocation, sender, fault=fault)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _submit_locked(
        self,
        invocation: Invocation,
        sender: Sender,
        *,
        fault: str | None,
    ) -> Receipt:
        """Perform one serialized journal transaction while holding the owner lock."""
        self._validate(invocation)
        prior = [
            event for event in self._events() if event.get("intent_id") == invocation.intent_id
        ]
        for event in prior:
            if event.get("event") == "receipt":
                return Receipt(
                    intent_id=invocation.intent_id,
                    outcome=str(event["outcome"]),
                    handle=str(event["handle"]) if event.get("handle") is not None else None,
                )
        if prior:
            raise ReconciliationRequiredError(
                "intent is durable but has no receipt; reconcile before retry"
            )

        self._append(
            {
                "version": 1,
                "event": "intent",
                "policy_sha256": self._policy_digest,
                **invocation.as_dict(),
            }
        )
        if fault == "after_intent_before_send":
            raise InjectedCrashError("injected crash after durable intent")

        response = sender(invocation)
        outcome = response.get("outcome")
        handle = response.get("handle")
        if outcome not in _OUTCOMES or (handle is not None and not isinstance(handle, (str, int))):
            raise RuntimeError("sender returned an invalid secret-free receipt")
        if fault == "after_commit_before_receipt":
            raise InjectedCrashError("injected crash after sender returned")

        receipt = Receipt(
            invocation.intent_id,
            str(outcome),
            str(handle) if handle is not None else None,
        )
        self._append(
            {
                "version": 1,
                "event": "receipt",
                "policy_sha256": self._policy_digest,
                "intent_id": receipt.intent_id,
                "outcome": receipt.outcome,
                "handle": receipt.handle,
            }
        )
        return receipt
