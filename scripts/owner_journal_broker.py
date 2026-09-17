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
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PROFILE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_OUTCOMES = frozenset({"succeeded", "failed", "outcome_unknown"})
_CONTROLLER_FLAGS = frozenset(
    {"--profile", "--project", "--input", "--yes", "--server-prefix", "--output", "--no-input"}
)
_SECRET_TEXT = re.compile(
    r"(?i)(api[_-]?(?:key|secret)|access[_-]?token|authorization|password|secret)"
    r"(\s*[:=]\s*)(?:\S+)"
)
_BEARER_TEXT = re.compile(r"(?i)\bBearer\s+\S+")
_PRE_DISPATCH_ERROR_CODES = frozenset(
    {
        "authentication_failed",
        "authorization_required",
        "confirmation_declined",
        "confirmation_required",
        "incomplete_environment_auth",
        "input_format_required",
        "invalid_argument",
        "invalid_arguments",
        "invalid_config_value",
        "invalid_input_document",
        "invalid_input_format",
        "invalid_workspace_id",
        "missing_argument",
        "missing_field",
        "profile_not_found",
        "project_required",
    }
)


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
    repeatable_operations: frozenset[str] = frozenset()

    def as_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "allowlist": sorted(self.allowlist),
            "repeatable_operations": sorted(self.repeatable_operations),
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


@dataclass(frozen=True)
class FrozenOperation:
    """One complete owner-approved command, with no agent-supplied arguments."""

    argv: tuple[str, ...]
    target: str
    resource: str
    budget: int
    input_path: Path | None = None
    input_sha256: str | None = None
    confirmation: bool = False


@dataclass(frozen=True)
class OwnerSubprocessPolicy:
    """Fixed executable, configuration, scope, and operation authority."""

    executable: Path
    executable_sha256: str
    profile: str
    config_home: Path
    agent_workspace: Path
    workspace_id: int
    project_id: int
    operations: Mapping[str, FrozenOperation]


def _path_is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _redact_text(value: str) -> str:
    value = _SECRET_TEXT.sub(r"\1\2<REDACTED>", value)
    return _BEARER_TEXT.sub("Bearer <REDACTED>", value)


class OwnerSubprocessSender:
    """Run only fixed owner commands with owner-only configuration.

    This adapter intentionally does not expose argv, environment, destination,
    or confirmation choices to an agent. The only accepted input is the
    journal's already scope-checked ``Invocation``.
    """

    def __init__(
        self,
        policy: OwnerSubprocessPolicy,
        *,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
    ) -> None:
        self.policy = policy
        self._runner = runner
        self._validate_policy()

    def _validate_policy(self) -> None:
        executable = self.policy.executable.resolve()
        config_home = self.policy.config_home.resolve()
        workspace = self.policy.agent_workspace.resolve()
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise BrokerPolicyError("owner executable must be an executable regular file")
        if not _HEX_SHA256.fullmatch(self.policy.executable_sha256):
            raise BrokerPolicyError("owner executable hash must be a lowercase SHA-256 digest")
        if _sha256_bytes(executable.read_bytes()) != self.policy.executable_sha256:
            raise BrokerPolicyError("owner executable does not match frozen artifact hash")
        if not _PROFILE_NAME.fullmatch(self.policy.profile) or not config_home.is_dir():
            raise BrokerPolicyError("owner profile and configuration directory are required")
        if _path_is_within(config_home, workspace):
            raise BrokerPolicyError("owner configuration must be outside the agent workspace")
        config_details = config_home.stat()
        if config_details.st_uid != os.geteuid() or stat.S_IMODE(config_details.st_mode) & 0o077:
            raise BrokerPolicyError("owner configuration must be private and owner-controlled")
        if self.policy.workspace_id <= 0 or self.policy.project_id <= 0:
            raise BrokerPolicyError("owner subprocess scope must be positive and fixed")
        if not self.policy.operations:
            raise BrokerPolicyError("owner subprocess operation allowlist is required")
        for name, operation in self.policy.operations.items():
            if not name or not operation.argv or not operation.target or not operation.resource:
                raise BrokerPolicyError("each frozen operation needs command, target, and resource")
            if operation.budget <= 0:
                raise BrokerPolicyError("each frozen operation needs a positive fixed budget")
            if any(
                token in _CONTROLLER_FLAGS
                or any(token.startswith(flag + "=") for flag in _CONTROLLER_FLAGS)
                or "\x00" in token
                or "\n" in token
                or "://" in token
                for token in operation.argv
            ):
                raise BrokerPolicyError("frozen operation contains an agent-bypass argument")
            self._validate_input(operation, workspace)

    @staticmethod
    def _validate_input(operation: FrozenOperation, workspace: Path) -> None:
        if operation.input_path is None:
            if operation.input_sha256 is not None:
                raise BrokerPolicyError("input digest requires a fixed input path")
            return
        input_path = operation.input_path.resolve()
        if (
            operation.input_sha256 is None
            or not _HEX_SHA256.fullmatch(operation.input_sha256)
            or not input_path.is_file()
            or _path_is_within(input_path, workspace)
        ):
            raise BrokerPolicyError("fixed input must be a hashed file outside the agent workspace")
        details = input_path.stat()
        if details.st_uid != os.geteuid() or stat.S_IMODE(details.st_mode) & 0o077:
            raise BrokerPolicyError("fixed input must be private and owner-controlled")
        if _sha256_bytes(input_path.read_bytes()) != operation.input_sha256:
            raise BrokerPolicyError("fixed input does not match its approved digest")

    def send(self, invocation: Invocation) -> Mapping[str, object]:
        """Execute one frozen command and return redacted process observation."""
        operation = self.policy.operations.get(invocation.operation)
        if operation is None:
            raise BrokerPolicyError("operation is outside the owner subprocess allowlist")
        if (invocation.workspace_id, invocation.project_id) != (
            self.policy.workspace_id,
            self.policy.project_id,
        ):
            raise BrokerPolicyError("subprocess invocation scope differs from fixed owner scope")
        executable = self.policy.executable.resolve()
        if _sha256_bytes(executable.read_bytes()) != self.policy.executable_sha256:
            raise BrokerPolicyError("owner executable changed after policy approval")
        self._validate_input(operation, self.policy.agent_workspace.resolve())
        command = [
            str(executable),
            *operation.argv,
            "--profile",
            self.policy.profile,
            "--project",
            str(self.policy.project_id),
            "--output",
            "json",
            "--no-input",
        ]
        if operation.input_path is not None:
            command.extend(("--input", str(operation.input_path.resolve())))
        if operation.confirmation:
            command.append("--yes")
        environment = {
            "PATH": "/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(self.policy.config_home.resolve()),
            "MAMMOTH_OWNER_BROKER": "1",
        }
        try:
            completed = self._runner(
                command,
                check=False,
                capture_output=True,
                env=environment,
                timeout=operation.budget,
            )
        except subprocess.TimeoutExpired as error:
            stdout = _redact_text(_as_text(error.stdout))
            stderr = _redact_text(_as_text(error.stderr))
            return {
                "ok": False,
                "exit_status": None,
                "stdout": stdout,
                "stderr": stderr,
                "outcome": "outcome_unknown",
                "handle": None,
            }
        private_stdout = _as_text(completed.stdout)
        private_stderr = _as_text(completed.stderr)
        outcome = _subprocess_outcome(completed.returncode, private_stdout, private_stderr)
        stdout = _redact_text(private_stdout)
        stderr = _redact_text(private_stderr)
        return {
            "ok": completed.returncode == 0,
            "exit_status": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "outcome": outcome,
            "handle": None,
        }


