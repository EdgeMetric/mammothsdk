"""``view explore-panel export-image``: its own handler, reachable from argv, gated as a read."""

from __future__ import annotations

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.view_explore import view_explore_panel_export_image
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.testing import make_runner

_COMMAND_ID = "view.explore-panel.export-image"


def test_the_command_runs_its_own_explore_handler() -> None:
    """The manifest's SDK symbol is a dashboards method, so the generic dashboard handler would
    take it unless the registry names this one."""
    assert HANDLERS[_COMMAND_ID] is view_explore_panel_export_image


def test_the_command_is_reachable_from_the_cli() -> None:
    record = command_by_id(_COMMAND_ID)
    assert record is not None
    result = make_runner().invoke([*record["command_path"].split(), "--help"])
    assert result.exit_code == 0


def test_the_manifest_gates_it_as_a_read_with_no_confirmation() -> None:
    record = command_by_id(_COMMAND_ID)
    assert record is not None
    assert (record["mutation_class"], record["confirmation"]) == ("read", "none")


def test_an_existing_output_file_is_refused_before_any_request(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """The file_exists guard belongs to export-image (it was once misplaced in panel edit)."""
    import json

    import pytest

    from mammoth_cli.errors.envelope import CliError
    from mammoth_cli.runtime.invocation import Invocation

    target = tmp_path / "card.svg"
    target.write_text("old", encoding="utf-8")
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"card": "Sales", "output_path": str(target)}), encoding="utf-8")
    invocation = Invocation(
        command_id=_COMMAND_ID, project=1, extra_args=["7"], input_file=str(doc)
    )
    with pytest.raises(CliError) as refused:
        view_explore_panel_export_image(invocation)
    assert refused.value.code == "file_exists"
    assert refused.value.exit_status == 6
    assert target.read_text(encoding="utf-8") == "old"
