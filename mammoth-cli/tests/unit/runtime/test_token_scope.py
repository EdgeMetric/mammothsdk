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
