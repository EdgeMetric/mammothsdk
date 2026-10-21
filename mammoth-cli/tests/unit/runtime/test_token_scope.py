"""A token limited to one project is refused before it creates a project it cannot open."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.doctor import _scope_check
from mammoth_cli.context import credentials
from mammoth_cli.context.credentials import OAuthSession
from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import token_scope
from mammoth_cli.runtime.token_scope import pinned_projects, refuse_pinned_project


def test_a_pinned_token_is_refused_with_the_project_it_is_limited_to() -> None:
    with pytest.raises(CliError) as refused:
        refuse_pinned_project(4404, "create a project")
    error = refused.value
    assert error.code == "authorization_required"
    assert "project 4404" in error.message
    assert "--project 4404" in (error.hint or "")
    assert error.recovery_commands == ["mammoth project get 4404"]


def test_an_unpinned_token_may_create() -> None:
    refuse_pinned_project(None, "create a project")


def test_doctor_reports_the_scope_of_a_pinned_token() -> None:
    check = _scope_check(4404, selected_project=4404)
    assert check["ok"] is True
    assert check["pinned_project_id"] == 4404
    assert "limited to project 4404" in check["detail"]


def test_doctor_fails_when_the_selected_project_is_not_the_pinned_one() -> None:
    check = _scope_check(4404, selected_project=7)
    assert check["ok"] is False
    assert "use --project 4404" in check["detail"]


def test_doctor_reports_an_unpinned_token() -> None:
    check = _scope_check(None, selected_project=7)
    assert check["ok"] is True
    assert check["pinned_project_id"] is None


def _forbidden() -> CliError:
    from mammoth_cli.services.mapping import PINNED_PROJECT_HINT

    return CliError(
        code="authorization_required",
        message="denied",
        hint="Ask an administrator. " + PINNED_PROJECT_HINT,
    )


def test_403_hint_drops_the_project_limited_blame_when_the_token_is_not_limited() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    error = qualify_pin_hint(_forbidden(), lambda: None)
    assert "limited to one project" not in error.hint
    assert error.hint == "Ask an administrator."


def test_403_hint_names_the_project_when_the_token_is_limited() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    error = qualify_pin_hint(_forbidden(), lambda: 77)
    assert "limited to project 77" in error.hint
    assert error.details["pinned_project_id"] == 77


def test_403_hint_is_left_alone_when_the_lookup_fails() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    def broken() -> int | None:
        raise RuntimeError("offline")

    original = _forbidden().hint
    assert qualify_pin_hint(_forbidden(), broken).hint == original


def test_403_hint_names_the_pinned_project_by_name_when_it_is_known() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    error = qualify_pin_hint(_forbidden(), lambda: 77, lambda pin: "Sales 2026")
    assert "limited to project Sales 2026 (77)" in error.hint
    assert "--project 77" in error.hint


def test_403_hint_falls_back_to_the_id_when_the_name_lookup_fails() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    def broken(pin: int) -> str | None:
        raise RuntimeError("offline")

    error = qualify_pin_hint(_forbidden(), lambda: 77, broken)
    assert "limited to project 77:" in error.hint


def test_refusing_a_pinned_token_names_the_project() -> None:
    with pytest.raises(CliError) as refused:
        refuse_pinned_project(4404, "create a project", project_name="Sales 2026")
    assert "project Sales 2026 (4404)" in refused.value.message


def _not_a_member() -> CliError:
    return CliError(
        code="authorization_required",
        message="You are not a member of project 4460.",
        hint="Project lists show only the projects you belong to. Ask a project admin to add you.",
    )


def test_a_pinned_token_is_not_told_to_ask_for_membership() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    error = qualify_pin_hint(_not_a_member(), lambda: 3633, lambda pin: "Analytics")
    assert "limited to project Analytics (3633)" in error.message
    assert "project 4460" in error.message
    assert "--project 3633" in error.hint
    assert "admin" not in error.hint
    assert error.details["pinned_project_id"] == 3633


def test_an_unpinned_token_keeps_the_membership_message() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    error = qualify_pin_hint(_not_a_member(), lambda: None)
    assert error.message == "You are not a member of project 4460."


# -- a token limited to several projects --------------------------------------------


class _Current:
    """What ``WorkspaceAPI.current`` answers, for the token-scope reader."""

    def __init__(self, answer: object) -> None:
        self.answer = answer

    def call(self, symbol: str, **kwargs: object) -> object:
        return self.answer


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ({"id": 4, "project": 3, "projects": [7, 3]}, (3, 7)),
        ({"id": 4, "project": 3}, (3,)),
        ({"id": 4, "project": 3, "projects": None}, (3,)),
        ({"id": 4, "project": None, "projects": None}, None),
        ({"id": 4}, None),
    ],
)
def test_pinned_projects_reads_the_set_else_the_one_project(
    answer: dict[str, object], expected: tuple[int, ...] | None
) -> None:
    from mammoth_cli.runtime.token_scope import pinned_projects

    assert pinned_projects(_Current(answer)) == expected  # type: ignore[arg-type]


def test_pinned_projects_reads_the_sdk_model() -> None:
    from mammoth.models.workspaces import CurrentWorkspace

    from mammoth_cli.runtime.token_scope import pinned_projects

    current = CurrentWorkspace.model_validate({"id": 4, "project": 3, "projects": [3, 7]})
    assert pinned_projects(_Current(current)) == (3, 7)  # type: ignore[arg-type]


def test_a_token_limited_to_several_projects_is_refused_naming_them_all() -> None:
    with pytest.raises(CliError) as refused:
        refuse_pinned_project((3, 7), "create a project")
    error = refused.value
    assert "projects 3, 7" in error.message
    assert "--project 3" in (error.hint or "")
    assert error.details == {"pinned_project_id": 3, "pinned_project_ids": [3, 7]}


def test_403_hint_names_every_project_of_a_token_limited_to_several() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    names = {3: "Sales", 7: "Ops"}
    error = qualify_pin_hint(_forbidden(), lambda: (3, 7), names.get)
    assert "limited to projects Sales (3), Ops (7)" in error.hint
    assert error.details["pinned_project_ids"] == [3, 7]


def test_not_a_member_of_one_of_the_pinned_projects_keeps_the_membership_message() -> None:
    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    error = qualify_pin_hint(_not_a_member(), lambda: (3, 4460))
    assert error.message == "You are not a member of project 4460."


def test_doctor_accepts_any_project_of_a_token_limited_to_several() -> None:
    check = _scope_check((3, 7), selected_project=7)
    assert check["ok"] is True
    assert check["pinned_project_ids"] == [3, 7]
    assert "limited to projects 3, 7" in check["detail"]


def test_doctor_fails_when_the_selected_project_is_none_of_the_pinned_ones() -> None:
    check = _scope_check((3, 7), selected_project=8)
    assert check["ok"] is False
    assert "use --project 3" in check["detail"]


# --- the on-disk pin cache ----------------------------------------------------------


class _CountingService:
    """A service whose ``/workspaces/current`` answer is fixed and whose calls are counted."""

    def __init__(self, current: dict[str, object]) -> None:
        self.current = current
        self.calls = 0

    def call(self, _symbol: str, /, **_kwargs: object) -> object:
        self.calls += 1
        return self.current


def _token_auth(token: str = "mm_abc") -> ResolvedAuth:
    return ResolvedAuth(None, None, 7, "https://api.example.test", api_token=token)


def _pins(
    service: _CountingService, auth: ResolvedAuth | None = None, **kwargs: Any
) -> token_scope.Pins | None:
    return pinned_projects(service, auth, **kwargs)  # type: ignore[arg-type]


def test_the_pin_is_read_live_once_then_from_the_cache() -> None:
    service = _CountingService({"projects": [9, 4]})
    auth = _token_auth()
    assert _pins(service, auth) == (4, 9)
    assert _pins(service, auth) == (4, 9)
    assert service.calls == 1


def test_an_unlimited_token_is_cached_too() -> None:
    service = _CountingService({})
    auth = _token_auth()
    assert _pins(service, auth) is None
    assert _pins(service, auth) is None
    assert service.calls == 1


def test_refresh_reads_live_and_updates_the_cache() -> None:
    service = _CountingService({"project": 4})
    auth = _token_auth()
    assert _pins(service, auth) == (4,)
    service.current = {"project": 5}
    assert _pins(service, auth, refresh=True) == (5,)
    assert _pins(service, auth) == (5,)
    assert service.calls == 2


def test_another_credential_does_not_share_the_answer() -> None:
    service = _CountingService({"project": 4})
    _pins(service, _token_auth("mm_one"))
    _pins(service, _token_auth("mm_two"))
    assert service.calls == 2


def test_no_auth_means_no_cache() -> None:
    service = _CountingService({"project": 4})
    _pins(service)
    _pins(service)
    assert service.calls == 2


def test_an_expired_entry_is_read_live(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _CountingService({"project": 4})
    auth = _token_auth()
    _pins(service, auth)
    later = time.time() + token_scope.PIN_CACHE_TTL_SECONDS + 1
    monkeypatch.setattr(token_scope.time, "time", lambda: later)
    _pins(service, auth)
    assert service.calls == 2


def test_a_corrupt_entry_falls_back_to_the_live_call() -> None:
    service = _CountingService({"project": 4})
    auth = _token_auth()
    _pins(service, auth)
    (path,) = token_scope.cache_dir().glob("pins-*.json")
    path.write_text("{not json", encoding="utf-8")
    assert _pins(service, auth) == (4,)
    assert service.calls == 2


def test_the_cache_file_is_private_and_holds_no_secret() -> None:
    _pins(_CountingService({"project": 4}), _token_auth("mm_secretvalue"))
    (path,) = token_scope.cache_dir().glob("pins-*.json")
    assert path.stat().st_mode & 0o777 == 0o600
    assert "mm_secretvalue" not in path.read_text(encoding="utf-8")


def test_an_oauth_login_is_keyed_by_its_connection_not_its_access_token(
    isolated_cli_config: Path,
) -> None:
    def store(access: str, refresh: str) -> None:
        credentials.store_credentials(
            "work",
            storage="file",
            oauth=OAuthSession(
                access=access, refresh=refresh, expires_at=1, client_id="cli", grant_id=11
            ),
        )

    auth = ResolvedAuth(None, None, 7, "https://api.example.test", token_provider=lambda: "x")
    service = _CountingService({"project": 4})
    store("access-1", "1.aaa")
    _pins(service, auth, profile="work")
    store("access-2", "1.bbb")  # a refresh: new access and refresh tokens, same connection
    _pins(service, auth, profile="work")
    assert service.calls == 1


def test_forgetting_the_pins_reads_live_again() -> None:
    service = _CountingService({"project": 4})
    auth = _token_auth()
    assert _pins(service, auth) == (4,)
    service.current = {"projects": [4, 6]}
    token_scope.forget_pins()
    assert _pins(service, auth) == (4, 6)
    assert service.calls == 2
