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
    ("pull data from a REST API on a schedule", "dataset.create"),
    ("connect a REST API", "connector.connection.create"),
    ("elasticsearch", "connector.connection.create"),
    ("group dashboards into a collection", "collection.create"),
    ("share a set of dashboards", "collection.share"),
    ("which collections hold my dashboard", "collection.for-dashboard"),
    ("who opened my dashboard", "dashboard.engagement.get"),
    ("remind people to look at the dashboard", "dashboard.engagement.remind"),
    ("use my own data on a template", "dashboard.own-data.start"),
    ("retry the failed agent run", "agent.run.retry"),
    ("which sub agents ran in this run", "agent.run.instance.list"),
    ("show the transcript of one agent in the run", "agent.run.instance.transcript"),
    ("which objects is the run working on", "agent.run.units.list"),
    ("that answer was the wrong kind of request", "agent.message.set-request-kind"),
    ("rename a step in the plan proposal", "agent.plan.edit-proposal"),
]


def _top_ids(goal: str) -> list[str]:
    result = find_schemas(goal)
    matches = [*result["matches"], *result.get("suggestions", [])]
    return [str(m["command_id"]) for m in matches][:3]


@pytest.mark.parametrize(("goal", "expected"), PHRASINGS)
def test_a_user_phrasing_reaches_its_command(goal: str, expected: str) -> None:
    assert expected in _top_ids(goal)
