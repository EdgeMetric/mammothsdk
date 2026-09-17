"""Independent M5 discovery and machine-output contract checks.

These tests deliberately exercise the public seams instead of rebuilding the
implementation's ranking constants.  In particular, the NDJSON assertions
capture the compatibility choice made by the CLI: JSON is one complete result
document, while NDJSON emits one complete JSON value per result item (and emits
no blank sentinel for an empty list).
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from mammoth_cli.commands.capability import find_capabilities
from mammoth_cli.commands.schema import find_schemas, get_schema, schema_entries
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.output.normalize import normalize
from mammoth_cli.output.policy import resolve_output, resolve_policy
from mammoth_cli.output.render import render
from mammoth_cli.runtime.input_loader import load_input_document


@dataclass
class _TypedCursor:
    value: str


class _SchemaDeclaration:
    @classmethod
    def model_json_schema(cls) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "api_key": {
                    "type": "string",
                    "default": "must-not-appear",
                    "allOf": [{"example": "must-not-appear"}],
                },
            },
        }


class _SecretBearingObject:
    def __init__(self) -> None:
        self.api_key = "must-not-appear"


def test_intent_synonyms_are_ranked_deterministically_from_a_cold_call() -> None:
    first = find_schemas("please import a spreadsheet")
    second = find_schemas("please import a spreadsheet")

    assert first == second
    assert first["matches"][0]["command_id"] == "file.upload"
    assert first["matches"][0]["full_schema_command"].startswith(
        "mammoth schema get file.upload"
    )


def test_display_name_language_composes_with_column_intent() -> None:
    result = find_schemas("display-name columns")

    assert result["matches"]
    assert any(match["command_id"].startswith("view.transform.") for match in result["matches"])


def test_local_export_intent_ranks_the_artifact_command_first() -> None:
    result = find_schemas("export local csv")

    assert result["matches"][0]["command_id"] == "view.export.csv"


def test_schema_find_has_bounded_cursor_continuation_and_no_fake_final_cursor() -> None:
    first = find_schemas("view transform", limit=3)
    continuation = first["continuation"]

    assert len(first["matches"]) == 3
    assert first["truncated"] is True
    assert continuation == {
        "next_cursor": "3",
        "has_more": True,
        "limit": 3,
        "query": "view transform",
    }

    next_page = find_schemas("view transform", limit=3, cursor=3)
    assert len(next_page["matches"]) == 3
    assert set(match["command_id"] for match in first["matches"]).isdisjoint(
        match["command_id"] for match in next_page["matches"]
    )

    final = find_schemas("upload csv")
    assert final["truncated"] is False
    assert final["continuation"] is None


@pytest.mark.parametrize("requested", [0, -1, 10_000])
def test_discovery_limit_is_finite_and_positive(requested: int) -> None:
    result = find_capabilities("show projects", limit=requested)

    assert 1 <= len(result["matches"]) <= 100
    assert result["continuation"] is None or result["continuation"]["limit"] <= 100


def test_capability_find_is_a_public_machine_command() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mammoth_cli",
            "capability",
            "find",
            "show projects",
            "--output",
            "json",
            "--no-input",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data"]["query"] == "show projects"
    assert payload["data"]["matches"]
    assert payload["data"]["matches"][0]["canonical_command"].startswith("project.")


def test_compact_contract_has_all_execution_dimensions() -> None:
    schema = get_schema("project.delete")
    assert schema is not None

    contract = schema["contract"]
    assert set(contract) == {
        "scope",
        "effects",
        "preconditions",
        "result",
        "async",
        "verification",
        "recovery",
        "limits",
    }
    assert contract["scope"] == "project"
    assert contract["effects"] == "destructive"
    assert contract["result"] == "ProjectDeleteResult"
    assert contract["async"] == "not_async"
    assert contract["limits"]["continuation"] is None
    assert "verify" in contract["recovery"]


def test_schema_marks_raw_task_specs_opaque_and_points_to_typed_transforms() -> None:
    schema = get_schema("view.task.add")
    assert schema is not None

    assert schema["contract_level"] == "opaque_expert"
    assert schema["unresolved_nested_fields"] == ["task_spec"]
    assert schema["safe_typed_alternatives"] == [
        "view.transform.filter",
        "view.transform.join",
        "view.transform.math",
    ]


def test_schema_marks_typed_transform_self_describing() -> None:
    schema = get_schema("view.transform.math")
    assert schema is not None

    assert schema["contract_level"] == "typed"
    assert schema["unresolved_nested_fields"] == []
    assert schema["safe_typed_alternatives"] == []


def test_generic_body_route_has_no_unreviewed_alternatives_and_list_exposes_levels() -> None:
    schema = get_schema("annotation.comment.add")
    assert schema is not None
    assert schema["contract_level"] == "partially_typed"
    assert schema["unresolved_nested_fields"] == ["body"]
    assert schema["safe_typed_alternatives"] == []

    task_entry = next(item for item in schema_entries() if item["command_id"] == "view.task.add")
    assert task_entry["contract_level"] == "opaque_expert"
    assert task_entry["unresolved_nested_fields"] == ["task_spec"]
    assert task_entry["safe_typed_alternatives"] == [
        "view.transform.filter",
        "view.transform.join",
        "view.transform.math",
    ]


def test_json_is_one_complete_parseable_document_and_preserves_token_count() -> None:
    stream = io.StringIO()
    envelope = {
        "schema_version": 1,
        "data": {"rows": [{"token_count": 7, "value": "ok"}]},
        "meta": {"command": "test"},
    }

    render(envelope, output="json", stream=stream)
    parsed = json.loads(stream.getvalue())

    assert parsed == envelope
    assert parsed["data"]["rows"][0]["token_count"] == 7
    assert stream.getvalue().count("{") == stream.getvalue().count("}")


def test_ndjson_emits_versioned_lifecycle_for_items_empty_and_error() -> None:
    stream = io.StringIO()
    render(
        {
            "schema_version": 1,
            "data": [{"id": 1}, {"id": 2}],
            "meta": {"pagination": {"next_cursor": "opaque", "has_more": True}},
        },
        output="ndjson",
        stream=stream,
    )
    lines = stream.getvalue().splitlines()
    frames = [json.loads(line) for line in lines]
    assert [frame["event"] for frame in frames] == ["start", "item", "item", "end"]
    assert [frame["data"] for frame in frames[1:3]] == [{"id": 1}, {"id": 2}]
    assert frames[0]["meta"]["pagination"] == {"next_cursor": "opaque", "has_more": True}
    assert frames[-1]["meta"] == frames[0]["meta"]
    assert frames[-1]["complete"] is True

    empty = io.StringIO()
    render({"schema_version": 1, "data": [], "meta": {}}, output="ndjson", stream=empty)
    assert [json.loads(line)["event"] for line in empty.getvalue().splitlines()] == ["start", "end"]

    failed = io.StringIO()
    render(
        {"schema_version": 1, "error": {"code": "interrupted"}, "meta": {}},
        output="ndjson",
        stream=failed,
    )
    assert json.loads(failed.getvalue()) == {
        "complete": False,
        "error": {"code": "interrupted"},
        "event": "error",
        "meta": {},
        "schema_version": 1,
        "stream_version": 2,
    }


def test_ndjson_legacy_mode_retains_item_only_compatibility() -> None:
    stream = io.StringIO()
    render(
        {"schema_version": 1, "data": [{"id": 1}], "meta": {}},
        output="ndjson",
        stream=stream,
        ndjson_legacy=True,
    )
    assert [json.loads(line) for line in stream.getvalue().splitlines()] == [{"id": 1}]


def test_table_keeps_fields_from_heterogeneous_rows() -> None:
    stream = io.StringIO()
    render(
        {
            "schema_version": 1,
            "data": [{"id": 1, "name": "first"}, {"id": 2, "status": "ok"}],
            "meta": {},
        },
        output="table",
        stream=stream,
    )

    output = stream.getvalue()
    assert "name" in output
    assert "status" in output
    assert "first" in output
    assert "ok" in output


def test_nonfinite_result_is_made_json_safe_instead_of_emitting_invalid_json() -> None:
    stream = io.StringIO()
    render(
        {"schema_version": 1, "data": {"value": float("nan")}, "meta": {}},
        output="json",
        stream=stream,
    )

    parsed = json.loads(stream.getvalue())
    assert parsed["data"]["value"] == "nan"
    assert "NaN" not in stream.getvalue()
    assert normalize({"value": float("inf")})["value"] == "inf"


def test_normalize_redacts_typed_secrets_and_preserves_typed_cursors_and_schemas() -> None:
    from pydantic import SecretStr

    normalized = normalize(
        {
            "innocuous_name": SecretStr("must-not-appear"),
            "cursor": _TypedCursor("opaque-next-page"),
            "schema": _SchemaDeclaration,
        }
    )

    assert normalized == {
        "cursor": "opaque-next-page",
        "innocuous_name": "***REDACTED***",
        "schema": {
            "properties": {
                "api_key": {
                    "allOf": [{"example": "***REDACTED***"}],
                    "default": "***REDACTED***",
                    "type": "string",
                },
                "page": {"type": "integer"},
            },
            "type": "object",
        },
    }


def test_result_then_render_preserves_schema_names_but_redacts_result_secrets() -> None:
    stream = io.StringIO()
    envelope = Result(
        data={"schema": _SchemaDeclaration, "api_key": "must-not-appear"},
        meta=Meta(command="test"),
    ).to_envelope()

    render(envelope, output="json", stream=stream)
    parsed = json.loads(stream.getvalue())

    assert parsed["data"]["api_key"] == "***REDACTED***"
    assert parsed["data"]["schema"]["properties"]["api_key"] == {
        "allOf": [{"example": "***REDACTED***"}],
        "default": "***REDACTED***",
        "type": "string",
    }


def test_schema_discovery_input_schema_survives_render_without_trusting_result_keys() -> None:
    stream = io.StringIO()
    schema = get_schema("auth.login")
    assert schema is not None
    envelope = Result(
        data={"schema": schema, "api_key": "must-not-appear"}, meta=Meta(command="test")
    ).to_envelope()

    render(envelope, output="json", stream=stream)
    parsed = json.loads(stream.getvalue())

    properties = parsed["data"]["schema"]["input_schema"]["properties"]
    assert {"api_key", "api_secret", "workspace_id"}.issubset(properties)
    assert parsed["data"]["api_key"] == "***REDACTED***"


def test_unknown_rich_object_fails_closed_without_exposing_attributes() -> None:
    normalized = normalize(_SecretBearingObject())

    assert normalized == "<unserializable _SecretBearingObject>"


def test_normalize_redacts_api_keys_without_erasing_cursor_or_schema_names() -> None:
    normalized = normalize(
        {
            "api_key": "must-not-appear",
            "secure_key": "must-not-appear",
            "next_token": "opaque-next-page",
            "continuation_token": "opaque-continuation",
            "design_tokens": ["primary", "spacing"],
            "schema": {"api_key": "must-not-appear"},
        }
    )

    assert normalized["api_key"] == "***REDACTED***"
    assert normalized["secure_key"] == "***REDACTED***"
    assert normalized["next_token"] == "opaque-next-page"
    assert normalized["continuation_token"] == "opaque-continuation"
    assert normalized["design_tokens"] == ["primary", "spacing"]
    assert normalized["schema"]["api_key"] == "***REDACTED***"


def test_nonfinite_json_input_is_rejected_before_command_execution(tmp_path: Path) -> None:
    path = tmp_path / "nonfinite.json"
    path.write_text('{"value": NaN}', encoding="utf-8")

    with pytest.raises(CliError) as error:
        load_input_document(str(path), None)

    assert error.value.code == "nonfinite_input_number"


def test_output_policy_distinguishes_redirected_and_tty_width_independent_of_color() -> None:
    assert resolve_output("auto", is_tty=False) == "json"
    assert resolve_output("auto", is_tty=True) == "table"
    redirected = resolve_policy(output="json", is_tty=False, env={"TERM": "xterm"})
    tty = resolve_policy(output="table", is_tty=True, env={"TERM": "xterm"})
    assert redirected.prompts_disabled and redirected.progress_disabled
    assert not tty.prompts_disabled and not tty.progress_disabled


def test_subprocess_machine_success_and_error_keep_streams_separate() -> None:
    cli_root = Path(__file__).parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        str(path) for path in (cli_root.parent, cli_root) if str(path)
    )
    success = subprocess.run(
        [
            sys.executable,
            "-m",
            "mammoth_cli",
            "schema",
            "get",
            "dataset.list",
            "--output",
            "json",
            "--no-input",
        ],
        cwd=cli_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert success.returncode == 0
    assert success.stderr == ""
    assert json.loads(success.stdout)["schema_version"] == 1

    failure = subprocess.run(
        [
            sys.executable,
            "-m",
            "mammoth_cli",
            "schema",
            "get",
            "missing.command",
            "--output",
            "json",
            "--no-input",
        ],
        cwd=cli_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert failure.returncode == 2
    assert failure.stdout == ""
    assert json.loads(failure.stderr)["error"]["code"] == "schema_not_found"
