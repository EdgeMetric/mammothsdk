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
    ("read view rows data", "view.data.get"),
    ("show rows of a view", "view.data.get"),
    ("preview rows", "view.data.get"),
    ("show me the first rows of a view", "view.data.get"),
    ("list my projects", "project.list"),
    ("delete a dataset", "dataset.delete"),
    ("schedule a daily refresh", "automation.create"),
    ("make a dashboard from this data", "dashboard.v3.generate"),
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
    ("approve the agent plan", "agent.plan.approve"),
    ("run it the plan the agent proposed", "agent.plan.approve"),
    ("skip one step of the agent plan", "agent.plan.skip"),
    ("discard the agent plan", "agent.plan.discard"),
    ("resume an interrupted collection upload", "collection.active-job"),
    ("attach a workbook to the chat", "dashboard.attachment-create"),
    ("make a dataset from each sheet of my excel file", "file.multi-sheet-extract"),
    ("see how each sheet of my excel workbook reads", "file.multi-sheet-preview"),
    ("archive this workflow", "workflow.archive"),
    ("save my workflow changes", "workflow.save"),
    ("disconnect an app I authorised", "auth.connected-apps.revoke"),
    ("which workspace is this token for", "workspace.current"),
    ("register an OAuth client", "workspace.oauth-client.create"),
    ("export explore card as image", "view.explore-panel.export-image"),
    ("save explore chart as png", "view.explore-panel.export-image"),
]

#: Goals the ranking misses today. ``strict`` xfail: the day one starts ranking, this
#: fails and the goal moves into ``PHRASINGS`` above.
KNOWN_MISSES = [
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
