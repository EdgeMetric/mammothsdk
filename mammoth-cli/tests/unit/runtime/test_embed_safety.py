"""Embedded calls under a host's thread pool: stray output, one envelope, lazy builds, exit."""

from __future__ import annotations

import sys
import threading
import time
from types import SimpleNamespace
from typing import Any

import pytest
import typer

from mammoth_cli import app as app_module
from mammoth_cli import embed
from mammoth_cli.commands.schema import _accepted_fields
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.embed import invoke
from mammoth_cli.errors.envelope import EXIT_AUTH, CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime import embedded, executor
from mammoth_cli.runtime.local_paths import local_path_commands
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.positionals import LOCAL_PATH
from mammoth_cli.services.testing import FakeMammothService

_LOGIN = ExplicitLogin(
    api_key=None, api_secret=None, api_token="jwt", server_prefix="box", headers={}
)


def _fake_run(monkeypatch: pytest.MonkeyPatch, body: Any) -> None:
    """Make ``invoke`` run ``body`` in place of the CLI."""
    monkeypatch.setattr(embed, "_run", lambda argv: body(argv))


# --- N5: exit status in the envelope ------------------------------------------------------


def test_success_envelope_carries_exit_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: FakeMammothService())
    monkeypatch.setattr("mammoth_cli.context.resolver.resolve_token_workspace", lambda *_args: 5)

    envelope = invoke(["project", "list"], login=_LOGIN)

    assert envelope["meta"]["exit"] == 0


def test_help_envelope_carries_exit_zero() -> None:
    assert invoke(["--version"], login=_LOGIN)["meta"]["exit"] == 0


def test_error_envelope_carries_the_exit_status() -> None:
    envelope = CliError(code="authentication_failed", message="x", exit_status=EXIT_AUTH)

    assert envelope.to_envelope()["error"]["exit"] == EXIT_AUTH


def test_usage_error_carries_exit_two() -> None:
    envelope = invoke(["project", "no-such-command"], login=_LOGIN)

    assert envelope["error"]["exit"] == 2


def test_executor_passes_the_verify_exit_to_the_envelope() -> None:
    call = embedded.EmbeddedCall(login=_LOGIN)
    token = embedded.enter(call)
    try:
        with pytest.raises(typer.Exit) as exit_info:
            executor.run("view.get", "json", lambda: ({"verify": {"outcome": "failed"}}, {}))
    finally:
        embedded.leave(token)

    assert exit_info.value.exit_code == 1
    assert call.envelopes[0]["meta"]["exit"] == 1


# --- N6: stray output ---------------------------------------------------------------------


def test_stray_stdout_is_returned_as_an_error_not_printed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def body(_argv: list[str]) -> None:
        print("oops " + "x" * 800)
        sys.stderr.write("warn\n")
        embedded.capture({"schema_version": 1, "data": {}, "meta": {"command": "x", "exit": 0}})

    _fake_run(monkeypatch, body)

    envelope = invoke(["project", "list"], login=_LOGIN)

    assert envelope["error"]["code"] == "stray_output"
    assert envelope["error"]["exit"] == 1
    assert envelope["error"]["details"]["stdout"].startswith("oops ")
    assert len(envelope["error"]["details"]["stdout"]) == 500
    assert envelope["error"]["details"]["stderr"] == "warn"
    assert capsys.readouterr() == ("", "")


def test_stderr_text_rides_on_a_success_envelope_and_does_not_fail_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import logging

    def body(_argv: list[str]) -> None:
        # No handler (and no propagation to pytest's): logging's last resort writes to
        # sys.stderr, looked up at call time.
        sdk_logger = logging.getLogger("mammoth.client.embed_test")
        sdk_logger.propagate = False
        sdk_logger.warning("sdk warns")
        embedded.capture({"schema_version": 1, "data": {}, "meta": {"command": "x", "exit": 0}})

    _fake_run(monkeypatch, body)

    envelope = invoke(["project", "list"], login=_LOGIN)

    assert "error" not in envelope
    assert "sdk warns" in envelope["meta"]["stderr"]
    assert capsys.readouterr() == ("", "")


