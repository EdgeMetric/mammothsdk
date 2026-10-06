"""Every ``fix`` hint a data read carries names a command the manifest has.

An agent runs a hint as written. A hint that names a command that does not exist,
passes an input field the command does not take, or is not valid shell sends the
agent on a failed call. The warnings are produced by the real code from real rows;
each hint is parsed the way a shell would and checked against the command manifest.
"""

from __future__ import annotations

import json
import re
import shlex
from typing import Any

import pytest

from mammoth_cli.commands.view import COLUMN_CHECK_ISSUES
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.dataset_health import with_dataset_health
from mammoth_cli.services.command_contract import resolve_command_contract
from mammoth_cli.services.data_quality import column_warnings

_COMMAND = re.compile(r"mammoth((?: [a-z][a-z-]*)+)")


def _assert_real_command(hint: str) -> list[str]:
    """Check each ``mammoth ...`` command in ``hint``; return the command ids found."""
    by_path = {record["command_path"]: record for record in load_commands()}
    found: list[str] = []
    commands = list(_COMMAND.finditer(hint))
    assert commands, f"no mammoth command in hint: {hint}"
    for index, match in enumerate(commands):
        words = match.group(1).split()
        path = next(
            (
                " ".join(words[:n])
                for n in range(len(words), 0, -1)
                if " ".join(words[:n]) in by_path
            ),
            None,
        )
        assert path is not None, f"hint names no command in the manifest: {match.group(0)!r}"
        record = by_path[path]
        found.append(record["command_id"])
        end = commands[index + 1].start() if index + 1 < len(commands) else len(hint)
        _assert_input_fields(record["command_id"], hint[match.start() : end])
    return found


def _assert_input_fields(command_id: str, segment: str) -> None:
    tokens = shlex.split(segment.split("; then", 1)[0])
    if "--input" not in tokens:
        return
    document = json.loads(tokens[tokens.index("--input") + 1])
    contract = resolve_command_contract(command_id)
    assert contract is not None
    if contract.accepts_extra:
        return
    unknown = set(document) - contract.declared_input_names
    assert not unknown, f"{command_id} does not take input field(s) {sorted(unknown)}"


def _by_issue(warnings: list[dict[str, Any]], issue: str) -> dict[str, Any]:
    (warning,) = [w for w in warnings if w["issue"] == issue]
    return warning


def _text_rows(column: str, values: list[object]) -> list[dict[str, object]]:
    return [{column: value} for value in values]


def test_numbers_stored_as_text_names_convert_type() -> None:
    rows = _text_rows("price", ["10", "20", "30", "40", "N/A"])
    warning = _by_issue(
        column_warnings(rows, {"price": "TEXT"}, view_id=7), "numbers_stored_as_text"
    )
    assert _assert_real_command(warning["fix"]) == ["view.transform.convert-type"]


def test_dates_stored_as_text_names_convert_type() -> None:
    rows = _text_rows("day", ["2026-01-02", "2026-02-03", "2026-03-04", "2026-04-05"])
    warning = _by_issue(column_warnings(rows, {"day": "TEXT"}, view_id=7), "dates_stored_as_text")
    assert _assert_real_command(warning["fix"]) == ["view.transform.convert-type"]


def test_dates_stored_as_text_on_a_read_only_read_names_no_command() -> None:
    rows = _text_rows("day", ["2026-01-02", "2026-02-03", "2026-03-04", "2026-04-05"])
    warnings = column_warnings(rows, {"day": "TEXT"}, view_id=7, read_only=True)
    assert "fix" not in _by_issue(warnings, "dates_stored_as_text")


def test_variant_spellings_names_bulk_replace() -> None:
    rows = _text_rows("brand", ["PEPSI", "Pepsi ", "pepsi", "Pepsi", "Coke", "Sprite"])
    warning = _by_issue(column_warnings(rows, {"brand": "TEXT"}, view_id=7), "variant_spellings")
    assert _assert_real_command(warning["fix"]) == ["view.transform.bulk-replace"]


def test_renamed_label_names_bulk_replace() -> None:
    rows = [
        {"store": "Riverside", "day": "2026-01-01"},
        {"store": "Riverside", "day": "2026-01-02"},
        {"store": "Riverside Mall", "day": "2026-02-01"},
        {"store": "Riverside Mall", "day": "2026-02-02"},
    ]
    warnings = column_warnings(rows, {"store": "TEXT", "day": "DATE"}, view_id=7)
    assert _assert_real_command(_by_issue(warnings, "renamed_label")["fix"]) == [
        "view.transform.bulk-replace"
    ]


def test_duplicate_rows_names_discard_duplicates() -> None:
    warnings = column_warnings([{"a": "1"}, {"a": "1"}], {"a": "TEXT"}, view_id=7, dataset_id=9)
    assert _assert_real_command(_by_issue(warnings, "duplicate_rows")["fix"]) == [
        "view.transform.discard-duplicates"
    ]


def test_blank_values_in_the_only_figure_names_filter() -> None:
    rows = [
        {"market": "A", "cpm": "150"},
        {"market": "A", "cpm": None},
        {"market": "A", "cpm": "145"},
    ]
    types = {"market": "TEXT", "cpm": "NUMERIC"}
    warning = _by_issue(column_warnings(rows, types, view_id=7, dataset_id=9), "blank_values")
    assert _assert_real_command(warning["fix"]) == ["view.transform.filter"]


def test_blank_values_that_need_a_decision_name_no_command() -> None:
    rows = [{"a": "1", "b": "5"}, {"a": None, "b": "6"}, {"a": "3", "b": "7"}]
    warning = _by_issue(
        column_warnings(rows, {"a": "NUMERIC", "b": "NUMERIC"}, view_id=7, dataset_id=9),
        "blank_values",
    )
    assert "fix" not in warning


def test_every_checked_issue_has_a_test_above() -> None:
    covered = {
        "numbers_stored_as_text",
        "dates_stored_as_text",
        "variant_spellings",
        "renamed_label",
        "duplicate_rows",
        "blank_values",
    }
    assert set(COLUMN_CHECK_ISSUES) == covered


def test_unhealthy_dataset_with_a_stored_suggestion_names_interpretation_commands() -> None:
    record = {
        "id": 3108,
        "status": "has_unstructured_data",
        "additional_info": {
            "interpretation": {
                "instruction_suggestions": ["Skip preamble rows, row 5 is the header"]
            }
        },
    }
    fix = with_dataset_health(record)["dataset_health"][0]["fix"]
    assert _assert_real_command(fix) == [
        "dataset.interpretation.preview",
        "dataset.interpretation.confirm",
    ]


def test_unhealthy_dataset_without_a_suggestion_names_the_reading_commands() -> None:
    record = {"id": 3108, "status": "need_action"}
    fix = with_dataset_health(record)["dataset_health"][0]["fix"]
    assert _assert_real_command(fix) == ["dataset.get", "dataset.broken-rows.list"]


@pytest.mark.parametrize("status", ["ready", "something_new"])
def test_a_healthy_or_unclassified_dataset_names_no_fix(status: str) -> None:
    entry = with_dataset_health({"datasets": [{"id": 1, "status": status}]})["dataset_health"][0]
    assert "fix" not in entry
