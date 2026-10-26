"""What a new user or agent types into ``schema find`` finds the right command in the top 3.

Each row is a goal in plain words and the command id that must be among the first
three ``matches``. The rows cover the first things people ask for: reading rows,
the column and row transforms, joins, exports, scheduling, dashboards, uploads,
listing, undo, deleting, and sign-in checks.
"""

from __future__ import annotations

import pytest

from mammoth_cli.commands.schema.find import find_schemas

QUERIES: list[tuple[str, str | tuple[str, ...]]] = [
    # reading rows
    ("show rows of a view", ("view.data.get", "view.data.query")),
    ("read view rows data", "view.data.get"),
    ("preview rows", "view.data.get"),
    ("query a view with a filter and get rows back", "view.data.query"),
    # filtering and column edits
    ("filter rows", "view.transform.filter"),
    ("keep only rows where region is West", "view.transform.filter"),
    ("delete a column", "view.transform.delete-columns"),
    ("rename column", "view.transform.rename-columns"),
    ("add a column", "view.transform.add-column"),
    ("add a calculated column", ("view.transform.math", "view.transform.add-column")),
    ("convert column type", "view.transform.convert-type"),
    ("change a text column to a number", "view.transform.convert-type"),
    ("math on two columns", "view.transform.math"),
    ("multiply price by quantity", "view.transform.math"),
    # reshaping
    ("pivot table", "view.transform.pivot"),
    ("group by region and sum revenue", ("view.transform.pivot", "view.data.aggregate")),
    ("join two datasets", "view.transform.join"),
    ("lookup a value from another table", "view.transform.lookup"),
    ("remove duplicates", "view.transform.discard-duplicates"),
    ("sort rows", "view.transform.sort"),
    ("keep the first 100 rows", "view.transform.limit-rows"),
    ("replace values in a column", ("view.transform.replace", "view.transform.bulk-replace")),
    ("fill missing values", "view.transform.fill-missing"),
    # dates and text
    ("get the year from a date", "view.transform.extract-date"),
    ("days between two dates", "view.transform.date-diff"),
    ("add 30 days to a date", "view.transform.increment-date"),
    ("make text uppercase", "view.transform.text"),
    ("trim spaces and clean text", "view.transform.text"),
    ("split a column on a comma", "view.transform.split"),
    # export
    ("download data as csv", "view.export.csv"),
    ("export the view to csv", "view.export.csv"),
    ("export a view into a new dataset", "view.export.dataset"),
    # scheduling and automation
    ("schedule daily export", ("schedule.create", "automation.create")),
    ("run something every day automatically", ("schedule.create", "automation.create")),
    # dashboards
    ("list my dashboards", "dashboard.list"),
    ("share dashboard with user", "dashboard.share"),
    ("delete a dashboard", "dashboard.delete"),
    # files and data in
    ("upload a file", "file.upload"),
    ("create a new dataset from csv upload", ("dataset.create", "file.upload")),
    ("append new data to a dataset", ("batch.create", "dataset.create")),
    # listing
    ("list my projects", "project.list"),
    ("list datasets", "dataset.list"),
    ("list views", "view.list"),
    # undo and delete
    ("undo a transform step", "view.task.delete"),
    ("remove the last step from a view", "view.task.delete"),
    ("delete a dataset", "dataset.delete"),
    ("delete a view", "view.delete"),
    # auth and health
    ("check who i am signed in as", "auth.status"),
    ("log in", "auth.login"),
    ("check my setup", "doctor"),
]


@pytest.mark.parametrize(("query", "expected"), QUERIES, ids=[q for q, _ in QUERIES])
def test_a_goal_in_plain_words_finds_its_command_in_the_top_three(
    query: str, expected: str | tuple[str, ...]
) -> None:
    wanted = {expected} if isinstance(expected, str) else set(expected)
    top = [m["command_id"] for m in find_schemas(query)["matches"][:3]]
    assert wanted & set(top), f"{query!r} -> {top}, wanted one of {sorted(wanted)}"


def test_the_table_has_at_least_forty_distinct_goals() -> None:
    assert len({query for query, _ in QUERIES}) >= 40
