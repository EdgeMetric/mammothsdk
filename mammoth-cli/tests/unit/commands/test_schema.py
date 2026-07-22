"""Unit tests for the R7 schema-discovery enrichment.

``mammoth schema get`` must expose enough for an agent to build a valid
invocation without reading source: each accepted field's type, enum values
(when it is an enum), and default; the command's real positional arguments
(derived from :mod:`mammoth_cli.services.positionals`, not the manifest's
placeholder empty list); and one complete, runnable example command line.
"""

from __future__ import annotations

import json
import shlex

from mammoth_cli.commands.schema import get_schema, runnable_example
from mammoth_cli.services.positionals import positionals_for

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
    item = fields["mapping"]["schema"]["items"]
    assert item["required"] == ["search", "replace"]
    assert item["properties"]["search"]["items"]["type"] == "string"


def test_bulk_replace_runnable_example_includes_the_positional_and_input() -> None:
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    example = schema["runnable_example"]
    assert example is not None
    assert example.startswith("mammoth view transform bulk-replace 123 ")
    assert "--input" in example
    assert "--output json --no-input" in example
    tokens = shlex.split(example)
    document = json.loads(tokens[tokens.index("--input") + 1])
    assert document["mapping"] == [{"search": ["example"], "replace": "example"}]


def test_optional_positional_command_has_no_required_positional_in_example() -> None:
    """'project delete' has an optional positional; the example need not force it."""
    schema = get_schema(_PROJECT_DELETE)
    assert schema is not None
    positionals = schema["positionals"]
    assert len(positionals) == 1
    assert positionals[0]["required"] is False
    assert all(field["name"] != "project_id" for field in schema["accepted_fields"])
    assert "project_id" not in schema["runnable_example"]


def test_fallback_positional_is_accepted_but_not_duplicated_in_example() -> None:
    schema = get_schema("project.create")
    assert schema is not None
    assert "name" in {field["name"] for field in schema["accepted_fields"]}
    tokens = shlex.split(schema["runnable_example"])
    assert tokens[:4] == ["mammoth", "project", "create", "example"]
    assert "--input" not in tokens


def test_unknown_command_returns_none() -> None:
    assert get_schema("nope.nope") is None


def test_schema_omits_fields_that_handlers_ignore_or_replace() -> None:
    skill = get_schema("skill.install")
    job = get_schema("job.get")
    assert skill is not None and job is not None
    skill_fields = {field["name"] for field in skill["accepted_fields"]}
    job_fields = {field["name"] for field in job["accepted_fields"]}
    assert {"home", "cwd", "timestamp"}.isdisjoint(skill_fields)
    assert "timeout" not in job_fields
    assert {"home", "cwd", "timestamp"}.isdisjoint(skill["input_schema"]["properties"])
    assert "timeout" not in job["input_schema"]["properties"]


def test_id_collection_schema_requires_positive_non_empty_ids() -> None:
    schema = get_schema("project.bulk-delete")
    assert schema is not None
    project_ids = schema["input_schema"]["properties"]["project_ids"]
    assert project_ids["minItems"] == 1
    assert project_ids["items"]["minimum"] == 1


def test_build_time_example_uses_explicit_operation_ids_not_generated_manifest(
    monkeypatch,
) -> None:
    """A clean manifest build cannot read the output it is in the middle of creating."""
    monkeypatch.setattr(
        "mammoth_cli.services.openapi_types.command_by_id",
        lambda _command_id: (_ for _ in ()).throw(AssertionError("manifest lookup")),
    )
    monkeypatch.setattr(
        "mammoth_cli.commands.schema.resolve_positionals",
        lambda _command_id: (_ for _ in ()).throw(AssertionError("manifest lookup")),
    )
    record = {
        "command_id": "dashboard.context.create",
        "command_path": "dashboard context create",
        "operation_ids": ["CreateContext"],
    }
    example = runnable_example(
        record,
        "mammoth.api.dashboards.DashboardsAPI.context_create",
        positionals_for(record["command_id"], None),
    )
    assert example is not None
    document = json.loads(shlex.split(example)[5])
    assert document == {"body": {"params": {"name": "example"}}}
