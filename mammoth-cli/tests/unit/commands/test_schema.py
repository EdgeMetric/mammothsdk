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
from pathlib import Path

import yaml

from mammoth_cli.commands.schema import find_schemas, get_schema, runnable_example
from mammoth_cli.services.positionals import positionals_for

_BULK_REPLACE = "view.transform.bulk-replace"
_TEXT_TRANSFORM = "view.transform.text"
_MATH_TRANSFORM = "view.transform.math"
_PROJECT_DELETE = "project.delete"
ROOT = Path(__file__).parents[3]


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


def test_transform_schema_advertises_exact_parent_dataset_context() -> None:
    schema = get_schema(_MATH_TRANSFORM)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["dataset_id"]["type"] == "int"
    assert fields["dataset_id"]["required"] is False
    assert fields["dataset_id"]["schema"]["anyOf"][0]["minimum"] == 1


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
    assert "--output json" not in example
    tokens = shlex.split(example)
    document = json.loads(tokens[tokens.index("--input") + 1])
    assert document["mapping"] == [{"search": ["sample"], "replace": "sample"}]


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
    assert tokens[:4] == ["mammoth", "project", "create", "Revenue report"]
    assert "--input" not in tokens


def test_exportable_config_schema_is_exact_one_of_and_view_centric() -> None:
    get = get_schema("view.exportable-config.get")
    apply = get_schema("view.exportable-config.apply")
    assert get is not None and apply is not None
    assert [p["name"] for p in get["positionals"]] == ["view_id", "dataset_id"]
    assert {field["name"]: field["required"] for field in get["accepted_fields"]} == {
        "dataset_id": False
    }
    assert get["input_schema"]["required"] == []
    assert "dataview_id" not in get["input_schema"]["properties"]
    schema = apply["input_schema"]
    assert {field["name"]: field["required"] for field in apply["accepted_fields"]}[
        "dataset_id"
    ] is False
    assert "dataset_id" in schema["properties"]
    assert schema["oneOf"] == [
        {"required": ["items"], "not": {"required": ["config"]}},
        {"required": ["config"], "not": {"required": ["items"]}},
    ]
    config_properties = schema["properties"]["config"]["properties"]
    assert config_properties["tasks"]["type"] == [
        "array",
        "null",
    ]
    assert config_properties["tasks"]["items"] == {"type": "object"}
    assert config_properties["name"]["type"] == [
        "string",
        "null",
    ]
    example = shlex.split(apply["runnable_example"])
    assert example[:5] == ["mammoth", "view", "exportable-config", "apply", "123"]
    assert "--yes" in example and example[example.index("--confirm") + 1] == "123"


def test_batch_data_schema_exposes_release_paging_bounds() -> None:
    schema = get_schema("dataset.batch-data")
    assert schema is not None
    assert schema["input_schema"]["properties"]["limit"]["minimum"] == 0
    assert schema["input_schema"]["properties"]["limit"]["maximum"] == 100
    assert schema["input_schema"]["properties"]["offset"]["minimum"] == 0


def test_unknown_command_returns_none() -> None:
    assert get_schema("nope.nope") is None


def test_schema_get_exposes_dispatch_policy_and_exact_sensitive_scope() -> None:
    project_admin = get_schema("project.user.update")
    share = get_schema("data-app.share")
    apply = get_schema("view.exportable-config.apply")
    assert project_admin is not None and share is not None and apply is not None

    assert (project_admin["mutation_class"], project_admin["confirmation"]) == (
        "high_impact",
        "yes_always",
    )
    assert project_admin["scope_requirements"]["required_context"] == ["project_id"]
    assert share["scope_requirements"] == {
        "kind": "workspace",
        "required_context": ["workspace_id"],
        "target_fields": ["data_app_id"],
        "target_rule": "data_app_id is a required positional",
    }
    assert (apply["mutation_class"], apply["confirmation"], apply["wait_policy"]) == (
        "reversible_pipeline",
        "confirm_target",
        "returns_job",
    )
    assert apply["scope_requirements"]["target_fields"] == ["view_id", "dataset_id"]
    assert "--yes" in shlex.split(project_admin["agent_example"])
    assert "--yes" in shlex.split(share["agent_example"])
    assert "--yes" in shlex.split(project_admin["runnable_example"])
    assert "--yes" in shlex.split(share["runnable_example"])


def test_agent_transform_language_finds_typed_routes() -> None:
    assert "view.transform.discard-duplicates" in {
        item["command_id"] for item in find_schemas("duplicate")["matches"]
    }
    assert "view.transform.convert-type" in {
        item["command_id"] for item in find_schemas("cast numeric type")["matches"]
    }
    assert "view.transform.fill-missing" in {
        item["command_id"] for item in find_schemas("fill missing")["matches"]
    }
    assert "view.transform.join" in {
        item["command_id"] for item in find_schemas("join blend")["matches"]
    }


def test_csv_export_contract_does_not_preserve_stale_permission_block() -> None:
    """Retained live evidence supersedes the old blanket export restriction."""
    schema = get_schema("view.export.csv")
    assert schema is not None
    assert "Live dataset permission is currently blocked" not in schema["preconditions"]


def test_ingestion_contract_preserves_supported_path_and_variant_boundaries() -> None:
    """Published discovery must not turn retained live evidence into a blanket block."""
    dataset_create = get_schema("dataset.create")
    file_upload = get_schema("file.upload")
    assert dataset_create is not None and file_upload is not None

    assert "BLOCKED[B06" not in dataset_create["preconditions"]
    assert "ds_creation_type=weburl" in dataset_create["preconditions"]
    assert dataset_create["async"] == "always_wait"
    assert (
        "variants beyond the documented path are not qualified" in dataset_create["preconditions"]
    )

    assert "IO-LIVE-PERMISSION" not in file_upload["preconditions"]
    assert "tenant- and scope-specific" in file_upload["preconditions"]
    # The contract states the measured boundaries instead of a blanket block.
    assert "Accepted extensions" in file_upload["preconditions"]
    assert "not json" in file_upload["preconditions"]
    assert "HTTP 413" in file_upload["preconditions"]
    assert "do not assume other upload variants are qualified" in file_upload["preconditions"]


def test_dataset_create_sdk_catalog_does_not_conflate_cli_waiting() -> None:
    """The SDK returns a job handle; the CLI handler owns its always-wait policy."""
    catalog = yaml.safe_load(
        (ROOT / "spec" / "manifests" / "sdk-catalog.source.yaml").read_text(encoding="utf-8")
    )
    record = next(
        item
        for item in catalog["sdk_methods"]
        if item["sdk_symbol"] == "mammoth.api.datasets.DatasetsAPI.create"
    )
    schema = get_schema("dataset.create")
    assert record["wait_policy"] == "not_async"
    assert "CLI command waits for the raw SDK job" in record["notes"]
    assert schema is not None and schema["async"] == "always_wait"


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
    assert document == {"body": {"params": {"name": "Revenue report"}}}


def test_schema_get_names_secret_fields_and_routes_their_example_through_a_file() -> None:
    from mammoth_cli.output.normalize import normalize

    postgres = get_schema("view.export.postgres")
    csv = get_schema("view.export.csv")
    assert postgres is not None and csv is not None

    assert postgres["secret_fields"] == ["password"]
    assert csv["secret_fields"] == []
    # The list names protected fields; it must survive output redaction so an
    # agent can see which commands need ``--input FILE``.
    assert normalize({"secret_fields": ["password"]}) == {"secret_fields": ["password"]}
    assert "/private/path/request.json" in postgres["agent_example"]
    assert "password" not in postgres["agent_example"]
