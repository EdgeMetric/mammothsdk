"""Usage events: the spool a command writes and the detached process that sends it."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
import typer

from mammoth_cli import __version__
from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import embedded, executor, runlog, trace, usage, usage_sender
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.sdk_service import SdkMammothService

SECRET_ARG = "customer-secret-value"
AUTH = ResolvedAuth(None, None, 42, "https://app.mammoth.io/api/v2", api_token="mm_x")


@pytest.fixture(autouse=True)
def usage_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn recording on; the suite turns it off for every other test."""
    monkeypatch.delenv(usage.DISABLE_ENV)
    monkeypatch.delenv("MAMMOTH_API_TOKEN", raising=False)


@pytest.fixture
def spawned(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record sender starts instead of starting a process."""
    calls: list[dict[str, Any]] = []

    def fake_popen(argv: list[str], **kwargs: Any) -> None:
        calls.append({"argv": argv, **kwargs})

    monkeypatch.setattr(usage.subprocess, "Popen", fake_popen)
    return calls


def _spool() -> Path:
    return runlog.log_dir() / "usage" / "pending.jsonl"


def _lines() -> list[dict[str, Any]]:
    return [json.loads(line) for line in _spool().read_text().splitlines()]


def _record(invocation: Invocation | None = None, command_id: str = "view.data.get") -> None:
    with trace.begin(command_id):
        usage.record(
            invocation or Invocation(command_id=command_id, profile="work"),
            exit_status=0,
            error_code=None,
            duration_ms=12,
        )


class _Service:
    """Stands in for the SDK service: takes events until told to fail."""

    sent: list[dict[str, Any]]
    fail_after: int | None = None
    closed = 0

    def __init__(self, auth: ResolvedAuth, *, timeout: float) -> None:
        self.auth = auth

    def send_user_event(self, event: dict[str, Any]) -> None:
        if _Service.fail_after is not None and len(_Service.sent) >= _Service.fail_after:
            raise OSError("no route")
        _Service.sent.append(event)

    def close(self) -> None:
        _Service.closed += 1


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> type[_Service]:
    """Send through :class:`_Service`, signed in as ``AUTH``."""
    _Service.sent = []
    _Service.fail_after = None
    _Service.closed = 0
    monkeypatch.setattr(usage_sender, "SdkMammothService", _Service)
    monkeypatch.setattr(usage_sender, "resolve_auth", lambda invocation: AUTH)
    return _Service


def test_a_line_holds_only_named_fields_and_never_an_argument() -> None:
    invocation = Invocation(
        command_id="view.data.get",
        profile="work",
        positionals={"name": SECRET_ARG},
        extra_args=[SECRET_ARG],
    )
    _record(invocation)

    assert SECRET_ARG not in _spool().read_text()
    line = _lines()[0]
    assert set(line) == {
        "ts",
        "cmd",
        "inv",
        "group",
        "surface",
        "agent",
        "exit_status",
        "error_code",
        "duration_ms",
        "cli_version",
        "profile",
        "profile_is_default",
        "env_key",
    }
    assert line["cmd"] == "view.data.get"
    assert line["cli_version"] == __version__


def test_nothing_is_recorded_when_embedded(
    monkeypatch: pytest.MonkeyPatch, spawned: list[dict[str, Any]]
) -> None:
    monkeypatch.setattr(embedded, "active", lambda: True)
    _record()
    usage.send_in_background()
    assert not _spool().exists()
    assert spawned == []


def test_the_switch_stops_recording_and_sending(
    monkeypatch: pytest.MonkeyPatch, spawned: list[dict[str, Any]]
) -> None:
    monkeypatch.setenv(usage.DISABLE_ENV, "1")
    _record()
    usage.send_in_background()
    assert not _spool().exists()
    assert spawned == []


def test_a_full_spool_takes_no_more_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(usage, "MAX_SPOOL_BYTES", 1)
    _record()
    _record()
    assert len(_lines()) == 1


def test_a_failed_write_never_reaches_the_command(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_disk(*args: Any, **kwargs: Any) -> None:
        raise OSError("read-only file system")

    monkeypatch.setattr(usage, "open", no_disk, raising=False)
    _record()


def test_the_sender_is_detached_and_does_not_inherit_stdio(
    spawned: list[dict[str, Any]],
) -> None:
    _record()
    usage.send_in_background()
    assert len(spawned) == 1
    call = spawned[0]
    assert call["argv"][1:] == ["-m", "mammoth_cli.runtime.usage_sender"]
    assert call["start_new_session"] is True
    assert call["close_fds"] is True
    for stream in ("stdin", "stdout", "stderr"):
        assert call[stream] == subprocess.DEVNULL


def test_nothing_waiting_starts_no_sender(spawned: list[dict[str, Any]]) -> None:
    usage.send_in_background()
    assert spawned == []


def test_one_sender_at_a_time_until_it_exits(spawned: list[dict[str, Any]]) -> None:
    _record()
    usage.send_in_background()
    usage.send_in_background()
    assert len(spawned) == 1
    usage.release_lock()
    usage.send_in_background()
    assert len(spawned) == 2


def test_a_crashed_senders_lock_expires(spawned: list[dict[str, Any]]) -> None:
    _record()
    usage.send_in_background()
    stale = time.time() - usage.LOCK_TTL_SECONDS - 1
    os.utime(_spool().parent / "sender.lock", (stale, stale))
    usage.send_in_background()
    assert len(spawned) == 2


def test_a_failed_start_leaves_the_lock_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def cannot_start(*args: Any, **kwargs: Any) -> None:
        raise OSError("no such interpreter")

    monkeypatch.setattr(usage.subprocess, "Popen", cannot_start)
    _record()
    usage.send_in_background()
    assert not (_spool().parent / "sender.lock").exists()


def test_a_second_claim_finds_nothing() -> None:
    _record()
    assert len(usage.take()) == 1
    assert usage.take() == []


def test_a_crashed_senders_claim_is_taken_over() -> None:
    _record()
    orphan = _spool().parent / "sending-1.jsonl"
    _spool().rename(orphan)
    assert usage.take() == []
    stale = time.time() - usage.LOCK_TTL_SECONDS - 1
    os.utime(orphan, (stale, stale))
    assert len(usage.take()) == 1
    assert not orphan.exists()


def test_an_unreadable_line_is_dropped() -> None:
    _record()
    with _spool().open("a") as file:
        file.write("not json\n[1]\n")
    assert len(usage.take()) == 1


def test_a_delivered_event_keeps_the_time_the_command_ended(
    service: type[_Service],
) -> None:
    with trace.begin("view.data.get"):
        traced = trace.current()
        assert traced is not None
        usage.record(
            Invocation(command_id="view.data.get", profile="work"),
            exit_status=0,
            error_code=None,
            duration_ms=12,
        )
    finished = _lines()[0]["ts"]

    assert usage_sender.drain() is True

    event = service.sent[0]
    assert event["timestamp"] == finished
    assert event["event_name"] == "cli_command_run"
    assert event["event_origin"] == "cli"
    assert event["domain"] == "app.mammoth.io"
    assert event["device_info"] == f"mammoth-cli/{__version__}"
    assert event["session_identifier"] == traced.group
    assert event["additional_info"] == {
        "cmd": "view.data.get",
        "inv": traced.invocation_id,
        "surface": "terminal",
        "agent": traced.agent,
        "outcome": "ok",
        "exit_status": 0,
        "error_code": None,
        "duration_ms": 12,
    }
    assert service.closed == 1
    assert not _spool().exists()


def test_a_local_profile_name_never_leaves_the_machine(service: type[_Service]) -> None:
    _record(Invocation(command_id="project.list", profile="acme-private-profile"))
    usage_sender.drain()
    assert "acme-private-profile" not in json.dumps(service.sent)


@pytest.mark.parametrize(
    ("exit_status", "error_code", "outcome"),
    [(0, None, "ok"), (3, None, "failed"), (2, "usage_error", "failed")],
)
def test_the_outcome_follows_the_exit(
    service: type[_Service], exit_status: int, error_code: str | None, outcome: str
) -> None:
    with trace.begin("project.list"):
        usage.record(
            Invocation(command_id="project.list", profile="work"),
            exit_status=exit_status,
            error_code=error_code,
            duration_ms=1,
        )
    usage_sender.drain()
    assert service.sent[0]["additional_info"]["outcome"] == outcome


def test_undelivered_lines_stay_for_the_next_sender(service: type[_Service]) -> None:
    service.fail_after = 1
    for _ in range(3):
        _record()
    delivered = _lines()[0]["inv"]

    assert usage_sender.drain() is True

    assert [event["additional_info"]["inv"] for event in service.sent] == [delivered]
    assert len(_lines()) == 2
    service.fail_after = None
    assert usage_sender.drain() is True
    assert len(service.sent) == 3
    assert not _spool().exists()


def test_a_login_that_cannot_resolve_keeps_its_lines(
    service: type[_Service], monkeypatch: pytest.MonkeyPatch
) -> None:
    def signed_out(invocation: Invocation) -> ResolvedAuth:
        raise CliError(code="not_authenticated", message="sign in", exit_status=3)

    monkeypatch.setattr(usage_sender, "resolve_auth", signed_out)
    _record()
    assert usage_sender.drain() is False
    assert len(_lines()) == 1


def test_an_old_line_is_dropped(service: type[_Service]) -> None:
    _record()
    line = _lines()[0]
    line["ts"] -= usage_sender.MAX_AGE_SECONDS + 1
    _spool().write_text(json.dumps(line) + "\n")
    assert usage_sender.drain() is False
    assert service.sent == []
    assert not _spool().exists()


def test_one_drain_sends_at_most_a_batch(
    service: type[_Service], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(usage_sender, "MAX_BATCH", 2)
    for _ in range(3):
        _record()
    usage_sender.drain()
    assert len(service.sent) == 2
    assert len(_lines()) == 1


def test_each_login_sends_as_itself(
    service: type[_Service], monkeypatch: pytest.MonkeyPatch
) -> None:
    logins: list[str | None] = []

    def resolve(invocation: Invocation) -> ResolvedAuth:
        logins.append(invocation.profile)
        return AUTH

    monkeypatch.setattr(usage_sender, "resolve_auth", resolve)
    _record(Invocation(command_id="project.list", profile="a"))
    _record(Invocation(command_id="project.list", profile="b"))
    _record(Invocation(command_id="project.list", profile="a"))
    usage_sender.drain()
    assert sorted(logins, key=str) == ["a", "b"]
    assert len(service.sent) == 3


def test_an_event_is_never_sent_with_another_token(
    service: type[_Service], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAMMOTH_API_TOKEN", "mm_alice")
    _record(Invocation(command_id="project.list"))
    monkeypatch.setenv("MAMMOTH_API_TOKEN", "mm_bob")

    assert usage_sender.drain() is False
    assert service.sent == []
    assert len(_lines()) == 1

    monkeypatch.setenv("MAMMOTH_API_TOKEN", "mm_alice")
    assert usage_sender.drain() is True
    assert len(service.sent) == 1


def test_the_token_is_never_written_to_the_spool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_TOKEN", "mm_alice_secret")
    _record(Invocation(command_id="project.list"))
    assert "mm_alice_secret" not in _spool().read_text()


def test_the_sender_frees_the_lock_even_when_a_drain_fails(
    monkeypatch: pytest.MonkeyPatch, spawned: list[dict[str, Any]]
) -> None:
    def broken() -> bool:
        raise ValueError("bad line")

    monkeypatch.setattr(usage_sender, "WAIT_SECONDS", 0)
    monkeypatch.setattr(usage_sender, "drain", broken)
    _record()
    usage.send_in_background()
    with pytest.raises(ValueError, match="bad line"):
        usage_sender.main()
    assert not (_spool().parent / "sender.lock").exists()


def test_a_successful_command_is_spooled_and_starts_the_sender(
    spawned: list[dict[str, Any]],
) -> None:
    invocation = Invocation(command_id="project.list", profile="work")
    executor.run("project.list", "json", lambda: ([], {}), invocation=invocation, interceptors=())
    assert _lines()[0]["exit_status"] == 0
    assert _lines()[0]["error_code"] is None
    assert len(spawned) == 1


def test_a_failed_command_is_spooled_with_its_code(spawned: list[dict[str, Any]]) -> None:
    def fails() -> Any:
        raise CliError(code="not_found", message="no such project", exit_status=4)

    invocation = Invocation(command_id="project.get", profile="work")
    with pytest.raises(typer.Exit):
        executor.run("project.get", "json", fails, invocation=invocation, interceptors=())
    line = _lines()[0]
    assert line["error_code"] == "not_found"
    assert line["exit_status"] == 4
    assert len(spawned) == 1


def test_the_service_posts_the_encoded_event_to_this_workspace() -> None:
    calls: list[tuple[Any, ...]] = []

    class Client:
        def request_json(self, method: str, path: str, *, json: dict[str, Any]) -> None:
            calls.append((method, path, json))

    service = SdkMammothService.__new__(SdkMammothService)
    service._client = Client()
    service._workspace_id = 42

    service.send_user_event({"event_name": "cli_command_run"})

    method, path, body = calls[0]
    assert (method, path) == ("POST", "/workspaces/42/mm-ue")
    assert json.loads(base64.b64decode(body["encoded_data"])) == {"event_name": "cli_command_run"}
