"""``mammoth_cli.embed.invoke``: in-process calls for a host's own users."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin, ResolvedAuth, resolve_auth
from mammoth_cli.embed import invoke
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.sdk_service import SdkMammothService
from mammoth_cli.services.testing import FakeMammothService

BASE_URL = "https://box.mammoth.io/api/v2"


_WORKSPACE_OF_TOKEN: dict[str, int] = {}


@pytest.fixture(autouse=True)
def _server_names_the_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token names its workspace and the CLI learns it from the server; no network here."""
    monkeypatch.setattr(
        resolver,
        "resolve_token_workspace",
        lambda _base_url, token, _timeout: _WORKSPACE_OF_TOKEN[token],
    )


def _login(workspace_id: int, token: str = "jwt-user") -> ExplicitLogin:
    _WORKSPACE_OF_TOKEN[token] = workspace_id
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
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


def test_pipeline_timeout_option_is_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[Invocation] = []
    real_resolve = resolve_auth

    def _spy(invocation: Invocation, explicit_login: ExplicitLogin | None = None) -> ResolvedAuth:
        captured.append(invocation)
        return real_resolve(invocation, explicit_login)

    monkeypatch.setattr("mammoth_cli.runtime.session.resolve_auth", _spy)
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: FakeMammothService())

    invoke(["project", "list"], login=_login(5), pipeline_timeout=300)

    assert captured[0].pipeline_timeout == 300.0


def test_explicit_pipeline_timeout_in_args_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[Invocation] = []
    real_resolve = resolve_auth

    def _spy(invocation: Invocation, explicit_login: ExplicitLogin | None = None) -> ResolvedAuth:
        captured.append(invocation)
        return real_resolve(invocation, explicit_login)

    monkeypatch.setattr("mammoth_cli.runtime.session.resolve_auth", _spy)
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: FakeMammothService())

    envelope = invoke(
        ["project", "list", "--pipeline-timeout", "600"], login=_login(5), pipeline_timeout=300
    )

    assert captured[0].pipeline_timeout == 600.0
    assert "error" not in envelope


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
    assert auth.workspace_id == 9
    assert "X-WORKSPACE-ID" not in service._client.session.headers


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


def test_job_timeout_and_return_running_options_are_appended() -> None:
    from mammoth_cli.embed import _argv

    argv = _argv(
        ["job", "wait", "9"],
        project_id=None,
        timeout=None,
        pipeline_timeout=None,
        job_timeout=45.0,
        return_running=True,
    )

    assert argv[:5] == ["job", "wait", "9", "--job-timeout", "45.0"]
    assert "--return-running" in argv


def test_args_that_already_set_job_timeout_and_return_running_win() -> None:
    from mammoth_cli.embed import _argv

    argv = _argv(
        ["job", "wait", "9", "--job-timeout=5", "--return-running"],
        project_id=None,
        timeout=None,
        pipeline_timeout=None,
        job_timeout=45.0,
        return_running=True,
    )

    assert argv.count("--return-running") == 1
    assert not any(token == "--job-timeout" for token in argv)


def test_project_use_says_to_pass_project_when_embedded(isolated_cli_config: Path) -> None:
    """An embedded call has no profile to save a project in (runtime/session.py), so
    ``context project use`` failed with profile_not_found and the host's agent kept
    retrying it. It must say what works instead."""
    envelope = invoke(["context", "project", "use", "6600"], login=_login(4))

    assert envelope["error"]["code"] == "no_saved_project"
    assert "--project" in envelope["error"]["hint"]


def test_project_clear_says_to_pass_project_when_embedded(isolated_cli_config: Path) -> None:
    envelope = invoke(["context", "project", "clear"], login=_login(4))

    assert envelope["error"]["code"] == "no_saved_project"


def test_a_missing_project_does_not_point_an_embedded_call_at_project_use() -> None:
    from mammoth_cli.errors.envelope import missing_project_error

    token = embedded.enter(embedded.EmbeddedCall(login=_login(4)))
    try:
        error = missing_project_error()
    finally:
        embedded.leave(token)

    assert not any("context project use" in c for c in error.recovery_commands)
    assert "--project" in (error.hint or "")


@pytest.mark.parametrize(
    "args",
    [
        ["dashboard", "create-blank", "--yes", "--input", '{"params": {"dataview_id": 1}}'],
        ["dashboard", "canvas", "save", "42", "--input", '{"body": {"params": {"canvas": {}}}}'],
        ["dashboard", "canvas", "restore", "42"],
        ["dashboard", "pages", "add", "42", "--yes", "--confirm", "42"],
        ["dashboard", "template", "apply", "--input", '{"body": {"params": {}}}'],
        ["dashboard", "template", "fit", "42"],
        ["dashboard", "templates", "use", "some-slug", "--yes"],
        ["dashboard", "template", "create", "--input", '{"body": {"params": {}}}'],
        [
            "dashboard",
            "import-workbook",
            "sample.twbx",
            "--project",
            "7",
            "--yes",
            "--confirm",
            "7",
        ],
    ],
)
def test_hand_crafted_dashboard_writes_are_refused_when_embedded(args: list[str]) -> None:
    """The in-product agent passes only the user's intent to the dashboard builder;
    every hand-crafting write fails fast and names the two intent commands."""
    envelope = invoke(args, login=_login(4))

    assert envelope["error"]["code"] == "intent_only_dashboards"
    assert "dashboard v3 generate" in envelope["error"]["hint"]
    assert "dashboard chat edit" in envelope["error"]["hint"]


def test_canvas_get_is_still_allowed_when_embedded(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeMammothService()
    fake.responses["mammoth.api.dashboards.DashboardsAPI.canvas_get"] = {"canvas": {}}
    monkeypatch.setattr(service_factory, "build_service", lambda auth, **_kw: fake)

    envelope = invoke(["dashboard", "canvas", "get", "42"], login=_login(4))

    assert "error" not in envelope