def _as_text(value: bytes | str | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _subprocess_outcome(exit_status: int, stdout: str, stderr: str) -> str:
    """Preserve CLI ambiguity instead of guessing a failed mutation was harmless."""
    if exit_status == 0:
        return "succeeded"
    if exit_status == 7:
        return "outcome_unknown"
    definite_failure = False
    for body in (stdout, stderr):
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError:
            continue
        if _has_unknown_outcome(envelope):
            return "outcome_unknown"
        definite_failure = definite_failure or _has_definite_failure(envelope)
    return "failed" if definite_failure else "outcome_unknown"


def _has_unknown_outcome(value: object) -> bool:
    if isinstance(value, dict):
        if (
            value.get("operation_state") == "outcome_unknown"
            or value.get("code") == "outcome_unknown"
        ):
            return True
        return any(_has_unknown_outcome(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_unknown_outcome(item) for item in value)
    return False


def _has_definite_failure(value: object) -> bool:
    if isinstance(value, dict):
        if value.get("operation_state") in {"failed", "not_started"}:
            return True
        if value.get("code") in _PRE_DISPATCH_ERROR_CODES or value.get("status") == 403:
            return True
        return any(_has_definite_failure(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_definite_failure(item) for item in value)
    return False


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
        if not policy.repeatable_operations <= policy.allowlist:
            raise BrokerPolicyError("repeatable operations must be within the owner allowlist")
        requested_root = Path(root)
        if requested_root.exists():
            self.root = requested_root.resolve()
            details = self.root.stat()
            if not self.root.is_dir() or details.st_uid != os.geteuid():
                raise BrokerPolicyError("journal root must be an owner-controlled directory")
            if stat.S_IMODE(details.st_mode) & 0o077:
                raise BrokerPolicyError(
                    "existing journal root must not be group or world accessible"
                )
        else:
            self.root = requested_root.resolve()
            self.root.mkdir(mode=0o700, parents=True)
            self.root.chmod(0o700)
            self._fsync_directory(self.root.parent)
        self.policy = policy
        self._policy_path = self.root / "policy.json"
        self._journal_path = self.root / "journal.jsonl"
        self._lock_path = self.root / "journal.lock"
        self._policy_digest = _sha256(policy.as_dict())
        self._install_or_verify_policy()

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        """Persist a new directory entry on Linux filesystems that support it."""
        if sys.platform != "linux":
            return
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

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
        self._fsync_directory(self.root)

    def _append(self, event: dict[str, object]) -> None:
        encoded = _canonical(event) + b"\n"
        created = not self._journal_path.exists()
        descriptor = os.open(self._journal_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if created:
            self._fsync_directory(self.root)

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
        intent = invocation.as_dict()
        intent_records = [event for event in prior if event.get("event") == "intent"]
        if intent_records and any(
            event.get("policy_sha256") != self._policy_digest
            or any(event.get(key) != value for key, value in intent.items())
            for event in intent_records
        ):
            raise BrokerPolicyError(
                "intent_id is already bound to a different immutable invocation"
            )
        if invocation.operation not in self.policy.repeatable_operations and any(
            event.get("event") == "intent"
            and event.get("operation") == invocation.operation
            and event.get("intent_id") != invocation.intent_id
            for event in self._events()
        ):
            raise BrokerPolicyError(
                "one-shot operation was already dispatched under a different intent_id"
            )
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
