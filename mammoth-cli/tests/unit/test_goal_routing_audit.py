"""Goal routing audit: each goal a person types lands on the recipe that does that job.

Every new recipe adds its phrasings here, with the recipe id it must route to. The goals are
checked through ``mammoth how``, the same path a user takes, because ``runnable_for`` only
returns recipes that have a ``run`` block and most recipes here have none.
"""

from __future__ import annotations

import pytest

from mammoth_cli.commands import how as how_cmd
from mammoth_cli.runtime.invocation import Invocation

_GOALS: list[tuple[str, str]] = [
    # Replacing rows: must not land on append-rows.
    ("replace a dataset's data with a newer file", "replace-data"),
    ("overwrite last month's data with this month's file", "replace-data"),
    ("swap the data in my dataset for a new export", "replace-data"),
    # Undoing an append: must not land on append-rows.
    ("undo the file I just appended", "undo-append"),
    ("undo the last upload batch", "undo-append"),
    ("remove the rows a file added", "undo-append"),
    ("take back an append", "undo-append"),
    # One sheet of a workbook.
    ("read the second tab of an excel workbook", "pick-sheet"),
    ("pick a sheet from an xlsx", "pick-sheet"),
    ("import one tab of a workbook", "pick-sheet"),
    # Heading and title rows.
    ("the header row is wrong", "fix-heading-row"),
    ("skip title rows at the top of a csv", "fix-heading-row"),
    ("the file has two title rows above the table", "fix-heading-row"),
    # The opposite job keeps routing to append-rows.
    ("append a new file to a dataset", "append-rows"),
]


def _how(goal: str) -> str | None:
    data, _ = how_cmd.how(Invocation(command_id="how", positionals={"goal": goal}))
    return str(data["recipe"]["id"]) if data["matched"] else None  # type: ignore[index]


@pytest.mark.parametrize(("goal", "expected"), _GOALS, ids=[goal for goal, _ in _GOALS])
def test_goal_routes_to_its_recipe(goal: str, expected: str) -> None:
    assert _how(goal) == expected
