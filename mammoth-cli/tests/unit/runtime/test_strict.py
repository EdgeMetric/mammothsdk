"""Unit tests for the surplus-positional (R5) and input-field-type (R6) checks.

These call the real validators (:mod:`mammoth_cli.runtime.strict`) against
real manifest commands and their real backing SDK signatures — no mocks.
"""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.strict import validate_extra_args, validate_input_fields

_PROJECT_DELETE = "project.delete"
_BULK_REPLACE = "view.transform.bulk-replace"
_PROJECT_LIST = "project.list"
_SKILL_INSTALL = "skill.install"


# --- R5: a surplus positional token is rejected, not silently dropped -----


def test_surplus_positional_beyond_the_accepted_count_is_rejected() -> None:
    """'project delete' accepts one (optional) positional; a second is refused."""
    with pytest.raises(CliError) as excinfo:
        validate_extra_args(_PROJECT_DELETE, ["1", "2"])
    assert excinfo.value.code == "unexpected_argument"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_single_positional_for_project_delete_still_passes() -> None:
    validate_extra_args(_PROJECT_DELETE, ["1"])


def test_project_delete_with_no_positional_still_passes() -> None:
    """The project-id positional is optional (falls back to the active project)."""
    validate_extra_args(_PROJECT_DELETE, [])


def test_view_receiver_command_accepts_exactly_one_positional() -> None:
    """A View-method command (bulk-replace) synthesizes exactly one id slot."""
    validate_extra_args(_BULK_REPLACE, ["1039"])
    with pytest.raises(CliError) as excinfo:
        validate_extra_args(_BULK_REPLACE, ["1039", "1040"])
    assert excinfo.value.code == "unexpected_argument"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_unknown_option_is_still_rejected_before_the_positional_count_check() -> None:
    """An option-like token fails as 'unknown_option', not 'unexpected_argument'."""
    with pytest.raises(CliError) as excinfo:
        validate_extra_args(_BULK_REPLACE, ["1039", "--nope"])
    assert excinfo.value.code == "unknown_option"


# --- R6: --input field values are validated/coerced to their real type ----


def test_int_field_given_an_unparsable_string_is_rejected() -> None:
    """'project list --input {"limit": "abc"}' must not crash the SDK call."""
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(_PROJECT_LIST, {"limit": "abc"})
    assert excinfo.value.code == "invalid_input_field_type"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_int_field_given_a_numeric_string_is_coerced() -> None:
    document = {"limit": "25"}
    validate_input_fields(_PROJECT_LIST, document)
    assert document["limit"] == 25
    assert isinstance(document["limit"], int)


def test_int_field_given_a_real_int_is_left_alone() -> None:
    document = {"limit": 25}
    validate_input_fields(_PROJECT_LIST, document)
    assert document["limit"] == 25


def test_bool_field_false_string_coerces_to_the_real_false() -> None:
    """Must never be a blanket bool('false'), which is True."""
    document = {"force": "false"}
    validate_input_fields(_SKILL_INSTALL, document)
    assert document["force"] is False


@pytest.mark.parametrize("token", ["true", "1", "TRUE", "yes", "on"])
def test_bool_field_true_spellings_coerce_to_true(token: str) -> None:
    document = {"force": token}
    validate_input_fields(_SKILL_INSTALL, document)
    assert document["force"] is True


@pytest.mark.parametrize("token", ["false", "0", "FALSE", "no", "off"])
def test_bool_field_false_spellings_coerce_to_false(token: str) -> None:
    document = {"force": token}
    validate_input_fields(_SKILL_INSTALL, document)
    assert document["force"] is False


def test_bool_field_given_an_unrecognized_string_is_rejected() -> None:
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(_SKILL_INSTALL, {"force": "maybe"})
    assert excinfo.value.code == "invalid_input_field_type"


def test_unaffected_field_types_pass_through_unchanged() -> None:
    """A list-typed field (columns) is untouched by scalar coercion."""
    document = {"columns": ["Item"], "mapping": [], "match_case": True}
    validate_input_fields(_BULK_REPLACE, document)
    assert document["columns"] == ["Item"]
    assert document["match_case"] is True


@pytest.mark.parametrize(
    ("command_id", "document"),
    [
        ("project.bulk-delete", {"project_ids": ["abc"]}),
        (_BULK_REPLACE, {"columns": "not-a-list", "mapping": []}),
        (_BULK_REPLACE, {"columns": ["Item"], "mapping": "not-a-list"}),
        (_SKILL_INSTALL, {"agents": "codex"}),
    ],
)
def test_recursive_collection_validation_rejects_malformed_values(
    command_id: str, document: dict[str, object]
) -> None:
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(command_id, document)
    assert excinfo.value.code == "invalid_input_field_type"


def test_nested_dataclass_requires_and_validates_members() -> None:
    # ``replace`` is a string field; a bool is never coerced to a string, so a
    # nested member of the wrong type is still reported by its path.
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(
            _BULK_REPLACE,
            {"columns": ["Item"], "mapping": [{"search": [], "replace": True}]},
        )
    assert excinfo.value.code == "invalid_input_field_type"
    assert "mapping[0].replace" in excinfo.value.message


def test_positional_resource_id_is_not_accepted_again_in_input() -> None:
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(_PROJECT_DELETE, {"project_id": 1})
    assert excinfo.value.code == "unknown_input_field"


def test_fallback_positional_field_remains_valid_structured_input() -> None:
    document = {"name": "Input-only project"}
    validate_input_fields("project.create", document)
    assert document == {"name": "Input-only project"}


@pytest.mark.parametrize(
    ("command_id", "document", "path"),
    [
        ("project.bulk-delete", {"project_ids": []}, "project_ids"),
        ("project.bulk-delete", {"project_ids": [-1, 2]}, "project_ids[0]"),
        ("project.bulk-delete", {"project_ids": [1, 0]}, "project_ids[1]"),
        ("job.get-many", {"job_ids": []}, "job_ids"),
        ("job.get-many", {"job_ids": [0]}, "job_ids[0]"),
    ],
)
def test_resource_id_collections_are_non_empty_and_positive(
    command_id: str, document: dict[str, object], path: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(command_id, document)
    assert excinfo.value.code == "invalid_input_field_type"
    assert path in excinfo.value.message


@pytest.mark.parametrize(
    ("command_id", "field"),
    [
        ("skill.install", "home"),
        ("skill.install", "cwd"),
        ("skill.install", "timestamp"),
        ("skill.update", "timestamp"),
        ("skill.path", "home"),
        ("job.get", "timeout"),
    ],
)
def test_handler_ignored_or_replaced_fields_are_rejected(command_id: str, field: str) -> None:
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(command_id, {field: "ignored"})
    assert excinfo.value.code == "unknown_input_field"
