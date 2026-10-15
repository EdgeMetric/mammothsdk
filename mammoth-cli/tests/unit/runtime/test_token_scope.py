"""A token limited to one project is refused before it creates a project it cannot open."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.doctor import _scope_check
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.token_scope import refuse_pinned_project


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
