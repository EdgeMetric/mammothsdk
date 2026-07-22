"""Validate every manifest record against the committed manifest schema."""

from __future__ import annotations

import glob
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

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
    for path in sorted(glob.glob(str(MANIFESTS / "commands" / "*.yaml"))):
        for record in yaml.safe_load(Path(path).read_text())["commands"]:
            errors += [
                f"{record['command_id']}: {e.message}" for e in validator.iter_errors(record)
            ]
    assert not errors, errors[:10]
