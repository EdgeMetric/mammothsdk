"""``schema find`` is graded by a table of how users word a goal, not by command names."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.schema import find_schemas

#: (what a user says, the command that must be among the first three matches)
PHRASINGS = [
    ("put my view in a managed postgres database", "view.export.publish-db"),
    ("send this view to a postgres table", "view.export.publish-db"),
    ("write this view into our sql database", "view.export.publish-db"),
    ("publish to mysql", "view.export.mysql"),
    ("make a live link to share the data", "view.export.live-link"),
    ("give me a link that always shows the latest data", "view.export.live-link"),
    ("change a column from number to text", "view.transform.convert-type"),
    ("make customer id text", "view.transform.convert-type"),
    ("total of quantity times unit price without changing anything", "view.data.aggregate"),
    ("sum revenue by region without editing the view", "view.data.aggregate"),
    ("join two tables", "view.transform.join"),
    ("remove duplicate rows", "view.transform.discard-duplicates"),
    ("filter rows where region is West", "view.transform.filter"),
    ("keep only rows from last year", "view.transform.filter"),
    ("rename a column", "view.transform.rename-columns"),
    ("sort the table by date newest first", "view.transform.sort"),
    ("split a full name column into first and last name", "view.transform.split"),
    ("remove a column i do not need", "view.transform.delete-columns"),
    ("fill empty cells with zero", "view.transform.fill-missing"),
    ("pivot months into columns", "view.transform.pivot"),
    ("upload a csv file", "file.upload"),
    ("export the view as a csv", "view.export.csv"),
    ("list my projects", "project.list"),
    ("delete a dataset", "dataset.delete"),
    ("schedule a daily refresh", "automation.create"),
    ("make a dashboard from this data", "dashboard.v3.generate"),
]

#: Goals the ranking misses today. ``strict`` xfail: the day one starts ranking, this
#: fails and the goal moves into ``PHRASINGS`` above.
KNOWN_MISSES = [
    ("show me the first rows of a view", "view.data.get"),
    ("check who i am signed in as", "auth.status"),
    ("undo a transform step", "view.task.delete"),
    ("count rows per category", "view.data.aggregate"),
]


def _top_ids(goal: str) -> list[str]:
    result = find_schemas(goal)
    matches = [*result["matches"], *result.get("suggestions", [])]
    return [str(m["command_id"]) for m in matches][:3]


@pytest.mark.parametrize(("goal", "expected"), PHRASINGS)
def test_a_user_phrasing_reaches_its_command(goal: str, expected: str) -> None:
    assert expected in _top_ids(goal)


@pytest.mark.xfail(strict=True, reason="schema find does not rank this goal in its top three yet")
@pytest.mark.parametrize(("goal", "expected"), KNOWN_MISSES)
def test_a_known_miss_is_tracked(goal: str, expected: str) -> None:
    assert expected in _top_ids(goal)
