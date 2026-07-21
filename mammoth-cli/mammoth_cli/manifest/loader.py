"""Load and validate the reviewed parity and command manifests.

These manifests are the single source of truth for capability discovery, schema
discovery, help generation, the agent skill, and the parity report. Runtime code
loads them read-only; the build scripts generate them.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SPEC_ROOT = Path(__file__).resolve().parent.parent.parent / "spec"
MANIFEST_DIR = SPEC_ROOT / "manifests"
COMMANDS_DIR = MANIFEST_DIR / "commands"
SCHEMA_PATH = MANIFEST_DIR / "schema-v1.json"
OPENAPI_OPERATIONS_PATH = MANIFEST_DIR / "openapi-operations.yaml"
SDK_METHODS_PATH = MANIFEST_DIR / "sdk-methods.yaml"

MANIFEST_SCHEMA_VERSION = 1


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema


@functools.lru_cache(maxsize=1)
def load_operations() -> list[dict[str, Any]]:
    data = _read_yaml(OPENAPI_OPERATIONS_PATH)
    if not data:
        return []
    return list(data.get("operations", []))


@functools.lru_cache(maxsize=1)
def load_sdk_methods() -> list[dict[str, Any]]:
    data = _read_yaml(SDK_METHODS_PATH)
    if not data:
        return []
    return list(data.get("methods", []))


@functools.lru_cache(maxsize=1)
def load_commands() -> list[dict[str, Any]]:
    """Load every command record across all command group files, sorted by id."""
    records: list[dict[str, Any]] = []
    if not COMMANDS_DIR.exists():
        return []
    for path in sorted(COMMANDS_DIR.glob("*.yaml")):
        data = _read_yaml(path)
        if not data:
            continue
        records.extend(data.get("commands", []))
    records.sort(key=lambda record: record["command_id"])
    return records


@dataclass(frozen=True)
class ManifestSet:
    operations: list[dict[str, Any]]
    sdk_methods: list[dict[str, Any]]
    commands: list[dict[str, Any]]


def load_all() -> ManifestSet:
    return ManifestSet(
        operations=load_operations(),
        sdk_methods=load_sdk_methods(),
        commands=load_commands(),
    )


def command_by_id(command_id: str) -> dict[str, Any] | None:
    for record in load_commands():
        if record["command_id"] == command_id:
            return record
    return None


def clear_cache() -> None:
    """Reset cached manifests (used in tests that rewrite manifest files)."""
    for func in (load_schema, load_operations, load_sdk_methods, load_commands):
        func.cache_clear()