def test_stderr_text_rides_on_an_error_envelope_in_details(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def body(_argv: list[str]) -> None:
        sys.stderr.write("x" * 800)
        embedded.capture(CliError(code="resource_not_found", message="gone").to_envelope())

    _fake_run(monkeypatch, body)

    envelope = invoke(["project", "list"], login=_LOGIN)

    assert envelope["error"]["code"] == "resource_not_found"
    assert envelope["error"]["details"]["stderr"] == "x" * 500
    assert capsys.readouterr() == ("", "")


def test_typer_echo_in_a_call_is_captured_as_text_and_never_raises(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def body(_argv: list[str]) -> None:
        typer.echo("out-line")
        typer.echo("err-line", err=True)
        sys.stdout.buffer.write(b"raw-bytes\n")
        embedded.capture({"schema_version": 1, "data": {}, "meta": {"command": "x", "exit": 0}})

    _fake_run(monkeypatch, body)

    envelope = invoke(["project", "list"], login=_LOGIN)

    assert envelope["error"]["code"] == "stray_output"
    assert envelope["error"]["details"]["stdout"] == "out-line\nraw-bytes"
    assert envelope["error"]["details"]["stderr"] == "err-line"
    assert capsys.readouterr() == ("", "")


def test_typer_echo_outside_a_call_still_reaches_the_real_stream(
    capsys: pytest.CaptureFixture[str],
) -> None:
    embedded.install_stream_guards()

    typer.echo("host-out")
    typer.echo("host-err", err=True)
    sys.stdout.buffer.write(b"host-bytes\n")
    sys.stdout.flush()

    out, err = capsys.readouterr()
    assert "host-out" in out
    assert "host-bytes" in out
    assert "host-err" in err


def test_the_guard_refuses_bytes_like_a_text_stream() -> None:
    embedded.install_stream_guards()

    with pytest.raises(TypeError):
        sys.stdout.write(b"x")  # type: ignore[arg-type]


def test_concurrent_calls_do_not_cross_capture_and_other_threads_still_print(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    both_inside = threading.Barrier(3, timeout=10)  # two calls and the bystander
    writes_done = threading.Barrier(3, timeout=10)

    def body(argv: list[str]) -> None:
        name = argv[0]
        both_inside.wait()
        for _ in range(50):
            print(f"stray-from-{name}")
            sys.stderr.write(f"err-from-{name}\n")
            time.sleep(0.001)
        writes_done.wait()

    _fake_run(monkeypatch, body)
    results: dict[str, dict[str, Any]] = {}

    def call(name: str) -> None:
        results[name] = invoke([name], login=_LOGIN)

    def bystander() -> None:
        # Not an embedded call: same process, other thread; the host's own output.
        both_inside.wait()
        for _ in range(50):
            print("host-line")
            time.sleep(0.001)
        writes_done.wait()

    threads = [threading.Thread(target=call, args=(name,)) for name in ("a", "b")]
    threads.append(threading.Thread(target=bystander))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)

    for name, other in (("a", "b"), ("b", "a")):
        details = results[name]["error"]["details"]
        assert details["stdout"].count(f"stray-from-{name}") > 0
        assert f"stray-from-{other}" not in details["stdout"]
        assert f"err-from-{other}" not in details["stderr"]
    out, err = capsys.readouterr()
    assert out.count("host-line") == 50
    assert "stray-from" not in out
    assert "err-from" not in err
    assert isinstance(sys.stdout, embedded._RoutedStream)


def test_install_is_idempotent_and_thread_safe() -> None:
    threads = [threading.Thread(target=embedded.install_stream_guards) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    stream = sys.stdout

    embedded.install_stream_guards()

    assert sys.stdout is stream
    assert isinstance(stream, embedded._RoutedStream)
    assert not isinstance(stream._real, embedded._RoutedStream)


# --- N7: one envelope ---------------------------------------------------------------------


def test_a_second_envelope_is_an_error_not_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    def body(_argv: list[str]) -> None:
        embedded.capture({"schema_version": 1, "data": {}, "meta": {"command": "x"}})
        embedded.capture(CliError(code="internal_error", message="late").to_envelope())

    _fake_run(monkeypatch, body)

    envelope = invoke(["project", "list"], login=_LOGIN)

    assert envelope["error"]["code"] == "multiple_envelopes"
    assert envelope["error"]["details"]["envelopes"] == ["data", "internal_error"]


# --- N12: lazy builds under threads -------------------------------------------------------


def test_a_lazy_leaf_is_built_once_under_concurrent_first_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds: list[int] = []

    def slow_build(_command_id: str) -> Any:
        builds.append(1)
        time.sleep(0.05)
        return lambda: None

    monkeypatch.setattr(app_module, "_build_leaf", slow_build)
    leaf = app_module._lazy_leaf_command("project.list")(name="list")
    start = threading.Barrier(8, timeout=10)
    seen: list[Any] = []

    def first_use() -> None:
        start.wait()
        seen.append(leaf._real())

    threads = [threading.Thread(target=first_use) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(builds) == 1
    assert all(item is seen[0] for item in seen)


def test_the_click_root_is_built_once_under_concurrent_first_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds: list[int] = []

    def slow_get_command(_app: Any) -> Any:
        builds.append(1)
        time.sleep(0.05)
        return SimpleNamespace(commands={})

    monkeypatch.setattr(app_module, "_ROOT_COMMAND", None)
    monkeypatch.setattr(app_module.typer.main, "get_command", slow_get_command)
    start = threading.Barrier(8, timeout=10)
    roots: list[Any] = []

    def first_use() -> None:
        start.wait()
        roots.append(app_module._root_click_command())

    threads = [threading.Thread(target=first_use) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(builds) == 1
    assert all(root is roots[0] for root in roots)


# --- N13: the run id comes from the login, not the process environment -------------------


def _client_headers(login: ExplicitLogin | None) -> Any:
    from mammoth_cli.context.resolver import resolve_auth
    from mammoth_cli.runtime.invocation import Invocation
    from mammoth_cli.services.sdk_service import SdkMammothService

    if login is None:
        raise AssertionError("login is required")
    call = embedded.EmbeddedCall(login=login)
    token = embedded.enter(call)
    try:
        auth = resolve_auth(Invocation(command_id="project.list", output="json"))
        return SdkMammothService(auth)._client.session.headers
    finally:
        embedded.leave(token)


def test_embedded_calls_ignore_the_agent_run_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("mammoth_cli.context.resolver.resolve_token_workspace", lambda *_args: 5)
    monkeypatch.setenv("MAMMOTH_AGENT_RUN", "run-from-env")
    plain = ExplicitLogin(
        api_key=None, api_secret=None, api_token="jwt", server_prefix="box", headers={}
    )
    with_header = ExplicitLogin(
        api_key=None,
        api_secret=None,
        api_token="jwt",
        server_prefix="box",
        headers={"X-Mammoth-Agent-Run": "run-from-login"},
    )

    assert "X-Mammoth-Agent-Run" not in _client_headers(plain)
    assert _client_headers(with_header)["X-Mammoth-Agent-Run"] == "run-from-login"


def test_a_terminal_run_still_reads_the_agent_run_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mammoth_cli.context.resolver import ResolvedAuth
    from mammoth_cli.services.sdk_service import SdkMammothService

    monkeypatch.setenv("MAMMOTH_AGENT_RUN", "run-from-env")
    auth = ResolvedAuth(
        api_key=None,
        api_secret=None,
        api_token="mm_" + "t" * 43,
        base_url="https://box.mammoth.io/api/v2",
        workspace_id=5,
    )

    service = SdkMammothService(auth)

    assert service._client.session.headers["X-Mammoth-Agent-Run"] == "run-from-env"


# --- N4 / N10: a local path is marked and refused when embedded -------------------------


def _takes_local_path(record: dict[str, Any]) -> bool:
    if any(item.get("kind") == LOCAL_PATH for item in record.get("positionals", [])):
        return True
    return any(field.get("kind") == LOCAL_PATH for field in _accepted_fields(record) or [])


def test_the_two_named_commands_are_marked() -> None:
    assert {"dashboard.chat.attachment.upload", "connector.draft.sample"} <= local_path_commands()


def test_help_that_says_local_path_is_marked() -> None:
    unmarked = [
        record["command_id"]
        for record in load_commands()
        for item in record.get("positionals", [])
        if "path to a local" in str(item.get("help", "")).lower() and item.get("kind") != LOCAL_PATH
    ]
    assert unmarked == []


def test_a_binary_input_field_is_marked() -> None:
    """A field typed as an open file takes a host file, so it must carry the marker."""
    unmarked = [
        (record["command_id"], field["name"])
        for record in load_commands()
        for field in _accepted_fields(record) or []
        if "BinaryIO" in str(field["type"]) and field.get("kind") != LOCAL_PATH
    ]
    assert unmarked == []


def test_schema_get_exposes_the_marker() -> None:
    by_id = {record["command_id"]: record for record in load_commands()}
    sample = by_id["connector.draft.sample"]
    upload = by_id["collection.files.upload"]

    assert [item["kind"] for item in sample["positionals"] if "kind" in item] == [LOCAL_PATH]
    assert {f["name"] for f in _accepted_fields(upload) or [] if f.get("kind")} == {"files"}


def test_every_command_that_takes_a_local_path_is_refused_when_embedded() -> None:
    marked = [r["command_id"] for r in load_commands() if _takes_local_path(r)]
    assert marked  # the scan finds the commands at all
    not_refused: list[str] = []
    for command_id in marked:
        call = embedded.EmbeddedCall(login=_LOGIN)
        token = embedded.enter(call)
        try:
            with pytest.raises(typer.Exit):
                executor.run(command_id, "json", _must_not_run)
        finally:
            embedded.leave(token)
        error = call.envelopes[0].get("error", {})
        # import-workbook keeps its own, more helpful intent-only refusal.
        if error.get("code") not in {"not_available_embedded", "intent_only_dashboards"}:
            not_refused.append(command_id)
    assert not_refused == []


def test_marked_commands_are_all_in_the_derived_set() -> None:
    marked = {r["command_id"] for r in load_commands() if _takes_local_path(r)}

    assert marked <= local_path_commands()


def test_the_two_named_commands_are_refused_through_invoke() -> None:
    for args in (
        ["dashboard", "chat", "attachment", "upload", "1", "notes.pdf"],
        ["connector", "draft", "sample", "1", "deals.csv"],
    ):
        envelope = invoke(args, login=_LOGIN)

        assert envelope["error"]["code"] == "not_available_embedded", args


def test_a_terminal_run_is_not_refused() -> None:
    call = embedded.current()
    assert call is None
    # Outside an embedded call the guard is inert.
    executor._refuse_if_embedded("dashboard.chat.attachment.upload")


def _must_not_run() -> tuple[Any, dict[str, Any]]:
    raise AssertionError("the command ran")
