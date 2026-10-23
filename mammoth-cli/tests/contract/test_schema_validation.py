"""Validate every manifest record against the committed manifest schema."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from mammoth_cli.manifest.loader import command_records, merge_command_record

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFESTS = CLI_ROOT / "spec" / "manifests"


def _schema() -> dict:
    return json.loads((MANIFESTS / "schema-v1.json").read_text(encoding="utf-8"))


def _validator(defname: str) -> Draft202012Validator:
    schema = _schema()
    subschema = dict(schema["$defs"][defname])
    subschema["$defs"] = schema["$defs"]
    return Draft202012Validator(subschema)


def test_schema_manifest_version_is_one() -> None:
    assert _schema()["manifest_schema_version"] == 1


def test_operation_records_validate() -> None:
    records = yaml.safe_load((MANIFESTS / "openapi-operations.yaml").read_text())["operations"]
    validator = _validator("operation_record")
    errors = [f"{r['identity']}: {e.message}" for r in records for e in validator.iter_errors(r)]
    assert not errors, errors[:10]


def test_sdk_records_validate() -> None:
    records = yaml.safe_load((MANIFESTS / "sdk-methods.yaml").read_text())["methods"]
    validator = _validator("sdk_record")
    errors = [f"{r['sdk_symbol']}: {e.message}" for r in records for e in validator.iter_errors(r)]
    assert not errors, errors[:10]


def test_command_records_validate() -> None:
    validator = _validator("command_record")
    errors = []
    for record in command_records():
        errors += [f"{record['command_id']}: {e.message}" for e in validator.iter_errors(record)]
    assert not errors, errors[:10]


def _command_records() -> list[dict]:
    return command_records()


def test_every_non_read_command_declares_edits_target() -> None:
    bad = [
        r["command_id"]
        for r in _command_records()
        if r["mutation_class"] != "read" and not isinstance(r.get("edits_target"), bool)
    ]
    assert not bad, bad[:10]


def test_schema_rejects_non_read_command_without_edits_target() -> None:
    record = next(dict(r) for r in _command_records() if r["mutation_class"] == "benign_mutation")
    del record["edits_target"]
    errors = [e.message for e in _validator("command_record").iter_errors(record)]
    assert any("edits_target" in message for message in errors), errors


def test_loader_serves_edits_target() -> None:
    from mammoth_cli.manifest.loader import command_by_id

    assert command_by_id("dataset.rename")["edits_target"] is True
    assert command_by_id("dashboard.qa.ask")["edits_target"] is False


def _generator():
    import importlib.util

    path = CLI_ROOT / "scripts" / "build_manifests.py"
    spec = importlib.util.spec_from_file_location("build_manifests_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_source_matches_committed_edits_target() -> None:
    """A regeneration must emit exactly the committed edits_target values."""
    generator = _generator()
    source = generator._load_edits_target_commands()
    records = _command_records()
    committed_true = {r["command_id"] for r in records if r.get("edits_target") is True}
    assert source == committed_true
    for record in records:
        stamped = generator._with_edits_target(dict(record), source)
        assert stamped.get("edits_target") == record.get("edits_target"), record["command_id"]
        assert list(stamped) == list(record), record["command_id"]


def test_build_leaves_hand_maintained_command_records_untouched(tmp_path, monkeypatch) -> None:
    """A regeneration rewrites no hand-written file and reproduces the generated records."""
    generator = _generator()
    manifests = tmp_path / "manifests"
    shutil.copytree(MANIFESTS, manifests)
    monkeypatch.setattr(generator, "MANIFESTS", manifests)
    monkeypatch.setattr(generator, "COMMANDS_DIR", manifests / "commands")
    monkeypatch.setattr(generator, "EDITS_TARGET_SOURCE", manifests / "edits-target.source.yaml")
    generated = manifests / generator.GENERATED_COMMANDS
    before = {p.name: p.read_bytes() for p in (manifests / "commands").glob("*.yaml")}
    generated_before = generated.read_bytes()

    generator.build()

    after = {p.name: p.read_bytes() for p in (manifests / "commands").glob("*.yaml")}
    assert after == before
    assert generated.read_bytes() == generated_before


def test_a_hand_written_record_overrides_the_generated_one_field_by_field() -> None:
    generated = {"command_id": "a.b", "mutation_class": "benign_mutation", "edits_target": False}
    written = {"command_id": "a.b", "mutation_class": "read", "unset": ["edits_target"]}
    assert merge_command_record(generated, written) == {
        "command_id": "a.b",
        "mutation_class": "read",
    }
    assert merge_command_record(None, written) == written
