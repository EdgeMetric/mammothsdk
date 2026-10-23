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

SPEC_ROOT = Path(__file__).resolve().parent.parent.parent / "spec"
MANIFEST_DIR = SPEC_ROOT / "manifests"
COMMANDS_DIR = MANIFEST_DIR / "commands"
GENERATED_COMMANDS_PATH = MANIFEST_DIR / "commands.generated.yaml"
#: The override key that drops generated fields from a command record.
UNSET_KEY = "unset"
SCHEMA_PATH = MANIFEST_DIR / "schema-v1.json"
OPENAPI_OPERATIONS_PATH = MANIFEST_DIR / "openapi-operations.yaml"
SDK_METHODS_PATH = MANIFEST_DIR / "sdk-methods.yaml"

SERVER_STATUS_PATH = MANIFEST_DIR / "server-status.json"

COMPILED_DIR = MANIFEST_DIR / "compiled"
COMPILED_COMMANDS = "commands"
COMPILED_OPERATIONS = "openapi-operations"
COMPILED_SDK_METHODS = "sdk-methods"

MANIFEST_SCHEMA_VERSION = 1
_CLEANED_MARKER = ".manifest-cache-cleaned"


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    # Imported here: the compiled JSON means most runs never parse YAML.
    import yaml

    # libyaml parses the 800 KiB of command manifests in ~0.2 s; the pure-Python
    # loader takes ~2 s, which used to be most of the CLI's start-up time.
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(path.read_text(encoding="utf-8"), Loader=loader)  # noqa: S506


def cache_dir() -> Path:
    """Return the user cache directory (not created); the manifests no longer live there."""
    import platformdirs  # only the one-off cleanup needs it

    return Path(platformdirs.user_cache_dir("mammoth-cli", "Mammoth"))


def _tidy_legacy_caches() -> None:
    """Delete the parsed-manifest caches older CLI versions left in the user cache dir.

    Those versions wrote ``commands-*``, ``openapi-operations-*`` and ``sdk-methods-*``
    files per install and per manifest edit, and they piled up (tens of MB). Nothing
    writes them now. The scan runs once, guarded by a marker file; a cache dir that
    does not exist yet has nothing to clean and costs a single ``stat``.
    """
    directory = cache_dir()
    marker = directory / _CLEANED_MARKER
    try:
        if not directory.is_dir() or marker.exists():
            return
        for stem in ("commands", "openapi-operations", "sdk-methods"):
            for path in directory.glob(f"{stem}-*"):
                try:
                    path.unlink()
                except OSError:
                    continue
        marker.write_text("", encoding="utf-8")
    except OSError:
        return


