"""``view explore-panel get|set`` and ``dashboard figure add``: input checks before any call.

Each handler refuses a bad ``--input`` before it opens a service, so these run the real
handlers and the real command registry with nothing standing in for either.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import make_runner

_FIGURE = {"kind": "hbar", "title": "Revenue by region", "dim": "Region", "measure": "Revenue"}


def _input(tmp_path: Path, document: object) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return str(path)


def _figure_add(tmp_path: Path, document: object) -> CliError:
    invocation = Invocation(
        command_id="dashboard.figure.add",
        extra_args=["7"],
        input_file=_input(tmp_path, document),
    )
    with pytest.raises(CliError) as refused:
        dashboard_cmd.dashboard_figure_add(invocation)
    return refused.value


def test_figure_add_names_a_missing_figure(tmp_path: Path) -> None:
    refused = _figure_add(tmp_path, {"dataview_id": 3})
    assert refused.code == "missing_field"
    assert "'figure'" in refused.message


def test_figure_add_names_a_missing_dataview_id(tmp_path: Path) -> None:
    refused = _figure_add(tmp_path, {"figure": _FIGURE})
    assert refused.code == "missing_field"
    assert "'dataview_id'" in refused.message


@pytest.mark.parametrize(
    "page",
    [{"id": "p1", "new_title": "Both"}, {"title": "wrong key"}, {}],
)
def test_figure_add_refuses_a_page_that_is_not_id_or_new_title(
    tmp_path: Path, page: object
) -> None:
    refused = _figure_add(tmp_path, {"dataview_id": 3, "figure": _FIGURE, "page": page})
    assert refused.code == "invalid_argument"
    assert "'page'" in refused.message


def test_figure_add_refuses_a_page_that_is_not_an_object(tmp_path: Path) -> None:
    refused = _figure_add(tmp_path, {"dataview_id": 3, "figure": _FIGURE, "page": "p1"})
    assert refused.code == "invalid_input_field_type"


def test_figure_add_does_not_accept_the_sdk_page_arguments(tmp_path: Path) -> None:
    """The endpoint's ``page`` is the only spelling; a second one would be dropped silently."""
    refused = _figure_add(tmp_path, {"dataview_id": 3, "figure": _FIGURE, "page_id": "p1"})
    assert refused.code == "unknown_input_field"


def test_page_maps_to_the_sdk_arguments() -> None:
    assert dashboard_cmd._figure_page_kwargs({"id": "p1"}) == {"page_id": "p1"}
    assert dashboard_cmd._figure_page_kwargs({"new_title": "From Explore"}) == {
        "page_new_title": "From Explore"
    }


def test_explore_panel_set_names_a_missing_panel(tmp_path: Path) -> None:
    invocation = Invocation(
        command_id="view.explore-panel.set",
        extra_args=["123"],
        project=180,
        input_file=_input(tmp_path, {}),
    )
    with pytest.raises(CliError) as refused:
        view_cmd.view_explore_panel_set(invocation)
    assert refused.value.code == "missing_field"
    assert "'panel'" in refused.value.message


def test_explore_panel_commands_need_a_project() -> None:
    for handler, command_id in (
        (view_cmd.view_explore_panel_get, "view.explore-panel.get"),
        (view_cmd.view_explore_panel_set, "view.explore-panel.set"),
    ):
        with pytest.raises(CliError) as refused:
            handler(Invocation(command_id=command_id, extra_args=["123"]))
        assert refused.value.code == "project_required"


@pytest.mark.parametrize(
    "command_id", ["view.explore-panel.get", "view.explore-panel.set", "dashboard.figure.add"]
)
def test_the_command_is_registered_and_in_the_manifest(command_id: str) -> None:
    assert command_id in HANDLERS
    assert command_by_id(command_id) is not None


@pytest.mark.parametrize(
    "words",
    [
        ["view", "explore-panel", "get"],
        ["view", "explore-panel", "set"],
        ["dashboard", "figure", "add"],
    ],
)
def test_the_command_is_reachable_from_the_cli(words: list[str]) -> None:
    result = make_runner().invoke([*words, "--help"])
    assert result.exit_code == 0
    assert " ".join(words) in " ".join(result.output.split())


def test_explore_help_says_it_reads_column_values_not_explore_cards() -> None:
    from typer.testing import CliRunner

    from mammoth_cli.app import app

    result = CliRunner().invoke(app, ["view", "data", "explore", "--help"])

    assert "not an Explore card" in " ".join(result.output.split())
