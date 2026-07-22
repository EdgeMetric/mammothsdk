"""Red-first parity and command-manifest contract tests.

These assert the reviewed manifests are complete and internally consistent.
They are red until the manifests and typed SDK symbols exist.
"""

from __future__ import annotations

import importlib
import shlex
from pathlib import Path

import pytest

from mammoth_cli.manifest.loader import (
    load_commands,
    load_operations,
    load_sdk_methods,
)
from mammoth_cli.services.positionals import positionals_for

CLI_ROOT = Path(__file__).resolve().parent.parent.parent

VALID_DISPOSITIONS = {"command", "alias", "protocol_only", "deprecated", "server_unavailable"}
LIVE_EVIDENCE = {"live_disposable_project", "live_dedicated_external_fixture", "live_read_only"}


def _resolve_symbol(symbol: str) -> object | None:
    """Resolve a dotted ``module.Class.attr`` symbol, or return None."""
    parts = symbol.split(".")
    for split in range(len(parts) - 1, 0, -1):
        module_name = ".".join(parts[:split])
        try:
            obj: object = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        try:
            for attr in parts[split:]:
                obj = getattr(obj, attr)
            return obj
        except AttributeError:
            return None
    return None


# --- OpenAPI operation dispositions ---------------------------------------


def test_every_openapi_operation_has_reviewed_disposition() -> None:
    operations = load_operations()
    assert operations, "operation manifest empty"
    for record in operations:
        assert record.get("disposition") in VALID_DISPOSITIONS, record["identity"]
        assert record.get("disposition_reason"), f"missing reason for {record['identity']}"
        assert record.get("reviewed_by"), f"missing reviewer for {record['identity']}"


def test_every_command_disposition_has_typed_sdk_symbol() -> None:
    for record in load_operations():
        if record.get("disposition") != "command":
            continue
        symbol = record.get("sdk_symbol")
        assert symbol, f"command op missing sdk_symbol: {record['identity']}"
        assert _resolve_symbol(symbol) is not None, f"unresolved sdk_symbol {symbol}"


def test_manifest_has_no_unknown_openapi_or_sdk_symbols() -> None:
    import json

    snapshot = CLI_ROOT / "spec" / "openapi" / "openapi.json"
    document = json.loads(snapshot.read_text(encoding="utf-8"))
    methods = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
    snapshot_ids = {
        f"{m.upper()} {p}"
        for p, item in document["paths"].items()
        for m in item
        if m.lower() in methods
    }
    manifest_ids = {record["identity"] for record in load_operations()}
    assert manifest_ids == snapshot_ids, "operation manifest and snapshot disagree"

    for record in load_sdk_methods():
        symbol = record["sdk_symbol"]
        assert _resolve_symbol(symbol) is not None, f"unknown sdk symbol {symbol}"


# --- SDK method parity -----------------------------------------------------


def test_every_public_sdk_method_has_command_or_alias() -> None:
    methods = load_sdk_methods()
    assert methods, "sdk manifest empty"
    for record in methods:
        has_command = bool(record.get("canonical_command"))
        has_alias = bool(record.get("alias_of"))
        # A small reviewed set of SDK-only helpers legitimately have no command
        # (e.g. a forbidden targetless bulk delete, a draft seam, a private
        # resolver). Each must carry a reviewed no_command_reason.
        has_exemption = bool(record.get("no_command_reason"))
        assert (
            has_command or has_alias or has_exemption
        ), f"sdk method has no command, alias, or exemption: {record['sdk_symbol']}"


# --- Command records -------------------------------------------------------


def test_every_command_has_request_and_result_models() -> None:
    commands = load_commands()
    assert commands, "command manifest empty"
    for record in commands:
        if record.get("disposition") == "alias":
            continue
        assert record.get("request_model"), f"{record['command_id']} missing request_model"
        assert record.get("result_model"), f"{record['command_id']} missing result_model"


def test_every_command_has_human_and_agent_examples() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert record.get("human_example"), f"{record['command_id']} missing human_example"
        assert record.get("agent_example"), f"{record['command_id']} missing agent_example"


