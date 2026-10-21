"""``view conditional-format`` create/replace/delete-all through the real CLI.

Expected wire bodies come from the backend contract in
``mvc-service/apiv2/apiv2/conditional_formatting/schema.py``: a RULE payload is
``{"FORMAT": {name, color, applies_to: row|columns, column_ids: JSON string},
"CONDITION": {"OR"|"AND": [{<internal column>: {<OP>: {"VALUE": v}}}]}}`` and
``column_ids`` is ``'[]'`` for ``row`` and a non-empty list for ``columns``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.services import conditional_format as cf
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_CREATE = "mammoth.api.dataviews.DataviewsAPI.conditional_format_create"
_REPLACE = "mammoth.api.dataviews.DataviewsAPI.conditional_format_replace"
_DELETE = "mammoth.api.dataviews.DataviewsAPI.conditional_format_delete"
_FIND_DATASET = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"

_VIEW = {
    "id": 7,
    "metadata": [
        {"display_name": "Q1", "internal_name": "column_q1", "type": "NUMERIC"},
        {"display_name": "Q2", "internal_name": "column_q2", "type": "NUMERIC"},
        {"display_name": "Status", "internal_name": "column_st", "type": "TEXT"},
    ],
}
_ARGS = ["--project", "180", "--output", "json", "--no-input"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_GET] = _VIEW
    fake_service.responses[_FIND_DATASET] = 9  # the read-back lists by view id alone
    return fake_service


def _run(args: list[str], payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    argv = [*args, *_ARGS]
    if payload is not None:
        argv += ["--input", json.dumps(payload)]
    result = make_runner().invoke(argv)
    start = result.output.find("{")
    assert start != -1, result.output
    return result.exit_code, json.loads(result.output[start:])


def _writes(service: FakeMammothService, symbol: str) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in service.call_log if name == symbol]


# ── the typed form: one RULE per column, built against the view's metadata ──


def test_typed_threshold_sends_one_rule_per_column_on_internal_names(
    service: FakeMammothService,
) -> None:
    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Q1", "Q2"], "operator": "<", "value": 55, "color": "red"},
    )

    assert code == 0, envelope
    sent = [call["rule"] for call in _writes(service, _CREATE)]
    assert sent == [
        {
            "cf_type": "RULE",
            "payload": {
                "FORMAT": {
                    "name": "Q1 < 55",
                    "color": "red",
                    "applies_to": "columns",
                    "column_ids": '["column_q1"]',
                },
                "CONDITION": {"OR": [{"column_q1": {"LT": {"VALUE": 55}}}]},
            },
        },
        {
            "cf_type": "RULE",
            "payload": {
                "FORMAT": {
                    "name": "Q2 < 55",
                    "color": "red",
                    "applies_to": "columns",
                    "column_ids": '["column_q2"]',
                },
                "CONDITION": {"OR": [{"column_q2": {"LT": {"VALUE": 55}}}]},
            },
        },
    ]
    assert {call["dataset_id"] for call in _writes(service, _CREATE)} == {9}


def test_typed_threshold_reports_the_created_rule_ids_by_highest_sequence(
    service: FakeMammothService,
) -> None:
    """Each response is the whole rule map; the new rule is the one with the top SEQUENCE."""
    maps = iter(
        [
            {"old": {"SEQUENCE": 1}, "new1": {"SEQUENCE": 2}},
            {"old": {"SEQUENCE": 1}, "new1": {"SEQUENCE": 2}, "new2": {"SEQUENCE": 3}},
        ]
    )
    service.responses[_CREATE] = lambda _log: next(maps)

    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Q1", "Q2"], "operator": ">", "value": 1, "color": "green"},
    )

    assert code == 0, envelope
    assert envelope["data"]["created_rule_ids"] == ["new1", "new2"]
    assert envelope["data"]["rules_created"] == 2


def test_a_single_rule_returns_the_backends_rule_map_unwrapped(
    service: FakeMammothService,
) -> None:
    service.responses[_CREATE] = {"r1": {"SEQUENCE": 1}}
    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Q1"], "operator": ">", "value": 1, "color": "green"},
    )
    assert code == 0, envelope
    assert envelope["data"]["r1"] == {"SEQUENCE": 1}
    assert "created_rule_ids" not in envelope["data"]


def test_a_failure_midway_names_the_rules_already_created(
    service: FakeMammothService,
) -> None:
    answers: list[Any] = [
        {"r1": {"SEQUENCE": 1}},
        CliError(code="api_error", message="server said no", exit_status=1),
    ]

    def respond(_log: Any) -> Any:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    service.responses[_CREATE] = respond
    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Q1", "Q2"], "operator": ">", "value": 1, "color": "green"},
    )

    assert code == 1
    assert envelope["error"]["code"] == "api_error"
    assert "Rules already created before the failure: ['r1']" in envelope["error"]["message"]
    assert envelope["error"]["details"]["created_rule_ids"] == ["r1"]


def test_row_rule_ors_or_ands_the_columns_and_clears_column_ids(
    service: FakeMammothService,
) -> None:
    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {
            "columns": ["Q1", "Q2"],
            "operator": ">=",
            "value": 10,
            "color": "blue",
            "applies_to": "row",
            "match": "all",
            "name": "Both high",
        },
    )

    assert code == 0, envelope
    (call,) = _writes(service, _CREATE)
    assert call["rule"]["payload"] == {
        "FORMAT": {"name": "Both high", "color": "blue", "applies_to": "row", "column_ids": "[]"},
        "CONDITION": {
            "AND": [
                {"column_q1": {"GTE": {"VALUE": 10}}},
                {"column_q2": {"GTE": {"VALUE": 10}}},
            ]
        },
    }


def test_row_rule_defaults_to_any_match(service: FakeMammothService) -> None:
    _run(
        ["view", "conditional-format", "create", "7", "9"],
        {
            "columns": ["Q1", "Q2"],
            "operator": "=",
            "value": 0,
            "color": "blue",
            "applies_to": "row",
        },
    )
    (call,) = _writes(service, _CREATE)
    assert list(call["rule"]["payload"]["CONDITION"]) == ["OR"]


def test_per_column_rules_use_the_given_name_as_a_prefix(service: FakeMammothService) -> None:
    _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Q1"], "operator": "<", "value": 5, "color": "red", "name": "Low"},
    )
    (call,) = _writes(service, _CREATE)
    assert call["rule"]["payload"]["FORMAT"]["name"] == "Low: Q1"


def test_duplicate_column_names_make_one_rule(service: FakeMammothService) -> None:
    _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Q1", "Q1"], "operator": "<", "value": 5, "color": "red"},
    )
    assert len(_writes(service, _CREATE)) == 1


# ── refusals: invalid_rule is a usage error and nothing is sent ──


@pytest.mark.parametrize(
    ("payload", "code", "needle"),
    [
        ({"operator": "<", "color": "red"}, "invalid_rule", "needs 'columns'"),
        ({"columns": ["Q1"], "color": "red"}, "invalid_rule", "needs 'operator'"),
        ({"columns": ["Q1"], "operator": "<"}, "invalid_rule", "needs 'color'"),
        (
            {"columns": [], "operator": "<", "color": "red"},
            "invalid_rule",
            "'columns' must be a non-empty list",
        ),
        (
            {"columns": ["Nope"], "operator": "<", "value": 1, "color": "red"},
            "invalid_rule",
            "Unknown column(s): Nope",
        ),
        # The input contract (spec/manifests input_fields) rejects these shapes before the
        # service sees them.
        ({"columns": "Q1", "operator": "<", "color": "red"}, "invalid_input_field_type", None),
        (
            {"columns": ["Q1"], "operator": "<", "value": 1, "color": "red", "match": "most"},
            "invalid_input_field_type",
            None,
        ),
        (
            {"columns": ["Q1"], "operator": "<", "value": 1, "color": "red", "applies_to": "cell"},
            "invalid_input_field_type",
            None,
        ),
    ],
)
def test_bad_typed_input_is_a_usage_error_and_sends_nothing(
    service: FakeMammothService, payload: dict[str, Any], code: str, needle: str | None
) -> None:
    status, envelope = _run(["view", "conditional-format", "create", "7", "9"], payload)

    assert status == 2, envelope
    assert envelope["error"]["code"] == code
    if needle:
        assert needle in envelope["error"]["message"]
    assert _writes(service, _CREATE) == []


def test_match_and_applies_to_are_checked_by_the_service_when_called_directly() -> None:
    columns = {"Q1": "column_q1"}
    base = {"columns": ["Q1"], "operator": "<", "value": 1, "color": "red"}
    with pytest.raises(CliError) as bad_match:
        cf.build_rules({**base, "applies_to": "row", "match": "most"}, columns, {})
    assert bad_match.value.message == "match must be one of any, all; got 'most'."
    assert bad_match.value.exit_status == 2
    with pytest.raises(CliError) as bad_non_list:
        cf.build_rules({**base, "columns": "Q1"}, columns, {})
    assert bad_non_list.value.message == "'columns' must be a non-empty list of column names."


def test_unknown_column_hint_lists_the_views_display_names(service: FakeMammothService) -> None:
    _, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"columns": ["Nope"], "operator": "<", "value": 1, "color": "red"},
    )
    assert envelope["error"]["hint"] == "Use display names of the view's columns: Q1, Q2, Status"


def test_rule_and_typed_fields_cannot_be_mixed(service: FakeMammothService) -> None:
    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9"],
        {"rule": {"cf_type": "RULE"}, "columns": ["Q1"]},
    )
    assert code == 2
    assert envelope["error"]["code"] == "invalid_rule"
    assert _writes(service, _CREATE) == []


def test_neither_rule_nor_typed_fields_is_a_missing_field(service: FakeMammothService) -> None:
    code, envelope = _run(["view", "conditional-format", "create", "7", "9"], {"dataset_id": 9})
    assert code == 2
    assert envelope["error"]["code"] == "missing_field"


@pytest.mark.parametrize(
    ("fmt", "needle"),
    [
        (
            {"name": "n", "color": "red", "applies_to": "cell"},
            "applies_to must be one of row, columns",
        ),
        (
            {"name": "n", "color": "red", "applies_to": "row", "column_ids": '["c"]'},
            "column_ids must be '[]' when applies_to is 'row'",
        ),
        (
            {"name": "n", "color": "red", "applies_to": "columns"},
            "column_ids must not be '[]' when applies_to is 'columns'",
        ),
        (
            {"name": "n", "color": "red", "applies_to": "columns", "column_ids": "[]"},
            "column_ids must not be '[]' when applies_to is 'columns'",
        ),
    ],
)
def test_raw_rule_format_is_checked_like_the_backend_before_any_request(
    service: FakeMammothService, fmt: dict[str, Any], needle: str
) -> None:
    rule = {"cf_type": "RULE", "payload": {"FORMAT": fmt, "CONDITION": {"OR": []}}}
    code, envelope = _run(["view", "conditional-format", "create", "7", "9"], {"rule": rule})

    assert code == 2, envelope
    assert envelope["error"]["code"] == "invalid_rule"
    assert needle in envelope["error"]["message"]
    assert _writes(service, _CREATE) == []


def test_raw_rule_with_valid_format_is_forwarded_untouched(service: FakeMammothService) -> None:
    rule = {
        "cf_type": "RULE",
        "payload": {
            "FORMAT": {"name": "n", "color": "red", "applies_to": "row"},
            "CONDITION": {"OR": [{"column_q1": {"LT": {"VALUE": 3}}}]},
        },
    }
    code, _ = _run(["view", "conditional-format", "create", "7", "9"], {"rule": rule})
    assert code == 0
    assert [call["rule"] for call in _writes(service, _CREATE)] == [rule]


def test_a_rule_without_a_format_object_is_left_to_the_backend(
    service: FakeMammothService,
) -> None:
    """COLOR_SCALE rules have no FORMAT; only a FORMAT that is present is checked."""
    rule = {"cf_type": "COLOR_SCALE", "payload": {"column": "column_q1", "scale": "green"}}
    code, _ = _run(["view", "conditional-format", "create", "7", "9"], {"rule": rule})
    assert code == 0
    assert [call["rule"] for call in _writes(service, _CREATE)] == [rule]


def test_a_non_object_format_is_refused() -> None:
    with pytest.raises(CliError) as excinfo:
        cf.validate_rule({"payload": {"FORMAT": "red"}})
    assert excinfo.value.code == "invalid_rule"
    assert excinfo.value.message == "A RULE payload needs a FORMAT object."


def test_no_value_operators_are_labelled_without_a_value() -> None:
    rules = cf.build_rules(
        {"columns": ["Status"], "operator": "IS_EMPTY", "color": "grey"},
        {"Status": "column_st"},
        {"Status": "TEXT"},
    )
    assert rules[0]["payload"]["FORMAT"]["name"] == "Status IS_EMPTY"


# ── dry run: every body that would be sent, not just the first ──


def test_dry_run_reports_every_rule_body(service: FakeMammothService) -> None:
    def gate(symbol: str, kwargs: dict[str, Any], **_: Any) -> None:
        if symbol == _CREATE:
            raise DryRunStop({"dry_run": True, "would_call": {"sdk_symbol": symbol}})

    service.gate = gate
    code, envelope = _run(
        ["view", "conditional-format", "create", "7", "9", "--dry-run"],
        {"columns": ["Q1", "Q2"], "operator": "<", "value": 55, "color": "red"},
    )

    assert code == 0, envelope
    rules = envelope["data"]["rules"]
    assert [r["payload"]["FORMAT"]["column_ids"] for r in rules] == [
        '["column_q1"]',
        '["column_q2"]',
    ]
    assert _writes(service, _CREATE) == []


# ── replace / delete-all ──


def test_replace_needs_confirmation_before_deleting_anything(
    service: FakeMammothService,
) -> None:
    code, envelope = _run(
        ["view", "conditional-format", "replace", "7", "9"],
        {"columns": ["Q1"], "operator": "<", "value": 5, "color": "red"},
    )
    assert code == 2
    assert envelope["error"]["code"] == "confirmation_required"
    assert _writes(service, _REPLACE) == []


def test_replace_with_yes_sends_all_new_rules_in_one_call(service: FakeMammothService) -> None:
    code, envelope = _run(
        ["view", "conditional-format", "replace", "7", "9", "--yes"],
        {"columns": ["Q1", "Q2"], "operator": "<", "value": 5, "color": "red"},
    )
    assert code == 0, envelope
    (call,) = _writes(service, _REPLACE)
    assert call["dataview_id"] == 7
    assert [r["payload"]["FORMAT"]["column_ids"] for r in call["rules"]] == [
        '["column_q1"]',
        '["column_q2"]',
    ]


def test_replace_validates_the_rule_before_asking_for_confirmation(
    service: FakeMammothService,
) -> None:
    code, envelope = _run(
        ["view", "conditional-format", "replace", "7", "9"],
        {"columns": ["Nope"], "operator": "<", "value": 5, "color": "red"},
    )
    assert code == 2
    assert envelope["error"]["code"] == "invalid_rule"


def test_delete_all_requires_rule_id_and_hints_at_list(service: FakeMammothService) -> None:
    code, envelope = _run(["view", "conditional-format", "delete-all", "7", "9", "--yes"], {})
    assert code == 2
    assert envelope["error"]["code"] == "missing_field"
    assert "view conditional-format list VIEW_ID" in envelope["error"]["hint"]
    assert _writes(service, _DELETE) == []
