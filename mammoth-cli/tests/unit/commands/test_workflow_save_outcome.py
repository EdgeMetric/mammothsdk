"""A workflow save that did not build every change is an error, not a table."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.workflow import _save_failure, _save_is_running
from mammoth_cli.errors.envelope import CODE_JOB_FAILED


def _workflow(**run: Any) -> dict[str, Any]:
    """A workflow as koyal returns it: the Save the server recorded is in ``canvas_state``."""
    return {"id": 405, "canvas_state": {"pending_changes": [], "save_run": run, "version": 3}}


def test_a_partial_save_fails_and_names_why_each_change_was_not_built() -> None:
    workflow = _workflow(
        status="partial",
        steps=[
            {
                "kind": "rename_dataset",
                "label": "Rename dataset to “Sales”",
                "status": "failed",
                "error": "The workspace couldn't be identified.",
            }
        ],
        needs_setup={"c2": "Change this in the Data Library."},
    )
    error = _save_failure(workflow)
    assert error is not None
    assert error.code == CODE_JOB_FAILED
    assert error.exit_status != 0
    assert "Rename dataset to “Sales”: The workspace couldn't be identified." in error.message
    assert "Change this in the Data Library." in error.message
    assert error.details["save_run"]["status"] == "partial"


def test_a_save_that_built_everything_is_not_an_error() -> None:
    assert _save_failure(_workflow(status="done", steps=[], needs_setup={})) is None


def test_a_running_save_is_waited_on_and_a_finished_one_is_not() -> None:
    assert _save_is_running(_workflow(status="running", steps=[])) is True
    assert _save_is_running(_workflow(status="partial", steps=[])) is False
    assert _save_is_running({"id": 405, "canvas_state": None}) is False
