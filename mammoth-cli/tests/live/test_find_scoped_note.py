"""Live checks: ``dataset find`` under a project does not call an unambiguous name ambiguous.

A name that is an exact match in the project the call runs under resolves there; the
same name in other projects must not turn into an "ask the user which one" note.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_find_scoped_note.py -m live -v
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

#: koyal QA fixture: the project, and a dataset in it whose name also exists elsewhere.
PROJECT = 18504
DATASET = 38715
NAME = "uqa-w25-B-c5"


def _find(live_cli: LiveCli, name: str) -> dict[str, object]:
    data, _ = live_cli.ok(
        "dataset", "find", name, "--input", json.dumps({"all_projects": True}), project=PROJECT
    )
    assert isinstance(data, dict)
    return data


def test_exact_name_in_the_project_is_not_called_ambiguous(live_cli: LiveCli) -> None:
    found = _find(live_cli, NAME)

    assert len(found["matches"]) > 1  # type: ignore[arg-type]
    note = str(found["note"])
    assert str(DATASET) in note
    assert "ask the user" not in note


def test_no_exact_name_in_the_project_still_asks(live_cli: LiveCli) -> None:
    found = _find(live_cli, "uqa-w25-B-c")

    assert "ask the user" in str(found["note"])


def test_default_scope_says_the_project_match_is_the_answer(live_cli: LiveCli) -> None:
    found, _ = live_cli.ok("dataset", "find", NAME, project=PROJECT)

    note = str(found["note"])
    assert "is the answer" in note
    assert "only when the user names another project" in note
    assert '"all_projects": true' in note
