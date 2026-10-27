"""``schema find`` returns what picks and calls a command; ``--full`` returns everything.

The agent reads a find's whole result into its context, then acts on one or two
matches by id. Each match was 10-11 keys, with a nested JSON Schema per field
and the near misses listed twice (``matches`` and ``suggestions``).
"""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.testing import make_runner

_PARTIAL_QUERY = "create dashboard from dataset"  # no command carries every word
_EXACT_QUERY = "join two datasets"


def _find(*args: str) -> dict[str, Any]:
    result = make_runner().invoke(["schema", "find", *args, "-o", "json"])
    assert result.exit_code == 0, result.output
    data: dict[str, Any] = json.loads(result.stdout)["data"]
    return data


def test_a_match_carries_the_id_summary_and_example_to_call_it() -> None:
    match = _find(_EXACT_QUERY)["matches"][0]
    assert match["command_id"] == "view.transform.join"
    assert match["summary"]
    assert match["agent_example"].startswith("mammoth view transform join")
    assert match["mutation_class"] and match["confirmation"]
    assert [f["name"] for f in match["accepted_fields"]]


def test_a_match_leaves_out_what_schema_get_returns() -> None:
    for match in _find(_EXACT_QUERY)["matches"] + _find(_PARTIAL_QUERY)["matches"]:
        for key in ("full_schema_command", "known_restrictions", "matched_on"):
            assert key not in match
        for field in match.get("accepted_fields", []):
            assert set(field) <= {"name", "type", "required", "enum", "schema"}


def test_an_object_field_keeps_its_nested_shape() -> None:
    match = _find("generate a dashboard from a view")["matches"][0]
    assert match["command_id"] == "dashboard.v3.generate"
    (body,) = [field for field in match["accepted_fields"] if field["name"] == "body"]
    assert body["type"] == "GenerateDashboardV3Spec"
    assert "dataview_id" in body["schema"]["$defs"]["GenerateDashboardV3Params"]["properties"]


def test_near_misses_are_listed_once_as_partial_matches() -> None:
    data = _find(_PARTIAL_QUERY)
    assert data["total_matches"] == 0
    assert "suggestions" not in data
    assert data["matches"] and all(match["partial"] for match in data["matches"])
    assert "suggestions" not in data["hint"]


def test_the_default_result_is_far_smaller_than_full() -> None:
    lean = json.dumps(_find(_PARTIAL_QUERY))
    full = json.dumps(_find("--full", _PARTIAL_QUERY))
    assert len(lean) < len(full) / 2


def test_full_returns_the_complete_shape() -> None:
    data = _find("--full", _PARTIAL_QUERY)
    assert data["suggestions"]
    match = data["matches"][0]
    assert match["full_schema_command"] == f"mammoth schema get {match['command_id']}"
    assert any("schema" in field for m in data["matches"] for field in m.get("accepted_fields", []))


def test_several_goals_are_trimmed_too() -> None:
    goals = _find(f"{_EXACT_QUERY}; {_PARTIAL_QUERY}")["goals"]
    assert len(goals) == 2
    assert all("full_schema_command" not in m for goal in goals for m in goal["matches"])
    assert "suggestions" not in goals[1]


def test_a_purpose_word_the_command_text_lacks_still_finds_it() -> None:
    # No automation command says "disable"; it is an update of the automation.
    data = _find("disable an automation")
    assert data["total_matches"] > 0
    assert data["matches"][0]["command_id"] == "automation.update"
