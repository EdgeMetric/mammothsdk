"""Every command group's --help shows its own description, and the data reads explain ``raw``."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from mammoth_cli import app as app_module
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


def test_no_command_in_the_tree_shows_the_dispatcher_placeholder_as_its_help() -> None:
    placeholder = "Dispatch a generated dashboard command"
    commands = [str(r["command_path"]).split() for r in load_commands()]
    assert commands
    offenders = [" ".join(words) for words in commands if placeholder in _help(*words)]
    assert offenders == []


def test_file_and_folder_group_help_say_which_command_does_what() -> None:
    """Bug bash 2026-10-15: finding upload/delete for files and folders took guessing."""
    from mammoth_cli.app import _GROUP_DESCRIPTIONS  # noqa: PLC2701

    assert "dataset delete" in _GROUP_DESCRIPTIONS["file"]
    assert "upload-folder" in _GROUP_DESCRIPTIONS["file"]
    assert "project folders" in _GROUP_DESCRIPTIONS["folder"]
    assert "file upload-folder" in _GROUP_DESCRIPTIONS["folder"]


def test_help_input_types_keep_their_brackets() -> None:
    """Bug bash 2026-10-15: ``list[a.B] | list[a.C]`` printed as ``B] | C] |``."""
    from mammoth_cli.app import _short_type  # noqa: PLC2701

    assert (
        _short_type("list[mammoth.m.ColumnNameMapping] | list[mammoth.m.ColumnIdMapping] | None")
        == "list[ColumnNameMapping] | list[ColumnIdMapping] | None"
    )
    assert _short_type("mammoth.condition.Condition | None") == "condition"
    assert _short_type("int") == "int"


def test_a_long_help_type_is_cut_at_a_word_never_inside_a_value() -> None:
    from mammoth_cli.app import _short_type  # noqa: PLC2701

    text = _short_type(
        "list[mammoth.m.ColumnNameMapping] | list[mammoth.m.ColumnIdMapping] | bytes | None"
    )
    assert text.endswith(" ...")
    assert len(text) <= 60


def test_download_help_lists_every_file_type() -> None:
    # #282: the Literal was cut at 60 characters, ending in the invalid value 'par.
    from mammoth_cli.app import _help_input_fields  # noqa: PLC2701

    line = _help_input_fields("view.export.download") or ""
    assert "file_type (csv | xlsx | json | ndjson | xml | yaml | parquet)" in line


def test_sdk_backed_leaf_help_reads_the_installed_sdk_not_the_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI accepts a range of SDK versions, so a stale index must not win for those."""
    command_id = "workspace.current"
    live = app_module.live_command_summary(command_id)
    assert live
    monkeypatch.setattr(app_module, "_summary_index", lambda: {command_id: "STALE INDEX TEXT"})
    help_text = app_module._command_help(command_id, None) or ""
    assert "STALE INDEX TEXT" not in help_text
    assert live in help_text


def test_handler_backed_leaf_help_still_reads_the_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_module, "_summary_index", lambda: {"project.list": "INDEX TEXT"})
    assert "INDEX TEXT" in (app_module._command_help("project.list", None) or "")
