"""Live: the embedded runtime (in-product agent): no profile, no keyring, no terminal.

Replaces the fake-socket realcode ``test_embedded_runtime``. ``mammoth_cli.embed.invoke`` runs
the real command stack with the live token as the host's login.
"""

from __future__ import annotations

import pytest
from live_harness import LiveCli

from mammoth_cli.commands import config as config_cmd
from mammoth_cli.commands import context as context_cmd
from mammoth_cli.context import profiles
from mammoth_cli.context.resolver import ExplicitLogin, not_authenticated_error
from mammoth_cli.embed import invoke
from mammoth_cli.errors.envelope import ERROR_SUMMARIES, CliError
from mammoth_cli.runtime import embedded

pytestmark = pytest.mark.live


def _profile_project() -> int | None:
    record = profiles.get_profile(profiles.get_selected())
    return None if record is None else record.project_id


def test_project_ensure_never_writes_the_hosts_profile(
    live_cli: LiveCli, login: ExplicitLogin, scratch_project: int
) -> None:
    name, _ = live_cli.ok("project", "get", str(scratch_project))
    before = _profile_project()

    envelope = invoke(["project", "ensure", name["name"]], login=login)

    assert envelope["data"]["project_id"] == scratch_project
    assert envelope["data"]["active"] is False
    assert _profile_project() == before


def test_doctor_is_ok_in_a_healthy_embedded_session(
    login: ExplicitLogin, scratch_project: int
) -> None:
    envelope = invoke(["doctor"], login=login, project_id=scratch_project)

    data = envelope["data"]
    checks = {c["name"]: c for c in data["checks"]}
    assert checks["profile"]["status"] == "not_applicable"
    assert checks["credentials"]["status"] == "not_applicable"
    assert data["ok"] is True
    assert not any("auth login" in r or "context project use" in r for r in data["recommendations"])


def test_authentication_failure_hint_is_reload_the_page(login: ExplicitLogin) -> None:
    expired = ExplicitLogin(
        api_key=None,
        api_secret=None,
        server_prefix=login.server_prefix,
        api_token="mm_" + "x" * 43,
        headers={"Authorization": "Bearer mm_" + "x" * 43},
    )

    error = invoke(["project", "list"], login=expired)["error"]

    assert error["code"] == "authentication_failed"
    assert "reload the page" in error["hint"]
    assert error["recovery_commands"] == []
    assert "API key" not in error["hint"]


def test_profile_and_login_errors_offer_no_login_command(login: ExplicitLogin) -> None:
    token = embedded.enter(embedded.EmbeddedCall(login=login))
    try:
        errors = [
            not_authenticated_error(),
            context_cmd._profile_not_found_error("nope"),
            config_cmd._profile_not_found_error("nope"),
        ]
        with pytest.raises(CliError) as selected:
            profiles.set_selected("nope")
        errors.append(selected.value)
    finally:
        embedded.leave(token)

    for error in errors:
        assert error.code in {"profile_not_found", "not_authenticated"}
        assert error.recovery_commands == []
        assert "auth login" not in (error.hint or "")


@pytest.mark.parametrize(
    "args",
    [
        ["auth", "login"],
        ["auth", "logout"],
        ["config", "set", "server_prefix", "x"],
        ["upgrade"],
        ["skill", "install"],
        ["skill", "uninstall"],
        ["skill", "update"],
        ["skill", "agents-md", "install"],
        ["completion", "install", "bash"],
    ],
)
def test_host_only_commands_are_refused_embedded(args: list[str], login: ExplicitLogin) -> None:
    error = invoke(args, login=login)["error"]

    assert error["code"] == "not_available_embedded"
    assert error["recovery_commands"] == []
    assert "not_available_embedded" in ERROR_SUMMARIES


def test_confirmation_hint_names_no_terminal(login: ExplicitLogin, scratch_project: int) -> None:
    error = invoke(["project", "delete", str(scratch_project)], login=login)["error"]

    assert error["code"] == "confirmation_required"
    assert "terminal" not in error["hint"]
