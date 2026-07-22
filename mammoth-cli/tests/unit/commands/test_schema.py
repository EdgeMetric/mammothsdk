"""Unit tests for the R7 schema-discovery enrichment.

``mammoth schema get`` must expose enough for an agent to build a valid
invocation without reading source: each accepted field's type, enum values
(when it is an enum), and default; the command's real positional arguments
(derived from :mod:`mammoth_cli.services.positionals`, not the manifest's
placeholder empty list); and one complete, runnable example command line.
"""

from __future__ import annotations

from mammoth_cli.commands.schema import get_schema

_BULK_REPLACE = "view.transform.bulk-replace"
_TEXT_TRANSFORM = "view.transform.text"
_PROJECT_DELETE = "project.delete"


def test_enum_field_exposes_its_member_values() -> None:
    """A command with an enum-typed field ('case') reports its values."""
    schema = get_schema(_TEXT_TRANSFORM)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["case"]["type"] == "TextCase"
    assert fields["case"]["enum"] == ["UPPER", "LOWER", "TITLE"]
    assert fields["case"]["required"] is False


def test_accepted_fields_report_type_and_default() -> None:
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["match_case"]["type"] == "bool"
    assert fields["match_case"]["default"] is True
    assert fields["columns"]["required"] is True
    assert fields["columns"]["enum"] is None


def test_bulk_replace_exposes_the_required_view_id_positional() -> None:
    """bulk-replace's positional (the view id) was previously invisible."""
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    positionals = schema["positionals"]
    assert len(positionals) == 1
    assert positionals[0]["name"] == "view_id"
    assert positionals[0]["type"] == "int"
    assert positionals[0]["required"] is True
    assert positionals[0]["metavar"] == "VIEW_ID"


def test_bulk_replace_exposes_the_typed_mapping_structure() -> None:
    """The 'mapping' field's type names BulkReplaceMapping, not opaquely."""
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["mapping"]["type"] == "list[BulkReplaceMapping]"


def test_bulk_replace_runnable_example_includes_the_positional_and_input() -> None:
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    example = schema["runnable_example"]
    assert example is not None
    assert example.startswith("mammoth view transform bulk-replace 123 ")
    assert "--input" in example
    assert "--output json --no-input" in example


def test_optional_positional_command_has_no_required_positional_in_example() -> None:
    """'project delete' has an optional positional; the example need not force it."""
    schema = get_schema(_PROJECT_DELETE)
    assert schema is not None
    positionals = schema["positionals"]
    assert len(positionals) == 1
    assert positionals[0]["required"] is False


def test_unknown_command_returns_none() -> None:
    assert get_schema("nope.nope") is None
