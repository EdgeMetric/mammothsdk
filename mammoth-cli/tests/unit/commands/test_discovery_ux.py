"""Focused coverage for help navigation and compact schema discovery."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.registry import _schema_find
from mammoth_cli.commands.schema import _COMMAND_DISCOVERY_PURPOSES, find_schemas, schema_entries
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import make_runner


def test_schema_find_returns_compact_matches_with_a_full_schema_route() -> None:
    result = find_schemas("view transform")
    matches = result["matches"]

    assert matches
    sample = next(
        match for match in matches if match["command_id"] == "view.transform.bulk-replace"
    )
    assert set(sample) == {
        "command_id",
        "command_path",
        "mutation_class",
        "confirmation",
        "full_schema_command",
    }
    assert sample["full_schema_command"].startswith(
        "mammoth schema get view.transform.bulk-replace"
    )
    assert "input_schema" not in sample
    assert result["total_matches"] >= len(matches)


def test_schema_find_cli_accepts_a_multiword_query() -> None:
    result = make_runner().invoke(
        ["schema", "find", "view transform", "--output", "json", "--no-input"]
    )

    assert result.exit_code == 0, result.output
    assert "view.transform.bulk-replace" in result.output


def test_schema_find_matches_resource_purpose_not_just_command_tokens() -> None:
    matches = find_schemas("upload csv")["matches"]

    assert matches[0]["command_id"] == "file.upload"


def test_schema_find_prioritizes_path_matches_and_caps_broad_results() -> None:
    result = find_schemas("view transform")

    assert result["total_matches"] > len(result["matches"])
    assert result["truncated"] is True
    assert all(match["command_id"].startswith("view.transform.") for match in result["matches"])
    assert len(result["matches"]) == 20


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        # A cold agent states the goal, not Mammoth's task name. Each of these
        # returned nothing (or the wrong command) before 2.0.37.
        ("merge two datasets", "view.transform.join"),
        ("combine datasets", "view.transform.join"),
        ("combine two views", "view.transform.join"),
        ("add columns from another dataset", "view.transform.join"),
        ("vlookup", "view.transform.join"),
        ("reference table", "view.transform.lookup"),
        ("dedupe", "view.transform.discard-duplicates"),
        ("remove duplicates", "view.transform.discard-duplicates"),
        ("keep rows", "view.transform.filter"),
        ("delete rows", "view.transform.filter"),
        ("summarise", "view.transform.ai"),
        ("aggregate", "view.transform.pivot"),
        ("calculate", "view.transform.math"),
        ("running total", "view.transform.window"),
        ("rank", "view.transform.window"),
        ("top n", "view.transform.limit-rows"),
        ("unpivot", "view.transform.unnest"),
        ("concatenate", "view.transform.combine-columns"),
        ("combine columns", "view.transform.combine-columns"),
        ("standardise", "view.transform.bulk-replace"),
        ("uppercase", "view.transform.text"),
        ("fill blanks", "view.transform.fill-missing"),
        ("parse date", "view.transform.convert-type"),
        ("classify", "view.transform.ai"),
        ("rename column", "view.transform.rename-columns"),
        ("change column name", "view.transform.rename-columns"),
        ("copy column", "view.transform.copy-columns"),
        ("sort rows by revenue", "view.transform.sort"),
        ("sort by date descending", "view.transform.sort"),
        ("top 10 rows", "view.transform.limit-rows"),
        ("days between two dates", "view.transform.date-diff"),
        ("append rows", "file.upload"),
        ("automation refresh dataset", "automation.create"),
        ("schedule a daily refresh", "automation.create"),
        ("run every week automatically", "automation.create"),
        # 2.0.71: a board is built from a sentence, never hand-authored JSON.
        ("create dashboard from a view", "dashboard.v3.generate"),
        ("build combined dashboard", "dashboard.v3.generate"),
        ("add a chart to the dashboard", "dashboard.chat.edit"),
        # Workflow Zoo QA 10-02: the agent could not find how to name a workflow or
        # propose its shape for review.
        ("rename workflow", "workflow.update"),
        ("name workflow", "workflow.create"),
        ("propose changes workflow", "workflow.canvas"),
        ("suggest changes to a workflow", "workflow.canvas"),
        ("sketch a workflow", "workflow.canvas"),
    ],
)
def test_schema_find_resolves_goal_phrasing_to_the_transform(query: str, command_id: str) -> None:
    matches = find_schemas(query)["matches"]

    assert matches, query
    assert matches[0]["command_id"] == command_id


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        # An agent plans by stating the whole goal, not Mammoth's task names;
        # each of these returned nothing (or the wrong command) as only a
        # `suggestions` entry before this fix -- the right command must now
        # be `matches[0]`.
        ("save view result to a new dataset", "view.export.dataset"),
        ("create a dataset from an existing view", "view.export.dataset"),
        ("combine two datasets by appending rows", "view.export.dataset"),
        ("union append stack rows from two existing views", "view.export.dataset"),
        ("combine monthly datasets as rows", "view.export.dataset"),
        ("join customer details into orders", "view.transform.join"),
        ("create a new view from an existing dataset", "view.create"),
        ("list datasets in a project", "dataset.list"),
        ("deduplicate rows by order id", "view.transform.discard-duplicates"),
        ("add a column with a constant value", "view.transform.set-values"),
        ("calculate revenue as quantity times price", "view.transform.math"),
        ("group and sum sales by store and month", "view.data.aggregate"),
        ("build dashboard from a view", "dashboard.v3.generate"),
        # Different phrasings of the same goals above, proving the fix is
        # general vocabulary (purpose text/synonyms/stopwords), not these
        # exact strings.
        ("copy this view into a new dataset", "view.export.dataset"),
        ("please create a new view using an existing dataset", "view.create"),
        ("remove duplicate rows for each order id", "view.transform.discard-duplicates"),
        ("quantity times price as revenue", "view.transform.math"),
        ("sum sales by store and month", "view.data.aggregate"),
    ],
)
def test_schema_find_resolves_natural_goal_phrasing_to_first_match(
    query: str, command_id: str
) -> None:
    matches = find_schemas(query)["matches"]

    assert matches, query
    assert matches[0]["command_id"] == command_id


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        # A key names the join column: appending rows is the wrong read of
        # "combine", and must not win once a key is named.
        ("combine two datasets on a key", "view.transform.join"),
    ],
)
def test_schema_find_still_prefers_join_when_a_key_is_named(query: str, command_id: str) -> None:
    matches = find_schemas(query)["matches"]

    assert matches, query
    assert matches[0]["command_id"] == command_id


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        # Data words (sales, warehouse, revenue) are dropped from the
        # required terms (see test_schema_find_still_resolves_a_goal_when_a_
        # data_word_rides_along), but these two still don't reach a full
        # match on any command, so they land in suggestions; the
        # board-by-sentence commands must still lead them.
        ("build a board showing sales by warehouse", "dashboard.v3.generate"),
        ("change the dashboard to show revenue by month", "dashboard.chat.edit"),
    ],
)
def test_schema_find_suggests_the_intent_command_for_a_board_request(
    query: str, command_id: str
) -> None:
    result = find_schemas(query)

    assert result["suggestions"][0]["command_id"] == command_id


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        # A business/data noun (a column or table name from the caller's own
        # data) riding along in an otherwise-complete goal must not sink the
        # match: find_schemas drops a term no command's curated discovery
        # text is about (see _command_vocabulary_tokens) before requiring
        # every term to be covered.
        ("remove duplicate suppliers by supplier number", "view.transform.discard-duplicates"),
        ("filter the shipments to late ones", "view.transform.filter"),
        # Matches whatever "total per group" already resolves to today
        # (view.transform.pivot) -- "supplier" is the data word riding
        # along, not a reason to change that ranking.
        ("total spend per supplier", "view.transform.pivot"),
    ],
)
def test_schema_find_still_resolves_a_goal_when_a_data_word_rides_along(
    query: str, command_id: str
) -> None:
    matches = find_schemas(query)["matches"]

    assert matches, query
    assert matches[0]["command_id"] == command_id


def test_every_view_transform_has_a_plain_language_discovery_purpose() -> None:
    transforms = {
        str(record["command_id"])
        for record in load_commands()
        if str(record["command_id"]).startswith("view.transform.")
        and record.get("disposition") != "alias"
    }

    assert transforms
    assert transforms <= set(_COMMAND_DISCOVERY_PURPOSES)


def test_schema_find_without_a_full_match_suggests_near_misses_and_the_menu() -> None:
    # "union two views" now genuinely resolves to view.export.dataset (its
    # own goal-phrasing coverage, see test_schema_find_resolves_natural_goal_
    # phrasing_to_first_match) -- a real fix, not a regression. A bare number
    # like "three" would be dropped as a data word (see
    # _command_vocabulary_tokens), so "sort" stands in: it's genuine CLI
    # vocabulary (view.transform.sort's own purpose text) that view.export.
    # dataset's text doesn't carry, so it keeps this a real partial-coverage
    # near miss instead of colliding with that improvement.
    result = find_schemas("union sort views")

    assert result["matches"] == []
    assert result["total_matches"] == 0
    suggested = [item["command_id"] for item in result["suggestions"]]
    assert "file.upload" in suggested and "view.export.dataset" in suggested
    assert all(item["matched_terms"] for item in result["suggestions"])
    assert all(
        item["full_schema_command"].startswith("mammoth schema get ")
        for item in result["suggestions"]
    )
    # T1-R-06: when suggestions exist, the hint presents them as candidates
    # to try rather than the harsher "no command matched, try fewer or other
    # words" framing (that framing is reserved for zero suggestions at all).
    assert "candidates" in result["hint"]


def test_schema_find_with_a_match_carries_no_suggestions() -> None:
    result = find_schemas("join")

    assert "suggestions" not in result
    assert "hint" not in result


def test_schema_find_rejects_an_empty_query() -> None:
    with pytest.raises(CliError, match="must contain") as error:
        _schema_find(Invocation(command_id="schema.find", extra_args=["   "]))

    assert error.value.code == "empty_search_query"


def test_schema_find_without_a_semicolon_is_unchanged() -> None:
    data, _ = _schema_find(Invocation(command_id="schema.find", extra_args=["view transform"]))

    assert data == find_schemas("view transform")
    assert "goals" not in data


def test_schema_find_splits_a_semicolon_query_into_several_goals() -> None:
    query = "join customers onto orders; remove duplicate rows; build a dashboard"
    data, _ = _schema_find(Invocation(command_id="schema.find", extra_args=[query]))

    assert list(data) == ["goals"]
    goals = data["goals"]
    assert [goal["goal"] for goal in goals] == [
        "join customers onto orders",
        "remove duplicate rows",
        "build a dashboard",
    ]
    # Each goal carries its own single-goal result shape.
    for goal in goals:
        assert set(goal) >= {"goal", "query", "matches", "total_matches", "truncated"}
    # More than one goal: inline accepted_fields/agent_example caps to the
    # top 1 match (or suggestion) per goal, so the envelope stays small.
    for goal in goals:
        entries = goal["matches"] or goal.get("suggestions") or []
        for entry in entries[1:]:
            assert "accepted_fields" not in entry
            assert "agent_example" not in entry
        if entries:
            assert "accepted_fields" in entries[0] or "agent_example" in entries[0]


def test_schema_find_semicolon_query_strips_and_drops_empty_goals() -> None:
    data, _ = _schema_find(
        Invocation(command_id="schema.find", extra_args=["  join two views ; ; remove duplicates "])
    )

    assert [goal["goal"] for goal in data["goals"]] == ["join two views", "remove duplicates"]


def test_schema_find_rejects_an_all_empty_semicolon_query() -> None:
    with pytest.raises(CliError, match="must contain") as error:
        _schema_find(Invocation(command_id="schema.find", extra_args=[" ; ; "]))

    assert error.value.code == "empty_search_query"


def test_schema_find_caps_the_number_of_goals_per_call() -> None:
    query = ";".join(f"goal {i}" for i in range(13))
    with pytest.raises(CliError, match="at most 12") as error:
        _schema_find(Invocation(command_id="schema.find", extra_args=[query]))

    assert error.value.code == "too_many_goals"


def test_root_help_groups_commands_by_task_and_explains_discovery() -> None:
    result = make_runner().invoke(["--help"])

    assert result.exit_code == 0, result.output
    for panel in (
        "Start here",
        "Discover commands",
        "Work with data",
        "Build and share",
        "Automate and integrate",
        "CLI and agent tools",
    ):
        assert panel in result.output
    assert "mammoth schema find QUERY" in result.output


def test_schema_group_help_explains_compact_and_full_discovery() -> None:
    result = make_runner().invoke(["schema", "--help"])

    assert result.exit_code == 0, result.output
    assert "Find concise command input guidance or fetch full schemas." in result.output
    assert "find" in result.output


def test_leaf_help_separates_global_options_by_purpose() -> None:
    result = make_runner().invoke(["schema", "find", "--help"])

    assert result.exit_code == 0, result.output
    for panel in ("Output and automation", "Context and timeouts", "Request input", "Safety"):
        assert panel in result.output


# Proposing a workflow's shape must never pull in plain view work: "add a view"
# is a build, not a proposal.
@pytest.mark.parametrize("query", ["add a view", "rename view", "create view"])
def test_view_work_does_not_resolve_to_a_workflow_proposal(query: str) -> None:
    matches = find_schemas(query)["matches"]

    assert "workflow.canvas" not in [match["command_id"] for match in matches[:3]], query


def test_workflow_canvas_says_it_proposes_structure_for_review_and_shows_the_ops() -> None:
    entry = next(e for e in schema_entries() if e["command_id"] == "workflow.canvas")
    preconditions = entry["preconditions"]

    assert "review and Save" in preconditions
    assert "cannot add filters" in preconditions
    assert "proposed_changes" in entry["agent_example"]
    # A whole shape in one call: a later change points at an earlier one's ref.
    assert "view_ref" in preconditions and '"view_ref": "urgent"' in entry["agent_example"]


# `workflow canvas` edits its workflow's canvas state, but a call that only proposes changes
# (sets canvas_state.proposed_changes) builds nothing until the user Saves on the canvas. The
# manifest says so as data, for callers that gate in-place edits behind an approval.
def test_workflow_canvas_declares_which_input_only_proposes() -> None:
    record = next(r for r in load_commands() if r["command_id"] == "workflow.canvas")

    assert record["edits_target"] is True
    assert record["proposal_input"] == "canvas_state.proposed_changes"