def _read_compiled(name: str) -> list[dict[str, Any]] | None:
    """Return the pre-compiled JSON records for ``name``, or None when absent or unusable."""
    try:
        data = json.loads((COMPILED_DIR / f"{name}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        return None
    return data


def _server_statuses() -> dict[str, str]:
    """Command id -> ``pending`` / ``removed_on_server``, derived by ``build_server_status.py``.

    A command not listed is ``served``.
    """
    try:
        data = json.loads(SERVER_STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {cid: str(item["server_status"]) for cid, item in data.get("commands", {}).items()}


def merge_command_record(
    generated: dict[str, Any] | None, written: dict[str, Any]
) -> dict[str, Any]:
    """One command record: the generated record with a hand-written one laid over it.

    A hand-written record for a command the generator also makes holds only the fields
    that differ, plus ``unset``: the generated fields it drops. A command the generator
    does not make is hand-written in full.

    Args:
        generated: The record ``scripts/build_manifests.py`` made, or None.
        written: The record in ``commands/<group>.yaml``.

    Returns:
        The full command record.
    """
    if generated is None:
        return dict(written)
    unset = set(written.get(UNSET_KEY, ()))
    merged = {key: value for key, value in generated.items() if key not in unset}
    merged.update((key, value) for key, value in written.items() if key != UNSET_KEY)
    return merged


def command_records() -> list[dict[str, Any]]:
    """Every command record parsed from the YAML: generated and hand-written, merged.

    Build scripts and manifest tests read this; the CLI reads the compiled JSON.

    Returns:
        The full records without the derived ``server_status``: the hand-written ones in
        file order, then the generated ones no file overrides, by command id.
    """
    data = _read_yaml(GENERATED_COMMANDS_PATH)
    generated = {record["command_id"]: record for record in (data or {}).get("commands", [])}
    written: dict[str, dict[str, Any]] = {}
    for path in sorted(COMMANDS_DIR.glob("*.yaml")):
        data = _read_yaml(path)
        if data:
            written.update((record["command_id"], record) for record in data.get("commands", []))
    order = [*written, *sorted(set(generated) - set(written))]
    return [
        merge_command_record(generated.get(command_id), written.get(command_id, {}))
        for command_id in order
    ]


def _parse_yaml_commands() -> list[dict[str, Any]]:
    records = sorted(command_records(), key=lambda record: record["command_id"])
    statuses = _server_statuses()
    for record in records:
        # ``served`` is the default and is not stored, so a regenerated manifest only
        # differs on the commands whose status is not the usual one.
        if record["command_id"] in statuses:
            record["server_status"] = statuses[record["command_id"]]
    return records


def _parse_yaml_list(path: Path, root_key: str) -> list[dict[str, Any]]:
    data = _read_yaml(path)
    return list(data.get(root_key, [])) if data else []


def parse_yaml_manifests() -> dict[str, list[dict[str, Any]]]:
    """Parse the authoring YAML into the records stored under ``compiled/`` (name -> records)."""
    return {
        COMPILED_COMMANDS: _parse_yaml_commands(),
        COMPILED_OPERATIONS: _parse_yaml_list(OPENAPI_OPERATIONS_PATH, "operations"),
        COMPILED_SDK_METHODS: _parse_yaml_list(SDK_METHODS_PATH, "methods"),
    }


def compile_manifests() -> list[Path]:
    """Write ``spec/manifests/compiled/*.json`` from the YAML; return the files written.

    One record per line, so a manifest edit shows up as a small diff in review.
    """
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, records in parse_yaml_manifests().items():
        lines = ",\n".join(json.dumps(record, separators=(",", ":")) for record in records)
        path = COMPILED_DIR / f"{name}.json"
        path.write_text(f"[\n{lines}\n]\n" if records else "[]\n", encoding="utf-8")
        written.append(path)
    return written


@functools.lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema


@functools.lru_cache(maxsize=1)
def load_operations() -> list[dict[str, Any]]:
    _tidy_legacy_caches()
    compiled = _read_compiled(COMPILED_OPERATIONS)
    return (
        compiled
        if compiled is not None
        else _parse_yaml_list(OPENAPI_OPERATIONS_PATH, "operations")
    )


@functools.lru_cache(maxsize=1)
def load_sdk_methods() -> list[dict[str, Any]]:
    _tidy_legacy_caches()
    compiled = _read_compiled(COMPILED_SDK_METHODS)
    return compiled if compiled is not None else _parse_yaml_list(SDK_METHODS_PATH, "methods")


@functools.lru_cache(maxsize=1)
def load_commands() -> list[dict[str, Any]]:
    """Load every command record across all command group files, sorted by id.

    Reads ``spec/manifests/compiled/commands.json``, generated from the YAML by
    ``scripts/compile_manifests.py`` (a unit test fails when it is stale). A source
    checkout without it parses the YAML in memory; nothing is written to disk.
    """
    _tidy_legacy_caches()
    compiled = _read_compiled(COMPILED_COMMANDS)
    if compiled is not None:
        return compiled
    return _parse_yaml_commands() if COMMANDS_DIR.exists() else []


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


def server_status(command_id: str) -> str:
    """``served``, ``pending`` or ``removed_on_server`` for a command (``served`` when unknown).

    Derived at build time from the pinned prod and master OpenAPI specs
    (``scripts/build_server_status.py``) and stored in the compiled manifests.
    """
    record = command_by_id(command_id)
    return str(record.get("server_status", "served")) if record else "served"


def is_pending_server_release(command_id: str) -> bool:
    """True when the production server does not serve the command's routes yet."""
    return server_status(command_id) == "pending"


def clear_cache() -> None:
    """Reset cached manifests (used in tests that rewrite manifest files)."""
    for func in (load_schema, load_operations, load_sdk_methods, load_commands):
        func.cache_clear()
