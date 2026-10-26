"""An embedded call's discovery leaves out what it cannot run (history, local files)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin, ResolvedAuth
from mammoth_cli.discovery import offered_recipes, runnable_recipes, visible_recipes
from mammoth_cli.embed import invoke
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.embed_scope import hidden_embedded, refused_embedded
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService

_LOCAL = {"append-rows", "upload-dashboard", "upload-clean", "join-files", "undo-last-change"}


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_args: 5)

    def _build(auth: ResolvedAuth, **_kwargs: Any) -> FakeMammothService:
        del auth
        return FakeMammothService()

    monkeypatch.setattr(service_factory, "build_service", _build)


def _login() -> ExplicitLogin:
    return ExplicitLogin(
        api_key=None, api_secret=None, api_token="jwt", server_prefix="box", workspace_id=5
    )


@pytest.fixture
def in_call() -> Iterator[None]:
    """Run the test body inside an embedded call that hides pending commands."""
    token = embedded.enter(embedded.EmbeddedCall(login=_login(), hide_pending=True))
    try:
        yield
    finally:
        embedded.leave(token)


def _data(argv: list[str]) -> dict[str, Any]:
    envelope = invoke(argv, login=_login(), project_id=9)
    assert "error" not in envelope, envelope
    data: dict[str, Any] = envelope["data"]
    return data


def test_a_terminal_run_refuses_and_hides_nothing() -> None:
    assert not refused_embedded("history.undo")
    assert not hidden_embedded("file.upload", "pending")
    assert offered_recipes() == runnable_recipes()


@pytest.mark.usefixtures("in_call")
def test_an_embedded_call_refuses_host_and_local_path_commands() -> None:
    assert refused_embedded("history.undo")
    assert refused_embedded("file.upload")
    assert not refused_embedded("view.transform.join")
    assert hidden_embedded("view.get", "pending")
    assert not hidden_embedded("view.get", "served")
    assert not hidden_embedded(None)


@pytest.mark.usefixtures("in_call")
def test_recipes_with_a_refused_run_line_are_not_offered() -> None:
    hidden = {recipe["id"] for recipe in runnable_recipes()} - {
        recipe["id"] for recipe in offered_recipes()
    }
    assert hidden == _LOCAL
    # Its steps show a 'file upload' for the inputs, but its run lines need none.
    assert "blend-by-key" in {recipe["id"] for recipe in visible_recipes()}


def test_embedded_recipe_list_leaves_out_local_file_recipes() -> None:
    listed = {recipe["id"] for recipe in _data(["recipe", "list"])["recipes"]}
    assert listed and not listed & _LOCAL
    assert "blend-by-key" in listed


def test_embedded_schema_find_leaves_out_history_commands() -> None:
    matches = _data(["schema", "find", "history undo resume"])["matches"]
    assert not [m for m in matches if str(m["command_id"]).startswith("history.")]


def test_embedded_capability_find_leaves_out_file_upload() -> None:
    matches = _data(["capability", "find", "upload file"])["matches"]
    assert "file.upload" not in {m.get("canonical_command") for m in matches}


def test_embedded_how_does_not_swap_in_a_weaker_recipe() -> None:
    data = _data(["how", "undo my last change"])
    assert data["matched"] is False
    assert data["steps"] == []
    assert "app does not have" in data["hint"]


def test_embedded_how_keeps_the_parts_it_can_do() -> None:
    data = _data(["how", "upload a file, remove duplicates then export csv"])
    commands = [step["command_id"] for step in data["steps"]]
    assert "file.upload" not in commands
    assert "view.export.csv" in commands