def test_manifest_positionals_match_the_canonical_source() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        expected = [
            positional.as_manifest()
            for positional in positionals_for(record["command_id"], record.get("sdk_symbol"))
        ]
        assert record.get("positionals") == expected, record["command_id"]


def test_human_examples_contain_only_required_positional_metavars() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        positionals = positionals_for(record["command_id"], record.get("sdk_symbol"))
        command_prefix = ["mammoth", *shlex.split(record["command_path"])]
        tokens = shlex.split(record["human_example"])
        assert tokens[: len(command_prefix)] == command_prefix, record["command_id"]
        assert tokens[len(command_prefix) :] == [
            *(positional.metavar for positional in positionals if positional.required),
            "--help",
        ], record["command_id"]


def test_agent_examples_use_concrete_positional_samples_in_declared_order() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        positionals = positionals_for(record["command_id"], record.get("sdk_symbol"))
        command_prefix = ["mammoth", *shlex.split(record["command_path"])]
        tokens = shlex.split(record["agent_example"])
        assert tokens[: len(command_prefix)] == command_prefix, record["command_id"]
        example_tokens = tokens[len(command_prefix) :]
        assert example_tokens == [
            *("123" if positional.type is int else "example" for positional in positionals),
            "--output",
            "json",
            "--no-input",
        ], record["command_id"]
        assert not {positional.metavar for positional in positionals}.intersection(
            example_tokens
        ), record["command_id"]


def test_every_command_has_test_ids() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert record.get("unit_tests"), f"{record['command_id']} missing unit_tests"
        assert record.get("contract_tests"), f"{record['command_id']} missing contract_tests"


def test_every_mutation_has_safety_class() -> None:
    valid = {
        "read",
        "benign_mutation",
        "reversible_pipeline",
        "destructive",
        "high_impact",
        "external_effect",
    }
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert record.get("mutation_class") in valid, record["command_id"]
        assert record.get("confirmation"), f"{record['command_id']} missing confirmation"


def test_every_async_operation_has_wait_policy() -> None:
    valid = {"always_wait", "start_or_wait", "returns_job", "not_async"}
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert record.get("wait_policy") in valid, record["command_id"]


def test_every_list_operation_has_pagination_policy() -> None:
    valid = {"none", "offset", "cursor", "single_page"}
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert record.get("pagination_policy") in valid, record["command_id"]


def test_every_secret_field_has_transport_and_redaction_policy() -> None:
    for record in load_commands():
        for option in record.get("options", []):
            if option.get("secret"):
                # A secret option must never be an ordinary CLI value.
                env = option.get("env")
                assert (
                    env or option.get("document_conflict") is not None
                ), f"{record['command_id']} secret option {option['name']} lacks safe transport"


def test_command_paths_are_unique() -> None:
    seen: dict[str, str] = {}
    for record in load_commands():
        path = record["command_path"]
        assert path not in seen, f"duplicate command path {path}"
        seen[path] = record["command_id"]


def test_alias_graph_has_no_cycles() -> None:
    by_id = {record["command_id"]: record for record in load_commands()}
    for record in load_commands():
        seen: set[str] = set()
        current = record
        while current.get("disposition") == "alias":
            cid = current["command_id"]
            assert cid not in seen, f"alias cycle at {cid}"
            seen.add(cid)
            target = current.get("alias_of")
            assert target in by_id, f"{cid} aliases unknown {target}"
            current = by_id[target]


def test_live_exemptions_have_reason_and_reviewer() -> None:
    for record in load_commands():
        if record.get("acceptance_evidence") in LIVE_EVIDENCE:
            continue
        assert record.get("live_exemption_reason"), f"{record['command_id']} needs exemption reason"
        assert record.get("reviewed_by"), f"{record['command_id']} needs reviewer"


def test_no_command_has_unresolved_design_fields() -> None:
    markers = {"tbd", "todo", "unknown", "xxx", "???"}
    for record in load_commands():
        for key, value in record.items():
            if isinstance(value, str):
                assert (
                    value.strip().lower() not in markers
                ), f"{record['command_id']}.{key} unresolved"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
