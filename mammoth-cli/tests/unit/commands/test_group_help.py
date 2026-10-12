"""Every command group's --help shows its own description, and the data reads explain ``raw``."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from mammoth_cli.app import _group_description, app
from mammoth_cli.manifest.loader import load_commands


def _help(*words: str) -> str:
    return " ".join(CliRunner().invoke(app, [*words, "--help"]).output.split())


@pytest.mark.parametrize(
    "words",
    [("view", "data"), ("view", "transform"), ("view", "explore-panel"), ("dashboard", "figure")],
)
def test_a_subgroup_help_shows_its_own_description_not_its_parents(
    words: tuple[str, ...],
) -> None:
    own, parent = _group_description(words), _group_description(words[:1])
    assert own in _help(*words)
    assert parent not in _help(*words)


def test_every_nested_group_has_a_description_of_its_own() -> None:
    nested = {
        tuple(str(record["command_path"]).split()[:depth])
        for record in load_commands()
        for depth in range(2, len(str(record["command_path"]).split()))
    }
    lacking = sorted(
        " ".join(path)
        for path in nested
        if _group_description(path)
        in (f"Commands for {' '.join(path)}.", _group_description(path[:1]))
    )
    assert lacking == []


@pytest.mark.parametrize("words", [("view", "data", "get"), ("view", "data", "query")])
def test_the_data_reads_say_what_raw_does(words: tuple[str, ...]) -> None:
    assert "raw: true returns DATE values with their time" in _help(*words)


#: Commands that shared the generic dashboard dispatcher's docstring as their help.
_ADDED_GENERATED = [
    ("auth", "connected-apps", "list"),
    ("auth", "connected-apps", "revoke"),
    ("collection", "list"),
    ("collection", "get"),
    ("collection", "create"),
    ("collection", "share"),
    ("dashboard", "engagement", "get"),
    ("dashboard", "own-data", "preview"),
    ("dashboard", "own-data", "status"),
    ("workspace", "current"),
    ("workspace", "oauth-client", "list"),
    ("workspace", "oauth-client", "delete"),
    ("workspace", "oauth-client", "revoke-grant"),
]


@pytest.mark.parametrize("words", _ADDED_GENERATED)
def test_a_generated_command_help_is_about_the_command_not_the_dispatcher(
    words: tuple[str, ...],
) -> None:
    assert "Dispatch a generated dashboard command" not in _help(*words)


def test_oauth_client_delete_and_revoke_grant_each_describe_themselves() -> None:
    assert "Delete an OAuth client registration" in _help("workspace", "oauth-client", "delete")
    assert "Revoke every grant to an OAuth client" in _help(
        "workspace", "oauth-client", "revoke-grant"
    )
