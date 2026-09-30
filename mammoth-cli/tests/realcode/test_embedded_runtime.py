"""The embedded runtime (in-product agent): no profile, no keyring, no terminal.

Drives ``mammoth_cli.embed.invoke`` through the real command stack with only the
HTTP socket faked.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import config as config_cmd
from mammoth_cli.commands import context as context_cmd
from mammoth_cli.context import profiles
from mammoth_cli.context.resolver import ExplicitLogin, not_authenticated_error
from mammoth_cli.embed import invoke
from mammoth_cli.errors.envelope import ERROR_SUMMARIES, CliError
from mammoth_cli.runtime import embedded
from mammoth_cli.services import factory

ServiceFactory = Callable[..., Any]

_LOGIN = ExplicitLogin(
    api_key=None,
    api_secret=None,
    workspace_id=4,
    api_token="jwt-user",
    server_prefix="box",
    headers={"Authorization": "Bearer jwt-user"},
)


def _bind(monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory) -> Any:
    service, api = real_service()
    monkeypatch.setattr(factory, "build_service", lambda *a, **k: service)
    return api


def _profile_project() -> int | None:
    record = profiles.get_profile(profiles.get_selected())
    return None if record is None else record.project_id


def test_project_ensure_never_writes_the_hosts_profile(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind(monkeypatch, real_service)
    api.on("GET", r"/projects", 200, {"projects": [{"id": 9, "name": "Work"}]})
    before = _profile_project()

    envelope = invoke(["project", "ensure", "Work"], login=_LOGIN)

    assert envelope["data"]["project_id"] == 9
    assert envelope["data"]["active"] is False
    assert _profile_project() == before


def test_doctor_is_ok_in_a_healthy_embedded_session(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind(monkeypatch, real_service)
    api.on("GET", r"/projects", 200, {"projects": [{"id": 9, "name": "Work"}]})

    envelope = invoke(["doctor"], login=_LOGIN, project_id=9)

    data = envelope["data"]
    checks = {c["name"]: c for c in data["checks"]}
    assert checks["profile"]["status"] == "not_applicable"
    assert checks["credentials"]["status"] == "not_applicable"
    assert data["ok"] is True
    assert not any("auth login" in r or "context project use" in r for r in data["recommendations"])


def test_authentication_failure_hint_is_reload_the_page(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind(monkeypatch, real_service)
    api.on("GET", r"/projects", 401, {"message": "expired"})

    error = invoke(["project", "list"], login=_LOGIN)["error"]

    assert error["code"] == "authentication_failed"
    assert "reload the page" in error["hint"]
    assert error["recovery_commands"] == []
    assert "API key" not in error["hint"]


def test_profile_and_login_errors_offer_no_login_command() -> None:
    token = embedded.enter(embedded.EmbeddedCall(login=_LOGIN))
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
def test_host_only_commands_are_refused_embedded(args: list[str], tmp_path: Path) -> None:
    error = invoke(args, login=_LOGIN)["error"]

    assert error["code"] == "not_available_embedded"
    assert error["recovery_commands"] == []
    assert "not_available_embedded" in ERROR_SUMMARIES


def test_confirmation_hint_names_no_terminal(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    _bind(monkeypatch, real_service)

    error = invoke(["project", "delete", "9"], login=_LOGIN)["error"]

    assert error["code"] == "confirmation_required"
    assert "terminal" not in error["hint"]
