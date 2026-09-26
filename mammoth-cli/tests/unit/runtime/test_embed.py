"""``mammoth_cli.embed.invoke``: in-process calls for a host's own users."""

from __future__ import annotations

import threading
from typing import Any

import pytest

from mammoth_cli.context.resolver import ExplicitLogin, ResolvedAuth, resolve_auth
from mammoth_cli.embed import invoke
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.sdk_service import SdkMammothService
from mammoth_cli.services.testing import FakeMammothService

BASE_URL = "https://box.mammoth.io/api/v2"


def _login(workspace_id: int, token: str = "jwt-user") -> ExplicitLogin:
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
        workspace_id=workspace_id,
        api_token=token,
        server_prefix="box",
        headers={"Authorization": f"Bearer {token}", "Cookie": f"session={token}"},
    )


def test_two_concurrent_calls_each_see_their_own_login(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    both_inside = threading.Barrier(2, timeout=10)
    seen: dict[int, ResolvedAuth] = {}

    def _build(auth: ResolvedAuth, **_kwargs: Any) -> FakeMammothService:
        both_inside.wait()  # both calls are in flight before either returns
        seen[auth.workspace_id] = auth
        return FakeMammothService()

    monkeypatch.setattr(service_factory, "build_service", _build)
    results: dict[int, dict[str, Any]] = {}

    def _run(workspace_id: int) -> None:
        results[workspace_id] = invoke(
            ["project", "list"], login=_login(workspace_id, token=f"jwt-{workspace_id}")
        )

    threads = [threading.Thread(target=_run, args=(ws,)) for ws in (11, 22)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert seen[11].headers == {"Authorization": "Bearer jwt-11", "Cookie": "session=jwt-11"}
    assert seen[22].headers == {"Authorization": "Bearer jwt-22", "Cookie": "session=jwt-22"}
    assert results[11]["meta"]["workspace_id"] == 11
    assert results[22]["meta"]["workspace_id"] == 22
    assert capsys.readouterr() == ("", "")
    assert embedded.current() is None


def test_cli_error_is_returned_not_raised(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    envelope = invoke(["project", "no-such-command"], login=_login(5))

    assert envelope["error"]["code"] in {"usage_error", "unknown_command"}
    assert capsys.readouterr() == ("", "")


def test_handler_error_is_returned_as_its_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    from mammoth_cli.errors.envelope import EXIT_AUTH, CliError

    fake = FakeMammothService()
    fake.responses["mammoth.api.projects.ProjectsAPI.list"] = CliError(
        code="authentication_failed", message="expired", exit_status=EXIT_AUTH
    )
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: fake)

    envelope = invoke(["project", "list"], login=_login(5))

    assert envelope["error"]["code"] == "authentication_failed"


def test_project_and_output_options_are_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[Invocation] = []
    real_resolve = resolve_auth

    def _spy(invocation: Invocation, explicit_login: ExplicitLogin | None = None) -> ResolvedAuth:
        captured.append(invocation)
        return real_resolve(invocation, explicit_login)

    monkeypatch.setattr("mammoth_cli.runtime.session.resolve_auth", _spy)
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: FakeMammothService())

    envelope = invoke(["project", "list", "--output", "table"], login=_login(5), project_id=42)

    assert (captured[0].output, captured[0].no_input, captured[0].project) == ("json", True, 42)
    assert envelope["meta"]["project_id"] == 42


def test_server_prefix_and_headers_reach_the_sdk_session() -> None:
    call = embedded.EmbeddedCall(login=_login(9, token="jwt-9"))
    token = embedded.enter(call)
    try:
        auth = resolve_auth(Invocation(command_id="project.list", output="json"))
    finally:
        embedded.leave(token)

    service = SdkMammothService(auth)

    assert auth.base_url == BASE_URL
    assert service._client.base_url == BASE_URL
    assert service._client.session.headers["Authorization"] == "Bearer jwt-9"
    assert service._client.session.headers["Cookie"] == "session=jwt-9"
    assert service._client.session.headers["X-WORKSPACE-ID"] == "9"


def test_update_check_and_run_log_are_off_when_embedded() -> None:
    from mammoth_cli.runtime import executor, updates

    call = embedded.EmbeddedCall(login=_login(9))
    token = embedded.enter(call)
    try:
        assert updates.enabled() is False
        invocation = Invocation(command_id="project.list", output="json")
        assert executor._open_run_log("project.list", invocation) is None
    finally:
        embedded.leave(token)


def test_help_is_captured_as_a_success_envelope_not_no_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """schema find's own no-match hint tells agents to run '--help'; an
    embedded agent following that advice must not dead-end on 'no_output'.
    """
    envelope = invoke(["view", "transform", "--help"], login=_login(5))

    assert "error" not in envelope
    assert "Transform" in envelope["data"]["help"]
    assert "date-diff" in envelope["data"]["help"]
    assert envelope["meta"]["command"] == "view transform"
    assert capsys.readouterr() == ("", "")
