"""Offline fault tests for the owner-side durable broker journal."""

from __future__ import annotations

import importlib.util
import json
import socket
import sys
import threading
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


def _broker(
    module,
    path: Path,
    *,
    allowlist: frozenset[str] | None = None,
    repeatable_operations: frozenset[str] = frozenset(),
):
    return module.OwnerJournalBroker(
        path,
        module.OwnerPolicy(
            workspace_id=7,
            project_id=9,
            allowlist=allowlist or frozenset({"dataset.create"}),
            repeatable_operations=repeatable_operations,
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
    broker = _broker(broker_module, tmp_path / fault)
    with pytest.raises(broker_module.ReconciliationRequiredError):
        broker.submit(_inv(broker_module), sender)
    assert calls == ([] if fault == "after_intent_before_send" else ["intent-1"])


def test_same_id_with_changed_fingerprint_is_rejected(broker_module, tmp_path: Path) -> None:
    broker = _broker(
        broker_module,
        tmp_path / "owner-only",
        allowlist=frozenset({"dataset.create", "dataset.update"}),
    )

    def sender(_):
        return {"outcome": "succeeded", "handle": "job-44"}

    broker.submit(_inv(broker_module), sender)

    changed_payload = broker_module.Invocation("intent-1", "dataset.create", 7, 9, "b" * 64)
    changed_operation = broker_module.Invocation("intent-1", "dataset.update", 7, 9, "a" * 64)
    for invocation in (changed_payload, changed_operation):
        with pytest.raises(broker_module.BrokerPolicyError, match="different immutable invocation"):
            broker.submit(invocation, sender)


def test_one_shot_operations_reject_new_agent_intent_ids(broker_module, tmp_path: Path) -> None:
    calls: list[str] = []

    def sender(invocation):
        calls.append(invocation.intent_id)
        return {"outcome": "succeeded"}

    broker = _broker(broker_module, tmp_path / "one-shot")
    broker.submit(_inv(broker_module, "intent-1"), sender)
    with pytest.raises(broker_module.BrokerPolicyError, match="one-shot operation"):
        broker.submit(_inv(broker_module, "agent-retry"), sender)
    assert calls == ["intent-1"]

    repeatable = _broker(
        broker_module,
        tmp_path / "repeatable-read",
        repeatable_operations=frozenset({"dataset.create"}),
    )
    repeatable.submit(_inv(broker_module, "intent-1"), sender)
    repeatable.submit(_inv(broker_module, "agent-retry"), sender)
    assert calls == ["intent-1", "intent-1", "agent-retry"]


def test_existing_insecure_root_is_not_repermissioned(broker_module, tmp_path: Path) -> None:
    root = tmp_path / "existing-root"
    root.mkdir(mode=0o700)
    root.chmod(0o755)

    with pytest.raises(broker_module.BrokerPolicyError, match="must not be group"):
        _broker(broker_module, root)
    assert root.stat().st_mode & 0o777 == 0o755


def _subprocess_policy(module, tmp_path: Path, operation):
    workspace = tmp_path / "agent-workspace"
    workspace.mkdir()
    config_home = tmp_path / "owner-config"
    config_home.mkdir()
    config_home.chmod(0o700)
    executable = tmp_path / "owner-mammoth"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    return module.OwnerSubprocessPolicy(
        executable=executable,
        executable_sha256=module._sha256_bytes(executable.read_bytes()),
        profile="owner-profile",
        config_home=config_home,
        agent_workspace=workspace,
        workspace_id=7,
        project_id=9,
        operations={"dataset.create": operation},
    )


def test_owner_sender_constructs_fixed_redacted_subprocess(broker_module, tmp_path: Path) -> None:
    owner_input = tmp_path / "owner-input.json"
    owner_input.write_text("{}", encoding="utf-8")
    owner_input.chmod(0o600)
    operation = broker_module.FrozenOperation(
        argv=("dataset", "create"),
        target="dataset-44",
        resource="dataset",
        budget=30,
        input_path=owner_input,
        input_sha256=broker_module._sha256_bytes(owner_input.read_bytes()),
        confirmation=True,
    )
    observed: dict[str, object] = {}

    def runner(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return broker_module.subprocess.CompletedProcess(
            command,
            0,
            stdout=b"Bearer token-value",
            stderr=b"api_key=not-recorded",
        )

    sender = broker_module.OwnerSubprocessSender(
        _subprocess_policy(broker_module, tmp_path, operation), runner=runner
    )
    result = sender.send(_inv(broker_module))

    assert result == {
        "ok": True,
        "exit_status": 0,
        "stdout": "Bearer <REDACTED>",
        "stderr": "api_key=<REDACTED>",
        "outcome": "succeeded",
        "handle": None,
    }
    command = observed["command"]
    assert command[0].endswith("owner-mammoth")
    assert command[command.index("--profile") + 1] == "owner-profile"
    assert command[command.index("--project") + 1] == "9"
    assert command[command.index("--input") + 1] == str(owner_input)
    assert command[-1] == "--yes"
    assert observed["kwargs"]["env"] == {
        "PATH": "/usr/bin:/bin",
        "XDG_CONFIG_HOME": str((tmp_path / "owner-config").resolve()),
        "MAMMOTH_OWNER_BROKER": "1",
    }
    injected_operation = broker_module.Invocation(
        "intent-2",
        "dataset.create --yes",
        7,
        9,
        "a" * 64,
    )
    with pytest.raises(broker_module.BrokerPolicyError, match="subprocess allowlist"):
        sender.send(injected_operation)


def test_fixed_input_must_remain_private_and_digest_bound(broker_module, tmp_path: Path) -> None:
    owner_input = tmp_path / "owner-input.json"
    owner_input.write_text("{}", encoding="utf-8")
    owner_input.chmod(0o600)
    operation = broker_module.FrozenOperation(
        argv=("dataset", "create"),
        target="dataset-44",
        resource="dataset",
        budget=30,
        input_path=owner_input,
        input_sha256=broker_module._sha256_bytes(owner_input.read_bytes()),
    )
    sender = broker_module.OwnerSubprocessSender(
        _subprocess_policy(broker_module, tmp_path, operation)
    )
    owner_input.write_text('{"changed":true}', encoding="utf-8")

    with pytest.raises(broker_module.BrokerPolicyError, match="approved digest"):
        sender.send(_inv(broker_module))


@pytest.mark.parametrize(
    "exit_status,stderr",
    [
        (7, b"not JSON"),
        (1, b'{"error":{"code":"outcome_unknown"}}'),
    ],
)
def test_sender_preserves_structured_or_retryable_unknown_outcomes(
    broker_module, tmp_path: Path, exit_status: int, stderr: bytes
) -> None:
    operation = broker_module.FrozenOperation(
        argv=("dataset", "create"), target="dataset-44", resource="dataset", budget=30
    )

    def runner(command, **_kwargs):
        return broker_module.subprocess.CompletedProcess(
            command, exit_status, stdout=b"", stderr=stderr
        )

    sender = broker_module.OwnerSubprocessSender(
        _subprocess_policy(broker_module, tmp_path, operation), runner=runner
    )
    assert sender.send(_inv(broker_module))["outcome"] == "outcome_unknown"


@pytest.mark.parametrize(
    "exit_status,stderr",
    [
        (-9, b""),
        (1, b"garbled partial output"),
        (1, b""),
    ],
)
def test_sender_defaults_unparseable_nonzero_mutations_to_unknown(
    broker_module, tmp_path: Path, exit_status: int, stderr: bytes
) -> None:
    operation = broker_module.FrozenOperation(
        argv=("dataset", "create"), target="dataset-44", resource="dataset", budget=30
    )

    def runner(command, **_kwargs):
        return broker_module.subprocess.CompletedProcess(
            command, exit_status, stdout=b"", stderr=stderr
        )

    sender = broker_module.OwnerSubprocessSender(
        _subprocess_policy(broker_module, tmp_path, operation), runner=runner
    )
    assert sender.send(_inv(broker_module))["outcome"] == "outcome_unknown"


@pytest.mark.parametrize(
    "stderr",
    [
        b'{"error":{"status":403,"code":"authorization_required"}}',
        b'{"error":{"code":"invalid_argument"}}',
        b'{"error":{"details":{"operation_state":"not_started"}}}',
    ],
)
def test_sender_accepts_explicit_definite_failure_envelopes(
    broker_module, tmp_path: Path, stderr: bytes
) -> None:
    operation = broker_module.FrozenOperation(
        argv=("dataset", "create"), target="dataset-44", resource="dataset", budget=30
    )

    def runner(command, **_kwargs):
        return broker_module.subprocess.CompletedProcess(command, 1, stdout=b"", stderr=stderr)

    sender = broker_module.OwnerSubprocessSender(
        _subprocess_policy(broker_module, tmp_path, operation), runner=runner
    )
    assert sender.send(_inv(broker_module))["outcome"] == "failed"


def test_owner_sender_rechecks_frozen_artifact_before_execution(
    broker_module, tmp_path: Path
) -> None:
    operation = broker_module.FrozenOperation(
        argv=("dataset", "create"), target="dataset-44", resource="dataset", budget=30
    )
    policy = _subprocess_policy(broker_module, tmp_path, operation)
    sender = broker_module.OwnerSubprocessSender(policy)
    policy.executable.write_text("changed", encoding="utf-8")
    policy.executable.chmod(0o700)

    with pytest.raises(broker_module.BrokerPolicyError, match="changed after policy approval"):
        sender.send(_inv(broker_module))


def _socket_exchange(server, request: bytes) -> dict[str, object]:
    server_side, client_side = socket.socketpair()
    worker = threading.Thread(target=server._serve_connection, args=(server_side,))
    worker.start()
    try:
        client_side.sendall(request)
        received = client_side.recv(65536)
    finally:
        client_side.close()
    worker.join(timeout=1)
    assert not worker.is_alive()
    return json.loads(received)


def _socket_server(module, tmp_path: Path, sender, *, receive_timeout_seconds: float = 5.0):
    broker = _broker(module, tmp_path / "journal")
    return module.OwnerBrokerSocketServer(
        tmp_path / "owner-socket" / "broker.sock",
        trial_handle="trial_opaque_1",
        broker=broker,
        sender=sender,
        receive_timeout_seconds=receive_timeout_seconds,
    )


def test_owner_socket_binds_private_path_and_returns_redacted_receipt(
    broker_module, tmp_path: Path
) -> None:
    calls: list[str] = []

    def sender(invocation):
        calls.append(invocation.intent_id)
        return {
            "outcome": "outcome_unknown",
            "handle": "job-44",
            "ok": False,
            "exit_status": 7,
            "stdout": "Bearer raw-token",
            "stderr": "api_key=raw-key",
        }

    server = _socket_server(broker_module, tmp_path, sender)
    server.bind()
    try:
        assert server.path.stat().st_mode & 0o777 == 0o600
        request = {
            "trial_handle": "trial_opaque_1",
            "intent_id": "intent-1",
            "operation": "dataset.create",
            "payload_sha256": "a" * 64,
        }
        response = _socket_exchange(server, json.dumps(request).encode() + b"\n")
        assert response == {
            "ok": True,
            "request_accepted": True,
            "receipt": {"intent_id": "intent-1", "outcome": "outcome_unknown", "handle": "job-44"},
            "observation": {
                "ok": False,
                "exit_status": 7,
                "stdout": "Bearer <REDACTED>",
                "stdout_truncated": False,
                "stderr": "api_key=<REDACTED>",
                "stderr_truncated": False,
            },
        }
        repeated = _socket_exchange(server, json.dumps(request).encode() + b"\n")
        assert repeated["receipt"] == response["receipt"]
        assert "observation" not in repeated
        assert calls == ["intent-1"]
    finally:
        server.close()


def test_owner_socket_times_out_an_idle_client(broker_module, tmp_path: Path) -> None:
    server = _socket_server(
        broker_module,
        tmp_path,
        lambda _: {"outcome": "succeeded"},
        receive_timeout_seconds=0.01,
    )
    server_side, client_side = socket.socketpair()
    worker = threading.Thread(target=server._serve_connection, args=(server_side,))
    worker.start()
    try:
        assert json.loads(client_side.recv(65536)) == {"error": "request_denied", "ok": False}
    finally:
        client_side.close()
    worker.join(timeout=1)
    assert not worker.is_alive()


def test_owner_socket_marks_truncated_observation(broker_module, tmp_path: Path) -> None:
    server = _socket_server(
        broker_module,
        tmp_path,
        lambda _: {
            "outcome": "succeeded",
            "ok": True,
            "exit_status": 0,
            "stdout": "x" * (broker_module._MAX_OBSERVATION_CHARS + 1),
        },
    )
    request = {
        "trial_handle": "trial_opaque_1",
        "intent_id": "intent-1",
        "operation": "dataset.create",
        "payload_sha256": "a" * 64,
    }
    response = _socket_exchange(server, json.dumps(request).encode() + b"\n")
    observation = response["observation"]
    assert observation["stdout_truncated"] is True
    assert len(observation["stdout"]) == broker_module._MAX_OBSERVATION_CHARS


@pytest.mark.parametrize(
    "frame",
    [
        b"not-json\n",
        b'{"trial_handle":"trial_opaque_1","argv":["--profile","bad"]}\n',
        b"x" * (64 * 1024 + 2),
    ],
)
def test_owner_socket_rejects_malformed_oversize_and_argv_requests(
    broker_module, tmp_path: Path, frame: bytes
) -> None:
    server = _socket_server(
        broker_module,
        tmp_path,
        lambda _: {"outcome": "succeeded", "ok": True, "exit_status": 0},
    )
    assert _socket_exchange(server, frame) == {"error": "request_denied", "ok": False}


def test_owner_socket_rejects_policy_denial(broker_module, tmp_path: Path) -> None:
    server = _socket_server(
        broker_module,
        tmp_path,
        lambda _: {"outcome": "succeeded", "ok": True, "exit_status": 0},
    )
    request = {
        "trial_handle": "trial_opaque_1",
        "intent_id": "intent-1",
        "operation": "project.delete",
        "payload_sha256": "a" * 64,
    }
    assert _socket_exchange(server, json.dumps(request).encode() + b"\n") == {
        "error": "request_denied",
        "ok": False,
    }


def test_owner_socket_rejects_insecure_existing_socket_directory(
    broker_module, tmp_path: Path
) -> None:
    socket_dir = tmp_path / "insecure-socket"
    socket_dir.mkdir(mode=0o700)
    socket_dir.chmod(0o755)
    with pytest.raises(broker_module.BrokerPolicyError, match="socket directory"):
        broker_module.OwnerBrokerSocketServer(
            socket_dir / "broker.sock",
            trial_handle="trial_opaque_1",
            broker=_broker(broker_module, tmp_path / "journal"),
            sender=lambda _: {"outcome": "succeeded"},
        )


@pytest.mark.parametrize(
    "argv,input_in_workspace",
    [
        (("dataset", "create", "--profile", "agent"), False),
        (("dataset", "create", "--project", "99"), False),
        (("dataset", "create", "https://external.invalid"), False),
        (("dataset", "create", "--yes"), False),
        (("dataset", "create"), True),
    ],
)
def test_agent_injected_overrides_cannot_enter_owner_policy(
    broker_module, tmp_path: Path, argv: tuple[str, ...], input_in_workspace: bool
) -> None:
    workspace = tmp_path / "agent-workspace"
    injected_input = workspace / "injected.json" if input_in_workspace else None
    operation = broker_module.FrozenOperation(
        argv=argv,
        target="dataset-44",
        resource="dataset",
        budget=30,
        input_path=injected_input,
    )

    with pytest.raises(broker_module.BrokerPolicyError):
        broker_module.OwnerSubprocessSender(_subprocess_policy(broker_module, tmp_path, operation))


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
